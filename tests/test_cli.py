"""Offline tests. They never call the network."""

import argparse
import contextlib
import io
import unittest

import grok_bots_cli as cli


RECIPE = {
    "profile": {"name": "Demo bot", "description": "A demo."},
    "memory": ["Remembers one fact."],
    "skills": [{"name": "Do a thing", "description": "Short.", "content": "Step 1.\n~~~\nnested fence\n~~~\n"}],
    "routines": [{"name": "daily", "description": "Every day.", "content": "Run daily."}],
    "plugins": [{"name": "tool", "description": "A plugin."}],
}


class SlugTests(unittest.TestCase):
    def test_plain_slug(self):
        self.assertEqual(cli.bot_slug("dr-eggbot-v2"), "dr-eggbot-v2")

    def test_listing_url(self):
        url = "https://x.ai/bot/marketplace/bots/dr-eggbot-v2/"
        self.assertEqual(cli.bot_slug(url), "dr-eggbot-v2")

    def test_rejects_other_hosts_and_http(self):
        for value in (
            "https://evil.example/bot/marketplace/bots/x",
            "http://x.ai/bot/marketplace/bots/x",
            "https://x.ai/other/x",
            "../etc/passwd",
        ):
            with self.subTest(value=value), self.assertRaises(argparse.ArgumentTypeError):
                cli.bot_slug(value)


class HostTests(unittest.TestCase):
    def test_https_host_check(self):
        self.assertTrue(cli.is_https_host("https://x.ai/a", cli.PAGE_HOSTS))
        self.assertFalse(cli.is_https_host("http://x.ai/a", cli.PAGE_HOSTS))
        self.assertFalse(cli.is_https_host("https://x.ai.evil.example/a", cli.PAGE_HOSTS))

    def test_fetch_refuses_unknown_host_before_network(self):
        with self.assertRaises(cli.MarketplaceError):
            cli.fetch("https://evil.example/", cli.PAGE_HOSTS, "Test")


class OutputTests(unittest.TestCase):
    def test_summary(self):
        summary = cli.summarize("demo", RECIPE)
        self.assertEqual(summary["profile"]["name"], "Demo bot")
        self.assertEqual(summary["memoryCount"], 1)
        self.assertEqual(summary["skills"], [{"name": "Do a thing", "description": "Short."}])

    def test_full_markdown(self):
        text = cli.full_recipe_markdown("demo", RECIPE)
        self.assertIn("## Skills (1)", text)
        self.assertIn("### Do a thing", text)
        self.assertIn("## Memories (1)", text)
        self.assertIn("~~~~text", text)  # fence longer than the nested one

    def test_full_markdown_blocks_credentials(self):
        recipe = dict(RECIPE, routines=[{"name": "r", "content": "API_KEY = abcdefghijklmnopqrstuvwxyz123456"}])
        with self.assertRaises(cli.MarketplaceError):
            cli.full_recipe_markdown("demo", recipe)

    def test_full_markdown_blocks_control_characters(self):
        recipe = dict(RECIPE, memory=["hidden \x1b[31m escape"])
        with self.assertRaises(cli.MarketplaceError):
            cli.full_recipe_markdown("demo", recipe)


class CommandTests(unittest.TestCase):
    def test_version(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit) as exit_info:
            cli.main(["--version"])
        self.assertEqual(exit_info.exception.code, 0)
        self.assertEqual(out.getvalue().strip(), f"grok-bots-cli {cli.__version__}")


if __name__ == "__main__":
    unittest.main()

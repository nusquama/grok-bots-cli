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
        text, redacted = cli.full_recipe_markdown("demo", RECIPE)
        self.assertEqual(redacted, 0)
        self.assertIn("## Skills (1)", text)
        self.assertIn("### Do a thing", text)
        self.assertIn("## Memories (1)", text)
        self.assertIn("~~~~text", text)  # fence longer than the nested one

    def test_full_markdown_redacts_credentials_and_keeps_the_rest(self):
        secret = "abcdefghijklmnopqrstuvwxyz123456"
        recipe = dict(RECIPE, routines=[{"name": "r", "content": f"Before.\nAPI_KEY = {secret}\nAfter."}])
        text, redacted = cli.full_recipe_markdown("demo", recipe)
        self.assertEqual(redacted, 1)
        self.assertNotIn(secret, text)
        self.assertIn(cli.REDACTED, text)
        self.assertIn("Before.", text)
        self.assertIn("After.", text)
        self.assertIn("1 possible credential(s) replaced", text)

    def test_redacts_token_shapes(self):
        for token in ("ghp_" + "a" * 36, "sk-" + "b" * 40, "-----BEGIN RSA PRIVATE KEY-----"):
            with self.subTest(token=token[:6]):
                text, count = cli.redact(f"value {token} end")
                self.assertEqual(count, 1)
                self.assertNotIn(token, text)

    def test_full_markdown_blocks_control_characters(self):
        recipe = dict(RECIPE, memory=["hidden \x1b[31m escape"])
        with self.assertRaises(cli.MarketplaceError):
            cli.full_recipe_markdown("demo", recipe)


class RedactDataTests(unittest.TestCase):
    def test_nested_json_section(self):
        token = "ghp_" + "c" * 36
        data = [{"name": "s", "content": f"use {token}", "n": 3}]
        result, count = cli.redact_data(data)
        self.assertEqual(count, 1)
        self.assertNotIn(token, str(result))
        self.assertEqual(result[0]["n"], 3)


class CommandTests(unittest.TestCase):
    def test_version(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit) as exit_info:
            cli.main(["--version"])
        self.assertEqual(exit_info.exception.code, 0)
        self.assertEqual(out.getvalue().strip(), f"grok-bots-cli {cli.__version__}")


if __name__ == "__main__":
    unittest.main()

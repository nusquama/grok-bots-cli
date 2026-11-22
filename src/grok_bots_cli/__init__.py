"""Read public Grok Bot Marketplace listings and recipes.

Unofficial tool. Not affiliated with, endorsed by, or sponsored by SpaceXSI or xAI.
"""

import argparse
import base64
import binascii
import json
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


__version__ = "0.1.0"

MARKETPLACE = "https://x.ai/bot/marketplace"
LISTING_API = "https://api2.cursor.sh/aiserver.v1.GrokBotService/GetPublicGrokBotMarketplaceListing"
TEMPLATE_HOST = "grok-bot-marketplace-public-assets.s3.us-east-1.amazonaws.com"
PAGE_HOSTS = {"x.ai", "www.x.ai"}
SLUG = r"[A-Za-z0-9_-]+"
BOT_PATH = "/bot/marketplace/bots/"
BASE64_PREFIX = "data:application/json;base64,"
MAX_BYTES = 8 * 1024 * 1024
SECTIONS = ("profile", "memory", "gettingStarted", "skills", "routines", "plugins")
POSSIBLE_CREDENTIAL = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----|"
    r"\b(?:sbp_[A-Za-z0-9]{25,}|gh[pousr]_[A-Za-z0-9]{20,}|"
    r"github_pat_[A-Za-z0-9_]{30,}|(?:sk-|xai-)[A-Za-z0-9_-]{25,}|"
    r"eyJ[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{12,})\b"
    r"|(?im:^[ \t]*(?:(?:export|const|let)[ \t]+)?[A-Z_]*(?:API[_-]?KEY|PASSWORD|TOKEN|SECRET)"
    r"[A-Z_]*[ \t]*[:=][ \t]*[\x22\x27]?[A-Za-z0-9_+/=-]{24,})"
)


class MarketplaceError(Exception):
    """An actionable error that can be printed without network response data."""


def is_https_host(url, hosts):
    parts = urlsplit(url)
    return parts.scheme == "https" and parts.netloc.lower() in hosts


class MarketplaceRedirect(HTTPRedirectHandler):
    def __init__(self, hosts):
        self.hosts = hosts

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not is_https_host(newurl, self.hosts):
            raise MarketplaceError("The marketplace redirected to an unexpected host.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(url, hosts, label, payload=None):
    if not is_https_host(url, hosts):
        raise MarketplaceError(f"{label} returned an unexpected URL.")
    headers = {"User-Agent": f"grok-bots-cli/{__version__} (+https://github.com/nusquama/grok-bots-cli)"}
    if payload is not None:
        headers.update({"Content-Type": "application/json", "Connect-Protocol-Version": "1"})
        payload = json.dumps(payload).encode()
    request = Request(url, data=payload, headers=headers)
    try:
        with build_opener(MarketplaceRedirect(hosts)).open(request, timeout=20) as response:
            data = response.read(MAX_BYTES + 1)
    except HTTPError as error:
        raise MarketplaceError(f"{label} returned HTTP {error.code}.") from None
    except (URLError, OSError):
        raise MarketplaceError(f"Could not connect to {label}.") from None
    if len(data) > MAX_BYTES:
        raise MarketplaceError(f"{label} returned a response larger than 8 MiB.")
    return data


def bot_slug(value):
    if re.fullmatch(SLUG, value):
        return value
    try:
        valid_host = is_https_host(value, PAGE_HOSTS)
        path = urlsplit(value).path
    except ValueError:
        valid_host = False
        path = ""
    match = re.fullmatch(rf"{BOT_PATH}({SLUG})/?", path)
    if valid_host and match:
        return match[1]
    raise argparse.ArgumentTypeError("expected a bot slug or an HTTPS Grok Bot Marketplace listing")


def list_bots():
    html = fetch(MARKETPLACE, PAGE_HOSTS, "Marketplace").decode("utf-8", errors="replace")
    slugs = sorted(set(re.findall(rf"{BOT_PATH}({SLUG})", html)))
    if not slugs:
        raise MarketplaceError("No bot listings were found on the Marketplace home page.")
    return slugs


def load_recipe(slug):
    listing = json.loads(fetch(LISTING_API, {"api2.cursor.sh"}, "Listing API", {"slug": slug}))
    template = listing.get("templateGetUrl") if isinstance(listing, dict) else None
    if not isinstance(template, str) or not template:
        raise MarketplaceError("The listing did not provide a public recipe.")
    if template.startswith(BASE64_PREFIX):
        data = base64.b64decode(template[len(BASE64_PREFIX):], validate=True)
    else:
        data = fetch(template, {TEMPLATE_HOST}, "Recipe download")
    recipe = json.loads(data)
    if not isinstance(recipe, dict) or not isinstance(recipe.get("profile"), dict):
        raise MarketplaceError("The public recipe has an unexpected format.")
    return recipe


def summarize(slug, recipe):
    return {
        "slug": slug,
        "url": f"https://x.ai{BOT_PATH}{slug}",
        "profile": {
            key: recipe["profile"][key]
            for key in ("name", "description")
            if isinstance(recipe["profile"].get(key), str)
        },
        "memoryCount": len(recipe.get("memory") or []),
        **{
            section: [
                {key: item[key] for key in ("name", "description") if isinstance(item.get(key), str)}
                for item in recipe.get(section) or []
                if isinstance(item, dict)
            ]
            for section in ("skills", "routines", "plugins")
        },
    }


def full_recipe_markdown(slug, recipe):
    lines = [f"# {slug}", "", f"https://x.ai{BOT_PATH}{slug}", ""]
    for section, title in (("skills", "Skills"), ("routines", "Routines"), ("memory", "Memories")):
        items = recipe.get(section)
        if items is None:
            items = []
        if not isinstance(items, list):
            raise MarketplaceError(f"Unexpected format for the {section} section.")
        lines.extend([f"## {title} ({len(items)})", ""])
        for index, item in enumerate(items, 1):
            heading = item.get("name") if isinstance(item, dict) and section != "memory" else None
            content = item.get("content") if isinstance(item, dict) else item
            if not isinstance(content, str):
                raise MarketplaceError(f"Missing text in the {section} section.")
            if not isinstance(heading, str) or not heading.strip() or not heading.isprintable():
                heading = f"{title} {index}" if section != "memory" else f"Memory {index}"
            if POSSIBLE_CREDENTIAL.search(content) or POSSIBLE_CREDENTIAL.search(heading):
                raise MarketplaceError(f"Export stopped: possible credential in {section}.")
            if re.search(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]", content):
                raise MarketplaceError(f"Export stopped: control characters in {section}.")
            longest = max(map(len, re.findall(r"~+", content)), default=0)
            fence = "~" * max(3, longest + 1)
            block = f"{fence}text\n{content}"
            if not block.endswith("\n"):
                block += "\n"
            lines.extend([f"### {heading}", "", block + fence, ""])
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="grok-bots-cli", description="Read public Grok Bot Marketplace listings and recipes."
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="List bot slugs found on the Marketplace home page.")
    show = commands.add_parser("show", help="Read one public recipe by slug or listing URL.")
    show.add_argument("bot", type=bot_slug)
    output = show.add_mutually_exclusive_group()
    output.add_argument("--section", choices=SECTIONS, help="Show the requested recipe section.")
    output.add_argument("--full", action="store_true", help="Print all skill, routine and memory texts as Markdown.")
    args = parser.parse_args(argv)
    try:
        if args.command == "list":
            print("\n".join(list_bots()))
        else:
            recipe = load_recipe(args.bot)
            if args.full:
                sys.stdout.write(full_recipe_markdown(args.bot, recipe))
            else:
                result = recipe.get(args.section) if args.section else summarize(args.bot, recipe)
                print(json.dumps(result, indent=2))
    except MarketplaceError as error:
        print(f"grok-bots-cli: {error}", file=sys.stderr)
        return 1
    except (ValueError, TypeError, binascii.Error):
        print("grok-bots-cli: The marketplace returned unexpected data.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

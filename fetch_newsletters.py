#!/usr/bin/env python3
"""
Newsletter Crawler Agent
========================
Connects to mishratulsinlupdates@gmail.com via IMAP,
fetches recent newsletter emails, categorises them,
extracts top stories, and writes newsletter_data.js
which newsletter.html loads as a script tag (works with file:// and http://).

Usage:
    python3 fetch_newsletters.py

You will be prompted for your Gmail App Password.
To create one: myaccount.google.com > Security > App Passwords
"""

import imaplib
import email
import json
import os
import re
import getpass
import sys
import html
import subprocess
from email.header import decode_header
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse

# ── Keychain helpers (macOS) ─────────────────────────────────────────────────
KEYCHAIN_SERVICE = "newsletter-crawler"
KEYCHAIN_ACCOUNT = "mishratulsinlupdates@gmail.com"

def keychain_get(service, account):
    """Read a password from macOS Keychain. Returns None if not found."""
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-s", service, "-a", account, "-w"],
            capture_output=True, text=True
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception:
        return None

def keychain_set(service, account, password):
    """Save a password to macOS Keychain (overwrites if exists)."""
    try:
        subprocess.run(
            ["security", "add-generic-password", "-s", service, "-a", account,
             "-w", password, "-U"],
            capture_output=True
        )
    except Exception:
        pass

# ── Config ──────────────────────────────────────────────────────────────────
EMAIL_ADDRESS = "mishratulsinlupdates@gmail.com"
IMAP_HOST     = "imap.gmail.com"
OUTPUT_FILE   = "newsletter_data.js"
TOP_PER_CAT   = 3            # stories shown per category on the page

# ── Category rules ──────────────────────────────────────────────────────────
# Each rule: (category_key, display_name, emoji, [keywords in sender/subject])
CATEGORIES = [
    ("hpc_ai",   "HPC & AI",              "⚡", [
        "hpc","supercomputer","cray","nvidia","gpu","deep learning",
        "machine learning","artificial intelligence","ai weekly","the batch",
        "synced","import ai","the gradient","alphasignal","papers with code",
        "jack clark","ml","llm","openai","anthropic","hugging face",
    ]),
    ("product",  "Product Management",    "🗺️", [
        "product hunt","mind the product","lenny","productboard","intercom",
        "aha!","product school","product coalition","dept of product",
        "productled","reforge","amplitude","mixpanel","roadmap","product manager",
        "ken norton","shreyas","productify","gibsonbiddle",
    ]),
    ("tech",     "Tech & Gadgets",        "💻", [
        "wired","the verge","techcrunch","ars technica","hacker news",
        "morning paper","stratechery","ben thompson","benedict evans",
        "exponential view","azeem azhar","technology review","ieee","acm",
        "hackernewsletter","tldr","bytes.dev","javascript weekly",
        "python weekly","devops","kubernetes","docker","aws","cloud",
    ]),
    ("business", "Business & Strategy",   "📈", [
        "morning brew","the hustle","axios","bloomberg","wsj","ft.com",
        "economist","quartz","business insider","fast company","inc.",
        "harvard business","mckinsey","bcg","hbr","fortune","forbes",
        "finimize","cbinsights","pitchbook","crunchbase",
    ]),
    ("stoic",    "Stoicism & Philosophy", "🧘", [
        "stoic","daily stoic","ryan holiday","marcus aurelius","seneca",
        "epictetus","philosophy","meditations","obstacle","perennial seller",
        "routines","morning ritual","james clear","atomic habits",
        "tim ferriss","naval","farnam street","brain pickings","fs.blog",
    ]),
    ("travel",   "Travel & Lifestyle",    "✈️", [
        "lonely planet","national geographic","nomadic matt","travel",
        "points guy","suitcase","condé nast traveler","afar","tripadvisor",
        "airbnb","skift","thrillist","culture trip","atlas obscura",
    ]),
]

# ── Helpers ──────────────────────────────────────────────────────────────────
def decode_str(value):
    """Decode email header string."""
    if value is None:
        return ""
    parts = decode_header(value)
    decoded = []
    for part, enc in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(enc or "utf-8", errors="replace"))
        else:
            decoded.append(part)
    return " ".join(decoded)

def extract_text(msg):
    """Pull plain-text or stripped-HTML body from a Message object."""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            cd = str(part.get("Content-Disposition", ""))
            if "attachment" in cd:
                continue
            if ct == "text/plain":
                charset = part.get_content_charset() or "utf-8"
                body += part.get_payload(decode=True).decode(charset, errors="replace")
                break
            elif ct == "text/html" and not body:
                charset = part.get_content_charset() or "utf-8"
                raw = part.get_payload(decode=True).decode(charset, errors="replace")
                body = re.sub(r"<[^>]+>", " ", raw)
    else:
        charset = msg.get_content_charset() or "utf-8"
        raw = msg.get_payload(decode=True).decode(charset, errors="replace")
        if msg.get_content_type() == "text/html":
            body = re.sub(r"<[^>]+>", " ", raw)
        else:
            body = raw
    # Collapse whitespace
    return re.sub(r"\s+", " ", html.unescape(body)).strip()[:2000]

def extract_links(msg):
    """Pull first meaningful http/https link from the HTML body."""
    links = []
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                charset = part.get_content_charset() or "utf-8"
                raw = part.get_payload(decode=True).decode(charset, errors="replace")
                links += re.findall(r'href=["\']?(https?://[^\s"\'<>]+)', raw)
    else:
        if msg.get_content_type() == "text/html":
            charset = msg.get_content_charset() or "utf-8"
            raw = msg.get_payload(decode=True).decode(charset, errors="replace")
            links += re.findall(r'href=["\']?(https?://[^\s"\'<>]+)', raw)

    # Filter out tracking pixels, unsubscribe links, logo assets
    skip = ["unsubscribe","tracking","pixel","beacon","open.php",
            "click.php","mailchimp","sendgrid","mailgun","constantcontact",
            "list-manage","campaign-archive","googleapis","gstatic",
            "gravatar","assets","cdn","logo","header","footer","banner"]
    clean = []
    for l in links:
        low = l.lower()
        if not any(s in low for s in skip):
            parsed = urlparse(l)
            if parsed.scheme in ("http","https") and "." in parsed.netloc:
                clean.append(l)
    return clean[0] if clean else ""

def categorise(sender, subject):
    """Return the best matching category key, or 'other'."""
    haystack = (sender + " " + subject).lower()
    for cat_key, _, _, keywords in CATEGORIES:
        if any(kw in haystack for kw in keywords):
            return cat_key
    return "other"

def make_snippet(text, max_len=160):
    s = re.sub(r"\s+", " ", text).strip()
    return (s[:max_len] + "…") if len(s) > max_len else s

def friendly_date(date_str):
    try:
        dt = email.utils.parsedate_to_datetime(date_str)
        return dt.strftime("%-d %b %Y")
    except Exception:
        return date_str or ""

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  Newsletter Crawler — mishratulsinlupdates@gmail.com")
    print("=" * 60)
    print()

    # Password lookup order: env var (CI) → Keychain (local) → interactive prompt
    app_password = os.environ.get("GMAIL_APP_PASSWORD")
    if app_password:
        print("🔑 Using App Password from environment variable.")
    else:
        app_password = keychain_get(KEYCHAIN_SERVICE, EMAIL_ADDRESS)
        if app_password:
            print("🔑 Using saved App Password from macOS Keychain.")
        else:
            if not sys.stdin.isatty():
                # Called non-interactively (e.g. from the browser refresh button or CI)
                print("❌ No App Password found in GMAIL_APP_PASSWORD env var or Keychain.")
                print("   Run the script manually once to save it:")
                print("   python3 fetch_newsletters.py")
                sys.exit(2)
            print("You need a Gmail App Password (not your regular password).")
            print("Get one at: myaccount.google.com > Security > App Passwords")
            print("It will be saved securely to your macOS Keychain for future runs.")
            print()
            app_password = getpass.getpass("Enter Gmail App Password: ")
            keychain_set(KEYCHAIN_SERVICE, EMAIL_ADDRESS, app_password)
            print("✅ Password saved to Keychain — you won't need to enter it again.")

    print("\n🔌 Connecting to Gmail IMAP…")
    try:
        mail = imaplib.IMAP4_SSL(IMAP_HOST)
        mail.login(EMAIL_ADDRESS, app_password)
    except imaplib.IMAP4.error as e:
        print(f"\n❌ Login failed: {e}")
        print("Make sure you're using an App Password, not your regular password.")
        # Clear any bad cached password from Keychain
        try:
            import subprocess as _sp
            _sp.run(["security", "delete-generic-password",
                     "-s", KEYCHAIN_SERVICE, "-a", EMAIL_ADDRESS],
                    capture_output=True)
            print("🗑  Removed bad password from Keychain. Run again to re-enter it.")
        except Exception:
            pass
        sys.exit(1)

    print("✅ Connected successfully!")

    # Select inbox
    mail.select("INBOX")

    # Search emails from yesterday onwards (covers today + yesterday = n and n-1)
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    since_str = yesterday.strftime("%d-%b-%Y")   # e.g. "05-Mar-2026"
    today_str = datetime.now(timezone.utc).strftime("%d %b %Y")
    yest_str  = yesterday.strftime("%d %b %Y")

    _, msg_ids = mail.search(None, f'SINCE {since_str}')
    scan_ids = msg_ids[0].split()
    scan_ids.reverse()  # newest first

    print(f"📬 Fetching emails from {yest_str} → {today_str}  ({len(scan_ids)} found)…\n")

    # Initialise buckets
    buckets = {cat[0]: [] for cat in CATEGORIES}
    buckets["other"] = []

    for i, eid in enumerate(scan_ids):
        try:
            _, data = mail.fetch(eid, "(RFC822)")
            raw = data[0][1]
            msg = email.message_from_bytes(raw)

            sender  = decode_str(msg.get("From", ""))
            subject = decode_str(msg.get("Subject", "(no subject)"))
            date    = msg.get("Date", "")

            cat = categorise(sender, subject)
            snippet = make_snippet(extract_text(msg))
            link    = extract_links(msg)

            entry = {
                "title":   subject,
                "sender":  re.sub(r"<.*?>", "", sender).strip(),
                "date":    friendly_date(date),
                "snippet": snippet,
                "link":    link,
                "category": cat,
            }

            bucket = buckets.get(cat, buckets["other"])
            bucket.append(entry)

            if (i + 1) % 20 == 0:
                print(f"  … processed {i + 1}/{len(scan_ids)}")

        except Exception as ex:
            continue

    mail.logout()

    # Build output: top N per category + all articles
    categories_out = []
    all_stories = []

    for cat_key, display, emoji, _ in CATEGORIES:
        stories = buckets.get(cat_key, [])
        if not stories:
            continue
        categories_out.append({
            "key":     cat_key,
            "name":    display,
            "emoji":   emoji,
            "count":   len(stories),
            "top":     stories[:TOP_PER_CAT],
            "all":     stories,
        })
        all_stories.extend(stories)

    # "Other" bucket — keep but don't display unless has content
    if buckets["other"]:
        categories_out.append({
            "key":   "other",
            "name":  "More Reads",
            "emoji": "📌",
            "count": len(buckets["other"]),
            "top":   buckets["other"][:TOP_PER_CAT],
            "all":   buckets["other"],
        })

    output = {
        "generated":        datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "date_range":       f"{yest_str} – {today_str}",
        "total_scanned":    len(scan_ids),
        "total_categorised": len(all_stories),
        "categories":       categories_out,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("// Auto-generated by fetch_newsletters.py — do not edit manually\n")
        f.write("window.NEWSLETTER_DATA = ")
        json.dump(output, f, indent=2, ensure_ascii=False)
        f.write(";\n")

    print(f"\n✅ Done! Scanned {len(scan_ids)} emails from {yest_str} → {today_str}.")
    print(f"   Categorised {len(all_stories)} newsletter stories.")
    print(f"\n📊 Breakdown:")
    for c in categories_out:
        print(f"   {c['emoji']}  {c['name']:30s}  {c['count']} stories")
    print(f"\n💾 Saved to {OUTPUT_FILE}")
    print("🌐 Open newsletter.html in your browser — works by double-click or via server.")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Close general/distracting Chrome tabs on macOS via AppleScript.

Closes:
  - youtube.com tabs
  - weebcentral.com tabs
  - Blank new tabs (chrome://newtab, about:blank)
  - Duplicate tabs (keeps the first occurrence, closes the rest)
  - Google search tabs NOT in AI Mode (keeps tabs with udm= param)
  - Gmail tabs

Usage:
  python tools/close_tabs.py          # Close all matching tabs
  python tools/close_tabs.py --dry-run  # Preview what would be closed
"""

import subprocess
import json
import sys


# --- Configuration -----------------------------------------------------------

# Domains/patterns to always close
CLOSE_DOMAINS = [
    "youtube.com",
    "weebcentral.com",
    "mail.google.com",
    "github.com",
    "claude.ai",
    "perplexity.ai",
    "cursor.com",
    "linkedin.com",
    "console.cloud.google.com",
]

# URLs that indicate a blank/new tab
BLANK_URLS = [
    "chrome://newtab",
    "chrome://newtab/",
    "about:blank",
]


# --- JXA / AppleScript helpers -----------------------------------------------

# Use JXA (JavaScript for Automation) for listing — handles large tab counts
# and returns clean JSON, unlike AppleScript string concatenation.
JXA_LIST_TABS = """
var chrome = Application('Google Chrome');
var results = [];
var windows = chrome.windows();
for (var w = 0; w < windows.length; w++) {
    var tabs = windows[w].tabs();
    for (var t = 0; t < tabs.length; t++) {
        results.push({
            window: w + 1,
            tab: t + 1,
            url: tabs[t].url(),
            title: tabs[t].title()
        });
    }
}
JSON.stringify(results);
"""

def build_close_script(tabs_to_close):
    """Build AppleScript that closes tabs in reverse order to avoid index shifting."""
    if not tabs_to_close:
        return None

    # Sort by window desc, then tab index desc so closing doesn't shift indices
    tabs_to_close.sort(key=lambda x: (x["window"], x["tab"]), reverse=True)

    lines = ['tell application "Google Chrome"']
    for tab in tabs_to_close:
        lines.append(f'    close tab {tab["tab"]} of window {tab["window"]}')
    lines.append("end tell")
    return "\n".join(lines)


# --- Closing logic -----------------------------------------------------------

def should_close(tab, seen_urls):
    """Determine if a tab should be closed. Returns (bool, reason)."""
    url = tab["url"].lower()

    # Blank tabs
    for blank in BLANK_URLS:
        if url == blank or url == blank.lower():
            return True, "blank tab"

    # Domain-based closing
    for domain in CLOSE_DOMAINS:
        if domain in url:
            return True, f"matches {domain}"

    # Google search without AI Mode
    if ("google.com/search" in url) and ("udm=" not in url) and ("ai_mode" not in url):
        return True, "Google search (not AI Mode)"

    # Duplicate detection (keep the first, close subsequent)
    normalized = url.split("#")[0].rstrip("/")  # strip fragment and trailing slash
    if normalized in seen_urls:
        return True, f"duplicate of tab in window {seen_urls[normalized]['window']}"
    seen_urls[normalized] = tab

    return False, ""


def main():
    dry_run = "--dry-run" in sys.argv

    # Check if Chrome is running
    check = subprocess.run(
        ["osascript", "-e", 'tell application "System Events" to (name of processes) contains "Google Chrome"'],
        capture_output=True, text=True,
    )
    if "true" not in check.stdout.lower():
        print("Google Chrome is not running.")
        return

    # Get all tabs via JXA (returns JSON)
    result = subprocess.run(
        ["osascript", "-l", "JavaScript", "-e", JXA_LIST_TABS],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"Error listing tabs: {result.stderr}")
        return

    try:
        tabs = json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"Error parsing tab data: {result.stdout[:200]}")
        return
    if not tabs:
        print("No tabs found.")
        return

    print(f"Found {len(tabs)} total tab(s) across Chrome windows.\n")

    # Evaluate each tab
    seen_urls = {}
    tabs_to_close = []

    for tab in tabs:
        close, reason = should_close(tab, seen_urls)
        if close:
            tab["reason"] = reason
            tabs_to_close.append(tab)

    if not tabs_to_close:
        print("No tabs to close. Everything looks clean!")
        return

    # Report
    print(f"{'[DRY RUN] ' if dry_run else ''}Closing {len(tabs_to_close)} tab(s):\n")
    for t in tabs_to_close:
        title_short = t["title"][:50] + "..." if len(t["title"]) > 50 else t["title"]
        print(f"  ✕ [{t['reason']}] {title_short}")
        print(f"    {t['url'][:80]}")

    if dry_run:
        print(f"\nDry run complete. {len(tabs_to_close)} tab(s) would be closed.")
        return

    # Close tabs
    close_script = build_close_script(tabs_to_close)
    if close_script:
        result = subprocess.run(
            ["osascript", "-e", close_script],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"\nError closing tabs: {result.stderr}")
        else:
            print(f"\nDone. Closed {len(tabs_to_close)} tab(s).")


if __name__ == "__main__":
    main()

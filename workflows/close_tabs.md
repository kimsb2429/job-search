# Close Browser Tabs Workflow

## Objective
Clean up Chrome by closing general/distracting tabs while preserving work-related tabs.

## What Gets Closed
| Category | Pattern | Notes |
|---|---|---|
| YouTube | `youtube.com` | All YouTube tabs |
| Weebcentral | `weebcentral.com` | All Weebcentral tabs |
| Gmail | `mail.google.com` | All Gmail tabs |
| Blank tabs | `chrome://newtab`, `about:blank` | Empty/new tabs |
| Google Search | `google.com/search` without `udm=` or `ai_mode` | Keeps AI Mode searches open |
| Duplicates | Same URL appearing multiple times | Keeps the first occurrence |

## What Gets Preserved
- Google Search tabs with AI Mode active (`udm=` or `ai_mode` in URL)
- All other tabs not matching the patterns above

## Tool
`tools/close_tabs.py`

## Usage

### Preview what would be closed (safe)
```bash
python tools/close_tabs.py --dry-run
```

### Close matching tabs
```bash
python tools/close_tabs.py
```

## Requirements
- macOS (uses AppleScript via `osascript`)
- Google Chrome must be running
- No additional Python packages needed (stdlib only)

## Customization
Edit the following in `tools/close_tabs.py`:
- `CLOSE_DOMAINS` — list of domains to always close
- `BLANK_URLS` — URLs considered "blank" tabs
- The Google search condition in `should_close()` — controls AI Mode detection

## Edge Cases
- **Reverse tab closing**: Tabs are closed from highest index to lowest to avoid index shifting
- **Chrome not running**: Script exits gracefully with a message
- **Duplicate detection**: Compares URLs after stripping fragments (`#`) and trailing slashes

# HueWheel

## Secrets and personal information

**This repo is public. Nothing private goes into it, in any file, commit message, PR, issue or
comment.** This rule is not optional and has no exceptions for tests, examples or quick fixes.

Never commit or push:

- The Hue application key, Wi-Fi name or password, or any other credential
- IP addresses, MAC addresses or hostnames from the owner's network
- The bridge ID, or Hue resource IDs (automations, rooms, devices)
- Real names of rooms or automations, alarm times or daily routine
- Email addresses, home directory paths or local usernames

Where these values live:

- `firmware/include/secrets.h` holds the Wi-Fi and Hue values. `tools/.hue-backup.json` holds a
  copy of a real automation. `.private-denylist` lists extra values to block. All three are
  git-ignored and must stay that way.
- In tracked files, use placeholders such as `<id>`, and make new private settings go through
  `secrets.h`.

Rules for working in this repo:

- Don't print the Hue key or Wi-Fi password in tool output. Scan with counts or file names.
- Never bypass the checks: no `--no-verify`, no changing `core.hooksPath`, and no weakening
  `tools/check_secrets.py` or adding to its allowlist to get a commit through. If the scanner
  blocks something, remove the value. If it looks like a false positive, ask the owner first.
- `.gitignore` is not a check on its own. Before committing, stage files by name and read what
  is staged.
- Only documentation and example values that are clearly fake may look like real ones, and the
  scanner may still block them. Reword rather than work around it.
- If something private does reach GitHub, stop and tell the owner immediately. Deleting it in a
  new commit does not remove it from history, so a leaked credential must be rotated.

### How this is enforced

`tools/check_secrets.py` runs from `.githooks` before every commit and every push, and from
`.github/workflows/secret-scan.yml` on GitHub. `.claude/settings.json` denies the commands that
skip the hooks.

The hooks are not active in a fresh clone. Turn them on first:

```bash
git config core.hooksPath .githooks
```

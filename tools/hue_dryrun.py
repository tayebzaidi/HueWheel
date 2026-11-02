#!/usr/bin/env python3
"""Try out the firmware's Hue calls from a PC, against a real bridge.

  hue_dryrun.py discover             find the bridge (no key needed)
  hue_dryrun.py pair                 press the bridge button first; saves the key
  hue_dryrun.py list                 show the Wake Up automations
  hue_dryrun.py use <id>             pick the automation the device will edit
  hue_dryrun.py plan HH:MM on|off    show what would be sent; changes nothing
  hue_dryrun.py apply HH:MM on|off   send it, read it back, keep a backup
  hue_dryrun.py restore              put the backup back

Bridge IP, key and automation id are stored in firmware/include/secrets.h, which
git ignores, and the same file builds into the firmware. The key is never printed.
Python standard library only.
"""
import argparse
import copy
import json
import re
import shutil
import ssl
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SECRETS = ROOT / "firmware/include/secrets.h"
EXAMPLE = ROOT / "firmware/include/secrets.example.h"
BACKUP = ROOT / "tools/.hue-backup.json"

# Same trade-off as firmware/src/hue.cpp: the bridge's certificate isn't verified.
TLS = ssl._create_unverified_context()


def read_secret(name):
    if not SECRETS.exists():
        return ""
    m = re.search(rf'#define {name} "([^"]*)"', SECRETS.read_text())
    return m.group(1) if m else ""


def write_secret(name, value):
    if not SECRETS.exists():
        shutil.copy(EXAMPLE, SECRETS)
    text, n = re.subn(rf'(#define {name} )"[^"]*"', rf'\1"{value}"', SECRETS.read_text())
    if n != 1:
        sys.exit(f"{name} not found in {SECRETS}")
    SECRETS.write_text(text)


def call(method, url, body=None, headers=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, context=TLS, timeout=15) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        text = e.read().decode(errors="replace")
        try:
            return e.code, json.loads(text)
        except ValueError:
            return e.code, text


def v2(method, path, body=None):
    ip, key = read_secret("HUE_BRIDGE_IP"), read_secret("HUE_APP_KEY")
    if not ip or not key:
        sys.exit("No bridge or key saved yet: run discover, then pair.")
    code, reply = call(method, f"https://{ip}/clip/v2/resource/{path}", body,
                       {"hue-application-key": key})
    if code != 200:
        sys.exit(f"{method} {path} -> HTTP {code}\n{json.dumps(reply, indent=2)}")
    return reply


def wakeup_id():
    wid = read_secret("HUE_WAKEUP_ID")
    if not wid:
        sys.exit("No automation chosen yet: run list, then use <id>.")
    return wid


def wakeup_scripts():
    return {s["id"]: s for s in v2("GET", "behavior_script")["data"]
            if "wake" in s.get("metadata", {}).get("name", "").lower()}


def get_instance(wid):
    return v2("GET", f"behavior_instance/{wid}")["data"][0]


def patched(inst, hour, minute):
    """The firmware's edit. Keep this matching hueSetAlarm() in firmware/src/hue.cpp."""
    cfg = copy.deepcopy(inst["configuration"])
    time_ = cfg["when"]["time_point"]["time"]
    time_["hour"], time_["minute"] = hour, minute
    return cfg


def parse_alarm(a):
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", a.time)
    if not m:
        sys.exit("Time must look like 07:30")
    hour, minute = int(m[1]), int(m[2])
    if hour > 23 or minute > 55 or minute % 5:
        sys.exit("Hours 00-23, minutes in 5-minute steps: that is all the wheels can show")
    return hour, minute, a.state == "on"


def cmd_discover(_):
    _, found = call("GET", "https://discovery.meethue.com/")
    print(json.dumps(found, indent=2))
    if not found:
        sys.exit("No bridge reported. Try: avahi-browse -rt _hue._tcp")
    ip = found[0]["internalipaddress"]
    _, cfg = call("GET", f"https://{ip}/api/0/config")
    print(json.dumps({k: cfg.get(k) for k in ("name", "modelid", "apiversion", "swversion")}, indent=2))
    write_secret("HUE_BRIDGE_IP", ip)
    print(f"Saved bridge {ip}")


def cmd_pair(_):
    ip = read_secret("HUE_BRIDGE_IP")
    if not ip:
        sys.exit("Run discover first.")
    print("Press the round button on the bridge. Waiting up to 40 seconds...")
    for _ in range(20):
        _, reply = call("POST", f"https://{ip}/api", {"devicetype": "huewheel#esp32c3"})
        entry = reply[0]
        if "success" in entry:
            write_secret("HUE_APP_KEY", entry["success"]["username"])
            print("Paired. Key saved to firmware/include/secrets.h")
            return
        if entry["error"]["type"] != 101:  # 101 = button not pressed yet
            sys.exit(entry["error"]["description"])
        time.sleep(2)
    sys.exit("Timed out waiting for the button.")


def cmd_list(_):
    scripts = wakeup_scripts()
    print("Wake-up scripts:", {i: s["metadata"]["name"] for i, s in scripts.items()})
    instances = [b for b in v2("GET", "behavior_instance")["data"] if b["script_id"] in scripts]
    if not instances:
        print("No Wake Up automations found. Create one in the Hue app.")
    for b in instances:
        print(json.dumps(b, indent=2))


def cmd_use(a):
    inst = get_instance(a.id)
    print(json.dumps(inst, indent=2))
    write_secret("HUE_WAKEUP_ID", a.id)
    print(f"Saved. The device will edit {inst.get('metadata', {}).get('name', a.id)!r}.")


def cmd_plan(a):
    hour, minute, enabled = parse_alarm(a)
    wid = wakeup_id()
    inst = get_instance(wid)
    body = {"enabled": enabled, "configuration": patched(inst, hour, minute)}
    print(f"Now: enabled={inst['enabled']} when={json.dumps(inst['configuration']['when'])}")
    print(f"Would PUT behavior_instance/{wid}:")
    print(json.dumps(body, indent=2))
    print("Nothing was sent.")


def cmd_apply(a):
    hour, minute, enabled = parse_alarm(a)
    wid = wakeup_id()
    inst = get_instance(wid)
    if not BACKUP.exists():
        BACKUP.write_text(json.dumps(inst, indent=2))
        print(f"Backed up the original to {BACKUP}")
    body = {"enabled": enabled, "configuration": patched(inst, hour, minute)}
    print(json.dumps(v2("PUT", f"behavior_instance/{wid}", body), indent=2))
    after = get_instance(wid)
    want = dict(inst, enabled=enabled, configuration=body["configuration"])
    changed = sorted(k for k in set(want) | set(after) if want.get(k) != after.get(k))
    print(f"Read back: enabled={after['enabled']} when={json.dumps(after['configuration']['when'])}")
    print("Fields that differ from what was expected:", changed or "none")


def cmd_restore(_):
    if not BACKUP.exists():
        sys.exit("No backup to restore.")
    inst = json.loads(BACKUP.read_text())
    v2("PUT", f"behavior_instance/{inst['id']}",
       {"enabled": inst["enabled"], "configuration": inst["configuration"]})
    after = get_instance(inst["id"])
    if after["configuration"] != inst["configuration"] or after["enabled"] != inst["enabled"]:
        sys.exit(f"Restore did not match. The backup is still at {BACKUP}")
    BACKUP.unlink()
    print("Restored, verified, backup removed.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("discover", cmd_discover), ("pair", cmd_pair), ("list", cmd_list),
                     ("restore", cmd_restore)):
        sub.add_parser(name).set_defaults(fn=fn)
    p = sub.add_parser("use")
    p.add_argument("id")
    p.set_defaults(fn=cmd_use)
    for name, fn in (("plan", cmd_plan), ("apply", cmd_apply)):
        p = sub.add_parser(name)
        p.add_argument("time")
        p.add_argument("state", choices=["on", "off"])
        p.set_defaults(fn=fn)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()

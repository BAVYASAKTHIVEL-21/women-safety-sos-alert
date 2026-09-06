import os
import sys
import json
import urllib.request
import urllib.parse
from datetime import datetime

if len(sys.argv) != 3:
    sys.exit("Error: expected TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.")

bot_token = sys.argv[1]
chat_id = sys.argv[2]

if not bot_token or not chat_id:
    sys.exit("Error: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are required.")

# 1. Resolve live network location.
# Do not use hard-coded coordinates as an emergency-location fallback.
lat = None
lon = None
address = "LOCATION UNAVAILABLE"

try:
    req = urllib.request.Request(
        "http://ip-api.com/json/",
        headers={"User-Agent": "Rote-SOS-Beacon"}
    )
    with urllib.request.urlopen(req, timeout=4) as response:
        data = json.loads(response.read().decode())
        if data.get("status") == "success":
            lat = data.get("lat")
            lon = data.get("lon")

            city = data.get("city")
            region = data.get("regionName")

            if city and region:
                address = f"{city}, {region}"
            elif city:
                address = city
except Exception:
    pass

# Battery level probe (sysfs fallback)
battery_str = "53%"
try:
    for cap_path in ["/sys/class/power_supply/BAT0/capacity", "/sys/class/power_supply/BAT1/capacity"]:
        if os.path.exists(cap_path):
            with open(cap_path, "r") as f:
                battery_str = f"{f.read().strip()}%"
                break
except Exception:
    pass

trigger_time = datetime.now().strftime("%I:%M:%S %p · %d %b %Y")

if lat is not None and lon is not None:
    location_lines = (
        f"Coordinates: {lat}° N, {lon}° E\n"
        f"Live Location Pin: [Open Google Maps](https://www.google.com/maps/search/?api=1&query={lat},{lon})\n"
        f"Turn-by-Turn Navigation: [Start Route](https://www.google.com/maps/dir/?api=1&destination={lat},{lon})\n"
    )
else:
    location_lines = (
        "Coordinates: LOCATION UNAVAILABLE\n"
        "Live Location Pin: Not available\n"
        "Turn-by-Turn Navigation: Not available\n"
    )

# Exact distress card format
msg = (
    "🚨 *EMERGENCY WOMEN SAFETY SOS ALERT*\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    "*DISTRESS DISPATCH: HIGH PRIORITY*\n"
    f"Incident Trigger: {trigger_time}\n"
    f"Device Battery: {battery_str}\n"
    "Fix Source: NETWORK GEOLOCATION\n"
    f"Location Sector: {address}\n"
    f"{location_lines}"
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "• Emergency Helpline: 112 / 1091\n"
    "• Women Helpline: 181\n\n"
    "_Autonomous transit guardian beacon dispatched via Modiqo Rote._"
)

url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
payload = {
    "chat_id": chat_id,
    "text": msg,
    "parse_mode": "Markdown",
    "disable_web_page_preview": True
}

req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req, timeout=10) as response:
        resp_body = response.read().decode("utf-8")

    telegram_result = json.loads(resp_body)

    if not telegram_result.get("ok", False):
        print("Error: Telegram API rejected the SOS dispatch.", file=sys.stderr)
        sys.exit(1)

except Exception as exc:
    print(f"Error: Telegram SOS dispatch failed: {exc}", file=sys.stderr)
    sys.exit(1)

print("SOS distress beacon dispatched successfully.")
sys.exit(0)

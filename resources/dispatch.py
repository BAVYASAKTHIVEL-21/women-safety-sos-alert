import os
import sys
import json
import time
import urllib.request
import subprocess
import select
from datetime import datetime

def detect_battery_status():
    # 1. PowerShell CIM check on Windows Host from WSL
    try:
        ps_cmd = "(Get-CimInstance Win32_Battery | Measure-Object -Property EstimatedChargeRemaining -Average).Average"
        proc = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            timeout=4
        )
        val = proc.stdout.strip()
        if proc.returncode == 0 and val and val.isdigit():
            return f"{val}%"
    except Exception:
        pass

    # 2. Linux sysfs
    try:
        base = "/sys/class/power_supply"
        if os.path.exists(base):
            for entry in os.listdir(base):
                cap_path = os.path.join(base, entry, "capacity")
                if os.path.isfile(cap_path):
                    with open(cap_path, "r") as f:
                        cap = f.read().strip()
                        if cap:
                            return f"{cap}%"
    except Exception:
        pass

    return "100% (AC / Wall Power)"

def reverse_geocode(lat, lng):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json"
        req = urllib.request.Request(url, headers={"User-Agent": "WomenSafetySOS/0.3.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("display_name")
    except Exception:
        return None

def detect_live_location():
    # Hardware / Wi-Fi Triangulation via Windows host
    try:
        ps_cmd = (
            "Add-Type -AssemblyName System.Device; "
            "$w = New-Object System.Device.Location.GeoCoordinateWatcher; "
            "$w.Start(); "
            "$t = 0; "
            "while ($w.Status -ne 'Ready' -and $t -lt 30) { Start-Sleep -Milliseconds 100; $t++ }; "
            "if ($w.Position.Location.IsUnknown) { exit 1 }; "
            "$loc = $w.Position.Location; "
            "@{ lat = $loc.Latitude; lng = $loc.Longitude; acc = $loc.HorizontalAccuracy } | ConvertTo-Json -Compress"
        )
        proc = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            timeout=5
        )
        if proc.returncode == 0 and proc.stdout.strip():
            data = json.loads(proc.stdout.strip())
            lat = str(round(float(data["lat"]), 6))
            lng = str(round(float(data["lng"]), 6))
            acc = round(float(data.get("acc", 30)), 1)
            address = reverse_geocode(lat, lng)
            sector = address if address else f"±{acc}m Accuracy Fix"
            return lat, lng, "DEVICE HARDWARE / WI-FI TRIANGULATION", sector
    except Exception:
        pass

    # Dynamic Network Geolocation
    try:
        req = urllib.request.Request(
            "http://ip-api.com/json/?fields=status,country,regionName,city,district,lat,lon,query",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("status") == "success":
                lat = str(data["lat"])
                lng = str(data["lon"])
                district = data.get("district", "")
                city = data.get("city", "Unknown City")
                region = data.get("regionName", "Unknown Region")
                sector = f"{district}, {city}" if district else f"{city}, {region}"
                return lat, lng, "DYNAMIC NETWORK FIX", sector
    except Exception:
        pass

    return None, None, None, None

def send_telegram(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("ok", True)
    except Exception as e:
        print(f"Telegram error: {e}", file=sys.stderr)
        return False

def build_distress_card(alert_title, lat, lng, fix_type, sector, battery, is_escalation=False):
    timestamp = datetime.now().strftime("%I:%M:%S %p · %d %b %Y")
    maps_url = f"https://maps.google.com/?q={lat},{lng}"
    nav_url = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}"

    status_tag = "⚠️ <b>AMBER ALERT: MISSED TRANSIT CHECK-IN</b>" if is_escalation else "⚠️ <b>DISTRESS DISPATCH: HIGH PRIORITY</b>"

    return (
        f"🚨 <b>{alert_title}</b> 🚨\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{status_tag}\n"
        f"⏱ <b>Incident Trigger:</b> <code>{timestamp}</code>\n"
        f"🔋 <b>Device Battery:</b> <code>{battery}</code>\n"
        f"📡 <b>Fix Source:</b> <code>{fix_type}</code>\n"
        f"📍 <b>Location Sector:</b> {sector}\n"
        f"🧭 <b>Coordinates:</b> <code>{lat}° N, {lng}° E</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "• <b>Emergency Helpline:</b> <code>112 / 1091</code>\n"
        "• <b>Women Helpline:</b> <code>181</code>\n\n"
        f"🗺️ <b>Live Location Pin:</b> <a href=\"{maps_url}\">[Open Google Maps]</a>\n"
        f"🚗 <b>Turn-by-Turn Navigation:</b> <a href=\"{nav_url}\">[Start Route]</a>\n\n"
        "🛡️ <i>Autonomous transit guardian beacon dispatched via Modiqo Rote.</i>"
    )

def run():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    mode = os.environ.get("MODE", "instant").strip().lower()
    watch_minutes = int(os.environ.get("WATCH_MINUTES", "15"))

    if not token or not chat_id:
        print("Error: Missing required TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID.", file=sys.stderr)
        return False

    lat, lng, fix_type, sector = detect_live_location()
    if not lat or not lng:
        print("Error: Could not resolve dynamic location.", file=sys.stderr)
        return False

    battery = detect_battery_status()

    # --- MODE 1: INSTANT SOS DISPATCH ---
    if mode != "watch":
        card = build_distress_card("EMERGENCY WOMEN SAFETY SOS ALERT", lat, lng, fix_type, sector, battery, is_escalation=False)
        return send_telegram(token, chat_id, card)

    # --- MODE 2: CADENCE WATCHER (DEAD-MAN SWITCH) ---
    start_time = datetime.now().strftime("%I:%M:%S %p")
    start_msg = (
        "🛡️ <b>TRANSIT CADENCE SENTINEL ACTIVATED</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱ <b>Trip Started:</b> <code>{start_time}</code>\n"
        f"⏳ <b>Expected Window:</b> <code>{watch_minutes} minutes</code>\n"
        f"🔋 <b>Initial Battery:</b> <code>{battery}</code>\n"
        f"📍 <b>Departure Area:</b> {sector}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Guardian monitoring active. If commuter does not confirm check-in within window, live distress beacon triggers automatically.</i>"
    )
    send_telegram(token, chat_id, start_msg)
    print(f"\n[CADENCE WATCHER ACTIVE] Monitoring transit for {watch_minutes} minutes.")
    print("Press ENTER at any time to confirm safe arrival...\n")

    timeout_sec = watch_minutes * 60
    start_epoch = time.time()
    confirmed_safe = False

    while (time.time() - start_epoch) < timeout_sec:
        # Non-blocking terminal input check
        rlist, _, _ = select.select([sys.stdin], [], [], 2.0)
        if rlist:
            sys.stdin.readline()
            confirmed_safe = True
            break
        # Print progress every 15s
        elapsed = int(time.time() - start_epoch)
        rem = timeout_sec - elapsed
        mins, secs = divmod(rem, 60)
        sys.stdout.write(f"\rSentinel Active: {mins:02d}m {secs:02d}s remaining before auto-escalation...")
        sys.stdout.flush()

    print("")
    if confirmed_safe:
        arrival_time = datetime.now().strftime("%I:%M:%S %p")
        end_battery = detect_battery_status()
        safe_msg = (
            "✅ <b>SAFE ARRIVAL CONFIRMED</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏱ <b>Arrived at:</b> <code>{arrival_time}</code>\n"
            f"🔋 <b>Battery Remaining:</b> <code>{end_battery}</code>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "<i>Cadence watcher deactivated. No distress escalation required.</i>"
        )
        send_telegram(token, chat_id, safe_msg)
        print("Safe arrival logged and verified with guardian.")
        return True
    else:
        print("\n[DEAD-MAN'S SWITCH BREACHED] Initiating emergency escalation broadcast...")
        lat_now, lng_now, fix_type_now, sector_now = detect_live_location()
        lat_final = lat_now if lat_now else lat
        lng_final = lng_now if lng_now else lng
        fix_final = fix_type_now if fix_type_now else fix_type
        sector_final = sector_now if sector_now else sector
        battery_now = detect_battery_status()

        escalation_card = build_distress_card(
            "MISSED CHECK-IN: TRANSIT SOS ESCALATION",
            lat_final, lng_final, fix_final, sector_final, battery_now,
            is_escalation=True
        )
        return send_telegram(token, chat_id, escalation_card)

if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)

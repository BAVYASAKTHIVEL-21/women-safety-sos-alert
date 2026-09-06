# 🚨 Women Safety SOS Alert

An autonomous **women safety SOS and emergency distress-dispatch workflow** built with **Modiqo Rote**.

The Play is designed for situations where a woman may be **travelling alone, commuting after dark, or working late-night/night-shift hours** and needs to trigger an emergency notification to a designated responder.

Instead of being a standalone script, the project is packaged as a versioned, inspectable **Rote Play** with declared parameters, execution steps, presentation output, and registry identity.

---

## 🎯 What It Does

The Women Safety SOS Alert Play performs the following workflow:

```text
Runtime Credentials
        │
        ▼
┌─────────────────────────┐
│   Rote Execution Layer  │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Launch SOS Dispatcher   │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Resolve Available       │
│ Network Location        │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Capture Battery Status  │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Build Emergency         │
│ Distress Card           │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Dispatch Through        │
│ Telegram Bot API        │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Verify Telegram API     │
│ Accepted the Message    │
└────────────┬────────────┘
             │
             ▼
       Rote Presentation
```

The important part is that the Play does **not simply assume that an alert was delivered**.

The dispatcher checks the Telegram API response and exits successfully only when Telegram confirms the request was accepted. Rote then evaluates the actual process outcome and presents either a successful dispatch or a failure.

---

# 🧠 Why Rote?

Rote turns a repeatable workflow into a **versioned, inspectable and runnable Play**.

A traditional script might require someone to:

1. Clone the repository.
2. Install dependencies.
3. Understand the code.
4. Configure environment variables.
5. Execute the correct script.
6. Interpret the result.

With a published Rote Play, the Play itself becomes the reusable method.

```text
PLAY URI
   │
   ├── Identity
   ├── Parameters
   ├── Requirements
   ├── Access declarations
   ├── Execution steps
   ├── Presentation
   └── Version
```

Rote supports inspecting a Play before execution and running it directly from its canonical URI. Published versions can also be pinned for reproducibility.

---

# ⚙️ How This Play Uses Rote

The project is implemented as a Rote Play with:

* **Typed runtime parameters**
* **Sequential execution**
* **Process-based execution**
* **Presentation output**
* **Runtime credential injection**
* **Execution-result inspection**
* **Versioned registry publication**

The core execution step launches:

```text
python3 resources/sos_dispatcher.py
```

with the Telegram credentials supplied as runtime parameters.

The credentials are therefore not hard-coded into the Play source.

---

# 🔐 Runtime Credentials

The Play expects two runtime parameters:

| Parameter            | Purpose                            |
| -------------------- | ---------------------------------- |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot API authentication    |
| `TELEGRAM_CHAT_ID`   | Destination responder chat/channel |

These values should be supplied at runtime.

**Never commit Telegram credentials, API tokens, passwords, or other secrets to this repository.**

Example:

```bash
rote play run <PLAY_URI> \
  TELEGRAM_BOT_TOKEN="$TELEGRAM_BOT_TOKEN" \
  TELEGRAM_CHAT_ID="$TELEGRAM_CHAT_ID"
```

Use your own secure runtime secret mechanism or shell variables.

---

# 📍 Location Handling

The dispatcher attempts to resolve the available network location at execution time.

When successful, the emergency message can contain:

* Location sector
* Latitude
* Longitude
* Google Maps location link
* Google Maps navigation link

If network geolocation cannot be resolved, the Play does **not invent coordinates**.

Instead, the alert explicitly reports:

```text
Coordinates: LOCATION UNAVAILABLE
Live Location Pin: Not available
Turn-by-Turn Navigation: Not available
```

This is intentional: an emergency workflow should expose missing information rather than present a fabricated location as real.

---

# 🔋 Battery Information

The dispatcher also attempts to capture the available device battery state.

The resulting emergency card includes the battery information so responders have additional context about the device's current state.

---

# 🚨 Emergency Alert

The generated Telegram message contains information such as:

```text
🚨 EMERGENCY WOMEN SAFETY SOS ALERT

DISTRESS DISPATCH: HIGH PRIORITY

Incident Trigger: <timestamp>
Device Battery: <battery status>
Fix Source: <location source>
Location Sector: <location>

Coordinates: <coordinates>
Live Location Pin: <maps link>
Turn-by-Turn Navigation: <navigation link>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Emergency Helpline: 112 / 1091
• Women Helpline: 181
```

The exact available location fields depend on what the runtime environment can resolve.

---

# 📡 Telegram Dispatch Verification

The dispatcher sends the emergency message through the Telegram Bot API.

The workflow does not treat a completed HTTP request alone as proof of success.

The response is parsed and the Telegram API's `ok` field is checked.

Conceptually:

```text
Telegram request
      │
      ▼
Telegram API response
      │
      ├── ok = true
      │       │
      │       ▼
      │    Dispatch SUCCESS
      │
      └── ok = false
              │
              ▼
         Dispatch FAILED
```

If Telegram rejects the dispatch or the request encounters an error, the dispatcher exits with a failure status.

Rote then receives that actual process outcome and reports the failure instead of displaying a false "success" message.

---

# 🧩 Project Structure

```text
women-safety-sos-alert/
│
├── main.ts
├── deps.toml
│
└── resources/
    ├── dispatch.py
    ├── sos_dispatcher.py
    │
    └── presentation-fixtures/
        ├── dispatch_sos.yaml
        ├── dispatch_sos.stdout.txt
        └── dispatch_sos.stderr.txt
```

### `main.ts`

The Rote Play contract.

It defines:

* Play metadata
* Version
* Parameters
* Output contract
* Execution step
* Presentation logic

### `resources/sos_dispatcher.py`

The actual emergency-dispatch process.

It handles:

* Runtime Telegram credentials
* Network geolocation
* Battery information
* Emergency message generation
* Telegram API communication
* Telegram response validation

### `resources/dispatch.py`

An additional dispatcher implementation retained in the repository for development/reference purposes.

It is not the active process invoked by the current Play entry point.

### `resources/presentation-fixtures/`

Presentation fixtures used by Rote to represent the process execution result during presentation/testing.

---

# 🧪 Validate the Play

From the project directory:

```bash
rote play lint main.ts
```

A successful lint confirms that the Play contract, presentation, step references and declared structure satisfy Rote's validation requirements.

---

# ▶️ Run Locally

After configuring your runtime credentials:

```bash
rote play run main.ts \
  TELEGRAM_BOT_TOKEN="$TELEGRAM_BOT_TOKEN" \
  TELEGRAM_CHAT_ID="$TELEGRAM_CHAT_ID"
```

You can also request structured output:

```bash
rote play run main.ts \
  TELEGRAM_BOT_TOKEN="$TELEGRAM_BOT_TOKEN" \
  TELEGRAM_CHAT_ID="$TELEGRAM_CHAT_ID" \
  --output=json
```

Rote supports human-readable, summary, and machine-readable JSON result modes.

---

# 🔎 Inspect the Published Play

Before running a published Play, inspect its contract:

```bash
rote play inspect https://play.modiqo.ai/bavya21/women-safety-sos-alert
```

This allows you to review the Play's identity, parameters, access requirements and other declared information before execution. Rote specifically recommends the inspect-before-run workflow for understanding what a Play reaches and requires.

---

# 🌐 Try the Published Play

### Latest release

```bash
rote play run https://play.modiqo.ai/bavya21/women-safety-sos-alert
```

The versionless URI follows the latest released version.

### Pinned release

Current published release:

```text
https://play.modiqo.ai/bavya21/women-safety-sos-alert@1.2.0
```

Run the exact published version:

```bash
rote play run https://play.modiqo.ai/bavya21/women-safety-sos-alert@1.2.0
```

Rote's documentation distinguishes these two forms: a versionless URI floats to the newest release, while a version-pinned URI identifies an immutable release.

### Play URI

**https://play.modiqo.ai/bavya21/women-safety-sos-alert**

---

# 🔄 How a Rote Play Travels

The general Rote lifecycle is:

```text
CREATE
  │
  ▼
VALIDATE
  │
  ▼
RELEASE
  │
  ▼
PUBLISH
  │
  ▼
REGISTRY
  │
  ▼
INSPECT
  │
  ▼
RUN
```

A published Play carries its executable method, presentation, declared parameters, requirements, ownership and version identity.

The canonical URI becomes the portable handoff point for the Play.

That means someone can receive:

```text
https://play.modiqo.ai/bavya21/women-safety-sos-alert
```

and use the URI to inspect or execute the published workflow without needing to rediscover how the method works.

---

# 🛡️ Safety & Limitations

This project is a **technical emergency-notification workflow**, not a replacement for emergency services, professional security systems, or guaranteed device-level location services.

Important limitations include:

* Network geolocation may be unavailable or inaccurate.
* Device hardware location is not guaranteed by the current active dispatcher.
* Telegram availability depends on network connectivity and Telegram service availability.
* Battery information depends on what the execution environment exposes.
* A Telegram API acceptance response confirms that Telegram accepted the message request; it does not guarantee that a human responder has read or acted on the alert.
* Emergency helpline numbers and local emergency procedures should always be independently verified for the deployment location.

For real-world deployment, the workflow should be tested against the intended hardware, network environment, responder configuration, and emergency-response procedures.

---

# 🚀 Project Goal

The goal is to demonstrate how **Rote can turn an emergency-response workflow into a reusable, inspectable and versioned Play**.

The broader idea is:

```text
Emergency intent
      ↓
Repeatable workflow
      ↓
Rote Play
      ↓
Versioned execution
      ↓
Verified result
      ↓
Reusable emergency method
```

Rather than simply writing another script, the project packages the workflow as an operational method that can be inspected, executed and shared through a canonical Play URI.

---

# 📌 Current Version

```text
Version: 1.2.0
Status: Released
Visibility: Public
Owner: bavya21
```

---

# 🔗 Links

**GitHub**

https://github.com/BAVYASAKTHIVEL-21/women-safety-sos-alert

**Latest Rote Play**

https://play.modiqo.ai/bavya21/women-safety-sos-alert

**Pinned Rote Play — v1.2.0**

https://play.modiqo.ai/bavya21/women-safety-sos-alert@1.2.0

---

## 💡 Built With

* **Modiqo Rote**
* **Python**
* **TypeScript**
* **Telegram Bot API**
* **Google Maps links**
* **Network geolocation**

---

## ⚠️ Important

Do not store real Telegram bot tokens or responder credentials in Git.

Supply secrets at runtime and rotate credentials immediately if a token is accidentally exposed.

/**
 * @rote-frontmatter
 * ---
 * name: women-safety-sos-alert
 * description: |
 *   Autonomous women safety SOS and distress-dispatch workflow built to help women travelling alone, commuting after dark, and working late-night or night-shift hours. Rote executes the workflow sequentially by securely receiving Telegram credentials as runtime parameters, launching the SOS dispatcher as an isolated process, resolving the available network location, capturing device battery status, generating a high-priority distress card with incident time, location, coordinates, navigation links, and emergency helplines, and dispatching the alert through Telegram to designated responders. Rote then evaluates the actual process execution result and reports success only when the Telegram API confirms that the emergency alert was accepted.
 * source: https://github.com/BAVYASAKTHIVEL-21/women-safety-sos-alert
 * tags:
 * - safety
 * - emergency
 * - sos
 * - women-safety
 * - night-shift
 * - emergency-response
 * - geolocation
 * - telegram
 * - telemetry
 * - incident-dispatch
 * metadata:
 *   rote_version: 0.2.0
 *   version: 1.2.0
 *   status: released
 *   kind: atomic
 *   flow_type: sequential
 *   execution_model: steps_with_presentation
 *   format: typescript
 *   requires_endpoints: []
 *   requires_sessions: false
 *   discoverability:
 *     tags:
 *     - safety
 *     - emergency
 *     - sos
 *     - women-safety
 *     - night-shift
 *     - emergency-response
 *     - geolocation
 *     - telegram
 *     - telemetry
 *     - incident-dispatch
 * presentation_fixtures:
 *   dispatch_sos: resources/presentation-fixtures/dispatch_sos.yaml
 * parameters:
 * - name: TELEGRAM_BOT_TOKEN
 *   param_type: string
 *   required: true
 *   secret: true
 *   masked: true
 *   description: Telegram Bot API authentication token supplied securely at runtime
 * - name: TELEGRAM_CHAT_ID
 *   param_type: string
 *   required: true
 *   secret: true
 *   masked: true
 *   description: Verified Telegram responder chat or channel ID supplied at runtime
 * output:
 *   type: object
 *   description: Verified SOS emergency-dispatch outcome
 *   properties:
 *     status:
 *       type: string
 *       description: Actual dispatch outcome reported by the Rote execution
 *     alert_level:
 *       type: string
 *       description: Severity classification of the emergency SOS alert
 *     channel:
 *       type: string
 *       description: Emergency alert delivery channel
 *     dispatched_at:
 *       type: string
 *       description: ISO timestamp recorded when a successful dispatch is reported
 *     error:
 *       type: string
 *       description: Dispatch failure reason when the emergency alert could not be delivered
 * steps:
 *   dispatch_sos:
 *     type: process.exec
 *     argv:
 *     - python3
 *     - resources/sos_dispatcher.py
 *     - $TELEGRAM_BOT_TOKEN
 *     - $TELEGRAM_CHAT_ID
 *     timeout_ms: 30000
 * ---
 */

const { FlowOutput, loadPresentationContext } = await import("__ROTE_PRESENTATION_SDK__");

const out = new FlowOutput();
const ctx = await loadPresentationContext();

const dispatch = ctx.step("dispatch_sos");

if (dispatch.outcome.status === "completed") {
  out.summary(
    "Women Safety SOS distress beacon dispatched successfully via Telegram."
  );

  out.human(
    "🚨 EMERGENCY WOMEN SAFETY SOS ALERT\n" +
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n" +
    "DISTRESS DISPATCH: HIGH PRIORITY\n" +
    "Status: Telegram dispatch confirmed."
  );

  out.result({
    status: "dispatched",
    alert_level: "critical",
    channel: "telegram",
    dispatched_at: new Date().toISOString()
  });
} else if (dispatch.outcome.status === "failed") {
  const failure = dispatch.outcome.output;
  const diagnostic = failure.diagnostic;

  out.summary(
    "Women Safety SOS distress beacon dispatch FAILED."
  );

  out.human(
    "🚨 EMERGENCY WOMEN SAFETY SOS ALERT\n" +
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n" +
    "DISTRESS DISPATCH: HIGH PRIORITY\n" +
    "Status: DISPATCH FAILED\n" +
    `Reason: ${failure.message}` +
    (diagnostic?.stderr ? `\nDetails: ${diagnostic.stderr}` : "")
  );

  out.result({
    status: "failed",
    alert_level: "critical",
    channel: "telegram",
    error: failure.message
  });
} else {
  out.summary(
    `Women Safety SOS dispatch was not completed (${dispatch.outcome.status}).`
  );

  out.human(
    "🚨 EMERGENCY WOMEN SAFETY SOS ALERT\n" +
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n" +
    "DISTRESS DISPATCH: HIGH PRIORITY\n" +
    `Status: ${dispatch.outcome.status.toUpperCase()}`
  );

  out.result({
    status: dispatch.outcome.status,
    alert_level: "critical",
    channel: "telegram"
  });
}

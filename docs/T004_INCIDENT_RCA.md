# T004 Incident RCA

RCA for a controlled incident I built and investigated on terminal T004,
as part of testing the transaction simulator and practicing incident
investigation the way I'd actually do it at work.

## Summary

On 2026-08-09, terminal T004 had a run of 12 consecutive System_Error
(response code 96) transactions between 20:17 and 20:28, before recovering
on its own. No other terminals showed anything unusual in the same window.

## Impact

12 transactions across 4 merchants failed with a technical error
(System_Error), as opposed to a normal business decline like insufficient
funds or an expired card. Anyone paying at T004 during that ~12-minute
window would have had their transaction fail; every other terminal and
merchant was unaffected.

## Timeline

- 20:15–20:16 — 2 normal Approved transactions on T004
- 20:17–20:28 — 12 consecutive System_Error transactions on T004
- 20:29 — T004 goes back to Approved, incident resolves on its own
- Total duration: ~12 minutes

## Findings

- Isolated entirely to T004 — no other terminal showed an elevated error
  rate in the same window
- Spread evenly across 4 merchants — rules out a merchant-specific cause
- All 12 transactions had unique STAN and RRN values — genuine
  independent transactions, not retries or duplicates
- PAN and amounts were unremarkable
- Since the problem stayed on one terminal instead of spreading across
  multiple terminals routing through the same issuer, an issuer-side
  outage looks unlikely

## Root cause (hypothesis)

Most likely a terminal-level connectivity or session issue at T004 — a
dropped or degraded connection between the terminal and the
acquirer/switch (network blip, terminal reboot, session timeout, that
kind of thing). This fits the data better than a certificate/licensing
failure or an issuer-side problem, since those would usually affect
multiple terminals sharing the same issuer, or would show up as a
different response code (91 Issuer_Unavailable) rather than a
terminal-specific 96. The clean, sudden recovery at 20:29 also points
toward a transient connectivity blip rather than something like an
expired certificate, which wouldn't normally fix itself without someone
intervening.

## Recommended action

- Check T004's network/connectivity logs (or terminal session/heartbeat
  logs, in a real environment) for the 20:15–20:30 window for drops or
  reconnects
- Confirm whether T004 was rebooted, restarted, or reconnected around
  20:29
- Keep an eye on T004 going forward — if this pattern repeats, escalate
  to field support/terminal maintenance for a proper health check
- No customer or card-level action needed — nothing here points to a
  card or merchant issue
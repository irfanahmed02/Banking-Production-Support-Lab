# Log Investigation Notes

This document captures a Linux log-investigation exercise performed against
`logs/api.log`, using `grep` to isolate, contextualize, and reason about
events recorded by the API's application logging. It also captures
design observations that came out of the investigation, worth carrying
into future iterations of the project.

---

## 1. Investigation: isolating a real incident from routine noise

The log file at the time of investigation contained 35 lines: 17 `INFO`,
18 `WARNING`, 0 `CRITICAL`. A plain `grep "WARNING"` would have returned 18
lines mostly routine, expected traffic (not-found lookups, invalid path
parameters, missing POST fields, invalid PAN/currency). Buried among them
was exactly one line representing a genuine technical failure:

```
grep "System_Error" logs/api.log
2026-08-15 21:34:53,210 - WARNING - Transaction failed: ID=1150, STAN=001112, RRN=000000001112, RESPONSE=System_Error
```

Searching for the specific term (`System_Error`) rather than the broad
severity level (`WARNING`) isolated the one line that mattered, instead of
requiring a manual read-through of 18 candidates.

### Contextualizing the incident

```
grep -4 "System_Error" logs/api.log
```

returned 4 lines before and 4 lines after the match, showing:

- Several unrelated `POST /transactions` validation failures immediately
  before the incident (missing `merchant_id`, invalid currency, unknown
  PAN)
- The `System_Error` transaction at `21:34:53`
- A successful `Approved` transaction ~2 minutes later
- A normal `Declined` (Insufficient_Funds) transaction shortly after that

### Conclusion

The surrounding validation failures are **coincidental, unrelated traffic**,
not a contributing cause — they fail with HTTP 422 before the endpoint code
ever reaches the point where a `response_code` (and thus a possible
`System_Error`) is assigned, so there is no code path connecting them to
the incident.

A single isolated `System_Error`, with normal `Approved` transactions both
before and after, does not indicate a systemic or ongoing problem. It looks
like a transient blip rather than an outage. In a real environment, the
next step would be to check actual network/infrastructure logs around
21:34 PM and trace the transaction's full payment-cycle path to pinpoint
where the drop occurred — data this simulated project doesn't have access
to, but which a real production investigation would pursue next.

---

## 2. Investigation: a duplicate-transaction pattern

Cross-checking the database around the same time window surfaced a second,
separate pattern — two consecutive transactions with identical PAN,
merchant, terminal, and amount, six seconds apart:

| ID   | PAN                | Amount  | STAN   | Response            | Time              |
|------|--------------------|---------|--------|----------------------|-------------------|
| 1151 | 52222*******2222   | 714.750 | 001113 | Approved             | 21:36:31.737276+03 |
| 1152 | 52222*******2222   | 714.750 | 001114 | Insufficient_Funds   | 21:36:37.428077+03 |

**Analysis:** the second attempt correctly failed with Insufficient_Funds,
consistent with the first transaction having already deducted the balance
on the same card. The system behaved correctly given the inputs.

**Important caveat:** this pattern most likely reflects manual/Postman
retesting during development (the same request resubmitted), not real
customer retry behavior. There's no independent evidence (e.g. two
distinct terminal-side network requests) to support a "customer tried
twice" narrative — that would be speculation dressed as a finding. The
data supports "the system correctly declined a duplicate charge attempt
given insufficient remaining balance"; it does not support any claim about
*why* a second attempt occurred.

---

## 3. Design observation: WARNING severity conflates three different categories

Counting severities in the test log:

```
grep -ic "info" api.log       → 17
grep -ic "warning" api.log    → 18
grep -ic "critical" api.log   → 0
```

A near 1:1 ratio of WARNING to INFO would be a concerning signal in a real
production system — but in this log, it isn't, because the current
logging conflates three meaningfully different categories under one
`WARNING` severity:

1. **Malformed/invalid client requests** — missing required fields, wrong
   data types (e.g. a non-integer transaction ID). These represent bad
   client-side integration, not customer behavior or system health.
2. **Normal business declines** — insufficient funds, expired card,
   unrecognized PAN. These are expected, healthy operation; a customer's
   card was legitimately declined.
3. **Would-be technical failures** — e.g. `System_Error`, `Issuer_Unavailable`.
   These are the only category that should actually inform "is the system
   healthy" in a monitoring/alerting context.

**Proposed improvement:** malformed requests (category 1) should ideally
be caught and rejected client-side — at the merchant/terminal integration
layer — before ever reaching the API. If a specific terminal is
*consistently* sending malformed requests (e.g. always missing
`terminal_id`), that points to a configuration or integration bug on that
terminal, and catching it locally reduces both wasted load on the
database and noise in the API's own logs.

This doesn't remove the need for server-side validation — a terminal could
be buggy, outdated, or compromised, so the API should never fully trust
client input. The goal is to reduce how *often* malformed requests occur
in the first place, not to eliminate the safety net.

**Possible follow-up (not yet implemented):** split logging severity
further, e.g. malformed requests and true technical failures at distinct
levels from ordinary business declines, so a WARNING/ERROR scan in
production reflects genuine system health rather than routine customer
outcomes mixed with integration bugs.

---

## 4. Logging gap found and fixed during this step

While reviewing the log, two cases were found to be silently unlogged: an
invalid-type path parameter (`/transactions/abc`) and a missing required
field on `POST /transactions`. Both are rejected by FastAPI's automatic
Pydantic validation *before* the endpoint function body ever executes, so
no `logging.x(...)` call inside any individual endpoint could ever catch
them.

**Fix:** a single global exception handler, registered once for the whole
app, intercepts every `RequestValidationError` regardless of which
endpoint triggered it:

```python
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    for err in exc.errors():
        field = err["loc"][-1] if err["loc"] else "unknown"
        logging.warning(f'path={request.url.path}, issue_field={field}, message={err["msg"]}')
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )
```

`err["loc"][-1]` (the last element of the location list) is used instead of
a fixed index, since the last element is always the actual field name
regardless of how deeply nested the validation error is — a fixed index
like `[1]` only happens to work for flat request bodies and simple path
parameters, and would break for nested models.

This closes the gap across every current and future endpoint at once,
rather than requiring per-endpoint logging for validation failures.

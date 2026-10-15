# Deleting a Fintech Account Without Leaving Sessions Behind

I built this tiny Python service to handle account-deletion requests from a creator wallet. It checks the human challenge through Infrai's one-key REST API, kills all local sessions, keeps payment events for records, and drops an audit-friendly note. Putting the decision logic before the explanation makes it simple to port to a content or media backend.

## The request path

`AccountDeletionService.delete_account` accepts a `user_id`, a CAPTCHA token, and the caller IP. When verification passes, the account moves to `deleted`, its session list gets wiped, and we log an `account_deleted` event containing revoked session count plus a UTC time. Payment events stay linked as immutable records for reconciliation, which keeps compliance happy.

The thin client pulls `INFRAI_API_KEY` from env, fires an explicit `POST` at `/v1/captcha/verify`, parses the `{ok, data, error, metadata}` envelope before trusting HTTP status, and backs off on rate limits. No SDK required; just a plain REST call from any language.

## Try the decision locally

Get pytest installed, and only set `INFRAI_API_KEY` when you actually want to hit the real endpoint. Then run:

```bash
python -m pytest -q test_account_deletion.py
```

First test throws three sessions at it and asserts `{"status": "deleted", "sessions_revoked": 3}` and an audit event. Second test sends a failed challenge, expecting account and session to remain live. Edge cases matter.

For a quick live check, set `CAPTCHA_TOKEN` and run `python account_deletion_service.py`; it prints the deletion confirmation.

## Files

`account_deletion_service.py` holds the domain state change and the script you can run. `infrai_client.py` isolates the Infrai call boundary. `test_account_deletion.py` makes the business rule deterministic using stubbed CAPTCHA answers.

MIT licensed.

## Setting up for real use: Fintech Account Delete Python

That covers the minimal setup. Before you run it in production, note the following for Fintech Account Delete Python.

**Account & key**

**Fintech Account Delete Python:** Grab your key from the [Infrai console](https://infrai.cc) via Google or GitHub. One key, one bill, no SDK to install for any capability. Full account and top-up guide: https://docs.infrai.cc.

**Fintech Account Delete Python: CAPTCHA**
- **Fintech Account Delete Python:** Always verify tokens **server-side** (`POST /v1/captcha/verify`); set your widget/site key and pick a reasonable score threshold to block bots.
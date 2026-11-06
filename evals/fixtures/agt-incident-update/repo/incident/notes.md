# Checkout outage, 2026-11-06 (on-call: Priya)

All times UTC.

- 09:12 Alert: checkout API 5xx rate 38%.
- 09:15 Priya paged, starts investigating.
- 09:24 Rolled back deploy 2026.11.06-1 (payment client upgrade). Error rate unchanged, so probably not the deploy.
- 09:31 payments-db connection pool exhausted (pgbouncer: "no more connections allowed"). Restarted pgbouncer.
- 09:47 5xx rate back to baseline (0.2%). Watching.

Impact: about 1,900 failed checkout attempts in the logs (09:12-09:47). Don't know yet how many customers retried successfully.

Root cause: NOT confirmed. Suspect the nightly reconciliation job (started 09:05, later than usual) holding connections open. Priya is checking its logs.

Deploy 2026.11.06-1 is still rolled back; re-deploy after the root cause is clear.

Next update: 13:00 UTC.

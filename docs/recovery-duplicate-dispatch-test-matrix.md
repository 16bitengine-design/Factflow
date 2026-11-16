# Recovery duplicate-dispatch test matrix

| Case | Expected watchdog behavior |
|---|---|
| Exact original slot reservation exists | Do not dispatch again |
| Immediate catch-up reservation is scheduled within 30 minutes after the missed slot | Treat it as the recovery for that slot; do not dispatch again |
| Catch-up reservation is incomplete | Fail closed and create an operational alert |
| Candidate reservation is outside the 30-minute window | Do not associate it with the missed slot |
| Candidate reservation is on another Kampala calendar day | Do not associate it with the missed slot |

The ledger's nested `buffer_posts.*.due_at` values remain the actual Buffer schedule times. The recovery association is only used to make the original missed slot idempotent.

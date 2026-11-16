# Missed-slot recovery idempotency

When the watchdog recovers a missed noon or evening slot, the production workflow may schedule the catch-up for a new time (normally at least twenty minutes after selection). The Buffer ledger therefore records the catch-up's actual `due_at`, which is later than the original slot.

The watchdog checks both the exact original slot and a same-day recovery reservation scheduled within the 30-minute grace window after that slot. A complete reservation with both platform post IDs suppresses another dispatch. An incomplete reservation remains fail-closed and is surfaced for inspection, avoiding duplicate public posts after partial Buffer success.

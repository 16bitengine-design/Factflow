# Publishing watchdog and missed-slot recovery

The publishing watchdog checks the noon and 18:00 Africa/Kampala slots. A future slot is eligible for recovery when it is more than five minutes and no more than thirty minutes away. A recently missed slot remains eligible for up to thirty minutes after its scheduled time.

Before dispatching production, the watchdog checks for an active production run and an exact slot reservation in `production/publishing-ledger.json`. A complete reservation with both YouTube and TikTok Buffer post IDs is treated as already scheduled. An incomplete reservation is deliberately blocked and reported rather than retried automatically, because one platform may already have accepted a post.

The watchdog also runs when its own recovery code or workflow definition is pushed to `main`. This provides an event-driven recovery check when a scheduled GitHub Actions event is delayed or dropped. It does not bypass the ledger, duplicate-run, or evidence safeguards.

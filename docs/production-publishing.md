# QuantaTale hands-off production publishing

QuantaTale selects, renders and schedules approved videos automatically. No daily video selection or manual entry of titles, descriptions, hashtags, content IDs, target channels or timestamps is required.

## Automatic schedule

The GitHub Actions workflow runs daily at:
- 12:00 Africa/Kampala: selects the approved video scheduled for 15:00.
- 18:00 Africa/Kampala: selects the approved video scheduled for 21:00.

GitHub cron uses UTC; these are 09:00 and 15:00 UTC respectively. The workflow can also be started manually; it still selects the next due approved item automatically.

## Production specifications

Each video JSON stores:
- Narration and voice.
- Post title, description and hashtags.
- Research source URLs.
- Content ID prefix and sequence suffix.
- Local publishing time and timezone.
- Editorial approval state.

Only entries with `editorial_approved: true` are eligible. Approval is a one-time editorial decision made before a video enters the automatic publishing queue. Unapproved entries are skipped.

## Automatic processing

For each run, QuantaTale:
1. Finds the next approved video whose publishing slot is within four hours.
2. Generates the unique content ID from the configured prefix, local date and suffix.
3. Reserves the content ID in `production/publishing-ledger.json` and commits that reservation before contacting external services.
4. Runs the full test suite, renders the selected specification, uploads the video to Cloudinary and schedules both configured Buffer channels.
5. Marks the ledger entry scheduled after Buffer confirms both posts.

The ledger prevents repeat scheduling. If a run fails after reservation—including a partial Buffer success—the entry remains reserved and is not retried automatically. Inspect Buffer and reconcile the ledger before any retry. This deliberately prefers preventing duplicate public posts over silently retrying an uncertain external operation.

## Current queue approvals

- Why Is the Sky Blue?: approved; 15:00 Africa/Kampala.
- Why Are Sunsets Red?: not yet approved; 21:00 Africa/Kampala. It is skipped until its final video has been reviewed and its approval flag is explicitly enabled.

## Publication and safety

- Posts are scheduled publicly to YouTube and TikTok through Buffer.
- Required GitHub repository secrets: `BUFFER_API_KEY`, `BUFFER_YOUTUBE_CHANNEL_ID`, `BUFFER_TIKTOK_CHANNEL_ID`, `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, and `CLOUDINARY_API_SECRET`.
- YouTube category defaults to Education (27), unless `BUFFER_YOUTUBE_CATEGORY_ID` is configured.
- GitHub Actions runtime, storage and artifact limits still apply. Kokoro model caching reduces repeated downloads but does not remove runner time limits.

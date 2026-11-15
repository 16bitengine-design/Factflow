# QuantaTale production publishing

The production workflow is separate from the Buffer integration-test workflow. The integration-test workflow always creates drafts. The production workflow creates publicly scheduled posts and must only be used after reviewing the exact video.

## Manual release procedure

1. Open Actions → QuantaTale production video scheduling → Run workflow.
2. Enter a unique content_id for the video. Never reuse an ID.
3. Enter due_at as an ISO-8601 timestamp with an explicit timezone offset. Uganda example: 2026-11-15T21:30:00+03:00.
4. Select YouTube, TikTok or both.
5. Check both approval boxes only after reviewing the exact video and caption.
6. Run the workflow and verify the returned Buffer post IDs and due times in Buffer.

The workflow runs pytest, renders with Kokoro, and uploads the MP4 to Cloudinary before scheduling through Buffer. YouTube privacy is set to public. Buffer uses customScheduled and dueAt in UTC.

## Safety

- The workflow is manual; there is no unattended cron schedule.
- Both editorial approval and public-scheduling confirmation are required.
- A workflow rerun is rejected to reduce accidental duplicate scheduling.
- Use a new unique content ID for each new video. Cloudinary's non-overwriting upload also rejects reuse of an existing production asset ID.
- If one platform schedules successfully and the other fails, inspect Buffer before taking any retry action. Do not rerun the same workflow.
- The workflow does not create drafts; it creates posts Buffer is expected to publish at the selected time.
- The existing buffer-draft-test.yml remains draft-only.

Buffer's official API documents mode customScheduled, schedulingType automatic, and dueAt for exact-time scheduling: https://developers.buffer.com/examples/create-scheduled-post.html

# QuantaTale production publishing

Production metadata is stored with each video specification. The workflow reads the saved title, caption, hashtags, unique content-ID prefix, local publishing time and timezone automatically.

## Release procedure

1. Open Actions → QuantaTale production video scheduling → Run workflow.
2. Select the video.
3. Review the selected video preview before release.
4. Check the single approval box and run the workflow.

No title, description, content ID, target channel or timestamp needs to be typed into GitHub Actions. The workflow publishes to both configured Buffer channels.

## Built-in schedule

- Why Is the Sky Blue?: 15:00 Africa/Kampala.
- Why Are Sunsets Red?: 21:00 Africa/Kampala.

If today's slot has already passed (or is less than five minutes away), the workflow automatically selects the next day's slot. Content IDs are generated from the configured prefix and scheduled local date.

## Safety and verification

- The workflow is manual and requires explicit editorial approval.
- It runs the full test suite and renders the selected production specification before upload.
- A workflow rerun is rejected to reduce accidental duplicates. If a run partially succeeds, inspect Buffer before taking any retry action.
- YouTube privacy is set to public. Buffer schedules both YouTube and TikTok posts.
- The separate Buffer integration-test workflow remains draft-only.
- Verify the returned Buffer post IDs and due times after each run.

Buffer scheduling uses customScheduled, schedulingType automatic and dueAt: https://developers.buffer.com/examples/create-scheduled-post.html

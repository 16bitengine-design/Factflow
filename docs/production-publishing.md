# QuantaTale hands-off production publishing

QuantaTale is designed to discover eligible topics, render narration-led videos in GitHub Actions, schedule them through Buffer, and verify the resulting platform posts without a daily manual production step.

## Daily publishing schedule

The target publishing times are **12:00 and 18:00 Africa/Kampala** every day.

GitHub Actions uses UTC. The production workflow and its independent watchdog check during the 30-minute preparation windows before each slot:
- 11:30–11:55 Africa/Kampala (08:30–08:55 UTC)
- 17:30–17:55 Africa/Kampala (14:30–14:55 UTC)

The production workflow selects the next available slot, renders the video, uploads it to the configured public media host, and schedules YouTube and TikTok through Buffer. Buffer performs the actual publication at the scheduled time. A successful workflow run or Buffer schedule response is **not** proof that a platform post has been published; the verification workflow checks the exact Buffer post IDs and records the final outcomes.

## Topic eligibility and evidence safeguards

Topics are eligible by default unless `publishing_enabled` is explicitly `false`. A topic is still blocked when:
- `source_passage_verification_required_before_publication` is `true`;
- a source has a `review_status` beginning with `source_lead_requires_human`;
- the production specification is malformed or cannot be rendered.

The `editorial_approved` field is retained as provenance but is not a universal publication gate. Automated claim extraction or assessment is not treated as complete fact verification. Evidence safeguards remain mandatory.

A topic cannot be used twice on the same Kampala calendar day. The publishing ledger reserves each content ID before external upload/scheduling so concurrent or repeated workflow runs do not create duplicate posts.

## Autonomous recovery

The publishing watchdog runs in the same preparation windows as production. It checks for an active production run and the exact slot's ledger entry:
- If a complete YouTube and TikTok Buffer post pair is already recorded as scheduled, it does nothing.
- If no reservation exists and no production run is active, it dispatches the production workflow automatically.
- If a reservation exists but the Buffer result is incomplete, it creates an operational GitHub issue and deliberately does not retry blindly. A timed-out request may have created a post even if the response was lost; automatic retry could duplicate public content.

For an operator-requested emergency run, the watchdog also exposes a manual `publish_now` input. That dispatches the production workflow in immediate mode, which selects an unused eligible topic and schedules it with enough lead time for rendering and upload. It does not bypass evidence safeguards or Buffer verification.

## Required repository configuration

The production workflow reads these GitHub Actions secrets:
- `BUFFER_API_KEY`
- `BUFFER_YOUTUBE_CHANNEL_ID`
- `BUFFER_TIKTOK_CHANNEL_ID`
- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`

Optional repository variable:
- `BUFFER_YOUTUBE_CATEGORY_ID` (defaults to Education, category 27)

The GitHub Actions token needs permission to update the publishing ledger. The watchdog also needs Actions write permission to dispatch the production workflow and Issues write permission to report unsafe partial outcomes.

## Operational limits

GitHub-hosted runners have time, CPU, memory, and artifact-retention limits. The workflow installs FFmpeg and uses CPU-based Kokoro TTS with cached model files where possible. Model downloads and video rendering can make a run take several minutes. Cloud media hosting and Buffer are external dependencies; their free tiers, quotas, terms, and availability can change. Keep the platform credentials configured as repository secrets, never commit them to the repository, and inspect failed workflow logs rather than assuming a post was created.

## Operational records

- `production/topic-library.json`: available production specifications and their enablement/evidence flags.
- `production/publishing-ledger.json`: unique reservations, Buffer post IDs, scheduled times, and verification outcomes.
- `buffer-production-publish.yml`: normal and immediate render/schedule execution.
- `publishing-watchdog.yml`: missing-run detection and safe recovery.
- `buffer-publication-verification.yml`: exact post verification and operational alerts.

The ledger is the source of truth for QuantaTale's recorded scheduling and verification state. Public publication must be confirmed from the platform-linked verification record.

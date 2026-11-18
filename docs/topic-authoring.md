# Automated topic authoring

QuantaTale writes its own new topics. No human approval step is involved; topics are accepted or discarded by automated gates.

## Pipeline (daily 01:30 UTC, or manual dispatch)
1. A language model proposes evergreen questions and candidate pages on registered publisher domains (`data/source_registry.json`).
2. Each page is fetched; unregistered, unreachable or too-short pages are dropped. At least **two independent publishers** must load.
3. The model writes a title, description, scene plan and a **script in its own words**, using only the fetched passages.
4. Automated gates (any failure discards the topic; it is never published):
   - every narration sentence cites a **verbatim quote** found in a fetched page (one opening question may be uncited);
   - every number in a sentence appears in its quote;
   - the script shares no run of 8 or more consecutive words with any source;
   - a second model pass must mark each sentence supported and report no conflicts;
   - a clickable title (20-70 characters, not a duplicate), a non-empty description, 60-170 words, 3-5 scenes.
5. Accepted specs are written to `production/specs/` and registered in the library with `passage_checked_supports_claim` and `review_method: automated_quote_grounding_and_model_entailment`.

These checks are automated and are **not complete fact verification**. Each spec says so in `source_assessment`.

## Free providers (tried in order)
1. **Groq** (`GROQ_API_KEY`)
2. **OVHcloud AI Endpoints** (anonymous, no key; very low rate limit)
3. **Cloudflare Workers AI** (`CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`)

A provider that is missing credentials, rate limited, down or returns unusable output is skipped. Free tiers, model names and endpoints can change; override with `GROQ_MODEL`, `GROQ_URL`, `OVH_MODEL`, `OVH_URL`, `CLOUDFLARE_MODEL`, `CLOUDFLARE_URL`. Limits apply per account or organization, not per key. Only public source text is sent. A local open-source model fallback is not implemented yet.

## Stock alert
After each run `quantatale topic-stock` counts never-used publishable topics. Fewer than 4 opens (once) the GitHub issue "QuantaTale topic stock is low". The authoring job fails visibly when every provider fails.

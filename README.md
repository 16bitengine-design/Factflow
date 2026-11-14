# QuantaTale

**KNOW MORE. SEE DIFFERENTLY.**

QuantaTale is a free, open-source, cloud-first production engine for turning reliable research into engaging narrated explainers, quick facts and educational videos across science, history, nature, technology, geography, health, engineering, mathematics and virtually any other subject.

Its signature presentation is **cinematic, code-generated holographic storytelling**: animated scientific diagrams, procedural 2D/3D scenes, simulations, luminous interfaces, motion graphics and visual effects. QuantaTale is designed to create its visuals with code and open-source tools—not stock footage or paid AI-video services.

## Brand identity

- **Name:** QuantaTale
- **Tagline:** KNOW MORE. SEE DIFFERENTLY.
- **Positioning:** Immersive, evidence-led explanations of fascinating facts, complex ideas and the world around us.
- **Personality:** Curious, intelligent, cinematic, clear and trustworthy.
- **Visual direction:** Deep midnight navy backgrounds, luminous cyan holographic elements, restrained violet accents, crisp white typography and a geometric QT-inspired symbol.
- **Content promise:** Make complex things easier to understand without compromising factual accuracy.

## Non-negotiable principles

- **Zero-cost core:** no paid APIs, subscriptions, credits or commercial generation services are mandatory.
- **Cloud-only execution:** production runs through GitHub Actions; no local rendering or installation is required.
- **Code-generated visuals:** scenes are created with open-source tools and project code.
- **Narration-first storytelling:** every video has a strong hook, clear explanation and memorable ending.
- **Evidence before publication:** factual claims must be traceable to reputable sources and reviewed before rendering.
- **Reproducible builds:** inputs, settings and outputs are versioned or recorded.
- **Honest limits:** free runners have time, storage and resource limits. QuantaTale must report these rather than promise unlimited production.

## Production flow

1. **Discover:** identify engaging topics and define the audience and learning objective.
2. **Research:** collect source-backed claims and preserve structured evidence.
3. **Assess:** examine publisher registration, source relevance, independent corroboration and uncertainty; require editorial review.
4. **Write:** prepare concise narration with a hook, explanation and memorable close.
5. **Plan scenes:** map each narration segment to an original explanatory visual.
6. **Generate voice:** use an open-source, cloud-runnable text-to-speech engine.
7. **Animate:** create 2D motion graphics and procedural 3D/holographic scenes with code.
8. **Assemble:** synchronize narration, visuals, captions and sound.
9. **Quality-check:** validate evidence status, timing, audio, captions, dimensions and render integrity.
10. **Export:** prepare platform-ready videos and publishing metadata for Shorts and longer formats.

## Cloud-only, zero-cost operating model

The initial execution target is GitHub Actions on GitHub-hosted runners. The repository prioritizes open-source tools and free public-repository runner capacity where available. Workflows must be efficient, avoid unnecessary repeated renders and respect free compute and storage limits.

**Important:** "100% free" means the core project must not require paid services or subscriptions. It does not mean unlimited compute, storage, bandwidth or guaranteed availability. GitHub and upstream projects can change their free-tier policies. QuantaTale will report resource limits clearly and fail safely when a job cannot complete.

No API keys or paid-provider credentials should be required for the core workflow.

## Repository layout

The current Python import package and legacy command remain `factflow` for compatibility with existing code and workflows. The supported product command is `quantatale`.

```text
.
├── .github/workflows/ci.yml
├── data/
│   ├── discovery_feeds.json
│   └── source_registry.json
├── examples/topics/why-the-sky-is-blue.json
├── src/factflow/
│   ├── __init__.py
│   ├── cli.py
│   ├── discovery.py
│   ├── fact_research.py
│   ├── research.py
│   └── topic.py
├── tests/
└── pyproject.toml
```

## Stage 1: project foundation

The first milestone established a Python package, a topic JSON specification, a command-line validator, automated tests and a GitHub Actions workflow.

## Stage 2: evidence and fact assessment

QuantaTale has a curated starting registry of reputable publishers, including scientific, government, health, historical, educational and statistical institutions. The registry is stored in `data/source_registry.json`.

Each factual claim records structured evidence:
- `publisher_id`: publisher identifier from the curated registry.
- `url`: page containing the evidence.
- `title`: source page title.
- `accessed_on`: date the source was reviewed.
- `evidence_summary`: editor's summary of the relevant material.
- `supports_claim`: set to `true` only after an editor confirms the source directly supports the claim.

Generate an evidence report:

```bash
quantatale research-report examples/topics/why-the-sky-is-blue.json
```

Add `--check-links` to check whether source URLs respond. A reachable page is not necessarily accurate, authoritative or relevant.

Evidence statuses are workflow signals, not truth scores. Even two independent registered publishers marked as supporting a claim do not automatically approve it. An editor must read the cited material, check wording and context, and approve the claim before publication.

## Stage 3: automated topic discovery

QuantaTale collects candidate story leads from a curated set of public RSS and Atom feeds. The configuration is in `data/discovery_feeds.json`; every feed and article URL must match the registered domains for its publisher.

Run discovery:

```bash
quantatale discover --limit 30 --output build/discovery-candidates.json
```

The GitHub Actions workflow runs this command automatically and uploads JSON reports as an artifact named `quantatale-research-reports` (retained for seven days). Open the repository's **Actions** tab, select the latest successful workflow run, and download the artifact.

Each result is labeled `candidate_unreviewed`. QuantaTale stores the headline, source URL, publication date when provided, and a short feed description. It does **not** turn a headline into a factual claim, copy feed descriptions into narration, or mark a source as supporting a claim. The original article must be opened and reviewed before claims are extracted.

Feed availability, formats, rate limits and terms can change. A failed feed is reported without silently substituting an unapproved source. Discovery is best-effort and the workflow can still complete when one configured feed is unavailable.

## Stage 4A: source retrieval and claim-candidate extraction

QuantaTale fetches a limited number of discovered article pages from their registered publisher domains and extracts sentence-shaped claim candidates from article paragraphs. Each candidate retains its original source passage, publisher ID, original and final URL, page title and extraction timestamp.

Run it after Stage 3 discovery:

```bash
quantatale research-candidates build/discovery-candidates.json --limit 10 --output build/research-candidates.json
```

The implementation uses deterministic Python standard-library parsing and requires no AI API, paid search service or additional package. It applies a page-size limit, checks publisher domains and rejects redirects outside the registered publisher domains. CI uploads the report with the other research artifacts.

**Important:** extracted sentences are unreviewed candidates, not verified claims. Extraction does not establish truth, source relevance, support, corroboration or contradiction. Human review of the original source remains mandatory. Independent-source discovery and structured contradiction assessment are later Stage 4 milestones.

## Current limits

- Topic discovery is currently feed-based, not a general-purpose search engine.
- Feed metadata is only a lead; it is not evidence verification.
- Extracted claim candidates still require source review and structured evidence assessment.
- Independent corroboration search and contradiction detection are not yet implemented.
- Automatic narration, voice generation, animation and MP4 rendering have not yet been implemented.

## Development roadmap

- [x] Establish repository foundation and cloud CI.
- [x] Define and validate the first topic specification.
- [x] Add a curated publisher registry and evidence-assessment workflow.
- [x] Add curated RSS/Atom topic discovery and candidate collection.
- [x] Retrieve source pages and extract unreviewed claim candidates.
- [ ] Discover independent evidence and identify possible contradictions.
- [ ] Expand discovery coverage and add topic scoring/diversity controls.
- [ ] Generate narration scripts and scene plans.
- [ ] Add fully cloud-runnable, open-source text-to-speech.
- [ ] Build reusable code-generated 2D animation components.
- [ ] Add procedural 3D holographic-style scenes.
- [ ] Assemble audio, animation and captions with FFmpeg.
- [ ] Add render profiles, quality gates and artifact exports.
- [ ] Add optional publishing integrations only if they remain free and do not become core dependencies.

## License

A project license will be selected and added before public code reuse is encouraged. Individual dependencies and downloaded voice models may have separate licenses; QuantaTale must record and respect them.


## Stage 4B: independent-feed evidence discovery and review dossiers

The first Stage 4B increment searches the configured public RSS/Atom feeds for articles whose titles or descriptions overlap with Stage 4A claim candidates. It retrieves a bounded number of matching pages from registered publisher domains, extracts additional unreviewed passages, groups records by the registry's publisher independence group, and flags possible wording/polarity or numerical differences.

Run it after Stage 4A:

```bash
quantatale evidence-dossier build/research-candidates.json --feed-limit 100 --article-limit 20 --output build/evidence-dossiers.json
```

The output is `build/evidence-dossiers.json`. CI includes this report in the seven-day research artifact.

**Important limitations:** discovery currently searches only configured feeds, not the entire web. Matching uses deterministic keyword overlap; it can miss relevant evidence and retrieve false matches. Independence groups are registry metadata, not proof of institutional independence. Difference flags are heuristic review signals, not confirmed contradictions. Human reviewers must compare full passages, dates, methods, definitions and units. Every dossier remains blocked from publication pending editorial review.

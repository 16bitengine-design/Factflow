# FactFlow

**Facts come to life.**

FactFlow is a cloud-first, open-source production pipeline for creating short, narrated, fact-based videos across science, history, nature, technology, geography, health, engineering and other subjects.

Its visual identity is **cinematic, code-generated holographic animation**: animated diagrams, 2D motion graphics, procedural 3D scenes, simulations, labels and visual effects. The project does not depend on stock footage or paid AI-video services.

## Non-negotiable principles

- **Zero-cost software stack:** no paid APIs, subscriptions, credits or commercial generation services.
- **Cloud-only execution:** production runs in GitHub Actions; no local rendering or installation is required.
- **Code-generated visuals:** scenes are created with open-source tools and project code.
- **Narration-first storytelling:** each Short has a strong hook, concise explanation and clear ending.
- **Evidence before publication:** factual claims must be traceable to reputable sources and reviewed before rendering.
- **Reproducible builds:** inputs, settings and outputs are versioned or recorded.
- **Honest limits:** free runners have time, storage and resource limits. FactFlow must respect them rather than promise unlimited production.

## Production flow

1. **Discover:** choose an engaging topic and define the audience and learning objective.
2. **Research:** collect source-backed claims and record structured evidence.
3. **Verify:** check publisher registration, source domains, independent corroboration and uncertainty; require editorial review.
4. **Write:** create a concise narration with a hook, explanation and memorable close.
5. **Plan scenes:** map each narration segment to an original animated visual.
6. **Generate voice:** use an open-source, cloud-runnable text-to-speech engine.
7. **Animate:** create 2D motion graphics and procedural 3D/holographic-style scenes with code.
8. **Assemble:** synchronize narration, visuals, captions and sound.
9. **Quality-check:** validate claims, timing, audio, captions, dimensions and final render.
10. **Export:** produce platform-ready MP4 files and metadata for Shorts and TikTok.

## Cloud-only, zero-cost operating model

The initial execution target is GitHub Actions on GitHub-hosted runners. The repository uses open-source tools and free public-repository runner capacity where available. Workflows must be efficient, avoid unnecessary repeated renders and respect the limits of free compute and storage.

**Important:** "100% free" means the core project must not require paid services or subscriptions. It does not mean unlimited compute, storage, bandwidth or guaranteed availability. GitHub and upstream projects can change their free-tier policies. FactFlow will report resource limits clearly and fail safely when a job cannot complete.

No API keys or paid-provider credentials should be required for the core workflow.

## Repository layout

```text
.
├── .github/
│   └── workflows/
│       └── ci.yml
├── data/
│   └── source_registry.json
├── examples/
│   └── topics/
│       └── why-the-sky-is-blue.json
├── src/
│   └── factflow/
│       ├── __init__.py
│       ├── cli.py
│       ├── research.py
│       └── topic.py
├── tests/
│   └── test_topic.py
├── .gitignore
└── pyproject.toml
```

## Stage 1: project foundation

The first milestone established a Python package, a topic JSON specification, a command-line validator, automated tests and a GitHub Actions workflow.

## Stage 2: evidence and fact assessment

FactFlow now has a curated starting registry of reputable publishers, including scientific, government, health, historical, educational and statistical institutions. The registry is stored in `data/source_registry.json` and can be expanded as new subject areas are added.

Each factual claim records structured evidence:
- `publisher_id`: publisher identifier from the curated registry.
- `url`: page containing the evidence.
- `title`: source page title.
- `accessed_on`: date the source was reviewed.
- `evidence_summary`: editor's summary of the relevant material (not an invented quotation).
- `supports_claim`: set to `true` only after an editor confirms the source directly supports the claim.

### Generate an evidence report

The report is generated automatically in GitHub Actions. To run the command in another environment:

```bash
factflow research-report examples/topics/why-the-sky-is-blue.json
```

To save the report:

```bash
factflow research-report examples/topics/why-the-sky-is-blue.json --output build/research-report.json
```

To also check whether source URLs respond:

```bash
factflow research-report examples/topics/why-the-sky-is-blue.json --check-links
```

Link checking requires outbound internet access. A reachable page is not necessarily accurate, authoritative or relevant.

### How claim statuses work

- `corroborated_pending_editorial_review`: at least two independent registered publisher groups are recorded as supporting the claim.
- `single_registered_source_pending_editorial_review`: one registered publisher group is recorded as supporting it.
- `evidence_not_yet_confirmed`: source records exist, but no source has been marked as directly supporting the claim.
- `unsupported_or_unregistered`: no usable registered evidence was found, or publisher/domain information failed registry checks.

The registry records independence groups so two websites belonging to the same publisher group are not automatically counted as independent corroboration.

**Critical limitation:** these are evidence-workflow statuses, not truth scores. Automated checks cannot reliably establish that a source's content proves a claim. An editor must read the cited material, check the exact wording and context, and approve the claim before publication. FactFlow's publication gate remains blocked pending editorial review.

## Development roadmap

- [x] Establish repository foundation and cloud CI.
- [x] Define and validate the first topic specification.
- [x] Add a curated publisher registry and evidence-assessment workflow.
- [ ] Add topic discovery and source collection.
- [ ] Generate narration scripts and scene plans.
- [ ] Add fully cloud-runnable, open-source text-to-speech.
- [ ] Build reusable code-generated 2D animation components.
- [ ] Add procedural 3D holographic-style scenes.
- [ ] Assemble audio, animation and captions with FFmpeg.
- [ ] Add render profiles, quality gates and artifact exports.
- [ ] Add optional publishing integrations only if they remain free and do not become core dependencies.

## License

A project license will be selected and added before public code reuse is encouraged. Individual dependencies and downloaded voice models may have separate licenses; FactFlow must record and respect them.

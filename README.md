# FactFlow

**Facts come to life.**

FactFlow is a cloud-first, open-source production pipeline for creating short, narrated, fact-based videos across science, history, nature, technology, geography, health, engineering and other subjects.

The visual identity is **cinematic, code-generated holographic animation**: animated diagrams, 2D motion graphics, procedural 3D scenes, simulations, labels and visual effects. The project does not depend on stock footage or paid AI-video services.

## Non-negotiable principles

- **Zero-cost software stack:** no paid APIs, subscriptions, credits or commercial generation services.
- **Cloud-only execution:** production runs in GitHub Actions; no local rendering or installation is required.
- **Code-generated visuals:** scenes are created with open-source tools and project code.
- **Narration-first storytelling:** each Short has a strong hook, concise explanation and clear ending.
- **Evidence before publication:** factual claims must be traceable to reputable sources and reviewed before rendering.
- **Reproducible builds:** inputs, settings and outputs are versioned or recorded.
- **Honest limits:** free runners have time, storage and resource limits. FactFlow must respect them rather than promise unlimited production.

## Planned production flow

1. **Discover:** choose an engaging topic and define the audience and learning objective.
2. **Research:** collect source-backed claims and record source URLs, dates and confidence.
3. **Verify:** check important claims against reputable independent sources; flag uncertainty and disagreement.
4. **Write:** create a concise narration with a hook, explanation and memorable close.
5. **Plan scenes:** map each narration segment to an original animated visual.
6. **Generate voice:** use an open-source, cloud-runnable text-to-speech engine.
7. **Animate:** create 2D motion graphics and procedural 3D/holographic-style scenes with code.
8. **Assemble:** synchronize narration, visuals, captions and sound.
9. **Quality-check:** validate claims, timing, audio, captions, dimensions and final render.
10. **Export:** produce platform-ready MP4 files and metadata for Shorts and TikTok.

## Cloud-only, zero-cost operating model

The initial execution target is GitHub Actions on GitHub-hosted runners. The repository will use open-source tools and free public-repository runner capacity where available. Workflows must be efficient, avoid unnecessary repeated renders, and upload finished videos as temporary workflow artifacts.

**Important:** "100% free" means the project must not require paid services or subscriptions. It does not mean unlimited compute, storage, bandwidth or guaranteed availability. GitHub and upstream projects can change their free-tier policies. FactFlow will report resource limits clearly and fail safely when a job cannot complete.

No API keys or paid-provider credentials should be required for the core workflow.

## Repository layout

```text
.
├── .github/
│   └── workflows/
│       └── ci.yml
├── examples/
│   └── topics/
│       └── why-the-sky-is-blue.json
├── src/
│   └── factflow/
│       ├── __init__.py
│       ├── cli.py
│       └── topic.py
├── tests/
│   └── test_topic.py
├── .gitignore
└── pyproject.toml
```

## First milestone: project foundation

The first milestone establishes a small, testable topic specification and a command-line validator. It deliberately does not pretend that the full video engine is complete yet.

### Run the validator in GitHub Actions

1. Open the **Actions** tab in this repository.
2. Select **FactFlow CI**.
3. Choose **Run workflow** if the manual trigger is available, or push a change to run it automatically.
4. The workflow installs the project and runs its tests, then validates the example topic.

The same commands can be run locally by a contributor, but local setup is not required for cloud production.

## Topic format

A topic JSON file must include:
- `id`: stable, lowercase identifier.
- `title`: topic title.
- `category`: subject category.
- `target_duration_seconds`: desired Short duration.
- `audience`: intended audience.
- `hook`: opening line.
- `narration`: narration text.
- `claims`: factual claims with at least one source URL each.
- `scenes`: ordered visual scene descriptions.

A source URL is a research lead, not proof by itself. Later verification stages will add source quality checks, claim-to-source matching and editorial review.

## Development roadmap

- [x] Establish repository foundation and cloud CI.
- [x] Define and validate the first topic specification.
- [ ] Add source records and fact-checking workflow.
- [ ] Generate narration scripts and scene plans.
- [ ] Add fully cloud-runnable, open-source TTS.
- [ ] Build reusable code-generated 2D animation components.
- [ ] Add procedural 3D holographic-style scenes.
- [ ] Assemble audio, animation and captions with FFmpeg.
- [ ] Add render profiles, quality gates and artifact exports.
- [ ] Add optional publishing integrations only if they remain free and do not become core dependencies.

## License

A project license will be selected and added before public code reuse is encouraged. Individual dependencies and downloaded voice models may have separate licenses; FactFlow must record and respect them.

# QuantaTale editorial review reserve

**Purpose:** prepare a reserve of distinct, researched short-video topics for the two daily Africa/Kampala publishing slots.

**Status:** all ten entries below are prepared candidates. None is editorially approved. The publishing scheduler must continue to ignore them until a human reviewer approves them.

## Review checklist

For each topic, open every listed source, verify the relevant passage and context, check every factual statement in the narration, and approve or reject the specification. A source link being reachable is not proof of support.

## Candidate reserve

| # | Topic | Main factual point | Sources | File |
|---:|---|---|---|---|
| 1 | The Moon's phases aren't Earth's shadow | Phases are our changing view of the Moon's sunlit half; Earth's shadow is involved in lunar eclipses | NASA; ESO | [moon-phases.json](specs/moon-phases.json) |
| 2 | Why the ocean looks blue | Water absorbs red wavelengths; particles and dissolved material can alter water colour | NOAA; USGS | [ocean-blue.json](specs/ocean-blue.json) |
| 3 | A Venus rotation takes longer than a year | Sidereal rotation is about 243 Earth days; orbit is about 225; solar day is about 117 | NASA; ESA | [venus-day.json](specs/venus-day.json) |
| 4 | What gets hot during lightning | Air around the lightning channel can reach roughly 50,000–54,000°F; rapid expansion produces thunder | NWS; NOAA | [lightning-hot-air.json](specs/lightning-hot-air.json) |
| 5 | Old Faithful isn't exact clockwork | Eruption intervals vary; predictions depend partly on the previous eruption | NPS; USGS | [old-faithful.json](specs/old-faithful.json) |
| 6 | Clouds need tiny particles | Water vapour condenses on microscopic nuclei as moist air cools | NOAA; NASA | [clouds-form.json](specs/clouds-form.json) |
| 7 | Why stars appear to twinkle | Turbulent air bends starlight, producing apparent flicker | NASA | [stars-twinkle.json](specs/stars-twinkle.json) |
| 8 | Continents move at fingernail speed | Tectonic plates move centimetres per year; GPS measures crustal motion | USGS | [tectonic-plates.json](specs/tectonic-plates.json) |
| 9 | What makes auroras glow | Energetic particles interact with oxygen and nitrogen in the upper atmosphere | NASA; NOAA | [aurora-lights.json](specs/aurora-lights.json) |
| 10 | Autumn leaves reveal hidden colours | Chlorophyll breaks down; carotenoids become visible and anthocyanins can form | NOAA; US Forest Service | [leaves-colour.json](specs/leaves-colour.json) |
| 11 | Why space is silent | Sound needs a material medium; electromagnetic light does not | NASA; Smithsonian | [sound-space.json](specs/sound-space.json) |
| 12 | Earth is not a perfect sphere | Rotation creates an equatorial bulge; topography and gravity make the real shape irregular | NOAA | [earth-shape.json](specs/earth-shape.json) |
| 13 | A day on Mercury lasts two Mercury years | Solar day is about 176 Earth days; Mercury's year is about 88 | NASA | [mercury-day.json](specs/mercury-day.json) |
| 14 | Mars has the solar system's largest volcano | Olympus Mons is over 25 miles tall and has a vast shield-volcano footprint | NASA; NASA JPL | [olympus-mons.json](specs/olympus-mons.json) |

## Approval policy

- `editorial_approved: false` and `status: awaiting_editorial_review` are intentional for every candidate.
- Automated discovery, source matching, text comparison and this review pack do not constitute human editorial approval.
- Only after the reviewer approves the actual scripts and sources should the spec be updated and registered as `approved_ready`.
- The scheduler selects only explicitly approved, ready specs and will not reuse a topic on the same local calendar day.

## Reserve target

Maintain at least **14 approved, unused-ready topics** (seven days at two distinct videos per day) as the operating target. Replenish when the approved reserve falls below 14. This target is a safety buffer, not a promise that discovery will always find sufficient high-quality evidence.

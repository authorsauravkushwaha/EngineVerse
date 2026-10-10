# The 13-section note template

Every full, standard-depth topic note in EngineVerse follows the same structure.
This is not a style preference — it is what makes the platform usable as a study
source rather than a link farm. A learner who knows that "Common mistakes" is
always the ninth section can navigate the catalogue without re-learning the
layout each time.

The template is defined once, in `scripts/seed.py`, as the `SECTIONS` list.
Adding or reordering a section is a one-line change there; the renderer, the
database and the templates all read from it.

## The sections

| # | Kind | Heading | Callout |
|---|---|---|---|
| 1 | `simple` | Explain it simply | remember |
| 2 | `definition` | Formal definition | — |
| 3 | `intuition` | Intuition — why it works | remember |
| 4 | `points` | Key points | — |
| 5 | `formula` | Formula and variables | exam |
| 6 | `derivation` | Derivation | — |
| 7 | `example` | Worked example | exam |
| 8 | `applications` | Real-world applications | realworld |
| 9 | `mistakes` | Common mistakes | warning |
| 10 | `exam` | Exam questions | exam |
| 11 | `interview` | Interview questions | interview |
| 12 | `diagram` | Diagram | — |
| 13 | `industry` | Industry practice | realworld |

The callout column drives the visual treatment: `warning` renders as an amber
panel, `exam` as a bordered box, `realworld` as a tinted panel. It is data, not a
template branch.

## Why each section exists

**1. Explain it simply.** The learner arrives not knowing the thing. This section
assumes nothing and uses no jargon that has not already been defined. If a
first-year student cannot read this section, the note has failed regardless of
how correct the rest is.

**2. Formal definition.** The precise statement, the one that gets quoted in an
exam answer and the one an interviewer expects. Kept separate from (1) so
rigour never has to be traded against accessibility.

**3. Intuition.** Why the definition is shaped the way it is. This is the section
that turns memorisation into understanding, and it is the one most textbooks
omit.

**4. Key points.** The scannable summary — what to recall at 2 a.m. before an
exam.

**5. Formula and variables.** Rendered from LaTeX by `markdown.py`, with a table
naming every symbol and its unit. A formula without a symbol table is not
usable.

**6. Derivation.** Where the formula comes from — the steps, not a restatement
of the result. Every topic now carries one; a section that merely reprints the
formula is worse than none, because it reads as though the reasoning were there.

**7. Worked example.** A problem solved end to end, with the reasoning shown, not
just the answer.

**8. Real-world applications.** Where this is actually used. This is the section
that answers "why am I learning this", and it is the reason the platform claims
engineers can apply what they read here.

**9. Common mistakes.** The traps. Rendered as a warning panel because it is the
section that most changes a grade.

**10. Exam questions.** Representative questions with worked answers.

**11. Interview questions.** The same topic from a hiring loop's perspective —
frequently a different question entirely from the exam one.

**12. Diagram.** An SVG with optional hotspots, so the labelled parts are
reachable as text rather than baked into pixels.

**13. Industry practice.** How this is handled in production, and where the
textbook version diverges from what is deployed.

## Depth presets

Not every learner needs all thirteen sections at once, so a note is authored at
one of four depths. Each depth is a subset of the same list — never a different
structure.

| Depth | Sections | For |
|---|---|---|
| `beginner` | 1, 4, 7, 9 | First exposure; the minimum that is still useful |
| `standard` | all 13 | The full note |
| `advanced` | 2, 5, 6, 7, 10 | Rigour and derivation |
| `industry` | 8, 13, 11, 9 | Applying it at work |

The learner's preferred depth is stored on their profile
(`profiles.note_quality`) and applied in `catalog.get_note()`, which falls back
to the closest available depth when the requested one has not been authored. A
learner who wants `industry` still gets a useful note on a topic that only has a
`standard` one.

## Storage

```
topics ──< notes ──< note_sections
           │
           ├── quality   (beginner|standard|advanced|industry)
           └── status, version, author_id
```

`notes` is unique on `(topic_id, quality)`, so a topic carries at most one note
per depth. `note_sections` holds one row per section, ordered by
`order_index`, with `kind` naming the template slot and `body_md` holding
markdown.

Keeping sections as rows rather than one markdown blob is what makes the
template enforceable: a missing section is an absent row, which the UI can
report, rather than a heading nobody wrote.

## Writing one

Sections are markdown. LaTeX is written inline with `$...$` or on its own line
with `$$...$$`, and is rendered by `markdown.py` — no external renderer, no
MathJax, no CDN.

```markdown
**Bernoulli's equation**

$$ p + \tfrac{1}{2}\rho v^2 + \rho g h = \text{constant} $$

| Symbol | Meaning | Unit |
| --- | --- | --- |
| $p$ | static pressure | Pa |
| $\rho$ | density | kg/m^3 |
| $v$ | flow speed | m/s |
```

Rules that keep notes trustworthy:

- Define a term before using it. If a section uses a word the learner has not met,
  link to the topic that defines it.
- State units. A number without a unit is not an engineering result.
- Show the reasoning in worked examples, not only the answer.
- Attribute diagrams. `diagrams.license` and `diagrams.source_url` exist for this.
- Label anything AI-assisted. Generated prose is marked as such in the UI, and
  answers cite the platform content they were grounded in.

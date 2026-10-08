# Content model and licensing

How content is added, reviewed, published, and what may legally be hosted.

## The content lifecycle

Every mutable content table carries `status`, `version` and `author_id`. A piece
of content moves through:

```
draft ──► under_review ──► approved ──► published ──► archived
  ▲            │                                        │
  └────────────┴──────────── changes requested ─────────┘
```

Only `published` rows reach learners. Every catalogue query filters on it —
`topics.status = 'published'`, `subjects.status = 'published'`, and so on — so a
draft is invisible without any extra logic in the templates.

Capability to move content along that path is defined in `security/rbac.py`, not
in the UI. `subject_expert` and `content_admin` hold `content.publish`;
`project_reviewer` holds `projects.review`; `student` holds none of them. A
learner cannot publish by crafting a request, because the check is on the server
and fails closed.

## What may be hosted

The rule is simple: **EngineVerse hosts what it creates, and links to everything
else.**

| Content | Policy |
|---|---|
| Notes, diagrams authored here, questions, coding problems, roadmaps | Hosted. Original work, CC-BY-4.0 unless stated otherwise. |
| Videos | **Linked only.** `videos.url` points at NPTEL, MIT OpenCourseWare, freeCodeCamp, Khan Academy. `videos.embed_id` exists in the model but is deliberately never populated. |
| Books | **Linked only.** `books.url` points at the publisher, or at the open-access source when the book is genuinely open. `books.is_free` says which. |
| External articles and documentation | **Linked only.** `resources.url`, with `is_free` marking open material. |
| Third-party diagrams | Only with a recorded `license` and `source_url`. |

No copyrighted book, paper or video is stored on EngineVerse servers, mirrored,
proxied, or embedded. A link to a legal source is not a substitute for hosting,
and it is the only thing this platform does with third-party media.

This is also why there is no upload pipeline for media: there is nothing to
upload.

## Certificates

Certificates carry a `verify_id` and are verifiable at
`/certificates/{verify_id}`. They state what the learner completed on
EngineVerse. They do **not** claim university accreditation, professional
licensure, or equivalence to any awarding body's qualification, and no template
or copy in the repository implies it. Anyone who needs that distinction can check
the verification URL.

## Seeding

`scripts/seed.py` builds a real catalogue, not placeholders:

```
universities 10 · colleges 13 · branches 45 · semesters 9 · curricula 180
curriculum_subjects 2756 · subjects 73 · modules 24 · topics 48 · notes 192
note_sections 1248 · diagrams 48 · models_3d 48 · formulas 15 · questions 38
question_options 152 · dpp_sets 14 · dpp_questions 68 · programming_languages 6
language_modules 23 · coding_problems 13 · coding_problem_stubs 16
coding_testcases 54 · projects 6 · project_steps 32 · project_resources 6
videos 174 · books 102 · resources 451 · roadmaps 5 · roadmap_nodes 57
flashcards 221 · plans 3 · site_config 12 · badges 12 · users 5
user_progress 29 · xp_events 29 · search index 1029
```

Every one of the 48 topics carries a full standard note (all thirteen sections),
an authored interactive diagram and a 3D model. Section bodies that are not part
of the original topic entry live in `seed_data/notes_extra.py`, keyed by topic
slug; `seed.py` raises at startup if that file names a topic that no longer
exists, so a renamed topic cannot silently drop content.

```bash
python scripts/seed.py --fresh    # drop and rebuild
python scripts/seed.py --stats    # print row counts
```

The seeder is idempotent: re-running it without `--fresh` upserts rather than
duplicating, so it is safe to run against a database that already has learner
data.

## Extending without a redesign

Nothing about the catalogue is hard-coded in the frontend. Branches, subjects,
topics, questions, problems and projects are rows, and the templates iterate
them. Adding a branch means inserting into `branches` and `subjects`; no template
changes.

### After you insert rows, the search index has to catch up

Global search and the AI tutor both read a derived index, not the content tables.
Nothing indexes a row at the moment it is written, so a subject you just inserted
is not searchable until the index is rebuilt. Two things do that:

```bash
python scripts/reindex.py            # rebuild now
python scripts/reindex.py --check    # report what the index holds, change nothing
```

and the application rebuilds on startup when it notices the content has changed.
`search.refresh_if_stale()` fingerprints the content tables — row counts and
`updated_at` sums per table — and compares it with the marker written at the last
build, so an insert, an edit or a delete all trigger a rebuild on the next boot.

Both are worth knowing about because the version marker alone is not enough.
It records which *schema* of index the code produces, and once it matches it
stays matched, so relying on it would have left newly added content invisible
until a schema change happened to force a rebuild.

A fingerprint cannot notice an edit that changes neither a row count nor a
timestamp. If you rewrite content in place by hand, run `scripts/reindex.py`.
`scripts/seed.py` reindexes as part of seeding, so reseeding never needs it.

The one place a new *shape* of content needs code is the coding judge: a problem
whose input is not one of the thirteen known forms needs a new wrapper in
`engineverse/drivers.py`. Everything else is data.

## AI-assisted content

Two rules, both enforced in the UI rather than left to convention:

1. **AI-generated prose is labelled.** A reader can always tell which text was
   machine-assisted.
2. **AI answers cite their sources.** The tutor grounds responses in platform
   content and references it, rather than answering from the model alone.

An unlabelled or unsourced AI answer on an education platform is worse than no
answer, because the learner cannot weigh it.

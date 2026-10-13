# Curriculum coverage

This is a count of rows in the database this script was pointed at. It is not a
statement that EngineVerse covers an engineering degree, a university syllabus,
or a placement season. Subjects that are absent are simply absent — this report
does not list planned or imagined ones.

Regenerate it with `python scripts/coverage_report.py --write docs/CURRICULUM_COVERAGE.md`
after seeding a development database. Do not treat a committed snapshot as live
production content unless you just generated it from that database.

## Totals

- Branches: 45
- Published subjects: 93
- Published topics: 406
- Published notes across all reading depths: 1624
- Note sections: 10556
- Standard notes with all 13 sections: 406
- Diagrams: 406
- 3D models: 406
- Formulas: 365
- Active questions: 525
- Published DPP sets: 105
- Published DPP question slots: 525
- Subjects represented in published DPPs: 93
- Language tracks represented in published DPPs: 9
- Coding problems: 95
- Curated coding sheets: 12 (125 problem slots; 0 problems in no sheet)
- Programming languages: 9
- Language modules: 68 (68 assigned to a stage)
- Language stages: 27
- Stage checkpoint links: 81 (81 pointing at active questions)
- Published project briefs: 16
- Project steps: 92
- Project resources: 27
- Language-linked capstone briefs: 9

## Coding sheets by stream

Each row is one branch category. A sheet is reachable from a stream when it
is written for everyone or names that category; the problem count is the
distinct bank problems those sheets reach, so a problem in two sheets is
counted once.

| Stream | Sheets | Problems reachable |
|---|---:|---:|
| Computer Science & IT | 10 | 77 |
| Electronics & Electrical | 10 | 80 |
| Mechanical & Manufacturing | 9 | 74 |
| Civil & Infrastructure | 8 | 65 |
| Chemical & Materials | 10 | 80 |
| Bio & Other Engineering | 9 | 73 |

A stream with no sheet of its own still gets the sheets written for every
branch - the pattern sheets and the interview set - so a learner is never left
with an empty page.

## Programming paths

Each path progresses through Foundations, Working Practice and Advanced Engineering. A stage with modules but no checkpoint, or a capstone column that is empty, is a gap - not a variant.

| Language | Modules | Foundations | Working Practice | Advanced Engineering | Checkpoints | Capstone |
|---|---:|---:|---:|---:|---:|---|
| Python | 13 | 5 | 4 | 4 | 9 | [python-field-notes-api](/projects/python-field-notes-api) |
| Java | 11 | 3 | 3 | 5 | 9 | [java-room-booking-service](/projects/java-room-booking-service) |
| JavaScript | 8 | 2 | 3 | 3 | 9 | [js-revision-dashboard](/projects/js-revision-dashboard) |
| TypeScript | 6 | 1 | 2 | 3 | 9 | [ts-task-api-client](/projects/ts-task-api-client) |
| C++ | 7 | 2 | 3 | 2 | 9 | [cpp-text-index-cli](/projects/cpp-text-index-cli) |
| Go | 6 | 1 | 3 | 2 | 9 | [go-healthcheck-service](/projects/go-healthcheck-service) |
| Rust | 6 | 1 | 2 | 3 | 9 | [rust-logscan-cli](/projects/rust-logscan-cli) |
| C | 5 | 2 | 2 | 1 | 9 | [c-sensor-ringlog](/projects/c-sensor-ringlog) |
| SQL | 6 | 2 | 3 | 1 | 9 | [sql-ops-reporting-db](/projects/sql-ops-reporting-db) |

## By branch

| Branch | Subjects | Topics | Notes | Questions |
|---|---:|---:|---:|---:|
| AI & Machine Learning | 2 | 8 | 32 | 8 |
| Aerospace Engineering | 1 | 4 | 16 | 4 |
| Agricultural Engineering | 1 | 4 | 16 | 4 |
| Automobile Engineering | 1 | 4 | 16 | 4 |
| Biomedical Engineering | 1 | 4 | 16 | 4 |
| Biotechnology Engineering | 1 | 4 | 16 | 4 |
| Blockchain Engineering | 1 | 4 | 16 | 4 |
| Chemical Engineering | 6 | 24 | 96 | 25 |
| Civil Engineering | 3 | 12 | 48 | 12 |
| Cloud Computing | 1 | 4 | 16 | 4 |
| Computer Science Engineering | 10 | 61 | 244 | 79 |
| Construction Engineering | 1 | 4 | 16 | 4 |
| Control Systems | 1 | 4 | 16 | 4 |
| Cyber Security | 1 | 14 | 56 | 14 |
| Data Science | 1 | 4 | 16 | 4 |
| DevOps & SRE | 1 | 4 | 16 | 4 |
| Electrical Engineering | 5 | 20 | 80 | 23 |
| Electronics & Communication | 6 | 24 | 96 | 26 |
| Electronics Engineering | 1 | 4 | 16 | 4 |
| Embedded Systems | 1 | 4 | 16 | 4 |
| Energy Engineering | 1 | 4 | 16 | 4 |
| Environmental Engineering | 1 | 4 | 16 | 4 |
| Food Technology | 1 | 4 | 16 | 4 |
| Geotechnical Engineering | 1 | 4 | 16 | 5 |
| Industrial Engineering | 1 | 4 | 16 | 4 |
| Information Technology | 1 | 4 | 16 | 4 |
| Instrumentation Engineering | 1 | 4 | 16 | 4 |
| Internet of Things | 1 | 4 | 16 | 4 |
| Manufacturing Engineering | 1 | 4 | 16 | 4 |
| Marine Engineering | 1 | 4 | 16 | 4 |
| Materials Engineering | 1 | 4 | 16 | 4 |
| Mechanical Engineering | 8 | 34 | 136 | 38 |
| Mechatronics | 1 | 4 | 16 | 4 |
| Metallurgical Engineering | 1 | 4 | 16 | 4 |
| Mining Engineering | 1 | 4 | 16 | 4 |
| Petroleum Engineering | 1 | 4 | 16 | 4 |
| Polymer Engineering | 1 | 4 | 16 | 4 |
| Production Engineering | 1 | 4 | 16 | 4 |
| Robotics | 1 | 4 | 16 | 4 |
| Robotics & Automation | 1 | 4 | 16 | 4 |
| Software Engineering | 1 | 4 | 16 | 4 |
| Structural Engineering | 2 | 8 | 32 | 8 |
| Textile Engineering | 1 | 4 | 16 | 4 |
| Transportation Engineering | 1 | 4 | 16 | 4 |
| VLSI Design | 1 | 4 | 16 | 4 |

A branch with a handful of subjects is a sample, not a semester. Core learning
stays free. Certificates issued by this application are not university degrees
and must not be described as accredited.

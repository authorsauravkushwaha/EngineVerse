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
- Active questions: 534
- Published DPP sets: 107
- Published DPP question slots: 535
- Subjects represented in published DPPs: 93
- Language tracks represented in published DPPs: 10
- Coding problems: 105
- Curated coding sheets: 14 (135 problem slots; 0 problems in no sheet)
- Programming languages: 10
- Language modules: 225 (225 assigned to a stage)
- Language stages: 30
- Stage checkpoint links: 90 (90 pointing at active questions)
- Published project briefs: 17
- Project steps: 98
- Project resources: 30
- Language-linked capstone briefs: 10

## Coding sheets by stream

Each row is one branch category. A sheet is reachable from a stream when it
is written for everyone or names that category; the problem count is the
distinct bank problems those sheets reach, so a problem in two sheets is
counted once.

| Stream | Sheets | Problems reachable |
|---|---:|---:|
| Computer Science & IT | 12 | 87 |
| Electronics & Electrical | 12 | 90 |
| Mechanical & Manufacturing | 11 | 84 |
| Civil & Infrastructure | 10 | 75 |
| Chemical & Materials | 12 | 90 |
| Bio & Other Engineering | 11 | 83 |

A stream with no sheet of its own still gets the sheets written for every
branch - the pattern sheets and the interview set - so a learner is never left
with an empty page.

## Programming paths

Each path progresses through Foundations, Working Practice and Advanced Engineering. A stage with modules but no checkpoint, or a capstone column that is empty, is a gap - not a variant.

| Language | Modules | Foundations | Working Practice | Advanced Engineering | Checkpoints | Capstone |
|---|---:|---:|---:|---:|---:|---|
| Python | 35 | 13 | 6 | 16 | 9 | [python-field-notes-api](/projects/python-field-notes-api) |
| Java | 31 | 10 | 4 | 17 | 9 | [java-room-booking-service](/projects/java-room-booking-service) |
| JavaScript | 23 | 9 | 5 | 9 | 9 | [js-revision-dashboard](/projects/js-revision-dashboard) |
| TypeScript | 16 | 5 | 2 | 9 | 9 | [ts-task-api-client](/projects/ts-task-api-client) |
| C++ | 27 | 8 | 4 | 15 | 9 | [cpp-text-index-cli](/projects/cpp-text-index-cli) |
| Go | 17 | 6 | 3 | 8 | 9 | [go-healthcheck-service](/projects/go-healthcheck-service) |
| Rust | 17 | 6 | 2 | 9 | 9 | [rust-logscan-cli](/projects/rust-logscan-cli) |
| C | 26 | 10 | 3 | 13 | 9 | [c-sensor-ringlog](/projects/c-sensor-ringlog) |
| C# | 18 | 8 | 5 | 5 | 9 | [csharp-tasks-api](/projects/csharp-tasks-api) |
| SQL | 15 | 5 | 3 | 7 | 9 | [sql-ops-reporting-db](/projects/sql-ops-reporting-db) |

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

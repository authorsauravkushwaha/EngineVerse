"""Staged progression and checkpoint quizzes for every programming path.

A language path is three stages - Foundations, Working Practice and Advanced
Engineering - and every module in the catalogue belongs to exactly one of
them. Each stage ends with a three-question checkpoint. Checkpoints are not a
parallel quiz system: they are ordinary rows in the ``questions`` table, linked
from ``language_checkpoints``, answered through the normal practice flow, with
attempt-based XP, mistake history and DPP rotation like any other question.

Design rules this file enforces on itself through ``validate()``:

* every language listed in ``library_data.LANGUAGES`` has all three stages;
* every seeded module slug appears in exactly one stage - no omissions, no
  duplicates, no assignments to modules that do not exist;
* every stage has exactly three checkpoint questions, each with four options,
  one correct answer, a real explanation and an explicit difficulty;
* correct-answer positions are rotated deterministically (the same rule
  ``subject_paths`` uses for generated questions), so reseeds are reproducible
  and the answer key is not a visible position pattern.

The questions are standard language facts written for these paths. They are
checks that a stage was understood, not a certification, and they do not claim
job readiness.
"""
from __future__ import annotations

import re

#: The three stages every language path progresses through, in order.
STAGES = (
    (
        "foundations",
        "Foundations",
        "Read and write the core constructs: values, control flow, functions and the "
        "structures the language is used through. Finish this stage able to run every "
        "example and explain what each line does.",
    ),
    (
        "working_practice",
        "Working Practice",
        "Organise code the way a working engineer does: types and structure, errors you "
        "handle on purpose, and tests that prove behaviour. Finish this stage able to "
        "change code without breaking it silently.",
    ),
    (
        "advanced_engineering",
        "Advanced Engineering",
        "Put the language to work behind a boundary: services, persistence, concurrency "
        "and safety limits, including carefully bounded tool-using agents where the "
        "language fits. Finish this stage able to ship the capstone brief.",
    ),
)

STAGE_SLUGS = tuple(slug for slug, _title, _summary in STAGES)
STAGE_TITLES = {slug: title for slug, title, _summary in STAGES}
STAGE_SUMMARIES = {slug: summary for slug, _title, summary in STAGES}

#: Iteration order for building checkpoint entries. Mirrors
#: ``library_data.LANGUAGES``; ``validate()`` asserts the two sets agree, so a
#: new language cannot be seeded without staging it here.
LANGUAGE_ORDER = ("python", "java", "javascript", "typescript", "cpp", "go", "rust", "c", "csharp", "sql")

#: Checkpoint questions live in the question bank under this subject, which is
#: the published first-year programming subject. That keeps them in the normal
#: bank, DPP rotation and coverage rules instead of inventing a second track.
CHECKPOINT_SUBJECT = "programming-fundamentals"

#: language -> stage -> module slugs, in reading order. Together these lists
#: must be exactly the merged module set (language_foundations, then
#: library_data.LANGUAGE_MODULES, then language_paths.EXTRA_MODULES, then the
#: language_book_*.BOOK_MODULES depth modules) for that language -
#: ``validate()`` fails the seed otherwise.
#:
#: Staging rule for the book-depth modules: they are interview-grade DSA and
#: engineering depth, so they extend the advanced stage of the nine original
#: languages (whose foundations and working practice already exist). C# has no
#: legacy modules - its whole path is book modules, staged across all three
#: stages so the gates still mean something.
MODULE_STAGES = {
    "python": {
        "foundations": [
            "python-why", "python-hello-setup", "python-operators",
            "python-decisions", "python-loops-from-scratch", "python-input-practice",
            "python-real-world-1", "python-lists-scratch",
            "python-variables", "python-control-flow", "python-functions",
            "python-collections", "python-strings-files",
        ],
        "working_practice": [
            "python-stdlib-os", "python-packaging",
            "python-oop", "python-errors", "python-modules", "python-testing",
        ],
        "advanced_engineering": [
            "python-fastapi-app", "python-sqlite-persistence",
            "python-agent-tools", "python-tested-app-capstone",
            "python-complexity-big-o", "python-strings-deep", "python-lists-deep",
            "python-dicts-sets", "python-recursion", "python-sorting-searching",
            "python-stacks-queues", "python-linked-lists", "python-trees-heaps",
            "python-graphs", "python-dp", "python-interview-mastery",
        ],
    },
    "java": {
        "foundations": [
            "java-why", "java-hello", "java-operators", "java-decisions",
            "java-loops-from-scratch", "java-real-world-1", "java-methods",
            "java-basics", "java-control-flow", "java-oop",
        ],
        "working_practice": ["java-interfaces", "java-exceptions", "java-testing", "java-build-test"],
        "advanced_engineering": [
            "java-http-service", "java-jdbc-data", "java-concurrency",
            "java-agent-tools", "java-application-capstone",
            "java-complexity-big-o", "java-strings-deep", "java-arrays-arraylist",
            "java-hashmap-hashset", "java-recursion", "java-sorting-searching",
            "java-stacks-queues", "java-linked-lists", "java-trees-heaps",
            "java-graphs", "java-dp", "java-interview-mastery",
        ],
    },
    "javascript": {
        "foundations": [
            "js-why", "js-hello", "js-operators", "js-decisions-loops",
            "js-real-world-1", "js-functions-scratch", "js-basics", "js-objects", "js-dom",
        ],
        "working_practice": ["js-async", "js-errors", "js-modules", "js-node-service", "js-testable-app"],
        "advanced_engineering": [
            "js-browser-security", "js-agent-tools", "js-fullstack-capstone",
            "js-complexity-big-o", "js-strings-arrays-deep", "js-recursion-sorting",
            "js-maps-sets", "js-trees-graphs", "js-interview-mastery",
        ],
    },
    "typescript": {
        "foundations": [
            "ts-why", "ts-hello", "ts-decisions-loops", "ts-real-world-1",
            "ts-types-functions",
        ],
        "working_practice": ["ts-web-app", "ts-http-validation"],
        "advanced_engineering": [
            "ts-node-service", "ts-agent-tools", "ts-test-release-capstone",
            "ts-complexity-big-o", "ts-collections-deep", "ts-recursion-sorting",
            "ts-generics-dsa", "ts-graphs-dp", "ts-interview-mastery",
        ],
    },
    "cpp": {
        "foundations": [
            "cpp-why", "cpp-hello", "cpp-variables-operators", "cpp-decisions-loops",
            "cpp-real-world-1", "cpp-functions-scratch", "cpp-basics", "cpp-memory",
        ],
        "working_practice": ["cpp-classes", "cpp-containers", "cpp-raii-memory-safety", "cpp-build-test"],
        "advanced_engineering": [
            "cpp-parse-safe-input", "cpp-professional", "cpp-safe-app-project",
            "cpp-complexity-big-o", "cpp-strings-deep", "cpp-vectors-arrays",
            "cpp-hash-unordered", "cpp-recursion", "cpp-sorting-searching",
            "cpp-stacks-queues", "cpp-linked-lists", "cpp-trees-heaps",
            "cpp-graphs", "cpp-dp", "cpp-interview-mastery",
        ],
    },
    "go": {
        "foundations": [
            "go-why", "go-hello", "go-variables-operators", "go-decisions-loops",
            "go-real-world-1", "go-types-errors",
        ],
        "working_practice": ["go-packages-tests", "go-http-api", "go-sql-data"],
        "advanced_engineering": [
            "go-concurrency-context", "go-agent-capstone",
            "go-complexity-big-o", "go-slices-maps-deep", "go-recursion-sorting",
            "go-stacks-queues", "go-trees-graphs", "go-interview-mastery",
        ],
    },
    "rust": {
        "foundations": [
            "rust-why", "rust-hello", "rust-variables-operators", "rust-decisions-loops",
            "rust-real-world-1", "rust-ownership-errors",
        ],
        "working_practice": ["rust-collections-iterators", "rust-tests-modules"],
        "advanced_engineering": [
            "rust-http-service", "rust-agent-tools", "rust-application-capstone",
            "rust-complexity-big-o", "rust-strings-vec-deep", "rust-recursion-sorting",
            "rust-hash-collections", "rust-graphs-dp", "rust-interview-mastery",
        ],
    },
    "c": {
        "foundations": [
            "c-why", "c-hello", "c-variables", "c-operators", "c-if-else", "c-loops",
            "c-arrays-scratch", "c-real-world-1", "c-basics", "c-pointers",
        ],
        "working_practice": ["c-structs", "c-functions", "c-headers-modules"],
        "advanced_engineering": [
            "c-files",
            "c-complexity-big-o", "c-strings-deep", "c-arrays-deep",
            "c-recursion-stack", "c-sorting-searching", "c-linked-lists",
            "c-stacks-queues", "c-hash-tables", "c-trees-heaps",
            "c-graphs", "c-dp-bitwise", "c-interview-mastery",
        ],
    },
    "csharp": {
        "foundations": [
            "csharp-why", "csharp-hello", "csharp-variables-operators",
            "csharp-decisions-loops", "csharp-methods-arrays", "csharp-strings-lists",
            "csharp-real-world-1", "csharp-complexity-big-o",
        ],
        "working_practice": [
            "csharp-oop", "csharp-collections-linq", "csharp-errors",
            "csharp-recursion-sorting", "csharp-stacks-queues",
        ],
        "advanced_engineering": [
            "csharp-trees-heaps", "csharp-graphs", "csharp-dp",
            "csharp-async-services", "csharp-interview-mastery",
        ],
    },
    "sql": {
        "foundations": ["sql-why", "sql-hello", "sql-select", "sql-filter", "sql-real-world-1"],
        "working_practice": ["sql-joins", "sql-group", "sql-null"],
        "advanced_engineering": [
            "sql-professional",
            "sql-subqueries-cte", "sql-window-functions", "sql-optimization-explain",
            "sql-recursion-cte", "sql-data-modeling", "sql-interview-mastery",
        ],
    },
}

# ---------------------------------------------------------------------------
# Checkpoint questions
#
# Each entry: title (unique across the whole bank), stem, four options, the
# authored correct index, an explanation, and a difficulty. The seeder rotates
# option positions deterministically (see checkpoint_questions()), so the
# authored index is only the starting point, never the stored answer position.
# ---------------------------------------------------------------------------

CHECKPOINTS = {
    "python": {
        "foundations": [
            {
                "title": "Python foundations checkpoint: tuple immutability",
                "stem": "What happens when a program runs `t = (1, 2, 3)` and then `t[0] = 9`?",
                "options": [
                    "A TypeError is raised: a tuple does not support item assignment, so it cannot be changed in place",
                    "t becomes (9, 2, 3)",
                    "Python quietly converts t to a list, then assigns",
                    "A ValueError is raised because 9 is outside the tuple",
                ],
                "correct": 0,
                "explanation": "Tuples are immutable: the name t can be rebound to a new tuple, but the existing "
                               "tuple object cannot be modified. Item assignment raises TypeError. Lists are the "
                               "mutable sequence; choose based on whether the value is allowed to change.",
                "difficulty": "easy",
            },
            {
                "title": "Python foundations checkpoint: equality does not coerce types",
                "stem": "What does `42 == '42'` evaluate to in Python?",
                "options": [
                    "False - an int and a str are different types and Python does not coerce between them for ==",
                    "True - Python converts the string to a number before comparing",
                    "True - both values print the same characters",
                    "It raises TypeError",
                ],
                "correct": 0,
                "explanation": "Python's == does not perform cross-type coercion the way JavaScript's == does; an "
                               "int never equals a str. To compare, convert explicitly with int('42') and handle "
                               "the ValueError when the text is not a number.",
                "difficulty": "easy",
            },
            {
                "title": "Python foundations checkpoint: slices produce new lists",
                "stem": "After `nums = [1, 2, 3, 4]` and `tail = nums[2:]`, which statement is true?",
                "options": [
                    "tail is [3, 4], and appending to tail leaves nums unchanged",
                    "tail is [2, 3, 4] because slicing includes the start index's predecessor",
                    "tail is another name for nums, so changing tail changes nums",
                    "nums becomes [1, 2] because the tail was removed",
                ],
                "correct": 0,
                "explanation": "A slice runs from the start index up to but excluding the end (here, the end of "
                               "the list), and it builds a new list. nums still holds all four items; tail is an "
                               "independent shallow copy of the last two.",
                "difficulty": "easy",
            },
        ],
        "working_practice": [
            {
                "title": "Python working practice checkpoint: when else runs",
                "stem": "In a `try / except / else / finally` block, when does the `else` clause run?",
                "options": [
                    "Only when the try block finished without raising an exception",
                    "Whenever the finally clause runs",
                    "When an exception was caught by the except clause",
                    "Before the try block, to set it up",
                ],
                "correct": 0,
                "explanation": "else runs on the no-exception path only. Keeping the success work in else (rather "
                               "than at the end of try) means an exception raised by that work is not accidentally "
                               "caught by the same except clause. finally runs on every path.",
                "difficulty": "medium",
            },
            {
                "title": "Python working practice checkpoint: order-dependent tests",
                "stem": "A pytest suite passes when one test file runs alone but fails on a full run. What is the most likely cause?",
                "options": [
                    "A test depends on state left behind by an earlier test - the tests are not isolated",
                    "pytest always shuffles files, so the code under test is nondeterministic",
                    "Python caches bytecode between tests and serves stale functions",
                    "Fixtures stop being defined after the first file",
                ],
                "correct": 0,
                "explanation": "Order dependence is the classic whole-suite failure: a shared global, a file left "
                               "on disk, or a row another test inserted. The fix is isolation - each test sets up "
                               "its own state (fixtures, tmp_path) and cleans up after itself.",
                "difficulty": "medium",
            },
            {
                "title": "Python working practice checkpoint: the main guard",
                "stem": "What does `if __name__ == '__main__':` do in a Python module?",
                "options": [
                    "Runs the guarded code when the file is executed directly, but not when it is imported",
                    "Makes every name in the module private",
                    "Runs the guarded code once per import, in every importer",
                    "Prevents the module from being imported at all",
                ],
                "correct": 0,
                "explanation": "A module run as a script has __name__ == '__main__'; imported, it has the module's "
                               "name. The guard keeps script behaviour (argument parsing, demo runs) out of "
                               "importers while leaving functions importable and testable.",
                "difficulty": "easy",
            },
        ],
        "advanced_engineering": [
            {
                "title": "Python advanced checkpoint: parameterized SQLite queries",
                "stem": "Why does `cursor.execute('SELECT * FROM notes WHERE tag = ?', (tag,))` prevent SQL injection where an f-string does not?",
                "options": [
                    "The placeholder binds the value as data, so it is never parsed as SQL syntax; an f-string splices text into the statement and a crafted tag can change its meaning",
                    "The ? placeholder escapes single quotes automatically, which is the only injection vector",
                    "Values passed in a tuple are encrypted before the query runs",
                    "It does not - only an ORM can prevent SQL injection",
                ],
                "correct": 0,
                "explanation": "Parameter binding preserves the boundary between the fixed SQL program and "
                               "untrusted values. An f-string builds one text where a value like `' OR 1=1 --` "
                               "becomes part of the query. sqlite3, psycopg and every serious driver support "
                               "binding; use it for every value.",
                "difficulty": "hard",
            },
            {
                "title": "Python advanced checkpoint: sessions prove identity, not permission",
                "stem": "An API endpoint that deletes a note receives a request with a valid session cookie. What must it still check before deleting?",
                "options": [
                    "That this authenticated user is authorized to delete this particular note - a valid login proves identity, not permission",
                    "Nothing: a valid session proves the request is authorized",
                    "That the request came from the official web page, which is the only client that can call the endpoint",
                    "Only the CSRF token, because ownership is implied by being logged in",
                ],
                "correct": 0,
                "explanation": "Authentication answers 'who is this', authorization answers 'may they do this'. "
                               "The endpoint must scope the delete to the owner (or an explicit role check) in the "
                               "query or code, server-side. CSRF protection and UI hiding are separate controls "
                               "and neither substitutes for the ownership check.",
                "difficulty": "hard",
            },
            {
                "title": "Python advanced checkpoint: bounding an agent's destructive tool",
                "stem": "A study agent is given a tool that can delete files. Which design bounds the damage?",
                "options": [
                    "An allowlist of directories the tool may touch, refusal of everything else, and an explicit confirmation step before any deletion runs",
                    "No restriction, but every deletion is written to a log",
                    "Restrict deletions to files smaller than 1 MB",
                    "Instruct the model in its prompt to refuse dangerous paths",
                ],
                "correct": 0,
                "explanation": "Bounds belong in code, not in logs or prompts: an allowlist makes the dangerous "
                               "action impossible outside known paths, and confirmation keeps a human in the loop "
                               "for irreversible effects. Logging is detective, not preventive; a prompt is advice "
                               "the model may not follow.",
                "difficulty": "hard",
            },
        ],
    },
    "java": {
        "foundations": [
            {
                "title": "Java foundations checkpoint: integer division",
                "stem": "What is the value of `int result = 7 / 2;` in Java?",
                "options": [
                    "3 - both operands are int, so the division truncates toward zero",
                    "3.5, rounded down when stored in the int",
                    "4 - Java rounds integer division to nearest",
                    "It does not compile; int cannot hold a division result",
                ],
                "correct": 0,
                "explanation": "int / int is integer division and discards the remainder. For 3.5, make at least "
                               "one operand double (7 / 2.0) or store into a double with a cast. The remainder "
                               "itself is 7 % 2.",
                "difficulty": "easy",
            },
            {
                "title": "Java foundations checkpoint: comparing strings",
                "stem": "With `String a = new String(\"hi\"); String b = new String(\"hi\");`, what does `a == b` evaluate to?",
                "options": [
                    "false - == compares object references and these are two distinct objects; a.equals(b) is true",
                    "true - Java compares string contents with ==",
                    "true - identical literals are always the same object",
                    "It does not compile; strings cannot be compared with ==",
                ],
                "correct": 0,
                "explanation": "== tests reference identity. new String(...) deliberately creates a separate "
                               "object, so the references differ even though the contents match. Content "
                               "comparison is a.equals(b) - one of the most common early Java defects.",
                "difficulty": "easy",
            },
            {
                "title": "Java foundations checkpoint: what static means",
                "stem": "What does declaring a field `static` mean in Java?",
                "options": [
                    "One copy is shared by the whole class instead of one copy per object",
                    "The field cannot be modified after the constructor finishes",
                    "The field is visible only inside its package",
                    "The field is stored outside the JVM",
                ],
                "correct": 0,
                "explanation": "static fields belong to the class: every instance sees the same value. "
                               "Immutability is final, visibility is public/private/protected - those are "
                               "separate modifiers. Mutable static state is shared state, which is exactly why "
                               "concurrent code treats it carefully.",
                "difficulty": "medium",
            },
        ],
        "working_practice": [
            {
                "title": "Java working practice checkpoint: programming to an interface",
                "stem": "Why is a method parameter declared as `List<Item>` rather than `ArrayList<Item>`?",
                "options": [
                    "Callers depend on the contract, so the implementation can be swapped or mocked without changing the code that uses it",
                    "Interfaces execute faster than concrete classes",
                    "An interface can hold the fields the object needs",
                    "Java forbids naming ArrayList in a signature",
                ],
                "correct": 0,
                "explanation": "The interface is the promise (ordered, indexed, iterable); the implementation is "
                               "a detail. Depending on the contract lets tests pass a fake list and production "
                               "switch to LinkedList or an immutable list without touching callers.",
                "difficulty": "medium",
            },
            {
                "title": "Java working practice checkpoint: checked exceptions",
                "stem": "A method declares `throws IOException`. What does that force callers to do?",
                "options": [
                    "Handle it with try/catch or declare it in their own throws clause - the compiler rejects code that ignores it",
                    "Nothing; the declaration is documentation only",
                    "Retry the call until it succeeds",
                    "Wrap every call in a synchronized block",
                ],
                "correct": 0,
                "explanation": "Checked exceptions are part of the method's contract and the compiler enforces "
                               "them. Catch the specific exception you can actually handle; catching Exception "
                               "and continuing hides failures, and declaring throws Exception everywhere just "
                               "moves the problem to callers.",
                "difficulty": "medium",
            },
            {
                "title": "Java working practice checkpoint: why the boundary test exists",
                "stem": "A JUnit test for `withdraw(amount)` already asserts a normal withdrawal succeeds. Why must it also assert that an overdraw is refused?",
                "options": [
                    "Boundary behaviour is where defects live: a suite that only covers the happy path stays green while the guard is broken",
                    "JUnit requires at least two tests per method",
                    "The happy path cannot be tested without a database",
                    "It raises the coverage percentage the build reports",
                ],
                "correct": 0,
                "explanation": "The refusal is the behaviour that protects the balance. Test the exact threshold "
                               "and one step past it, and name tests after the behaviour "
                               "(withdrawRefusesToOverdraw). Coverage numbers can rise while the assertion that "
                               "matters is missing.",
                "difficulty": "medium",
            },
        ],
        "advanced_engineering": [
            {
                "title": "Java advanced checkpoint: PreparedStatement",
                "stem": "What is the main security reason to use a JDBC `PreparedStatement` with `?` placeholders instead of concatenating user input into SQL?",
                "options": [
                    "The value is bound as data and never re-parsed as SQL, so a crafted input cannot change the statement's meaning",
                    "PreparedStatement encrypts parameter values in transit",
                    "String concatenation is slower, which risks denial of service",
                    "The driver validates that inputs are well-formed identifiers",
                ],
                "correct": 0,
                "explanation": "Binding keeps the code/data boundary: the SQL program is fixed before values "
                               "arrive. Concatenation lets input like `' OR 1=1 --` extend the program. Prepared "
                               "statements also let the database cache plans, but injection prevention is the "
                               "reason they are non-negotiable.",
                "difficulty": "hard",
            },
            {
                "title": "Java advanced checkpoint: bounded executors",
                "stem": "Why does a service submit work to a fixed-size `ExecutorService` instead of starting a new `Thread` per request?",
                "options": [
                    "A bounded pool caps concurrent work, so a traffic spike queues or rejects gracefully instead of exhausting memory and threads",
                    "Pooled threads never throw exceptions",
                    "new Thread() cannot run user-supplied code",
                    "A pool makes each individual task finish faster",
                ],
                "correct": 0,
                "explanation": "Unbounded thread creation is a resource-exhaustion vector: each thread costs "
                               "stack memory and scheduler time. A fixed pool plus a bounded queue defines what "
                               "happens at the limit (block, reject, or shed load) - and shutdown() must be called "
                               "so the JVM can exit.",
                "difficulty": "hard",
            },
            {
                "title": "Java advanced checkpoint: authorization is its own check",
                "stem": "An HTTP endpoint publishes content and requires the content.publish capability. A request arrives with a valid student session. What must the endpoint do?",
                "options": [
                    "Check the capability server-side and answer 403 for this student - authentication proved who they are, not what they may do",
                    "Allow it: a valid session is proof of authorization",
                    "Allow it, but record a warning in the audit log",
                    "Answer 401, because the session lacks the capability",
                ],
                "correct": 0,
                "explanation": "The capability check belongs on the server, per request, regardless of what any "
                               "client shows or hides. 403 (forbidden: authenticated but not permitted) is the "
                               "honest status; 401 would claim they are not authenticated. UI hiding is not a "
                               "control.",
                "difficulty": "hard",
            },
        ],
    },
    "javascript": {
        "foundations": [
            {
                "title": "JavaScript foundations checkpoint: == versus ===",
                "stem": "What do `0 == ''` and `0 === ''` evaluate to in JavaScript?",
                "options": [
                    "true and false - == coerces types before comparing, === compares type first and never coerces",
                    "false and true - === coerces the empty string to 0",
                    "Both true, because an empty string is falsy",
                    "Both false, because a number never equals a string",
                ],
                "correct": 0,
                "explanation": "== follows coercion rules ('' becomes 0), which is why 0 == '' is true while "
                               "0 == '0' is also true and false == '0' is true. === asks: same type, same value. "
                               "Use === unless you can explain the exact coercion you want.",
                "difficulty": "easy",
            },
            {
                "title": "JavaScript foundations checkpoint: const binds names, not values",
                "stem": "Given `const user = { name: 'Asha' };`, which statement is true?",
                "options": [
                    "`user.name = 'Ravi'` is allowed; `user = {}` throws a TypeError",
                    "Both throw - const makes the whole object immutable",
                    "`user = {}` is allowed; `user.name = 'Ravi'` throws",
                    "const cannot be used with object literals",
                ],
                "correct": 0,
                "explanation": "const prevents rebinding the name, not mutating the value. The object's fields "
                               "stay writable; Object.freeze(user) would make the top level read-only (nested "
                               "objects remain mutable unless frozen too).",
                "difficulty": "easy",
            },
            {
                "title": "JavaScript foundations checkpoint: filter does not mutate",
                "stem": "After `const passed = marks.filter((m) => m >= 75);`, what is true of `marks`?",
                "options": [
                    "It is unchanged - filter returns a new array and never modifies the original",
                    "It now contains only the passing marks",
                    "It is empty, because filter consumed it",
                    "It contains the failing marks that filter removed",
                ],
                "correct": 0,
                "explanation": "map, filter and reduce build new arrays and leave the source alone, which is why "
                               "they compose safely. Methods like push, splice and sort (in place) do mutate - "
                               "know which family you are calling when the original still matters.",
                "difficulty": "easy",
            },
        ],
        "working_practice": [
            {
                "title": "JavaScript working practice checkpoint: microtasks before timers",
                "stem": "What does this log, in order? `console.log('1'); setTimeout(() => console.log('2'), 0); Promise.resolve().then(() => console.log('3')); console.log('4');`",
                "options": [
                    "1, 4, 3, 2 - synchronous code finishes, then promise microtasks run, then timer callbacks",
                    "1, 2, 3, 4 - each statement runs in the order written",
                    "1, 4, 2, 3 - a 0 ms timer fires before any promise callback",
                    "4, 1, 3, 2 - logging is deferred to the end of the tick",
                ],
                "correct": 0,
                "explanation": "The event loop drains the microtask queue (promise callbacks) after the current "
                               "synchronous run completes, before moving to timer callbacks - even a 0 ms "
                               "setTimeout. Knowing this order explains most 'why did this log last' mysteries.",
                "difficulty": "hard",
            },
            {
                "title": "JavaScript working practice checkpoint: bounded request bodies",
                "stem": "Why does a small Node HTTP API cap request body size and parse JSON inside try/catch?",
                "options": [
                    "The body is attacker-controlled work: an uncapped body can exhaust memory and malformed JSON would throw and crash the process if unhandled",
                    "Node refuses to receive bodies larger than its default cap",
                    "Capping the body makes successful responses arrive faster",
                    "JSON.parse cannot handle multi-byte characters without try/catch",
                ],
                "correct": 0,
                "explanation": "Treat every request as hostile until validated: bound the bytes, parse "
                               "defensively, answer 400 for malformed input and 413 for oversized input. An "
                               "uncaught exception in a request handler takes the whole service down, not just "
                               "that request.",
                "difficulty": "medium",
            },
            {
                "title": "JavaScript working practice checkpoint: inject the clock",
                "stem": "A 'due today' function reads `new Date()` internally and its test fails on some days. Which change makes the test deterministic?",
                "options": [
                    "Pass the current date into the function as a parameter, so the test controls it",
                    "Run the test twice and keep the passing run",
                    "Add a setTimeout before each assertion",
                    "Delete the assertions that involve dates",
                ],
                "correct": 0,
                "explanation": "A hidden clock is hidden state. Injecting it (a parameter, or a small clock "
                               "object) makes the boundary explicit and lets tests pin midnight, month ends and "
                               "leap days. node:test supports mocking timers too, but the injectable design helps "
                               "production code as well.",
                "difficulty": "medium",
            },
        ],
        "advanced_engineering": [
            {
                "title": "JavaScript advanced checkpoint: textContent prevents injection",
                "stem": "A page displays a username that another user typed. Which rendering choice prevents script injection?",
                "options": [
                    "Set `element.textContent = name` - the value becomes text and is never parsed as HTML",
                    "Set `element.innerHTML = name` after replacing < and > by hand",
                    "Set `element.innerHTML = name` inside a try/catch",
                    "Escape the name with encodeURIComponent before assigning innerHTML",
                ],
                "correct": 0,
                "explanation": "innerHTML parses markup, so any user text reaching it is an injection point "
                               "(XSS). textContent creates a text node and cannot execute. Hand-rolled escaping "
                               "misses contexts (attributes, event handlers), try/catch does not sanitize, and "
                               "encodeURIComponent is for URL components, not HTML.",
                "difficulty": "hard",
            },
            {
                "title": "JavaScript advanced checkpoint: the clipboard is an untrusted input",
                "stem": "Why should a page read the clipboard only on an explicit user action and treat pasted content as untrusted?",
                "options": [
                    "Clipboard data can come from any application, so it must be validated like any external input - and silent polling could capture sensitive data the user never meant to share",
                    "The clipboard API is deprecated in every browser",
                    "Pasted text cannot contain Unicode, so it needs decoding",
                    "Browsers encrypt clipboard content until the page is clicked",
                ],
                "correct": 0,
                "explanation": "Paste is a trust boundary: the content was authored elsewhere. Read it on user "
                               "intent, validate and bound it like a form field, render it as text, and never let "
                               "pasted data become implicit execution (no eval, no auto-followed URLs).",
                "difficulty": "hard",
            },
            {
                "title": "JavaScript advanced checkpoint: allowlisted agent tools",
                "stem": "A browser study agent can call tools you expose. Which design keeps tool use safe?",
                "options": [
                    "A fixed allowlist of tools with schema-validated arguments, plus an explicit confirmation step before anything destructive runs",
                    "Let the agent compose arbitrary JavaScript and eval it inside a try/catch",
                    "Give every tool the user's session token so calls always succeed",
                    "Rank tools by predicted usefulness and always execute the top result",
                ],
                "correct": 0,
                "explanation": "The safe shape is: closed set of tools, validated arguments, least privilege per "
                               "tool, human confirmation for irreversible effects, and an audit record. eval of "
                               "model output is arbitrary code execution; sharing the session token grants the "
                               "tool everything the user has.",
                "difficulty": "hard",
            },
        ],
    },
    "typescript": {
        "foundations": [
            {
                "title": "TypeScript foundations checkpoint: narrowing a union",
                "stem": "Given `function fmt(value: string | number)`, what must the body do before calling `value.toUpperCase()`?",
                "options": [
                    "Narrow the type first - e.g. `if (typeof value === 'string')` - because toUpperCase does not exist on number",
                    "Cast value with `as any`, which adds the method at runtime",
                    "Nothing; TypeScript selects the right method at runtime",
                    "Declare the parameter as string | number | unknown so every method exists",
                ],
                "correct": 0,
                "explanation": "A union value only exposes what every member has. A typeof guard narrows the "
                               "union inside the branch, and the compiler then allows string methods. Casting to "
                               "any silences the error without fixing the crash it predicts.",
                "difficulty": "easy",
            },
            {
                "title": "TypeScript foundations checkpoint: unknown beats any",
                "stem": "Why is `unknown` safer than `any` for data crossing a boundary?",
                "options": [
                    "unknown refuses every operation until the code narrows it, so untrusted data cannot be used by accident; any switches checking off entirely",
                    "unknown values are validated and converted at runtime",
                    "any no longer exists in modern TypeScript",
                    "unknown is faster because it skips type checking at runtime",
                ],
                "correct": 0,
                "explanation": "any is an escape hatch that propagates: one any silently disables checking "
                               "everywhere it flows. unknown says 'some value, prove its shape first' - typeof "
                               "guards, instanceof, or a runtime schema turn it into something usable.",
                "difficulty": "medium",
            },
            {
                "title": "TypeScript foundations checkpoint: reading a generic signature",
                "stem": "What does the signature `function first<T>(items: T[]): T | undefined` promise?",
                "options": [
                    "It returns either an element of the same type as the array's items, or undefined - and the empty-array case is part of the contract",
                    "It returns the first item or throws on an empty array",
                    "It works only for arrays of a single fixed type chosen at compile time",
                    "It removes the first element from the array",
                ],
                "correct": 0,
                "explanation": "The generic T carries the element type through the call, and `| undefined` "
                               "forces callers under strict null checks to handle the empty case. A signature "
                               "that hid the undefined would move the crash to the caller's first property "
                               "access.",
                "difficulty": "medium",
            },
        ],
        "working_practice": [
            {
                "title": "TypeScript working practice checkpoint: types are erased",
                "stem": "An API client types a fetch response as `User`. Why validate it with a runtime schema anyway?",
                "options": [
                    "TypeScript types are erased at compile time - the server can send anything, so the annotation is an assumption until a runtime check proves it",
                    "fetch() strips type information from JSON before parsing",
                    "Because the User interface might be misspelled in another file",
                    "Runtime validation converts JSON into class instances automatically",
                ],
                "correct": 0,
                "explanation": "The compiler checks your code, not the network. A schema library (e.g. zod) "
                               "parses the payload, rejects what does not match, and yields a value whose type "
                               "is now backed by evidence. Validate at the boundary, trust the types inside it.",
                "difficulty": "hard",
            },
            {
                "title": "TypeScript working practice checkpoint: strict null checks",
                "stem": "With strict null checks enabled, what does a return type of `Element | null` force callers to do?",
                "options": [
                    "Handle the null case explicitly - the compiler rejects using the value as an Element until it has been checked",
                    "Nothing; null is ignored at runtime like in JavaScript",
                    "Cast the result to Element before using it",
                    "Replace null with undefined at every call site",
                ],
                "correct": 0,
                "explanation": "`Element | null` documents that the lookup can fail and makes the failure "
                               "unskippable. `!` and `as Element` override the check and reintroduce exactly the "
                               "runtime TypeError strict mode exists to prevent.",
                "difficulty": "medium",
            },
            {
                "title": "TypeScript working practice checkpoint: real buttons are accessible",
                "stem": "Why does an accessible web interface use a real `<button>` element rather than a styled `<div>` with a click handler?",
                "options": [
                    "A button is keyboard-operable and announced as actionable by assistive technology with no extra work; a div gets neither by default",
                    "A div cannot receive click events in modern browsers",
                    "Buttons render faster because the browser optimizes form elements",
                    "A div cannot be styled to look like a button",
                ],
                "correct": 0,
                "explanation": "Native elements carry behaviour: focus, Enter/Space activation, and semantics "
                               "screen readers announce. Recreating that on a div needs tabindex, key handlers "
                               "and ARIA roles - more code, and easy to get wrong. Types describe your data; "
                               "semantics describe your UI to people.",
                "difficulty": "medium",
            },
        ],
        "advanced_engineering": [
            {
                "title": "TypeScript advanced checkpoint: the typed UI is not the boundary",
                "stem": "A typed frontend only renders the delete button for admins. Why must the Node API still check authorization on every delete request?",
                "options": [
                    "Any client can craft the HTTP request directly, so the typed UI is not a security boundary - the server-side check is the only one that counts",
                    "Because the frontend's types might be stale after a refactor",
                    "To improve API response times by rejecting early",
                    "Because TypeScript cannot express roles in its type system",
                ],
                "correct": 0,
                "explanation": "Types constrain your own code at compile time; attackers do not run your "
                               "frontend. The API must verify the capability per request, scope data to the "
                               "owner, and fail closed. Client-side hiding is a UX courtesy, never a control.",
                "difficulty": "hard",
            },
            {
                "title": "TypeScript advanced checkpoint: validating model-produced tool calls",
                "stem": "Agent tool calls are modelled as `type ToolCall = SearchCall | SaveCall`. What must the runtime still do when a call arrives from the model?",
                "options": [
                    "Validate the payload against the union and refuse unknown tool names - the compiler never sees data produced at runtime",
                    "Nothing; the discriminated union guarantees every arriving call is valid",
                    "Recompile the TypeScript before dispatching the call",
                    "Convert the call to a string and evaluate it",
                ],
                "correct": 0,
                "explanation": "A discriminated union makes exhaustive handling checkable inside your code, but "
                               "the model's output is external data: parse it with a runtime schema, dispatch on "
                               "the validated tag, and return a typed 'unknown tool' error for anything else. "
                               "Types describe intent; parsers enforce it.",
                "difficulty": "hard",
            },
            {
                "title": "TypeScript advanced checkpoint: the release check is more than tsc",
                "stem": "What belongs in the one-command release check for a TypeScript service?",
                "options": [
                    "Type-check, lint and the test suite together - type-checking proves shapes line up, not that behaviour is correct",
                    "Only tsc, since a program that type-checks cannot misbehave",
                    "Only end-to-end tests run against production",
                    "A manual click-through of every screen before each deploy",
                ],
                "correct": 0,
                "explanation": "Each tool catches a different class: tsc catches shape errors, lint catches "
                               "dangerous patterns (floating promises, anys), tests catch behaviour regressions. "
                               "One command (npm run check) that runs all three is the gate a release - or a CI "
                               "pipeline - can actually enforce.",
                "difficulty": "medium",
            },
        ],
    },
    "cpp": {
        "foundations": [
            {
                "title": "C++ foundations checkpoint: at() versus operator[]",
                "stem": "What is the difference between `v[i]` and `v.at(i)` on a std::vector?",
                "options": [
                    "at(i) checks the bound and throws std::out_of_range; operator[] does not check, and an out-of-range access is undefined behaviour",
                    "operator[] is bounds-checked and at(i) is the fast, unchecked access",
                    "Both throw std::out_of_range on an invalid index",
                    "Both silently return a zero-initialized element",
                ],
                "correct": 0,
                "explanation": "operator[] trades safety for speed and promises nothing past the end - the "
                               "program may appear to work and corrupt memory elsewhere. at(i) converts the "
                               "mistake into a catchable exception. Validate indices at boundaries and prefer "
                               "at(i) or explicit bounds checks on untrusted input.",
                "difficulty": "easy",
            },
            {
                "title": "C++ foundations checkpoint: references are aliases",
                "stem": "After `int x = 1; int& r = x; r = 2;`, what is true?",
                "options": [
                    "x is 2 - r is an alias for x itself, and a reference cannot be reseated to another variable",
                    "x is 1 and r is 2, because a reference holds a copy",
                    "x is 2 only until r goes out of scope, then it reverts to 1",
                    "The code does not compile; references must be const",
                ],
                "correct": 0,
                "explanation": "A reference is another name for an existing object: reads and writes go to that "
                               "object, and the binding is fixed at initialization. A pointer holds an address "
                               "and can be reassigned or null - which is why interfaces choose deliberately "
                               "between the two.",
                "difficulty": "easy",
            },
            {
                "title": "C++ foundations checkpoint: new[] pairs with delete[]",
                "stem": "What is the consequence of `int* p = new int[10];` followed by `delete p;`?",
                "options": [
                    "Undefined behaviour - memory allocated with new[] must be released with delete[]",
                    "The array is freed correctly; delete handles both forms",
                    "Only the first element leaks, which is acceptable in practice",
                    "The compiler rejects the mismatched delete",
                ],
                "correct": 0,
                "explanation": "Mismatched new/delete is undefined behaviour: the runtime may free the wrong "
                               "amount or corrupt bookkeeping. In modern C++ the fix is structural - std::vector "
                               "or std::unique_ptr<int[]> owns the memory and releases it correctly on every "
                               "path, including exceptions.",
                "difficulty": "medium",
            },
        ],
        "working_practice": [
            {
                "title": "C++ working practice checkpoint: RAII covers the error path",
                "stem": "Why does RAII keep a resource safe when an exception is thrown?",
                "options": [
                    "The destructor of a stack object runs during stack unwinding, so the resource is released even on the error path",
                    "RAII retries the failed operation until it succeeds",
                    "Destructors run when the program exits, releasing everything at once",
                    "RAII moves the resource to the heap where exceptions cannot reach it",
                ],
                "correct": 0,
                "explanation": "Tying a resource's lifetime to an object's lifetime means every exit path - "
                               "return, break, throw - releases it exactly once. Manual release calls between "
                               "new and a possible throw are the leak; std::lock_guard, fstream and smart "
                               "pointers are the RAII answer.",
                "difficulty": "medium",
            },
            {
                "title": "C++ working practice checkpoint: default to unique_ptr",
                "stem": "A heap object has exactly one owner. What is the right handle for it?",
                "options": [
                    "std::unique_ptr - it cannot be copied, so ownership stays unambiguous, and shared_ptr's reference counting buys nothing here",
                    "std::shared_ptr, because shared ownership is always safer",
                    "A raw pointer plus a comment naming the owner",
                    "std::weak_ptr as the owning handle",
                ],
                "correct": 0,
                "explanation": "unique_ptr expresses sole ownership at zero steady-state cost and moves "
                               "explicitly. shared_ptr answers 'who owns this?' with 'everyone, until no one "
                               "does' - cycles of shared_ptr leak unless broken with weak_ptr, which observes "
                               "but never owns.",
                "difficulty": "medium",
            },
            {
                "title": "C++ working practice checkpoint: headers and the one-definition rule",
                "stem": "In a multi-file C++ project, why do class definitions live in headers while ordinary function definitions live in exactly one .cpp file?",
                "options": [
                    "Every translation unit needs the class definition to compile against it, but a non-inline function defined in a header would be emitted into every unit and violate the one-definition rule at link time",
                    "Headers are compiled before source files, so they are faster",
                    "The linker cannot read definitions inside .cpp files",
                    "Classes are not allowed inside .cpp files",
                ],
                "correct": 0,
                "explanation": "The compiler needs declarations to check calls; the linker needs exactly one "
                               "definition of each non-inline function. Header-only definitions duplicate that "
                               "symbol per translation unit (duplicate-symbol errors), which is why templates and "
                               "inline functions are the deliberate exceptions.",
                "difficulty": "hard",
            },
        ],
        "advanced_engineering": [
            {
                "title": "C++ advanced checkpoint: iterator invalidation",
                "stem": "What is wrong with `for (auto it = v.begin(); it != v.end(); ++it) if (bad(*it)) v.push_back(fix(*it));`?",
                "options": [
                    "push_back can reallocate the vector's buffer, invalidating every iterator - continuing to use it is undefined behaviour",
                    "The loop never ends because end() is evaluated only once",
                    "push_back cannot be called on a vector while iterating with auto",
                    "The condition must use it-> instead of *it",
                ],
                "correct": 0,
                "explanation": "Growing past capacity moves the elements to a new buffer; old iterators, "
                               "pointers and references dangle. Collect the new values first and append after "
                               "the loop, or reserve() capacity up front when the bound is known - and remember "
                               "erase/insert invalidate too.",
                "difficulty": "hard",
            },
            {
                "title": "C++ advanced checkpoint: bounds-check a length prefix",
                "stem": "A parser reads a length prefix from an untrusted binary file. What must it do before allocating that many bytes?",
                "options": [
                    "Bounds-check the declared length against a sane maximum and the bytes actually remaining - an unchecked size can exhaust memory or overflow the allocation arithmetic",
                    "Allocate exactly the declared length; an opened file is trusted input",
                    "Round the length up to the next power of two for safety",
                    "Read the entire file into memory first, so the length cannot lie",
                ],
                "correct": 0,
                "explanation": "The prefix is a claim, not a fact. Validate it against the real remaining size "
                               "and a maximum, and prefer checked construction (resize on a vector, or a "
                               "multiplication-overflow check) over raw `new char[n * k]`. Reading the whole file "
                               "first just moves the exhaustion risk.",
                "difficulty": "hard",
            },
            {
                "title": "C++ advanced checkpoint: exceptions stop at the boundary",
                "stem": "Why does a service layer that talks to C code or crosses a plugin boundary convert exceptions into status codes?",
                "options": [
                    "Exception propagation is not guaranteed across language or ABI boundaries, so a defined error value keeps the contract explicit and testable",
                    "Exceptions are slower than every alternative in all cases",
                    "C++ forbids throwing exceptions across any function call",
                    "Status codes cannot represent distinct error kinds",
                ],
                "correct": 0,
                "explanation": "A throw that crosses into code compiled without unwinding information (a C "
                               "caller, a different compiler settings set) is undefined or terminating. At the "
                               "boundary, catch everything and translate to documented codes or an error type; "
                               "inside C++, exceptions and RAII remain the idiomatic pair.",
                "difficulty": "hard",
            },
        ],
    },
    "go": {
        "foundations": [
            {
                "title": "Go foundations checkpoint: errors are values to check",
                "stem": "What is wrong with `data, _ := os.ReadFile(path)` in production code?",
                "options": [
                    "The error is discarded, so a failed read leaves data empty or partial and the program continues as if nothing happened",
                    "Nothing - the blank identifier is the idiomatic way to handle errors",
                    "os.ReadFile cannot fail, so there is never an error to check",
                    "The compiler rejects the blank identifier in a two-value assignment",
                ],
                "correct": 0,
                "explanation": "Go returns errors as values precisely so callers decide what a failure means. "
                               "_ throws that decision away. Check err immediately, wrap it with context "
                               "(fmt.Errorf(\"...: %w\", err)) and return it, or handle it - but never ignore it "
                               "silently.",
                "difficulty": "easy",
            },
            {
                "title": "Go foundations checkpoint: nil maps and nil slices differ",
                "stem": "With `var m map[string]int` (never initialized), what happens on `m[\"a\"] = 1` versus `v := m[\"a\"]`?",
                "options": [
                    "The write panics (assignment to entry in nil map); the read returns the zero value without panicking",
                    "Both panic, because the map was never made",
                    "Both work; the map grows on demand like a slice",
                    "The write works; the read panics",
                ],
                "correct": 0,
                "explanation": "A nil map is readable (zero values) but not writable - make(map[string]int) "
                               "before storing. Nil slices behave differently: append to a nil slice works fine. "
                               "Zero values are useful, but each type's zero has its own rules.",
                "difficulty": "medium",
            },
            {
                "title": "Go foundations checkpoint: := can shadow err",
                "stem": "An outer `var err error` stays nil even though `if data, err := load(); err == nil { ... }` handled a failure inside the block. Why?",
                "options": [
                    ":= declared a new err scoped to the if statement, shadowing the outer variable - the outer err was never assigned",
                    "err is read-only outside functions in Go",
                    "If statements execute in a separate goroutine with their own memory",
                    "The compiler hoists err to package scope, resetting it",
                ],
                "correct": 0,
                "explanation": "Short variable declaration creates new variables when at least one name on the "
                               "left is new - here both are new inside the if scope. Shadowed errors are a "
                               "classic Go bug; linters (go vet -vettool shadow, golangci-lint) flag them, and "
                               "keeping err handling in one scope avoids them.",
                "difficulty": "medium",
            },
        ],
        "working_practice": [
            {
                "title": "Go working practice checkpoint: table-driven tests",
                "stem": "What makes a table-driven Go test effective?",
                "options": [
                    "One loop runs many named cases - including boundaries and error cases - through the same arrange/act/assert code, so adding a case is adding a row",
                    "It allows test cases to run without any assertions",
                    "It guarantees the cases execute in parallel",
                    "It replaces the need for the race detector",
                ],
                "correct": 0,
                "explanation": "The table separates data from logic: names make failures readable, rows make "
                               "coverage of edge cases cheap, and subtests (t.Run) allow targeting one case. "
                               "Parallelism needs an explicit t.Parallel(), and -race remains a separate, "
                               "essential check.",
                "difficulty": "medium",
            },
            {
                "title": "Go working practice checkpoint: server timeouts are a defence",
                "stem": "Why does a production `http.Server` set ReadHeaderTimeout, ReadTimeout and WriteTimeout?",
                "options": [
                    "Without them a slow or malicious client can hold connections open indefinitely (Slowloris-style) and exhaust the server's resources",
                    "Timeouts make each handler's code execute faster",
                    "net/http refuses to listen unless timeouts are configured",
                    "They encrypt traffic between client and server",
                ],
                "correct": 0,
                "explanation": "The default zero values mean 'wait forever', so one attacker with modest "
                               "bandwidth can pin every connection. Bound the whole request lifecycle - read, "
                               "header, write - and bound handler work with a context deadline. Encryption is "
                               "TLS's job, not the timeouts'.",
                "difficulty": "hard",
            },
            {
                "title": "Go working practice checkpoint: parameterized queries with database/sql",
                "stem": "Which call correctly runs `SELECT id FROM users WHERE email = $1` with database/sql?",
                "options": [
                    "db.QueryRow(query, email) - the driver binds email as a value; the query text is never built from input",
                    "db.QueryRow(fmt.Sprintf(query, email))",
                    "db.QueryRow(strings.Replace(query, \"$1\", email, 1))",
                    "db.Exec(query + email)",
                ],
                "correct": 0,
                "explanation": "Arguments after the query string are bound as data by the driver, which is what "
                               "prevents SQL injection. Any formatting or concatenation of input into the query "
                               "text re-opens it. Also check rows.Err() after iteration and handle NULL with "
                               "sql.NullString or COALESCE.",
                "difficulty": "medium",
            },
        ],
        "advanced_engineering": [
            {
                "title": "Go advanced checkpoint: bounded worker pools",
                "stem": "A health-checker must fetch thousands of URLs. Why run a fixed pool of N workers reading from a channel instead of `go check(url)` per URL?",
                "options": [
                    "A million URLs would spawn a million goroutines and exhaust memory and sockets; a bounded pool caps concurrent work while channels keep the hand-off race-free",
                    "Goroutines cannot make HTTP requests",
                    "The compiler rejects unbounded goroutine creation",
                    "A pool makes each individual check finish faster",
                ],
                "correct": 0,
                "explanation": "Goroutines are cheap but not free, and the real limits are downstream: file "
                               "descriptors, remote servers, memory. A pool of N with a jobs channel and a "
                               "WaitGroup bounds the blast radius; per-request contexts bound each unit of work.",
                "difficulty": "hard",
            },
            {
                "title": "Go advanced checkpoint: context propagates cancellation",
                "stem": "What does passing a `ctx context.Context` with a deadline into a handler and its downstream calls achieve?",
                "options": [
                    "Cancellation or timeout at the top propagates down, so abandoned requests stop consuming database, network and goroutine resources",
                    "It makes the function run concurrently in its own goroutine",
                    "It replaces the need to return errors",
                    "It caches the call's result for later requests",
                ],
                "correct": 0,
                "explanation": "Context carries deadlines, cancellation and request-scoped values through call "
                               "boundaries. Functions that block (queries, HTTP calls) select on ctx.Done() and "
                               "return early; ignoring ctx leaves work running for clients that are long gone. "
                               "Convention: ctx is the first parameter, never stored in a struct.",
                "difficulty": "hard",
            },
            {
                "title": "Go advanced checkpoint: graceful shutdown",
                "stem": "What should a Go HTTP service do when it receives SIGTERM?",
                "options": [
                    "Stop accepting new connections and let in-flight requests finish within a shutdown timeout (Server.Shutdown with a context), then close the database",
                    "Exit immediately so the supervisor can restart it cleanly",
                    "Ignore the signal until all handlers return naturally, however long that takes",
                    "Close the listener and leave handlers blocked forever",
                ],
                "correct": 0,
                "explanation": "signal.NotifyContext plus Server.Shutdown drains traffic: new connections are "
                               "refused, running ones get a bounded window, and dependent resources close in "
                               "reverse order. Exiting at once truncates requests; waiting forever blocks "
                               "deploys. Bounded, then gone.",
                "difficulty": "medium",
            },
        ],
    },
    "rust": {
        "foundations": [
            {
                "title": "Rust foundations checkpoint: assignment moves ownership",
                "stem": "After `let s = String::from(\"hi\"); let t = s;`, what happens if the program then uses `s`?",
                "options": [
                    "Compile error - s was moved into t and can no longer be used; borrowing (&s) or cloning avoids the move",
                    "s is now an empty string",
                    "s and t share one buffer and either may be used freely",
                    "The program panics at runtime when s is touched",
                ],
                "correct": 0,
                "explanation": "For heap-owning types like String, assignment transfers ownership so exactly one "
                               "owner can free the buffer - use-after-move is caught by the compiler, not by a "
                               "crash later. Copy types (i32, char) copy instead, and &s borrows without taking "
                               "ownership.",
                "difficulty": "easy",
            },
            {
                "title": "Rust foundations checkpoint: the borrowing rule",
                "stem": "Which combination of references to one value does the borrow checker allow at the same time?",
                "options": [
                    "Any number of shared references (&T), or exactly one mutable reference (&mut T) - never both together",
                    "One shared reference plus one mutable reference",
                    "Any number of mutable references, guarded at runtime",
                    "No references at all while the value is in scope",
                ],
                "correct": 0,
                "explanation": "Aliasing plus mutation is the recipe for a data race, so Rust forbids it at "
                               "compile time: readers are many, a writer is alone. The rule applies per scope, "
                               "and iterators, closures and threads all inherit it - which is why whole classes "
                               "of concurrency bugs simply do not compile.",
                "difficulty": "medium",
            },
            {
                "title": "Rust foundations checkpoint: what ? does",
                "stem": "What does `let file = File::open(path)?;` do when open fails?",
                "options": [
                    "It returns the error from the enclosing function immediately (after From conversion), keeping the happy path readable without nested match blocks",
                    "It panics with the error message",
                    "It retries the open once before giving up",
                    "It converts the error into None and continues",
                ],
                "correct": 0,
                "explanation": "? is early return with error propagation - it works in functions returning "
                               "Result (or Option). unwrap()/expect() panic instead: fine in tests and examples "
                               "with a stated reason, not a habit in libraries. The error's type must convert "
                               "into the function's error type, which keeps error contracts explicit.",
                "difficulty": "easy",
            },
        ],
        "working_practice": [
            {
                "title": "Rust working practice checkpoint: iterator adaptors are lazy",
                "stem": "Why does `lines.filter(is_error).map(to_entry)` do nothing until `.collect()` is called?",
                "options": [
                    "filter and map are lazy adaptors that build a recipe; only a consuming adaptor like collect, count or for-actually runs it",
                    "Because Vec allocates its buffer lazily on first read",
                    "Because lines is a borrowed slice and cannot execute",
                    "Because closures are evaluated at compile time",
                ],
                "correct": 0,
                "explanation": "Adaptors chain transformations without touching elements; consumers drive the "
                               "iteration. Laziness lets the whole chain fuse into one pass (no intermediate "
                               "collections) - and explains the classic bug of building a chain, never consuming "
                               "it, and wondering why nothing happened.",
                "difficulty": "medium",
            },
            {
                "title": "Rust working practice checkpoint: unit tests versus tests/",
                "stem": "What is the difference between `#[cfg(test)]` unit tests inside src/ and files under tests/?",
                "options": [
                    "Unit tests compile only under cargo test and can exercise private items; tests/ files are separate crates that see only the public API",
                    "tests/ files run before the unit tests and can abort them",
                    "Unit tests inside src/ cannot fail the build",
                    "tests/ is reserved for benchmarks, which need nightly Rust",
                ],
                "correct": 0,
                "explanation": "The split mirrors intent: unit tests sit next to the code and may reach "
                               "internals; integration tests consume the crate like any other user and prove the "
                               "public surface works. Benchmarks live in benches/ (criterion or nightly). "
                               "cargo test runs all of them.",
                "difficulty": "medium",
            },
            {
                "title": "Rust working practice checkpoint: typed errors beat strings",
                "stem": "Why should a library return a typed error (custom enum or thiserror-style) instead of `Result<T, String>`?",
                "options": [
                    "Callers can match on the kind of failure and react accordingly; a string forces fragile text comparisons and loses structure",
                    "String errors allocate more slowly than enums",
                    "The compiler forbids String in a Result position",
                    "Typed errors cannot carry human-readable messages",
                ],
                "correct": 0,
                "explanation": "An enum error makes every failure mode part of the contract: callers match "
                               "NotFound versus PermissionDenied and decide to retry, skip or abort. Display "
                               "still gives the message, and source()/? preserve the chain. A String error says "
                               "'something went wrong, guess what'.",
                "difficulty": "hard",
            },
        ],
        "advanced_engineering": [
            {
                "title": "Rust advanced checkpoint: parse, don't validate",
                "stem": "At an HTTP boundary, why parse request data into validated types once instead of re-checking fields ad hoc throughout the code?",
                "options": [
                    "After parsing, the type system carries the invariants into every later use; scattered checks leave code paths where unvalidated data slips through",
                    "Parsing is measurably faster than validating in every case",
                    "Types make all runtime errors impossible once compiled",
                    "Validation cannot be expressed in Rust's type system at all",
                ],
                "correct": 0,
                "explanation": "A `ValidatedEmail` newtype or a parsed config struct proves its contents at "
                               "construction, so downstream functions cannot receive the invalid case at all. "
                               "Ad-hoc checks are per-call-site discipline; the type makes the discipline "
                               "structural. Parse at the edge, trust the interior.",
                "difficulty": "hard",
            },
            {
                "title": "Rust advanced checkpoint: closed tool registries still refuse at runtime",
                "stem": "An agent's tool registry is an enum, but the model outputs a tool name as text. What keeps the dispatch safe when the name is unknown?",
                "options": [
                    "Parsing the name against the closed set returns a typed UnknownTool error that the agent reports back - compilation never sees runtime-produced strings",
                    "The compiler rejects unknown tool names when the binary is built",
                    "The registry should panic so the operator notices the misuse",
                    "Unknown names are skipped silently and the agent moves on",
                ],
                "correct": 0,
                "explanation": "The enum guarantees exhaustiveness inside the program; the string from the model "
                               "still has to cross the boundary through a total parse function (TryFrom or a "
                               "match) whose failure case is a value, not a crash. Panicking on model output "
                               "turns a bad suggestion into an outage; silence hides it.",
                "difficulty": "hard",
            },
            {
                "title": "Rust advanced checkpoint: Send and Sync are compile-time proof",
                "stem": "What do the Send and Sync marker traits guarantee in a concurrent Rust service?",
                "options": [
                    "The compiler checks that values crossing thread boundaries (Send) or shared between threads (Sync) are safe to do so, rejecting data races at compile time",
                    "They make shared state lock-free automatically",
                    "They are runtime checks executed before each cross-thread call",
                    "They remove the need for Arc<Mutex<T>> or channels",
                ],
                "correct": 0,
                "explanation": "Send/Sync are auto-implemented proof obligations: Rc is neither (use Arc), "
                               "RefCell is not Sync (use Mutex/RwLock). Sharing still needs a strategy - "
                               "Arc<Mutex<T>> for guarded state, channels for ownership hand-off - but the "
                               "compiler guarantees you cannot forget the guard.",
                "difficulty": "medium",
            },
        ],
    },
    "c": {
        "foundations": [
            {
                "title": "C foundations checkpoint: no bounds checks",
                "stem": "A program declares `int a[5];` and writes to `a[5]`. What happens?",
                "options": [
                    "Undefined behaviour - C performs no bounds check, so the write lands on whatever memory follows the array",
                    "The array grows automatically to hold the sixth element",
                    "The runtime raises a bounds error at that line",
                    "The value is discarded and the program continues safely",
                ],
                "correct": 0,
                "explanation": "Valid indices are 0..4. Writing a[5] may corrupt a neighbouring variable, a "
                               "saved return address, or nothing visible today - which is why it survives casual "
                               "testing. Tools (compiler warnings, -fsanitize=address, static analysers) exist "
                               "because the language will not stop you.",
                "difficulty": "easy",
            },
            {
                "title": "C foundations checkpoint: uninitialized locals",
                "stem": "Why can reading an uninitialized local variable produce a bug that appears on one machine and not another?",
                "options": [
                    "Its value is whatever bits happen to occupy that stack memory, so behaviour varies with prior calls, builds and machines",
                    "The C standard defines it as zero, but some compilers disagree",
                    "Local variables are allocated on the heap, which is shared between runs",
                    "The linker assigns random initial values per platform",
                ],
                "correct": 0,
                "explanation": "Reading an uninitialized automatic variable is undefined behaviour: the bits are "
                               "leftovers from earlier stack frames. Initialize at declaration (= {0} for "
                               "structs), and let warnings (-Wuninitialized, -Wall -Wextra) catch the rest.",
                "difficulty": "medium",
            },
            {
                "title": "C foundations checkpoint: what strlen counts",
                "stem": "For a C string `char s[] = \"hello\";`, what does `strlen(s)` return?",
                "options": [
                    "5 - it counts the bytes before the terminating NUL; the NUL itself is not counted, while sizeof(s) is 6",
                    "6 - it counts every byte of the array including the terminator",
                    "5 only if the array was declared with an explicit size",
                    "It returns a pointer to the last character",
                ],
                "correct": 0,
                "explanation": "A C string is a byte sequence ending at the first '\\0'. strlen walks to that "
                               "terminator, so a missing terminator makes it read past the buffer - the source "
                               "of countless overflows. sizeof on the array includes the terminator; on a "
                               "pointer parameter it is the pointer's size, not the string's.",
                "difficulty": "medium",
            },
        ],
        "working_practice": [
            {
                "title": "C working practice checkpoint: structs pass by value",
                "stem": "A function `void bump(struct Point p) { p.x += 1; }` is called with a local struct. What is true of the caller's variable afterwards?",
                "options": [
                    "It is unchanged - C passes structs by value, so bump() modifies a copy; a pointer parameter (struct Point *p) is needed to affect the original",
                    "It gained 1 in x, because structs are always passed by reference",
                    "The compiler rejects modifying a parameter field",
                    "The struct is converted to a pointer automatically at the call",
                ],
                "correct": 0,
                "explanation": "Everything in C is passed by value, including whole structs - which also costs a "
                               "copy. Pass a pointer to modify the caller's object (and say so in the interface), "
                               "or const struct Point * to read a large struct without copying it.",
                "difficulty": "medium",
            },
            {
                "title": "C working practice checkpoint: freeing a list safely",
                "stem": "When destroying a singly linked list, why must the code save `next` before calling `free(node)`?",
                "options": [
                    "After free(node), reading node->next is a use-after-free - the memory no longer belongs to the program, so the pointer to the rest of the list must be copied first",
                    "free() sets node->next to NULL, hiding the rest of the list",
                    "free() is asynchronous and runs after the loop finishes",
                    "Only the head node may be freed while the list is linked",
                ],
                "correct": 0,
                "explanation": "The safe walk is `while (n) { struct Node *next = n->next; free(n); n = next; }`. "
                               "Every malloc gets exactly one free: freeing twice is undefined behaviour, and "
                               "never freeing leaks. Ownership - who allocates, who frees - is part of a C "
                               "interface's contract.",
                "difficulty": "hard",
            },
            {
                "title": "C working practice checkpoint: prototypes are contracts",
                "stem": "Why must a function's prototype in a header match its definition exactly?",
                "options": [
                    "A call compiled against a mismatched prototype passes arguments the callee does not expect - undefined behaviour, and in older C dialects not even a required diagnostic",
                    "The linker renames functions to match the header automatically",
                    "Prototypes exist only as documentation for readers",
                    "The C library detects mismatches at runtime and aborts",
                ],
                "correct": 0,
                "explanation": "The prototype is how the compiler knows the calling convention: argument count, "
                               "types and order. A mismatch corrupts the call - wrong sizes on the stack, "
                               "reinterpreted bits. Including the header in the definition's .c file makes the "
                               "compiler verify both sides agree.",
                "difficulty": "hard",
            },
        ],
        "advanced_engineering": [
            {
                "title": "C advanced checkpoint: check fopen and friends",
                "stem": "Why must every `fopen` result be checked before it is used?",
                "options": [
                    "fopen returns NULL on failure (missing file, permissions, descriptor limit); passing NULL to fread or fprintf is undefined behaviour and typically crashes",
                    "fopen is asynchronous and the handle arrives later",
                    "NULL indicates the file exists but is empty",
                    "On Linux the check is optional because failures cannot happen",
                ],
                "correct": 0,
                "explanation": "The professional habit is checking every fallible call: fopen against NULL, "
                               "fread/fwrite against short counts and ferror, fclose against failure on streams "
                               "that wrote (flush errors surface there). Each failure mode has a decision - "
                               "retry, report, degrade - and skipping the check makes that decision by accident.",
                "difficulty": "medium",
            },
            {
                "title": "C advanced checkpoint: size arithmetic overflows",
                "stem": "Before `malloc(n * sizeof(int))` where n was read from a file, what must be checked?",
                "options": [
                    "That n is within a sane bound and that the multiplication cannot overflow - a wrapped size allocates a small buffer that later writes overrun",
                    "Nothing; malloc rejects any dangerous size by returning the requested bytes anyway",
                    "That n is positive, which is sufficient because overflow cannot occur in size arithmetic",
                    "That sizeof(int) is 4 before trusting the product",
                ],
                "correct": 0,
                "explanation": "n from a file is attacker-chosen. If n * sizeof(int) wraps past SIZE_MAX, malloc "
                               "succeeds with a tiny buffer and every subsequent write is a heap overflow. "
                               "calloc(n, sizeof(int)) performs the multiplication with an overflow check; "
                               "an explicit maximum on n is the other half of the defence.",
                "difficulty": "hard",
            },
            {
                "title": "C advanced checkpoint: sanitizers in the loop",
                "stem": "What does building tests with `-fsanitize=address,undefined` add to a C workflow?",
                "options": [
                    "It turns silent memory and undefined-behaviour bugs - overruns, use-after-free, invalid shifts - into reported errors while the tests run",
                    "It makes the shipped binary faster by removing checks at link time",
                    "It replaces the need for a test suite",
                    "It encrypts global variables against tampering",
                ],
                "correct": 0,
                "explanation": "Sanitizers instrument the build so bugs announce themselves with a stack trace "
                               "instead of corrupting memory quietly. Run them in CI on the test suite (they add "
                               "runtime overhead, so not usually in production); Valgrind is the "
                               "no-recompile alternative. A bug only a sanitizer catches is still a bug caught.",
                "difficulty": "medium",
            },
        ],
    },
    "sql": {
        "foundations": [
            {
                "title": "SQL foundations checkpoint: WHERE runs before GROUP BY",
                "stem": "In a query with both WHERE and GROUP BY, when does the WHERE filter apply?",
                "options": [
                    "Before grouping - it selects which rows enter the aggregation; conditions on aggregate results belong in HAVING",
                    "After grouping, filtering the computed groups",
                    "After ORDER BY, as the final step",
                    "Only when an index supports the condition",
                ],
                "correct": 0,
                "explanation": "The logical order is FROM/JOIN, WHERE, GROUP BY, HAVING, SELECT, ORDER BY, "
                               "LIMIT. WHERE cannot reference aggregates because they do not exist yet; HAVING "
                               "filters groups after aggregation. Knowing the order explains most 'column not "
                               "found here' errors.",
                "difficulty": "easy",
            },
            {
                "title": "SQL foundations checkpoint: deterministic pages need a tiebreaker",
                "stem": "Why does `ORDER BY created_at LIMIT 10 OFFSET 10` sometimes skip or repeat rows when many rows share a timestamp?",
                "options": [
                    "Equal values may be ordered differently between executions - adding a unique tiebreaker (ORDER BY created_at, id) makes page boundaries deterministic",
                    "LIMIT counts from zero, so every page is shifted by one row",
                    "OFFSET deletes the skipped rows permanently",
                    "Timestamps cannot be used in ORDER BY at all",
                ],
                "correct": 0,
                "explanation": "The database only promises the order you ask for; ties are resolved arbitrarily "
                               "and can change with the plan. A unique final key (the primary key) gives one "
                               "total order, so pagination and 'latest row' queries stay stable across runs.",
                "difficulty": "medium",
            },
            {
                "title": "SQL foundations checkpoint: DISTINCT applies to the whole row",
                "stem": "What does `SELECT DISTINCT branch, year FROM students` return?",
                "options": [
                    "One row per distinct (branch, year) combination - DISTINCT applies to all selected columns together, not to each one separately",
                    "Distinct branches only, with an arbitrary year attached",
                    "All rows, with duplicates flagged in an extra column",
                    "The number of distinct branches as a count",
                ],
                "correct": 0,
                "explanation": "DISTINCT collapses identical result rows across the whole SELECT list. For "
                               "per-column distinctness (branches with their earliest year, say) use GROUP BY "
                               "with an aggregate. A COUNT(DISTINCT branch) is how the count itself is asked "
                               "for.",
                "difficulty": "easy",
            },
        ],
        "working_practice": [
            {
                "title": "SQL working practice checkpoint: the LEFT JOIN that acts inner",
                "stem": "A report should list every student, including those with no submission, via `LEFT JOIN submissions s ON s.student_id = st.id WHERE s.score > 50`. Why do the no-submission students disappear?",
                "options": [
                    "Their joined columns are NULL, and NULL > 50 is not true, so the WHERE filters them out - the condition turns the LEFT JOIN into an INNER JOIN; it belongs in ON, or must allow NULL",
                    "LEFT JOIN never produces NULL columns, so the query is fine and the data is wrong",
                    "WHERE executes before the JOIN, removing students early",
                    "score > 50 also excludes zero scores, which is the only real difference",
                ],
                "correct": 0,
                "explanation": "The classic outer-join trap: filtering the right table in WHERE undoes the "
                               "outer-ness. Either move the predicate into the ON clause (keeping unmatched "
                               "students) or write WHERE (s.score > 50 OR s.student_id IS NULL) - and know which "
                               "report you meant.",
                "difficulty": "hard",
            },
            {
                "title": "SQL working practice checkpoint: COUNT(*) versus COUNT(column)",
                "stem": "Over the same set of rows, what is the difference between `COUNT(*)` and `COUNT(email)`?",
                "options": [
                    "COUNT(*) counts rows; COUNT(email) counts only rows where email is not NULL",
                    "They always return the same number",
                    "COUNT(*) also skips rows where every column is NULL",
                    "COUNT(email) counts distinct email addresses",
                ],
                "correct": 0,
                "explanation": "Aggregates ignore NULLs per column, so COUNT(email) silently under-reports when "
                               "the column is nullable - a report that 'lost' users is usually this. COUNT("
                               "DISTINCT email) is the distinct count; COUNT(*) is the honest row count.",
                "difficulty": "medium",
            },
            {
                "title": "SQL working practice checkpoint: NULL makes comparisons unknown",
                "stem": "With status values 'open', 'closed' and NULL, what does `WHERE status <> 'closed'` return?",
                "options": [
                    "Only rows where status is 'open' - NULL <> 'closed' evaluates to UNKNOWN, which is not true, so NULL rows are excluded",
                    "Rows with 'open' and rows with NULL, since NULL is not 'closed'",
                    "Every row that is not literally the text 'closed', NULLs included",
                    "A syntax error; <> cannot be used with nullable columns",
                ],
                "correct": 0,
                "explanation": "SQL is three-valued: true, false, unknown - and only true passes a filter. Any "
                               "comparison with NULL yields unknown, including NULL = NULL (use IS NULL). To "
                               "include NULLs, branch explicitly (OR status IS NULL) or use the engine's "
                               "null-safe operator (IS DISTINCT FROM in PostgreSQL, IS NOT in SQLite).",
                "difficulty": "hard",
            },
        ],
        "advanced_engineering": [
            {
                "title": "SQL advanced checkpoint: leftmost prefix of a composite index",
                "stem": "An index is defined on (tenant_id, created_at). Which query can use it fully?",
                "options": [
                    "WHERE tenant_id = 7 ORDER BY created_at - the leading column is matched by equality and the second supplies the ordering",
                    "WHERE created_at > '2026-01-01' with no tenant_id condition",
                    "Any query on the table, because an index accelerates everything",
                    "WHERE title LIKE '%cat%' on an indexed title column",
                ],
                "correct": 0,
                "explanation": "B-tree composite indexes serve leftmost prefixes: tenant_id alone, or tenant_id "
                               "then created_at. Skipping the leading column leaves the index unusable for a "
                               "range on the second, and a leading-wildcard LIKE cannot seek a B-tree at all. "
                               "Every index also slows writes, so index for the queries that actually run.",
                "difficulty": "hard",
            },
            {
                "title": "SQL advanced checkpoint: one transaction or half a transfer",
                "stem": "Why must 'deduct from account A, then add to account B' run inside a single transaction?",
                "options": [
                    "Without it a failure between the two statements leaves money deducted but never added; a transaction makes both commit or neither, and isolates the pair from concurrent readers",
                    "Transactions make individual writes execute faster",
                    "Account tables require an index before they can be updated",
                    "It lets A and B be updated by independent sessions in parallel",
                ],
                "correct": 0,
                "explanation": "Atomicity is the point: BEGIN ... COMMIT with a ROLLBACK on any error keeps the "
                               "ledger consistent, and isolation keeps a concurrent reader from seeing the "
                               "half-transfer. The same reasoning covers any multi-statement change that must "
                               "stand or fall together.",
                "difficulty": "hard",
            },
            {
                "title": "SQL advanced checkpoint: parameters and least privilege",
                "stem": "A report tool runs queries influenced by user input. Which pair of controls addresses both injection and blast radius?",
                "options": [
                    "Never splice user text into SQL - bind parameters or accept only a validated allowlist of queries - and run the application's database account with least privilege (no DDL, only the tables it needs)",
                    "Double every single quote in the input and connect as the database superuser so queries never fail",
                    "Run each query twice and compare the results before displaying them",
                    "Validate the SQL syntax in the browser before sending it",
                ],
                "correct": 0,
                "explanation": "Parameter binding keeps user data out of the SQL program; an allowlist keeps "
                               "even query shape fixed when values are not enough. Least privilege limits what a "
                               "successful injection can do - DROP TABLE fails for an account that cannot run "
                               "DDL. Quote-doubling is a blacklist with a long history of bypasses.",
                "difficulty": "hard",
            },
        ],
    },
    "csharp": {
        "foundations": [
            {
                "title": "C-sharp foundations checkpoint: value types copy, references share",
                "stem": "After `int a = 5; int b = a; b = 9;` and separately `var p = new List<int> { 1 }; var q = p; q.Add(2);`, what is true?",
                "options": [
                    "a is still 5 because int is a value type that copies on assignment, while p now holds 2 items because List<T> is a reference type and q points at the same object",
                    "a is 9 because assignment always aliases, and p still holds 1 item because collections copy on assignment",
                    "Both a and p are unchanged, because C# assignments never affect the source",
                    "The code does not compile; var cannot be used with collection initializers",
                ],
                "correct": 0,
                "explanation": "Value types (int, double, bool, struct) carry their data with them: assignment "
                               "copies the value. Reference types (class, interface, string, arrays, List<T>) "
                               "carry a pointer: assignment copies the pointer, so both names observe the same "
                               "object. Knowing which family a type belongs to predicts aliasing bugs.",
                "difficulty": "easy",
            },
            {
                "title": "C-sharp foundations checkpoint: var is still statically typed",
                "stem": "What does `var total = 0;` declare in C#?",
                "options": [
                    "An int, exactly as if int had been written - the compiler infers the type from the initializer and total cannot later hold a string",
                    "A dynamically typed variable that can hold any type at runtime",
                    "An implicitly nullable int that starts as null",
                    "Nothing; var is only allowed for loop variables",
                ],
                "correct": 0,
                "explanation": "var is shorthand for the compiler, not dynamic typing: the declared type is "
                               "fixed at compile time from the right-hand side, so `total = \"x\"` fails to "
                               "build. Use var when the type is obvious from the initializer; write the type "
                               "explicitly when it carries meaning the reader cannot see.",
                "difficulty": "easy",
            },
            {
                "title": "C-sharp foundations checkpoint: null-coalescing gives a default",
                "stem": "With `string? name = null;`, what does `name ?? \"guest\"` evaluate to?",
                "options": [
                    "\"guest\" - ?? returns the left side when it is non-null, otherwise the right side, so it supplies a default for a missing value",
                    "null, because ?? propagates null like every other operator",
                    "It throws NullReferenceException, because name was dereferenced",
                    "It does not compile; ?? requires both sides to be non-nullable",
                ],
                "correct": 0,
                "explanation": "The ?? operator is the concise null-default: left ?? right reads as 'left, or "
                               "right when left is null'. Its relatives are ?. (null-conditional access, which "
                               "short-circuits to null) and throw expressions for fail-fast guards. Together "
                               "they replace most explicit null checks.",
                "difficulty": "medium",
            },
        ],
        "working_practice": [
            {
                "title": "C-sharp working practice checkpoint: LINQ queries are lazy",
                "stem": "A program builds `var adults = users.Where(u => u.Age >= 18);`, adds another user to the list, then enumerates adults twice. What happens?",
                "options": [
                    "The query re-executes on every enumeration against the current list contents, so the new user appears and any side effect in the predicate runs twice - call ToList() to freeze one snapshot",
                    "adults holds a snapshot taken when Where was called, so the new user never appears",
                    "The second enumeration throws because a query can only be enumerated once",
                    "The predicate runs once per user at the Where call, and enumeration is free",
                ],
                "correct": 0,
                "explanation": "Most LINQ operators return a lazy recipe, not results: nothing runs until the "
                               "sequence is enumerated, and each enumeration re-runs the pipeline against the "
                               "live source. That is efficient for chains but surprising for repeated or "
                               "timed enumeration - materialize with ToList()/ToArray() when you need one "
                               "stable pass.",
                "difficulty": "hard",
            },
            {
                "title": "C-sharp working practice checkpoint: program to the interface",
                "stem": "Why should a method take `IList<Order>` (or `IReadOnlyList<Order>`) instead of `List<Order>`?",
                "options": [
                    "Callers depend on the contract, so the method accepts any implementation - including arrays and test fakes - and IReadOnlyList additionally promises the method will not modify the caller's data",
                    "Interfaces execute faster than concrete classes in .NET",
                    "List<T> cannot be passed across method boundaries",
                    "An interface parameter automatically validates the elements",
                ],
                "correct": 0,
                "explanation": "The interface is the promise (indexed, countable, enumerable); List<T> is one "
                               "way to keep it. Depending on the contract keeps callers flexible and tests "
                               "simple, and the read-only variant documents non-mutation in the signature "
                               "itself. The same rule applies to IDictionary<TKey, TValue> and IEnumerable<T>.",
                "difficulty": "medium",
            },
            {
                "title": "C-sharp working practice checkpoint: using releases deterministically",
                "stem": "Why wrap a `StreamReader` in a `using` declaration instead of just letting the garbage collector handle it?",
                "options": [
                    "using calls Dispose at the end of the scope, releasing the file handle deterministically - the garbage collector reclaims memory on its own schedule and does not close handles promptly",
                    "The garbage collector cannot collect StreamReader objects at all",
                    "using makes file reads measurably faster",
                    "Without using, the file contents are never flushed to the reader",
                ],
                "correct": 0,
                "explanation": "IDisposable separates scarce unmanaged resources (handles, connections, locks) "
                               "from memory: Dispose releases them now, while finalization runs later if at "
                               "all. using generates the try/finally that guarantees disposal on every path, "
                               "including exceptions - the C# equivalent of RAII.",
                "difficulty": "medium",
            },
        ],
        "advanced_engineering": [
            {
                "title": "C-sharp advanced checkpoint: await frees the thread",
                "stem": "An ASP.NET endpoint awaits an `HttpClient.GetAsync` call. Why is that better than blocking on `.Result`, and what does await do while waiting?",
                "options": [
                    "await returns the thread to the pool while the I/O is in flight so it can serve other requests, then resumes after the await; blocking with .Result holds the thread (and risks deadlock under a synchronization context)",
                    "await makes the HTTP call itself complete faster",
                    ".Result and await are identical; await is only shorter to type",
                    "await moves the request to a new thread that is reserved for it",
                ],
                "correct": 0,
                "explanation": "Async I/O is about thread economics, not speed: thousands of concurrent "
                               "requests share a small pool because waiting requests hold no thread. Blocking "
                               "calls defeat that sharing and can deadlock when the continuation needs the "
                               "blocked context. Async all the way down, with ConfigureAwait(false) in "
                               "libraries, is the discipline.",
                "difficulty": "hard",
            },
            {
                "title": "C-sharp advanced checkpoint: the GetHashCode contract",
                "stem": "A class overrides `Equals` so two instances with the same Id compare equal, but does not override `GetHashCode`. What breaks?",
                "options": [
                    "Hash-based collections misbehave: equal objects land in different Dictionary buckets, so lookups miss and a HashSet can hold 'duplicates' - equal objects must return equal hash codes",
                    "Nothing; Dictionary compares keys with Equals only",
                    "The program fails to compile, because Equals requires GetHashCode",
                    "Only sorting breaks; hashing is unaffected",
                ],
                "correct": 0,
                "explanation": "The contract is: equal objects, equal hash codes. Dictionaries and hash sets "
                               "bucket by the hash first and only then call Equals, so a default "
                               "identity-based GetHashCode scatters equal keys across buckets. Overriding one "
                               "without the other is a classic defect - records get both generated for free.",
                "difficulty": "hard",
            },
            {
                "title": "C-sharp advanced checkpoint: authorize on the server, per request",
                "stem": "A frontend only shows the delete button to admins. Why must the minimal API behind it still check the caller's role on every delete request?",
                "options": [
                    "Any client can craft the HTTP request directly, so the UI is not a security boundary - role and ownership checks belong on the server, per request, regardless of what any page shows",
                    "Because the frontend's cached role might be stale after a deploy",
                    "To make delete requests measurably faster by rejecting early",
                    "Because minimal APIs cannot read authorization headers",
                ],
                "correct": 0,
                "explanation": "Client-side hiding is a courtesy, never a control: attackers do not run your "
                               "UI. The endpoint must authenticate the caller, authorize the action (role plus "
                               "ownership of the specific resource), validate the input, and fail closed - "
                               "with 401 for unauthenticated and 403 for authenticated-but-forbidden.",
                "difficulty": "hard",
            },
        ],
    },
}

_DIFFICULTIES = {"easy", "medium", "hard"}


def _slugify(value: str) -> str:
    # Keep aligned with engineverse.security.sanitize.slugify: apostrophes are
    # removed, not converted into word separators.
    cleaned = value.lower().replace("\u2019", "").replace("'", "")
    return re.sub(r"[^a-z0-9]+", "-", cleaned).strip("-")[:96].strip("-") or "item"


def module_stage_map() -> dict[str, dict[str, str]]:
    """{language slug: {module slug: stage slug}} for every assignment above."""
    result: dict[str, dict[str, str]] = {}
    for language, stages in MODULE_STAGES.items():
        assignment: dict[str, str] = {}
        for stage, module_slugs in stages.items():
            for module_slug in module_slugs:
                assignment[module_slug] = stage
        result[language] = assignment
    return result


def checkpoint_questions() -> list[dict]:
    """Checkpoint entries in the shape ``scripts/seed.py`` seeds questions from.

    Correct-answer positions are rotated by a deterministic shift derived from
    the entry's position in this fixed iteration order, exactly as
    ``subject_paths`` rotates its generated questions. A reseed therefore
    reproduces the same bank, while the stored answer key is not a visible
    position pattern.
    """
    entries: list[dict] = []
    index = 0
    for language in LANGUAGE_ORDER:
        for stage, _title, _summary in STAGES:
            for order, checkpoint in enumerate(CHECKPOINTS[language][stage]):
                options = list(checkpoint["options"])
                correct = int(checkpoint["correct"])
                shift = index % len(options)
                options = options[shift:] + options[:shift]
                correct = (correct - shift) % len(options)
                entries.append({
                    "subject": CHECKPOINT_SUBJECT,
                    "topic": None,
                    "title": checkpoint["title"],
                    "difficulty": checkpoint["difficulty"],
                    "statement": checkpoint["stem"],
                    "options": options,
                    "correct": correct,
                    "explanation": checkpoint["explanation"],
                    "tags": [language, stage, "checkpoint"],
                    "source": "EngineVerse language checkpoint",
                    "language": language,
                    "stage": stage,
                    "order": order,
                    "slug": _slugify(checkpoint["title"]),
                })
                index += 1
    return entries


def checkpoint_links() -> list[tuple[str, str, str, int]]:
    """(language, stage, question slug, order) rows for ``language_checkpoints``."""
    return [(entry["language"], entry["stage"], entry["slug"], entry["order"])
            for entry in checkpoint_questions()]


def validate(languages: set[str], modules_by_language: dict[str, list[str]]) -> None:
    """Fail the seed on any drift between this file and the module catalogue.

    Checks languages, modules and checkpoints together, collecting every
    problem so one run names all of them instead of one per reseed.
    """
    problems: list[str] = []

    if set(LANGUAGE_ORDER) != languages:
        problems.append(
            f"LANGUAGE_ORDER does not match the seeded languages: "
            f"missing {sorted(languages - set(LANGUAGE_ORDER))}, "
            f"unknown {sorted(set(LANGUAGE_ORDER) - languages)}"
        )
    if set(MODULE_STAGES) != languages:
        problems.append(f"MODULE_STAGES covers {sorted(set(MODULE_STAGES) - languages)} which are not languages")
    if set(CHECKPOINTS) != languages:
        problems.append(f"CHECKPOINTS covers {sorted(set(CHECKPOINTS) - languages)} which are not languages")

    stage_map = module_stage_map()
    for language in sorted(languages):
        known_modules = list(modules_by_language.get(language, []))
        assigned = stage_map.get(language, {})
        if not known_modules:
            problems.append(f"{language}: no modules are seeded for this language")
            continue
        missing = [slug for slug in known_modules if slug not in assigned]
        unknown = sorted(set(assigned) - set(known_modules))
        if missing:
            problems.append(f"{language}: modules with no stage assignment: {missing}")
        if unknown:
            problems.append(f"{language}: stage assignments to modules that do not exist: {unknown}")
        for stage in STAGE_SLUGS:
            staged = MODULE_STAGES.get(language, {}).get(stage, [])
            if not staged:
                problems.append(f"{language}: stage {stage!r} has no modules")

    titles: set[str] = set()
    for language in LANGUAGE_ORDER:
        for stage in STAGE_SLUGS:
            entries = CHECKPOINTS.get(language, {}).get(stage)
            if entries is None:
                problems.append(f"{language}: stage {stage!r} has no checkpoints")
                continue
            if len(entries) < 3:
                problems.append(f"{language}/{stage}: {len(entries)} checkpoints, at least 3 required")
            for entry in entries:
                title = entry.get("title", "")
                if not title or title in titles:
                    problems.append(f"{language}/{stage}: duplicate or empty checkpoint title {title!r}")
                titles.add(title)
                if len(entry.get("options", [])) != 4:
                    problems.append(f"{title!r}: needs exactly four options")
                if not 0 <= int(entry.get("correct", -1)) < 4:
                    problems.append(f"{title!r}: correct index {entry.get('correct')!r} is out of range")
                if not entry.get("stem", "").strip():
                    problems.append(f"{title!r}: empty stem")
                if len(entry.get("explanation", "").strip()) < 40:
                    problems.append(f"{title!r}: explanation is missing or stub-thin")
                if entry.get("difficulty") not in _DIFFICULTIES:
                    problems.append(f"{title!r}: difficulty {entry.get('difficulty')!r} is not easy/medium/hard")

    if problems:
        raise ValueError(
            "language_curriculum.py does not match the seeded catalogue:\n  " + "\n  ".join(problems)
        )

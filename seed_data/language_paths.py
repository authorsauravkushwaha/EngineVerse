"""Extra language modules so every listed language has a scratch-to-working path.

These are standard language facts, not a complete reference and not a claim
that reading them makes someone job-ready. The seeder appends them after the
modules already in library_data.
"""

EXTRA_MODULES = {
    "java": [
        (
            "java-testing",
            "Testing the behaviour",
            "A professional Java change is one you can prove still works.",
            "A test calls the code and checks the result. Name it after the behaviour, "
            "not after the method: `withdraw_refuses_to_overdraw`, not `test1`.\n\n"
            "You do not need a framework to start. A small `check` method that throws "
            "when the expectation is wrong is a real test. JUnit, when you add it later, "
            "is the same idea with a runner and a report.\n\n"
            "Cover the boundaries: empty input, zero, the exact threshold, and one step "
            "past it. Those are where the defects are. A suite that only tests the happy "
            "path will stay green while the bug ships.",
            "public class Main {\n"
            "    static void check(boolean condition, String message) {\n"
            "        if (!condition) throw new AssertionError(message);\n"
            "    }\n\n"
            "    static int clamp(int value, int low, int high) {\n"
            "        return Math.max(low, Math.min(high, value));\n"
            "    }\n\n"
            "    public static void main(String[] args) {\n"
            "        check(clamp(150, 0, 100) == 100, \"above the range\");\n"
            "        check(clamp(-3, 0, 100) == 0, \"below the range\");\n"
            "        check(clamp(40, 0, 100) == 40, \"inside the range\");\n"
            "        check(clamp(0, 0, 100) == 0, \"exact lower bound\");\n"
            "        System.out.println(\"all checks passed\");\n"
            "    }\n"
            "}",
            "Write three checks for a withdraw method: a normal withdrawal, an exact-balance withdrawal, and an overdraw that must be refused.",
        ),
    ],
    "javascript": [
        (
            "js-objects",
            "Objects and arrays",
            "The two structures almost every JavaScript program is made of.",
            "An array is an ordered list. An object is a set of named fields. "
            "`const user = { name: 'Asha', marks: [72, 85] }` is both.\n\n"
            "Copying an object with `const copy = user` does not copy it. Both names "
            "point at the same object, so a change through one is visible through the "
            "other. `const copy = { ...user }` copies the top level only. Nested arrays "
            "are still shared.\n\n"
            "`map`, `filter` and `reduce` build a new array. They do not change the "
            "old one. Prefer that when the old list still matters.",
            "const marks = [72, 85, 91, 68];\n"
            "const passed = marks.filter((mark) => mark >= 75);\n"
            "const average = marks.reduce((sum, mark) => sum + mark, 0) / marks.length;\n"
            "const report = { count: marks.length, average, passed };\n"
            "console.log(report);\n"
            "console.log(marks.length); // still 4 — filter did not change it",
            "Build an array of three subject names and an object that stores the average mark for each. Print the subject with the highest average.",
        ),
        (
            "js-errors",
            "Errors and untrusted input",
            "What a program should do when the input is missing, wrong, or hostile.",
            "`try / catch` handles a failure you can recover from. A bare `catch (e) {}` "
            "that ignores the error hides the bug. Log it, or let it surface.\n\n"
            "Never build HTML from a string that contains what a user typed. "
            "`element.innerHTML = name` is how a page gets script injected into it. "
            "Set `textContent` instead.\n\n"
            "`===` does not coerce types. `==` does, and `0 == ''` is true. Use `===` "
            "unless you have a reason you can explain.",
            "function grade(score) {\n"
            "  if (typeof score !== 'number' || Number.isNaN(score)) {\n"
            "    throw new TypeError('score must be a number');\n"
            "  }\n"
            "  if (score < 0 || score > 100) {\n"
            "    throw new RangeError('score must be between 0 and 100');\n"
            "  }\n"
            "  if (score >= 90) return 'A';\n"
            "  if (score >= 75) return 'B';\n"
            "  if (score >= 50) return 'C';\n"
            "  return 'F';\n"
            "}\n\n"
            "for (const value of [91, 50, -1, '72']) {\n"
            "  try {\n"
            "    console.log(value, grade(value));\n"
            "  } catch (error) {\n"
            "    console.log(value, error.name, error.message);\n"
            "  }\n"
            "}",
            "Write grade so that the exact boundaries 90, 75 and 50 are the higher grade, and a string is rejected rather than coerced.",
        ),
        (
            "js-modules",
            "Modules and a professional habit",
            "Split the program, and do not trust data that crossed a boundary.",
            "A module is a file that exports names. `export function grade(score) {}` "
            "in one file, `import { grade } from './grade.js'` in another. The rest of "
            "the file stays private. That is how a large program stays changeable.\n\n"
            "Anything that arrived from a form, a URL, or another service is untrusted. "
            "Check its type and its range before you use it. The check belongs next to "
            "the boundary, not scattered through the calculation.\n\n"
            "A professional JavaScript change has a small function, a check for the bad "
            "input, and a way to run that check again. The browser console is enough to "
            "start. A test runner is the same habit, kept.",
            "// grade.js\n"
            "export function grade(score) {\n"
            "  if (typeof score !== 'number') throw new TypeError('score must be a number');\n"
            "  if (score >= 90) return 'A';\n"
            "  if (score >= 50) return 'C';\n"
            "  return 'F';\n"
            "}\n\n"
            "// main.js\n"
            "import { grade } from './grade.js';\n"
            "console.log(grade(91));",
            "Move your grade function into its own file, import it, and run one check for a valid score and one for a value that must throw.",
        ),
    ],
    "cpp": [
        (
            "cpp-containers",
            "vector, string and map",
            "The containers you should reach for before a raw array.",
            "`std::vector` grows, knows its length, and frees its memory. A raw array "
            "does none of those. `std::string` is the same idea for text.\n\n"
            "`std::map` keeps keys in order and finds them in logarithmic time. "
            "`std::unordered_map` is usually faster for a pure lookup and does not "
            "keep order. Pick the one whose guarantee you need, and say why.\n\n"
            "Passing a large vector by value copies it. Pass `const std::vector<int>&` "
            "when the function only reads. Pass a non-const reference when it must change "
            "the caller's vector.",
            "#include <iostream>\n"
            "#include <map>\n"
            "#include <string>\n"
            "#include <vector>\n\n"
            "int main() {\n"
            "    std::vector<int> marks = {72, 85, 91, 68};\n"
            "    std::map<std::string, int> by_subject = {\n"
            "        {\"mechanics\", 72}, {\"circuits\", 85}, {\"dsa\", 91}\n"
            "    };\n"
            "    int total = 0;\n"
            "    for (int mark : marks) total += mark;\n"
            "    std::cout << \"average \" << static_cast<double>(total) / marks.size() << \"\\n\";\n"
            "    std::cout << \"dsa \" << by_subject[\"dsa\"] << \"\\n\";\n"
            "    return 0;\n"
            "}",
            "Read subject names and marks until a blank line, store them in a map, and print the subject with the highest mark.",
        ),
        (
            "cpp-professional",
            "Errors, sanitizers and the rule you keep",
            "The habits that stop a C++ program from failing in production.",
            "Prefer an exception or a returned status over a crash you did not intend. "
            "Catch only what you can handle. A catch-all that continues is how a "
            "corrupt state survives.\n\n"
            "Compile with warnings and a sanitizer while you learn: "
            "`g++ -Wall -Wextra -std=c++20 -fsanitize=address,undefined main.cpp`. "
            "AddressSanitizer catches the out-of-bounds access and the use-after-free "
            "that a green run would otherwise hide.\n\n"
            "The professional habit is not 'I know the syntax'. It is: the ownership "
            "is obvious, the bounds are checked, and the failing case has a test. "
            "RAII — acquire in a constructor, release in a destructor — is how the "
            "ownership stays obvious.",
            "#include <iostream>\n"
            "#include <stdexcept>\n"
            "#include <vector>\n\n"
            "int at(const std::vector<int>& items, int index) {\n"
            "    if (index < 0 || index >= static_cast<int>(items.size())) {\n"
            "        throw std::out_of_range(\"index\");\n"
            "    }\n"
            "    return items[index];\n"
            "}\n\n"
            "int main() {\n"
            "    std::vector<int> marks = {72, 85, 91};\n"
            "    try {\n"
            "        std::cout << at(marks, 1) << \"\\n\";\n"
            "        std::cout << at(marks, 9) << \"\\n\";\n"
            "    } catch (const std::out_of_range& error) {\n"
            "        std::cout << \"rejected: \" << error.what() << \"\\n\";\n"
            "    }\n"
            "    return 0;\n"
            "}",
            "Write a function that returns the last element of a vector and refuses an empty vector. Run it under AddressSanitizer if you have a compiler.",
        ),
    ],
    "c": [
        (
            "c-functions",
            "Functions, headers and the stack",
            "How a C program is split without losing track of who owns the memory.",
            "A function receives values or pointers. A large struct should be passed "
            "as a pointer. Mark it `const` if the function must not change it — the "
            "compiler then rejects an accidental write.\n\n"
            "A header (`.h`) declares the function. The `.c` file defines it. Other "
            "files include the header. Do not define the function in the header unless "
            "you know why a static inline is required.\n\n"
            "Local variables live on the stack and die when the function returns. "
            "Returning a pointer to a local variable is a bug: the caller receives an "
            "address that is no longer valid. Return the value, or write into memory "
            "the caller allocated.",
            "#include <stdio.h>\n\n"
            "int max_of(const int* values, int count) {\n"
            "    if (values == NULL || count <= 0) return 0;\n"
            "    int best = values[0];\n"
            "    for (int i = 1; i < count; i++) {\n"
            "        if (values[i] > best) best = values[i];\n"
            "    }\n"
            "    return best;\n"
            "}\n\n"
            "int main(void) {\n"
            "    int marks[] = {72, 85, 91, 68};\n"
            "    int n = (int)(sizeof marks / sizeof marks[0]);\n"
            "    printf(\"max %d\\n\", max_of(marks, n));\n"
            "    printf(\"empty %d\\n\", max_of(NULL, 0));\n"
            "    return 0;\n"
            "}",
            "Split max_of into a header and a source file, then call it from main. Refuse a null pointer and a zero count.",
        ),
        (
            "c-files",
            "Files and the checks a professional does not skip",
            "Persistence, and the return values C will not check for you.",
            "`fopen` returns NULL on failure. `fread` and `fgets` can stop early. "
            "Ignoring those returns is how a program prints garbage and looks like it "
            "worked.\n\n"
            "Always close a file you opened. Check `fclose` too if the write must have "
            "reached disk. A format-string mismatch in `printf` is undefined behaviour, "
            "not a warning you can ignore — compile with `-Wall -Wextra`.\n\n"
            "The professional C habit is: every allocation has one free, every open has "
            "one close, and every untrusted length is checked before you copy into a "
            "buffer. Run the program with `-fsanitize=address` or Valgrind before you "
            "trust it.",
            "#include <stdio.h>\n\n"
            "int main(void) {\n"
            "    FILE* handle = fopen(\"marks.txt\", \"w\");\n"
            "    if (handle == NULL) {\n"
            "        perror(\"marks.txt\");\n"
            "        return 1;\n"
            "    }\n"
            "    if (fprintf(handle, \"72 85 91\\n\") < 0) {\n"
            "        perror(\"write\");\n"
            "        fclose(handle);\n"
            "        return 1;\n"
            "    }\n"
            "    if (fclose(handle) == EOF) {\n"
            "        perror(\"close\");\n"
            "        return 1;\n"
            "    }\n"
            "    printf(\"wrote marks.txt\\n\");\n"
            "    return 0;\n"
            "}",
            "Read integers from a file until the end and print their average. Check fopen, check that you read at least one value, and close the file on every path.",
        ),
    ],
    "sql": [
        (
            "sql-select",
            "Reading rows",
            "SQL asks a question of a table. You describe the result, not the loop.",
            "A table is a named set of rows. A column has a type. `SELECT name, marks FROM students` "
            "returns those two columns for every row. `SELECT *` is fine while you explore and a "
            "poor habit in a program, because a new column then changes your result without warning.\n\n"
            "SQL is not run step by step in the order you picture. You say what you want. The "
            "engine decides how to get it. That is why an index can change the speed without "
            "changing the answer.\n\n"
            "End the statement with a semicolon in most clients. Keywords are not case-sensitive. "
            "Write them in capitals only so a reader can see them. The data is what is case-sensitive, "
            "depending on the database.",
            "SELECT name, marks\n"
            "FROM students;",
            "Write a query that returns only the name column from a table called subjects.",
        ),
        (
            "sql-filter",
            "WHERE, ORDER BY and LIMIT",
            "Most questions are 'which rows' and 'in what order'.",
            "`WHERE` keeps rows that match. `marks >= 75` is a condition. Text is compared "
            "in quotes: `branch = 'mechanical'`. Numbers are not quoted.\n\n"
            "`AND` and `OR` combine conditions. `AND` binds more tightly. Use parentheses "
            "when a reader could misread the mix.\n\n"
            "`ORDER BY marks DESC` sorts. `LIMIT 5` keeps the first five of that order. "
            "Without `ORDER BY`, `LIMIT` returns an arbitrary five. If you care which five, "
            "you must sort.",
            "SELECT name, marks\n"
            "FROM students\n"
            "WHERE branch = 'electrical' AND marks >= 75\n"
            "ORDER BY marks DESC\n"
            "LIMIT 5;",
            "Return the three lowest marks in a table, with the student name. Then add a condition that excludes marks below 40.",
        ),
        (
            "sql-joins",
            "Joining two tables",
            "Real data is split so a fact is stored once. JOIN puts it back together for a question.",
            "A student row should not repeat the full name of the branch in every record if the "
            "branch has its own facts. Store `branch_id`, and keep branches in another table.\n\n"
            "`INNER JOIN` keeps only rows that match in both tables. A student with no branch, "
            "or a branch with no students, disappears from an inner join. That is often what you "
            "want, and sometimes a bug. Know which one you asked for.\n\n"
            "`LEFT JOIN` keeps every row of the left table. Where the right table has no match, "
            "its columns are NULL. Forgetting that NULL and then filtering with `WHERE branch.name = ...` "
            "turns the left join back into an inner join.",
            "SELECT students.name, branches.name AS branch\n"
            "FROM students\n"
            "INNER JOIN branches ON branches.id = students.branch_id\n"
            "WHERE branches.name = 'mechanical'\n"
            "ORDER BY students.name;",
            "Write an inner join between a projects table and a students table so each project shows the student who built it. Then say which rows an inner join would drop.",
        ),
        (
            "sql-group",
            "Aggregates and GROUP BY",
            "Questions about a set: how many, how much, the average.",
            "`COUNT(*)` counts rows. `AVG(marks)`, `SUM(marks)`, `MIN` and `MAX` collapse "
            "many rows into one value. Without `GROUP BY`, the collapse is the whole table.\n\n"
            "`GROUP BY branch` makes one result row per branch. Every selected column must "
            "either be in the group or be inside an aggregate. Selecting `name` while grouping "
            "by branch is a mistake: there are many names in the group.\n\n"
            "`WHERE` filters rows before the group. `HAVING` filters groups after the aggregate. "
            "`WHERE marks >= 40` drops weak rows first. `HAVING AVG(marks) >= 70` drops weak groups after.",
            "SELECT branch, COUNT(*) AS students, AVG(marks) AS average_marks\n"
            "FROM students\n"
            "WHERE marks >= 40\n"
            "GROUP BY branch\n"
            "HAVING COUNT(*) >= 2\n"
            "ORDER BY average_marks DESC;",
            "For each subject, show how many students sat it and the highest mark. Hide subjects with fewer than three students.",
        ),
        (
            "sql-null",
            "NULL and mistakes that pass a casual test",
            "NULL means unknown, not zero and not an empty string.",
            "`NULL = NULL` is not true in SQL. It is unknown. Use `IS NULL` and `IS NOT NULL`. "
            "A condition that looks obvious, `WHERE phone = NULL`, matches nothing.\n\n"
            "`COUNT(phone)` skips NULL. `COUNT(*)` does not. They answer different questions. "
            "An average also skips NULL, so a missing mark is not a zero unless you decide it is "
            "and write that decision down.\n\n"
            "Comparing text with `=` is exact. `LIKE 'mech%'` is a pattern. A leading wildcard, "
            "`LIKE '%mech%'`, usually cannot use an ordinary index.",
            "SELECT name\n"
            "FROM students\n"
            "WHERE branch_id IS NULL;\n\n"
            "SELECT COUNT(*) AS rows, COUNT(phone) AS phones_known\n"
            "FROM students;",
            "Find every project whose repository link is missing. Explain why `link = ''` and `link IS NULL` are different questions.",
        ),
        (
            "sql-professional",
            "Indexes, transactions and what not to ship",
            "The habits that matter once the table is no longer a classroom example.",
            "An index speeds the lookup you designed it for and slows every insert and update, "
            "because the index must be maintained. Index the columns you filter and join on. "
            "Do not index every column 'to be safe'.\n\n"
            "A transaction is a group of statements that commit together or roll back together. "
            "Transferring a mark from one record to another without a transaction can leave the "
            "data half-updated if the second statement fails. `BEGIN`, the statements, then "
            "`COMMIT`. On failure, `ROLLBACK`.\n\n"
            "Never build a SQL statement by pasting user text into the string. That is SQL "
            "injection. Use a parameter: the value is data, not part of the query. A professional "
            "query is one whose answer you can explain, whose NULL cases you tested, and whose "
            "inputs cannot change the statement itself.",
            "-- The ? is a parameter. The database never treats it as SQL.\n"
            "SELECT name, marks\n"
            "FROM students\n"
            "WHERE branch = ?\n"
            "ORDER BY marks DESC;\n\n"
            "BEGIN;\n"
            "UPDATE accounts SET balance = balance - 10 WHERE id = 1;\n"
            "UPDATE accounts SET balance = balance + 10 WHERE id = 2;\n"
            "COMMIT;",
            "Name one column you would index on a students table and one you would not, and say why. Then write the parameterised query you would use for a branch chosen by the user.",
        ),
    ],
}

# Modules below deliberately bridge language syntax to tested, bounded apps and
# tool-using agents. These are learning paths and project blueprints, not claims
# that one short course makes a learner production-ready.
ADVANCED_MODULES = {
    "python": [
        (
            "python-fastapi-app",
            "Build a small validated API",
            "Turn functions into an HTTP application with explicit request and response models.",
            "An API route is a boundary: accept a known schema, validate lengths and ranges, call a small service function, and return a deliberate status. FastAPI uses type hints and Pydantic models to validate JSON before the handler runs. Authentication identifies a caller; authorization still checks whether that caller may access a record.\n\n"
            "Keep network calls and database work out of the schema model. Separate routes, domain logic, and persistence so each can be tested. Set timeouts for external calls, return generic errors, and never put API keys in source or responses.",
            'from fastapi import FastAPI, HTTPException\nfrom pydantic import BaseModel, Field\n\napp = FastAPI()\n\nclass StudyItem(BaseModel):\n    title: str = Field(min_length=1, max_length=120)\n\n@app.post("/items", status_code=201)\ndef create_item(item: StudyItem):\n    title = item.title.strip()\n    if not title:\n        raise HTTPException(status_code=422, detail="invalid title")\n    return {"title": title}\n',
            "Add an owner id and a list endpoint. Write down which check authenticates the caller and which query ensures they can see only their own items.",
        ),
        (
            "python-sqlite-persistence",
            "Persist data with SQLite safely",
            "Save application state with transactions and bound parameters, not string-built SQL.",
            "A database connection owns a transaction boundary. Group changes that must succeed together, commit once, and roll back on error. Always bind untrusted values through the driver placeholder API. A parameter is data; string formatting can turn it into SQL syntax.\n\n"
            "Use a unique constraint for identity, validate foreign references, and decide what deletion should cascade. Keep connection lifetime short and never expose raw database exceptions to a user.",
            "import sqlite3\n\nwith sqlite3.connect(\"study.db\") as con:\n    con.execute(\"CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY, title TEXT NOT NULL)\")\n    con.execute(\"INSERT INTO items(title) VALUES (?)\", (\"Review arrays\",))\n    rows = con.execute(\"SELECT id, title FROM items ORDER BY id\").fetchall()\nprint(rows)\n",
            "Add an owner column and a query that filters by the authenticated user's id. Try malformed and oversized titles before saving them.",
        ),
        (
            "python-agent-tools",
            "Build a bounded tool-using agent",
            "A useful agent is an ordinary program around a model: a small tool allowlist, validated arguments, and a strict loop budget.",
            "A model can suggest a tool call, but your application decides whether that tool exists, whether its JSON arguments match a schema, and whether the caller is authorized. Expose narrow functions such as search_notes or make_quiz; never expose eval, exec, arbitrary shell, unrestricted file access, or arbitrary URLs.\n\n"
            "Set a maximum number of steps, a wall-clock timeout, input/output size limits, and a budget. Treat retrieved documents as untrusted data, not instructions. Ask for human confirmation before sending messages, deleting records, or making purchases. Keep API keys outside prompts and logs. Test prompt injection, malformed arguments, tool errors, and unsupported requests.",
            "TOOLS = {\"search_notes\": search_notes, \"make_quiz\": make_quiz}\nMAX_STEPS = 4\n\ndef call_tool(name, arguments):\n    if name not in TOOLS:\n        raise ValueError(\"tool not allowed\")\n    if not isinstance(arguments, dict) or len(arguments) > 8:\n        raise ValueError(\"invalid arguments\")\n    return TOOLS[name](**arguments)\n\n# The orchestration loop must stop after MAX_STEPS and validate each call.\n",
            "Add a search_notes schema with a query string capped at 120 characters. Add a test that an unknown tool and an extra argument are rejected.",
        ),
        (
            "python-tested-app-capstone",
            "Capstone: a secure study planner and citation-first agent",
            "Combine a tested API, SQLite persistence, a modest user interface, and a tool-limited study assistant.",
            "Project brief: learners create a weekly study plan from published topics, mark tasks complete, and ask an assistant to find supporting notes. Start with a one-page UI and a FastAPI service; keep account ownership checks on the server. Store plans with parameterized SQLite statements and transactions.\n\n"
            "Milestones: write the data model and threat model; add validated CRUD routes; build a responsive client; add tests for permissions, empty/oversized input, and repeated requests; add an agent with only search_notes and draft_plan tools; evaluate citation accuracy and prompt-injection refusal; containerize and deploy behind HTTPS. Add health checks, structured logs without message bodies, secret configuration, dependency pinning, backups, and a short incident plan.\n\n"
            "Definition of done: a new developer can run tests from a clean checkout, a user cannot read another user's plan, the agent cites retrieved notes, and unsafe actions require confirmation.",
            "# Suggested app boundary\n# routes/       HTTP schema and authentication\n# services/     plan rules and tool allowlist\n# storage/      parameterized SQL and transactions\n# tests/        permissions, limits, retries, agent evaluations\n# web/          accessible client; no secret keys in browser code\n",
            "Deliver a README, architecture diagram, tests, a demo dataset, an accessibility pass, a security checklist, and three recorded agent-evaluation cases. Explain one design trade-off in a project review.",
        ),
    ],
    "java": [
        (
            "java-build-test",
            "Organize a buildable Java application",
            "Packages, a reproducible build, tests, and configuration turn a collection of classes into a maintainable application.",
            "Place production code and tests in separate source roots. A build tool such as Maven or Gradle resolves pinned dependencies and runs repeatable checks. Keep small domain classes independent of the HTTP framework; inject collaborators rather than hiding global mutable state.\n\n"
            "Treat configuration as input: parse it once, validate required values, and fail closed if a secret is absent. Never commit credentials. Use unit tests for domain rules and integration tests for database and HTTP boundaries.",
            "// A tiny domain function remains testable without a server.\npublic final class Planner {\n    private Planner() {}\n\n    public static int boundedMinutes(int requested) {\n        if (requested < 1 || requested > 240) {\n            throw new IllegalArgumentException(\"minutes must be 1-240\");\n        }\n        return requested;\n    }\n}\n",
            "Create a Maven or Gradle project, add tests for 1, 240, 0, and 241 minutes, and document the exact command that runs a clean build.",
        ),
        (
            "java-http-service",
            "Expose a small HTTP service",
            "Map routes to validated commands and return explicit status codes instead of mixing transport and business rules.",
            "An HTTP handler parses the request, checks size and media type, authenticates the principal, authorizes the object, calls a service, and maps the result to a response. Keep exception messages generic at the boundary; log a safe correlation id and exception type, not passwords or tokens.\n\n"
            "Use a maintained server framework in a real app. Set request and outbound-call timeouts, bound concurrent work, and never trust a client-supplied user id as proof of ownership.",
            "// Framework-neutral service boundary\nrecord CreateTask(String title, int minutes) {}\n\nfinal class TaskService {\n    Task create(CreateTask input, Principal actor) {\n        if (input.title() == null || input.title().isBlank() || input.title().length() > 120)\n            throw new IllegalArgumentException(\"invalid title\");\n        if (input.minutes() < 1 || input.minutes() > 240)\n            throw new IllegalArgumentException(\"invalid duration\");\n        return repository.insert(actor.id(), input.title().trim(), input.minutes());\n    }\n}\n",
            "Add a controller that returns 201 for a new task, 400 for invalid fields, and 404 rather than another user's task.",
        ),
        (
            "java-jdbc-data",
            "Use JDBC with prepared statements",
            "PreparedStatement binds values separately from SQL and transactions group related writes.",
            "Do not concatenate request strings into SQL. Use PreparedStatement placeholders, set typed values, and choose transaction boundaries deliberately. A database role should have only the permissions the service needs.\n\n"
            "Map database rows into domain objects; do not return a raw exception or stack trace. Test rollback, duplicate keys, missing records, and per-user filtering against a disposable test database.",
            "String sql = \"SELECT id, title FROM tasks WHERE owner_id = ? AND id = ?\";\ntry (PreparedStatement statement = connection.prepareStatement(sql)) {\n    statement.setString(1, actor.id());\n    statement.setLong(2, taskId);\n    try (ResultSet rows = statement.executeQuery()) {\n        if (!rows.next()) return Optional.empty();\n        return Optional.of(new Task(rows.getLong(\"id\"), rows.getString(\"title\")));\n    }\n}\n",
            "Write a transaction that inserts a plan and its tasks together, then force the second insert to fail and verify the first insert rolls back.",
        ),
        (
            "java-concurrency",
            "Bound concurrent work",
            "Use managed executors, cancellation, and timeouts instead of creating unlimited threads per request.",
            "One thread per request can exhaust memory under load. A managed executor caps workers and queue size. Propagate cancellation, set deadlines on outbound calls, and avoid holding locks while waiting for network I/O.\n\n"
            "Shared mutable state needs synchronization or, preferably, an immutable message passed between tasks. A timeout is not a proof that the remote operation stopped; design retries to be safe and idempotent.",
            "ExecutorService pool = Executors.newFixedThreadPool(8);\ntry {\n    Future<String> result = pool.submit(() -> fetchSummary(taskId));\n    System.out.println(result.get(2, TimeUnit.SECONDS));\n} finally {\n    pool.shutdownNow();\n}\n",
            "Add a maximum queue or semaphore, handle TimeoutException without returning partial sensitive data, and make one retry idempotent.",
        ),
        (
            "java-agent-tools",
            "Design an agent with explicit tool interfaces",
            "Keep model output as a proposal; the application validates and authorizes every tool call.",
            "Define an interface per capability, such as NoteSearch or QuizDraft. Parse arguments into typed records with length and range constraints; reject unknown tool names and unknown fields. Limit steps, time, tokens, and output size. Retrieved text is untrusted context, not policy.\n\n"
            "Do not expose Runtime.exec, reflection-based dispatch from arbitrary model text, or unrestricted network access. Require confirmation before a tool changes user data. Write deterministic tests around policy and separate evaluations for answer quality.",
            "sealed interface ToolResult permits SearchResult, QuizDraft {}\nrecord ToolCall(String name, Map<String, String> arguments) {}\n\nToolResult dispatch(ToolCall call, User actor) {\n    return switch (call.name()) {\n        case \"search_notes\" -> noteSearch.run(validateQuery(call.arguments()), actor);\n        case \"draft_quiz\" -> quizDraft.run(validateTopic(call.arguments()), actor);\n        default -> throw new SecurityException(\"tool not allowed\");\n    };\n}\n",
            "Add step-budget and timeout checks. Test a forged tool name, a cross-user record id, malformed arguments, and an action that must ask for approval.",
        ),
        (
            "java-application-capstone",
            "Capstone: an authenticated study planner API",
            "Build a Java service with clear layers, tests, database ownership checks, and an optional read-only study assistant.",
            "Create a REST API for study tasks using a maintained Java framework, JDBC or a repository layer, and a relational database. Separate controllers, domain services, and persistence. Add an authenticated owner scope to every query; do not accept an owner id from a request body.\n\n"
            "Ship migrations, validation, prepared statements, unit and integration tests, a small UI, and a deployment guide. For the assistant, expose only search and draft tools, validate each argument, cap its loop and response, and require the learner to approve writes. Keep credentials in deployment secrets and redact logs. Treat the capstone as a portfolio demonstration, not a claim of production certification.",
            "// Build order\n// 1. Task domain + boundary tests\n// 2. Authenticated API + owner-scoped queries\n// 3. Database migration + rollback test\n// 4. UI + accessibility + error states\n// 5. Read-only agent tools + evaluation set\n// 6. CI, pinned dependencies, deployment, backups\n",
            "Publish an architecture diagram, test evidence, API contract, threat model, deployment steps, and a demo with two users proving records stay private.",
        ),
    ],
    "javascript": [
        (
            "js-node-service",
            "Build a Node.js HTTP service",
            "Use Node's server APIs or a maintained framework to make a small route with bounded parsing and clear responses.",
            "A backend service parses bytes, validates JSON shape, checks authentication and object permissions, calls application logic, and returns a status. Set a body limit before JSON parsing; cap concurrent work and external request timeouts.\n\n"
            "Never construct HTML with untrusted strings. In a browser UI prefer textContent and DOM APIs; in a server template use an autoescaping template engine. Keep secrets on the server, and use environment configuration rather than bundling them into frontend code.",
            "import { createServer } from 'node:http';\n\nconst server = createServer((request, response) => {\n  if (request.method === 'GET' && request.url === '/health') {\n    response.writeHead(200, { 'content-type': 'application/json' });\n    response.end(JSON.stringify({ ok: true }));\n    return;\n  }\n  response.writeHead(404, { 'content-type': 'application/json' });\n  response.end(JSON.stringify({ error: 'not found' }));\n});\nserver.listen(3000);\n",
            "Add a POST route with a 16 KB body limit, a bounded title, and a test for missing, invalid, and oversized JSON.",
        ),
        (
            "js-testable-app",
            "Test behavior with Node's test runner",
            "Small repeatable tests let you change a UI or service without guessing what broke.",
            "Keep pure functions independent of DOM and network objects; inject those dependencies at the edge. Node's built-in test runner can check values, thrown errors, and async behavior. Test boundaries and failure paths, not only a happy example.\n\n"
            "For browser code, use DOM fixtures and ensure user-controlled text is inserted as text, not interpreted as markup. Tests complement review; they do not prove an application has no vulnerabilities.",
            "import test from 'node:test';\nimport assert from 'node:assert/strict';\n\nfunction boundedTitle(value) {\n  if (typeof value !== 'string' || value.trim().length < 1 || value.length > 120) {\n    throw new TypeError('invalid title');\n  }\n  return value.trim();\n}\n\ntest('accepts a normal title', () => {\n  assert.equal(boundedTitle(' Arrays '), 'Arrays');\n});\n\ntest('rejects an oversized title', () => {\n  assert.throws(() => boundedTitle('x'.repeat(121)), TypeError);\n});\n",
            "Add tests for null, an object instead of text, exactly 120 characters, and 121 characters. Run them with node --test.",
        ),
        (
            "js-browser-security",
            "Browser boundaries: identity, output, and clipboard",
            "A browser form is not an authorization boundary, and pasted or fetched strings are not trusted markup.",
            "Use textContent for user-controlled text; avoid innerHTML unless a reviewed sanitizer is required. A server must validate and authorize every action even if the button is hidden. Use same-origin protections and CSRF tokens for cookie-authenticated mutations.\n\n"
            "Clipboard access should happen only after an explicit user gesture. Show the destination, avoid background overwrites, and never execute pasted source automatically. Keep tokens in protected server-side sessions where possible; never place a long-lived API key in a bundle or localStorage.",
            "const output = document.querySelector('#result');\nconst userText = new URLSearchParams(location.search).get('q') ?? '';\noutput.textContent = userText; // display as text, not executable HTML\n\n// A privileged action still calls the server, which checks the session\n// and capability; hiding its button is only presentation.",
            "Build an explicit Copy button that works after a click, announces success accessibly, and never reads or changes the clipboard in the background.",
        ),
        (
            "js-agent-tools",
            "Compose a tool-using study agent",
            "Use typed tools and a fixed decision loop; model output never gains JavaScript execution privileges.",
            "Define a fixed map of supported functions. Validate each argument with a runtime schema, check the current user's permissions, and cap the loop and output. Never eval a generated string or pass it to a shell. Retrieved pages are data, not instructions.\n\n"
            "A useful first agent can search published notes and draft a quiz. Add citations, timeouts, retries with limits, a human approval step for writes, and test cases for injected instructions and unknown tools.",
            "const tools = {\n  searchNotes: async ({ query }) => searchPublishedNotes(query),\n  draftQuiz: async ({ topicId }) => draftQuizForAuthorizedTopic(topicId),\n};\n\nasync function dispatch(name, input) {\n  if (!Object.hasOwn(tools, name)) throw new Error('tool not allowed');\n  if (!input || typeof input !== 'object' || Array.isArray(input)) {\n    throw new TypeError('arguments must be an object');\n  }\n  return tools[name](input);\n}\n",
            "Add a maximum of four model/tool turns, validate query length and topic ownership, and require confirmation before saving the quiz.",
        ),
        (
            "js-fullstack-capstone",
            "Capstone: a study dashboard and guarded agent",
            "Connect accessible browser UI, a Node API, tests, persistence, and narrow assistant tools.",
            "Build a small dashboard that lists a learner's study tasks and practice history. Add a Node service, persistent storage through a parameterized data layer, and a browser interface that handles loading, empty, and error states. Authenticate at the server and scope every query to the session user.\n\n"
            "Tests cover route permissions, input limits, XSS-safe rendering, retries, and unknown resources. An assistant may search public notes and draft a plan; writes require a user confirmation. Add a threat model, pinned dependencies, secret configuration, rate limits, monitoring without raw message logging, a backup/restore test, and clear setup documentation.",
            "// Suggested components\n// web/       accessible UI, textContent for untrusted strings\n// api/       schema validation, authn + authz per route\n// data/      parameterized queries and transaction tests\n// agent/     allowlisted tools, bounded loop, approval gate\n// tests/     permissions, payload limits, evaluations, restore drill\n",
            "Demo two user accounts and prove they cannot cross-read tasks. Publish a short threat model and show evaluation results for unsupported and prompt-injected requests.",
        ),
    ],
    "cpp": [
        (
            "cpp-raii-memory-safety",
            "Ownership, RAII, and safe resource handling",
            "Make ownership visible so files, locks, and memory are released on every exit path.",
            "RAII ties a resource lifetime to an object's lifetime. Prefer values and standard containers; use unique_ptr for exclusive dynamic ownership and shared_ptr only for genuine shared ownership. A reference is non-owning and must not outlive its object.\n\n"
            "Validate lengths before indexing, avoid raw new/delete in application code, and compile with warnings and address/undefined-behavior sanitizers during development. A crash-free sample run is not a bounds proof.",
            "#include <memory>\n#include <string>\n#include <vector>\n\nstruct Task { std::string title; };\n\nint main() {\n    std::vector<Task> tasks; // owns its storage\n    tasks.push_back(Task{\"Review arrays\"});\n    auto selected = std::make_unique<Task>(Task{\"Practice graphs\"});\n    return tasks.empty() || selected->title.empty();\n}\n",
            "Refactor a raw owning pointer to unique_ptr, validate an index before access, and run AddressSanitizer on a failing boundary test.",
        ),
        (
            "cpp-build-test",
            "Build and test a multi-file project",
            "CMake, warnings, and a repeatable test target make a C++ application easier to review and ship.",
            "Separate public headers from implementation files, keep the executable entry point small, and let CMake describe targets. Turn on warnings. A test should exercise a function through its public interface and include boundaries.\n\n"
            "Treat compiler diagnostics as evidence. Sanitizers catch classes of memory defects at runtime; they do not replace correct ownership, input validation, or code review.",
            "// CMakeLists.txt\ncmake_minimum_required(VERSION 3.20)\nproject(study_planner LANGUAGES CXX)\nset(CMAKE_CXX_STANDARD 20)\nset(CMAKE_CXX_STANDARD_REQUIRED ON)\nadd_executable(planner src/main.cpp src/planner.cpp)\ntarget_compile_options(planner PRIVATE -Wall -Wextra -Wpedantic)\n",
            "Add a CTest target for a duration-validation function. Test the minimum, maximum, and both invalid sides.",
        ),
        (
            "cpp-parse-safe-input",
            "Parse input without undefined behavior",
            "Check the result of every parse and range operation before using a value.",
            "Input can be missing, malformed, or outside the representable range. Prefer std::from_chars for locale-independent integer parsing; check its error code and that the entire input was consumed. Avoid unchecked casts and indexes.\n\n"
            "Keep bounds and units explicit. Reject invalid values rather than silently wrapping, truncating, or substituting a privileged default.",
            "#include <charconv>\n#include <string_view>\n#include <system_error>\n\nbool parse_minutes(std::string_view text, int& minutes) {\n    int value = 0;\n    const auto result = std::from_chars(text.data(), text.data() + text.size(), value);\n    if (result.ec != std::errc{} || result.ptr != text.data() + text.size()) return false;\n    if (value < 1 || value > 240) return false;\n    minutes = value;\n    return true;\n}\n",
            "Test empty text, trailing characters, a large integer, 1, 240, 0, and 241 without reading past the buffer.",
        ),
        (
            "cpp-safe-app-project",
            "Capstone: an engineering CLI with a safe service boundary",
            "Build a useful native tool with tested parsing, persistence abstraction, and explicit capability boundaries.",
            "Build a CLI that imports engineering measurements, validates units and ranges, summarizes them, and exports a report. Keep parsing, calculations, storage, and output in separate functions. Use standard containers and RAII.\n\n"
            "Tests include malformed files, large inputs, boundary values, and output permissions. If adding a network or database layer, use a maintained library, parameterized queries, timeouts, and a least-privilege service account. Do not embed credentials. Add a threat model, dependency inventory, reproducible CMake build, CI sanitizer job, and recovery notes.",
            "// parse -> validate -> calculate -> report\n// Each stage has a narrow input/output contract.\n// No raw user string becomes a path, SQL fragment, or shell command.\n",
            "Ship source, CMake configuration, tests, sample input, a profiling note, a threat model, and a README with exact build and run commands.",
        ),
    ],
    "typescript": [
        (
            "ts-types-functions",
            "Model data with TypeScript types",
            "Types make contracts visible at compile time, while runtime input still needs validation.",
            "Use interfaces, unions, and generics to express program state. A type assertion does not validate JSON from a URL or server. Treat external values as unknown, check their shape, then narrow the type.\n\n"
            "Prefer discriminated unions for state such as loading/success/error. Keep strict mode enabled, avoid any, and validate authorization on the server rather than assuming a typed client is trustworthy.",
            "type Result<T> =\n  | { kind: 'ok'; value: T }\n  | { kind: 'error'; message: string };\n\nfunction titleFrom(value: unknown): string | null {\n  if (typeof value !== 'string') return null;\n  const title = value.trim();\n  return title.length > 0 && title.length <= 120 ? title : null;\n}\n",
            "Write a type guard for an API response with id and title, then test null, an array, and an object with missing fields.",
        ),
        (
            "ts-web-app",
            "Build an accessible browser interface",
            "Compose typed components around semantic HTML, explicit state, and safe text rendering.",
            "A browser application has loading, empty, success, and error states. Use semantic buttons and forms, label controls, preserve keyboard navigation, and announce asynchronous status. Treat strings returned by the API as text.\n\n"
            "TypeScript types help refactoring but disappear at runtime. Validate network payloads, handle non-2xx status, and never bundle a server secret. Cookie-authenticated mutations need server-side CSRF protection.",
            "type StudyTask = { id: string; title: string };\n\nfunction renderTask(list: HTMLElement, task: StudyTask) {\n  const item = document.createElement('li');\n  item.textContent = task.title; // not innerHTML\n  list.append(item);\n}\n",
            "Add keyboard-operable completion controls, a live loading message, and an empty state. Confirm an untrusted title is rendered as text.",
        ),
        (
            "ts-http-validation",
            "Call APIs with timeouts and runtime schemas",
            "A typed fetch wrapper still needs a timeout, status check, and runtime validation of the response.",
            "Network requests can fail, stall, return malformed JSON, or return an error status. Use AbortSignal.timeout where supported or an AbortController. Validate the parsed result before treating it as a domain object.\n\n"
            "Use a relative API URL in a browser app so the same-origin server or proxy can route it. Avoid hardcoded localhost URLs in browser-facing code and never leak service credentials into client bundles.",
            "async function fetchTask(id: string): Promise<unknown> {\n  const response = await fetch(`/api/tasks/${encodeURIComponent(id)}`, {\n    signal: AbortSignal.timeout(5000),\n    headers: { accept: 'application/json' },\n  });\n  if (!response.ok) throw new Error('Task request failed');\n  return response.json();\n}\n",
            "Add a validator for the returned object, handle timeout and 404 states, and use relative URLs for every browser request.",
        ),
        (
            "ts-node-service",
            "Build a Node API with explicit authorization",
            "Use typed route schemas for developer clarity and repeat the real checks on the server at runtime.",
            "A request body can be forged regardless of the client types. Validate JSON at the server boundary, authenticate the session, authorize the operation, and scope database queries to the principal. Keep route handlers small and return generic safe errors.\n\n"
            "Set body limits, timeouts, rate limits, and bounded response sizes. Use prepared database queries. Never dispatch a model-generated function name directly or expose arbitrary file, shell, or network access.",
            "type Principal = { userId: string; capabilities: ReadonlySet<string> };\n\nfunction requireCapability(actor: Principal, capability: string): void {\n  if (!actor.capabilities.has(capability)) {\n    throw new Error('forbidden');\n  }\n}\n\n// Validate unknown JSON before this function; types do not replace validation.\n",
            "Add an owner-scoped task route and test that a signed-in user cannot read another user's identifier.",
        ),
        (
            "ts-agent-tools",
            "Implement typed, allowlisted agent tools",
            "Types clarify tool contracts; runtime schemas, authorization, and budgets enforce them.",
            "Model output is untrusted. Map a small set of names to narrow functions, validate arguments at runtime, verify the current principal's permission, and stop at a fixed step budget. Never use eval or invoke arbitrary package methods from generated text.\n\n"
            "Retrieved documents can contain prompt injection; they are evidence, not higher-priority instructions. Require human confirmation before writes and evaluate citations, refusal behavior, and malformed tool calls.",
            "type ToolName = 'searchNotes' | 'draftPlan';\ntype ToolCall = { name: string; arguments: unknown };\n\nfunction allowedTool(name: string): name is ToolName {\n  return name === 'searchNotes' || name === 'draftPlan';\n}\n\nfunction dispatch(call: ToolCall) {\n  if (!allowedTool(call.name)) throw new Error('tool not allowed');\n  // Parse call.arguments with a runtime schema before dispatch.\n}\n",
            "Reject unknown tool names, unexpected keys, overlong search strings, and a write action without an explicit approval signal.",
        ),
        (
            "ts-test-release-capstone",
            "Capstone: a TypeScript study app and evaluation harness",
            "Build a browser client, Node API, persistent service, tests, and a restrained assistant as one reviewed project.",
            "Build a study dashboard with typed UI state, runtime validation for every network boundary, a same-origin Node API, and owner-scoped data access. Use a relational store with parameters and transactions.\n\n"
            "Tests cover malformed payloads, authorization, rendering, keyboard access, retries, and API errors. The agent can search public course notes and draft a plan, but cannot execute code or write without approval. Add prompt-injection and citation evaluation cases, dependency checks, secret management, body/rate limits, health checks, and deployment documentation.",
            "// project slices\n// client: semantic UI + validated fetch responses\n// server: session, capability checks, request limits\n// tools: allowlisted calls + bounded agent loop\n// tests: unit, API, browser accessibility, agent evals\n",
            "Deliver a demo, architecture diagram, threat model, test/evaluation report, and deployment/rollback checklist.",
        ),
    ],
    "go": [
        (
            "go-types-errors",
            "Types, functions, and explicit errors",
            "Go makes data shapes and error paths visible with small structs and multiple return values.",
            "Define structs around domain data and return errors instead of hiding failures. Check every returned error. Wrap errors with context internally but do not expose driver details to API clients.\n\n"
            "Validate ranges at the boundary; a zero value may be meaningful. Use context.Context for cancellation and deadlines. Keep package APIs small and avoid global mutable state.",
            'package main\n\nimport (\n    "errors"\n    "strings"\n    "unicode/utf8"\n)\n\ntype StudyTask struct {\n    ID string\n    Title string\n    Minutes int\n}\n\nfunc validate(task StudyTask) error {\n    title := strings.TrimSpace(task.Title)\n    if title == "" || utf8.RuneCountInString(title) > 120 {\n        return errors.New("invalid title")\n    }\n    if task.Minutes < 1 || task.Minutes > 240 {\n        return errors.New("invalid duration")\n    }\n    return nil\n}\n',
            "Add table-driven cases for empty, maximum-length, and too-long titles, plus durations at 0, 1, 240, and 241.",
        ),
        (
            "go-packages-tests",
            "Packages and repeatable tests",
            "Small packages and table-driven tests make changes understandable and easy to check in CI.",
            "Keep package responsibilities narrow. Export only names another package needs. Table-driven tests make boundary cases visible; the race detector can help identify data races.\n\n"
            "A green unit suite is evidence for tested behavior, not proof of security. Add integration tests for persistence, authorization, timeouts, and request-size limits.",
            'package main\n\nimport "testing"\n\nfunc TestValidateMinutes(t *testing.T) {\n    cases := []struct { name string; minutes int; wantErr bool }{\n        {"minimum", 1, false}, {"maximum", 240, false},\n        {"zero", 0, true}, {"too large", 241, true},\n    }\n    for _, tc := range cases {\n        t.Run(tc.name, func(t *testing.T) {\n            err := validate(StudyTask{Title: "Review", Minutes: tc.minutes})\n            if (err != nil) != tc.wantErr { t.Fatalf("error = %v", err) }\n        })\n    }\n}\n',
            "Run go test ./... and go test -race ./...; add a test for the ownership check on a task route.",
        ),
        (
            "go-http-api",
            "Serve a bounded HTTP API",
            "Use request contexts, explicit JSON schemas, and deadlines around work at the network boundary.",
            "The standard net/http server supports handlers and request contexts. Limit body reads before decoding, reject unknown or malformed fields where appropriate, and return safe status codes. Authenticate and authorize per route; validate the target object belongs to the principal.\n\n"
            "Configure server read/write/idle timeouts and outbound client timeouts. Use a reverse proxy for TLS and deployment policy, but do not trust forwarded headers unless the proxy chain is configured.",
            'package main\n\nimport (\n    "io"\n    "log"\n    "net/http"\n    "time"\n)\n\nfunc main() {\n    mux := http.NewServeMux()\n    mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {\n        w.Header().Set("Content-Type", "application/json")\n        w.WriteHeader(http.StatusOK)\n        _, _ = io.WriteString(w, `{"ok":true}`)\n    })\n\n    server := &http.Server{\n        Addr: ":8080", Handler: mux,\n        ReadHeaderTimeout: 5 * time.Second,\n        ReadTimeout: 10 * time.Second,\n        WriteTimeout: 10 * time.Second,\n        IdleTimeout: 60 * time.Second,\n    }\n    if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {\n        log.Fatal(err)\n    }\n}\n',
            "Add a body-size cap to a POST route, set a timeout on outbound requests, and test a slow client and invalid JSON.",
        ),
        (
            "go-sql-data",
            "Use database/sql with parameterized queries",
            "Pass values as arguments and use transactions for changes that must succeed together.",
            "The database driver binds query parameters (placeholder syntax varies by driver); it must not receive SQL built by concatenating request text. Use context-aware calls, close rows, check errors, and use a transaction for related writes. Scope every read/update to the authenticated user.\n\n"
            "A timeout should cancel the query when supported. Select columns explicitly, enforce uniqueness in the schema, and return a safe domain error instead of SQL details.",
            "row := db.QueryRowContext(ctx,\n    `SELECT id, title FROM tasks WHERE owner_id = ? AND id = ?`,\n    actorID, taskID)\nvar task Task\nif err := row.Scan(&task.ID, &task.Title); err != nil {\n    return Task{}, err\n}\n",
            "Write a transaction that creates a plan and task. Force the second write to fail and verify that neither row commits.",
        ),
        (
            "go-concurrency-context",
            "Use contexts and bounded concurrency",
            "Goroutines are cheap, not free; cancellation, semaphores, and deadlines keep work bounded.",
            "Every goroutine needs a clear owner and a way to stop. Pass context.Context through request-scoped work, set deadlines for outbound calls, and bound fan-out with a semaphore or worker pool.\n\n"
            "Avoid leaking goroutines waiting on channels after a client disconnects. Retries can duplicate writes; use idempotency keys or safe operations.",
            "ctx, cancel := context.WithTimeout(parent, 2*time.Second)\ndefer cancel()\nreq, err := http.NewRequestWithContext(ctx, http.MethodGet, endpoint, nil)\nif err != nil { return err }\nresp, err := client.Do(req)\nif err != nil { return err }\ndefer resp.Body.Close()\n",
            "Fan out to a maximum of four read-only sources. Cancel them when the request is abandoned and cap each response body.",
        ),
        (
            "go-agent-capstone",
            "Capstone: a Go study API with guarded tools",
            "Combine net/http, validated data, SQL, tests, and a narrow tool interface into a deployable learning service.",
            "Build a task API for study plans with authenticated owner-scoped access, database migrations, request limits, and clear error handling. Use interfaces to test storage and external clients.\n\n"
            "An optional agent may call SearchNotes or DraftPlan through typed interfaces. Enforce an allowlist, argument schemas, a step/time budget, citations, and approval for writes. Add race tests, dependency checks, secret configuration, safe logs, backup/restore, and a deployment runbook.",
            "// Agent boundary\ntype Tool interface {\n    Name() string\n    Validate(json.RawMessage) error\n    Run(context.Context, Principal, json.RawMessage) (json.RawMessage, error)\n}\n// Registry is a fixed map; model output cannot create new tools.\n",
            "Demonstrate owner isolation, cancellation, malformed-tool rejection, and an evaluation case with hostile retrieved text.",
        ),
    ],
    "rust": [
        (
            "rust-ownership-errors",
            "Ownership, borrowing, and Result",
            "Rust's type system makes ownership and many error paths explicit before the program runs.",
            "An owned value has one owner; borrowing gives temporary access without transferring ownership. Use references for read-only access and Result for expected failures. Avoid cloning large values merely to silence the borrow checker; first decide which layer should own the data.\n\n"
            "Types and borrow checking prevent many memory-safety errors, but business authorization, input validation, cryptographic correctness, and dependency safety still need explicit work.",
            "fn bounded_title(raw: &str) -> Result<String, &'static str> {\n    let title = raw.trim();\n    if title.is_empty() || title.len() > 120 {\n        return Err(\"invalid title\");\n    }\n    Ok(title.to_owned())\n}\n\nfn main() {\n    match bounded_title(\" Review arrays \") {\n        Ok(title) => println!(\"{title}\"),\n        Err(error) => eprintln!(\"{error}\"),\n    }\n}\n",
            "Add tests for empty, valid, and overlong input. Return an error instead of panicking on user-controlled data.",
        ),
        (
            "rust-collections-iterators",
            "Collections and iterators",
            "Use Vec, HashMap, and iterator adapters while keeping ownership and complexity visible.",
            "Vec is a growable sequence, HashMap maps keys to values, and iterators compose transformations without requiring manual index arithmetic. Know when a collection clones values and when it borrows.\n\n"
            "Avoid unwrap on untrusted data. Use checked indexing or get, and propagate errors with Result. Choose ordering or hashing based on the behavior the application needs.",
            "use std::collections::HashMap;\n\nfn counts(words: &[&str]) -> HashMap<String, usize> {\n    let mut result = HashMap::new();\n    for word in words {\n        *result.entry((*word).to_owned()).or_insert(0) += 1;\n    }\n    result\n}\n\nfn main() {\n    let words = [\"build\", \"test\", \"build\"];\n    println!(\"{:?}\", counts(&words));\n}\n",
            "Return the three most common words with deterministic tie-breaking and test repeated, empty, and Unicode input.",
        ),
        (
            "rust-tests-modules",
            "Modules, tests, and Cargo",
            "Cargo gives a repeatable build and test workflow for a multi-module Rust application.",
            "Use modules to express ownership of responsibilities, not simply to split long files. Cargo.toml records dependencies and metadata; commit Cargo.lock for an application. Run formatting, tests, and clippy in CI.\n\n"
            "Do not claim that a dependency audit proves safety. Review updates, pin compatible versions, and use minimal permissions and features.",
            'fn bounded_title(raw: &str) -> Result<String, &\'static str> {\n    let title = raw.trim();\n    if title.is_empty() || title.len() > 120 {\n        return Err("invalid title");\n    }\n    Ok(title.to_owned())\n}\n\n#[cfg(test)]\nmod tests {\n    use super::*;\n\n    #[test]\n    fn rejects_blank_title() {\n        assert!(bounded_title("  ").is_err());\n    }\n\n    #[test]\n    fn trims_a_valid_title() {\n        assert_eq!(bounded_title(" Rust ").unwrap(), "Rust");\n    }\n}\n',
            "Add tests for the maximum title size and inspect cargo clippy output.",
        ),
        (
            "rust-http-service",
            "Build a service with explicit boundaries",
            "A safe Rust HTTP service still needs request limits, authorization, timeouts, and reviewed dependencies.",
            "Choose a maintained framework, deserialize into a narrow request struct, validate it, authenticate the caller, and authorize the requested resource. Keep SQL parameterized. Set body and response limits and timeouts.\n\n"
            "Use Result at the boundary and map internal errors to a generic response. Do not return file paths or database diagnostics. Rust prevents classes of memory errors; it does not make every application decision secure by default.",
            "#[derive(serde::Deserialize)]\nstruct CreateTask {\n    title: String,\n    minutes: u16,\n}\n\nfn validate(input: CreateTask) -> Result<CreateTask, &'static str> {\n    if input.title.trim().is_empty() || input.title.len() > 120 {\n        return Err(\"invalid title\");\n    }\n    if !(1..=240).contains(&input.minutes) {\n        return Err(\"invalid duration\");\n    }\n    Ok(input)\n}\n",
            "Add an authenticated owner id that is derived from the session, never from the JSON body. Test invalid JSON and a cross-user read.",
        ),
        (
            "rust-agent-tools",
            "Build a constrained agent tool registry",
            "Use enums and typed arguments to restrict what a model-driven workflow can request.",
            "Represent supported actions as an enum and parse external tool names into that enum. Validate arguments, principal permissions, and budgets before running a function. Do not pass generated text to a shell or dynamic evaluator.\n\n"
            "Limit tool steps, elapsed time, response bytes, and model spend. Retrieved content is untrusted input. Require a user confirmation for writes and evaluate citation quality separately from policy enforcement.",
            "enum ToolName { SearchNotes, DraftPlan }\n\nfn parse_tool(name: &str) -> Result<ToolName, &'static str> {\n    match name {\n        \"search_notes\" => Ok(ToolName::SearchNotes),\n        \"draft_plan\" => Ok(ToolName::DraftPlan),\n        _ => Err(\"tool not allowed\"),\n    }\n}\n",
            "Add typed argument structs, a four-step cap, and tests for an unknown name, oversized search, unauthorized plan, and unapproved write.",
        ),
        (
            "rust-application-capstone",
            "Capstone: a study-planner service with a safe assistant",
            "Build a tested Rust application that demonstrates ownership, API design, persistence, and careful tool orchestration.",
            "Build a small authenticated planner API with a browser or mobile client, relational storage, typed validation, and owner-scoped access. Separate domain types, API adapters, and persistence. Use a maintained framework and reviewed dependencies.\n\n"
            "Add unit and integration tests, request limits, deadlines, secure configuration, dependency checks, backup and restore, and safe operational logs. Optional agent tools are limited to public note search and plan drafting; require approval before writes and cite source lessons.",
            "// project checklist\n// domain types + Result-based errors\n// API schemas + owner authorization\n// parameterized storage + migrations\n// bounded tool registry + citation tests\n// Cargo lockfile + CI + backup/restore runbook\n",
            "Publish a threat model, ownership explanation, test report, dependency review, and a two-user isolation demo.",
        ),
    ],
}

for _language, _rows in ADVANCED_MODULES.items():
    EXTRA_MODULES.setdefault(_language, []).extend(_rows)

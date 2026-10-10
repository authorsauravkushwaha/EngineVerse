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

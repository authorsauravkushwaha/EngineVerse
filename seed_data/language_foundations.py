"""Scratch-first modules: why the language, then variables, decisions, loops, practice.

These prepend the existing catalogue so a learner who picks Python (or Java, C,
JavaScript, …) starts at zero: importance, Hello World, types, operators,
if/else, loops, input, then real-world drills — before the later modules on
functions, modules, testing and services. Standard language facts, not a
complete reference and not a job-readiness claim.
"""

from __future__ import annotations

FOUNDATION_MODULES: dict[str, list[tuple]] = {
    "python": [
        (
            "python-why",
            "Why Python exists",
            "What this language is for, and why engineers still pick it first.",
            "Python is a high-level, dynamically typed language whose syntax is close to "
            "how people write steps in English. That is why it is the usual first language "
            "in universities, data work, automation and machine learning.\n\n"
            "EngineVerse itself is written in Python. The same language that runs this site "
            "is the one you will type in the first modules.\n\n"
            "**Where it is used.** Scripts that rename a folder of files. APIs. Data analysis. "
            "Teaching. Glue between other systems.\n\n"
            "**What it is not.** It is not the fastest language at the metal. Games, kernels "
            "and tight embedded loops usually use C, C++ or Rust. Python's job is to let you "
            "express the idea clearly and ship it.\n\n"
            "A professional Python programmer can read a traceback, write a test, and refuse "
            "to paste untrusted input into SQL or a shell.",
            "print('Python is used to think clearly and ship tools.')\n"
            "print('This site is one of those tools.')",
            "Write three sentences: one use of Python you care about, one thing it is bad at, "
            "and one habit a professional keeps (tests, types, or input checks).",
        ),
        (
            "python-hello-setup",
            "Hello World and how a program runs",
            "Install nothing extra yet: a `.py` file is a list of statements the interpreter runs top to bottom.",
            "A Python program is a text file. The interpreter reads it from the first line to "
            "the last. `print(...)` writes to standard output — the same stream a terminal shows.\n\n"
            "`#` starts a comment. Comments are for the next reader, including you in six months.\n\n"
            "Indentation is syntax, not decoration. Four spaces is the convention. Mixing tabs "
            "and spaces is an error.\n\n"
            "Run with `python hello.py` (or `python3` on some systems). The file name is not "
            "magic; the contents are.",
            "print('Hello, EngineVerse')  # first program\n"
            "print(2 + 2)\n"
            "print('year', 2026)",
            "Create hello.py, print your name and today's date, and run it until the output is exactly what you intended.",
        ),
        (
            "python-operators",
            "Operators and expressions",
            "Arithmetic, comparison and boolean operators — the atoms of every later program.",
            "`+ - * / // % **` are arithmetic. `/` always returns a float. `//` is floor "
            "division. `%` is remainder. `**` is power.\n\n"
            "`== != < > <= >=` compare and return `True` or `False`. `=` is assignment, "
            "`==` is equality. Mixing them up is the first real bug most people hit.\n\n"
            "`and`, `or`, `not` combine booleans. Python stops early: `False and expensive()` "
            "never calls `expensive()`.\n\n"
            "Parentheses make order obvious. Do not make the next reader memorise precedence.",
            "a, b = 17, 5\n"
            "print(a + b, a - b, a * b, a / b, a // b, a % b, a ** 2)\n"
            "print(a > b, a == 17, a != b)\n"
            "print(a > 10 and b < 10)\n"
            "print(not (a < 0))",
            "Compute the remaining minutes in a 90-minute exam after 37 minutes have passed, using // and %.",
        ),
        (
            "python-decisions",
            "Decisions: if, elif, else",
            "A program that always does the same thing is a calculator. Real programs branch.",
            "`if condition:` runs a block when the condition is true. `elif` is another "
            "check. `else` is the leftover case.\n\n"
            "Empty strings, `0`, `[]` and `None` are falsy. That is convenient and also a "
            "trap: a mark of `0` is a real value, not 'missing'.\n\n"
            "Keep conditions small. If you need five `and`s, name the parts.\n\n"
            "After this module you should be able to grade a mark, reject a bad input, and "
            "explain which branch ran.",
            "score = 73\n"
            "if score >= 90:\n"
            "    grade = 'A'\n"
            "elif score >= 75:\n"
            "    grade = 'B'\n"
            "elif score >= 50:\n"
            "    grade = 'C'\n"
            "else:\n"
            "    grade = 'F'\n"
            "print(score, '→', grade)\n"
            "if score < 0 or score > 100:\n"
            "    print('that score cannot be right')",
            "Write a fare function: under 5 years free, 5–18 half, 18–60 full, over 60 half. Print all four cases.",
        ),
        (
            "python-loops-from-scratch",
            "Loops: for and while",
            "Repeat work without copying the same line ten times.",
            "`for item in sequence:` walks each element. `range(n)` is 0 .. n-1. "
            "`range(1, 11)` is 1 .. 10.\n\n"
            "`while condition:` repeats until the condition is false. A while loop that "
            "never updates the condition is an infinite loop — stop it with Ctrl-C.\n\n"
            "`break` leaves the loop. `continue` skips to the next item.\n\n"
            "Prefer `for` when you know the collection. Prefer `while` when you are waiting "
            "for a condition (user input, a remainder becoming zero).",
            "print('table of 7')\n"
            "for n in range(1, 11):\n"
            "    print(f'7 × {n} = {7 * n}')\n"
            "\n"
            "n = 17\n"
            "steps = 0\n"
            "while n > 1:\n"
            "    n = n // 2 if n % 2 == 0 else 3 * n + 1\n"
            "    steps += 1\n"
            "print('collatz steps', steps)",
            "Print every even number from 2 to 20, then rewrite it with a while loop. Sum them.",
        ),
        (
            "python-input-practice",
            "Input, conversion and tiny programs",
            "Read from a person, convert types, and refuse garbage.",
            "`input(prompt)` always returns a string. `int(...)` and `float(...)` convert. "
            "A letter in `int('12a')` raises `ValueError` — catch it or the program dies.\n\n"
            "Never trust input. Strip whitespace. Check ranges. Ask again on failure.\n\n"
            "This is the first real-world shape: prompt → convert → decide → print.",
            "raw = '72'  # stand-in for input('score: ')\n"
            "try:\n"
            "    score = int(raw.strip())\n"
            "except ValueError:\n"
            "    print('not a number')\n"
            "else:\n"
            "    if 0 <= score <= 100:\n"
            "        print('recorded', score)\n"
            "    else:\n"
            "        print('out of range')",
            "Write a loop that asks for positive integers until the user types 0, then prints the count and the sum.",
        ),
        (
            "python-real-world-1",
            "Real-world drills I",
            "Small problems that use only variables, decisions and loops.",
            "Professionals do not skip drills. These are the same shapes you will meet in "
            "billing, sensors and reports.\n\n"
            "1. FizzBuzz: 1 to 30, `Fizz` on multiples of 3, `Buzz` on 5, both on 15.\n"
            "2. Palindrome: a string that reads the same backwards.\n"
            "3. Running total: keep adding numbers until a sentinel.\n"
            "4. Min/max: scan a list once, not sort it.\n\n"
            "Write them without looking up answers. Then compare with the example.",
            "for n in range(1, 31):\n"
            "    if n % 15 == 0:\n"
            "        print('FizzBuzz')\n"
            "    elif n % 3 == 0:\n"
            "        print('Fizz')\n"
            "    elif n % 5 == 0:\n"
            "        print('Buzz')\n"
            "    else:\n"
            "        print(n)\n"
            "\n"
            "word = 'level'\n"
            "print(word, 'palindrome' if word == word[::-1] else 'not')",
            "A shop gives 10% off above 1000. Write a program that takes three item prices and prints the bill with tax at 5%.",
        ),
        (
            "python-lists-scratch",
            "Lists from scratch",
            "An ordered, mutable sequence — the workhorse of Python programs.",
            "A list is written `[1, 2, 3]`. Index from 0. Negative index counts from the end.\n\n"
            "`append` adds. `pop` removes. `len` is length. Slice `items[1:3]` is a new list.\n\n"
            "`for x in items` walks values. `for i, x in enumerate(items)` walks index and value.\n\n"
            "Do not mutate a list you are iterating if you can avoid it. Build a new one.",
            "marks = [72, 85, 91, 68]\n"
            "marks.append(77)\n"
            "print(marks[0], marks[-1], len(marks))\n"
            "print(sum(marks) / len(marks))\n"
            "passed = [m for m in marks if m >= 75]\n"
            "print('passed', passed)",
            "Store seven daily temperatures. Print the average, the hottest day index, and how many days were above 30.",
        ),
        (
            "python-stdlib-os",
            "The standard library you will actually use",
            "datetime, pathlib, json, random, statistics — batteries that are already installed.",
            "Before you install a package, look in the standard library.\n\n"
            "`datetime` for dates. `pathlib.Path` for files. `json` for data interchange. "
            "`random` for simulations (not for security). `statistics` for mean and median.\n\n"
            "`import json` loads a module. A module is a file of names. The next stage "
            "teaches you to write your own.",
            "from datetime import date\n"
            "import json, statistics\n"
            "marks = [72, 85, 91, 68]\n"
            "payload = {'day': date.today().isoformat(), 'mean': statistics.mean(marks)}\n"
            "print(json.dumps(payload, indent=2))",
            "Write a script that dumps today's date and a list of three tasks to tasks.json and reads it back.",
        ),
        (
            "python-packaging",
            "Virtual environments and your own module",
            "Isolate dependencies, split code into files, run only when intended.",
            "`python -m venv .venv` then activate it. Packages you install stay in that "
            "folder. Production and classmates can recreate it from `requirements.txt`.\n\n"
            "A `.py` file is a module. `import tools` loads `tools.py`. "
            "`if __name__ == '__main__':` runs only when you execute the file, not when "
            "someone imports it.\n\n"
            "This is the professional habit: small functions, a module boundary, a way to "
            "run checks again.",
            "# tools.py\n"
            "def clamp(value, low, high):\n"
            "    return max(low, min(high, value))\n"
            "\n"
            "if __name__ == '__main__':\n"
            "    assert clamp(150, 0, 100) == 100\n"
            "    print('ok')",
            "Split clamp into tools.py, import it from main.py, and run one passing and one failing assertion on purpose.",
        ),
    ],
    "java": [
        (
            "java-why",
            "Why Java exists",
            "A typed language built for large, long-lived systems.",
            "Java is statically typed and compiled to bytecode that the JVM runs. The same "
            "`.class` files run on Linux, Windows and Android runtimes.\n\n"
            "Banks, Android apps, Hadoop, and huge internal tools are Java (or Kotlin on the "
            "same JVM). Types catch a class of bugs before the program runs.\n\n"
            "You will write more characters than in Python. That verbosity is the point: "
            "names, types and access modifiers are documentation the compiler checks.",
            "public class WhyJava {\n"
            "    public static void main(String[] args) {\n"
            "        System.out.println(\"Java: one language, many machines.\");\n"
            "    }\n"
            "}",
            "List three systems you have used that are likely backed by Java, and one reason a team would still choose it in 2026.",
        ),
        (
            "java-hello",
            "Hello World, classes and main",
            "Every Java program starts at `public static void main`.",
            "A source file `Hello.java` contains a class `Hello`. `javac Hello.java` produces "
            "`Hello.class`. `java Hello` runs `main`.\n\n"
            "Statements end with `;`. Blocks use `{ }`. Types are written before names: "
            "`int year = 2026;`.\n\n"
            "Until you learn objects, treat `public class Name` and `main` as the ritual that "
            "lets the JVM find your code.",
            "public class Hello {\n"
            "    public static void main(String[] args) {\n"
            "        System.out.println(\"Hello, EngineVerse\");\n"
            "        int year = 2026;\n"
            "        System.out.println(year);\n"
            "    }\n"
            "}",
            "Compile and run a class that prints your name and the sum of 19 and 23.",
        ),
        (
            "java-operators",
            "Java operators",
            "Arithmetic, comparison, boolean and the increment operators you will see everywhere.",
            "`+ - * / %` on integers truncate toward zero. `5 / 2` is `2`. Cast to `double` "
            "when you want a fraction.\n\n"
            "`==` on primitives compares values. On objects it compares references — use "
            "`equals` for strings.\n\n"
            "`&&` and `||` short-circuit. `++i` / `i++` change a variable; prefer `i += 1` "
            "until you are sure which one you mean.",
            "public class Ops {\n"
            "    public static void main(String[] args) {\n"
            "        int a = 17, b = 5;\n"
            "        System.out.println(a / b);\n"
            "        System.out.println((double) a / b);\n"
            "        System.out.println(\"hi\".equals(\"hi\"));\n"
            "        System.out.println(a > 10 && b < 10);\n"
            "    }\n"
            "}",
            "Print whether 2026 is a leap year using % 4, % 100 and % 400.",
        ),
        (
            "java-decisions",
            "if, else and switch",
            "Branch on conditions with types the compiler already checked.",
            "`if / else if / else` as in every C-family language. Conditions must be "
            "`boolean` — you cannot write `if (score)` on an int.\n\n"
            "Modern `switch` can return a value with arrows. Exhaustiveness on enums is a "
            "feature: the compiler nags when you forget a case.\n\n"
            "Guard bad input at the top of the method and return early.",
            "public class Grade {\n"
            "    static String grade(int score) {\n"
            "        if (score < 0 || score > 100) throw new IllegalArgumentException(\"range\");\n"
            "        if (score >= 90) return \"A\";\n"
            "        if (score >= 75) return \"B\";\n"
            "        if (score >= 50) return \"C\";\n"
            "        return \"F\";\n"
            "    }\n"
            "    public static void main(String[] args) {\n"
            "        System.out.println(grade(73));\n"
            "    }\n"
            "}",
            "Write a method that returns the ticket price for child/adult/senior using if, then rewrite the same rules with switch on an enum.",
        ),
        (
            "java-loops-from-scratch",
            "for, while and arrays",
            "Repeat work over a fixed-size array and a growing list.",
            "`for (int i = 0; i < n; i++)` is the classic loop. Enhanced `for (int x : xs)` "
            "walks values.\n\n"
            "Arrays have a fixed length. `ArrayList` grows. Out-of-bounds throws instead of "
            "corrupting memory.\n\n"
            "`break` and `continue` work as you expect.",
            "public class Loops {\n"
            "    public static void main(String[] args) {\n"
            "        int[] marks = {72, 85, 91, 68};\n"
            "        int total = 0;\n"
            "        for (int m : marks) total += m;\n"
            "        System.out.println(total / (double) marks.length);\n"
            "        for (int n = 1; n <= 10; n++) {\n"
            "            System.out.println(\"7 x \" + n + \" = \" + (7 * n));\n"
            "        }\n"
            "    }\n"
            "}",
            "Print the multiplication table of 9, store the products in an array, and print their sum.",
        ),
        (
            "java-real-world-1",
            "Real-world drills in Java",
            "FizzBuzz, min/max and a tiny bill — with types.",
            "Write these before objects: they prove you can run the language.\n\n"
            "Reject scores outside 0–100 with an exception. Sum with `long` if the count can "
            "grow. Format with `printf`.",
            "public class Drills {\n"
            "    public static void main(String[] args) {\n"
            "        for (int n = 1; n <= 30; n++) {\n"
            "            if (n % 15 == 0) System.out.println(\"FizzBuzz\");\n"
            "            else if (n % 3 == 0) System.out.println(\"Fizz\");\n"
            "            else if (n % 5 == 0) System.out.println(\"Buzz\");\n"
            "            else System.out.println(n);\n"
            "        }\n"
            "    }\n"
            "}",
            "Three item prices as doubles, 10% off over 1000, 5% tax. Print a line-item bill.",
        ),
        (
            "java-methods",
            "Methods before objects",
            "Name a piece of work, give it parameters, return a result.",
            "`static` methods belong to the class, not an instance. Start here. Instance "
            "methods come with objects.\n\n"
            "Parameters are passed by value. For objects the value is a reference, so the "
            "callee can mutate the object but cannot rebind the caller's variable.\n\n"
            "One method, one job. Name it after the result: `average`, `clamp`, `grade`.",
            "public class Methods {\n"
            "    static int clamp(int value, int low, int high) {\n"
            "        return Math.max(low, Math.min(high, value));\n"
            "    }\n"
            "    public static void main(String[] args) {\n"
            "        System.out.println(clamp(150, 0, 100));\n"
            "        System.out.println(clamp(-3, 0, 100));\n"
            "    }\n"
            "}",
            "Write average(int[] xs) that returns 0.0 on empty, and test empty, one element, and four elements.",
        ),
    ],
    "javascript": [
        (
            "js-why",
            "Why JavaScript exists",
            "The language the browser already runs — and Node.js took to the server.",
            "Every web page can run JavaScript. There is no install step for the reader. "
            "That is why front-end engineering is JavaScript (or TypeScript that compiles to it).\n\n"
            "Node.js uses the same language on the server. One language, two runtimes, very "
            "different APIs (`document` vs `fs`).\n\n"
            "It is dynamically typed. `==` coerces; `===` does not. Professionals use `===`, "
            "`const`/`let`, and never `innerHTML` with user text.",
            "console.log('JavaScript runs where the user already is.');\n"
            "console.log(typeof 3, typeof '3', 3 === '3');",
            "Open the browser console on any page and evaluate 0 == '' versus 0 === ''. Write one sentence on why === is the default.",
        ),
        (
            "js-hello",
            "Hello World in the console and a file",
            "`node hello.js` or a `<script>` tag — same language.",
            "`console.log` writes a line. `const` cannot be rebound. `let` can. Never `var`.\n\n"
            "A statement usually ends at the newline. Semicolons are optional and still "
            "recommended in teams that want ASI surprises gone.\n\n"
            "Template strings use backticks: `` `Hello, ${name}` ``.",
            "const name = 'EngineVerse';\n"
            "let year = 2026;\n"
            "console.log(`Hello, ${name} in ${year}`);",
            "Write hello.js that prints your name and 2 ** 8, and run it with node.",
        ),
        (
            "js-operators",
            "Operators and types",
            "Numbers, strings, booleans, and the coercion traps.",
            "`+` adds numbers and concatenates strings. `'2' + 2` is `'22'`. Number() or "
            "`Number.parseInt` when you mean a number.\n\n"
            "`NaN` is not equal to itself. Use `Number.isNaN`.\n\n"
            "`&&` `||` `??` (nullish) `?.` (optional chaining) are everyday tools.",
            "console.log(2 + 2, '2' + 2, Number('2') + 2);\n"
            "console.log(Number.isNaN(Number('x')));\n"
            "const user = { name: 'Asha' };\n"
            "console.log(user.city ?? 'unknown');",
            "Parse three strings that look like numbers, skip the ones that are NaN, and print the sum.",
        ),
        (
            "js-decisions-loops",
            "if, else, for and while",
            "Control flow without the DOM yet.",
            "`if / else if / else`. `for (let i = 0; i < n; i++)`. `for (const x of xs)`. "
            "`while`.\n\n"
            "`switch` exists; `===` matching. Prefer a map or ifs for two or three cases.\n\n"
            "Arrays are dynamic. `push`, `length`, `map`, `filter` come next — first, write a for loop by hand.",
            "const marks = [72, 85, 91, 68];\n"
            "let total = 0;\n"
            "for (const m of marks) total += m;\n"
            "const avg = total / marks.length;\n"
            "console.log(avg >= 75 ? 'pass with merit' : 'pass');\n"
            "for (let n = 1; n <= 10; n++) console.log(`7 × ${n} = ${7 * n}`);",
            "FizzBuzz 1–30 in the console, then rewrite the loop with while.",
        ),
        (
            "js-real-world-1",
            "Real-world drills in JavaScript",
            "A bill, a palindrome, and a running average — in the language of the browser.",
            "These run in Node or the console. No page required.\n\n"
            "Reject non-numbers with `typeof` and `Number.isFinite`. Do not use `==`.",
            "function palindrome(word) {\n"
            "  const s = String(word).toLowerCase();\n"
            "  return s === [...s].reverse().join('');\n"
            "}\n"
            "console.log(palindrome('Level'), palindrome('Engine'));\n"
            "function bill(prices) {\n"
            "  const net = prices.reduce((a, b) => a + b, 0);\n"
            "  const discounted = net > 1000 ? net * 0.9 : net;\n"
            "  return discounted * 1.05;\n"
            "}\n"
            "console.log(bill([400, 400, 300]));",
            "Write grade(score) with boundaries 90/75/50 and throw TypeError on a non-number. Call it on 91, 50, and '72'.",
        ),
        (
            "js-functions-scratch",
            "Functions as values",
            "function declarations, arrows, and why defaults matter.",
            "`function grade(score) {}` is hoisted. `const grade = (score) => {}` is not.\n\n"
            "Default parameters: `function clamp(n, low = 0, high = 100)`.\n\n"
            "Return early. One function, one job. The next modules put these functions on "
            "buttons and then on a server.",
            "const clamp = (n, low = 0, high = 100) => Math.max(low, Math.min(high, n));\n"
            "console.log(clamp(150), clamp(-3), clamp(40));",
            "Write average(xs) that returns 0 on an empty array, and a second function that uses it to print a report object.",
        ),
    ],
    "typescript": [
        (
            "ts-why",
            "Why TypeScript exists",
            "JavaScript plus a type checker that runs before the browser does.",
            "TypeScript erases types when it compiles to JavaScript. The browser still runs "
            "JS. The win is that `tsc` (or your editor) refuses `grade('72')` if you said "
            "`score: number`.\n\n"
            "Types are not a runtime firewall. JSON from the network is still `unknown` until "
            "you validate it. That is the whole later path.",
            "function greet(name: string): string {\n"
            "  return `Hello, ${name}`;\n"
            "}\n"
            "console.log(greet('EngineVerse'));",
            "Write add(a: number, b: number): number and try to call it with a string. Read the error. Then fix it.",
        ),
        (
            "ts-hello",
            "Hello World with types",
            "`let year: number`, interfaces, and `tsc`.",
            "`const name: string = 'Asha'`. If the initializer is obvious, let inference work.\n\n"
            "`interface User { name: string; marks: number[] }` names a shape.\n\n"
            "Run `npx tsc --noEmit` on a file. No emit still type-checks.",
            "interface User { name: string; marks: number[] }\n"
            "const asha: User = { name: 'Asha', marks: [72, 85] };\n"
            "const avg = asha.marks.reduce((a, b) => a + b, 0) / asha.marks.length;\n"
            "console.log(asha.name, avg.toFixed(1));",
            "Define Product { name, price } and a function that returns the taxed total of an array of products.",
        ),
        (
            "ts-decisions-loops",
            "Control flow, unions and narrowing",
            "if/else and for, plus types that get smaller as you check them.",
            "`type Id = string | number`. After `if (typeof id === 'string')` the type inside "
            "the block is `string`. That is narrowing.\n\n"
            "The same if/for/while as JavaScript. The extra power is refusing the wrong call "
            "before runtime.",
            "function label(id: string | number): string {\n"
            "  if (typeof id === 'string') return id.trim();\n"
            "  return String(id);\n"
            "}\n"
            "for (let n = 1; n <= 5; n++) console.log(label(n), label('  x  '));",
            "Write grade(score: number): 'A' | 'B' | 'C' | 'F' and a loop that prints grades for [91, 75, 49].",
        ),
        (
            "ts-real-world-1",
            "Real-world drills in TypeScript",
            "A typed bill and a typed clamp — still no framework.",
            "Keep functions tiny. Export them when you split files. Tests come in working practice.",
            "export function clamp(n: number, low = 0, high = 100): number {\n"
            "  return Math.max(low, Math.min(high, n));\n"
            "}\n"
            "export function bill(prices: number[]): number {\n"
            "  const net = prices.reduce((a, b) => a + b, 0);\n"
            "  return (net > 1000 ? net * 0.9 : net) * 1.05;\n"
            "}\n"
            "console.log(clamp(150), bill([400, 400, 300]));",
            "Add a TaxConfig type { rate: number } and make bill take it instead of hard-coding 1.05.",
        ),
    ],
    "cpp": [
        (
            "cpp-why",
            "Why C++ exists",
            "Control of memory and speed, with abstractions that can cost nothing.",
            "C++ sits on C and adds classes, templates, RAII and the STL. Game engines, "
            "browsers, databases and contest programming use it because you can see every "
            "allocation — and because a tight loop stays a tight loop.\n\n"
            "Undefined behaviour is the cost. Out-of-bounds is not an exception unless you "
            "use tools that add one. Later modules teach RAII so resources still get released.",
            "#include <iostream>\n"
            "int main() {\n"
            "    std::cout << \"C++ is for when the cost of a layer matters\\n\";\n"
            "}",
            "Name two programs on your machine that are likely C++, and one risk of writing C++ like Python.",
        ),
        (
            "cpp-hello",
            "Hello World, compile and run",
            "`g++ -std=c++17 hello.cpp -o hello` then `./hello`.",
            "`#include <iostream>` brings `std::cout`. `int main()` returns 0 on success.\n\n"
            "Compile with a standard: `-std=c++17` or newer. Warnings: `-Wall -Wextra`.\n\n"
            "`using namespace std;` in a header is a professional foul. In a 10-line drill it is merely lazy.",
            "#include <iostream>\n"
            "int main() {\n"
            "    int year = 2026;\n"
            "    std::cout << \"Hello, EngineVerse \" << year << '\\n';\n"
            "    return 0;\n"
            "}",
            "Compile with -Wall and fix every warning. Print 19 + 23.",
        ),
        (
            "cpp-variables-operators",
            "Variables, types and operators",
            "`int`, `double`, `bool`, `std::string`, and integer division.",
            "`int a = 17;` `double` for fractions. `5 / 2` is `2`. `5.0 / 2` is `2.5`.\n\n"
            "`std::string` from `<string>`. `==` works for strings.\n\n"
            "Prefer `std::int64_t` from `<cstdint>` when the width matters.",
            "#include <iostream>\n"
            "#include <string>\n"
            "int main() {\n"
            "    int a = 17, b = 5;\n"
            "    std::string name = \"EngineVerse\";\n"
            "    std::cout << a / b << ' ' << a / 5.0 << '\\n';\n"
            "    std::cout << name << ' ' << (a > b) << '\\n';\n"
            "}",
            "Read two integers (or hard-code them) and print quotient, remainder, and whether the first is even.",
        ),
        (
            "cpp-decisions-loops",
            "if, for and while",
            "Control flow and a first array.",
            "`if / else`. `for (int i = 0; i < n; ++i)`. Range-for: `for (int x : xs)`.\n\n"
            "`std::vector<int>` from `<vector>` grows. `xs.size()` is the length. "
            "`xs.at(i)` throws on a bad index; `xs[i]` does not.",
            "#include <iostream>\n"
            "#include <vector>\n"
            "int main() {\n"
            "    std::vector<int> marks{72, 85, 91, 68};\n"
            "    int total = 0;\n"
            "    for (int m : marks) total += m;\n"
            "    std::cout << total / static_cast<double>(marks.size()) << '\\n';\n"
            "    for (int n = 1; n <= 10; ++n) std::cout << 7 * n << '\\n';\n"
            "}",
            "FizzBuzz 1–30, then store seven temperatures in a vector and print min, max and mean.",
        ),
        (
            "cpp-real-world-1",
            "Real-world drills in C++",
            "A bill and a clamp, compiled with warnings as errors.",
            "Compile with `-Wall -Wextra -Werror`. That is a professional default.\n\n"
            "Pass vectors by `const std::vector<int>&` so you do not copy.",
            "#include <algorithm>\n"
            "#include <iostream>\n"
            "int clamp(int v, int lo, int hi) { return std::max(lo, std::min(hi, v)); }\n"
            "int main() {\n"
            "    std::cout << clamp(150, 0, 100) << '\\n';\n"
            "}",
            "Write average(const std::vector<double>&) that returns 0 on empty, and a bill() with 10% off over 1000.",
        ),
        (
            "cpp-functions-scratch",
            "Functions, headers later",
            "Declarations, definitions, and why a function belongs in one place.",
            "A function has a return type, a name, and parameters. Define it before `main` or "
            "declare it first.\n\n"
            "Later you will split declaration into a `.h` and definition into a `.cpp`. For "
            "now, one file is honest.",
            "#include <iostream>\n"
            "int add(int a, int b) { return a + b; }\n"
            "int main() { std::cout << add(19, 23) << '\\n'; }",
            "Write is_leap(int year) and print 1900, 2000, 2024, 2026.",
        ),
    ],
    "go": [
        (
            "go-why",
            "Why Go exists",
            "A small language for network services, tools and boring reliability.",
            "Go (Golang) was built at Google for servers: fast compile, a complete standard "
            "library, goroutines for concurrency, and `gofmt` so nobody argues about braces.\n\n"
            "It is statically typed. Errors are values: `result, err := thing()`. You check "
            "`err` on purpose. That habit is the language.",
            "package main\n"
            "import \"fmt\"\n"
            "func main() { fmt.Println(\"Go is for services you can still read in a year\") }",
            "Name one CLI tool you use that is written in Go (git is not; docker, gh, terraform often are) and why a small language helps a large team.",
        ),
        (
            "go-hello",
            "Hello World, packages and go run",
            "`go run hello.go` — package main is the program.",
            "`package main` plus `func main()` is the entry. `import \"fmt\"`.\n\n"
            "`go run .` in a module. `go build` writes a binary. No classes. Functions and "
            "structs are enough to start.",
            "package main\n"
            "import \"fmt\"\n"
            "func main() {\n"
            "    name := \"EngineVerse\"\n"
            "    year := 2026\n"
            "    fmt.Println(name, year)\n"
            "}",
            "Print your name and 19+23 with go run.",
        ),
        (
            "go-variables-operators",
            "Variables, types and operators",
            "`:=`, zero values, and integer division.",
            "`var n int` is 0. `name := \"Asha\"` infers string. Exported names start with a "
            "capital letter.\n\n"
            "`5 / 2` is `2`. Convert with `float64(a) / float64(b)`.\n\n"
            "`==` works on comparable types. Slices are not comparable.",
            "package main\n"
            "import \"fmt\"\n"
            "func main() {\n"
            "    a, b := 17, 5\n"
            "    fmt.Println(a/b, float64(a)/float64(b), a%b)\n"
            "}",
            "Declare marks []int, print len, cap after append, and the mean as float64.",
        ),
        (
            "go-decisions-loops",
            "if, for — the only loop",
            "Go has one loop keyword. if can have a short statement.",
            "`for i := 0; i < n; i++ {}`. `for _, v := range xs {}`. `for condition {}` is "
            "while. `for {}` is forever.\n\n"
            "`if err := work(); err != nil { return err }` is the everyday shape.",
            "package main\n"
            "import \"fmt\"\n"
            "func main() {\n"
            "    marks := []int{72, 85, 91, 68}\n"
            "    total := 0\n"
            "    for _, m := range marks { total += m }\n"
            "    fmt.Println(float64(total) / float64(len(marks)))\n"
            "    for n := 1; n <= 10; n++ { fmt.Println(7 * n) }\n"
            "}",
            "FizzBuzz 1–30 and a function clamp(v, lo, hi int) int.",
        ),
        (
            "go-real-world-1",
            "Real-world drills in Go",
            "A bill, a palindrome, and an error return.",
            "Return `(float64, error)` from bill when the slice is empty. Check the error in main.",
            "package main\n"
            "import (\n"
            "    \"errors\"\n"
            "    \"fmt\"\n"
            ")\n"
            "func bill(prices []float64) (float64, error) {\n"
            "    if len(prices) == 0 { return 0, errors.New(\"empty\") }\n"
            "    var net float64\n"
            "    for _, p := range prices { net += p }\n"
            "    if net > 1000 { net *= 0.9 }\n"
            "    return net * 1.05, nil\n"
            "}\n"
            "func main() {\n"
            "    total, err := bill([]float64{400, 400, 300})\n"
            "    if err != nil { fmt.Println(err); return }\n"
            "    fmt.Println(total)\n"
            "}",
            "Write average(xs []float64) (float64, error) and test empty vs three values in main.",
        ),
    ],
    "rust": [
        (
            "rust-why",
            "Why Rust exists",
            "Memory safety without a garbage collector, for systems that cannot crash quietly.",
            "Rust uses ownership: each value has one owner, borrows are checked, and data "
            "races are compile errors. Browsers, kernels, CLIs and cloud agents increasingly "
            "pick it when C++ undefined behaviour is not acceptable.\n\n"
            "The compiler is strict. That is the product. Fighting the borrow checker is "
            "learning the model, not failing the language.",
            "fn main() {\n"
            "    println!(\"Rust makes the dangerous things loud.\");\n"
            "}",
            "Write one sentence on ownership and one on why a CLI might choose Rust over Go.",
        ),
        (
            "rust-hello",
            "Hello World and cargo",
            "`cargo new hello` then `cargo run`.",
            "`fn main()` is the entry. `println!` is a macro — notice the `!`.\n\n"
            "`let x = 3;` is immutable. `let mut x = 3;` can change. Immutability by default "
            "is a professional default in any language; Rust enforces it.",
            "fn main() {\n"
            "    let name = \"EngineVerse\";\n"
            "    let year = 2026;\n"
            "    println!(\"Hello, {name} in {year}\");\n"
            "}",
            "Create a cargo binary that prints 19+23 and your name.",
        ),
        (
            "rust-variables-operators",
            "Types, operators and Result later",
            "`i32`, `f64`, `bool`, `String`, and integer division.",
            "`17 / 5` is `3`. Cast with `as f64` carefully. `i32::checked_add` returns "
            "`Option` instead of wrapping.\n\n"
            "`String` owns text. `&str` borrows it. Start with `String::from` and `.len()`.",
            "fn main() {\n"
            "    let a = 17;\n"
            "    let b = 5;\n"
            "    println!(\"{} {}\", a / b, a as f64 / b as f64);\n"
            "}",
            "Print whether 2024 is a leap year using %.",
        ),
        (
            "rust-decisions-loops",
            "if, loop, while, for",
            "if is an expression. for walks iterators.",
            "`let grade = if score >= 90 { 'A' } else { 'B' };`\n\n"
            "`for n in 1..=10`. `while`. `loop { break; }`.\n\n"
            "`Vec<i32>` grows. `vec![1,2,3]`. `iter()` borrows; `into_iter()` consumes.",
            "fn main() {\n"
            "    let marks = vec![72, 85, 91, 68];\n"
            "    let total: i32 = marks.iter().sum();\n"
            "    println!(\"{}\", total as f64 / marks.len() as f64);\n"
            "    for n in 1..=10 { println!(\"{}\", 7 * n); }\n"
            "}",
            "FizzBuzz 1..=30 and a clamp(v, lo, hi: i32) -> i32.",
        ),
        (
            "rust-real-world-1",
            "Real-world drills in Rust",
            "A bill that returns Result, because empty input is an error.",
            "`Result<T, E>` forces the caller to handle failure. That is the professional "
            "shape you will keep through HTTP and files.",
            "fn bill(prices: &[f64]) -> Result<f64, &'static str> {\n"
            "    if prices.is_empty() { return Err(\"empty\"); }\n"
            "    let mut net: f64 = prices.iter().sum();\n"
            "    if net > 1000.0 { net *= 0.9; }\n"
            "    Ok(net * 1.05)\n"
            "}\n"
            "fn main() {\n"
            "    match bill(&[400.0, 400.0, 300.0]) {\n"
            "        Ok(total) => println!(\"{total}\"),\n"
            "        Err(e) => println!(\"{e}\"),\n"
            "    }\n"
            "}",
            "Write average(xs: &[f64]) -> Option<f64> and print Some vs None.",
        ),
    ],
    "c": [
        (
            "c-why",
            "Why C exists",
            "The language operating systems, embedded chips and other languages are built in.",
            "C is small: types, pointers, structs, and a standard library that is really a "
            "set of functions. Linux, Python's interpreter, and microcontrollers speak C.\n\n"
            "There is no safety net. A bad pointer is undefined behaviour. Learning C is "
            "learning what a byte, a stack frame and a segfault are.\n\n"
            "A professional C programmer compiles with warnings, never `gets`, checks "
            "`malloc`, and treats every buffer as a length plus a pointer.",
            "#include <stdio.h>\n"
            "int main(void) {\n"
            "    puts(\"C is close to the machine on purpose.\");\n"
            "    return 0;\n"
            "}",
            "Name one tool on your computer that is written in C, and one bug class (overflow, use-after-free) you will refuse to ignore.",
        ),
        (
            "c-hello",
            "Hello World, compile and return codes",
            "`cc -Wall -Wextra -std=c11 hello.c -o hello`.",
            "`#include <stdio.h>` for `printf`. `int main(void)` returns 0 on success.\n\n"
            "`printf` needs a format string. Never pass user text as the format.\n\n"
            "Warnings are errors in waiting. Add `-Werror` once the file is clean.",
            "#include <stdio.h>\n"
            "int main(void) {\n"
            "    printf(\"Hello, EngineVerse\\n\");\n"
            "    printf(\"year %d\\n\", 2026);\n"
            "    return 0;\n"
            "}",
            "Print your name and 19+23. Compile with -Wall. Fix every warning.",
        ),
        (
            "c-variables",
            "Variables and types in C",
            "`int`, `long`, `double`, `char`, and why width matters.",
            "`int` is at least 16 bits, usually 32. Use `<stdint.h>` `int32_t` when the width "
            "is part of the contract.\n\n"
            "Uninitialised locals are garbage. Always initialise.\n\n"
            "`sizeof` tells you the width on this machine. Print it once so the machine is not a mystery.",
            "#include <stdio.h>\n"
            "#include <stdint.h>\n"
            "int main(void) {\n"
            "    int year = 2026;\n"
            "    double pi = 3.14159;\n"
            "    int32_t count = 3;\n"
            "    printf(\"%d %.2f %d sizes %zu %zu\\n\", year, pi, count, sizeof(int), sizeof(double));\n"
            "    return 0;\n"
            "}",
            "Declare marks for three subjects, print their average as a double, and print sizeof each type you used.",
        ),
        (
            "c-operators",
            "Operators and integer pitfalls",
            "Division truncates. Overflow wraps. `%` follows the dividend's sign.",
            "`5 / 2` is `2`. Cast one operand to `double` for a fraction.\n\n"
            "Signed overflow is undefined. Do not increment past `INT_MAX`.\n\n"
            "`&&` `||` short-circuit. `&` `|` `^` are bitwise — different operators.",
            "#include <stdio.h>\n"
            "int main(void) {\n"
            "    int a = 17, b = 5;\n"
            "    printf(\"%d %f %d\\n\", a / b, (double)a / b, a % b);\n"
            "    printf(\"%d\\n\", a > 10 && b < 10);\n"
            "    return 0;\n"
            "}",
            "Print whether 1900, 2000 and 2024 are leap years using %.",
        ),
        (
            "c-if-else",
            "if, else and switch",
            "Decisions with no boolean type in older C — still use `_Bool` or `stdbool.h`.",
            "`if (score >= 90) { ... } else if ... else`. Parentheses around the condition "
            "are required.\n\n"
            "`switch (c) { case 'A': ... break; default: ... }` — forgetting `break` falls "
            "through. That is a bug unless you comment it.\n\n"
            "`#include <stdbool.h>` for `true` and `false`.",
            "#include <stdio.h>\n"
            "int main(void) {\n"
            "    int score = 73;\n"
            "    char grade;\n"
            "    if (score >= 90) grade = 'A';\n"
            "    else if (score >= 75) grade = 'B';\n"
            "    else if (score >= 50) grade = 'C';\n"
            "    else grade = 'F';\n"
            "    printf(\"%d -> %c\\n\", score, grade);\n"
            "    return 0;\n"
            "}",
            "Write a fare printer for child/adult/senior ages using if, then the same with switch on a category char.",
        ),
        (
            "c-loops",
            "for, while and do-while",
            "Repeat work. Know when the loop ends before you write it.",
            "`for (int i = 0; i < n; i++)` needs C99. `while (n > 0)`. `do { } while (cond)` "
            "runs once even if cond is false — rarely what you want.\n\n"
            "`break` and `continue`. An infinite loop is `for (;;)`.\n\n"
            "Count with `size_t` when the bound is a length.",
            "#include <stdio.h>\n"
            "int main(void) {\n"
            "    for (int n = 1; n <= 10; n++) {\n"
            "        printf(\"7 x %d = %d\\n\", n, 7 * n);\n"
            "    }\n"
            "    int n = 17, steps = 0;\n"
            "    while (n > 1) {\n"
            "        n = n % 2 == 0 ? n / 2 : 3 * n + 1;\n"
            "        steps++;\n"
            "    }\n"
            "    printf(\"steps %d\\n\", steps);\n"
            "    return 0;\n"
            "}",
            "Print even numbers 2..20 two ways (for and while) and their sum.",
        ),
        (
            "c-arrays-scratch",
            "Arrays and strings as arrays of char",
            "A length you must track yourself, and a zero byte that ends a string.",
            "`int marks[4] = {72, 85, 91, 68};` Length is not stored. Pass `n` with the pointer.\n\n"
            "`char name[] = \"Asha\";` is six bytes including `'\\0'`. `strlen` counts before "
            "the zero. Never write past `n - 1`.\n\n"
            "This module is the seed of every later buffer bug. Treat length as data.",
            "#include <stdio.h>\n"
            "int main(void) {\n"
            "    int marks[] = {72, 85, 91, 68};\n"
            "    int n = (int)(sizeof marks / sizeof marks[0]);\n"
            "    int total = 0;\n"
            "    for (int i = 0; i < n; i++) total += marks[i];\n"
            "    printf(\"avg %.2f\\n\", total / (double)n);\n"
            "    char word[] = \"level\";\n"
            "    printf(\"%s\\n\", word);\n"
            "    return 0;\n"
            "}",
            "Store seven temperatures, print min, max and mean. Then copy a string with a loop until '\\0', into a buffer of known size.",
        ),
        (
            "c-real-world-1",
            "Real-world drills in C",
            "FizzBuzz, clamp, and a bill — with no hidden allocations.",
            "No `malloc` yet. Stack arrays. Check every format. Return non-zero from `main` "
            "on bad input.",
            "#include <stdio.h>\n"
            "int clamp(int v, int lo, int hi) {\n"
            "    if (v < lo) return lo;\n"
            "    if (v > hi) return hi;\n"
            "    return v;\n"
            "}\n"
            "int main(void) {\n"
            "    for (int n = 1; n <= 30; n++) {\n"
            "        if (n % 15 == 0) puts(\"FizzBuzz\");\n"
            "        else if (n % 3 == 0) puts(\"Fizz\");\n"
            "        else if (n % 5 == 0) puts(\"Buzz\");\n"
            "        else printf(\"%d\\n\", n);\n"
            "    }\n"
            "    printf(\"%d\\n\", clamp(150, 0, 100));\n"
            "    return 0;\n"
            "}",
            "Three prices as doubles, 10% off over 1000, 5% tax. Print the total with two decimal places.",
        ),
        (
            "c-headers-modules",
            "Headers, .c files and make",
            "A module in C is a header plus a source file, compiled together.",
            "`tools.h` declares `int clamp(int v, int lo, int hi);`. `tools.c` defines it. "
            "`main.c` includes the header.\n\n"
            "Include guards: `#ifndef TOOLS_H` `#define TOOLS_H` ... `#endif`.\n\n"
            "`cc -c tools.c` then link. A Makefile records the commands so you do not type "
            "them wrong.\n\n"
            "This is the professional C habit: one job per file, a header that is the contract, "
            "warnings as errors.",
            "/* tools.h */\n"
            "#ifndef TOOLS_H\n"
            "#define TOOLS_H\n"
            "int clamp(int v, int lo, int hi);\n"
            "#endif\n"
            "\n"
            "/* tools.c */\n"
            "int clamp(int v, int lo, int hi) {\n"
            "    if (v < lo) return lo;\n"
            "    if (v > hi) return hi;\n"
            "    return v;\n"
            "}\n"
            "\n"
            "/* cc -Wall -std=c11 tools.c main.c */",
            "Split clamp into tools.h/tools.c, write a main that asserts clamp(150,0,100)==100, and a two-line Makefile.",
        ),
    ],
    "sql": [
        (
            "sql-why",
            "Why SQL exists",
            "Data lives in relations. SQL is how you ask them questions without writing a loop.",
            "A relational database stores tables: named columns, typed values, rows that are "
            "facts. SQL is the language of those facts: select, filter, join, group.\n\n"
            "Every backend you will write eventually speaks SQL, even if an ORM hides it. "
            "Professionals read the SQL.\n\n"
            "SQL is not a general-purpose language. No loops in everyday queries. Think in "
            "sets, not in rows one at a time.",
            "-- this is a query, not a program\n"
            "SELECT 'SQL asks the database; the database walks the rows' AS idea;",
            "Write one sentence on why filtering in SQL is safer and usually faster than loading a whole table into Python.",
        ),
        (
            "sql-hello",
            "Tables, rows and a first SELECT",
            "Name the columns you want. Never `SELECT *` in production.",
            "`CREATE TABLE` names columns and types. `INSERT` adds rows. `SELECT col FROM "
            "t` reads them.\n\n"
            "`*` is for exploration. Applications list columns so a new column does not "
            "break a client.",
            "CREATE TABLE marks (\n"
            "  id INTEGER PRIMARY KEY,\n"
            "  student TEXT NOT NULL,\n"
            "  score INTEGER NOT NULL\n"
            ");\n"
            "INSERT INTO marks (student, score) VALUES ('Asha', 72), ('Ravi', 91);\n"
            "SELECT student, score FROM marks;",
            "Create a subjects table with name and credits, insert three rows, and select only the names.",
        ),
        (
            "sql-real-world-1",
            "Real-world drills in SQL",
            "A bill-like aggregate, a filter, and a check constraint.",
            "`WHERE` filters rows. `AVG`, `SUM`, `COUNT` aggregate. `CHECK (score BETWEEN 0 "
            "AND 100)` refuses garbage at the door.\n\n"
            "Parameterise values in application code. The drills here use literals because "
            "there is no host language yet.",
            "SELECT student, AVG(score) AS avg_score\n"
            "FROM marks\n"
            "WHERE score >= 50\n"
            "GROUP BY student\n"
            "HAVING AVG(score) >= 75;",
            "Write a query that lists students with at least two scores and an average below 50 — the ones who need help.",
        ),
    ],
}


def slugs() -> dict[str, list[str]]:
    return {lang: [row[0] for row in rows] for lang, rows in FOUNDATION_MODULES.items()}

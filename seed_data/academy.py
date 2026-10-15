"""Original, structured learning units attached to existing language modules.

Shared algorithm explanations are intentional; syntax, runtime semantics,
examples and debugging advice are language-specific. No learner code executes
here. Verification runs only these trusted repository sources, never a form.
"""
from __future__ import annotations

from engineverse.lesson_schema import SECTION_TITLES, validate_unit

# Each program prints 6, then 3: a minimal loop and a practical basket total.
PROFILES = {
    "python": {
        "module": "python-loops-from-scratch", "version": "Python 3.11+", "extension": "py",
        "setup": "Save as lesson.py; run python3 lesson.py. Python parses the file and executes its top-level statements. No third-party package is needed.",
        "syntax": "A colon opens the loop suite and indentation defines its body. `range(1, 4)` yields 1, 2, 3: the stop is excluded. `for value in values` iterates elements, not indices. Integers have arbitrary precision subject to available memory; this is a language feature, not a promise of constant-cost arithmetic for huge values.",
        "code": "total = 0\nfor value in range(1, 4):\n    total += value\nprint(total)\n\nprices = [4, -2, 1]\nbalance = 0\nfor price in prices:\n    balance += price\nprint(balance)\n",
        "bug": "total = 0\nfor value in [1, 2, 3]:\n    total = 0  # wrong: discards previous iterations\n    total += value\nprint(total)  # 3, not 6\n",
        "fix": "Remove the assignment inside the loop. The initialization above the loop runs once. Then totals are 1, 3, 6. Python does not give a for loop its own block scope; the final loop variable remains bound for a nonempty iterable. Avoid relying on it after an empty iteration.",
        "reference": "import sys\n\ndef positive_total(values):\n    total = 0\n    for value in values:\n        if value > 0:\n            total += value\n    return total\n\ndata = list(map(int, sys.stdin.read().split()))\nn = data[0]\nprint(positive_total(data[1:1 + n]))\n",
        "ref": ("Python tutorial: control flow", "https://docs.python.org/3/tutorial/controlflow.html"),
        "next": "python-lists-scratch", "specific": "Compare an explicit accumulator with sum(values). The explicit version exposes state for debugging; sum is clearer once you understand the operation. A generator can filter without constructing another list.",
    },
    "c": {
        "module": "c-loops", "version": "C17", "extension": "c",
        "setup": "Save as lesson.c; compile with cc -std=c17 -Wall -Wextra -Wconversion lesson.c -o lesson, then run ./lesson. Compilation checks syntax/types; linking resolves printf from the C library. Use a local compiler, not a website form.",
        "syntax": "`for (initialization; condition; update)` checks the condition before each iteration. A declaration in the initializer is valid since C99. Braces group statements. `int` is at least 16 bits, not necessarily 32; our values and totals fit even that minimum in the examples. Signed integer overflow is undefined behavior. Size and range are implementation properties available via limits.h.",
        "code": "#include <stdio.h>\nint main(void) {\n    int total = 0;\n    for (int value = 1; value < 4; ++value) { total += value; }\n    printf(\"%d\\n\", total);\n    const int prices[] = {4, -2, 1};\n    int balance = 0;\n    for (int i = 0; i < 3; ++i) { balance += prices[i]; }\n    printf(\"%d\\n\", balance);\n    return 0;\n}\n",
        "bug": "int total = 0;\nfor (int value = 1; value < 4; ++value) {\n    total = 0; /* wrong: erases the prefix total */\n    total += value;\n}\n/* total is 3, not 6 */",
        "fix": "Remove the inner initialization. Do not fix a loop by changing i < 3 to i <= 3: prices[3] is outside this array and reading it has undefined behavior. A compiler need not diagnose it. Enable warnings and, when supported, address/undefined-behavior sanitizers in your local development build.",
        "reference": "#include <stdio.h>\nint main(void) {\n    int n;\n    if (scanf(\"%d\", &n) != 1 || n < 0 || n > 1000) return 1;\n    long long total = 0;\n    for (int i = 0; i < n; ++i) {\n        long long value;\n        if (scanf(\"%lld\", &value) != 1 || value < -1000000 || value > 1000000) return 1;\n        if (value > 0) total += value;\n    }\n    printf(\"%lld\\n\", total);\n    return 0;\n}\n",
        "ref": ("WG14: C11 committee draft N1570, §6.8.5 (iteration; applies to these C17 constructs)", "https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf"),
        "next": "c-arrays-scratch", "specific": "Indexing is appropriate for an array, but C does not attach a length to a pointer. Pass a length with an array parameter. Choose a while loop for input-driven termination; distinguish end-of-file from malformed input instead of reusing an uninitialized value.",
    },
    "cpp": {
        "module": "cpp-decisions-loops", "version": "C++17", "extension": "cpp",
        "setup": "Save as lesson.cpp; run c++ -std=c++17 -Wall -Wextra lesson.cpp -o lesson, then ./lesson. The compiler creates object code; the driver links the standard library. These examples require no nonstandard bits/stdc++.h header.",
        "syntax": "`for (int value = 1; value < 4; ++value)` initializes once, checks before each body, then increments. A range-based for iterates elements. Here `int price` copies each small integer; `const auto&` can avoid copying a large object. int width is platform-dependent; signed overflow is undefined behavior, even on machines with wrapping hardware instructions.",
        "code": "#include <iostream>\n#include <array>\nint main() {\n    int total = 0;\n    for (int value = 1; value < 4; ++value) total += value;\n    std::cout << total << '\\n';\n    const std::array<int, 3> prices{4, -2, 1};\n    int balance = 0;\n    for (int price : prices) balance += price;\n    std::cout << balance << '\\n';\n}\n",
        "bug": "int total = 0;\nfor (int value = 1; value < 4; ++value) {\n    total = 0; // wrong: loses previous values\n    total += value;\n}\n// total == 3",
        "fix": "Keep initialization before the loop, not in its body. For std::vector, operator[] does not do bounds checking; at() checks and throws on an invalid index. Do not modify a vector's size while iterating without understanding iterator invalidation. A range-for is not protection against invalidating its underlying iterators.",
        "reference": "#include <iostream>\nint main() {\n    int n;\n    if (!(std::cin >> n) || n < 0 || n > 1000) return 1;\n    long long total = 0;\n    for (int i = 0; i < n; ++i) {\n        long long value;\n        if (!(std::cin >> value) || value < -1000000 || value > 1000000) return 1;\n        if (value > 0) total += value;\n    }\n    std::cout << total << '\\n';\n}\n",
        "ref": ("C++ reference: range-based for (secondary reference)", "https://en.cppreference.com/w/cpp/language/range-for.html"),
        "next": "cpp-functions-scratch", "specific": "Use range-for when only values matter, indexed for when you need positions, and a standard algorithm when its contract expresses the operation better. std::accumulate's initial value determines the accumulator type: 0 and 0LL are not equivalent for large totals.",
    },
    "java": {
        "module": "java-loops-from-scratch", "version": "Java 17+", "extension": "java",
        "setup": "Save as Main.java; compile with javac --release 17 Main.java; run java Main. javac creates bytecode, then a JVM executes it. The JDK supplies both tools. Class and source filename match because Main is public.",
        "syntax": "The basic for has initialization, a boolean condition and an update. The enhanced for (`for (int price : prices)`) reads successive array elements; assigning price does not update an array element. int is a signed 32-bit type; overflowing integer addition wraps, it does not automatically report an error. Use long or Math.addExact when the contract requires it.",
        "code": "public class Main {\n    public static void main(String[] args) {\n        int total = 0;\n        for (int value = 1; value < 4; ++value) total += value;\n        System.out.println(total);\n        int[] prices = {4, -2, 1};\n        int balance = 0;\n        for (int price : prices) balance += price;\n        System.out.println(balance);\n    }\n}\n",
        "bug": "int total = 0;\nfor (int value = 1; value < 4; ++value) {\n    total = 0; // wrong: discards the accumulated prefix\n    total += value;\n}\n// total is 3",
        "fix": "Remove the inner assignment. An out-of-range array index throws ArrayIndexOutOfBoundsException, unlike C's undefined behavior. Read its stack trace and index before changing the loop. Array length is a field (prices.length), whereas String length is a method (text.length()).",
        "reference": "import java.util.Scanner;\npublic class Main {\n    public static void main(String[] args) {\n        Scanner input = new Scanner(System.in);\n        int n = input.nextInt();\n        long total = 0;\n        for (int i = 0; i < n; ++i) {\n            long value = input.nextLong();\n            if (value > 0) total += value;\n        }\n        System.out.println(total);\n    }\n}\n",
        "ref": ("Java Language Specification 17: §14.14, for statement", "https://docs.oracle.com/javase/specs/jls/se17/html/jls-14.html#jls-14.14"),
        "next": "java-methods", "specific": "An array loop avoids boxing. Streams can express filtering and summing, but use IntStream/LongStream for primitive numeric operations and do not mutate a shared accumulator in parallel forEach. A local ordinary loop is the simplest implementation to reason about here.",
    },
    "csharp": {
        "module": "csharp-decisions-loops", "version": "C# 10 / .NET 6 minimum; use a currently supported SDK", "extension": "cs",
        "setup": "Create a console project with dotnet new console -n LoopLab, replace Program.cs, and run dotnet run --project LoopLab. Top-level statements require C# 9+; these examples target C# 10/.NET 6 APIs and also work on newer SDKs. .NET 6 is an API baseline here, not a recommendation to deploy an unsupported runtime.",
        "syntax": "`foreach (int price in prices)` iterates values; the iteration variable cannot be assigned to. The ordinary for has initializer, boolean condition and update. int is signed 32-bit, long is signed 64-bit. Overflow behavior depends on checked/unchecked context and compiler configuration; use checked addition when exceeding the range must be an error.",
        "code": "using System;\nint total = 0;\nfor (int value = 1; value < 4; ++value) total += value;\nConsole.WriteLine(total);\nint[] prices = {4, -2, 1};\nint balance = 0;\nforeach (int price in prices) balance += price;\nConsole.WriteLine(balance);\n",
        "bug": "int total = 0;\nfor (int value = 1; value < 4; ++value) {\n    total = 0; // wrong: forgets previous iterations\n    total += value;\n}\n// total is 3",
        "fix": "Remove the assignment inside the loop. An index outside an array throws IndexOutOfRangeException. A null array fails before useful iteration: validate nullable inputs at an API boundary. Nullable annotations help static analysis but do not automatically enforce a runtime null check.",
        "reference": "using System;\nstring[] tokens = Console.In.ReadToEnd().Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries);\nint n = int.Parse(tokens[0]);\nlong total = 0;\nfor (int i = 0; i < n; ++i) {\n    long value = long.Parse(tokens[i + 1]);\n    if (value > 0) total = checked(total + value);\n}\nConsole.WriteLine(total);\n",
        "ref": ("C# language reference: iteration statements", "https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/statements/iteration-statements"),
        "next": "csharp-methods", "specific": "LINQ Where(...).Sum() expresses filtering plus aggregation, while foreach gives explicit state and early exits. Enumeration is not always a materialized array; repeated enumeration can repeat work or side effects. Do not claim that any IEnumerable traversal has constant total cost.",
    },
    "javascript": {
        "module": "js-decisions-loops", "version": "ECMAScript 2022 / Node.js 18+ APIs", "extension": "js",
        "setup": "Save as lesson.js; run node lesson.js using a currently supported Node release. Browser console examples can use console.log, but the reference's fs input is Node-specific. JavaScript language rules and Node APIs are different layers.",
        "syntax": "Use let for a changing accumulator and const for an array binding you do not reassign. const does not freeze the array's contents. for...of reads values; for...in enumerates property keys and is not an array-value loop. Number is binary64 floating point: integers are exact only through Number.MAX_SAFE_INTEGER (2^53 - 1). Our bounded integer totals are safely below it.",
        "code": "let total = 0;\nfor (let value = 1; value < 4; ++value) total += value;\nconsole.log(total);\nconst prices = [4, -2, 1];\nlet balance = 0;\nfor (const price of prices) balance += price;\nconsole.log(balance);\n",
        "bug": "let total = 0;\nfor (const value of [1, 2, 3]) {\n  total = 0; // wrong: resets the state\n  total += value;\n}\nconsole.log(total); // 3",
        "fix": "Remove the inner assignment. Also check types: adding the string '4' concatenates, so a mixed input can turn total into text. Explicitly parse and validate external input. Avoid silently coercing arbitrary values with loose equality. Reading an absent array element gives undefined; arithmetic with it can produce NaN rather than a useful bounds error.",
        "reference": "const fs = require('node:fs');\nconst data = fs.readFileSync(0, 'utf8').trim().split(/\\s+/).map(Number);\nconst n = data[0];\nlet total = 0;\nfor (let i = 0; i < n; ++i) {\n  const value = data[i + 1];\n  if (value > 0) total += value;\n}\nconsole.log(total);\n",
        "ref": ("ECMAScript: for-in and for-of statements", "https://tc39.es/ecma262/multipage/ecmascript-language-statements-and-declarations.html#sec-for-in-and-for-of-statements"),
        "next": "js-functions-scratch", "specific": "reduce can express aggregation, but always supply an initial value for an empty collection. An explicit loop is easier to step through. Neither form makes a slow algorithm fast by itself; avoid building copied accumulator arrays on every iteration.",
    },
    "typescript": {
        "module": "ts-decisions-loops", "version": "TypeScript 5+, target ES2022", "extension": "ts",
        "setup": "Save as lesson.ts; with a local TypeScript compiler run tsc --strict --target ES2022 lesson.ts, then node lesson.js. Type checking happens before JavaScript execution; most type annotations are erased. Use an installed project toolchain, not an unpinned remote script.",
        "syntax": "`let total: number = 0` annotates a changing Number value. `readonly number[]` prevents writes through that typed reference; it does not freeze a runtime array. for...of reads values. TypeScript's number retains JavaScript's binary64 limits. A type annotation does not validate an HTTP response or user input.",
        "code": "let total: number = 0;\nfor (let value = 1; value < 4; ++value) total += value;\nconsole.log(total);\nconst prices: readonly number[] = [4, -2, 1];\nlet balance = 0;\nfor (const price of prices) balance += price;\nconsole.log(balance);\n",
        "bug": "let total: number = 0;\nfor (const value of [1, 2, 3]) {\n  total = 0; // type-correct, but logically wrong\n  total += value;\n}\nconsole.log(total); // 3",
        "fix": "Remove the reset. A compiler checks assignability, not your intended invariant. `as number[]` on unknown data is only an assertion, not conversion or validation. With noUncheckedIndexedAccess, indexed reads may be undefined; a for...of over a validated dense array avoids that indexing issue.",
        "reference": "// A testable function: call positiveTotal([4, -2, 0, 7]) -> 11.\nfunction positiveTotal(values: readonly number[]): number {\n  let total = 0;\n  for (const value of values) {\n    if (value > 0) total += value;\n  }\n  return total;\n}\n",
        "ref": ("TypeScript handbook: narrowing and control flow", "https://www.typescriptlang.org/docs/handbook/2/narrowing.html"),
        "next": "ts-real-world-1", "specific": "Use a typed loop for stateful logic, a typed reduce for a simple aggregation, and runtime validation at untrusted boundaries. strictNullChecks and noUncheckedIndexedAccess strengthen different checks; neither proves that totals satisfy a business rule.",
    },
    "go": {
        "module": "go-decisions-loops", "version": "Go 1.22+", "extension": "go",
        "setup": "Save as lesson.go and run go run lesson.go. For a project, use go mod init example.com/looplab and go test ./.... Go compiles before running; gofmt formats the source. These examples do not require third-party modules.",
        "syntax": "Go uses for for both counting and condition-driven loops. `for _, price := range prices` discards the index and copies each value. Braces are required. int has an implementation-dependent 32- or 64-bit size; use int64 for the bounded challenge total. Integer overflow is defined by Go's integer rules, not an automatic exception. Avoid relying on overflow for business totals.",
        "code": "package main\nimport \"fmt\"\nfunc main() {\n    total := 0\n    for value := 1; value < 4; value++ { total += value }\n    fmt.Println(total)\n    prices := []int{4, -2, 1}\n    balance := 0\n    for _, price := range prices { balance += price }\n    fmt.Println(balance)\n}\n",
        "bug": "total := 0\nfor value := 1; value < 4; value++ {\n    total := 0 // wrong: a new shadowing variable\n    total += value\n    _ = total\n}\n// outer total is still 0",
        "fix": "Delete the inner declaration; update the outer total. `:=` may declare a new variable in an inner scope, unlike `=`. Range copies a struct value too; mutating the copy does not update the slice element. If mutation is required, use the index deliberately. Loop-variable capture rules changed in Go 1.22; do not generalize an older closure example to every version.",
        "reference": "package main\nimport (\"bufio\"; \"fmt\"; \"os\")\nfunc main() {\n    in := bufio.NewReader(os.Stdin)\n    var n int\n    fmt.Fscan(in, &n)\n    var total int64\n    for i := 0; i < n; i++ {\n        var value int64\n        fmt.Fscan(in, &value)\n        if value > 0 { total += value }\n    }\n    fmt.Println(total)\n}\n",
        "ref": ("Go specification: for statements", "https://go.dev/ref/spec#For_statements"),
        "next": "go-real-world-1", "specific": "A range loop is idiomatic for reading slice values. An index loop is useful for updating positions. A nil slice iterates zero times; it is not an error. Keep error handling for input separate from the accumulation rule; the reference assumes the stated well-formed input contract.",
    },
    "rust": {
        "module": "rust-decisions-loops", "version": "Rust 2021 edition", "extension": "rs",
        "setup": "Save as lesson.rs; run rustc --edition=2021 lesson.rs -o lesson, then ./lesson. A larger project uses cargo new and cargo test. Compiler borrow/type errors occur before running; a panic is a runtime event, not a compilation failure.",
        "syntax": "Bindings are immutable unless marked mut. `for value in 1..4` excludes 4; `1..=4` includes it. `for &price in &prices` borrows the array and copies each i32 out of its reference. Integer types have fixed widths except isize/usize. Overflow checks depend on build settings; do not rely on debug and optimized builds failing identically. checked_add makes an overflow policy explicit.",
        "code": "fn main() {\n    let mut total: i32 = 0;\n    for value in 1..4 { total += value; }\n    println!(\"{}\", total);\n    let prices = [4, -2, 1];\n    let mut balance = 0;\n    for &price in &prices { balance += price; }\n    println!(\"{}\", balance);\n}\n",
        "bug": "let mut total = 0;\nfor value in 1..4 {\n    let mut total = 0; // wrong: shadows the outer total\n    total += value;\n    println!(\"{}\", total);\n}\n// outer total remains 0",
        "fix": "Remove the inner let binding, then mutate the original total. Rust permits shadowing, so compilation alone cannot catch this logic bug. Iterating a Vec by value consumes it; use iter() or a borrowed loop when later code needs the Vec. Bounds-checked indexing can panic; safe references do not eliminate all runtime errors.",
        "reference": "use std::io::{self, Read};\nfn main() {\n    let mut input = String::new();\n    io::stdin().read_to_string(&mut input).unwrap();\n    let mut words = input.split_whitespace();\n    let n: usize = words.next().unwrap().parse().unwrap();\n    let mut total: i64 = 0;\n    for _ in 0..n {\n        let value: i64 = words.next().unwrap().parse().unwrap();\n        if value > 0 { total += value; }\n    }\n    println!(\"{}\", total);\n}\n",
        "ref": ("Rust book: control flow", "https://doc.rust-lang.org/book/ch03-05-control-flow.html"),
        "next": "rust-real-world-1", "specific": "Iterator filter and sum can express the same reduction without mutable state in user code. A borrowed iterator avoids consuming the collection. The challenge reference uses unwrap only under its valid-input contract; a public CLI should return a Result and explain malformed input instead of panicking.",
    },
}

SUM_TESTS = [
    {"input": "0\n", "expected": "0\n", "reason": "empty input collection"},
    {"input": "3\n-4 0 -9\n", "expected": "0\n", "reason": "no positive values"},
    {"input": "4\n-2 0 5 7\n", "expected": "12\n", "reason": "mixed signs and zero"},
    {"input": "1\n9\n", "expected": "9\n", "reason": "single value"},
    {"input": "4\n3 3 -1 3\n", "expected": "9\n", "reason": "duplicates are not removed"},
    {"input": "1000\n" + "1000000 " * 1000 + "\n", "expected": "1000000000\n", "reason": "largest allowed total"},
]


def loop_unit(language: str, p: dict) -> dict:
    return {
        "schema_version": 1, "language": language, "version": p["version"],
        "minutes": 35, "level": 2, "prerequisites": [],
        "prerequisite_text": "Before this unit, run the language's Hello World module and practice variables, addition and a boolean comparison. Review those modules in the course index if needed.",
        "setup": p["setup"], "kind": "loop",
        "objectives": "Trace an accumulator without running it; distinguish initialization, condition and update; explain why an empty loop leaves the initial total unchanged; implement and test a filtered total without losing earlier work.",
        "intuition": "Imagine a basket with a running receipt. Each item changes the total once. The total is a summary of everything already processed, not just the most recent item. The analogy stops at machine arithmetic: programs use precisely defined numeric types, not unlimited real-world amounts. Here amounts are integer units, not floating-point currency.",
        "technical": "A loop repeats a body while moving toward termination. The accumulator starts at the identity for addition, zero. Our invariant is: after k iterations, total equals the sum of the first k values. It holds initially because the empty sum is zero. Adding the next value preserves it. After all n values, k = n, so the total is the required sum. A bounded counter advances on every iteration and eventually reaches n; this is the termination argument, separate from the invariant. No input is changed.",
        "visual": "Read the trace as a state table. Each row shows state *after* processing one value. The initial row matters: a collection with zero items must still have a result.",
        "syntax": p["syntax"],
        "examples": "The first half is the smallest useful counting loop; it prints 6. The second half models signed basket adjustments (a refund is negative); it prints 3. Initialization happens once, the addition happens for each value, and printing happens after the loop. These examples deliberately use small values so arithmetic range does not hide the control-flow lesson.",
        "code_examples": [{"label": "Minimal and everyday examples", "code": p["code"], "expected": "6\n3\n"}, {"label": "Deliberate logic bug — predict before running", "code": p["bug"], "expected": None}],
        "trace": [{"step": "initial", "value": "—", "state": "0"}, {"step": "1", "value": "4", "state": "4"}, {"step": "2", "value": "-2", "state": "2"}, {"step": "3", "value": "1", "state": "3"}],
        "walkthrough": "Start balance at 0. Read 4: balance becomes 4. Read -2: balance becomes 2; subtracting a refund is not skipping it. Read 1: balance becomes 3. Stop after exactly three values. Resetting balance inside the body would keep only the last value. Moving the print into the loop produces three partial totals rather than the one requested final result. Step through the table and say which prefix each state summarizes.",
        "applications": "Use an accumulator for sensor readings, inventory adjustments or a count of successful requests. For real money choose an explicit integer minor-unit or decimal policy, rounding and overflow checks. For unbounded streams, a rolling total can avoid retaining all records, but you must define cancellation, invalid input and recovery. Do not replace an accounting database with an unchecked in-memory counter.",
        "mistakes": p["fix"],
        "alternatives": p["specific"] + " A while loop can express the same operation but makes advancing the cursor your responsibility. Recursion needs a base case and usually adds call-stack space for this simple linear task. Choose a loop or fold unless recursion reflects the structure of the problem.",
        "check": "For [4, -2, 1], what does balance mean immediately before processing 1? Is a nested loop necessary to total n items? Explain why the initial value must be zero when n = 0.",
        "check_answer": "It is 2, the sum of the first two values, not the count of iterations or the current item. Only one traversal is needed. The empty sum is zero; starting at the first element would require a separate empty-input case. If you answered 3 before the last addition, you used the final state one step too early.",
        "guided": "Write a loop that counts strictly negative adjustments instead of summing them. Input: a collection of n integers, 0 ≤ n ≤ 1000, each between -1,000,000 and 1,000,000. Output one integer count. For [4, -2, 0, -1], output 2; for [], output 0. Do not count zero. State the invariant before coding.",
        "guided_hints": ["What is the count before reading any item?", "Use one condition per item: value < 0. Increment the count only when it holds.", "After k items, count equals the number of negative items in that prefix. Test [], [0], [-1], and [1, -1, -1]."],
        "challenge": "**Positive adjustments only.** Compute the sum of strictly positive values, preserving duplicates. Unlike the signed total example, negative values must not reduce the answer.\n\n**Input:** an integer n (0 ≤ n ≤ 1000), followed by exactly n integers in [-1,000,000, 1,000,000], separated by whitespace. Input is well-formed. **Output:** one integer and a newline. For TypeScript, implement positiveTotal(values: readonly number[]): number instead of stdin parsing; the same collection constraints apply.\n\n**Sample:** input `4` followed by `-2 0 5 7`; output `12`. For n = 0 output `0`. Test all-negative input, zero, one element, duplicates and the maximum total 1,000,000,000. A public application would additionally reject malformed input; that is outside this exercise's valid-input contract.\n\n**Target:** Θ(n) time and O(1) auxiliary accumulator space, excluding input storage/parsing. Reading the whole input into an array uses O(n) additional storage. Sorting first would add unnecessary work; enumerating subsets solves a different problem.",
        "challenge_hints": ["How does the new specification differ from summing every signed adjustment?", "Keep the same invariant, but summarize only positive values in the processed prefix.", "Do not reset total when you meet a negative value; leave the previously accumulated state unchanged."],
        "reference": p["reference"],
        "solution_explanation": "Initialize total to zero; for each value, add it only if it is strictly greater than zero. After k items total is exactly the sum of positive values in that prefix. The update preserves this invariant whether the next value is positive or not. At termination the prefix is the whole input. Every item can change the result, so in the worst case any correct algorithm must inspect all n items. The loop is Θ(n) under bounded-width arithmetic (also valid for these bounded Python integers), with O(1) accumulator storage. Some reference parsers hold all tokens: their total space is O(n), not O(1).",
        "test_strategy": "Coverage categories, not secret online tests: empty, all nonpositive, mixed signs, singleton, repeated positives and maximum allowed total. A sum-all implementation fails the mixed-sign case. A last-positive-only implementation fails repeated positives. A deduplicating set fails duplicates. There is no hidden-test service on this page: run your program locally and compare these expected outputs.",
        "tests": SUM_TESTS,
        "mastery": "Before continuing: (1) answer the conceptual question without looking; (2) run your guided and independent code on empty, boundary and mixed-sign cases; (3) write a two-sentence invariant/termination argument; (4) explain your numeric range and input-storage cost. A self-report is not machine-graded mastery. If any part is uncertain, review the trace, repair the code and retry. Existing stage quizzes provide separate account-backed conceptual feedback.",
        "further": "Build a small daily-adjustment report with signed total, positive total and negative count. Specify how invalid input is rejected; keep I/O separate from calculation so tests can call a function. Then study collections and functions in the next modules. Only add running averages after deciding the empty-input result and rounding policy.",
        "next_slug": p["next"],
        "references": [{"title": p["ref"][0], "url": p["ref"][1]}],
        "review": "Authored 2026-10-15; runtime verification is reported separately by scripts/verify_academy.py. References are reading pointers, not a claim of live network review or expert sign-off.",
    }


UNITS = {p["module"]: loop_unit(language, p) for language, p in PROFILES.items()}

UNITS['csharp-decisions-loops']['next_slug'] = 'csharp-methods-arrays'
_PREREQUISITES = {
    'python': ['python-hello-setup', 'python-operators'],
    'c': ['c-hello', 'c-operators'],
    'cpp': ['cpp-hello', 'cpp-variables-operators'],
    'java': ['java-hello', 'java-operators'],
    'csharp': ['csharp-hello', 'csharp-variables-operators'],
    'javascript': ['js-hello', 'js-operators'],
    'typescript': ['ts-hello'],
    'go': ['go-hello', 'go-variables-operators'],
    'rust': ['rust-hello', 'rust-variables-operators'],
}
for _language, _profile in PROFILES.items():
    UNITS[_profile['module']]['prerequisites'] = _PREREQUISITES[_language]


SQL_EXAMPLE = """CREATE TABLE adjustments (id INTEGER PRIMARY KEY, amount INTEGER NOT NULL);
INSERT INTO adjustments VALUES (1, 4), (2, -2), (3, 1);
SELECT COALESCE(SUM(amount), 0) AS balance FROM adjustments;
"""
SQL_REFERENCE = """CREATE TABLE adjustments (id INTEGER PRIMARY KEY, amount INTEGER NOT NULL);
INSERT INTO adjustments VALUES (1, -2), (2, 0), (3, 5), (4, 7);
SELECT COALESCE(SUM(amount), 0) AS positive_total
FROM adjustments WHERE amount > 0;
"""
UNITS['sql-real-world-1'] = {
    'schema_version': 1, 'language': 'sql', 'version': 'SQLite 3.37+ (SQL dialect explicitly scoped)',
    'minutes': 40, 'level': 2, 'kind': 'sql', 'prerequisites': ['sql-hello'],
    'prerequisite_text': 'Read Tables, rows and a first SELECT. Understand rows, columns, integer literals and a WHERE predicate.',
    'setup': 'Use a disposable SQLite database with the sqlite3 command-line tool, or Python’s sqlite3 module. Paste the example into a new database. CREATE/INSERT change data; do not run these statements against the EngineVerse application database. This page does not execute SQL.',
    'objectives': 'Distinguish row filtering from aggregation; predict SUM on empty data; preserve duplicates when totaling records; write a conditional report with explicit NULL and numeric-range policies.',
    'intuition': 'A report summarizes a bag of records. WHERE first chooses which records qualify; SUM then combines their amounts. SQL is declarative: you describe the result, not the iteration order. A receipt analogy is useful, but a SQL table has no guaranteed row order without ORDER BY, and SQL has NULL rather than only ordinary numbers.',
    'technical': 'WHERE retains rows whose condition is TRUE, not FALSE or UNKNOWN. SUM ignores NULL inputs and returns NULL if there are no non-NULL inputs. COALESCE replaces that NULL result with zero under this report’s empty-total policy. Duplicates remain separate input rows unless you explicitly request DISTINCT. The amount column is NOT NULL here, so missing amounts cannot silently disappear. The database chooses a physical execution plan; the query text is not a prescribed loop.',
    'visual': 'Think in two intermediate relations: qualifying rows, then a one-row aggregate result. The trace is a conceptual explanation, not a promise about SQLite’s physical row order.',
    'syntax': '`SELECT COALESCE(SUM(amount), 0) FROM adjustments WHERE amount > 0;` returns one aggregate row, even for empty input. Use WHERE for input rows and HAVING for filtering groups. SQLite permits some permissive typing; adding a declared INTEGER type alone is not a general validation boundary. SQLite integer SUM can raise an overflow error if its integer accumulator exceeds signed 64-bit range. Other databases have different aggregate result types.',
    'examples': 'The complete example creates three non-NULL adjustments and prints 3. SUM combines 4, -2 and 1. COALESCE defines the empty result. A table does not need GROUP BY when the whole filtered input is one aggregate group. For reports per account, GROUP BY account_id would create independent totals, and your access policy must filter to authorized accounts.',
    'code_examples': [{'label': 'A complete signed-adjustment report', 'code': SQL_EXAMPLE, 'expected': '3\n'}, {'label': 'Incorrect duplicate removal', 'code': 'SELECT SUM(DISTINCT amount) FROM adjustments;\n-- For amounts 5, 5 this returns 5, not 10.', 'expected': None}],
    'trace': [{'step': 'source rows', 'value': '-2, 0, 5, 7', 'state': '4 records'}, {'step': 'WHERE amount > 0', 'value': '5, 7', 'state': '2 qualifying records'}, {'step': 'SUM', 'value': '5 + 7', 'state': '12'}, {'step': 'COALESCE', 'value': 'not NULL', 'state': '12'}],
    'walkthrough': 'For the independent problem, -2 and 0 do not satisfy amount > 0. Values 5 and 7 do, so SUM returns 12. With only -2 and 0, no row qualifies; SUM returns NULL; COALESCE returns 0. If two qualifying rows both have value 5, SUM counts both and returns 10. Their distinct primary keys identify separate records even when amounts are equal.',
    'applications': 'Use aggregate queries for bounded reconciliation reports and inventory summaries. Define whether missing data means unknown or zero before using COALESCE. Use transactions and a suitable isolation policy when a report must agree with concurrent updates. Never concatenate user-supplied account names into SQL; bind parameters and enforce authorization separately.',
    'mistakes': 'SUM(DISTINCT amount) incorrectly drops legitimate repeated amounts. Correct it to SUM(amount). Selecting an arbitrary id beside SUM without grouping is not a portable meaningful record identifier. A LEFT JOIN can multiply rows and inflate totals: first verify join cardinality, or aggregate each side before joining. An index is not a correctness fix for a duplicated join.',
    'alternatives': 'WHERE amount > 0 excludes nonpositive rows before aggregation. SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) is useful when producing several conditional totals in one scan. SUM(amount) FILTER (WHERE amount > 0) is another form supported by modern SQLite, but not all dialects. All need an explicit empty-input policy. Fetching all rows into application code adds transfer cost and is usually unnecessary for this report.',
    'check': 'For two records of amount 5 and one record of amount -2, is SUM(DISTINCT amount) a valid signed balance? What is SUM(amount) over zero rows before COALESCE?',
    'check_answer': 'No. SUM(DISTINCT amount) returns 3, but the signed balance is 8 because both records of amount 5 count. Over zero rows SUM returns NULL, not zero. COALESCE is a report policy applied after aggregation, not a change to the underlying data.',
    'guided': 'Count negative records in adjustments. Return one integer named negative_count; do not count zero. For amounts 4, -2, 0, -1 return 2. For an empty table return 0. Use COUNT(*) with an input filter; do not use COUNT(amount < 0), which counts non-NULL boolean expression results including false.',
    'guided_hints': ['Filter input rows before counting.', 'COUNT(*) counts records; WHERE amount < 0 chooses negative records.', 'SELECT COUNT(*) AS negative_count FROM adjustments WHERE amount < 0; returns zero for an empty filtered relation.'],
    'challenge': '**Positive adjustments report.** Given adjustments(id INTEGER PRIMARY KEY, amount INTEGER NOT NULL), return exactly one row and one column named positive_total, containing the sum of strictly positive amounts or 0 when none qualify. There are 0–1000 rows; every amount is an integer between -1,000,000 and 1,000,000. Preserve duplicates. For amounts -2, 0, 5, 7 return 12. Do not create or alter tables in your answer query.\n\nUnder a full-table scan plan, time is Θ(n) in the number of records, with constant aggregate state; physical storage, indexes and engine workspace are outside that simplified model. Inspect EXPLAIN QUERY PLAN before making performance claims. An index may change how qualifying rows are read; it does not magically make SUM over many matches O(1).',
    'challenge_hints': ['Separate row qualification from the aggregate.', 'Use amount > 0, not >= 0. Consider what SUM does for an empty relation.', 'Apply COALESCE around SUM, not only around each input value.'],
    'reference': SQL_REFERENCE,
    'solution_explanation': 'The fixture demonstrates the schema and sample; the answer is only the SELECT statement. WHERE selects precisely the positive records, SUM includes each selected record once, and COALESCE implements the required zero result for no matches. NOT NULL and the bounded integer inputs eliminate missing-value and overflow ambiguity for this exercise. A proof follows directly from the selected relation and SUM’s contract, without assuming a physical iteration order.',
    'tests': [{'input': 'amounts: []', 'expected': '0', 'reason': 'empty'}, {'input': 'amounts: [-2, 0, 5, 7]', 'expected': '12', 'reason': 'mixed'}, {'input': 'amounts: [5, 5]', 'expected': '10', 'reason': 'duplicates'}, {'input': 'amounts: [-5, 0]', 'expected': '0', 'reason': 'no positives'}],
    'test_strategy': 'Run the SELECT against independently created empty, mixed, duplicate and nonpositive fixtures. A SUM-all query fails mixed signs; DISTINCT fails duplicates; missing COALESCE fails the empty fixture. These are disclosed coverage categories, not a claim of a hidden judging service.',
    'mastery': 'Explain WHERE versus HAVING, predict the empty aggregate, and demonstrate correct output for all four fixtures. Then explain how a one-to-many join could corrupt the report. If you cannot justify a step, rebuild the tiny table and inspect the qualifying records before aggregating. This is self-review, not an automatically graded SQL assessment.',
    'further': 'Build a report with one row per account, negative_count and positive_total. Specify whether accounts with no adjustments appear. Learn GROUP BY, joins and transaction isolation next; add parameterized filters and authorization before putting it behind an API.',
    'next_slug': None,
    'references': [{'title': 'SQLite aggregate function contracts', 'url': 'https://www.sqlite.org/lang_aggfunc.html'}, {'title': 'SQLite SELECT processing', 'url': 'https://www.sqlite.org/lang_select.html'}],
    'review': 'Authored 2026-10-15; SQLite examples checked by the trusted-source verifier. Official links are reading pointers; live reference fetching was unavailable in this environment.',
}

BOUND_CODE = {
    'python': ('length = 8\nsteps = 0\nwhile length > 1:\n    length //= 2\n    steps += 1\nprint(steps)\n', '''def lower_bound(values, target):
    lo, hi = 0, len(values)
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if values[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    return lo

print(lower_bound([1, 3, 3, 9], 8))
print(lower_bound([], 8))
'''),
    'c': ('''#include <stdio.h>
int main(void) {
    int length = 8, steps = 0;
    while (length > 1) { length /= 2; ++steps; }
    printf("%d\\n", steps);
    return 0;
}
''', '''#include <stddef.h>
#include <stdio.h>
size_t lower_bound(const int *values, size_t n, int target) {
    size_t lo = 0, hi = n;
    while (lo < hi) {
        size_t mid = lo + (hi - lo) / 2;
        if (values[mid] < target) lo = mid + 1;
        else hi = mid;
    }
    return lo;
}
int main(void) {
    const int values[] = {1, 3, 3, 9};
    printf("%zu\\n", lower_bound(values, 4, 8));
    printf("%zu\\n", lower_bound(NULL, 0, 8));
    return 0;
}
'''),
    'cpp': ('''#include <iostream>
int main() {
    int length = 8, steps = 0;
    while (length > 1) { length /= 2; ++steps; }
    std::cout << steps << '\\n';
}
''', '''#include <iostream>
#include <vector>
#include <cstddef>
std::size_t lower_bound_index(const std::vector<int>& values, int target) {
    std::size_t lo = 0, hi = values.size();
    while (lo < hi) {
        std::size_t mid = lo + (hi - lo) / 2;
        if (values[mid] < target) lo = mid + 1;
        else hi = mid;
    }
    return lo;
}
int main() {
    std::cout << lower_bound_index({1, 3, 3, 9}, 8) << '\\n';
    std::cout << lower_bound_index({}, 8) << '\\n';
}
'''),
    'java': ('''public class Main {
    public static void main(String[] args) {
        int length = 8, steps = 0;
        while (length > 1) { length /= 2; ++steps; }
        System.out.println(steps);
    }
}
''', '''public class Main {
    static int lowerBound(int[] values, int target) {
        int lo = 0, hi = values.length;
        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (values[mid] < target) lo = mid + 1;
            else hi = mid;
        }
        return lo;
    }
    public static void main(String[] args) {
        System.out.println(lowerBound(new int[]{1, 3, 3, 9}, 8));
        System.out.println(lowerBound(new int[]{}, 8));
    }
}
'''),
    'csharp': ('''using System;
int length = 8, steps = 0;
while (length > 1) { length /= 2; ++steps; }
Console.WriteLine(steps);
''', '''using System;
static int LowerBound(int[] values, int target) {
    int lo = 0, hi = values.Length;
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (values[mid] < target) lo = mid + 1;
        else hi = mid;
    }
    return lo;
}
Console.WriteLine(LowerBound(new int[]{1, 3, 3, 9}, 8));
Console.WriteLine(LowerBound(Array.Empty<int>(), 8));
'''),
}

BOUND_SPECIFICS = {
    'python': 'A list provides constant-time indexing in the usual Python implementation model; slicing makes a copy, so binary search by values[:mid] adds allocation/copy costs. Use indices rather than slicing. Python integers avoid fixed-width overflow, but their operations are not constant cost for unbounded bit lengths. bisect_left is the library alternative for sorted sequences.',
    'c': 'For this bounded-array challenge, target a hosted implementation with int able to represent ±1,000,000 and size_t able to represent 100,000; C17 alone does not guarantee those widths. Inspect limits.h and stdint.h on a smaller target and adjust types/contracts. Pointer indexing requires a valid object and an explicit length. This API allows NULL only when n is zero, because no element is then accessed. size_t is unsigned: avoid n - 1 for an empty array. lo + (hi - lo) / 2 avoids overflow of lo + hi when lo ≤ hi. bsearch finds an equal element, not necessarily the first duplicate or an insertion point.',
    'cpp': 'Use a const reference so searching does not copy the vector. std::lower_bound is normally preferable to handwritten binary search. Its comparison count is logarithmic, but on non-random-access iterators traversal can take linear iterator increments. Do not infer logarithmic elapsed work for a linked list from comparison count alone.',
    'java': 'int[] has constant-time indexing in the cost model and an int length. lo + (hi - lo) / 2 avoids overflowing lo + hi. Arrays.binarySearch returns an equal match or an encoded insertion point; it does not guarantee the first equal duplicate. A linked List may not support O(1) get(mid), so the container matters.',
    'csharp': 'int[] provides direct indexed access. Avoid LINQ Skip/Take materialization inside the loop: it changes the space and work model. Array.BinarySearch may return any equal duplicate or a complemented insertion index, not the first equal position. Overflow checking can vary by configuration; the difference-based midpoint is safe for valid array bounds.',
}

for _language, (_example, _reference) in BOUND_CODE.items():
    _p = PROFILES[_language]
    _slug = f'{_language}-complexity-big-o'
    UNITS[_slug] = {
        'schema_version': 1, 'language': _language, 'version': _p['version'],
        'minutes': 50, 'level': 3, 'kind': 'bounds',
        'prerequisites': [_p['module']],
        'prerequisite_text': 'Trace a loop, read a sorted array, and understand integer division before starting. Return to the accumulator unit if loop state is still unclear.',
        'setup': _p['setup'],
        'objectives': 'Define O, Ω and Θ without confusing bounds with best/worst cases; choose an input size and cost model; prove a half-open binary-search invariant; distinguish comparison count from total runtime and auxiliary space.',
        'intuition': 'Doubling the number of records does not necessarily double every algorithm’s work. Scanning touches each record; repeatedly halving a sorted search interval needs about one extra decision after doubling. This is a growth comparison, not a claim that binary search is faster on every tiny input. Sorting and data access may cost more than the search itself.',
        'technical': 'For eventually nonnegative functions f and g, f ∈ O(g) means f(n) ≤ c·g(n) for all n ≥ n₀ and some c > 0. Ω reverses the inequality; Θ means both bounds hold. These symbols do NOT choose worst, average or best case: define the cost function first. A full scan can be Θ(n) in every case; an early-exit search can be Θ(1) best case and Θ(n) worst case. A linear function is also O(n²), but Θ(n) is tighter. Average-case analysis requires an input distribution; amortized analysis bounds a sequence of operations and is not an average over random inputs. Here n is array length, comparisons/indexing of bounded integers cost O(1), and input loading is counted separately.',
        'visual': 'For the insertion-point example, the interval is [lo, hi). The trace tracks which indices remain possible, not a shrinking copied array. hi = n is a valid boundary but never an array element to read.',
        'syntax': BOUND_SPECIFICS[_language],
        'examples': 'The minimal program starts length at 8 and repeatedly divides by 2, printing 3 iterations. For powers of two this count is log₂(n); for other positive lengths integer division changes rounding, not logarithmic growth. This program models interval shrinkage only; it does not read an array or prove sortedness. The reference below turns the idea into a real insertion-point search.',
        'code_examples': [{'label': 'Minimal halving experiment', 'code': _example, 'expected': '3\n'}, {'label': 'Incorrect update, expressed as pseudocode', 'code': 'while lo < hi:\n    mid = lo + (hi - lo) // 2\n    if values[mid] < target:\n        lo = mid  # wrong: may not advance\n    else:\n        hi = mid', 'expected': None}],
        'trace': [{'step': 'initial', 'value': '[1, 3, 3, 9], target 8', 'state': 'lo=0 hi=4'}, {'step': '1', 'value': 'mid=2, 3 < 8', 'state': 'lo=3 hi=4'}, {'step': '2', 'value': 'mid=3, 9 ≥ 8', 'state': 'lo=3 hi=3'}, {'step': 'stop', 'value': 'insertion index', 'state': '3'}],
        'walkthrough': 'Maintain: every element before lo is < target; every element at or after hi is ≥ target. Both claims are vacuous at lo=0, hi=n. If a[mid] < target, sortedness puts every earlier element below target too, so set lo=mid+1. Otherwise a[mid] and every later element qualify, so set hi=mid. The interval length strictly decreases. When lo=hi the boundary is the first qualifying index, or n if none exists. The argument handles duplicates and empty arrays without a separate element access.',
        'applications': 'Insertion points support sorted indexes, threshold reports and version lookups. Use binary search only when the predicate is monotone or the collection is sorted by the same ordering. If each predicate calls a remote service, include that cost. For one query on unsorted data, a linear scan may beat paying Θ(n log n) to sort; sorting can also destroy meaningful original positions.',
        'mistakes': 'Setting lo=mid can loop forever on an interval of length one. Correct it to lo=mid+1 on the strictly-below branch. Setting hi=mid-1 mixes inclusive and half-open conventions and may lose the first qualifying position. Test length 0, length 1 and all equal elements before random data. Never benchmark a nonterminating version with an unbounded run.',
        'alternatives': 'A linear insertion-point scan costs Θ(n) worst-case time, uses O(1) auxiliary space and needs fewer indexing assumptions. Binary search uses O(log(n+1)) comparisons and O(1) auxiliary space on an indexed array. For a general container the per-access cost must be included. Recursive search can use O(log n) stack frames without tail-call guarantees. Standard library search avoids custom boundary bugs when its duplicate and insertion contracts match yours.',
        'check': 'Does O(n) mean worst case? Is 3n + 7 in O(n²)? Can binary search be claimed logarithmic if indexing is itself linear?',
        'check_answer': 'No: O denotes an asymptotic upper bound on whichever cost function you defined. Yes, 3n+7 is O(n²), although Θ(n) is tighter. Logarithmic comparisons do not guarantee logarithmic total work when access costs grow with n. Calling Ω “best case” would make the same case-selection mistake in reverse.',
        'guided': 'Instrument the halving example with lengths 1, 2, 4, 8 and 16. Predict iteration counts 0, 1, 2, 3 and 4. Then count operations for a full linear scan of those lengths. Explain why the scan is Θ(n), not merely O(n²), under the stated cost model. Do not use elapsed nanoseconds as a mathematical proof.',
        'guided_hints': ['Write the length after each integer division.', 'An upper bound alone is insufficient for Θ; give a lower bound too.', 'A full scan performs n visits, giving both an n upper and lower bound up to fixed overhead.'],
        'challenge': '**First qualifying position.** Implement lower_bound(values, target), named lower_bound_index in C++, lowerBound in Java and LowerBound in C#. C additionally receives the array length n. Return the smallest index i with values[i] ≥ target, or n if no such element exists.\n\nInput is a nondecreasing integer array with 0–100,000 elements and a target; each integer is in [-1,000,000, 1,000,000]. Return an index, not a boolean. Do not mutate or copy the array. [1,3,3,9] with target 8 returns 3; target 3 returns 1; [] returns 0.\n\nTarget O(log(n+1)) time and O(1) auxiliary space with constant-cost indexing. Explain why sortedness is a prerequisite and why duplicate values do not invalidate the proof. The complete reference programs demonstrate two calls; adapt their main function to run the remaining cases locally.',
        'challenge_hints': ['Use a boundary interval [0, n), not element indices [0, n-1].', 'What can be ruled out when values[mid] < target? What remains possible when it equals target?', 'Equality must move hi left, not immediately return mid, to find the first duplicate.'],
        'reference': _reference,
        'solution_explanation': 'The reference is a complete runnable program including the function and two sample calls; it prints 3 then 0. Its loop is exactly the invariant-preserving algorithm in the walkthrough. Each iteration reduces the candidate interval by approximately half; at most O(log(n+1)) iterations occur, with a constant number of bounded operations per iteration. Only lo, hi and mid are stored. Verification fixtures include duplicates, no match, both extremes, empty input and singleton inputs; a correct midpoint formula alone is not a proof of correct boundaries.',
        'tests': [{'input': '[], target 8', 'expected': '0', 'reason': 'empty'}, {'input': '[1], target 2', 'expected': '1', 'reason': 'none qualifies'}, {'input': '[1], target 0', 'expected': '0', 'reason': 'first qualifies'}, {'input': '[1,3,3,9], target 3', 'expected': '1', 'reason': 'first duplicate'}, {'input': '[1,3,3,9], target 8', 'expected': '3', 'reason': 'gap'}, {'input': '[1,3,3,9], target 10', 'expected': '4', 'reason': 'past end'}],
        'test_strategy': 'Use the disclosed cases, then compare many small sorted arrays against a simple linear oracle. A return-on-equality implementation fails the first-duplicate test. lo=mid may hang on singleton input. Reject unsupported unsorted-input claims rather than silently sorting and changing indices. This page itself does not execute hidden tests.',
        'mastery': 'Pass all cases locally; state the invariant, strict-decrease termination measure and cost model; classify an early-exit scan’s best and worst cost functions separately using Θ. If you cannot explain an empty interval, retry with the trace before proceeding. This self-review does not write a graded mastery score.',
        'further': 'Extend to an upper bound (first element strictly greater than target), then count equal elements as upper minus lower. Try a monotone feasibility predicate in a scheduling problem; prove monotonicity before applying binary search. Study prefix sums, hashing and amortized dynamic-array growth next.',
        'next_slug': None,
        'references': [{'title': _p['ref'][0], 'url': _p['ref'][1]}, {'title': 'MIT 6.006: course notes and asymptotic analysis materials', 'url': 'https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/pages/lecture-notes/'}],
        'review': 'Authored 2026-10-15. Bounds follow the declared array/word-cost model, not measured benchmarks. Compiler availability and execution results are reported by the verifier; references are not claimed to have been fetched live.',
    }

def searchable_body(unit: dict) -> str:
    """Plain authored sections also remain searchable through the existing index."""
    return '\n\n'.join(f'## {title}\n\n{unit[key]}' for key, title in SECTION_TITLES)


def validate_catalogue(modules_by_language: dict[str, list[str]]) -> None:
    for slug, unit in UNITS.items():
        validate_unit(unit)
        known = modules_by_language.get(unit['language'], [])
        if slug not in known:
            raise ValueError(f'academy unit points to absent module: {slug}')
        for target in [*unit['prerequisites'], unit.get('next_slug')]:
            if target and (target not in known or target == slug):
                raise ValueError(f'invalid academy navigation: {slug} -> {target}')
    # Prerequisite edges must form a DAG; legacy prerequisites are leaves.
    visiting, visited = set(), set()
    def visit(slug):
        if slug in visiting:
            raise ValueError(f'cyclic academy prerequisite: {slug}')
        if slug in visited or slug not in UNITS:
            return
        visiting.add(slug)
        for target in UNITS[slug]['prerequisites']:
            visit(target)
        visiting.remove(slug)
        visited.add(slug)
    for slug in UNITS:
        visit(slug)

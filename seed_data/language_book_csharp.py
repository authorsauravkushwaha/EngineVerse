"""Complete C# path: scratch-first foundations plus book-depth DSA and mastery.

C# is the enterprise and Unity/game-development workhorse: statically typed,
garbage-collected, with LINQ, async/await and a superb standard library. This
file carries the whole path — why/hello/variables/decisions/methods/strings/
drills/complexity (foundations), OOP/collections/errors/recursion/stacks
(working practice), trees/graphs/DP/async-services/mastery (advanced).

Each module ends with a runnable example and one judged problem to code.
"""

from __future__ import annotations

BOOK_MODULES: dict[str, list[tuple]] = {
    "csharp": [
        (
            "csharp-why",
            "Why C# exists",
            "Type-safe productivity for apps, games, services and tools.",
            """**Why this matters.** C# is Microsoft's general-purpose language:
desktop apps, ASP.NET Core services, Unity games, mobile (MAUI), and
scripting/tools. It blends Java-like OOP with modern functional touches
(LINQ, pattern matching, records) and first-class async. Learning C#
teaches static typing, managed memory and framework-scale thinking —
skills that transfer to Java, Kotlin and TypeScript.

**Where it is used.** Enterprise backends (ASP.NET Core is fast and
cross-platform), Unity (most mobile games), Windows apps, cloud services
on Azure, and interview rooms at Microsoft/Amazon (many allow C#).
`dotnet` runs on Linux/macOS/Windows — C# has been cross-platform since
.NET Core.

**What it is not.** Not the systems language (no manual memory; kernels
and drivers stay C/C++/Rust). Not the data-science default (Python).
The GC pauses (usually milliseconds, tunable) rule out hard real-time.

**The professional shape.** Nullable reference types on (`<Nullable>
enable</Nullable>`), warnings as errors, `dotnet test` green, async
all the way down (never `.Result` on a hot path — deadlocks), LINQ for
queries, records for data. A C# hire is expected to know the BCL
(collections, IO, HTTP) more than the syntax.

**Your first run.** `dotnet new console -n Hello` then `dotnet run`.
Top-level statements (no `Main` boilerplate since C# 9) keep day one
to a single `Console.WriteLine`. The tooling — SDK, NuGet, VS Code +
C# Dev Kit — is the smoothest in the industry; use it.""",
            """// Program.cs — top-level statements, no boilerplate.
Console.WriteLine("Hello, EngineVerse");
Console.WriteLine($"2 + 2 = {2 + 2}");
Console.WriteLine($"Year: {2026}");""",
            """Create a console app, print your name and today's date, and run
it with `dotnet run`. Then solve the judged warm-up `fizzbuzz`.
Practice: /practice/problems/fizzbuzz""",
        ),
        (
            "csharp-hello",
            "Hello World: SDK, projects and how it runs",
            "`dotnet new`, `dotnet run`, and what the CLR does with your code.",
            """**Why this matters.** C# never runs as source: it compiles to IL
(intermediate language), then the CLR JITs it to machine code at runtime
— with a garbage collector, type safety and exceptions. Understanding
the pipeline (source → assembly → JIT → GC) explains the tooling and
the error messages you will live with.

**Projects and SDK.** `dotnet new console` scaffolds a `.csproj` (SDK-
style: target framework, nullable, LangVersion) and `Program.cs`.
`dotnet build` compiles; `dotnet run` builds + runs; `dotnet test`
runs xUnit/NUnit/MSTest; `dotnet publish` ships self-contained. NuGet
(`dotnet add package X`) is the library feed. `global.json` pins SDKs
for teams. Learn these five commands before any syntax.

**Top-level statements.** `Console.WriteLine("hi");` at file scope is a
complete program (C# 9+); the compiler generates `Main` for you. Add a
second file with `static` helpers or full `class Program { static void
Main() }` when you outgrow it — both styles coexist. `using System;`
is implicit now (ImplicitUsings) — know it exists when reading old code.

**Types from day one.** `var` infers statically (`var x = 3;` is int —
hover to see; it is NOT dynamic). `Console.ReadLine()` returns
`string?` (nullable!) — check for null. Format with interpolation
(`$"..."`), never `+` in loops (same quadratic rule — `StringBuilder`
for building).

**Common mistakes.** Editing without saving before `dotnet run` (it
builds disk state); targeting the wrong framework (`net8.0` vs `net9.0`
— match installed SDK: `dotnet --list-sdks`); ignoring nullable warnings
(they ARE the bug reports — fix, do not suppress); committing
`bin/`/`obj/` (gitignore them).

**Interview angle.** "Compiled to IL, JITed by the CLR, memory managed
by a generational GC" — one sentence that answers "how does C# run?"
Then write code; the SDK handles the rest.""",
            """// Days until graduation, with input and interpolation.
Console.Write("Graduation year: ");
string? raw = Console.ReadLine();
if (int.TryParse(raw, out int year))
{
    Console.WriteLine($"Hello! {year - 2026} year(s) to go.");
}
else
{
    Console.WriteLine("That was not a number.");
}""",
            """Read two numbers and print their sum, product and average
(double). Validate with TryParse. Then solve the judged drill
`drill-times-table` (print a times table).
Practice: /practice/problems/drill-times-table""",
        ),
        (
            "csharp-variables-operators",
            "Variables, types and operators",
            "Value vs reference types, and the operators you will use daily.",
            """**Why this matters.** C# splits the world in two: value types
(structs: int, double, bool, char, DateTime — copied on assignment,
live on stack/inline) and reference types (classes, strings, arrays —
a reference copied, one shared object). Half of all C# bugs are
expecting value semantics from a reference (or vice versa). Learn the
split now.

**The types.** `int` (32-bit), `long`, `double` (binary float — money
uses `decimal`!), `bool`, `char` (UTF-16 unit), `string` (immutable
reference). `var` infers (still static). Literals: `1_000_000`, `3.14`,
`'A'`, `"text"`, `$"interp {x}"`, `@”verbatim”`. Conversions: implicit
widening (int→long→double), explicit cast `(int)3.9` (truncates!),
`Convert`, `Parse`/`TryParse` (TryParse never throws — the professional
default for input).

**Operators.** Arithmetic `+ - * / %` (`/` on ints truncates: `7/2==3`
— cast for fractions). `++`/`--`, compound `+=`. Comparison `== != < >
<= >=` (works on strings by value!). Logical `&& || !` (short-circuit)
vs bitwise `& | ^ ~ << >>` (different!). Null-coalescing `??` (`name ??
"guest"`), null-conditional `?.` (`user?.Name`), ternary `?:`, pattern
`is` (`if (x is int n)` declares n!). `==` on records compares by value
— a modern favourite.

**Common mistakes.** Integer division truncation; `==` on classes
comparing references (records/strings excepted — override Equals or use
records); float for money (use decimal); `TryParse` ignored (check the
bool!); null dereference (nullable warnings exist to stop this — heed
them); `char` vs `string` (`'A'` ≠ `"A"`).

**Interview angle.** "Value types copy, references share; string is an
immutable reference" — say it when aliasing questions arise. Reach for
`TryParse`, `??` and `is` patterns unprompted; they read as modern C#,
not translated Java.""",
            """int a = 17, b = 5;
Console.WriteLine($"{a / b} {(double)a / b} {a % b}");  // 3 3.4 2
Console.WriteLine($"{a == 17} {a != b} {a > 10 && b < 10}"); // True True True

string? name = null;
Console.WriteLine($"Hello, {name ?? "guest"}!");   // null-coalescing
object x = 42;
if (x is int n) Console.WriteLine($"int {n}");     // pattern declares n

var point = (X: 3, Y: 4);                          // value tuple
Console.WriteLine(point.X + point.Y);              // 7""",
            """Compute exam stats: given three marks, print total, average
(double, 1 decimal) and pass/fail (>= 40 each and avg >= 50). Then
solve the judged drill `drill-min-max-scan` (single-pass min/max).
Practice: /practice/problems/drill-min-max-scan""",
        ),
        (
            "csharp-decisions-loops",
            "Decisions and loops: if, switch, for, foreach, while",
            "Branching with patterns, and the only loop shapes you need.",
            """**Why this matters.** Decisions and loops are control flow —
every algorithm is branches + repetition. C# offers pattern-matching
`switch` expressions (concise, exhaustive-checked) alongside classic
`if/for/foreach/while`. Learn all five shapes and when each fits.

**Decisions.** `if/else if/else` with `&& || !`. `switch` statements
AND expressions: `grade = score switch { >= 90 => 'A', >= 75 => 'B', >=
50 => 'C', _ => 'F' };` — the `_` discard is required (exhaustiveness!).
Switch on types/patterns: `case int n when n > 0:`. Prefer switch
expressions for pure mapping (grade bands, token kinds); if-chains for
complex conditions. No fall-through by default (unlike C — `break` or
expression form).

**Loops.** `for (int i = 0; i < n; i++)` (index needed), `foreach (var
x in items)` (values; cannot modify the collection mid-loop!),
`while` (condition-led), `do-while` (runs once — rare). `break` exits,
`continue` skips, labeled break via extracted method (C# has `goto case`
but methods are cleaner). `for` with two indices for two-pointer scans.

**foreach rules.** Iterating `List<T>` while adding/removing throws
(InvalidOperationException) — iterate a copy (`ToList()`) or index
backwards for removal. `foreach` on arrays/strings is fast and safe.
`Enumerable.Range(1, 10)` generates ranges LINQ-style.

**Common mistakes.** `=` vs `==` (compiler catches most — heed it);
missing `_` in switch expressions (compile error — good!); modifying
collections in foreach; `i <= n` off-by-one (use `<`); infinite while
(condition never flips — update inside!); `switch` on strings with
case/culture surprises (use Ordinal compares for protocol text).

**Interview angle.** Reach for switch expressions for banding/mapping
— interviewers read them as modern. State loop invariants ("before i:
sorted") on array problems. `foreach` for reads, `for` for rewrites:
say the rule, follow it.""",
            """static char Grade(int score) => score switch
{
    >= 90 => 'A',
    >= 75 => 'B',
    >= 50 => 'C',
    _ => 'F',
};

for (int n = 1; n <= 15; n++)          // FizzBuzz
{
    string s = (n % 3 == 0, n % 5 == 0) switch
    {
        (true, true) => "FizzBuzz",
        (true, false) => "Fizz",
        (false, true) => "Buzz",
        _ => n.ToString(),
    };
    Console.WriteLine(s);
}
Console.WriteLine(Grade(73));          // C""",
            """Print a 10×10 multiplication table (aligned, width 4). Then
solve the judged drill `drill-grade-bands` (boundaries matter!).
Practice: /practice/problems/drill-grade-bands""",
        ),
        (
            "csharp-methods-arrays",
            "Methods and arrays: signatures, ref/out, contiguous storage",
            "Overloads, optional/named args, and arrays done in place.",
            """**Why this matters.** Methods are C#'s unit of reuse; arrays are
its fastest storage. Interviews test both constantly: clean signatures
with `out`/`ref`/`in`, and in-place array algorithms (dedup, rotate,
partition). C# arrays are reference types with runtime bounds checks
(IndexOutOfRangeException, not corruption — safer than C, same speed).

**Methods.** `static int Add(int a, int b) => a + b;` (expression body
for one-liners). Overloads by arity/types (not by return!). Optional
`void Log(string msg, int level = 1)`, named `Log(level: 3, msg:
"hi")`. `out` (must assign: `TryParse` pattern — copy it for your own
parsers), `ref` (read-write alias), `in` (read-only ref, perf),
`params int[] rest` (variadic). Tuples for multi-return: `(int min, int
max) Range(int[] a)`. `void` vs returning status — prefer returning
results, throwing only for exceptional failures.

**Arrays.** `int[] a = new int[5];` (zeroed), `var b = new[] {1,2,3};`,
`int[][] jagged` (arrays of arrays — lengths may differ!) vs `int[,]
rect` (true 2D, `GetLength(d)`). `Length` (not Count!). `Array.Sort/
BinarySearch/Reverse/Fill/Copy`. `Span<T>`/`stackalloc` for hot paths
(interviews: mention, rarely require). Bounds checked — off-by-one
throws instead of corrupting (still wrong, just loudly).

**In-place technique.** Read/write pointers, invariant-first. Dedup
sorted, move zeroes, remove element: `O(n)`/`O(1)`. Rotation by
reversal (`Array.Reverse` segments). Merge from the end with tail space.
Return new length; caller slices (`a[..k]` ranges — C# 8+).

**Common mistakes.** `==` on arrays (reference compare — use
`SequenceEqual`); jagged vs rect confusion (`a[i][j]` vs `a[i,j]`);
`Array.Sort` on `null`; forgetting `out` assignment on all paths
(compile error — good); `params` ambiguity; modifying `foreach`
variable (it is read-only!).

**Interview angle.** Signature with contract first: "returns new length;
first k valid." `out`/`Try` pattern for fallible work. Ranges (`a[1..^1]`)
for slices — modern and safe.""",
            """static int RemoveDuplicates(int[] a)
{
    if (a.Length == 0) return 0;
    int write = 1;   // invariant: a[0..write) holds kept items
    for (int read = 1; read < a.Length; read++)
        if (a[read] != a[read - 1]) a[write++] = a[read];
    return write;
}

static bool TryParsePair(string s, out int x, out int y)
{
    x = y = 0;
    var parts = s.Split(',');
    return parts.Length == 2 && int.TryParse(parts[0], out x) && int.TryParse(parts[1], out y);
}

int[] a = { 0, 0, 1, 1, 1, 2, 3, 3 };
int n = RemoveDuplicates(a);
Console.WriteLine(string.Join(" ", a[..n]));   // 0 1 2 3
Console.WriteLine(TryParsePair("3,4", out int x, out int y) + $" {x},{y}");""",
            """Implement `RotateRight(a, k)` via three `Array.Reverse` calls.
Then solve the judged drill `drill-sum-until-zero` (sentinel loop).
Practice: /practice/problems/drill-sum-until-zero""",
        ),
        (
            "csharp-strings-lists",
            "Strings and List<T>: text plus the growable array",
            "Immutability, StringBuilder, and List<T> as default storage.",
            """**Why this matters.** `string` (immutable, interned literals,
`==` by value) and `List<T>` (growable array, the C# vector) are the two
types you will use most. Text patterns (palindrome, window, anagram) plus
list mechanics (add/index/sort) cover the interview basics in C#.

**Strings.** Immutable: `s[0] = 'x'` fails to compile; `+`/`+=` in loops
is quadratic — `StringBuilder` (Append in loops, ToString once) or
`string.Create`/`Join`. Interpolation `$"..."` with format specs
(`$"{avg:F1}"`). Methods: `Substring` (range `s[1..^1]` preferred),
`Split` (with `StringSplitOptions.RemoveEmptyEntries`), `Replace`,
`StartsWith/EndsWith/Contains` (pass `StringComparison.Ordinal` for
protocol text!), `Trim`, `ToUpperInvariant` (culture-safe). `char.IsLetter
OrDigit/ToLowerInvariant` for normalisation. `string.IsNullOrWhiteSpace`
guards input.

**List<T>.** `var xs = new List<int> {1,2};`: `Add` amortised `O(1)`,
index `O(1)`, `Insert/RemoveAt(0)` `O(n)`, `Sort` (`O(n log n)`,
intro-sort, NOT stable — `OrderBy` is stable), `BinarySearch` (sorted!),
`Contains/IndexOf` (`O(n)` — HashSet for membership!). Capacity doubles;
`new List<int>(n)`/`EnsureCapacity` when known. `T[]` interop: `ToArray`,
`AsReadOnly`, `CollectionsMarshal.AsSpan` (advanced).

**Patterns.** Palindrome (two indices, skip non-alnum). Window + last-
index `int[128]`/`Dictionary<char,int>`. Anagram via `int[26]` or
sorted-char key. Build outputs in `List<char>`/`StringBuilder`, join
once.

**Common mistakes.** `+=` in loops; `Split` without RemoveEmptyEntries
(empty entries surprise); culture-sensitive compares on protocol text
(use Ordinal/Invariant); `List.RemoveAt(0)` in loops (quadratic —
Queue/LinkedList or reverse iteration); `Sort` instability assumed
stable; modifying in foreach.

**Interview angle.** "StringBuilder with capacity; Ordinal compares;
List for building, array for fixed" — unprompted, in the first minute.
Then the algorithm. C# text fluency is StringComparison + StringBuilder
discipline.""",
            """using System.Text;

static bool IsPalindrome(string s)
{
    int l = 0, r = s.Length - 1;
    while (l < r)
    {
        if (!char.IsLetterOrDigit(s[l])) { l++; continue; }
        if (!char.IsLetterOrDigit(s[r])) { r--; continue; }
        if (char.ToLowerInvariant(s[l++]) != char.ToLowerInvariant(s[r--])) return false;
    }
    return true;
}

var words = new List<string> { "eat", "tea", "tan" };
words.Sort(StringComparer.Ordinal);
var sb = new StringBuilder(capacity: 64);
foreach (var w in words) sb.Append(w).Append(';');
Console.WriteLine(IsPalindrome("A man, a plan, a canal: Panama")); // True
Console.WriteLine(sb.ToString());""",
            """Write `LongestUniqueSubstring` (window + last-index, O(n)).
Then solve the judged drill `drill-count-vowels`.
Practice: /practice/problems/drill-count-vowels""",
        ),
        (
            "csharp-real-world-1",
            "Real-world drills I: bills, validation, files",
            "Small honest programs: money, input loops, and safe file IO.",
            """**Why this matters.** Professionals write bills, validators and
file tools — not just algorithms. This module drills the shapes: decimal
money math, retry-until-valid input, `File`/`StreamReader` with `using`,
CSV-ish parsing with `TryParse`. Boring, employable, and exactly what
junior interviews probe ("parse this file, handle bad rows").

**Money.** `decimal` for currency (base-10 exact; double is binary —
`0.1 + 0.2 != 0.3`!). Format `$"{total:C2}"` (culture-aware) or
`F2` for fixed. Tax/discount as decimals; round explicitly
(`Math.Round(x, 2, MidpointRounding.AwayFromZero)` for half-up —
banker's rounding is the default and surprises).

**Input loops.** `while (true) { Console.Write(prompt); if
(TryParse(ReadLine(), out var v) && Valid(v)) return v; Console.WriteLine
("Try again..."); }` — the retry shape. Sentinel loops (sum until 0),
count+sum+min+max in one pass. Never trust input: null, empty, overflow
(`TryParse` handles all three).

**Files.** `File.ReadAllLines/ReadAllText/WriteAllText` for small;
`StreamReader/StreamWriter` + `using` for large/streaming. `Path.Combine`
(paths, not `+ "/"`!). Parse defensively: split, length-check, TryParse
each field, collect errors with line numbers (do not crash on row 999).
`FileNotFoundException`/`IOException` caught narrowly with a useful
message.

**Common mistakes.** double for money; `int.Parse` on user input
(throws — TryParse!); `+ "/"` paths (breaks on Windows — Path.Combine);
loading giant files wholly (stream!); swallowing exceptions (`catch {}` —
log or rethrow); forgetting `using` (locked files).

**Interview angle.** "decimal, TryParse, using, Path.Combine, errors
with line numbers" — say the checklist, then code it. File+parse tasks
are graded on robustness, not speed. Handle the bad row out loud.""",
            """using System.Globalization;

static (int Count, decimal Total) Bill(decimal[] prices)
{
    decimal subtotal = 0m;
    foreach (var p in prices) subtotal += p;
    decimal discounted = subtotal > 1000m ? subtotal * 0.9m : subtotal;
    return (prices.Length, Math.Round(discounted * 1.05m, 2, MidpointRounding.AwayFromZero));
}

static int ReadInt(string prompt)
{
    while (true)
    {
        Console.Write(prompt);
        if (int.TryParse(Console.ReadLine(), out int v)) return v;
        Console.WriteLine("Not a number — try again.");
    }
}

var (count, total) = Bill(new decimal[] { 299.99m, 899.50m, 49.99m });
Console.WriteLine($"{count} items: {total.ToString("C2", CultureInfo.GetCultureInfo("en-IN"))}");""",
            """Parse lines `name,score` (skip bad rows, report line numbers),
print count/avg/min/max. Then solve the judged drill
`drill-valid-identifier`. Practice: /practice/problems/drill-valid-identifier""",
        ),
        (
            "csharp-complexity-big-o",
            "Big-O in C#: collections costs and LINQ passes",
            "Growth rates plus the real costs of List/Dictionary/LINQ.",
            """**Why this matters.** C# interviews ask complexity with
collections named: "List.Contains in a loop — what is that?" (`O(n²)`.)
LINQ makes passes invisible (each operator is a loop), so counting
passes is the skill. Learn growth rates plus the BCL cost table.

**Growth.** `O(1)` index/dictionary-hit, `O(log n)` halving/SortedSet,
`O(n)` scans, `O(n log n)` OrderBy/Sort, `O(n²)` pairs/nested scans.
Analyse loops, then price the inside: `List.Add` amortised `O(1)`,
`Insert/RemoveAt(0)` `O(n)`, `Contains/IndexOf` `O(n)`,
`Dictionary.TryGetValue/Add` `O(1)` avg, `SortedDictionary` `O(log n)`,
`OrderBy` `O(n log n)`, `string.Contains` substring `O(n·m)`,
`+` on strings in a loop quadratic (StringBuilder!).

**LINQ passes.** `Where().Select().ToList()` = one pass (deferred!) +
materialise; but `Count()` after `Where` without `ToList` re-enumerates
(two passes); `OrderBy` buffers all (`O(n)` space); `ToDictionary/
ToHashSet` build (`O(n)` space). Deferred execution bites: query
re-runs per enumeration (materialise once with ToList when reusing!).
`Any()` short-circuits (prefer over `Count() > 0` — full count!).

**Space.** Extra collections `O(n)`; in-place on arrays `O(1)`;
recursion depth counted (`O(h)`); closures capture (hidden allocs in hot
loops — hoist); boxing (`int`→`object` in non-generic APIs — generics
avoid it).

**Common mistakes.** `Count() > 0` (use Any); re-enumerated queries;
`OrderBy` in a loop; `List.Contains` as membership (HashSet!);
`Dictionary[]` getter on miss (throws — TryGetValue!); measuring tiny
n; ignoring GC pauses in "realtime" claims.

**Interview angle.** "Brute O(n²); Dictionary makes it O(n)/O(n)"
— with the type named. For LINQ: "single deferred pass, materialised
once." C# interviewers listen for the collection names and the pass
count.""",
            """var data = Enumerable.Range(0, 20000).ToList();

// O(n^2): Contains scans per item.
bool HasDupBrute(List<int> xs)
{
    var seen = new List<int>();
    foreach (var x in xs)
    {
        if (seen.Contains(x)) return true;
        seen.Add(x);
    }
    return false;
}

// O(n): HashSet membership.
bool HasDupFast(List<int> xs)
{
    var seen = new HashSet<int>();
    foreach (var x in xs)
    {
        if (!seen.Add(x)) return true;
    }
    return false;
}

var sw = System.Diagnostics.Stopwatch.StartNew();
HasDupBrute(data);
Console.WriteLine($"brute {sw.ElapsedMilliseconds} ms");
sw.Restart();
HasDupFast(data);
Console.WriteLine($"fast {sw.ElapsedMilliseconds} ms");""",
            """Time both at n = 40,000; confirm superlinear gap. Then solve
the judged problem `binary-search` and state its complexity.
Practice: /practice/problems/binary-search""",
        ),
        (
            "csharp-oop",
            "OOP: classes, properties, interfaces, records",
            "Encapsulation that interviews actually test: contracts + invariants.",
            """**Why this matters.** C# is an OOP language with modern data
types (records, init-only, required). Interviews test design, not
definitions: "design LRU / parking lot / deck" means choose classes,
draw contracts, protect invariants. Memorised "four pillars" recitations
score zero; a clean `LRUCache` scores everything.

**Classes and properties.** Auto-properties `{ get; set; }`, init-only
`{ get; init; }` (set at construction only), `required` (must set,
C# 11+). Private setters + constructors establish invariants ("capacity
> 0, else throw"). Methods over anemic getters: `Withdraw(amount)`
validates (no overdraft!) rather than exposing `Balance` settable.
`readonly` fields, `const` for true constants. Static for stateless
helpers only (testability!).

**Interfaces and polymorphism.** `interface IRepository { Item? Get(int
id); }` — depend on abstractions (test fakes, swapping stores).
`abstract` for shared base + enforced overrides; `sealed` to close
inheritance deliberately; `virtual/override` (C# methods are non-virtual
by default — unlike Java!). Default interface methods exist (use
sparingly). Prefer composition (small services injected) over deep
hierarchies.

**Records and structs.** `record class/point` — value equality,
`with` copying, concise: perfect for DTOs/keys/messages. `record
struct` for small values. `struct` custom only for tiny immutable values
(16 bytes guideline — bigger structs copy-costly). `readonly struct`
enforces.

**Common mistakes.** Public setters destroying invariants; god classes;
inheritance for reuse (composition!); `==` on classes (reference —
records or Equals override); mutable structs (evil — readonly!);
throwing `Exception` (throw specific: ArgumentOutOfRange, InvalidOperation);
empty interfaces (role must be real).

**Interview angle.** Start with the interface + one invariant sentence:
"Balance never negative; enforced in Withdraw." Then implement. Mention
test seams (interfaces injectable). Design answers are graded on
contracts defended, not features listed.""",
            """public sealed class Account
{
    public decimal Balance { get; private set; }
    public Account(decimal opening) =>
        Balance = opening >= 0 ? opening : throw new ArgumentOutOfRangeException(nameof(opening));

    public void Deposit(decimal amount)
    {
        if (amount <= 0) throw new ArgumentOutOfRangeException(nameof(amount));
        Balance += amount;
    }

    public bool TryWithdraw(decimal amount)   // invariant: Balance never < 0
    {
        if (amount <= 0 || amount > Balance) return false;
        Balance -= amount;
        return true;
    }
}

public record Point(int X, int Y);   // value equality, with-copy

var a = new Account(100m);
Console.WriteLine(a.TryWithdraw(30m) + " " + a.Balance);  // True 70
Console.WriteLine(new Point(1, 2) == new Point(1, 2));    // True""",
            """Design `ParkingLot(capacity)` with `Park`/`Unpark`/`Full`,
defending "never over capacity" via API (no public counter setter).
Then solve the judged design problem `lru-cache`.
Practice: /practice/problems/lru-cache""",
        ),
        (
            "csharp-collections-linq",
            "Collections and LINQ: Dictionary, HashSet, queries",
            "The BCL containers plus declarative queries — with pass discipline.",
            """**Why this matters.** `Dictionary<K,V>`, `HashSet<T>`,
`List<T>`, `Queue/Stack/PriorityQueue` plus LINQ (`Where/Select/GroupBy/
OrderBy/ToDictionary`) are daily C#. Interviews expect fluent container
choice AND honest LINQ costing (passes + buffering). This module pairs
them.

**Containers.** Dictionary: `TryGetValue/TryAdd`, indexer (throws on
miss-get, upserts on set — know the asymmetry!), `GetValueOrDefault`.
HashSet: `Add` (false if present), set ops (`IntersectWith/ExceptWith/
Overlaps`). `SortedDictionary/SortedSet` (`O(log n)`, ordered).
`Queue/Stack` (`Enqueue/Dequeue`, `Push/Pop/Peek` — throw when empty:
`TryDequeue/TryPeek/TryPop` for safe). `PriorityQueue<TElement,
TPriority>` (.NET 6+: Enqueue/Dequeue/Peek, min-first; `EnqueueDequeue`
for bounded top-k!). `LinkedList<T>` (O(1) node ops for LRU).

**LINQ core.** `Where/Select/SelectMany/OrderBy/ThenBy/GroupBy/Join/
Distinct/First/FirstOrDefault/Single/Any/All/Count/Sum/Min/Max/Average/
ToList/ToArray/ToDictionary/ToHashSet/Chunk` (.NET 6+). Deferred vs
immediate: queries re-run per enumeration (materialise shared ones!).
`Any()` not `Count() > 0`. `FirstOrDefault` + null-check (or `?? throw`).
Method syntax > query syntax in interviews (clearer, composable).

**Patterns.** Two Sum (Dictionary check-then-add). Group anagrams
(`GroupBy(sorted-key)` or `ToLookup`). Top-k (`OrderByDescending.Take`
`O(n log n)` vs size-k PriorityQueue `O(n log k)` — state both!).
Frequency (`GroupBy.Count` or manual). Intersect/dedup (HashSet/Distinct
— `DistinctBy` (.NET 6+) for keys!).

**Common mistakes.** Indexer-get on miss (throws!); re-enumeration;
`OrderBy` in loops; `First()` on empty (throws — FirstOrDefault!);
`Single` when many possible (throws — know the contract); mutating
during enumeration; `ToList` everywhere (buffering unneeded); forgetting
`StringComparer.Ordinal` in dictionaries of protocol text (culture key
bugs! — pass comparer explicitly).

**Interview angle.** "LINQ single pass, materialised once" or "manual
loop — hot path, avoid delegate+iterator overhead." Stating when you
WOULD NOT use LINQ shows seniority. Name comparers for string keys.""",
            """var words = new[] { "eat", "tea", "tan", "ate", "nat", "bat" };

// Group anagrams: LINQ one-liner + manual Dictionary version.
var groups = words.GroupBy(w => string.Concat(w.OrderBy(c => c)))
                  .Select(g => g.OrderBy(x => x, StringComparer.Ordinal).ToList())
                  .ToList();
Console.WriteLine(groups.Count);   // 3

// Top-2 frequent via bounded PriorityQueue: O(n log k).
int[] nums = { 1, 1, 1, 2, 2, 3 };
var freq = new Dictionary<int, int>();
foreach (var x in nums) freq[x] = freq.GetValueOrDefault(x) + 1;
var pq = new PriorityQueue<int, int>();   // (value, count), min-first
foreach (var (value, count) in freq)
{
    pq.Enqueue(value, count);
    if (pq.Count > 2) pq.Dequeue();
}
var top = new List<int>();
while (pq.Count > 0) top.Add(pq.Dequeue());
Console.WriteLine(string.Join(",", top));  // 2,1 (ascending by count)""",
            """Solve top-k-frequent both ways (OrderBy-Take vs bounded PQ)
and time at n = 200k. Then solve the judged problem `two-sum`.
Practice: /practice/problems/two-sum""",
        ),
        (
            "csharp-errors",
            "Errors: exceptions, using, nullable, Try-patterns",
            "Throw rarely, dispose always, parse with Try, null with intent.",
            """**Why this matters.** C# errors come in three systems:
exceptions (exceptional failures), nullable (`?` — expected absence),
and Try-patterns (`bool TryX(out v)` — fallible parsing). Mixing them
up (exceptions for control flow, nulls unmarked, Parse on user input)
is the #1 junior smell. Learn each system's job.

**Exceptions.** Throw for exceptional, caller-cannot-prevent failures
(IO down, invariant violated — `Argument*/InvalidOperation/
NotSupported`, custom `DomainException : Exception` with context).
Catch narrowly (`catch (IOException ex)` + message with path!), `finally`
for cleanup, `using` for disposal (preferred — deterministic!). Never
`catch {}` (hides bugs — log + rethrow bare `throw;` to preserve stack;
`throw ex;` resets it — know the difference!). `ExceptionDispatchInfo`
for advanced rethrow. Validate public inputs eagerly (throw
Argument*), not deep inside.

**using and IDisposable.** `using var fs = File.OpenRead(path);` (C# 8+
declaration form — disposes at scope end). `await using` for
IAsyncDisposable. Implement `Dispose()` for owned unmanaged/managed-
disposable resources (full pattern with `Dispose(bool)` + finalizer only
for direct unmanaged handles — rare). `HttpClient` reuse (single
instance/static — socket exhaustion otherwise!), not per-call dispose.

**Nullable and Try.** `<Nullable>enable</Nullable>` + `string?` for
maybe-absent; `??`/`?.`/`!` (null-forgiving ONLY with proof — comment
why!). `TryParse/TryGetValue/TryDequeue/TryPop` for expected failure
(input, lookups) — no exceptions on hot paths. Result types
(`OneOf`/`FluentResults` or tuples `(bool Ok, T? Value, string? Error)`)
for domain failures without exceptions.

**Common mistakes.** Exceptions for flow (return Try/Result!); empty
catch; `throw ex` (stack reset); missing using (leaks/locks); `!
` to silence warnings (lies — fix the null!); `Parse` on input;
`async void` (except event handlers — unobserved crashes!); `.Result`
deadlocks (await all the way).

**Interview angle.** "Expected absence: nullable/Try; exceptional: typed
exceptions with context; resources: using." Say the three systems, place
each decision. Robustness answers are graded on the taxonomy, not just
the catch.""",
            """static bool TryGrade(int score, out char grade)
{
    grade = score switch
    {
        >= 0 and <= 100 => score switch
        {
            >= 90 => 'A',
            >= 75 => 'B',
            >= 50 => 'C',
            _ => 'F',
        },
        _ => 'X',
    };
    return score is >= 0 and <= 100;
}

static int CountLines(string path)
{
    try
    {
        using var reader = new StreamReader(path);
        int count = 0;
        while (reader.ReadLine() is not null) count++;
        return count;
    }
    catch (IOException ex)
    {
        Console.Error.WriteLine($"Cannot read '{path}': {ex.Message}");
        return -1;
    }
}

Console.WriteLine(TryGrade(73, out char g) + " " + g);  // True C
Console.WriteLine(TryGrade(150, out _) == false);       // True""",
            """Write `TryParseVersion("1.2.10")` → (1,2,10) or false (no
exceptions on bad input). Then solve the judged parsing problem
`version-compare`. Practice: /practice/problems/version-compare""",
        ),
        (
            "csharp-recursion-sorting",
            "Recursion and sorting: memo, comparers, OrderBy",
            "Base cases + memo dictionaries, and ordering done right.",
            """**Why this matters.** Recursion (trees, backtracking, top-down DP)
plus sorting (OrderBy/sort with comparers, binary search) are the
algorithmic core. C# specifics: memo `Dictionary<(int,int),long>`,
`IComparer<T>`/`Comparison<T>`, stable `OrderBy` vs unstable
`List.Sort`, `BinarySearch` contracts.

**Recursion.** Base + progress + trust. Depth = height/chain (stack
~1MB default per thread — deep linear recursion overflows; iterate or
explicit `Stack<T>`). Memoize overlapping subproblems:
`Dictionary<int,long>` or arrays (-1 sentinel). Fibonacci `O(φⁿ)`→`O(n)`.
Backtracking: shared `List<int>` path + add/explore/remove; board arrays
for N-Queens/word-search with mark/restore. Tail recursion NOT guaranteed
(iterate deep chains!).

**Sorting.** `List.Sort()` (intro-sort, unstable, in place) vs
`OrderBy().ThenBy()` (stable, deferred+buffered, needs `ToList`).
Comparers: `Comparer<int>.Create((a,b) => ...)`, `StringComparer.Ordinal
`, `OrderBy(x => x.Age).ThenBy(x => x.Name)`. Multi-key arrays:
`Array.Sort(keys, items)`! `BinarySearch` (sorted + same comparer;
negative `~index` = insertion point — decode with `~`). `PriorityQueue`
for streaming top-k (`O(n log k)` beats full sort).

**Search.** `List.BinarySearch`, `Array.BinarySearch`, `SortedSet.GetView
Between` (ranges!). Hand binary search for custom predicates (first/last/
rotated/sqrt/search-on-answer): invariant + overflow-safe mid (`lo + (hi
- lo) / 2` — int overflow wraps silently in unchecked! use long or
checked where adversarial).

**Common mistakes.** No memo (exponential); sentinel collision;
`OrderBy` without `ToList` re-sorting per enumeration; unstable sort
assumed stable; `BinarySearch` unsorted/wrong comparer; `~` insertion
point mishandled; recursion depth unexamined; `Comparison` inconsistent
(sort misbehaves/crashes).

**Interview angle.** "Top-down memo O(states); bottom-up next with
compression." For ordering: "stable OrderBy needed here because..."
vs "in-place Sort suffices." Comparer + stability + binary-search
contract, stated together, is complete.""",
            """// Top-down fib with memo dictionary: O(n).
static long Fib(int n, Dictionary<int, long> memo)
{
    if (n < 2) return n;
    if (memo.TryGetValue(n, out long v)) return v;
    return memo[n] = Fib(n - 1, memo) + Fib(n - 2, memo);
}

var students = new List<(string Name, int Grade)> { ("b", 2), ("a", 3), ("a", 1) };
var ordered = students.OrderBy(s => s.Name, StringComparer.Ordinal).ThenBy(s => s.Grade).ToList();
Console.WriteLine(Fib(90, new Dictionary<int, long>()));
foreach (var s in ordered) Console.WriteLine($"{s.Name} {s.Grade}");

int[] sorted = { 1, 2, 2, 2, 5 };
Console.WriteLine(Array.BinarySearch(sorted, 2));   // some index of 2 (>= 0)""",
            """Implement lower-bound by hand (first >= target). Then solve
the judged problem `merge-intervals` (sort + single merge pass).
Practice: /practice/problems/merge-intervals""",
        ),
        (
            "csharp-stacks-queues",
            "Stack, Queue, PriorityQueue: processing order",
            "LIFO/FIFO discipline, monotonic stacks, BFS and top-k.",
            """**Why this matters.** `Stack<T>` (Push/Pop/Peek/TryPop),
`Queue<T>` (Enqueue/Dequeue/TryDequeue), `PriorityQueue<TElement,
TPriority>` (min-first) cover parentheses, RPN, next-greater, BFS
levels, Dijkstra, top-k, scheduling. Order-of-processing IS the
algorithm — pick the structure that processes first what matters first.

**Stacks.** `Push/Pop/Peek` (`O(1)` amortised); empty Pop/Peek throws
(InvalidOperation — `TryPop/TryPeek` for safe!). Parentheses: push
openers, match closers, empty at end. RPN: numbers push, operators pop-
apply-push. Monotonic (indices, decreasing values): next-greater,
temperatures, spans, largest rectangle — each index pushed/popped once
(`O(n)` proof in one line). Min-stack: stack of (value, running-min).

**Queues and BFS.** `Enqueue/Dequeue/Peek/Count`; `TryDequeue` safe.
BFS: seed, pop, push unvisited; `for (i < Count-at-layer-start)` loops
per level (distances!). Multi-source: enqueue all starts (oranges).
`PriorityQueue` for Dijkstra/A*/best-first (no decrease-key: push
updated + skip stale on pop — state the trick!). `EnqueueDequeue` for
bounded streams.

**PriorityQueue details.** `.NET 6+`; `Enqueue(element, priority)`
(min-first!); `Dequeue/Peek/Try*`; `Count`. Max-heap: negate numeric
priorities or custom comparer (no comparer ctor — wrap priorities!).
Unbounded growth on push-heavy streams: bound explicitly (size-k heaps
for top-k: `O(n log k)`).

**Common mistakes.** Pop/Dequeue on empty (throws!); `Queue.Count` in
`for` condition re-evaluated (capture layer size first!); PQ max/min
confusion (min-first default!); stale heap entries without skip-check;
no visited in BFS; `Stack` enumerated expecting pop order (enumeration
is top-down but non-destructive — fine, just know it).

**Interview angle.** Triggers: "recent unmatched" → Stack; "layers/
shortest" → Queue BFS; "k extreme/streaming" → bounded PQ. State
"each item enters/leaves once" for `O(n)`; "no decrease-key, lazy
stale-skip" for Dijkstra. Order vocabulary = algorithm vocabulary.""",
            """static bool IsValid(string s)
{
    var pairs = new Dictionary<char, char> { [')'] = '(', [']'] = '[', ['}'] = '{' };
    var st = new Stack<char>();
    foreach (char ch in s)
    {
        if (pairs.TryGetValue(ch, out char open))
        {
            if (!st.TryPop(out char top) || top != open) return false;
        }
        else st.Push(ch);
    }
    return st.Count == 0;
}

static int EvalRpn(string[] tokens)
{
    var st = new Stack<int>();
    foreach (var t in tokens)
    {
        if (int.TryParse(t, out int n)) st.Push(n);
        else
        {
            int b = st.Pop(), a = st.Pop();
            st.Push(t switch { "+" => a + b, "-" => a - b, "*" => a * b, _ => a / b });
        }
    }
    return st.Pop();
}

Console.WriteLine(IsValid("()[]{}") + " " + IsValid("([)]"));  // True False
Console.WriteLine(EvalRpn(new[] { "2", "1", "+", "3", "*" })); // 9""",
            """Solve daily-temperatures with a monotonic index stack. Then
solve the judged stack problem `evaluate-rpn`.
Practice: /practice/problems/evaluate-rpn""",
        ),
        (
            "csharp-trees-heaps",
            "Trees and heaps: walks, BST, PriorityQueue",
            "Traversals with records/classes, ordered sets, streaming extremes.",
            """**Why this matters.** Trees (file hierarchies, DOMs, indexes) +
heaps (top-k, scheduling, medians) are the medium/hard core. C# gives
clean node classes, `SortedSet` (red-black, `O(log n)`), and
`PriorityQueue`. Traversal choice IS the solution — name it first.

**Trees.** `class TreeNode { public int Value; public TreeNode? Left,
Right; }` (nullable children!). Preorder (copy/serialize), inorder (BST
sorted), postorder (heights/diameter/delete-logic), level order
(`Queue<TreeNode>` rows). Max depth `1 + max(l,r)`. Symmetry mirrors.
Diameter tracks `l + r` in height pass. BST validate with `(long? min,
max)` bounds (int edges!). Kth smallest inorder-count. `SortedSet/
SortedDictionary` when balance guaranteed matters (mention vs hand-BST).

**Heaps.** `PriorityQueue<TElement, TPriority>` min-first. Top-k: bound
at k (`O(n log k)`). Kth largest, merge-k-sorted (heap of heads +
indices), task scheduler, running median (two PQs: max-low via negated
priorities + min-high, rebalance). No decrease-key → lazy stale-skip
(Dijkstra!). No max-first flag → negate or invert comparer logic.

**C# specifics.** Nullable children force null-handling (good!). Pattern
matching on nodes (`if (node is { Left: not null }`). `record` nodes for
immutable trees (functional style + `with`). `yield return` inorder
enumerators (lazy, elegant — mention stack depth caveat). `GC` frees
unreachable subtrees (no manual delete — but still `null` deliberately
in caches to release!).

**Common mistakes.** Null base forgotten (warnings exist — heed!);
BST local-only validation; depth/level confusion; skewed recursion
(explicit stack!); PQ min/max flipped; stale entries; `SortedSet` with
bad comparer (duplicates vanish — comparer defines equality!).

**Interview angle.** "Inorder because BST-sorted" / "postorder because
children-first" — traversal justified in one clause. Height caveat.
Heap: "k small ⇒ O(n log k); lazy stale-skip." Drawn tree + named walk
= full marks.""",
            """public class TreeNode
{
    public int Value;
    public TreeNode? Left, Right;
    public TreeNode(int v) => Value = v;
}

static int MaxDepth(TreeNode? root) =>
    root is null ? 0 : 1 + Math.Max(MaxDepth(root.Left), MaxDepth(root.Right));

static List<IList<int>> LevelOrder(TreeNode? root)
{
    var outp = new List<IList<int>>();
    if (root is null) return outp;
    var q = new Queue<TreeNode>();
    q.Enqueue(root);
    while (q.Count > 0)
    {
        var level = new List<int>();
        for (int i = 0, n = q.Count; i < n; i++)
        {
            var cur = q.Dequeue();
            level.Add(cur.Value);
            if (cur.Left is not null) q.Enqueue(cur.Left);
            if (cur.Right is not null) q.Enqueue(cur.Right);
        }
        outp.Add(level);
    }
    return outp;
}

static int KthLargest(int[] nums, int k)
{
    var pq = new PriorityQueue<int, int>();
    foreach (var x in nums)
    {
        pq.Enqueue(x, x);
        if (pq.Count > k) pq.Dequeue();
    }
    return pq.Peek();
}

var root = new TreeNode(3) { Left = new TreeNode(9), Right = new TreeNode(20) };
Console.WriteLine(MaxDepth(root));              // 3
Console.WriteLine(KthLargest(new[] { 3, 2, 1, 5, 6, 4 }, 2));  // 5""",
            """Write `IsSymmetric` (mirror recursion). Then solve the judged
heap problem `kth-largest` (bounded PQ, O(n log k)).
Practice: /practice/problems/kth-largest""",
        ),
        (
            "csharp-graphs",
            "Graphs: adjacency, grids, BFS/DFS, topo, DSU",
            "Dictionary adjacency, flood fill, shortest paths, schedules.",
            """**Why this matters.** Graphs = connections: networks, grids,
prereqs, social. C# shapes: `Dictionary<int, List<int>>` adjacency,
2D arrays as implicit grids, `Queue` BFS, recursive/iterative DFS,
Kahn's topo, DSU arrays. Model ("nodes=cells, 4-neighbour") then pick
shortest (BFS) vs connectivity/order (DFS/topo/DSU).

**Representations.** `Dictionary<T, List<T>>` (sparse, `TryGetValue` for
missing); `List<int>[]` (dense ids); `int[,]`/`bool[,]` grids (GetLength
dims!); edge lists for DSU/Kruskal. Build once; traverse with visited
(`HashSet<T>` or `bool[]/bool[,]` — in-place grid marks only with
caller consent!).

**BFS/DFS.** BFS: seed queue, pop, push unvisited; layer loops for
distance; multi-source (all starts at 0). DFS: recursion (depth risk —
grids R·C worst! iterative `Stack<T>` for big) or explicit; colours
0/1/2 for directed cycle (1-revisit = back edge); finish-order for topo.
`O(V+E)`; grids `O(R·C)`.

**Topo + DSU.** Kahn: `Dictionary<T,int>` indegree + zero-queue + peel;
peeled < V ⟺ cycle. Course schedules I/II. DSU: parent/rank arrays,
halving find, union-by-rank — provinces, redundant edge, Kruskal (sort
edges + DSU). 25 lines from memory — drill it.

**Common mistakes.** No visited; single-source on disconnected (outer
loop!); directed/undirected mixup; recursion on huge grids; grid-mark
destroying input; `Dictionary` missing-key throw (TryGetValue!);
`int[,]` vs jagged indexing (`[i,j]` vs `[i][j]` — different types!);
queue layer-size capture forgotten.

**Interview angle.** Model sentence + traversal choice + `O(V+E)` with
V/E named + allocation named ("one R·C visited"). C# bonus: `ValueTuple`
coords in HashSet/Queue (`(r, c)` — value equality free!).""",
            """static int Islands(char[][] grid)
{
    int count = 0;
    for (int r = 0; r < grid.Length; r++)
        for (int c = 0; c < grid[r].Length; c++)
            if (grid[r][c] == '1') { count++; Flood(grid, r, c); }
    return count;
}

static void Flood(char[][] g, int r, int c)
{
    if (r < 0 || c < 0 || r >= g.Length || c >= g[r].Length || g[r][c] != '1') return;
    g[r][c] = '#';
    Flood(g, r + 1, c); Flood(g, r - 1, c); Flood(g, r, c + 1); Flood(g, r, c - 1);
}

// DSU with path halving + union by rank.
sealed class Dsu
{
    private readonly int[] _parent, _rank;
    public Dsu(int n) { _parent = Enumerable.Range(0, n).ToArray(); _rank = new int[n]; }
    public int Find(int x)
    {
        while (_parent[x] != x) { _parent[x] = _parent[_parent[x]]; x = _parent[x]; }
        return x;
    }
    public void Union(int a, int b)
    {
        a = Find(a); b = Find(b);
        if (a == b) return;
        if (_rank[a] < _rank[b]) _parent[a] = b;
        else if (_rank[a] > _rank[b]) _parent[b] = a;
        else { _parent[b] = a; _rank[a]++; }
    }
}

char[][] g = { "11110".ToCharArray(), "11010".ToCharArray(), "11000".ToCharArray(), "00000".ToCharArray() };
Console.WriteLine(Islands(g));   // 1""",
            """Implement Kahn's topo sort (peel-count detects cycles). Then
solve the judged problem `number-of-islands`.
Practice: /practice/problems/number-of-islands""",
        ),
        (
            "csharp-dp",
            "Dynamic programming: memo, tables, compression",
            "Top-down dictionaries, bottom-up arrays, rolling space cuts.",
            """**Why this matters.** DP: state/transition/base. C# gives
`Dictionary<(int,int),long>` memo (ValueTuple keys — free equality!),
`int[]`/`int[,]` tables, LINQ-free hot loops. Stairs/robber/coin/LIS/
LCS/edit/knapsack share the skeleton; compression (rolling rows/vars,
descending 1D) is the follow-up.

**Top-down.** Recursion + memo dict/array; only reachable states compute.
`long F(int i) { if (base) return ...; if (memo.TryGetValue(i, out var v))
return v; return memo[i] = Combine(...); }`. 2D: `(i, j)` tuple keys or
`long?[,]` (null = uncomputed — elegant!). Depth = chain (bottom-up for
long chains).

**Bottom-up.** Fill dependency order: 1D ascending, 2D row-major,
intervals by length, subsets by sum (0/1 DESCENDING — ascending =
unbounded! The direction rule is the knapsack question). `Array.Fill`
sentinels; `dp[0]` = empty-input base (off-by-one lives here!).

**Compression.** Two vars (stairs/robber `O(1)`); two rows (edit/LCS
`O(min)`); 1D descending (0/1 knapsack `O(W)`). Offer unprompted after
the table — "and it compresses because transitions look back fixed
distance."

**Recognising DP.** "Ways/min-max/can" + small choices + compact state.
1D index / 2D grid-pair / subset-sum bool / knapsack / bitmask — one
canonical each. No overlap → divide-and-conquer. Exploding state →
greedy/backtrack.

**Common mistakes.** Base/init off-by-one; fill order; 0/1-vs-unbounded
direction; `int` overflow in counts (`long`! `checked` where adversarial);
sentinel collision (use `long?`/seen-flags); recursion sans memo;
tuple-key perf fine but array faster (state the trade, pick by clarity
first).

**Interview angle.** "States × transition; live table space." Top-down
board, bottom-up + compression offered. Point at cells read. C# tuple
memo is board-friendly — use it.""",
            """static int CoinChange(int[] coins, int amount)
{
    const int INF = int.MaxValue / 2;
    var table = new int[amount + 1];
    Array.Fill(table, INF);
    table[0] = 0;
    for (int v = 1; v <= amount; v++)
        foreach (int c in coins)
            if (c <= v) table[v] = Math.Min(table[v], table[v - c] + 1);
    return table[amount] >= INF ? -1 : table[amount];
}

static int Rob(int[] nums)   // O(1) space: two rolling states.
{
    int prev2 = 0, prev1 = 0;
    foreach (int x in nums)
    {
        int cur = Math.Max(prev1, prev2 + x);
        prev2 = prev1; prev1 = cur;
    }
    return prev1;
}

// Top-down with tuple-key memo.
static long CountWays(int n, Dictionary<int, long> memo)
{
    if (n <= 1) return 1;
    if (memo.TryGetValue(n, out long v)) return v;
    return memo[n] = CountWays(n - 1, memo) + CountWays(n - 2, memo);
}

Console.WriteLine(CoinChange(new[] { 1, 2, 5 }, 11));  // 3
Console.WriteLine(Rob(new[] { 2, 7, 9, 3, 1 }));       // 12""",
            """Solve longest-increasing-subsequence O(n²), then describe
patience O(n log n). Then solve the judged problem `coin-change`
(and show greedy failing on [1,3,4]/6).
Practice: /practice/problems/coin-change""",
        ),
        (
            "csharp-async-services",
            "async/await and minimal APIs: C# at work",
            "Tasks without deadlocks, and a real HTTP service in 30 lines.",
            """**Why this matters.** C# interviews beyond DSA probe async and
services: "fetch N URLs concurrently", "build a tiny API". `async/
await` + `HttpClient` + minimal APIs are the professional core. Get
concurrency right (no `.Result` deadlocks, bounded parallelism) and a
working service shape, and you interview as a builder.

**async/await.** `async Task<T> M() { ... await X(); ... }` — await
yields without blocking threads. Rules: async all the way (no `.Result/
Wait()` — deadlocks under contexts!); `Task.WhenAll` for concurrency
(fire all, await once); `SemaphoreSlim` to bound it (unbounded = socket/
server abuse); `CancellationToken` through everything; `ConfigureAwait
(false)` in libraries (not needed in ASP.NET Core, harmless); `async
void` ONLY for event handlers (crashes unobserved otherwise!);
`ValueTask` for hot paths (know it exists).

**HttpClient.** ONE long-lived instance (static/singleton/DI —
per-call dispose exhausts sockets!). `GetFromJsonAsync<T>`,
`PostAsJsonAsync`, timeouts via `CancellationTokenSource.CancelAfter`,
`Polly`/resilience for retries (or manual exponential backoff).
Dispose responses (`using var resp`), check `IsSuccessStatusCode`.

**Minimal API.** `var builder = WebApplication.CreateBuilder(args); var
app = builder.Build(); app.MapGet("/notes/{id:int}", (int id) =>
store.TryGet(id, out var n) ? Results.Ok(n) : Results.NotFound());
app.Run();` — routing, binding, `Results.*`, validation (`[AsParameters]`
+ manual checks — never trust input!), auth (`RequireAuthorization` +
ownership checks — identity ≠ permission!). EF Core/SQLite for
persistence (parameterized — never interpolated SQL!).

**Common mistakes.** `.Result` deadlocks; unbounded WhenAll; new
HttpClient per call; `async void`; fire-and-forget without tracking
(exceptions lost!); trusting route/query input; missing ownership checks
(IDOR!); sync-over-async in ASP.NET (thread-pool starvation).

**Interview angle.** "Bounded concurrency with SemaphoreSlim(8) +
cancellation; single HttpClient." For APIs: "validate, authorize
ownership, parameterize." Working-service answers are graded on the
safety trio: bounds, validation, ownership.""",
            """// Concurrent fetch, bounded to 4 at a time, cancellable.
using System.Net.Http.Json;

static readonly HttpClient Http = new() { Timeout = TimeSpan.FromSeconds(10) };

static async Task<string[]> FetchAllAsync(string[] urls, CancellationToken ct)
{
    using var gate = new SemaphoreSlim(4);
    async Task<string> OneAsync(string url)
    {
        await gate.WaitAsync(ct);
        try
        {
            using var resp = await Http.GetAsync(url, ct);
            resp.EnsureSuccessStatusCode();
            return await resp.Content.ReadAsStringAsync(ct);
        }
        finally { gate.Release(); }
    }
    return await Task.WhenAll(urls.Select(OneAsync));
}

// Minimal API sketch (Program.cs of `dotnet new web`):
// var builder = WebApplication.CreateBuilder(args);
// var app = builder.Build();
// app.MapGet("/health", () => Results.Ok(new { status = "ok" }));
// app.MapGet("/notes/{id:int}", (int id) => id > 0 ? Results.Ok(new { id }) : Results.BadRequest());
// app.Run();

Console.WriteLine("HttpClient ready; MapGet sketch above.");""",
            """Fetch 5 URLs concurrently (bound 2), measure wall time vs
sequential. Then solve the judged practical problem `base64-encode`
(encoding for service payloads). Practice: /practice/problems/base64-encode""",
        ),
        (
            "csharp-interview-mastery",
            "Google-level problem solving in C#",
            "Method + BCL precision + nullable-clean code, every time.",
            """**Why this matters.** Method wins hard interviews: clarify,
brute force, optimise, code, test — with C# precision (collections
named, nullables honoured, LINQ costed). This module fuses the atlas
with C# idioms into a rehearsal plan.

**Five steps, C#.** (1) Clarify + nullables: examples, sizes, sorted,
mutable, "can input be null/empty?" (signature `string?` vs `string`
decides!). (2) Brute force aloud + complexity. (3) Optimise by pattern:
inner search → Dictionary/HashSet; sorted pairs → two pointers; window
→ counts; nested → Stack; levels/shortest → Queue BFS; order/connect →
DFS/topo/DSU; k-extreme → PriorityQueue; counting/optimum → DP;
boundary → binary search on answer; choose/unchoose → backtracking.
(4) Code: Try-patterns, `is` patterns, invariant comments, `'\n'` joins.
(5) Trace + null/empty/single/dupe/max; nullable warnings zero; tests.

**Design (LRU etc.).** `Dictionary<K, LinkedListNode<KV>>` + `LinkedList
<KV>` (O(1) move-to-front via node handles — the C# LRU). MinStack
(value, min) pairs. Trie (Dictionary<char,Node>/arrays + end flag).
TimeMap (Dictionary + SortedList + binary search). State per-op Big-O
as you declare methods.

**Behave senior.** Nullable annotations on every signature; `TryGetValue/
TryParse/TryDequeue`; `StringComparison.Ordinal` for protocol text;
`Any()` not `Count > 0`; materialise shared LINQ once; `long` for
counts; overflow-aware mids; `required`/`init` for DTOs; xUnit tests
with `[Theory]` cases (boundaries!). Talk continuously — narrate
invariant + next lines.

**Common mistakes.** Silent coding; memorised scripts vs twists;
nullable warnings ignored (they ARE latent NullRefs!); exceptions for
flow; `.Result`; re-enumerated LINQ; no dry-run; `First()` on maybe-
empty.

**Rehearsal.** 120+ aloud-timed atlas-wide; miss-log by pattern; weekly
redos; monthly from-memory LRU/Trie/DSU/heap. Nullable-clean + tested +
timed = the offer profile.""",
            """// LRU the C# way: Dictionary + LinkedList node handles, O(1).
public sealed class LruCache
{
    private readonly int _cap;
    private readonly Dictionary<int, LinkedListNode<(int Key, int Value)>> _map = new();
    private readonly LinkedList<(int Key, int Value)> _order = new();

    public LruCache(int capacity) => _cap = capacity > 0
        ? capacity : throw new ArgumentOutOfRangeException(nameof(capacity));

    public int Get(int key)
    {
        if (!_map.TryGetValue(key, out var node)) return -1;
        _order.Remove(node);
        _order.AddFirst(node);
        return node.Value.Value;
    }

    public void Put(int key, int value)
    {
        if (_map.TryGetValue(key, out var existing))
        {
            _order.Remove(existing);
            existing.Value = (key, value);
            _order.AddFirst(existing);
            return;
        }
        if (_map.Count == _cap)
        {
            var lru = _order.Last!;
            _order.RemoveLast();
            _map.Remove(lru.Value.Key);
        }
        var node = _order.AddFirst((key, value));
        _map[key] = node;
    }
}

var c = new LruCache(2);
c.Put(1, 1); c.Put(2, 2);
Console.WriteLine(c.Get(1));  // 1
c.Put(3, 3);                  // evicts 2
Console.WriteLine(c.Get(2));  // -1""",
            """Implement MinStack + Trie from memory, nullable-clean. Then
solve the judged DP hard `word-break` (memo + trie-pruned follow-up).
Practice: /practice/problems/word-break""",
        ),
    ]
}

#: Module slug -> judged problem slug for the "code what you learned" button.
MODULE_PRACTICE: dict[str, str] = {
    "csharp-why": "fizzbuzz",
    "csharp-hello": "drill-times-table",
    "csharp-variables-operators": "drill-min-max-scan",
    "csharp-decisions-loops": "drill-grade-bands",
    "csharp-methods-arrays": "drill-sum-until-zero",
    "csharp-strings-lists": "drill-count-vowels",
    "csharp-real-world-1": "drill-valid-identifier",
    "csharp-complexity-big-o": "binary-search",
    "csharp-oop": "lru-cache",
    "csharp-collections-linq": "two-sum",
    "csharp-errors": "version-compare",
    "csharp-recursion-sorting": "merge-intervals",
    "csharp-stacks-queues": "evaluate-rpn",
    "csharp-trees-heaps": "kth-largest",
    "csharp-graphs": "number-of-islands",
    "csharp-dp": "coin-change",
    "csharp-async-services": "base64-encode",
    "csharp-interview-mastery": "word-break",
}

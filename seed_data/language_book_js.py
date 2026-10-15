"""Book-depth JavaScript and TypeScript modules: DSA with types and tests.

JavaScript is the web's language (browser + Node); TypeScript adds static
types for larger codebases. Both share the DSA core — complexity, strings/
arrays, recursion/sorting, maps/sets, trees/graphs, DP — taught here with
idiomatic JS/TS (map/filter/reduce honestly costed, Map/Set over objects,
generics in TS) plus a method module each. Six modules per language.
"""

from __future__ import annotations

BOOK_MODULES: dict[str, list[tuple]] = {
    "javascript": [
        (
            "js-complexity-big-o",
            "Big-O in JavaScript: loops, methods and hidden passes",
            "Growth rates plus what map/filter/find really cost.",
            """**Why this matters.** JS array methods hide loops: `filter().map()`
is two passes; `includes` in a loop is quadratic; `sort` without a
comparator sorts lexicographically (`[10, 9].sort()` → `[10, 9]` — the
classic bug). Interviews ask complexity expecting you to see through the
chaining. Learn growth + method costs together.

**Growth.** `O(1)` index/Map-hit, `O(log n)` halving, `O(n)` scans, `O(n
log n)` sort, `O(n²)` pairs. Price the inside: `arr.push` amortised
`O(1)`, `shift/unshift` `O(n)` (use index pointers instead!), `includes/
indexOf/find` `O(n)`, `Map/Set` ops average `O(1)`, `sort` `O(n log n)`
(TimSort, stable), `slice/splice` copy (`O(k)`), string `+` in loops
quadratic (array + `join`!).

**Chaining honesty.** `arr.filter(f).map(g)` = 2 passes + 1 temp array
(fine usually; one `for` loop when hot). `find` short-circuits (good);
`forEach` cannot break (use `for...of` + break, or `some/every`).
`reduce` is a loop with an accumulator — readable for sums, write-only
for cleverness. Spread `{...obj}`/`[...arr]` copies (`O(n)` — in a loop,
quadratic!).

**Space.** Temps per chain link `O(n)`; in-place index work `O(1)`;
recursion depth counted (call stack ~10k — deep chains overflow!);
closures capture (fine, but hoist hot allocs).

**Common mistakes.** Lexicographic sort (`sort((a,b) => a-b)` for
numbers!); `shift` in loops; `includes` membership (Set!); re-sorting
per query; `JSON.parse/stringify` in hot paths (expensive!);
`==` coercion (`===` always).

**Interview angle.** "Two passes + one temp; single loop if hot."
Name the comparator for every sort. JS interviewers watch method-cost
literacy — chaining is encouraged, blind chaining is not.""",
            """// O(n²): includes() scans per item.
function hasDupBrute(xs) {
  const seen = [];
  for (const x of xs) {
    if (seen.includes(x)) return true;
    seen.push(x);
  }
  return false;
}

// O(n): Set membership.
function hasDupFast(xs) {
  const seen = new Set();
  for (const x of xs) {
    if (seen.has(x)) return true;
    seen.add(x);
  }
  return false;
}

const data = Array.from({ length: 30000 }, (_, i) => i);
for (const [name, fn] of [["brute", hasDupBrute], ["fast", hasDupFast]]) {
  const t0 = Date.now();
  fn(data);
  console.log(name, Date.now() - t0 + "ms");
}
console.log([10, 9, 80].sort((a, b) => a - b));  // 9,10,80 (not lexical!)""",
            """Time both at n = 60,000. Then solve the judged problem
`binary-search` and state why it is O(log n).
Practice: /practice/problems/binary-search""",
        ),
        (
            "js-strings-arrays-deep",
            "Strings and arrays: text patterns, in-place skill",
            "Two pointers, windows, and read/write invariants on arrays.",
            """**Why this matters.** Strings (immutable UTF-16, `charAt/
slice/split`) + arrays (the universal structure) + two patterns
(pointers, windows) solve most JS interview basics. In-place array work
(dedup, move-zeroes, rotate) tests the read/write invariant.

**Strings.** Immutable (`s[0] = 'x'` silently fails — no error!).
`slice/substring`, `split/join`, `replace` (string = first only!
`/re/g` or `replaceAll` for all), `trim`, `startsWith/endsWith/includes`,
`toLowerCase` (locale variants for i18N — `toLocaleLowerCase('tr')` is
the famous surprise). Surrogate pairs: emoji are two UTF-16 units
(`'😀'.length === 2` — `Array.from(s)` splits by code point; mention
it, rarely implement). Build via array + `join('')`.

**Arrays.** `push/pop` `O(1)`; `shift/unshift` `O(n)`; `splice` mutates
+ returns removed (powerful, `O(n)`); `slice` copies; `sort` needs
comparator; `map/filter/reduce/find/some/every` (know short-circuiters);
`flat/flatMap`, `at(-1)` (negative index!), destructuring `[a, b] = [b,
a]` swaps. `Array.from({length: n})` builds ranges.

**Patterns.** Palindrome (indices inward, skip non-alnum with
`/\\W/`... careful: test). Window + last-index Map (longest unique).
Anagram (`sort` key or 26-counts). In-place: read/write pointers,
reverse segments for rotation, end-merge with tail space. Invariant
before code, always.

**Common mistakes.** Mutating strings (impossible!); `sort()` lexical;
`splice` during iteration (index chaos — iterate backwards!); `==`;
`length` truncation tricks (works but obscure — slice instead); sparse
arrays (`new Array(3).map` skips holes — `Array.from` or `fill` first!).

**Interview angle.** "Strings immutable → build in array, join once;
arrays in place with write-invariant." Emoji/surrogate awareness said
once shows depth. Comparator on every sort, no exceptions.""",
            """function isPalindrome(s) {
  let l = 0, r = s.length - 1;
  const isAlnum = (c) => /[a-z0-9]/i.test(c);
  while (l < r) {
    if (!isAlnum(s[l])) { l++; continue; }
    if (!isAlnum(s[r])) { r--; continue; }
    if (s[l].toLowerCase() !== s[r].toLowerCase()) return false;
    l++; r--;
  }
  return true;
}

function moveZeroes(nums) {   // write-invariant, O(1) space
  let w = 0;
  for (let r = 0; r < nums.length; r++) {
    if (nums[r] !== 0) [nums[w++], nums[r]] = [nums[r], nums[w]];
  }
  return nums;
}

console.log(isPalindrome("A man, a plan, a canal: Panama")); // true
console.log(moveZeroes([0, 1, 0, 3, 12]));                   // 1,3,12,0,0""",
            """Write longest-unique-substring (window + Map, O(n)). Then solve
the judged text problem `reverse-words`.
Practice: /practice/problems/reverse-words""",
        ),
        (
            "js-recursion-sorting",
            "Recursion and sorting: memo, comparators, merge",
            "Base cases with Map memo, and ordering you can defend.",
            """**Why this matters.** Recursion (trees, backtracking, top-down
DP) + sorting (comparators, binary search, merge) in idiomatic JS: `Map`
memo, arrow comparators, `sort` stability (guaranteed), spread-safe
merging. Depth discipline matters (stack ~10k frames).

**Recursion.** Base + progress + trust. Memoize with `Map` (any key
type!) or arrays; fib `O(φⁿ)`→`O(n)`. Backtracking: shared `path` array
+ push/explore/pop; subsets/permutations/combinations; prune early.
Depth = height/chain — deep linear recursion overflows (iterate or
trampoline for those). Default params carry accumulators cleanly
(`function dfs(node, path = [])`).

**Sorting.** `sort((a, b) => a - b)` numbers (comparator required!);
multi-key `(a, b) => a[0] - b[0] || a[1] - b[1]`; `localeCompare` for
strings (`a.localeCompare(b, 'en')`); stable (equal keeps order —
useful!). `toSorted` (non-mutating, modern). Merge-two-sorted with
indices (merge sort's heart + standalone problem). `nth_element`? None
built-in — quickselect by hand or `sort` + index (state the trade!).

**Binary search.** No built-in (write it!): invariant + overflow-safe
mid (`lo + ((hi - lo) >> 1)` — bit-shift floors for 32-bit; or
`Math.floor`). Variants: first/last, rotated, sqrt, search-on-answer
(koko/capacity — monotone predicate!).

**Common mistakes.** No memo; `sort()` lexical; mutating inputs callers
need (`toSorted`/copy!); comparator inconsistency (sort misbehaves);
`>>` on > 2³¹ (use Math.floor for big); recursion on huge depth;
`Array(n).map` holes.

**Interview angle.** "Memo Map: O(states); bottom-up + compression
next." Sorting: "comparator + stability noted; O(n log n)." JS
interviewers accept recursion freely but check depth awareness — state
it.""",
            """const memo = new Map();
function fib(n) {
  if (n < 2) return n;
  if (memo.has(n)) return memo.get(n);
  const v = fib(n - 1) + fib(n - 2);
  memo.set(n, v);
  return v;
}

function mergeSorted(a, b) {
  const out = [];
  let i = 0, j = 0;
  while (i < a.length && j < b.length)
    out.push(a[i] <= b[j] ? a[i++] : b[j++]);
  return out.concat(a.slice(i), b.slice(j));
}

console.log(fib(50));                          // 12586269025
console.log(mergeSorted([1, 3, 5], [2, 4, 6])); // 1..6
console.log([3, 1, 2].toSorted((a, b) => a - b));""",
            """Write binary search returning leftmost index (or -1). Then
solve the judged merge problem `merge-sorted-arrays`.
Practice: /practice/problems/merge-sorted-arrays""",
        ),
        (
            "js-maps-sets",
            "Map, Set and counting patterns",
            "Hashing without object pitfalls, plus top-k and grouping.",
            """**Why this matters.** `Map`/`Set` (any keys, insertion-ordered,
`O(1)` avg, `.size`) beat plain objects (string keys, prototype chain,
no size) for algorithmic work. Complement/frequency/seen patterns run
on them; grouping + top-k complete the toolkit.

**Map over object.** `map.get/set/has/delete`, `has` before `get`
(`undefined` ambiguity otherwise!), `getOrDefault` pattern (`map.get(k)
?? 0`). Any key type (objects by identity!). Iteration ordered. `Object`
for records/JSON shapes; `Map` for algorithmic maps — state the rule.
`WeakMap/WeakSet` for metadata without leaks (mention, rarely implement).

**Set.** `add/has/delete`, dedup (`[...new Set(xs)]`, ordered!), set
algebra via filter (`a.filter(x => b.has(x))` intersection, `O(n)`),
`union/intersection/difference` methods (modern JS has them — or
one-liners).

**Patterns.** Complement (Two Sum: check-then-set). Frequency (`count.set
(x, (count.get(x) ?? 0) + 1)`; anagrams; ransom). Seen (dupes, visited,
cycle states). Grouping (`Map<key, array>` + `if (!has) set([])`).
Top-k: full sort `O(n log n)` vs manual min-heap `O(n log k)` (no
built-in heap — implement or sort-and-slice, stating the trade!).

**Common mistakes.** Object as map (proto/`__proto__`/no-size traps —
`Object.create(null)` or Map!); `get` undefined ambiguity; `NaN` as Map
key (works — SameValueZero! — but confusing); mutating during iteration
(collect-then-mutate); `JSON.stringify(map)` → `{}` (Maps don't
serialize — spread to object/array first!).

**Interview angle.** "Map: O(n) avg for O(n) space; object would risk
key-collision/prototype issues." Top-k: "sort O(n log n) acceptable
here; heap O(n log k) for streams — I can write the heap." Judgment +
offer.""",
            """function twoSum(nums, target) {
  const seen = new Map();   // value -> index
  for (let i = 0; i < nums.length; i++) {
    const need = target - nums[i];
    if (seen.has(need)) return [seen.get(need), i];
    seen.set(nums[i], i);
  }
  return [];
}

function topKFrequent(nums, k) {
  const freq = new Map();
  for (const x of nums) freq.set(x, (freq.get(x) ?? 0) + 1);
  return [...freq.entries()]
    .sort((a, b) => b[1] - a[1] || a[0] - b[0])
    .slice(0, k)
    .map(([x]) => x);
}

console.log(twoSum([2, 7, 11, 15], 9));       // 0,1
console.log(topKFrequent([1, 1, 1, 2, 2, 3], 2)); // 1,2""",
            """Solve group-anagrams with Map<sortedKey, string[]>. Then solve
the judged counting problem `top-k-frequent`.
Practice: /practice/problems/top-k-frequent""",
        ),
        (
            "js-trees-graphs",
            "Trees and graphs: traversals, BFS, components",
            "Object/class nodes, level order, floods and shortest paths.",
            """**Why this matters.** Trees (DOM! JSON! org charts) + graphs
(networks, grids, deps) with JS-idiomatic traversals: recursion,
`queue` via index-pointer (never `shift`!), `Set` visited, `Map`
adjacency. DOM experience transfers directly (walk = traversal).

**Trees.** `{ value, left, right }` or classes. Preorder/inorder/
postorder recursion; level order via array-queue with head index
(`q.push(root); let h = 0; while (h < q.length) {...q[h++]}` — `O(1)`
amortised, no `shift`!). Depth `1 + max`. Symmetry mirrors. BST validate
with (min, max). Kth smallest inorder-count. JSON trees (`children[]`)
traverse identically (n-ary: loop children).

**Graphs.** `Map<node, neighbor[]>` adjacency; grids implicit (bounds +
visited `Set` of `"r,c"` keys or `boolean[][]`); edge lists for DSU.
BFS (array-queue + head index): shortest unweighted, levels, multi-
source. DFS: connectivity, islands/floods, colours cycle-detect, topo
finish-order. `O(V+E)`; grids `O(R·C)`.

**DSU/topo.** DSU parent/rank arrays (or Maps for sparse ids), halving
find. Kahn indegree-Map + zero-queue + peel-count. Course schedules,
provinces, redundant edges — same shapes as every language.

**Common mistakes.** `shift()` queues (quadratic!); no visited; recursion
depth on huge grids; directed/undirected mixup; single-source on
disconnected; `"r,c"` key building cost in hot loops (encode `r * C + c`
numbers instead!); mutating input grids callers need.

**Interview angle.** "Nodes = X; BFS shortest unweighted; visited Set of
encoded ints." DOM analogy welcome ("like walking childNodes"). State
`O(V+E)` + queue/visited space. JS graph code should look boringly
correct — arrays, indices, Sets.""",
            """function maxDepth(root) {
  if (!root) return 0;
  return 1 + Math.max(maxDepth(root.left), maxDepth(root.right));
}

function oranges(grid) {   // multi-source BFS, head-index queue
  const rows = grid.length, cols = grid[0].length;
  const q = [];
  let fresh = 0;
  for (let r = 0; r < rows; r++)
    for (let c = 0; c < cols; c++) {
      if (grid[r][c] === 2) q.push([r, c]);
      else if (grid[r][c] === 1) fresh++;
    }
  let minutes = 0, head = 0;
  const dirs = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  while (head < q.length && fresh > 0) {
    minutes++;
    const layer = q.length - head;
    for (let i = 0; i < layer; i++) {
      const [r, c] = q[head++];
      for (const [dr, dc] of dirs) {
        const nr = r + dr, nc = c + dc;
        if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && grid[nr][nc] === 1) {
          grid[nr][nc] = 2; fresh--;
          q.push([nr, nc]);
        }
      }
    }
  }
  return fresh === 0 ? minutes : -1;
}

console.log(maxDepth({ value: 1, left: { value: 2 }, right: null })); // 2""",
            """Count islands via DFS flood (mark + recurse 4-way). Then solve
the judged BFS problem `bfs-grid-distance`.
Practice: /practice/problems/bfs-grid-distance""",
        ),
        (
            "js-interview-mastery",
            "Google-level problem solving in JavaScript",
            "Method + idioms + edge discipline, timed and aloud.",
            """**Why this matters.** JS interviews span DSA + practical ("parse,
validate, fetch, render-safe"). Method wins both: clarify, brute force,
optimise, code, test — with JS idioms (Map/Set, comparators, no-shift
queues, `textContent` safety) and edge discipline (empty/NaN/unicode/
async). Rehearse the whole loop aloud.

**Five steps, JS.** (1) Clarify: examples, sizes, sorted?, mutate?, null/
undefined/NaN valid? async? (2) Brute force + complexity aloud. (3)
Optimise by atlas: inner search → Map/Set; sorted pairs → pointers;
window → counts; nested → array-stack; levels/shortest → head-index BFS;
order/connect → DFS/topo/DSU; k-extreme → sort-vs-heap (state!); ways/
optimum → DP; boundary → binary search on answer; choose/unchoose →
backtracking. (4) Code: helpers, `const`, invariant comments, `===`,
comparators. (5) Trace + `[]`/`""`/single/dupe/NaN/emoji/max; `node --
check` + quick test script.

**Practical axis.** Validate forms (`trim`, `Number.isNaN`, ranges);
`fetch` with `AbortController` timeouts + `response.ok` checks; render
safe (`textContent`, never `innerHTML` with user data!); `try/catch`
around JSON/parse; debounce expensive handlers. "Full-stack" follow-ups
grade this, not more DSA.

**Hard favourites.** Median-two-sorted (partition), trap-water (two
pointers), LRU (Map re-insertion order trick: `delete` + `set` moves to
end — the JS LRU!), serialize-tree, word ladder, longest-palindromic
(expand-around-center `O(n²)`/manacher mention), min-window (need/have
counts). Shapes, not scripts.

**Common mistakes.** Silent coding; `==`; lexical sort; `shift` queues;
objects-as-maps; unhandled rejections (async without catch!);
`innerHTML` with input (XSS!); no dry-run; memorised code vs twists.

**Rehearsal.** 120+ aloud-timed; miss-log by pattern; weekly redos;
monthly LRU/trie/heap/DSU from memory. Plus 5 practical builds (fetch +
validate + render-safe). Methodical = "natural".""",
            """// LRU via Map insertion order: delete + set moves key to end. O(1) avg.
class LRUCache {
  constructor(capacity) {
    this.cap = capacity;
    this.map = new Map();   // key -> value, LRU first
  }
  get(key) {
    if (!this.map.has(key)) return -1;
    const v = this.map.get(key);
    this.map.delete(key);
    this.map.set(key, v);
    return v;
  }
  put(key, value) {
    if (this.map.has(key)) this.map.delete(key);
    else if (this.map.size === this.cap) {
      const lru = this.map.keys().next().value;  // first = least recent
      this.map.delete(lru);
    }
    this.map.set(key, value);
  }
}

const c = new LRUCache(2);
c.put(1, 1); c.put(2, 2);
console.log(c.get(1));  // 1
c.put(3, 3);
console.log(c.get(2));  // -1 (evicted)""",
            """Solve longest-palindromic-substring via expand-around-center
O(n²). Then solve the judged problem of the same name and compare with
the DP editorial. Practice: /practice/problems/longest-palindromic-substring""",
        ),
    ],
    "typescript": [
        (
            "ts-complexity-big-o",
            "Big-O in TypeScript: typed code, same growth",
            "Complexity analysis with types that prevent whole bug classes.",
            """**Why this matters.** TypeScript adds compile-time contracts to
JavaScript's runtime — but Big-O is unchanged: loops, method costs and
hidden passes decide performance. Types help analysis (readonly arrays
signal no-copy? `ReadonlyArray` documents intent) and prevent bugs
(noUncheckedIndexedAccess catches OOB!). Learn both together.

**Growth + method costs.** Identical to JS: `O(1)` index/Map, `O(log n)`
halving, `O(n)` scans, `O(n log n)` sort (comparator! `sort((a,b) => a-b)`
— lexical default bites TS equally), `O(n²)` pairs. `push` amortised
`O(1)`; `shift` `O(n)` (index pointers!); `includes/find` `O(n)`;
`Map/Set` avg `O(1)`; `slice/spread` copy `O(n)`; string `+` loops
quadratic (array + `join`).

**Types that help.** `readonly number[]` params (no accidental mutation
— compiler-enforced!). `ReadonlyMap/Set`. `noUncheckedIndexedAccess`:
`arr[i]` is `T | undefined` — forces bounds handling (the OOB bug class,
gone!). `as const` tuples for fixed shapes. Generics preserve element
types through helpers (`function first<T>(xs: T[]): T | undefined`).

**LINQ-like chains, honestly.** `filter().map()` = 2 passes + temp (fine
or fuse to one loop when hot). `find` short-circuits; `some/every` for
existence; `reduce` for folds (readable simple, opaque clever). `for..of`
+ `break` beats `forEach` (no break!). Count passes aloud in interviews.

**Common mistakes.** `any` (analysis + safety gone — `unknown` + narrow
instead!); non-null `!` lies (prove or handle!); lexical sort (same bug,
typed!); `shift` loops; re-sorting; `Object` as map (use Map!);
unchecked indexing without the flag (enable it!).

**Interview angle.** "Typed signatures + complexity: `function f(xs:
readonly number[]): number` — O(n) time, O(1) space." Types as
documentation + analysis in one line. TS interviewers grade the
strictness settings as engineering judgment (`strict` on, always).""",
            """function hasDupFast(xs: readonly number[]): boolean {
  const seen = new Set<number>();
  for (const x of xs) {
    if (seen.has(x)) return true;
    seen.add(x);
  }
  return false;
}

function first<T>(xs: readonly T[]): T | undefined {
  return xs.length > 0 ? xs[0] : undefined;  // honest about empty
}

const data: readonly number[] = Array.from({ length: 30000 }, (_, i) => i);
const t0 = Date.now();
console.log(hasDupFast(data));   // false
console.log(`checked in ${Date.now() - t0}ms`);
console.log([10, 9, 80].sort((a, b) => a - b));  // typed AND correct""",
            """Enable `strict` + `noUncheckedIndexedAccess`; fix all new
errors in an old file. Then solve the judged problem `binary-search`.
Practice: /practice/problems/binary-search""",
        ),
        (
            "ts-collections-deep",
            "Collections: Arrays, Maps, Sets with generics",
            "Typed containers, readonly discipline, and counting patterns.",
            """**Why this matters.** TS collections = JS containers + type
params: `Map<string, number>`, `Set<number>`, `readonly T[]`. Generics
turn helpers reusable (`groupBy<T, K>`) while readonly prevents mutation
bugs at compile time. Counting/grouping patterns complete the basics.

**Typed containers.** `const m = new Map<string, number[]>()`; `m.get(k)
?? []` (undefined-aware!). `Set<T>` dedup preserving order. `readonly
T[]` inputs (callers keep ownership; compiler blocks `push`!). `as const`
for literal unions (`"red" | "blue"`). Tuples `[number, string]` with
names (`[x: number, y: number]`). `Record<string, T>` for string-keyed
objects (with the prototype caveats — Map for algorithmic use!).

**Generics.** `function groupBy<T, K>(xs: T[], key: (x: T) => K):
Map<K, T[]>` — reusable, typed. Constraints (`<T extends { id: string }>`).
`keyof`/`in` for mapped helpers. Avoid `any` (infectious!); `unknown` +
narrowing (`typeof`/`in`/`instanceof`/predicates `x is T`) for boundaries.

**Patterns.** Complement (Two Sum, typed `Map<number, number>`).
Frequency (`Map` + `?? 0`). Grouping (`Map<K, T[]>` + get-or-create).
Dedup (`[...new Set]`). Top-k (sort-slice `O(n log n)` vs heap `O(n log
k)` — state!). Window counts (`Map<char, number>` + matched).

**Common mistakes.** `any` leakage; `!` assertions instead of handling;
mutating readonly inputs (copy first!); `Record` with `__proto__` keys
(Map!); `Map.get` undefined unhandled; `JSON` boundaries unvalidated
(validate at runtime — types erase! zod/valibot in real apps).

**Interview angle.** "Generic, readonly inputs, Map for O(1) — types
prove the contract." Write the signature first, implementation second.
TS interviews grade boundary validation highly: "input crosses trust
boundary → validate at runtime, types don't survive JSON." Say it.""",
            """function groupBy<T, K>(xs: readonly T[], key: (x: T) => K): Map<K, T[]> {
  const out = new Map<K, T[]>();
  for (const x of xs) {
    const k = key(x);
    const bucket = out.get(k);
    if (bucket) bucket.push(x);
    else out.set(k, [x]);
  }
  return out;
}

function twoSum(nums: readonly number[], target: number): [number, number] | [] {
  const seen = new Map<number, number>();
  for (let i = 0; i < nums.length; i++) {
    const need = target - nums[i];
    const j = seen.get(need);
    if (j !== undefined) return [j, i];
    seen.set(nums[i], i);
  }
  return [];
}

console.log(twoSum([2, 7, 11, 15], 9));  // [0, 1]
console.log(groupBy(["eat", "tea", "tan"], (w) => [...w].sort().join("")).size); // 2""",
            """Write `topKFrequent` typed (Map + sort-slice). Then solve the
judged dedup problem `contains-duplicate` (Set, three ways + timings).
Practice: /practice/problems/contains-duplicate""",
        ),
        (
            "ts-recursion-sorting",
            "Recursion and sorting: narrowing, comparators, merge",
            "Base cases with strict null checks, and ordering done right.",
            """**Why this matters.** Recursion under `strictNullChecks`
(nullables explicit!) + sorting with typed comparators + merge/binary
search. TS forces base-case honesty (`TreeNode | null`) — the compiler
is your interviewer for nulls.

**Recursion.** `strict` makes `null` visible: `function depth(root:
TreeNode | null): number { if (root === null) return 0; ... }` — no
accidental deref. Memo `Map<number, number>` / arrays. Backtracking with
typed paths (`number[]` + push/pop). Depth = height/chain (stack ~10k).
Narrowing (`if (x === null) return` refines below!) replaces casts.

**Sorting.** `sort((a, b) => a - b)` (numbers!); `localeCompare` strings;
multi-key `||` chains; `toSorted` (immutable!); stable. `Array.prototype.
sort` mutates — `readonly` inputs need `[...xs].sort(...)` (copy!).
Merge-two-sorted typed. `lowerBound` by hand (no built-in!): invariant +
`Math.floor` mid.

**Predicates and narrowing.** `function isNonNull<T>(x: T | null): x is T`
(type predicates!) for `filter(isNonNull)` (typed output `T[]` — magic!).
`in`/`instanceof` narrow unions. Discriminated unions (`{ kind: "ok",
value } | { kind: "err", error }`) for results — exhaustive `switch`
checked!

**Common mistakes.** `!` instead of narrowing; `sort()` lexical;
mutating readonly (copy!); `filter(Boolean)` (untyped — predicate!);
recursion depth; `any[]` sorts (type the elements!); `undefined` vs
`null` confusion (pick one per API!).

**Interview angle.** "Strict nulls: signature proves empty-handling."
Discriminated-union Results for fallible work. Comparator + copy-vs-
mutate stated. TS recursion should read as total functions (every input
handled — compiler-verified!).""",
            """type Tree = { value: number; left: Tree | null; right: Tree | null } | null;

function maxDepth(root: Tree): number {
  if (root === null) return 0;   // narrowing: below, root is non-null
  return 1 + Math.max(maxDepth(root.left), maxDepth(root.right));
}

function isNonNull<T>(x: T | null | undefined): x is T {
  return x !== null && x !== undefined;
}

const mixed: (number | null)[] = [3, null, 1, 2];
const clean: number[] = mixed.filter(isNonNull).toSorted((a, b) => a - b);
console.log(maxDepth({ value: 1, left: { value: 2, left: null, right: null }, right: null })); // 2
console.log(clean);  // [1, 2, 3]""",
            """Hand-write lowerBound (first >= target) typed. Then solve the
judged pointers problem `sorted-squares`.
Practice: /practice/problems/sorted-squares""",
        ),
        (
            "ts-generics-dsa",
            "Generics in DSA: Stack<T>, Queue<T>, heaps from scratch",
            "Reusable typed structures: adapters, monotonic stacks, heaps.",
            """**Why this matters.** TS has no built-in Stack/Queue/Heap —
you write generic ones (`class Stack<T>`) or adapt arrays. That
limitation teaches the semantics: adapters, monotonic discipline, heap
invariants with comparators. Interviews accept array-adapters with typed
wrappers.

**Generic adapters.** `class Stack<T> { private items: T[] = []; push(x:
T): void {...} pop(): T | undefined {...} get size(): number {...} }`
— undefined-returning pop (honest!). Queue with head index (no `shift`!):
`{ items: T[]; head = 0; enqueue/dequeue/size }`. Types prove usage;
`readonly` where apt.

**Monotonic stacks.** Indices + decreasing values: next-greater,
temperatures, spans, rectangles — `O(n)` (push/pop once each). Typed
`number[]` indices. Heaps: `class MinHeap<T> { constructor(private
less: (a: T, b: T) => boolean) ... }` with sift up/down — top-k `O(n log
k)`, merge-k, medians (two heaps). Write once, reuse forever.

**BFS with types.** `Queue<[number, number]>` coords; `Set<number>`
visited (encoded `r * C + c`); layer loops. `Map` adjacency for general
graphs. Discriminated states where apt (`type Cell = { kind: "wall" } |
{ kind: "open", dist: number }`).

**Common mistakes.** `pop()` undefined unhandled (strictNullChecks
catches — handle!); `shift` queues; heap comparator flipped (test n=3!);
`any` in generics (constrain!); class boilerplate where array-adapter
suffices (match ceremony to need!); forgetting `size` vs `length` (own
API — document!).

**Interview angle.** "Generic adapter, undefined-safe pops, O(1)
amortised." Heap: "comparator-injected, O(log n) ops." Writing the tiny
typed structure live (not importing) is often the point — rehearse
Stack/Queue/Heap skeletons until fluent.""",
            """class Stack<T> {
  private items: T[] = [];
  push(x: T): void { this.items.push(x); }
  pop(): T | undefined { return this.items.pop(); }
  peek(): T | undefined { return this.items[this.items.length - 1]; }
  get size(): number { return this.items.length; }
}

function isValid(s: string): boolean {
  const pairs = new Map<string, string>([[")", "("], ["]", "["], ["}", "{"]]);
  const st = new Stack<string>();
  for (const ch of s) {
    const open = pairs.get(ch);
    if (open !== undefined) {
      if (st.pop() !== open) return false;
    } else st.push(ch);
  }
  return st.size === 0;
}

class MinHeap {
  private h: number[] = [];
  get size(): number { return this.h.length; }
  push(v: number): void {
    const h = this.h;
    h.push(v);
    let i = h.length - 1;
    while (i > 0) {
      const p = (i - 1) >> 1;
      if (h[p] <= h[i]) break;
      [h[p], h[i]] = [h[i], h[p]];
      i = p;
    }
  }
  pop(): number | undefined {
    const h = this.h;
    if (h.length === 0) return undefined;
    const top = h[0];
    const last = h.pop()!;
    if (h.length > 0) {
      h[0] = last;
      let i = 0;
      for (;;) {
        const l = 2 * i + 1, r = 2 * i + 2;
        let m = i;
        if (l < h.length && h[l] < h[m]) m = l;
        if (r < h.length && h[r] < h[m]) m = r;
        if (m === i) break;
        [h[m], h[i]] = [h[i], h[m]];
        i = m;
      }
    }
    return top;
  }
}

console.log(isValid("()[]{}"), isValid("([)]"));  // true false""",
            """Finish with `kthLargest` via size-k MinHeap. Then solve the
judged stack problem `valid-parentheses`.
Practice: /practice/problems/valid-parentheses""",
        ),
        (
            "ts-graphs-dp",
            "Graphs and DP: typed adjacency, memo, tables",
            "BFS/DFS/topo/DSU plus state-transition-base with strict types.",
            """**Why this matters.** Graphs (adjacency Maps, grid BFS, topo
schedules, DSU) + DP (tuple-key memo, typed tables, compression) with
strictness proving handling. `strictNullChecks` + discriminated unions
make illegal states unrepresentable — the TS superpower for algorithms.

**Graphs.** `Map<number, number[]>` adjacency (`?? []` for missing).
Grids: `number[][]` + bounds + `Set<number>` visited (encoded!) or
`boolean[][]`. BFS head-index queue (`[r, c][]` tuples); DFS recursion
(depth!) or explicit stack; colours for directed cycles; Kahn (indegree
Map + zero-queue + peel-count); DSU class (parent/rank arrays, halving).
`O(V+E)`; grids `O(R·C)`.

**DP.** Memo `Map<string, number>` (key `${i},${j}`) or `number[]?`/
`number[][]` tables with sentinel (`-1`/null-uncomputed). Bottom-up
fill order (1D asc, 2D row-major, intervals by length, subset DESC for
0/1!). Compression (rolling vars/rows/descending 1D). Types: `dp: number[]`
+ `strict` bounds (noUncheckedIndexedAccess → `??` sentinels!).

**State modelling.** Discriminated states (`type State = { tag: "idle" }
| { tag: "holding", price: number }` — stocks!) with exhaustive switches.
Tuple keys for multi-dim memo. `readonly` inputs, fresh outputs (no
aliasing bugs!).

**Common mistakes.** `!` on Map.get (handle undefined!); missing visited;
directed/undirected mixup; single-source disconnected; recursion depth;
DP base/fill/direction errors; `number[][]` ragged (validate rect!);
`infinity` sentinels in typed mins (use `Number.POSITIVE_INFINITY`
explicitly!).

**Interview angle.** "Adjacency Map + visited Set; O(V+E)." DP: "states ×
transition; strictNullChecks proves base coverage." Model types as part
of the answer (State union on the board!). TS DP should look
machine-checked — because it is.""",
            """function rob(nums: readonly number[]): number {
  let prev2 = 0, prev1 = 0;   // O(1): only two states live
  for (const x of nums) {
    const cur = Math.max(prev1, prev2 + x);
    prev2 = prev1;
    prev1 = cur;
  }
  return prev1;
}

function islands(grid: string[][]): number {
  let count = 0;
  const flood = (r: number, c: number): void => {
    if (r < 0 || c < 0 || r >= grid.length || c >= grid[r].length || grid[r][c] !== "1") return;
    grid[r][c] = "#";
    flood(r + 1, c); flood(r - 1, c); flood(r, c + 1); flood(r, c - 1);
  };
  for (let r = 0; r < grid.length; r++)
    for (let c = 0; c < grid[r].length; c++)
      if (grid[r][c] === "1") { count++; flood(r, c); }
  return count;
}

console.log(rob([2, 7, 9, 3, 1]));  // 12
console.log(islands([["1","1","0"],["1","1","0"],["0","0","1"]]));  // 2""",
            """Solve coin-change top-down (Map memo) + bottom-up. Then solve
the judged DP problem `house-robber` with rolling vars.
Practice: /practice/problems/house-robber""",
        ),
        (
            "ts-interview-mastery",
            "Google-level problem solving in TypeScript",
            "Method + strict types + runtime validation at boundaries.",
            """**Why this matters.** TS hard interviews = JS method + type
proof + boundary validation (types erase at JSON!). Clarify, brute
force, optimise, code, test — with signatures that prove contracts and
runtime checks where types cannot reach. Rehearse typed + timed.

**Five steps, TS.** (1) Clarify + nullables (`T | null`? `[]` valid?
sorted? mutate?). (2) Brute force + complexity aloud. (3) Atlas: inner
search → Map/Set; sorted pairs → pointers; window → counts; nested →
Stack<T>; levels/shortest → head-index BFS; order/connect → DFS/topo/
DSU; k-extreme → sort-vs-heap; ways/optimum → DP; boundary → binary
search on answer; choose/unchoose → backtracking. (4) Code: generics,
readonly, predicates, invariant comments. (5) Trace + null/empty/single/
dupe/unicode/max; `tsc --noEmit` zero errors; quick vitest/node:test
cases.

**Boundaries.** JSON/API/form input: `unknown` + validate (narrowing/
predicates/schema lib) — NEVER cast (`as T` lies!). `fetch` with
`AbortSignal.timeout`, `response.ok`, typed parse-or-throw. Render safe
(`textContent`). Env/config: parse + defaults + fail-fast on missing.

**Hard favourites.** Median (partition), trap-water (pointers), LRU
(Map order trick, typed!), serialize-tree (preorder + `#`), word ladder
(BFS + patterns), edit distance (2D → rolling), min-window (need/have).
Shapes + typed skeletons, not scripts.

**Common mistakes.** Silent coding; `any`/`as` lies; unvalidated
boundaries; lexical sort; `shift` queues; re-enumerated chains (TS has
no LINQ-deferral, but generator re-runs!); no `tsc` check; memorised vs
twists.

**Rehearsal.** 120+ typed + aloud + timed; `strict` + `noUncheckedIndexed
Access` always; miss-log by pattern; weekly redos; monthly LRU/trie/heap/
DSU typed from memory. Compiler-clean + tested + timed = hireable.""",
            """// Typed LRU via Map insertion order. O(1) average.
class LRUCache<K, V> {
  private map = new Map<K, V>();
  constructor(private cap: number) {
    if (cap <= 0) throw new RangeError("capacity must be positive");
  }
  get(key: K): V | undefined {
    const v = this.map.get(key);
    if (v === undefined) return undefined;
    this.map.delete(key);
    this.map.set(key, v);
    return v;
  }
  put(key: K, value: V): void {
    if (this.map.has(key)) this.map.delete(key);
    else if (this.map.size >= this.cap) {
      const lru = this.map.keys().next();
      if (!lru.done) this.map.delete(lru.value);
    }
    this.map.set(key, value);
  }
}

function editDistance(a: string, b: string): number {
  let prev = Array.from({ length: b.length + 1 }, (_, j) => j);  // rolling row
  for (let i = 1; i <= a.length; i++) {
    const cur = [i];
    for (let j = 1; j <= b.length; j++) {
      cur[j] = a[i - 1] === b[j - 1]
        ? prev[j - 1]
        : 1 + Math.min(prev[j], cur[j - 1], prev[j - 1]);
    }
    prev = cur;
  }
  return prev[b.length];
}

const c = new LRUCache<number, number>(2);
c.put(1, 1);
console.log(c.get(1), editDistance("horse", "ros"));  // 1 3""",
            """Solve min-window-substring (need/have counts, O(n)). Then
solve the judged hard DP `edit-distance` (table → rolling).
Practice: /practice/problems/edit-distance""",
        ),
    ]
}

#: Module slug -> judged problem slug for the "code what you learned" button.
MODULE_PRACTICE: dict[str, str] = {
    "js-complexity-big-o": "binary-search",
    "js-strings-arrays-deep": "reverse-words",
    "js-recursion-sorting": "merge-sorted-arrays",
    "js-maps-sets": "top-k-frequent",
    "js-trees-graphs": "bfs-grid-distance",
    "js-interview-mastery": "longest-palindromic-substring",
    "ts-complexity-big-o": "binary-search",
    "ts-collections-deep": "contains-duplicate",
    "ts-recursion-sorting": "sorted-squares",
    "ts-generics-dsa": "valid-parentheses",
    "ts-graphs-dp": "house-robber",
    "ts-interview-mastery": "edit-distance",
}

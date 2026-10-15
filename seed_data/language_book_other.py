"""Book-depth Go, Rust and SQL modules: systems DSA plus data fluency.

Go (simple, concurrent, honest errors), Rust (ownership, zero-cost, fearless
refactoring) and SQL (the data language every backend interview touches):
six modules each. Go/Rust teach DSA with systems flavour (slices/borrowing,
explicit errors, no exceptions); SQL teaches querying-to-mastery with
exercises that run in /studio plus judged transfer problems.
"""

from __future__ import annotations

BOOK_MODULES: dict[str, list[tuple]] = {
    "go": [
        (
            "go-complexity-big-o",
            "Big-O in Go: slices, maps and honest costs",
            "Growth plus append/copy/sort costs and benchmark proof.",
            """**Why this matters.** Go's simplicity makes costs visible:
`append` amortised, `copy` linear, `sort` `n log n`, map ops average
`O(1)` — but string concat loops are still quadratic and `insert-at-0`
still linear. Add `go test -bench` and you prove complexity instead of
claiming it. Interviews love the benchmark sentence.

**Growth.** `O(1)` index/map-hit, `O(log n)` halving (`sort.Search`!),
`O(n)` scans, `O(n log n)` `sort.Slice` (pattern-defeating quicksort —
fast, unstable; `sort.SliceStable` keeps order), `O(n²)` pairs. `append`
amortised `O(1)` (growth doubling); `copy`/`append(s, t...)` `O(n)`;
`string +` in loops quadratic (`strings.Builder`!); `maps` grow/rehash
(span: pre-size with `make(map[K]V, hint)`).

**Slices.** `make([]T, 0, cap)` (pre-size hot paths!); `len` vs `cap`;
slicing shares arrays (aliasing! `copy` to detach); `slices` package
(`slices.Sort`, `slices.BinarySearch`, `slices.Compact`, `slices.Clone`
— modern Go!). `for i, v := range` (value copies! index when mutating).

**Benchmarks.** `func BenchmarkX(b *testing.B) { for i := 0; i < b.N;
i++ { ... } }`, `go test -bench=. -benchmem` (allocs/op!). `b.ReportAllocs`,
`-benchtime`, `-cpuprofile`. "Benchmark says..." beats "I think...".

**Common mistakes.** `sort` without less (compile error — good! but
inconsistent less = chaos); append-aliasing (stale slices!); string
concat loops; `range` value-copy mutation (use index!); ignoring allocs
(`-benchmem`!); `interface{}` soup (generics since 1.18!).

**Interview angle.** "O(n) time, O(1) space; benchmark confirms — N=
10⁵ in Xms, Y allocs." Pre-sized maps/slices stated. Go interviewers
grade simplicity + measurement: obvious code, benchmarked claims.""",
            """package main

import (
\t"fmt"
\t"slices"
\t"time"
)

func hasDupFast(xs []int) bool {
\tseen := make(map[int]struct{}, len(xs))
\tfor _, x := range xs {
\t\tif _, ok := seen[x]; ok {
\t\t\treturn true
\t\t}
\t\tseen[x] = struct{}{}
\t}
\treturn false
}

func main() {
\tdata := make([]int, 30000)
\tfor i := range data {
\t\tdata[i] = i
\t}
\tt0 := time.Now()
\tfmt.Println(hasDupFast(data)) // false
\tfmt.Println("checked in", time.Since(t0))
\tfmt.Println(slices.IsSorted(data)) // true
\t// go test -bench=. -benchmem  <-- prove it, don't claim it
}""",
            """Write BenchmarkHasDup (fast vs includes-style) and run with
-benchmem. Then solve the judged problem `binary-search`.
Practice: /practice/problems/binary-search""",
        ),
        (
            "go-slices-maps-deep",
            "Slices and maps: two pointers, windows, counting",
            "Idiomatic containers plus the patterns that run on them.",
            """**Why this matters.** Slices + maps are 90% of Go DSA:
two-pointer string/array work, sliding windows, frequency/complement
counting. Idioms (comma-ok, zero values, `slices` package) make the
code read like Go, not translated Java.

**Slices deep.** `slices.Sort`/`BinarySearch`/`Compact`/`Reverse`/
`Clone`; `sort.Slice` with less for structs; `slices.SortFunc` +
`cmp.Compare` (modern!). Two pointers (palindrome, dedup, move-zeroes,
rotate-by-reverse, merge-from-end). Windows (last-index map, counts +
matched, shrink-while-invalid). `strings.Builder`/`[]rune` (runes for
unicode! bytes vs runes — state it).

**Maps.** `make(map[K]V, hint)`, comma-ok (`v, ok := m[k]`), zero-value
defaulting (`m[k]++` works on missing keys! — counting one-liner), `delete`,
`clear` (1.21+), iteration RANDOM order (never depend on it! sort keys
for output!). `map[T]struct{}` sets. Keys must be comparable (slices
aren't — encode!).

**Patterns.** Complement (Two Sum: check-then-set). Frequency (anagrams,
ransom, `m[k]++`). Grouping (`map[string][]string` + append — nil slice
appends fine!). Top-k (sort pairs `O(n log n)` vs `container/heap` `O(n
log k)` — implement heap.Interface, stating the trade!).

**Common mistakes.** Range-value mutation; map iteration order assumed;
concurrent map access (fatal! mutex or sync.Map); `nil` vs empty slices
(`len` works on both — usually fine, JSON differs!); slice aliasing
across appends; key slices (unhashable!).

**Interview angle.** "Map with comma-ok: O(n) avg, O(n) space; zero-value
counting." Runes for unicode stated. Go map/set code should look boring
— `m[k]++`, comma-ok, done. Simplicity is the flex.""",
            """package main

import "fmt"

func twoSum(nums []int, target int) []int {
\tseen := make(map[int]int, len(nums))
\tfor i, x := range nums {
\t\tif j, ok := seen[target-x]; ok {
\t\t\treturn []int{j, i}
\t\t}
\t\tseen[x] = i
\t}
\treturn nil
}

func isAnagram(s, t string) bool {
\tif len(s) != len(t) {
\t\treturn false
\t}
\tcount := make(map[rune]int, len(s))
\tfor _, r := range s {
\t\tcount[r]++
\t}
\tfor _, r := range t {
\t\tcount[r]--
\t\tif count[r] < 0 {
\t\t\treturn false
\t\t}
\t}
\treturn true
}

func main() {
\tfmt.Println(twoSum([]int{2, 7, 11, 15}, 9)) // [0 1]
\tfmt.Println(isAnagram("anagram", "nagaram"))   // true
}""",
            """Solve group-anagrams (sorted-key map). Then solve the judged
complement problem `two-sum`.
Practice: /practice/problems/two-sum""",
        ),
        (
            "go-recursion-sorting",
            "Recursion and sorting: memo, search, ordering",
            "Base cases with map memo, sort.Search, and merge discipline.",
            """**Why this matters.** Recursion (trees, backtracking, top-down
DP) with map memo + sorting (`slices.Sort`, `sort.Search`, comparators)
+ merge. Go's explicit errors shape DP APIs (`(int, error)` vs panics —
choose and defend!). Goroutines are NOT for recursion parallelism here
(state why: overhead > gain at interview scale).

**Recursion.** Base + progress + trust. Memo `map[int]int` / `[][]int`
sentinels; fib `O(φⁿ)`→`O(n)`. Backtracking: shared path + append/
explore/truncate (`path = path[:len(path)-1]`); subsets/permutations/
combinations; prune. Depth = height/chain (goroutine stacks grow — 1GB
max default — but deep chains still smell; iterate when linear!).

**Sorting/searching.** `slices.Sort` (numbers), `sort.Slice` + less
(structs), `slices.SortFunc` + `cmp.Or` multi-key (modern!), `sort.Search`
(binary search on predicate — first-true!): `sort.Search(n, func(i int)
bool { return a[i] >= x })` (lower bound one-liner!). Merge-two-sorted
by hand. Search-on-answer (koko/capacity — monotone predicate + `sort.
Search` on answer range!).

**Errors.** `(T, error)` returns; `fmt.Errorf("...: %w", err)` wrap;
sentinel errors (`var ErrX = errors.New`) + `errors.Is`; `panic` only
for impossible (programmer error!). Algorithm bugs → error values or
test failures, never silent.

**Common mistakes.** No memo; inconsistent less (sort chaos!); mutating
inputs (Clone first!); `sort.Search` predicate flipped (first-TRUE!);
recursion where iteration fits; error swallowed (`_ =`); goroutine-per-
item (spawn cost!).

**Interview angle.** "Memo map: O(states); sort.Search for the bound."
Errors explicit in signature. Go recursion should look plain — plain is
correct, clever is suspicious. State depth bounds.""",
            """package main

import (
\t"fmt"
\t"sort"
)

var memo = map[int]int{}

func fib(n int) int {
\tif n < 2 {
\t\treturn n
\t}
\tif v, ok := memo[n]; ok {
\t\treturn v
\t}
\tv := fib(n-1) + fib(n-2)
\tmemo[n] = v
\treturn v
}

func lowerBound(a []int, x int) int {
\treturn sort.Search(len(a), func(i int) bool { return a[i] >= x })
}

func main() {
\tfmt.Println(fib(50))                    // 12586269025
\tfmt.Println(lowerBound([]int{1, 2, 4, 4, 5}, 4)) // 2
}""",
            """Write merge-two-sorted + table tests (`[]struct` cases). Then
solve the judged recurrence `climb-stairs`.
Practice: /practice/problems/climb-stairs""",
        ),
        (
            "go-stacks-queues",
            "Stacks, queues and heaps: adapters plus container/heap",
            "Slice adapters, monotonic discipline, and heap.Interface.",
            """**Why this matters.** Go has no built-in stack/queue/heap —
slice adapters + `container/heap` (you implement `heap.Interface`!).
That ceremony teaches the invariants; monotonic stacks and BFS queues
complete the toolkit. Interviews accept adapters with clean APIs.

**Adapters.** Stack: `[]T` + push/pop (pop: `n := len(s)-1; v := s[n];
s = s[:n]`). Queue: slice + head index (no O(n) shifts!) or `container/
list` (pointer-chasing — slice+head usually wins). Clear names (`type
Stack []int` + methods) beat raw slices in interviews.

**Monotonic stacks.** Indices + decreasing values: next-greater,
temperatures, spans, rectangles — `O(n)`. Valid-parens via map pairs +
stack. Min-stack (value,min pairs). RPN eval (stack machine!). Each: pop
condition + what the survivor means.

**container/heap.** Implement `Len/Less/Swap/Push/Pop` on your slice;
`heap.Init/Push/Pop` drive it. Top-k `O(n log k)`, merge-k-lists, median
(two heaps). Ceremony, but explicit — very Go. (Or `slices.Sort` + slice
for one-shot top-k — state the trade!)

**Common mistakes.** Pop from empty (guard!); `s = s[1:]` queues (memory
leak by reslicing — head index + periodic compact, or ring!); heap Less
flipped; `heap.Pop` vs slice pop confusion (use heap.*!); copying locks
(no locks here — but don't copy heaps mid-use!).

**Interview angle.** "Slice-backed stack, O(1) amortised; monotonic
gives O(n)." Heap: "heap.Interface, O(log n) ops." Write the adapter
(5 lines) instead of apologising for no stdlib — Go interviewers respect
the 5 lines.""",
            """package main

import (
\t"container/heap"
\t"fmt"
)

type IntHeap []int

func (h IntHeap) Len() int            { return len(h) }
func (h IntHeap) Less(i, j int) bool  { return h[i] < h[j] }
func (h IntHeap) Swap(i, j int)       { h[i], h[j] = h[j], h[i] }
func (h *IntHeap) Push(x any)         { *h = append(*h, x.(int)) }
func (h *IntHeap) Pop() any {
\told := *h
\tn := len(old)
\tv := old[n-1]
\t*h = old[:n-1]
\treturn v
}

func isValid(s string) bool {
\tpairs := map[rune]rune{')': '(', ']': '[', '}': '{'}
\tvar st []rune
\tfor _, ch := range s {
\t\tif open, ok := pairs[ch]; ok {
\t\t\tif len(st) == 0 || st[len(st)-1] != open {
\t\t\t\treturn false
\t\t\t}
\t\t\tst = st[:len(st)-1]
\t\t} else {
\t\t\tst = append(st, ch)
\t\t}
\t}
\treturn len(st) == 0
}

func main() {
\th := &IntHeap{3, 1, 2}
\theap.Init(h)
\tfmt.Println(heap.Pop(h))          // 1
\tfmt.Println(isValid("()[]{}"), isValid("([)]")) // true false
}""",
            """Solve daily-temperatures (monotonic, O(n)). Then solve the
judged stack problem `valid-parentheses`.
Practice: /practice/problems/valid-parentheses""",
        ),
        (
            "go-trees-graphs",
            "Trees and graphs: pointers, BFS, components",
            "Struct nodes, level order, floods and shortest paths.",
            """**Why this matters.** Trees (pointers + nil!) + graphs
(adjacency maps, grid BFS, topo, DSU) in plain Go: structs, slices,
head-index queues, visited sets. Nil-handling is the Go tax — pay it
gladly (every deref guarded!).

**Trees.** `type Node struct { Val int; Left, Right *Node }` — nil =
empty (check before deref, always!). Preorder/inorder/postorder; level
order (head-index queue); depth; symmetry; BST validate (min/max);
kth inorder-count. Build-from-slice helpers in tests. Iterative with
explicit stacks when depth threatens.

**Graphs.** `map[int][]int` adjacency (comma-ok neighbors!); grids
implicit (bounds + `map[[2]int]bool` or `[][]bool` visited); edge lists
for DSU. BFS head-index queue: shortest unweighted, levels, multi-
source. DFS: connectivity, floods, colours cycle-detect, topo finish-
order. `O(V+E)`; grids `O(R·C)`.

**DSU/topo.** DSU slices (parent/rank, halving find). Kahn (indegree map
+ zero-queue + peel-count). Provinces, redundant edges, course orders —
same shapes, Go spelling.

**Common mistakes.** Nil deref (guard every Left/Right!); value-receiver
mutation (pointer receivers for mutating methods!); queue reslice leak;
no visited; directed/undirected mixup; single-source disconnected;
recursion depth on huge grids (explicit stack!).

**Interview angle.** "Nil-checked recursion; BFS shortest unweighted."
Pointer-vs-value receivers stated. Go graph code: maps + slices +
head-index queues — boring, correct, fast. Nil discipline said once
shows systems maturity.""",
            """package main

import "fmt"

type Node struct {
\tVal         int
\tLeft, Right *Node
}

func maxDepth(root *Node) int {
\tif root == nil {
\t\treturn 0
\t}
\tl, r := maxDepth(root.Left), maxDepth(root.Right)
\tif l > r {
\t\treturn l + 1
\t}
\treturn r + 1
}

func oranges(grid [][]int) int {
\trows, cols := len(grid), len(grid[0])
\ttype cell struct{ r, c int }
\tq := []cell{}
\tfresh := 0
\tfor r := range grid {
\t\tfor c := range grid[r] {
\t\t\tif grid[r][c] == 2 {
\t\t\t\tq = append(q, cell{r, c})
\t\t\t} else if grid[r][c] == 1 {
\t\t\t\tfresh++
\t\t\t}
\t\t}
\t}
\tminutes := 0
\tdirs := [][2]int{{1, 0}, {-1, 0}, {0, 1}, {0, -1}}
\tfor head := 0; head < len(q) && fresh > 0; {
\t\tminutes++
\t\tfor n := len(q) - head; n > 0; n-- {
\t\t\tcur := q[head]
\t\t\thead++
\t\t\tfor _, d := range dirs {
\t\t\t\tnr, nc := cur.r+d[0], cur.c+d[1]
\t\t\t\tif nr >= 0 && nr < rows && nc >= 0 && nc < cols && grid[nr][nc] == 1 {
\t\t\t\t\tgrid[nr][nc] = 2
\t\t\t\t\tfresh--
\t\t\t\t\tq = append(q, cell{nr, nc})
\t\t\t\t}
\t\t\t}
\t\t}
\t}
\tif fresh > 0 {
\t\treturn -1
\t}
\treturn minutes
}

func main() {
\troot := &Node{Val: 1, Left: &Node{Val: 2}}
\tfmt.Println(maxDepth(root)) // 2
}""",
            """Count islands (flood + mark). Then solve the judged tree
problem `max-depth-binary-tree`.
Practice: /practice/problems/max-depth-binary-tree""",
        ),
        (
            "go-interview-mastery",
            "Google-level problem solving in Go",
            "Method + benchmarks + table tests, timed and aloud.",
            """**Why this matters.** Go interviews prize simplicity that
scales: clarify, brute force, optimise, code, test — with table-driven
tests, benchmarks, and explicit errors. "Obvious code, measured claims"
is the Go hiring bar. Rehearse the loop until boring.

**Five steps, Go.** (1) Clarify: examples, sizes, sorted?, mutate?, nil/
empty?, concurrency needed? (usually no!). (2) Brute force + complexity
aloud. (3) Atlas: inner search → map; sorted pairs → pointers; window →
counts; nested → slice-stack; levels/shortest → head-index BFS; order/
connect → DFS/topo/DSU; k-extreme → sort-vs-heap (state!); ways/optimum
→ DP; boundary → sort.Search on answer; choose/unchoose → backtracking.
(4) Code: small funcs, comma-ok, named types, invariant comments. (5)
Table tests (`[]struct{ in; want }` + `t.Run`) + nil/empty/single/max;
`go vet`, `gofmt`, benchmark the hot one.

**Engineering axis.** `gofmt` clean; `go vet` zero; errors wrapped (`%w`);
no goroutines unless asked (say why!); context for cancellation (mention
in system-y follow-ups); `slices`/`maps` packages modern. "Production"
follow-ups grade this.

**Hard favourites.** Median (partition), trap-water (pointers), LRU
(`container/list` + map — the Go LRU!), serialize-tree, word ladder,
min-window (need/have), edit distance (rolling). Shapes + table tests,
not scripts.

**Common mistakes.** Silent coding; cleverness over clarity; goroutines
for DSA (overhead!); nil deref; swallowed errors; no tests; memorised
vs twists; unfmt'd code (gofmt is free — run it!).

**Rehearsal.** 120+ aloud-timed with table tests; miss-log by pattern;
weekly redos; monthly LRU/trie/heap/DSU from memory; benchmark one hot
path weekly. Boring-correct + measured = hired.""",
            """package main

import "fmt"

// Two pointers: trap rain water, O(n) time, O(1) space.
func trap(height []int) int {
\tleft, right := 0, len(height)-1
\tleftMax, rightMax, water := 0, 0, 0
\tfor left < right {
\t\tif height[left] < height[right] {
\t\t\tif height[left] >= leftMax {
\t\t\t\tleftMax = height[left]
\t\t\t} else {
\t\t\t\twater += leftMax - height[left]
\t\t\t}
\t\t\tleft++
\t\t} else {
\t\t\tif height[right] >= rightMax {
\t\t\t\trightMax = height[right]
\t\t\t} else {
\t\t\t\twater += rightMax - height[right]
\t\t\t}
\t\t\tright--
\t\t}
\t}
\treturn water
}

func main() {
\tfmt.Println(trap([]int{0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1})) // 6
\t// Table test + BenchmarkTrap live in trap_test.go — write them.
}""",
            """Implement LRU (list+map) with table tests. Then solve the
judged hard problem `container-most-water` (two pointers, O(n)).
Practice: /practice/problems/container-most-water""",
        ),
    ],
    "rust": [
        (
            "rust-complexity-big-o",
            "Big-O in Rust: ownership meets growth",
            "Complexity plus borrow/clone costs and criterion proof.",
            """**Why this matters.** Rust's ownership makes costs explicit:
`clone()` is linear (visible!), borrowing is free, `Vec::push`
amortised, `HashMap` average O(1) — but SipHash default is slow-ish
(mention `ahash`/`FxHashMap` for hot paths!). Add `cargo bench`/
criterion and claims become measurements.

**Growth.** `O(1)` index (bounds-checked — panic on OOB, or `get` for
Option!)/map-hit, `O(log n)` halving (`binary_search`/`partition_point`!),
`O(n)` scans, `O(n log n)` `sort_unstable` (fast, unstable) vs `sort`
(stable merge), `O(n²)` pairs. `push` amortised `O(1)`; `insert(0)`/
`remove(0)` `O(n)` (`VecDeque` for queues!); `contains` `O(n)`; `HashMap/
HashSet` avg `O(1)`; string `+` in loops quadratic (`push_str`!).

**Ownership costs.** Borrow (`&`) = free; `clone()` = deep copy (linear
— grep clones in hot code!); `Copy` types (ints, chars, small) move free;
`to_vec`/`to_string`/`to_owned` copy (fine at boundaries, audit in
loops!). `with_capacity` pre-size (Vec + `HashMap::with_capacity`!).

**Benchmarks.** `cargo bench` (criterion): black_box inputs, compare
impls, allocs via dhat/heaptrack (mention). "Criterion says 1.2µs" >
"I think it's fast".

**Common mistakes.** Hidden clones (`.to_vec()` chains!); `sort` vs
`sort_unstable` unchosen (state!); `remove(0)` queues (VecDeque!);
fighting the borrow checker with clones (restructure: indices > refs!);
`unwrap` in libs (return Result!); `HashMap` iteration order assumed.

**Interview angle.** "O(n) time, O(n) space; one clone at the boundary,
borrows inside." Indices-over-refs for graph/DP code (say it upfront —
every Rust interviewer nods). Measured claims, zero-cost idioms.""",
            """use std::collections::HashSet;
use std::time::Instant;

fn has_dup_fast(xs: &[i32]) -> bool {
    let mut seen = HashSet::with_capacity(xs.len());
    for &x in xs {
        if !seen.insert(x) {
            return true;
        }
    }
    false
}

fn main() {
    let data: Vec<i32> = (0..30000).collect();
    let t0 = Instant::now();
    println!("{}", has_dup_fast(&data)); // false
    println!("checked in {:?}", t0.elapsed());
    let mut v = vec![10, 9, 80];
    v.sort_unstable();
    println!("{:?}", v); // [9, 10, 80]
}""",
            """Benchmark sort vs sort_unstable (criterion or Instant loop).
Then solve the judged problem `binary-search`.
Practice: /practice/problems/binary-search""",
        ),
        (
            "rust-strings-vec-deep",
            "Strings, Vec and text patterns: bytes, chars, windows",
            "UTF-8 honesty plus two pointers and in-place invariants.",
            """**Why this matters.** Rust strings are UTF-8 (`String` owned,
`&str` borrowed; byte-indexing panics on boundaries!). Text patterns
need the bytes-vs-chars decision upfront; Vec in-place work needs the
read/write invariant. State both, always.

**Strings.** `&str` (borrowed slice) vs `String` (owned, growable);
`.chars()` (unicode scalar) vs `.bytes()` (ASCII-fast!); `s[i]` doesn't
exist (slicing `&s[a..b]` panics on non-boundaries — `get` for safety!).
ASCII problems: bytes (`s.as_bytes()`, `b'a'` literals). Unicode: chars
+ awareness (graphemes need crates — mention!). Build: `push_str`/`+`
(move semantics!) or `Vec<char>` + `collect::<String>()`.

**Vec.** `push/pop` `O(1)`; `insert/remove(0)` `O(n)` (VecDeque!);
`sort/sort_unstable`, `binary_search` (Ok(idx)/Err(pos)!), `dedup`,
`retain`, `swap_remove` (`O(1)` unordered removal!); `with_capacity`;
`split_off`/`drain`. Destructuring swaps (`std::mem::swap(&mut a, &mut
b)` — borrowck-safe!).

**Patterns.** Palindrome (chars collect + indices, or bytes for ASCII).
Window + last-index map (longest unique). Anagram (sort key or 26-array/
HashMap counts). In-place: read/write indices, reverse segments,
end-merge. Invariant comments (borrowck-friendly indices!).

**Common mistakes.** Byte-slicing unicode (panic!); `s[i]` (doesn't
exist!); char-vs-byte len confusion; `collect` clones in loops; fighting
borrows with `clone` (indices!); `String` where `&str` suffices (API
ergonomics — accept `&str`, store `String`!).

**Interview angle.** "ASCII → bytes O(1) each; unicode → chars, noted."
Indices over references (borrowck + cache!). Rust text code should show
the UTF-8 decision in line one — interviewers check it first.""",
            """use std::collections::HashMap;

fn is_anagram(s: &str, t: &str) -> bool {
    if s.len() != t.len() {
        return false;
    }
    let mut count = HashMap::new(); // byte -> balance (ASCII fast path)
    for &b in s.as_bytes() {
        *count.entry(b).or_insert(0) += 1;
    }
    for &b in t.as_bytes() {
        let e = count.entry(b).or_insert(0);
        *e -= 1;
        if *e < 0 {
            return false;
        }
    }
    true
}

fn move_zeroes(nums: &mut Vec<i32>) {
    let mut w = 0; // write-invariant: [..w] settled non-zero
    for r in 0..nums.len() {
        if nums[r] != 0 {
            nums.swap(w, r);
            w += 1;
        }
    }
}

fn main() {
    println!("{}", is_anagram("anagram", "nagaram")); // true
    let mut v = vec![0, 1, 0, 3, 12];
    move_zeroes(&mut v);
    println!("{:?}", v); // [1, 3, 12, 0, 0]
}""",
            """Write longest-unique (bytes + last-index array, O(n)). Then
solve the judged counting problem `valid-anagram`.
Practice: /practice/problems/valid-anagram""",
        ),
        (
            "rust-recursion-sorting",
            "Recursion and sorting: memo, partition_point, merge",
            "Base cases with HashMap memo, and ordering with comparators.",
            """**Why this matters.** Recursion (trees need Box/Rc — the
ownership lesson!, backtracking, top-down DP) + sorting (`sort_by`,
`partition_point` binary search, merge). Rust recursion teaches ownership:
Box for trees, indices for graphs, slices for divide-and-conquer.

**Recursion.** Base + progress + trust. Memo `HashMap<Key, Val>` / `vec![-1; n]`;
fib `O(φⁿ)`→`O(n)`. Backtracking: `&mut Vec<T>` path + push/explore/pop;
subsets/perms/combos; prune. Divide-and-conquer on slices (`&[T]` splits
borrowck-clean!). Depth = height/chain (stack 8MB default — deep chains
overflow; iterate!).

**Trees + ownership.** `Box<Node>` (owned children!) or arena (`Vec<Node>`
+ indices — borrowck-free graphs!): `struct Node { val: i32, left: Option<Box<Node>>,
right: Option<Box<Node>> }`. Pattern-match (`if let Some(n) = &node.left`).
Rc<RefCell<>> for shared (mention cost!). Arena-indices for interview graphs
(state the choice!).

**Sorting/searching.** `sort/sort_unstable`, `sort_by(|a, b| a.cmp(b))`,
`sort_by_key`, `partition_point(|x| *x < target)` (lower bound!),
`binary_search` (Ok/Err). Merge-two-sorted (slices in, Vec out). Search-on-
answer (monotone + partition_point on answer range!).

**Common mistakes.** No memo; Box/RefCell overkill (arena!); `sort`
confusion (state stable/unstable!); cloning to please borrowck (indices/
slices!); recursion depth; `RefCell` borrow panics (runtime!).

**Interview angle.** "Arena indices: O(states), no borrow fights."
`partition_point` for bounds (idiomatic!). Rust recursion answers should
name the ownership strategy first (Box/arena/slices) — that IS the design.""",
            """use std::collections::HashMap;

fn fib(n: u64, memo: &mut HashMap<u64, u64>) -> u64 {
    if n < 2 {
        return n;
    }
    if let Some(&v) = memo.get(&n) {
        return v;
    }
    let v = fib(n - 1, memo) + fib(n - 2, memo);
    memo.insert(n, v);
    v
}

fn lower_bound(a: &[i32], x: i32) -> usize {
    a.partition_point(|&v| v < x) // first index where predicate fails
}

fn main() {
    println!("{}", fib(50, &mut HashMap::new())); // 12586269025
    println!("{}", lower_bound(&[1, 2, 4, 4, 5], 4)); // 2
}""",
            """Write merge-two-sorted on slices. Then solve the judged
search-on-answer problem `koko-eating-bananas`.
Practice: /practice/problems/koko-eating-bananas""",
        ),
        (
            "rust-hash-collections",
            "HashMap, HashSet and counting patterns",
            "Entry API, custom keys, and top-k with BinaryHeap.",
            """**Why this matters.** `HashMap`/`HashSet` + the `entry` API
(`or_insert`, `and_modify`) make counting idiomatic; custom-hashable
keys + `BinaryHeap` (max-heap; `Reverse` for min!) complete top-k.
Ownership shapes every pattern (owned keys, borrowed lookups!).

**Entry API.** `*m.entry(k).or_insert(0) += 1` (counting one-liner!);
`or_insert_with(Vec::new).push(x)` (grouping!); `and_modify(|c| *c += 1).
or_insert(1)`. Lookups borrow (`m.get(&k)` — no clone for queries!).
Keys owned (`String`/tuples/arrays — `Copy` scalars cheapest!).

**Sets.** `insert` returns false-if-present (dup detect!); `contains`;
difference/intersection/union iterators (set algebra, lazy!); `BTreeMap/
BTreeSet` for ORDERED (range queries! `O(log n)` + iteration sorted —
state when order matters!).

**Patterns.** Complement (Two Sum: check-then-insert). Frequency
(anagrams, entry counting). Grouping (entry-vec). Top-k: `BinaryHeap`
(`O(n log k)` with size-k min via `Reverse`!) vs sort-slice (`O(n log
n)` — state!). Prefix-sum map (subarray-sum-k — the advanced counting!).

**Hashers.** Default SipHash (DoS-safe, slower); hot paths: `ahash`/
`FxHashMap` (state the trade: speed vs DoS-resistance!). `HashMap::with_
capacity` pre-size. Iteration order RANDOM (sort for output!).

**Common mistakes.** Cloning keys for lookups (borrow!); `m[k]` (panics
— `get`!); entry borrow conflicts (compute key first!); `BinaryHeap` max
confusion (`Reverse` for min!); order assumed (BTree or sort!); SipHash
hot-loop blindness (measure!).

**Interview angle.** "Entry API, O(n) avg; owned keys, borrowed queries."
Top-k: "BinaryHeap<Reverse> O(n log k)." Hasher + capacity stated. Rust
hashing code should read clone-free in the hot loop — interviewers grep
mentally.""",
            """use std::collections::{BinaryHeap, HashMap};
use std::cmp::Reverse;

fn top_k_frequent(nums: Vec<i32>, k: usize) -> Vec<i32> {
    let mut freq = HashMap::with_capacity(nums.len());
    for x in nums {
        *freq.entry(x).or_insert(0) += 1;
    }
    let mut heap = BinaryHeap::with_capacity(k + 1); // max-heap of Reverse = min-heap
    for (x, c) in freq {
        heap.push((Reverse(c), x));
        if heap.len() > k {
            heap.pop();
        }
    }
    heap.into_iter().map(|(_, x)| x).collect()
}

fn main() {
    let mut ans = top_k_frequent(vec![1, 1, 1, 2, 2, 3], 2);
    ans.sort_unstable();
    println!("{:?}", ans); // [1, 2]
}""",
            """Solve subarray-sum-equals-k (prefix map, O(n)). Then solve the
judged prefix problem of the same name.
Practice: /practice/problems/subarray-sum-equals-k""",
        ),
        (
            "rust-graphs-dp",
            "Graphs and DP: arenas, VecDeque BFS, tables",
            "Borrowck-free graphs (indices!) plus memo and compression.",
            """**Why this matters.** Rust graphs done right = arena indices
(`Vec<Node>` + `usize`), never reference spaghetti. BFS via `VecDeque`,
DP via tables/memo with rolling compression. Ownership strategy stated
first — that sentence is half the Rust interview.

**Arenas.** `struct Graph { adj: Vec<Vec<usize>> }` — indices, not refs!
Grids: `Vec<Vec<u8>>`/`Vec<i32>` flat (`r * c + c`!) + `vec![false; n]`
visited or bitset. No lifetimes, no RefCell, cache-friendly. Say "arena"
and interviewers relax.

**BFS/DFS.** `VecDeque<usize>` (+`push_back`/`pop_front` `O(1)`!); layer
loops; multi-source; distances `vec![-1; n]`. DFS recursion (depth!) or
explicit `Vec` stack; colours for directed cycles; Kahn (indegree vec +
VecDeque + peel-count); DSU (parent/rank vecs, halving). `O(V+E)`.

**DP.** Memo `HashMap<(usize, usize), i64>` (tuple keys!) or `vec![-1;
n]`/`vec![vec![0; m]; n]` sentinels. Bottom-up fill (1D asc, 2D
row-major, intervals by length, 0/1 DESC!). Compression (rolling vars/
rows/descending 1D). `i64` for sums (overflow panics in debug — choose
widths deliberately!).

**Common mistakes.** RefCell graphs (arena!); `Rc` cycles (Weak or arena!);
`pop_front` on Vec (`O(n)` — VecDeque!); missing visited; directed/
undirected mixup; `usize` underflow (`i - 1` at 0 panics in debug —
guard!); `i32` overflow (widen!); DP direction errors.

**Interview angle.** "Arena + VecDeque: O(V+E), zero borrow issues."
DP: "states × transition, O(X) compressed." Width/overflow stated
(`i64`, `saturating_*` where apt). Rust graph/DP code: indices
everywhere, clones nowhere — that's the look.""",
            """use std::collections::VecDeque;

fn num_islands(mut grid: Vec<Vec<char>>) -> i32 {
    let rows = grid.len();
    let cols = grid[0].len();
    let mut count = 0;
    for r in 0..rows {
        for c in 0..cols {
            if grid[r][c] != '1' {
                continue;
            }
            count += 1;
            let mut q = VecDeque::from([(r, c)]);
            grid[r][c] = '#';
            while let Some((cr, cc)) = q.pop_front() {
                for (dr, dc) in [(1, 0), (-1, 0), (0, 1), (0, -1)] {
                    let nr = cr as i32 + dr;
                    let nc = cc as i32 + dc;
                    if nr >= 0 && nr < rows as i32 && nc >= 0 && nc < cols as i32 {
                        let (ur, uc) = (nr as usize, nc as usize);
                        if grid[ur][uc] == '1' {
                            grid[ur][uc] = '#';
                            q.push_back((ur, uc));
                        }
                    }
                }
            }
        }
    }
    count
}

fn unique_paths(m: usize, n: usize) -> i32 {
    let mut dp = vec![1; n]; // rolling row, O(n) space
    for _ in 1..m {
        for j in 1..n {
            dp[j] += dp[j - 1];
        }
    }
    dp[n - 1]
}

fn main() {
    let g = vec![vec!['1', '1', '0'], vec!['1', '1', '0'], vec!['0', '0', '1']];
    println!("{} {}", num_islands(g), unique_paths(3, 7)); // 2 28
}""",
            """Solve rotting-oranges (multi-source + fresh count). Then solve
the judged grid DP `unique-paths`.
Practice: /practice/problems/unique-paths""",
        ),
        (
            "rust-interview-mastery",
            "Google-level problem solving in Rust",
            "Method + ownership design + clippy-clean code, timed.",
            """**Why this matters.** Rust interviews test algorithms THROUGH
ownership: arena-vs-Box-vs-slices decisions, clone-free hot loops,
`Result` discipline, clippy-clean idioms — plus the five-step method
aloud. Design sentence first, code second, `cargo clippy` third.

**Five steps, Rust.** (1) Clarify + ownership sketch (arena? Box? slices?
widths? empty/invalid?). (2) Brute force + complexity aloud. (3) Atlas:
inner search → HashMap/entry; sorted pairs → pointers; window → counts;
nested → Vec-stack; levels/shortest → VecDeque BFS; order/connect →
DFS/topo/DSU (arenas!); k-extreme → BinaryHeap<Reverse>/sort (state!);
ways/optimum → DP; boundary → partition_point on answer; choose/unchoose
→ backtracking (`&mut Vec` path). (4) Code: indices, entry API,
`?` errors, invariant comments. (5) Trace + empty/single/unicode(u!)/max/
overflow; `cargo test`, `cargo clippy -- -D warnings`, benchmark hot.

**API design.** Accept borrowed (`&[T]`, `&str`), return owned; `Option`
for absent, `Result` for fallible (never `unwrap` in libs!); `thiserror`/
`anyhow` in real code (mention!); `#[must_use]` pure helpers; docs with
`///` + doctests (they RUN — write them!).

**Hard favourites.** Median (partition), trap-water (pointers), LRU
(`HashMap` + `LinkedList`? — or `indexmap`/`lru` crates: implement with
HashMap+Vec-arena + free-list, state!; `std::collections::LinkedList`
exists but O(n) touch — discuss!), serialize-tree (preorder + `#`),
word ladder (BFS + patterns), min-window (need/have arrays), edit
distance (rolling). Shapes + ownership plans.

**Common mistakes.** Silent coding; clone-soup; RefCell graphs; `unwrap`
libs; `LinkedList` misuse (discuss, don't default!); no clippy; memorised
vs twists; `usize` underflow; width blindness.

**Rehearsal.** 120+ aloud-timed, clippy-clean; miss-log by pattern;
weekly redos; monthly LRU/trie/BinaryHeap/DSU from memory (arenas!). Ownership sentence first, every time.""",
            """use std::collections::HashMap;

// Expand-around-center: longest palindromic substring, O(n^2)/O(1).
fn longest_palindrome(s: &str) -> &str {
    let b = s.as_bytes(); // ASCII lens; chars for unicode (state it!)
    let (n, mut best) = (b.len(), (0, 0));
    let expand = |mut l: isize, mut r: isize| -> (usize, usize) {
        while l >= 0 && r < n as isize && b[l as usize] == b[r as usize] {
            l -= 1;
            r += 1;
        }
        ((l + 1) as usize, r as usize)
    };
    for i in 0..n {
        for (l, r) in [expand(i as isize, i as isize), expand(i as isize, i as isize + 1)] {
            if r - l > best.1 - best.0 {
                best = (l, r);
            }
        }
    }
    &s[best.0..best.1]
}

fn main() {
    println!("{}", longest_palindrome("babad")); // bab (or aba)
    let _freq: HashMap<u8, usize> = HashMap::new(); // entry API lives here
}""",
            """Solve min-window-substring (need/have, O(n)). Then solve the
judged hard window `minimum-window-substring`.
Practice: /practice/problems/minimum-window-substring""",
        ),
    ],
    "sql": [
        (
            "sql-subqueries-cte",
            "Subqueries and CTEs: structure any question",
            "WITH-first thinking: build complex answers from named steps.",
            """**Why this matters.** Real interview SQL (FAANG data/backend)
is multi-step: filter → aggregate → rank → join. CTEs (`WITH x AS (...)`)
turn that into readable named steps; subqueries (scalar/IN/EXISTS/
derived) handle the rest. "CTE-first" is the professional default.

**WITH.** `WITH filtered AS (SELECT ... WHERE ...), ranked AS (SELECT
..., ROW_NUMBER() OVER (...) rn FROM filtered) SELECT ... FROM ranked
WHERE rn = 1;` — comma-separated, referenced later/once, readable top-
down. Prefer CTEs over nesting (reviewers + interviewers agree!).

**Subqueries.** Scalar (`WHERE salary > (SELECT AVG(salary) FROM emp)` —
one value!); `IN` (membership — NULL trap: `NOT IN` with NULLs returns
NOTHING! use `NOT EXISTS`!); `EXISTS` (correlated semi-join — fastest
pattern!); derived tables (`FROM (...) t` — needs alias!); `ANY/ALL`.

**Correlated.** Inner references outer (`WHERE salary > (SELECT AVG...
WHERE dept = e.dept)` — per-row!): powerful, sometimes slow (rewrite as
join/group when hot). `EXISTS` corrrectness > cleverness.

**Set ops.** `UNION` (dedup!) vs `UNION ALL` (fast, keeps dupes — default
unless dedup needed!); `INTERSECT`/`EXCEPT` (portable-ish; MySQL lacks —
rewrite as joins!). Column count/types must match.

**Common mistakes.** `NOT IN` + NULLs (empty result! — NOT EXISTS!);
`=` with multi-row subquery (IN!); missing derived alias; CTE referenced
twice (recomputed — temp table if huge!); `SELECT *` in EXISTS (fine —
`SELECT 1`, style!); deep nesting (flatten to CTEs!).

**Interview angle.** "WITH steps: filter, aggregate, rank, pick."
EXISTS over IN for anti-joins. NULL-trap awareness said once = senior
signal. Run every query in /studio before claiming it works.""",
            """-- Second-highest salary per department (CTE + window).
WITH ranked AS (
    SELECT dept_id, salary,
           DENSE_RANK() OVER (PARTITION BY dept_id ORDER BY salary DESC) AS rnk
    FROM employees
)
SELECT dept_id, salary
FROM ranked
WHERE rnk = 2;

-- Anti-join done right: customers with NO orders (NOT EXISTS, NULL-safe).
SELECT c.id, c.name
FROM customers c
WHERE NOT EXISTS (
    SELECT 1 FROM orders o WHERE o.customer_id = c.id
);""",
            """In /studio: top-3 salaries per dept (CTE + DENSE_RANK). Then
solve the judged aggregation-thinking problem `mean-median-mode`
(same grouping logic, Python-side).
Practice: /practice/problems/mean-median-mode""",
        ),
        (
            "sql-window-functions",
            "Window functions: ROW_NUMBER, RANK, running totals",
            "OVER/PARTITION/ORDER/FRAME — analytics without self-joins.",
            """**Why this matters.** Windows answer "top-N per group",
"running total", "previous row", "percent of total" — the daily analytics
set — without self-joins. `OVER (PARTITION BY ... ORDER BY ... ROWS ...)`.
FAANG SQL screens are ~50% windows.

**Core.** `ROW_NUMBER()` (unique 1..n — dedup/top-1!), `RANK()` (gaps:
1,2,2,4), `DENSE_RANK()` (no gaps: 1,2,2,3 — top-N WITH ties!), `LAG/LEAD`
(prev/next row — deltas! `value - LAG(value) OVER (ORDER BY t)`), `SUM/
AVG/COUNT OVER` (running: `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT
ROW` — default with ORDER BY is RANGE, differs with ties!).

**Frames.** `ROWS` (physical) vs `RANGE` (logical/peers!) — with ORDER BY
+ ties they differ (classic trap!). `ROWS BETWEEN 6 PRECEDING AND CURRENT
ROW` (7-day moving!). `UNBOUNDED PRECEDING/FOLLOWING`, `CURRENT ROW`.
Explicit frames = senior.

**PARTITION.** `PARTITION BY dept` (per-group numbering!) + `ORDER BY
salary DESC` (rank within!). Multiple windows, one pass. `FILTER (WHERE
...)` for conditional aggregates (Postgres!); `CASE` inside aggregate
(portable!).

**Nesting.** Windows can't nest directly / can't appear in WHERE (compute
in CTE, filter outside!): `WITH r AS (SELECT ..., ROW_NUMBER() OVER ...
rn FROM t) SELECT * FROM r WHERE rn <= 3;` — the pattern.

**Common mistakes.** WHERE on window (CTE first!); RANK vs DENSE_RANK vs
ROW_NUMBER mixed (ties semantics!); RANGE vs ROWS (ties!); missing ORDER
BY (nondeterministic!); `LAG` default (provide: `LAG(x, 1, 0)`!).

**Interview angle.** "DENSE_RANK per group in a CTE, filter outside."
Frame stated for runnings. Ties-semantics named (ROW vs RANK vs DENSE).
Windows + CTEs = the senior SQL look.""",
            """-- 7-day moving average of daily revenue (explicit ROWS frame).
WITH daily AS (
    SELECT date_trunc('day', created_at)::date AS d,
           SUM(amount) AS revenue
    FROM orders
    GROUP BY 1
)
SELECT d, revenue,
       AVG(revenue) OVER (
           ORDER BY d
           ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
       ) AS avg_7d
FROM daily
ORDER BY d;

-- Dedup: keep latest row per (user_id).
WITH ranked AS (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY user_id ORDER BY updated_at DESC
    ) AS rn
    FROM events
)
SELECT * FROM ranked WHERE rn = 1;""",
            """In /studio: day-over-day delta via LAG (CTE + compute). Then
solve the judged window-thinking problem `moving-average`.
Practice: /practice/problems/moving-average""",
        ),
        (
            "sql-optimization-explain",
            "Indexes and EXPLAIN: make queries fast, prove it",
            "B-trees, covering indexes, and reading query plans.",
            """**Why this matters.** "Write it" gets juniors hired; "make it
fast + prove with EXPLAIN" gets seniors hired. Indexes (B-tree default,
composite order, covering), plan reading (seq scan vs index, nested loop
vs hash join), and the measurement loop (`EXPLAIN ANALYZE`).

**Indexes.** B-tree: equality + range + ORDER BY (leftmost!). Composite
`(a, b)`: serves `a = ?`, `a = ? AND b = ?`, `a = ? ORDER BY b` — NOT `b
= ?` alone (leftmost rule!). Covering (index-only scan: all cols in
index!). Partial (`WHERE active` — small, hot!). Unique (constraint +
lookup!). GIN (JSON/arrays/full-text — mention!). Unused/many indexes =
write-tax (measure!).

**EXPLAIN.** `EXPLAIN (ANALYZE, BUFFERS)` (Postgres): actual time/rows vs
estimates; Seq Scan (ok small, suspect large!), Index/Index-Only Scan,
Bitmap Heap, Nested Loop (small-outer!), Hash Join (large!), Sort +
sort-key, misestimates (rows off 10x → ANALYZE/stale stats!). Read
inside-out, worst node first.

**Rewrites.** sargable (`created_at >= ?`, NOT `YEAR(created_at) = ?` —
functions kill indexes!); selective WHERE early; `EXISTS` vs `IN`; avoid
`SELECT *` (covering!); pagination `keyset` (`WHERE id > ? ORDER BY id
LIMIT n` — NOT deep OFFSET!); CTEs (optimization fences in old PG —
know version!); `UNION ALL` over `UNION`.

**Common mistakes.** Indexing everything (write-tax!); leading-wildcard
LIKE (`%x` — unindexable! trigram/GIN for that!); functions on columns;
deep OFFSET; OR across tables (union rewrite!); trusting estimates
(ANALYZE!); `N+1` (app-side — join/batch!).

**Interview angle.** "Composite (a, b) leftmost; EXPLAIN shows index-only;
keyset pagination." Plan vocabulary fluent (scan types, join types,
misestimates). Optimisation interviews = measurement + vocabulary.""",
            """-- Sargable + covering: recent active orders per customer.
CREATE INDEX orders_customer_created_idx
    ON orders (customer_id, created_at DESC)
    INCLUDE (amount, status);   -- covering: index-only scans

EXPLAIN (ANALYZE, BUFFERS)
SELECT customer_id, SUM(amount)
FROM orders
WHERE customer_id = 42
  AND created_at >= now() - interval '90 days'
GROUP BY customer_id;

-- Keyset pagination (no deep OFFSET).
SELECT id, created_at, amount
FROM orders
WHERE id > 100000
ORDER BY id
LIMIT 50;""",
            """In /studio: EXPLAIN a join before/after adding an index; note
the scan change. Then solve the judged grouping problem
`histogram-bins` (bucketing logic transfers).
Practice: /practice/problems/histogram-bins""",
        ),
        (
            "sql-recursion-cte",
            "Recursive CTEs: hierarchies, paths, sequences",
            "WITH RECURSIVE: org trees, graphs, and generated series.",
            """**Why this matters.** Hierarchies (org charts, categories,
threads), paths (BOM, referral chains), sequences (date spines!) need
recursion — `WITH RECURSIVE` (anchor + recursive + UNION ALL + depth
guard!). Plus the graph-thinking transfer (traversal = BFS/DFS in SQL).

**Shape.** `WITH RECURSIVE chain AS (SELECT ... FROM emp WHERE mgr IS
NULL  -- anchor;  UNION ALL  SELECT ... FROM emp e JOIN chain c ON e.mgr
= c.id WHERE c.depth < 20  -- recursive + GUARD) SELECT * FROM chain;`
Anchor (seeds) + recursive (grows) + UNION ALL + termination (depth cap/
visited!). UNION (dedup) vs ALL (fast — guard yourself!).

**Uses.** Subtree (all reports under X — anchor X, recurse down!). Path
(strings: `path || '>' || name` — breadcrumb!). Level/depth (indent!).
Date spine (`generate_series` PG — or recursive dates!). Hierarchies up
(managers chain) + down (reports). Cycle guard (`WHERE NOT path @> ...`
or depth cap + visited array!).

**Graphs.** Reachability (transitive closure!); shortest-ish (BFS layers
via depth — true shortest needs iterative deepening, state limits!);
topo-ish (levels!). SQL recursion = fixed-point iteration (same math as
DSU/BFS layers — say it!).

**Limits.** Depth caps (default 100 PG `max_recursion_depth` MySQL 1000
— tune consciously!); perf (index the join key!); cycles (guard!);
dialects (syntax varies — CTE core portable, options differ!).

**Common mistakes.** No termination guard (infinite!); UNION vs ALL
unconsidered; anchor too broad (whole table × levels!); unindexed join
key; path cycles unhandled; recursion for sequences (generate_series!).

**Interview angle.** "Anchor + recursive + depth guard; path strings for
breadcrumbs." Spine + hierarchy fluency. Recursion interviews test
termination thinking — guards first, cleverness never.""",
            """-- Org subtree under manager 7 with depth + breadcrumb path.
WITH RECURSIVE reports AS (
    SELECT id, name, manager_id, 0 AS depth,
           name::text AS path
    FROM employees
    WHERE id = 7                      -- anchor: the subtree root
    UNION ALL
    SELECT e.id, e.name, e.manager_id, r.depth + 1,
           r.path || ' > ' || e.name
    FROM employees e
    JOIN reports r ON e.manager_id = r.id
    WHERE r.depth < 20                -- termination guard
)
SELECT id, name, depth, path
FROM reports
ORDER BY path;

-- Date spine: last 30 days (drives gap-free reports).
WITH RECURSIVE days(d) AS (
    SELECT CURRENT_DATE - 29
    UNION ALL
    SELECT d + 1 FROM days WHERE d < CURRENT_DATE
)
SELECT * FROM days;""",
            """In /studio: managers-chain UP from one employee (anchor +
recurse). Then solve the judged recurrence `climb-stairs` — same
fixed-point thinking, Python-side.
Practice: /practice/problems/climb-stairs""",
        ),
        (
            "sql-data-modeling",
            "Data modeling: normal forms, keys, real schemas",
            "Design schemas that stay correct as they grow.",
            """**Why this matters.** System-design interviews ask "design the
schema" (Twitter, Uber, URL shortener!): entities, keys, relationships,
normalization vs denormalization, constraints. Good modeling prevents
whole bug classes (dupes, orphans, anomalies!). The DDL IS the answer.

**Keys.** PK (surrogate `bigint GENERATED ALWAYS AS IDENTITY` vs natural
— surrogate default, natural when truly stable like ISO codes!). FKs
(`REFERENCES ... ON DELETE RESTRICT/CASCADE/SET NULL` — choose
deliberately, RESTRICT default!). Unique (business identity!). Composite
(join tables!). `NOT NULL` (default non-nullable — nulls are decisions!).

**Normal forms.** 1NF (atomic values — no CSV-in-cell!). 2NF (no partial
deps — split!). 3NF (no transitive — lookup tables!). Know when to STOP:
counters/caches/leaderboards denormalize deliberately (with refresh
strategy!). M2M (join table + composite PK!). 1-1 (shared PK or unique
FK!). Hierarchies (adjacency + recursive CTE vs ltree/closure — state!).

**Constraints.** `CHECK` (ranges, state machines in DDL!). `UNIQUE`
(idempotency keys! `UNIQUE(request_id)` — exactly-once!). `EXCLUDE`
(no-overlap bookings — PG superpower!). FKs (referential!). Defaults
(`now()`, `gen_random_uuid()`). Domain types (email/positive-int!).

**Evolving.** Migrations (expand-contract!: add nullable → backfill →
constrain → drop old!). Indexes concurrently (`CONCURRENTLY` — no locks!).
Backfills batched (keyset!). Zero-downtime = additive-first.

**Common mistakes.** No FKs ("app enforces" — lies!); EAV soup; CSV
cells; nullable-everything; natural PKs that change; missing uniques
(dupes!); premature denormalization; giant migrations (lock!).

**Interview angle.** "Entities, surrogate PKs, FKs with RESTRICT,
UNIQUE(request_id) for idempotency, expand-contract to evolve." Draw
boxes-arrows-keys, defend each constraint. Modeling interviews =
correctness vocabulary.""",
            """-- URL shortener core: users, urls, clicks (3NF, honest keys).
CREATE TABLE users (
    id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email      citext NOT NULL UNIQUE,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE urls (
    id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    owner_id   bigint NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    code       text NOT NULL UNIQUE CHECK (code ~ '^[A-Za-z0-9]{6,}$'),
    target     text NOT NULL CHECK (target LIKE 'https://%'),
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX urls_owner_idx ON urls (owner_id, created_at DESC);

CREATE TABLE clicks (
    id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    url_id     bigint NOT NULL REFERENCES urls (id) ON DELETE CASCADE,
    clicked_at timestamptz NOT NULL DEFAULT now(),
    request_id uuid NOT NULL UNIQUE  -- idempotent ingest
);""",
            """Design Pastebin schema (DDL + 2 indexes + 1 CHECK) in /studio.
Then solve the judged text-normalization problem `slugify` (data
cleaning transfers to modeling judgment).
Practice: /praent).
Practice: /practice/problems/slugify""",
        ),
        (
            "sql-interview-mastery",
            "SQL interview mastery: method, drills, hard favourites",
            "The full loop: clarify, CTE, validate, optimize — timed.",
            """**Why this matters.** SQL interviews (screens + onsites +
data/system rounds) grade method: clarify grain, CTE steps, validate
(counts/ties/nulls!), optimize with EXPLAIN. Rehearse the loop timed —
fluency under pressure is the skill.

**Five steps, SQL.** (1) Clarify: grain (one row per WHAT?), ties (top-1
vs with-ties?), nulls (exclude?), dupes (dedupe key?), dialect (PG/MySQL
— date funcs differ!), scale (index talk?). (2) Explore: `COUNT(*)`,
`COUNT(DISTINCT key)`, min/max, null rates (5 quick probes!). (3) Build:
CTEs (filter → shape → aggregate → window → pick!). (4) Validate: row
counts per CTE (sanity!), tie spot-checks, NULL probes, edge (empty
groups? zero-division `NULLIF`!). (5) Optimize: EXPLAIN, indexes,
sargable, keyset — only if asked/slow.

**Hard favourites.** Top-N per group (DENSE_RANK + ties talk!). Gaps-
and-islands (`row_number() - row_number() OVER (PARTITION BY grp)` —
the island key!). Retention cohorts (first-touch CTE + matrix!). Funnels
(conditional COUNT + step CTEs!). Running totals (frames!). Dedup
(ROW_NUMBER + delete!). Median (PERCENTILE_CONT vs manual!). Sessionize
(LAG + gap flag + running SUM — islands again!).

**Dialects.** Dates (`date_trunc` PG vs `DATE_FORMAT` MySQL!);
`FILTER` (PG) vs `SUM(CASE...)` (portable!); `ILIKE` (PG) vs `LOWER`
(portable!); `generate_series` (PG) vs recursive spine (portable!);
`LIMIT` vs `TOP`/`FETCH FIRST`. State dialect, prefer portable.

**Common mistakes.** Wrong grain (fanout joins!); ties unhandled;
NULL logic (`NOT IN`! `COUNT(col)` vs `COUNT(*)`!); division by zero
(`NULLIF`!); unvalidated (no counts!); premature optimization; dialect
mixups.

**Rehearsal.** 60+ queries timed + aloud; miss-log (grain/ties/nulls/
frame/dialect!); weekly redos; monthly gaps-islands/cohort/sessionize
from memory. Every query runs in /studio before claimed.""",
            """-- Gaps-and-islands: consecutive login streaks per user.
WITH ordered AS (
    SELECT user_id, login_date,
           login_date - ROW_NUMBER() OVER (
               PARTITION BY user_id ORDER BY login_date
           )::int AS island_key   -- constant within a streak!
    FROM (SELECT DISTINCT user_id, login_date::date FROM logins) d
),
streaks AS (
    SELECT user_id, island_key,
           COUNT(*) AS streak_len,
           MIN(login_date) AS started,
           MAX(login_date) AS ended
    FROM ordered
    GROUP BY user_id, island_key
)
SELECT user_id, streak_len, started, ended
FROM streaks
WHERE streak_len >= 7
ORDER BY streak_len DESC, user_id;

-- NULLIF: division that can't explode.
SELECT region,
       SUM(revenue) / NULLIF(SUM(orders), 0) AS avg_order_value
FROM sales
GROUP BY region;""",
            """Solve sessionize-by-30min-gap (LAG + islands) in /studio. Then
solve the judged stats problem `standard-deviation` (two-pass vs
Welford — numerical thinking transfers).
Practice: /practice/problems/standard-deviation""",
        ),
    ]
}

#: Module slug -> judged problem slug for the "code what you learned" button.
MODULE_PRACTICE: dict[str, str] = {
    "go-complexity-big-o": "binary-search",
    "go-slices-maps-deep": "two-sum",
    "go-recursion-sorting": "climb-stairs",
    "go-stacks-queues": "valid-parentheses",
    "go-trees-graphs": "max-depth-binary-tree",
    "go-interview-mastery": "container-most-water",
    "rust-complexity-big-o": "binary-search",
    "rust-strings-vec-deep": "valid-anagram",
    "rust-recursion-sorting": "koko-eating-bananas",
    "rust-hash-collections": "subarray-sum-equals-k",
    "rust-graphs-dp": "unique-paths",
    "rust-interview-mastery": "minimum-window-substring",
    "sql-subqueries-cte": "mean-median-mode",
    "sql-window-functions": "moving-average",
    "sql-optimization-explain": "histogram-bins",
    "sql-recursion-cte": "climb-stairs",
    "sql-data-modeling": "slugify",
    "sql-interview-mastery": "standard-deviation",
}

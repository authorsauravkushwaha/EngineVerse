"""Book-depth C++ modules: STL, algorithms and interview mastery.

C++ interviews are won on the STL: vector, string, unordered_map, map,
set, stack, queue, priority_queue, and <algorithm> — used with correct
complexity, const-correctness and move awareness. This book teaches data
structures through the STL plus from-scratch builds (for the "implement
it" follow-ups), then algorithms and a method module. Compile with
-std=c++17 -Wall -Wextra; test under ASan/UBSan.
"""

from __future__ import annotations

BOOK_MODULES: dict[str, list[tuple]] = {
    "cpp": [
        (
            "cpp-complexity-big-o",
            "Big-O in C++: operations, allocs and cache",
            "Price every STL op, count allocations, and respect the cache.",
            """**Why this matters.** C++ interviews assume you know container
costs cold: `vector::push_back` amortised `O(1)`, `unordered_map::find`
average `O(1)`, `map::find` `O(log n)`, `sort` `O(n log n)`. Wrong
container = timeout, and "it passed in Python" is no defence. This
module fixes the cost table in memory and adds C++ specifics —
allocations, moves, cache — that decide real performance.

**The cost table (memorise).** vector: index `O(1)`, push/pop back
amortised `O(1)`, insert/erase mid `O(n)`. deque: both ends `O(1)`.
list: splice `O(1)`, search `O(n)` (rarely the answer). unordered_map/
set: average `O(1)`, worst `O(n)`. map/set (red-black): `O(log n)`
with order. priority_queue: push/pop `O(log n)`, top `O(1)`. sort:
`O(n log n)` (introsort, not stable; stable_sort when needed).
`string::find`/`substr` (copy!). `lower_bound/upper_bound` `O(log n)`
on random access.

**Allocations are cost.** Each `new`/node alloc costs time and fragments;
`vector` reserves contiguously (reserve() up front!), node containers
(map/set/list) allocate per element. Pass `const vector<int>&` (never by
value unless owning), return by value (RVO/move makes it free), move
(`std::move`) large locals you no longer need. `emplace_back` builds in
place (no temporary). These four habits are "C++ performance" for 95% of
code.

**Cache.** Contiguous vector scans beat list/map pointer-chasing ~10x at
scale. Prefer vector even for "theoretically" worse ops when n is
moderate — mention the trade explicitly; it reads as experienced.

**Common mistakes.** `map` where `unordered_map` sufficed (log factor
for nothing — unless order needed); `list` for scans; pass-by-value
vectors; `substr` in loops (copies); `endl` (flushes! use `'\\n'`);
`-O0` timings; `using namespace std;` in headers.

**Interview angle.** "unordered_map: O(n) average time, O(n) space;
worst O(n²) on adversarial hash — acceptable here." Naming average vs
worst with the structure's real name is the C++ fluency check.""",
            """#include <algorithm>
#include <chrono>
#include <iostream>
#include <unordered_set>
#include <vector>

static bool has_dup_brute(const std::vector<int>& a) {   // O(n^2)
    for (size_t i = 0; i < a.size(); i++)
        for (size_t j = i + 1; j < a.size(); j++)
            if (a[i] == a[j]) return true;
    return false;
}

static bool has_dup_fast(const std::vector<int>& a) {    // O(n) avg
    std::unordered_set<int> seen;
    seen.reserve(a.size() * 2);
    for (int x : a)
        if (!seen.insert(x).second) return true;
    return false;
}

int main() {
    std::vector<int> data(20000);
    for (int i = 0; i < 20000; i++) data[i] = i;
    for (int t = 0; t < 2; t++) {
        auto start = std::chrono::steady_clock::now();
        bool r = t ? has_dup_fast(data) : has_dup_brute(data);
        auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::steady_clock::now() - start).count();
        std::cout << (t ? "fast" : "brute") << " " << r << " " << ms << " ms\\n";
    }
    return 0;
}""",
            """Time both at n = 40,000 (-O2). Then solve the judged problem
`binary-search` and state time + space with the container costs named.
Practice: /practice/problems/binary-search""",
        ),
        (
            "cpp-strings-deep",
            "std::string: views, building and text patterns",
            "string_view for zero-copy, ostringstream discipline, windows and pointers.",
            """**Why this matters.** `std::string` owns; `std::string_view`
borrows — and interviews reward knowing which to pass. Concatenation in
loops is quadratic (same as every language); `ostringstream`/`append`
with `reserve` is linear. Two pointers and sliding windows on
`std::string` cover the text half of interviews.

**string vs string_view.** Take `std::string_view` for read-only params
(no copy, works for string/char*/literal). Return `std::string` when
owning (never return a view of a local!). `sv.substr` is `O(1)` (view);
`s.substr` copies (`O(k)`). Compare with `==` (works, unlike Java/C!).
`find` returns `npos` on miss — check it. `stoi/stol` with size_t* pos
for errors (or `from_chars` in C++17 — fastest, no exceptions, no locale).

**Building.** `reserve` then `+=`/`append` in loops (amortised linear);
`ostringstream` for mixed formatting; `std::string(sv)` to materialise.
Never `s = s + ch` per char without reserve in hot code (still amortised,
but reserve documents intent). Join: accumulate with delimiter logic or
`std::accumulate` — no built-in join (C++20 ranges help; interviews
accept loops).

**Patterns.** Palindrome: indices inward, `isalnum/tolower` (cast to
`unsigned char`!). Anagram: `array<int,26>` counts. Longest substring:
window + last-index array[128]. Parse: `istringstream` or manual index
walks (manual is faster and clearer for interview parsing).

**Common mistakes.** Returning string_view of a temporary/local
(dangling!); `s[i]` out of range (use `.at()` when unsure — throws);
`c_str()` lifetime (valid until next non-const call); `stoi` exceptions
unhandled; `find == -1` instead of `npos`; signed char to ctype (UB —
cast!).

**Interview angle.** "Taking string_view — zero copies; building the
answer in a reserved std::string." That sentence, unprompted, is modern
C++ fluency. Then pointers or window with the invariant stated.""",
            """#include <array>
#include <iostream>
#include <string>
#include <string_view>

static bool is_palindrome(std::string_view s) {
    size_t l = 0, r = s.size();
    if (r == 0) return true;
    r--;
    while (l < r) {
        unsigned char a = static_cast<unsigned char>(s[l]);
        unsigned char b = static_cast<unsigned char>(s[r]);
        if (!std::isalnum(a)) { l++; continue; }
        if (!std::isalnum(b)) { r--; continue; }
        if (std::tolower(a) != std::tolower(b)) return false;
        l++; r--;
    }
    return true;
}

static int longest_unique(std::string_view s) {   // sliding window, O(n)
    std::array<int, 128> last;
    last.fill(-1);
    int start = 0, best = 0;
    for (int i = 0; i < (int)s.size(); i++) {
        unsigned char c = static_cast<unsigned char>(s[i]);
        if (last[c] >= start) start = last[c] + 1;
        last[c] = i;
        best = std::max(best, i - start + 1);
    }
    return best;
}

int main() {
    std::cout << is_palindrome("A man, a plan, a canal: Panama") << "\\n"; // 1
    std::cout << longest_unique("abcabcbb") << "\\n";                       // 3
    return 0;
}""",
            """Write `isAnagram` with array<int,26> in O(n). Then solve the
judged problem `longest-substring` (window + last-index).
Practice: /practice/problems/longest-substring""",
        ),
        (
            "cpp-vectors-arrays",
            "vector and array: contiguous power, in-place skill",
            "Growth, reserve, and the read/write pointer technique.",
            """**Why this matters.** `std::vector` is the default container —
contiguous, cache-friendly, `O(1)` index/push. `std::array` fixes size
at compile time. In-place vector algorithms (dedup, partition, rotate,
merge) are core interview material, and const-ref discipline separates
fluent C++ from translated Java.

**vector mechanics.** Capacity doubles (amortised `O(1)` push_back);
`reserve(n)` preallocates (do it when n is known — avoids all
reallocation + iterator invalidation); `resize` changes size (value-
initialises); `shrink_to_fit` is a non-binding request. Reallocation
invalidates iterators/pointers — the #1 vector bug (never hold `&v[0]`
across pushes). `emplace_back(args...)` constructs in place.
`vector<bool>` is a bitset specialization (not a container — avoid! use
`vector<char>` or `std::vector<uint8_t>`).

**array and C arrays.** `std::array<int, N>`: stack, fixed, `.size()`,
bounds-checked `.at()`, no decay. Prefer over C arrays always. C arrays
appear in legacy signatures — wrap immediately. `int arr[n]` VLA is NOT
standard C++ (GCC extension — never in portable code; use vector).

**In-place technique.** Read/write pointers, invariant "before write:
final". Dedup-sorted, remove-element, move-zeroes: `O(n)`/`O(1)`.
Partition (Lomuto) for quickselect. Rotation by reversal. Merge from the
end with tail space. Return new logical length; caller `resize`s. Pass
`vector<int>&` for in-place, `const vector<int>&` for reads — state the
choice.

**Common mistakes.** Iterator invalidation across push/erase (erase-
remove idiom: `v.erase(remove_if(...), end)`); `operator[]` out of range
(UB — `.at()` in doubt); `reserve` vs `resize` confusion (reserve does
not change size!); `vector<bool>`; returning iterators to locals.

**Interview angle.** Signature discipline: `int dedup(vector<int>& a)`
with "returns new length" contract. Invariant before code. Mention
reserve when building. In-place + const-correct reads as production
C++, not puzzle C++.""",
            """#include <algorithm>
#include <iostream>
#include <vector>

// Invariant: a[0..write) holds kept items. Returns new length.
static int remove_duplicates(std::vector<int>& a) {
    if (a.empty()) return 0;
    int write = 1;
    for (size_t read = 1; read < a.size(); read++)
        if (a[read] != a[read - 1]) a[write++] = a[read];
    return write;
}

static void rotate_right(std::vector<int>& a, int k) {
    int n = (int)a.size();
    if (n == 0) return;
    k %= n;
    std::reverse(a.begin(), a.end());
    std::reverse(a.begin(), a.begin() + k);
    std::reverse(a.begin() + k, a.end());
}

int main() {
    std::vector<int> a = {0, 0, 1, 1, 1, 2, 3, 3};
    int n = remove_duplicates(a);
    a.resize(n);
    for (int x : a) std::cout << x << " ";   // 0 1 2 3
    std::cout << "\\n";
    std::vector<int> b = {1, 2, 3, 4, 5};
    rotate_right(b, 2);                       // 4 5 1 2 3
    for (int x : b) std::cout << x << " ";
    std::cout << "\\n";
    return 0;
}""",
            """Implement Lomuto partition + quickselect (avg O(n)). Then solve
the judged problem `remove-duplicates-sorted`.
Practice: /practice/problems/remove-duplicates-sorted""",
        ),
        (
            "cpp-hash-unordered",
            "unordered_map/set: hashing, custom keys, patterns",
            "Average O(1) with control: reserve, max_load, and hashing pairs.",
            """**Why this matters.** `unordered_map`/`unordered_set` are the
C++ interview workhorses — Two Sum, anagrams, grouping, top-k counting.
But C++ hashing has sharp edges: no default pair hash, worst-case
degradation, rehash costs. Know the controls (`reserve`,
`max_load_factor`, custom hashers) and the ordered alternatives.

**Mechanics.** Bucket array + chaining (typical); `find/insert/erase`
average `O(1)`, worst `O(n)`. `reserve(n)` preallocates buckets
(avoid rehash pauses); `max_load_factor(0.7)` tightens; `operator[]`
inserts default on miss (use `find`/`contains` (C++20) for pure lookup).
Iterators stay valid across insert (but not rehash for some ops —
rehash invalidates iterators!). No order — never depend on iteration
sequence.

**Custom keys.** `struct PairHash { size_t operator()(const pair<int,int>&
p) const noexcept { return hash<int>{}(p.first) * 31u +
hash<int>{}(p.second); } };` — combine with splitmix64 for adversarial
robustness (hackable default hash is a real contest/DoS concern; mention
it). Custom structs need `operator==` + hasher. `map`/`set` (red-black,
`O(log n)`) when order or worst-case guarantees matter; `std::array`/
`vector<int>` frequency tables beat hashing for small alphabets.

**Patterns.** Complement (need = target - x, check-then-insert).
Frequency (`m[x]++`, then decide; top-k via heap of pairs). Grouping
(`unordered_map<string, vector<string>>` with sorted-key). Seen
(visited, dedup, cycle states). Sliding-window counts with
`unordered_map<char,int>` + matched counter.

**Common mistakes.** `operator[]` for lookup (mutates!); missing pair
hash (compile error — write the hasher); iterator use across rehash;
`hash<int>` on untrusted input without hardening (mention splitmix);
`map` paying log for unordered needs; `erase` while ranging (use
iterator-returning erase).

**Interview angle.** "unordered_map: O(n) average, O(n) space; worst
O(n) per op on collision attack — map would guarantee log." Offering
the ordered fallback + the frequency-array special case shows judgment,
not just API memory.""",
            """#include <iostream>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

struct PairHash {
    size_t operator()(const std::pair<int, int>& p) const noexcept {
        size_t h1 = std::hash<int>{}(p.first);
        size_t h2 = std::hash<int>{}(p.second);
        return h1 ^ (h2 + 0x9e3779b9u + (h1 << 6) + (h1 >> 2));
    }
};

static std::vector<int> two_sum(const std::vector<int>& nums, int target) {
    std::unordered_map<int, int> seen;   // value -> index
    seen.reserve(nums.size() * 2);
    for (int i = 0; i < (int)nums.size(); i++) {
        int need = target - nums[i];
        auto it = seen.find(need);       // find: no accidental insert
        if (it != seen.end()) return {it->second, i};
        seen[nums[i]] = i;
    }
    return {};
}

int main() {
    auto r = two_sum({2, 7, 11, 15}, 9);
    std::cout << r[0] << " " << r[1] << "\\n";   // 0 1
    std::unordered_map<std::pair<int, int>, std::string, PairHash> grid;
    grid[{3, 4}] = "cell";
    std::cout << grid[{3, 4}] << "\\n";
    return 0;
}""",
            """Solve group-anagrams with unordered_map<string, vector<string>>
(sorted key). Then solve the judged problem `group-anagrams`.
Practice: /practice/problems/group-anagrams""",
        ),
        (
            "cpp-recursion",
            "Recursion in C++: frames, memo tables, backtracking",
            "Base cases, stack budgets, and choose/explore/unchoose.",
            """**Why this matters.** C++ recursion is machine-close: frames on
a finite stack, no tail-call guarantee, segfault past the limit. Trees,
DFS, backtracking and top-down DP all recurse — with explicit memo
vectors and move-aware signatures. Depth accounting is systems literacy.

**Frames and budgets.** Each call pushes return address + locals;
typical 8MB stack ≈ 10⁵–10⁶ small frames. Depth = height for trees
(`O(log n)` balanced, `O(n)` skewed — state it), = n for linear chains
(iterate those!). `std::function` recursion adds type-erasure overhead
— prefer named functions/lambdas with auto& self (C++14 generic lambda
trick) or plain functions in hot code.

**Memoization.** `vector<int> memo(n+1, -1)` (-1 = uncomputed, when valid
answers exclude it) or `vector<vector<int>>` for 2D; `unordered_map` for
sparse/composite states (with custom hash). Fibonacci `O(φⁿ)` → `O(n)`;
climbing stairs likewise. Pass memo by reference. Bottom-up next: same
states, loops, then rolling compression.

**Backtracking.** Shared `vector<int> path` / board, push-explore-pop.
Subsets, permutations (swap-based `O(1)` extra), combinations, N-Queens
(col/diag sets), word search (in-place mark + restore). Prune hard:
invalid prefix stops the subtree. Copy path to output only at leaves
(`out.push_back(path)` — the copies dominate: state `O(2ⁿ · n)`).

**Move semantics in recursion.** Return `vector<vector<int>>` by value
(RVO elides copies); `std::move` path into output when done with it.
Take large inputs by `const&`. These details in recursive code read as
optimizing-competent.

**Common mistakes.** No base/progress (stack overflow = segfault, not
exception); `std::function` in tight recursion (slow); copying vectors
per call (pass by ref!); forgetting unchoose (cross-branch pollution);
memo sentinel colliding with valid answers; recursion on untrusted depth.

**Interview angle.** "Depth h, O(h) stack; memo O(states)." Offer
iterative + explicit `vector` stack. C++ interviewers watch copies:
narrate every `&` and `move` as you write it.""",
            """#include <functional>
#include <iostream>
#include <vector>

static long long fib_memo(int n, std::vector<long long>& memo) {
    if (n < 2) return n;
    if (memo[n] != -1) return memo[n];
    return memo[n] = fib_memo(n - 1, memo) + fib_memo(n - 2, memo);
}

static void subsets(const std::vector<int>& nums, size_t i,
                    std::vector<int>& path,
                    std::vector<std::vector<int>>& out) {
    if (i == nums.size()) { out.push_back(path); return; }  // leaf copy
    path.push_back(nums[i]);                                 // choose
    subsets(nums, i + 1, path, out);
    path.pop_back();                                        // unchoose
    subsets(nums, i + 1, path, out);
}

int main() {
    std::vector<long long> memo(91, -1);
    std::cout << fib_memo(90, memo) << "\\n";
    std::vector<std::vector<int>> out;
    std::vector<int> path;
    subsets({1, 2, 3}, 0, path, out);
    std::cout << out.size() << " subsets\\n";   // 8
    return 0;
}""",
            """Write permutations via index-swapping (no used-array). Then
solve the judged problem `climb-stairs` top-down + bottom-up.
Practice: /practice/problems/climb-stairs""",
        ),
        (
            "cpp-sorting-searching",
            "sort, binary search and <algorithm> power",
            "Comparators, bounds, nth_element and search-on-the-answer.",
            """**Why this matters.** `<algorithm>` is C++'s unfair advantage:
`sort`, `lower_bound`, `nth_element`, `merge`, `rotate`, `partition` —
each optimal, each one line. Interviews test whether you reach for them
(and write correct comparators) instead of hand-rolling bugs. Sorting
unlocks pairs/triples/intervals; binary search unlocks boundaries.

**sort and friends.** `sort(begin, end)` introsort `O(n log n)` avg,
`O(n log n)` worst (introsort guarantees it — unlike C qsort), NOT
stable; `stable_sort` when stability matters (`O(n log²n)`/extra mem).
Comparator must be strict-weak-ordering: `(a,b) -> a[0] < b[0]`; multi-
level with `std::tie(a[0],a[1]) < std::tie(b[0],b[1])`. `nth_element`
puts the nth in place, average `O(n)` — kth smallest without full sort.
`partial_sort` for top-k sorted. `binary_search/lower_bound/upper_bound`
`O(log n)` on random access (need sorted!).

**Hand binary search.** Invariant "answer in [lo, hi] if any"; `mid = lo
+ (hi - lo) / 2` (overflow-safe — `int` overflow is UB!); strict shrink.
Variants: first/last occurrence, rotated (one half sorted), peak, sqrt,
and search-on-answer ("min feasible x", monotone predicate — koko, ship,
split-array). `std::midpoint` (C++20) is overflow-safe and slick.

**Common mistakes.** Bad comparator (not strict-weak → UB/crashes —
`<=` instead of `<` is the classic); `(lo+hi)/2` overflow (UB for int!);
bounds on unsorted data; `lower_bound` dereferenced at end without check;
`sort` on `list` (member sort instead — or use vector); forgetting
`std::` (ADL usually saves you; write it anyway).

**Interview angle.** Name the algorithm and guarantee: "introsort,
O(n log n) worst; not stable — stability unneeded here." For binary
search, invariant as comment. For kth: "nth_element O(n) average beats
sort; heap O(n log k) streams." Precision about guarantees is the C++
bar.""",
            """#include <algorithm>
#include <iostream>
#include <vector>

static int lower_bound_ge(const std::vector<int>& a, int target) {
    int lo = 0, hi = (int)a.size() - 1, ans = -1;
    while (lo <= hi) {                        // answer in [lo, hi] if any
        int mid = lo + (hi - lo) / 2;
        if (a[mid] >= target) { ans = mid; hi = mid - 1; }
        else lo = mid + 1;
    }
    return ans;
}

int main() {
    std::vector<std::vector<int>> iv = {{8,10},{1,3},{2,6},{15,18}};
    std::sort(iv.begin(), iv.end(),
        [](const auto& a, const auto& b){ return a[0] < b[0]; });
    for (auto& p : iv) std::cout << "[" << p[0] << "," << p[1] << "] ";
    std::cout << "\\n";
    std::vector<int> a = {1, 2, 2, 2, 5};
    std::cout << lower_bound_ge(a, 2) << "\\n";  // 1
    std::nth_element(a.begin(), a.begin() + 2, a.end());
    std::cout << "3rd smallest=" << a[2] << "\\n";
    return 0;
}""",
            """Implement integer sqrt by hand (floor). Then solve the judged
problem `three-sum` (sort + two pointers + dedup).
Practice: /practice/problems/three-sum""",
        ),
        (
            "cpp-stacks-queues",
            "stack, queue, deque, priority_queue",
            "Adapters over deque/vector, monotonic stacks, and heaps.",
            """**Why this matters.** C++ stack/queue are adapters (default over
deque) with minimal APIs — `push/pop/top/empty`, no iteration. That
minimalism enforces discipline. Add `priority_queue` (max-heap) and you
cover parentheses, next-greater, BFS, top-k and scheduling.

**stack and queue.** `stack<int> st; st.push/top/pop/empty`. `queue<int>
q; q.push/front/pop`. Underlying deque gives `O(1)`; `vector` as
underlying (`stack<int, vector<int>>`) is more cache-friendly — mention
it. No `clear()` (swap with empty: `st = stack<int>()`), no iteration
(by design). For parentheses/RPN/monotonic work this is exactly enough.

**deque.** `deque<int>`: both ends `O(1)`, indexed `O(1)`, middle `O(n)`.
Sliding-window maximum (monotonic deque of indices), BFS queues, double-
ended sweeps. `emplace_front/back` construct in place.

**priority_queue.** Max-heap default: `push/pop/top` (`O(log n)`/top
`O(1)`). Min-heap: `priority_queue<int, vector<int>, greater<int>>`.
Custom: struct with `operator()` or lambda with `decltype`. Top-k:
size-k min-heap `O(n log k)`. Merge-k-sorted: heap of (value, list-id,
index). No iteration, no `clear`, no decrease-key (push duplicates +
lazy discard — standard trick, state it).

**Monotonic stack.** Indices, decreasing values, pop-and-record:
next-greater, temperatures, stock spans, largest rectangle — each `O(n)`
(one push/pop per item). Implement on `vector<int>` used as stack
(`push_back/pop_back/back`) for speed + index access.

**Common mistakes.** `top/front` on empty (UB! guard with empty());
adapters have no iteration (use underlying container directly when
needed); `priority_queue` iteration confusion (heap order ≠ sorted);
default max-heap when min needed; `queue::pop` returns void (copy front
first!).

**Interview angle.** "Monotonic stack: each index pushed/popped once,
O(n)." For heaps: "k small so O(n log k); no decrease-key so lazy
deletion." C++ adapters force the vocabulary — use it precisely.""",
            """#include <iostream>
#include <queue>
#include <stack>
#include <string>
#include <unordered_map>
#include <vector>

static bool is_valid(const std::string& s) {
    std::unordered_map<char, char> pairs = {{')','('},{']','['},{'}','{'}};
    std::stack<char> st;
    for (char ch : s) {
        auto it = pairs.find(ch);
        if (it != pairs.end()) {
            if (st.empty() || st.top() != it->second) return false;
            st.pop();
        } else st.push(ch);
    }
    return st.empty();
}

static std::vector<int> daily_temps(const std::vector<int>& t) {
    std::vector<int> ans(t.size(), 0);
    std::vector<int> st;   // indices, decreasing temps
    for (int i = 0; i < (int)t.size(); i++) {
        while (!st.empty() && t[i] > t[st.back()]) {
            ans[st.back()] = i - st.back();
            st.pop_back();
        }
        st.push_back(i);
    }
    return ans;
}

int main() {
    std::cout << is_valid("()[]{}") << " " << is_valid("([)]") << "\\n";
    for (int x : daily_temps({73,74,75,71,69,72,76,73})) std::cout << x << " ";
    std::cout << "\\n";   // 1 1 4 2 1 1 0 0
    return 0;
}""",
            """Solve largest-rectangle-in-histogram with a monotonic stack.
Then solve the judged problem `daily-temperatures`.
Practice: /practice/problems/daily-temperatures""",
        ),
        (
            "cpp-linked-lists",
            "Linked lists: unique_ptr ownership, raw-pointer rewiring",
            "Modern ownership with manual pointer discipline.",
            """**Why this matters.** C++ list interviews test two things at
once: pointer rewiring (dummy, fast/slow, reversal) and ownership
(who deletes?). `std::unique_ptr` answers ownership; raw pointers answer
traversal. Show both and you show senior C++.

**Ownership models.** Teaching/exercise: raw `new` + careful delete, or
unique_ptr chains (`unique_ptr<Node> next` — auto-frees the tail, move
semantics on insert). Interviews: usually raw-pointer structs with
"assume freed by caller" or a `delete_list` helper — state the contract.
`std::list` (doubly-linked, `O(1)` splice) exists but interviews want
hand-rolled singly-linked: build it.

**Rewiring.** Insert after p: `n->next = p->next; p->next = n;` (new
first!). Dummy head absorbs head-change. Fast/slow: cycle (`==`), middle
(slow at end of fast). Reversal prev/cur/nxt `O(1)`. Merge sorted with
dummy tail, reusing nodes. Partition with two dummy chains. Every bug is
a lost `.next` — save before redirect, draw before coding.

**unique_ptr sketch.** `struct Node { int v; unique_ptr<Node> next; };`
Insert: `n->next = std::move(p->next); p->next = std::move(n);`
Reversal with unique_ptr is fiddly (ownership transfers per link) — know
it exists, but raw pointers are clearer for algorithms; convert at
boundaries. Mention this trade explicitly.

**Common mistakes.** Lost next; double-delete (two owners — use
unique_ptr or document single ownership); cycles leaking under
unique_ptr/shared_ptr (weak_ptr breaks them — mention); `delete` then
dereference; recursion depth on long lists; `==` on values vs nodes in
cycle detect (identity!).

**Interview angle.** Contract first: "nodes owned by the list; deleted
by delete_list; functions borrow." Invariant during rewiring. ASan-clean
run offered. Ownership + discipline is the complete C++ answer.""",
            """#include <iostream>
#include <vector>

struct Node {
    int v;
    Node* next;
    Node(int value, Node* n = nullptr) : v(value), next(n) {}
};

static Node* build(const std::vector<int>& values) {
    Node dummy(0);
    Node* tail = &dummy;
    for (int x : values) {
        tail->next = new Node(x);   // owned by the list; see destroy
        tail = tail->next;
    }
    return dummy.next;
}

static Node* reverse(Node* head) {
    Node* prev = nullptr;
    while (head) {                  // before prev: reversed
        Node* nxt = head->next;     // 1. save
        head->next = prev;          // 2. redirect
        prev = head; head = nxt;    // 3. advance
    }
    return prev;
}

static bool has_cycle(Node* head) {
    Node* slow = head;
    Node* fast = head;
    while (fast && fast->next) {
        slow = slow->next;
        fast = fast->next->next;
        if (slow == fast) return true;
    }
    return false;
}

static void destroy(Node* head) {
    while (head) {
        Node* nxt = head->next;
        delete head;
        head = nxt;
    }
}

int main() {
    Node* list = build({1, 2, 3, 4});
    std::cout << has_cycle(list) << "\\n";   // 0
    list = reverse(list);
    for (Node* p = list; p; p = p->next) std::cout << p->v;
    std::cout << "\\n";                        // 4321
    destroy(list);
    return 0;
}
// g++ -std=c++17 -Wall -Wextra -fsanitize=address,undefined list.cpp""",
            """Write merge-two-sorted reusing nodes (dummy tail). Then solve
the judged problem `detect-cycle` and prove Floyd terminates.
Practice: /practice/problems/detect-cycle""",
        ),
        (
            "cpp-trees-heaps",
            "Trees and heaps: traversals, BST, priority_queue",
            "Recursive structure, ordered maps, and streaming extremes.",
            """**Why this matters.** Trees test recursion over branches;
heaps test streaming extremes. C++ offers both raw (`struct TreeNode`,
hand recursion) and ordered containers (`map`/`set`, red-black `O(log
n)`) plus `priority_queue`. Know when each wins.

**Traversals.** Preorder (copy/serialize), inorder (BST sorted), postorder
(children first: heights, diameter, delete), level order (queue: rows,
views). Max depth postorder. Symmetry mirrors. Diameter via height pass.
BST validate with (long long min, max) bounds (int edges overflow!).
Kth smallest: inorder count `O(h + k)` (or augmented subtree sizes).
LCA in BST: descend to split. `map`/`set` when you need ordered + balanced
guarantees without implementing red-black.

**Heaps.** `priority_queue` max-heap; min via `greater<>`. Top-k size-k
heap `O(n log k)`; kth largest; merge-k (heap of heads); median (two
heaps, rebalance to |diff| ≤ 1); task scheduling with cooldown (heap +
cooldown queue). Custom comparators for tuple entries (vector compares
lexicographically — handy: `priority_queue<vector<int>>` orders by
element 0, then 1...). No decrease-key: lazy deletion (push new, skip
stale on pop — state it).

**Smart-pointer trees.** `unique_ptr<TreeNode>` children auto-free
postorder (destructor recursion — depth risk on skewed trees, same as
manual). Interviews usually raw + `delete_tree` postorder helper; state
ownership either way.

**Common mistakes.** Null base forgotten; BST local-only validation
(needs ancestor bounds); recursion on skewed (iterate + stack); heap
comparator direction flipped (test with 3 elements!); `priority_queue`
of vectors comparing unexpectedly; long long bounds skipped.

**Interview angle.** Traversal named + why, before code. Height caveat
for BST. Heap: "k small ⇒ O(n log k); lazy deletion for updates." Draw
tree, trace heap ops — C++ interviewers trust visible mechanics.""",
            """#include <iostream>
#include <queue>
#include <vector>

struct TreeNode {
    int v;
    TreeNode* l;
    TreeNode* r;
    TreeNode(int x) : v(x), l(nullptr), r(nullptr) {}
};

static int max_depth(TreeNode* root) {
    if (!root) return 0;
    return 1 + std::max(max_depth(root->l), max_depth(root->r));
}

static std::vector<std::vector<int>> level_order(TreeNode* root) {
    std::vector<std::vector<int>> out;
    if (!root) return out;
    std::queue<TreeNode*> q;
    q.push(root);
    while (!q.empty()) {
        std::vector<int> level;
        for (size_t i = 0, n = q.size(); i < n; i++) {
            TreeNode* cur = q.front(); q.pop();
            level.push_back(cur->v);
            if (cur->l) q.push(cur->l);
            if (cur->r) q.push(cur->r);
        }
        out.push_back(std::move(level));
    }
    return out;
}

static int kth_largest(const std::vector<int>& nums, int k) {
    std::priority_queue<int, std::vector<int>, std::greater<int>> heap;
    for (int x : nums) {
        heap.push(x);
        if ((int)heap.size() > k) heap.pop();
    }
    return heap.top();
}

int main() {
    TreeNode* root = new TreeNode(3);
    root->l = new TreeNode(9);
    root->r = new TreeNode(20);
    root->r->l = new TreeNode(15);
    root->r->r = new TreeNode(7);
    std::cout << max_depth(root) << "\\n";   // 3
    for (auto& row : level_order(root)) {
        for (int x : row) std::cout << x << " ";
        std::cout << "| ";
    }
    std::cout << "\\n" << kth_largest({3,2,1,5,6,4}, 2) << "\\n";  // 5
    return 0;  // exercise: write delete_tree postorder
}""",
            """Write `delete_tree` (postorder) and run under ASan with zero
leaks. Then solve the judged problem `level-order-traversal`.
Practice: /practice/problems/level-order-traversal""",
        ),
        (
            "cpp-graphs",
            "Graphs: adjacency, grids, BFS/DFS, union-find",
            "Vector adjacency, matrix grids, topo sort and DSU.",
            """**Why this matters.** Graphs in C++: `vector<vector<int>>`
adjacency, `vector<string>`/`vector<vector<int>>` grids, BFS with
`queue`, DFS recursive/iterative, Kahn's topo, DSU with path compression.
Networks, maps, schedules, components — the shapes are universal; C++
makes them fast.

**Representations.** `vector<vector<int>> adj(n)` (sparse, `O(V+E)`);
`vector<vector<int>> mat(n, vector<int>(n))` (dense, `O(V²)`, Floyd);
grids implicit (neighbours computed; `vector<vector<char>>` visited or
in-place mark with consent); edge lists `vector<pair<int,int>>` for DSU/
Kruskal. Build once (`adj[u].push_back(v)`; both directions iff
undirected).

**BFS/DFS.** BFS (`queue<pair<int,int>>` or encoded ints): shortest
unweighted, levels, multi-source (oranges). DFS: connectivity, islands,
colours cycle-detect (0/1/2; 1-revisit = back edge), topo via finish
order. `O(V+E)`; grids `O(R·C)`. Iterative DFS with explicit
`vector<int>` stack for deep graphs (recursion segfaults past ~10⁵
frames).

**Topo + DSU.** Kahn: indegree `vector<int>`, zero-queue, peel; peeled <
n ⟺ cycle. DSU: parent/rank vectors, halving find, union by rank —
amortised α(n); provinces, redundant edge, Kruskal (`sort` edges +
DSU). DSU from memory in 25 lines is a rite of passage — drill it.

**Common mistakes.** DFS recursion on huge grids; no visited; directed/
undirected mixup; single-source on disconnected (outer loop!); grid
mark destroying input; `vector<bool>` visited (bitset proxy slowness +
proxy-reference bugs — use `vector<char>`); queue of pairs without
structured bindings (C++17: `auto [r,c] = q.front();`).

**Interview angle.** Model sentence first: "nodes = cells, 4-neighbour,
unweighted ⇒ BFS shortest." `O(V+E)` with V/E named. Allocation named
("one R×C visited"). C++ bonus: mention `vector<int>` stack / reserve
for the frontier.""",
            """#include <iostream>
#include <queue>
#include <vector>

// Union-find (DSU) with path halving + union by rank.
struct DSU {
    std::vector<int> parent, rank;
    DSU(int n) : parent(n), rank(n, 0) {
        for (int i = 0; i < n; i++) parent[i] = i;
    }
    int find(int x) {
        while (parent[x] != x) {
            parent[x] = parent[parent[x]];
            x = parent[x];
        }
        return x;
    }
    void unite(int a, int b) {
        a = find(a); b = find(b);
        if (a == b) return;
        if (rank[a] < rank[b]) parent[a] = b;
        else if (rank[a] > rank[b]) parent[b] = a;
        else { parent[b] = a; rank[a]++; }
    }
};

static int oranges(std::vector<std::vector<int>>& g) {
    int rows = g.size(), cols = g[0].size(), fresh = 0, minutes = 0;
    std::queue<std::pair<int,int>> q;
    for (int r = 0; r < rows; r++)
        for (int c = 0; c < cols; c++) {
            if (g[r][c] == 2) q.emplace(r, c);
            else if (g[r][c] == 1) fresh++;
        }
    const int dirs[4][2] = {{1,0},{-1,0},{0,1},{0,-1}};
    while (!q.empty() && fresh > 0) {
        minutes++;
        for (size_t i = 0, n = q.size(); i < n; i++) {
            auto [r, c] = q.front(); q.pop();
            for (auto& d : dirs) {
                int nr = r + d[0], nc = c + d[1];
                if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && g[nr][nc] == 1) {
                    g[nr][nc] = 2; fresh--;
                    q.emplace(nr, nc);
                }
            }
        }
    }
    return fresh == 0 ? minutes : -1;
}

int main() {
    DSU dsu(3);
    dsu.unite(0, 1);
    std::cout << (dsu.find(0) == dsu.find(1)) << "\\n";  // 1
    std::vector<std::vector<int>> g = {{2,1,1},{1,1,0},{0,1,1}};
    std::cout << oranges(g) << "\\n";                    // 4
    return 0;
}""",
            """Implement Kahn's topo sort with cycle detect. Then solve the
judged problem `rotting-oranges` (multi-source BFS).
Practice: /practice/problems/rotting-oranges""",
        ),
        (
            "cpp-dp",
            "Dynamic programming: tables, rolling arrays, states",
            "Top-down memo vectors, bottom-up tables, O(1) compression.",
            """**Why this matters.** DP in C++ is explicit tables:
`vector<int> dp(n+1)`, `vector<vector<int>>`, rolling pairs. No
decorators — loops, sentinels, fill order you control. Stairs, robber,
coin change, LIS, LCS, edit distance, knapsack: state/transition/base,
then compress.

**Top-down.** Recursion + `vector<int> memo(n+1, -1)` (sentinel valid
only if -1 is not an answer — else `vector<char> seen` + values).
`dp(i)` tries choices, memoizes. Only reachable states compute. Depth =
state chain (watch stack on long chains — bottom-up for those).

**Bottom-up.** Fill dependency order: 1D ascending (stairs/robber/coin),
2D row-major (paths/LCS/edit), intervals by length (burst/pal-partition),
subsets by sum (partition/knapsack — iterate sums DESCENDING for 0/1 to
avoid reuse! ascending = unbounded. This direction rule is the knapsack
question in one line).

**Compression.** Need only previous row/few cells? Rolling: two rows
(`O(cols)`), two vars (`O(1)` robber/stairs), 1D descending (0/1
knapsack `O(W)`). Offer compression as the follow-up — practise the
transformation until mechanical.

**Recognising DP.** "Ways/min-max/can" + small choices + compact state
(index, remainder, last, mask). 1D/2D/subset/knapsack/bitmask families —
one canonical each. No overlap → divide-and-conquer, skip memo. State
exploding → greedy/backtrack instead.

**Common mistakes.** Base/init off-by-one (dp[0] = empty!); wrong fill
order; 0/1 vs unbounded direction; int overflow in counts (long long);
sentinel collision; `vector<vector<int>>(n, vector<int>(m))` dimension
mixups (rows first!); recursion without memo (exponential).

**Interview angle.** "States × transition" time, "live table" space.
Top-down on board, bottom-up + compression offered. Point at cells the
transition reads. C++ tables make DP visible — use that.""",
            """#include <algorithm>
#include <iostream>
#include <vector>

static int coin_change(const std::vector<int>& coins, int amount) {
    const int INF = amount + 1;
    std::vector<int> table(amount + 1, INF);
    table[0] = 0;
    for (int v = 1; v <= amount; v++)
        for (int c : coins)
            if (c <= v) table[v] = std::min(table[v], table[v - c] + 1);
    return table[amount] > amount ? -1 : table[amount];
}

static int lis_n2(const std::vector<int>& a) {   // O(n^2); patience is O(n log n)
    if (a.empty()) return 0;
    std::vector<int> dp(a.size(), 1);
    int best = 1;
    for (size_t i = 1; i < a.size(); i++) {
        for (size_t j = 0; j < i; j++)
            if (a[j] < a[i]) dp[i] = std::max(dp[i], dp[j] + 1);
        best = std::max(best, dp[i]);
    }
    return best;
}

int main() {
    std::cout << coin_change({1, 2, 5}, 11) << "\\n";  // 3
    std::cout << lis_n2({10, 9, 2, 5, 3, 7, 101, 18}) << "\\n";  // 4
    return 0;
}""",
            """Solve partition-equal-subset (0/1 knapsack, 1D descending).
Then solve the judged problem `longest-increasing-subsequence`.
Practice: /practice/problems/longest-increasing-subsequence""",
        ),
        (
            "cpp-interview-mastery",
            "Google-level problem solving in C++",
            "Method + STL precision + sanitizer-clean code, every time.",
            """**Why this matters.** C++ hard interviews grade three axes:
algorithmic method, STL correctness (complexity + invalidation +
constness), and systems hygiene (no UB, no leaks, sanitizer-clean).
Five steps govern every problem; C++ adds its own checklist per step.
Rehearse both until automatic.

**Five steps, C++-flavoured.** (1) Clarify + contract: examples, sizes,
sortedness, mutability, ownership ("who frees?"), value ranges (int vs
long long!). (2) Brute force aloud with time/space/allocs. (3) Optimise
by pattern: inner search → unordered_map/set (or array table); sorted
pairs → two pointers; constrained window → counts; nested → vector
stack; levels/shortest → queue BFS; connectivity/order → DFS/topo/DSU;
k-extreme → priority_queue; counting/optimum → DP; boundary → binary
search on answer; choose/unchoose → backtracking. (4) Code: const& ins,
value/move outs, reserve, invariant comments, `'\n'` not endl. (5) Trace
examples + empty/single/dupe/max; compile `-Wall -Wextra -Werror
-fsanitize=address,undefined`; run.

**Hard favourites.** Median-two-sorted (binary partition, `O(log min)`),
trap-rain-water (two pointers), LRU (unordered_map + list::splice,
`O(1)`), serialize-tree (preorder + nulls), word ladder (BFS + generic
patterns), merge-k (heap of heads), alien dictionary (topo on char
graph). Each has a "textbook" shape — learn the shape, not the script
(follow-ups twist inputs).

**Behave senior.** `const&`/`&&` narrated; `reserve` before building;
`emplace` in place; no `new` without ownership story (prefer vector/
unique_ptr); `long long` for counts/sums; overflow-safe mids; `at()`
where unsure; structured bindings; sanitizer command offered. Talk
through invalidation ("push may reallocate — no live iterators here").

**Common mistakes.** Silent coding; memorised scripts breaking on
twists; UB (overflow/OOB) unmentioned; leaks (new without delete —
ASan would scream); `map` for unordered; `endl` everywhere; no dry-run.

**Rehearsal.** 120+ aloud-timed across the atlas; miss-log by pattern;
weekly redos; monthly from-memory vector/hash/heap/DSU/trie. Methodical
repetition manufactures "natural" talent.""",
            """#include <algorithm>
#include <iostream>
#include <vector>

// Median of two sorted arrays, O(log min(m,n)): partition so that
// max(left) <= min(right); median falls out of the boundary.
static double find_median(std::vector<int> a, std::vector<int> b) {
    if (a.size() > b.size()) a.swap(b);   // a is the smaller
    int m = a.size(), n = b.size();
    int lo = 0, hi = m;
    while (lo <= hi) {
        int i = lo + (hi - lo) / 2;       // partition of a
        int j = (m + n + 1) / 2 - i;      // partition of b
        int a_left = i == 0 ? INT_MIN : a[i - 1];
        int a_right = i == m ? INT_MAX : a[i];
        int b_left = j == 0 ? INT_MIN : b[j - 1];
        int b_right = j == n ? INT_MAX : b[j];
        if (a_left <= b_right && b_left <= a_right) {
            if ((m + n) % 2 == 1) return std::max(a_left, b_left);
            return (std::max(a_left, b_left) + std::min(a_right, b_right)) / 2.0;
        }
        if (a_left > b_right) hi = i - 1;
        else lo = i + 1;
    }
    return 0.0;  // unreachable for sorted input
}

int main() {
    std::cout << find_median({1, 3}, {2}) << "\\n";       // 2
    std::cout << find_median({1, 2}, {3, 4}) << "\\n";    // 2.5
    return 0;
}
// g++ -std=c++17 -Wall -Wextra -Werror -fsanitize=address,undefined median.cpp""",
            """Solve trapping-rain-water three ways (brute/DP/two-pointer),
all sanitizer-clean. Then solve the judged hard `median-two-sorted`.
Practice: /practice/problems/median-two-sorted""",
        ),
    ]
}

#: Module slug -> judged problem slug for the "code what you learned" button.
MODULE_PRACTICE: dict[str, str] = {
    "cpp-complexity-big-o": "binary-search",
    "cpp-strings-deep": "longest-substring",
    "cpp-vectors-arrays": "remove-duplicates-sorted",
    "cpp-hash-unordered": "group-anagrams",
    "cpp-recursion": "climb-stairs",
    "cpp-sorting-searching": "three-sum",
    "cpp-stacks-queues": "daily-temperatures",
    "cpp-linked-lists": "detect-cycle",
    "cpp-trees-heaps": "level-order-traversal",
    "cpp-graphs": "rotting-oranges",
    "cpp-dp": "longest-increasing-subsequence",
    "cpp-interview-mastery": "median-two-sorted",
}

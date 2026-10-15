"""Book-depth Python modules: data structures, algorithms and interview mastery.

These extend the scratch-first foundations and the catalogue modules with the
material that turns a reader into a problem solver: complexity analysis, the
four core structures explained to the level of their trade-offs, recursion,
sorting, stacks, linked lists, trees, heaps, graphs, dynamic programming, and
a capstone module on how Google-style interviews are actually solved.

Every module ends with a runnable example and an exercise that points at one
judged coding problem, so the learner codes what they just read. Bodies use
real newlines (triple-quoted) and are rendered as Markdown by the language
page. Standard language and algorithm facts; complexity bounds are the
textbook ones (CLRS).
"""

from __future__ import annotations

BOOK_MODULES: dict[str, list[tuple]] = {
    "python": [
        (
            "python-complexity-big-o",
            "Big-O: thinking in growth rates",
            "Why an O(n log n) solution beats O(n²) long before n gets big.",
            """**Why this matters.** Every interview problem and every slow program
comes down to one question: how does the work grow when the input grows?
Big-O is the vocabulary for answering it. A developer who can look at two
nested loops and say "quadratic — that dies at ten thousand items" will
never ship the accidental O(n²) that pages them at 2am.

**The idea in one minute.** Big-O describes the worst-case growth of steps
(or memory) as n grows, dropping constants and lower terms. `O(1)` is
constant (indexing a list), `O(log n)` halves the problem each step
(binary search), `O(n)` touches each item once, `O(n log n)` is the price
of comparison sorting, `O(n²)` touches pairs, and `O(2ⁿ)` explores
subsets. Constants do not matter because at large n the growth term
dominates: `100n` beats `n²` once n passes 100.

**How to analyse code.** Count how many times the innermost statement
runs. A single loop over n is `O(n)`. Two nested loops over n is `O(n²)`.
A loop that halves (`i *= 2`) is `O(log n)`. Sequential steps add — keep
the largest. Crucially, know your operations: `list.append` is amortised
`O(1)`, `x in list` is `O(n)`, `x in set` is `O(1)` average, slicing a
list of length k costs `O(k)`, and `sorted()` costs `O(n log n)`.
Most "my Python is slow" stories are really "I used a list where a set
belonged" — the fix is one data structure, not a faster language.

**Space matters too.** An algorithm that builds a second list is `O(n)`
space. Two pointers on the input is `O(1)`. Interviews often ask for the
follow-up: "now do it in constant space", which usually means reusing the
input as scratch space or replacing storage with arithmetic.

**Common mistakes.** Confusing worst case with average case (hash maps
are `O(1)` average but `O(n)` worst); forgetting that string
concatenation in a loop is `O(n²)` (build a list and `''.join` it);
measuring with tiny inputs where constants dominate — always test with
n = 10⁵ or more when comparing growth.

**Interview angle.** State your complexity before you code, unprompted:
"Brute force is O(n²) time and O(1) space; I can do O(n) with a hash
map." Interviewers score that sentence. Then code the better one.""",
            """import time

def has_duplicate_bruteforce(items):
    for i in range(len(items)):          # O(n²)
        for j in range(i + 1, len(items)):
            if items[i] == items[j]:
                return True
    return False

def has_duplicate_fast(items):
    seen = set()                         # O(n) time, O(n) space
    for x in items:
        if x in seen:
            return True
        seen.add(x)
    return False

data = list(range(4000))
for fn in (has_duplicate_bruteforce, has_duplicate_fast):
    start = time.perf_counter()
    fn(data)
    print(fn.__name__, f'{(time.perf_counter() - start) * 1000:.1f} ms')""",
            """Time both functions above with 8,000 items and confirm the gap
widens faster than linearly. Then solve the judged problem
`binary-search`: implement it, and explain in one paragraph why it is
O(log n) while a linear scan is O(n). Practice: /practice/problems/binary-search""",
        ),
        (
            "python-strings-deep",
            "Strings: slicing, immutability and fast patterns",
            "Slices, two pointers on text, and why you never += in a loop.",
            """**Why this matters.** Half of all interview problems are string
problems in disguise: palindromes, anagrams, windows, parsing. Python
strings are immutable sequences of Unicode characters, and that one fact
explains every performance rule: each `+` builds a new string, so
`s += ch` in a loop is quadratic. Build a list of pieces and
`''.join(pieces)` once — linear, and the professional default.

**Slicing is a superpower.** `s[i:j]` copies from i up to but excluding j;
`s[::-1]` reverses; `s[k:]` takes the tail. Negative indices count from
the end. Slicing never raises on overrun — `s[0:100]` on a short string
just stops. But remember a slice is a copy of length k, costing `O(k)`
time and space, so slicing inside a loop can silently square your work.

**The patterns that recur.** Two pointers from both ends (palindrome
check, `O(1)` space). The sliding window (longest substring without
repeats — expand right, shrink left past the duplicate). Counting with
`collections.Counter` (anagrams: two words are anagrams exactly when
their counters are equal). Normalise first: `lower()`, strip spaces,
decide what "ignore" means — most failed submissions mishandle case or
punctuation, not the algorithm.

**Methods worth memorising.** `split`/`join` (parse and rebuild),
`strip`, `startswith`, `replace`, `isalnum`/`isdigit` (validation),
and f-strings for building output. `in` on strings is substring search
(`O(n·m)` worst case, fast in practice). For heavy parsing, `re` exists
but is rarely needed in interviews — explicit loops are clearer.

**Common mistakes.** Forgetting strings are immutable (`s[0] = 'x'`
raises — build a list of chars instead); comparing with `is` instead of
`==`; using `+=` in a loop; off-by-one window edges (draw indices 0..3
on paper before coding).

**Interview angle.** Say the normalisation out loud: "I'll ignore case
and non-alphanumerics." Then two pointers or a window. Clean string code
with named helpers (`is_palindrome`, `normalise`) reads as senior.""",
            """def is_palindrome(text):
    cleaned = [c.lower() for c in text if c.isalnum()]
    left, right = 0, len(cleaned) - 1
    while left < right:
        if cleaned[left] != cleaned[right]:
            return False
        left += 1
        right -= 1
    return True

print(is_palindrome('A man, a plan, a canal: Panama'))  # True
print(is_palindrome('race a car'))                       # False
print('hello'[::-1])                                     # olleh
print('-'.join(['2026', '10', '15']))                    # 2026-10-15""",
            """Write `is_anagram(a, b)` using Counter, ignoring case and
spaces, in O(n). Then solve the judged problem `valid-palindrome` and
compare your window/pointer approach with the editorial.
Practice: /practice/problems/valid-palindrome""",
        ),
        (
            "python-lists-deep",
            "Lists: the dynamic array and its costs",
            "Amortised append, in-place tricks, and when a list is the wrong tool.",
            """**Why this matters.** The list is Python's workhorse — stack,
queue-ish buffer, result collector. Underneath it is a dynamic array:
a contiguous block of pointers that doubles when full. That design gives
`append` amortised `O(1)` (occasional copies average out), indexing
`O(1)`, but `insert(0, x)` and `pop(0)` cost `O(n)` because everything
shifts. Need a real queue? `collections.deque` pops left in `O(1)`.

**In-place thinking.** Many problems demand `O(1)` extra space: move
zeroes to the end, remove duplicates from a sorted list, rotate an
array. The shape is always the same — a write pointer lags behind a
read pointer, and you overwrite deliberately. `nums[w] = nums[r]` looks
destructive until you see the invariant: everything before w is already
correct. Practice stating the invariant; it is what interviewers listen
for.

**Comprehensions and their limits.** `[f(x) for x in items if p(x)]`
is clearer and faster than an explicit loop for building lists.
`any`/`all` with generator expressions short-circuit. But a
comprehension with three nested loops is write-only code — expand it.
And never mutate a list while iterating it (except via indices you
control); iterate over a copy or build a new list.

**Sorting and searching lists.** `list.sort()` is Timsort: `O(n log n)`,
stable (equal items keep their order — genuinely useful). `bisect`
finds insertion points in sorted lists in `O(log n)`. `heapq` turns a
list into a heap in `O(n)`. Know these three modules; reimplementing
them in an interview wastes the clock.

**Common mistakes.** `[[0]] * 3` aliases one inner list three times
(use a comprehension); `pop(0)` in a loop (quadratic — use deque);
`min`/`max`/`sum` inside a loop (each is a full scan — hoist them);
shallow copies sharing nested lists (`copy.deepcopy` when you must).

**Interview angle.** "Can I modify the input?" is always worth asking —
it decides between the `O(n)`-space clean version and the `O(1)`-space
follow-up. Offer both, code the one asked for.""",
            """from collections import deque

def move_zeroes(nums):
    write = 0  # invariant: nums[:write] holds the non-zeroes, in order
    for read in range(len(nums)):
        if nums[read] != 0:
            nums[write], nums[read] = nums[read], nums[write]
            write += 1
    return nums

print(move_zeroes([0, 1, 0, 3, 12]))  # [1, 3, 12, 0, 0]

queue = deque([1, 2, 3])
queue.popleft()   # O(1), unlike list.pop(0)
queue.append(4)
print(list(queue))""",
            """Implement `remove_duplicates_sorted(nums)` in place, returning
the new length, in O(n)/O(1). Then solve the judged problem
`move-zeroes` and state its invariant in your own words.
Practice: /practice/problems/move-zeroes""",
        ),
        (
            "python-dicts-sets",
            "Dicts and sets: hashing, the interview cheat code",
            "Average O(1) lookup, and the patterns (complement, frequency, seen) behind dozens of problems.",
            """**Why this matters.** If lists are the workhorse, hash maps are
the cheat code. "Have I seen this before?" in `O(1)` turns Two Sum,
anagrams, first-unique, longest-consecutive and dozens more from `O(n²)`
into `O(n)`. Python's `dict` and `set` are superbly engineered hash
tables; your job is recognising when a problem is secretly a lookup
problem.

**How hashing works (enough to reason).** A hash function maps each key
to a bucket; equal keys must hash equally. Lookup hashes the key and
checks that one bucket — `O(1)` average, `O(n)` worst case if everything
collides (pathological, vanishingly rare with good hashes). Keys must be
hashable: ints, strings, tuples of hashables — never lists or dicts.
Insertion order is preserved (guaranteed since 3.7), which `group-anagrams`
style problems exploit for deterministic output.

**The three patterns.** (1) *Complement*: for each x, need `target - x`
already seen (Two Sum). (2) *Frequency*: count with `Counter` or
`dict.get(k, 0) + 1`, then decide (top-k, anagrams, ransom note).
(3) *Seen*: remember visited states to detect repeats or cycles
(duplicate detection, happy numbers, visited cells in a grid). If your
brute force has an inner "search for y" loop, that loop is begging to
become a set.

**Sets deserve equal billing.** Membership, dedup (`list(set(items))`
when order does not matter), and set algebra (`a & b`, `a - b`) for
"in both / only in first" questions. `setdefault` and
`collections.defaultdict(list)` remove the tedious "if key not in d"
dance when grouping.

**Common mistakes.** Mutating a dict while iterating it (iterate over
`list(d)`); using a list as a key (use a tuple); forgetting `get`'s
default; assuming `Counter` subtraction clips at zero the way you expect
(it keeps negatives unless you use `+`/`-` operators between Counters);
ordering assumptions in older Pythons.

**Interview angle.** Name the trade explicitly: "a hash map buys O(n)
time for O(n) space." Then mention the no-space alternative when one
exists (sorting first, bit tricks for fixed alphabets). That sentence
signals engineering judgement, not just memorisation.""",
            """from collections import Counter, defaultdict

def two_sum(nums, target):
    seen = {}  # value -> index
    for i, x in enumerate(nums):
        need = target - x
        if need in seen:
            return [seen[need], i]
        seen[x] = i
    return []

def group_anagrams(words):
    groups = defaultdict(list)
    for w in words:
        groups[''.join(sorted(w))].append(w)
    return [sorted(g) for g in groups.values()]

print(two_sum([2, 7, 11, 15], 9))          # [0, 1]
print(group_anagrams(['eat', 'tea', 'tan', 'ate', 'nat', 'bat']))
print(Counter('hello')['l'])               # 2""",
            """Solve `contains-duplicate` three ways: brute force, sorting,
and a set — and time all three at n = 50,000. Then solve the judged
problem `two-sum` and write down why checking before inserting avoids
using one element twice. Practice: /practice/problems/two-sum""",
        ),
        (
            "python-recursion",
            "Recursion: base cases, stacks and memoization",
            "Think in self-similar subproblems; let the call stack do the bookkeeping.",
            """**Why this matters.** Trees, backtracking, divide-and-conquer
and most dynamic programming are recursion wearing different hats.
Recursion is not magic: a function that calls itself with a smaller
input, where every chain of calls reaches a base case. If you can write
the base case and the reduction step, the machine handles the rest.

**The template.** (1) Base case — the smallest input, answered directly.
(2) Recursive step — solve smaller instance(s), combine. (3) Progress —
every call must move toward the base case, or you recurse forever.
Trace small inputs by hand: `fact(3) = 3 * fact(2)`, and trust the
recursion for the rest. Professionals do not simulate the whole tree;
they verify the base case and the combination step.

**The cost you must see.** Each call is a stack frame. Depth d costs
`O(d)` space, and Python's default limit is 1000 frames (`RecursionError`
beyond that — `sys.setrecursionlimit` raises the ceiling but not the
wisdom; deep recursion in Python is slow). Time is the number of calls:
naive Fibonacci makes ~φⁿ calls — exponential. `functools.lru_cache`
memoizes repeated subproblems and collapses it to `O(n)`. Recognising
"same subproblem solved twice" is the entire gateway to dynamic
programming.

**Where recursion shines.** Tree traversals (the code mirrors the
structure), backtracking (N-Queens, subsets, permutations — choose,
explore, unchoose), binary search and mergesort (halving). Where it
does not: simple loops (iteration is clearer), deep linear chains
(use a loop or an explicit stack), and hot paths (call overhead).

**Common mistakes.** Missing or unreachable base case (infinite
recursion); no progress toward it; recomputing shared subproblems
(add `lru_cache`); returning the recursive call's value incorrectly
(the classic "forgot to return"); mutable default arguments
accumulating across calls.

**Interview angle.** Always state depth/space: "recursion depth is the
tree height — O(log n) balanced, O(n) skewed." Offer the iterative
version with an explicit stack as the follow-up. That pair answers the
question and the unasked next question.""",
            """from functools import lru_cache

def fib(n):
    if n < 2:            # base cases
        return n
    return fib(n - 1) + fib(n - 2)   # exponential without memoization

@lru_cache(maxsize=None)
def fib_fast(n):
    if n < 2:
        return n
    return fib_fast(n - 1) + fib_fast(n - 2)  # O(n) time now

print([fib_fast(i) for i in range(10)])
print(fib_fast(100))  # instant; fib(100) would outlive you""",
            """Write `climb_stairs(n)` recursively with lru_cache (1 or 2
steps at a time), then convert it to bottom-up with two variables.
Then solve the judged problem `climb-stairs`.
Practice: /practice/problems/climb-stairs""",
        ),
        (
            "python-sorting-searching",
            "Sorting and searching: order as a tool",
            "Timsort, binary search, and turning sortedness into answers.",
            """**Why this matters.** Sorted order is information. Binary search
turns `O(n)` lookups into `O(log n)`; sorting first turns many `O(n²)`
pair problems into `O(n log n)`; merge patterns underlie half of
divide-and-conquer. Python gives you world-class sorting — the skill is
knowing what sortedness buys you.

**Sorting in Python.** `sorted(items)` returns new; `list.sort()`
sorts in place. Both are Timsort: `O(n log n)` time, `O(n)` space,
stable. The `key` function is the whole game: `sort(key=len)`,
`sort(key=lambda p: (p[0], -p[1]))` for multi-level order. `reverse=True`
exists but negating in the key keeps stability semantics obvious.
`heapq.nsmallest(k, items)` beats full sorting when k is small
(`O(n log k)`).

**Binary search, properly.** Maintain the invariant: "if the target is
present, it is within [lo, hi]". Compare mid, discard half. `bisect_left`
/`bisect_right` implement it for insertion points — use them rather than
hand-rolling, except when the interview explicitly asks for the code.
The classic variants (first/last occurrence, rotated array, peak, sqrt,
"koko eats bananas") are all the same loop with a different predicate:
find the boundary where a condition flips from False to True. Learn to
see "smallest x such that feasible(x)" — that sentence is binary search
on the answer.

**Common mistakes.** Off-by-one loop conditions (`lo <= hi` with
`mid ± 1` updates is the safe standard form); integer overflow in other
languages (`mid = lo + (hi - lo) // 2` — good habit everywhere);
forgetting the input must be sorted (or sorting it and losing original
indices — pair values with indices first); using linear `in` on a
sorted list out of habit.

**Interview angle.** When stuck, ask: "does sorting help?" For pairs,
triples, intervals and duplicates the answer is usually yes. State the
cost honestly: sorting is `O(n log n)`, so a hash map wins when order
is irrelevant — compare both, then choose.""",
            """from bisect import bisect_left

def search(nums, target):
    lo, hi = 0, len(nums) - 1
    while lo <= hi:                      # invariant: target in [lo, hi] if present
        mid = lo + (hi - lo) // 2
        if nums[mid] == target:
            return mid
        if nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1

print(search([-1, 0, 3, 5, 9, 12], 9))    # 4
print(search([-1, 0, 3, 5, 9, 12], 2))    # -1

pairs = [('b', 2), ('a', 3), ('a', 1)]
print(sorted(pairs, key=lambda p: (p[0], p[1])))  # multi-level key""",
            """Implement `first_occurrence(nums, target)` with binary search
(leftmost index or -1). Then solve the judged problem
`merge-intervals`: sort by start, then merge in one pass.
Practice: /practice/problems/merge-intervals""",
        ),
        (
            "python-stacks-queues",
            "Stacks and queues: order of processing",
            "LIFO vs FIFO, monotonic stacks, and BFS in ten lines.",
            """**Why this matters.** Stacks and queues are not "easy data
structures" — they are control flow. A stack says "handle the most
recent unfinished thing" (undo, backtracking, nested brackets). A queue
says "handle things in arrival order" (printing, BFS levels). Choosing
between them decides what your program does first, which is often the
whole algorithm.

**Stacks in Python.** A list is a fine stack: `append` pushes, `pop()`
pops, `stack[-1]` peeks — all amortised `O(1)`. Valid parentheses is
the archetype: push openers, match closers, empty at the end means
valid. The deeper pattern is the *monotonic stack*: keep items in
increasing (or decreasing) order to find "next greater element", daily
temperatures, or largest-rectangle heights in one `O(n)` pass. Each item
is pushed and popped once — that is the whole complexity argument.

**Queues and deques.** `collections.deque` gives `O(1)` appends and pops
from both ends (`popleft` for queues; `list.pop(0)` is `O(n)` — never).
BFS is a queue: seed with the start, pop left, push unvisited neighbours.
The queue guarantees level order, which is why BFS finds shortest paths
in unweighted graphs. `queue.Queue` is for threads; in algorithms, always
`deque`.

**Common mistakes.** Peeking/popping an empty stack (guard with
`if stack`); using a list as a queue (`pop(0)` quadratic); forgetting
visited-sets in BFS (infinite loops on cyclic graphs); implementing a
queue with two stacks when `deque` exists (fine as an exercise, silly
in production).

**Interview angle.** "Last unmatched opener" and "process in layers"
are trigger phrases — say "that sounds like a stack/BFS" early.
Monotonic-stack problems look hard until you have seen one; rehearse
next-greater-element until the push/pop discipline is muscle memory.""",
            """from collections import deque

def is_valid(s):
    pairs = {')': '(', ']': '[', '}': '{'}
    stack = []
    for ch in s:
        if ch in pairs:                       # closer: must match the top
            if not stack or stack.pop() != pairs[ch]:
                return False
        else:
            stack.append(ch)
    return not stack

def bfs_levels(start, neighbours):
    seen, queue, order = {start}, deque([start]), []
    while queue:
        node = queue.popleft()
        order.append(node)
        for nxt in neighbours(node):
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return order

print(is_valid('()[]{}'), is_valid('([)]'))   # True False""",
            """Solve next-greater-element with a monotonic stack in O(n):
for each item, pop smaller items and record their answer. Then solve
the judged problem `valid-parentheses`.
Practice: /practice/problems/valid-parentheses""",
        ),
        (
            "python-linked-lists",
            "Linked lists: pointers without the pain",
            "Nodes, the dummy head, and fast/slow pointers.",
            """**Why this matters.** Nobody chooses linked lists for storage
anymore — but interviews love them because they test pointer discipline:
rewiring references without losing the rest of the structure. In Python
you build nodes as tiny objects; the ideas (dummy heads, two pointers,
in-place reversal) transfer directly to C, Java and every systems
interview.

**The model.** A node holds a value and a reference to the next node.
The list is just its head reference; the empty list is `None`. Every
operation is local: to insert after a node, point the new node where it
pointed, then point it at the new node. Order matters — wire the new
node first or you orphan the tail. Draw three boxes and move arrows by
hand before coding; every linked-list bug is a lost reference.

**The three tricks.** (1) *Dummy head*: a throwaway node before the real
head eliminates "what if the head changes?" special cases (removal,
merging, partitioning). (2) *Fast/slow pointers*: advance one pointer
twice as fast — they meet iff there is a cycle (Floyd), and slow lands
mid-list when fast finishes. (3) *In-place reversal*: keep `prev`,
`cur`, `nxt`; redirect, advance. Three variables, `O(1)` space, and the
most-asked list routine in existence.

**Python specifics.** Define `ListNode` with `__init__(self, value=0,
nxt=None)`. Helpers `build(values)` and `to_list(head)` make testing
painless. Recursion is elegant (`reverse` in 5 lines) but costs `O(n)`
stack — iterative is the production answer. `is` compares node identity
(same object), `==` compares values — cycle detection needs `is`.

**Common mistakes.** Losing the reference to the rest of the list
(save `nxt` first); forgetting the empty/single-node cases; returning
the old head after it moved (return `prev`/`dummy.next`); infinite
loops from a cycle you created while rewiring.

**Interview angle.** Narrate the invariant: "everything before prev is
reversed; cur is next." Run one example by hand on the whiteboard. List
problems are graded on discipline, not cleverness — slow, correct
pointer moves beat fast, lost ones.""",
            """class ListNode:
    def __init__(self, value=0, nxt=None):
        self.value = value
        self.next = nxt

def build(values):
    dummy = tail = ListNode()
    for v in values:
        tail.next = ListNode(v)
        tail = tail.next
    return dummy.next

def to_list(head):
    out = []
    while head:
        out.append(head.value)
        head = head.next
    return out

def reverse_list(head):
    prev, cur = None, head
    while cur:                       # invariant: before prev is reversed
        nxt = cur.next               # 1. save the rest
        cur.next = prev              # 2. redirect
        prev, cur = cur, nxt         # 3. advance
    return prev

print(to_list(reverse_list(build([1, 2, 3, 4, 5]))))  # [5, 4, 3, 2, 1]""",
            """Write `has_cycle(head)` with fast/slow pointers in O(1) space.
Then solve the judged problem `reverse-linked-list` iteratively, and
explain why the recursive version risks RecursionError on long lists.
Practice: /practice/problems/reverse-linked-list""",
        ),
        (
            "python-trees-heaps",
            "Trees and heaps: recursion over branching structure",
            "Traversals, BST order, and priority queues with heapq.",
            """**Why this matters.** Trees are where recursion earns its keep:
file systems, DOMs, indexes, parse trees, decision paths. And heaps
answer "the k most/least important" in streaming fashion. Together they
cover a huge slice of medium and hard interview problems.

**Binary trees.** Each node has left/right children; depth is edges from
the root. The four traversals: preorder (node, left, right — copy a
tree), inorder (left, node, right — yields sorted order for a BST),
postorder (children first — delete safely, compute heights), level
order (BFS with a queue — row by row). Most tree problems are one
sentence once you pick the traversal: max depth is postorder ("1 + max
of children"), symmetry compares mirrors, diameter tracks the best
through-path during a height computation.

**BSTs and heaps.** A binary search tree keeps left < node < right, so
search/insert/delete are `O(h)` — `O(log n)` balanced, `O(n)` skewed
(know that `sortedcontainers`/balanced trees exist; interviews accept
the analysis). A heap is a complete tree with the min (or max) on top:
`heapq.heappush/heappop` in `O(log n)`, `heapq.heapify` in `O(n)`.
Top-k frequent, kth largest, merge-k-sorted, running median (two heaps)
— all heap problems once you see "extreme of a stream".

**Python specifics.** `heapq` is min-heap only: store `(-x)` for max
behaviour, tuples `(priority, item)` for objects (add a counter to
break ties when items are not comparable). Recursion depth is tree
height — fine balanced, dangerous skewed; iterative DFS with an
explicit stack is the robust alternative.

**Common mistakes.** Forgetting the `None` base case; confusing depth
(edges) with levels (nodes); mutating during traversal; heap tuple
comparison exploding on ties; rebuilding a heap per query instead of
maintaining one (`O(n log n)` vs `O(n log k)`).

**Interview angle.** Draw the tree. State the traversal and why.
For heaps, say "k is small relative to n, so O(n log k) beats sorting."
Tree problems reward the candidate who picks the right walk — the code
is then five lines.""",
            """import heapq
from collections import deque

class TreeNode:
    def __init__(self, value=0, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right

def max_depth(root):
    if not root:
        return 0
    return 1 + max(max_depth(root.left), max_depth(root.right))

def level_order(root):
    if not root:
        return []
    out, queue = [], deque([root])
    while queue:
        level = []
        for _ in range(len(queue)):
            node = queue.popleft()
            level.append(node.value)
            if node.left: queue.append(node.left)
            if node.right: queue.append(node.right)
        out.append(level)
    return out

def kth_largest(nums, k):
    heap = []
    for x in nums:
        heapq.heappush(heap, x)
        if len(heap) > k:
            heapq.heappop(heap)
    return heap[0]

root = TreeNode(3, TreeNode(9), TreeNode(20, TreeNode(15), TreeNode(7)))
print(max_depth(root), level_order(root))   # 3 [[3], [9, 20], [15, 7]]
print(kth_largest([3, 2, 1, 5, 6, 4], 2))   # 5""",
            """Write `is_symmetric(root)` (mirror comparison) recursively.
Then solve the judged problem `max-depth-binary-tree` and the heap
problem `kth-largest`, stating both complexities.
Practice: /practice/problems/max-depth-binary-tree""",
        ),
        (
            "python-graphs",
            "Graphs: BFS, DFS and the shapes they solve",
            "Grids are graphs; shortest path is BFS; cycles need colours.",
            """**Why this matters.** Networks, maps, dependencies, friendships,
grids — graphs model connection itself. The good news: nearly every
graph problem is BFS or DFS plus one twist. Learn the two traversals
cold and the family (islands, shortest path, topo sort, cycle detect,
union-find) falls into place.

**Representations.** Adjacency list (`dict[node, list[neighbours]]`)
for sparse graphs — almost always. Grids are implicit graphs: each cell
neighbours up/down/left/right; mark visited in place (`grid[r][c] =
'#visited'`) or with a set. Edge lists suit union-find. Choose by
operation: neighbour iteration favours adjacency lists.

**BFS vs DFS.** BFS (queue) explores in waves — first arrival is the
shortest path in unweighted graphs (rotting oranges minutes, grid
distance). DFS (recursion or explicit stack) explores depth-first —
connectivity, cycle detection, topological order, path existence. Same
`O(V + E)` time; BFS uses `O(V)` queue space, DFS `O(h)` stack. On
grids, both are `O(rows × cols)`.

**The patterns.** *Flood fill / islands*: DFS/BFS from each unvisited
land cell, count components. *Shortest path*: BFS from source(s) —
multi-source BFS (all rotten oranges at once) is a favourite twist.
*Cycle detect*: directed — three colours (white/grey/black; grey
revisit means cycle) or Kahn's algorithm; undirected — DFS with parent
tracking. *Topo sort*: DFS finishing order or Kahn's indegree peeling
(course schedules). *Union-find*: dynamic connectivity with path
compression (provinces, redundant connections).

**Common mistakes.** No visited set (exponential re-visits or infinite
loops); mutating the grid when the caller needs it (copy first);
recursion depth on large grids (use iterative); forgetting disconnected
components (loop over all nodes, not one BFS); mixing directed and
undirected logic.

**Interview angle.** Say the model first: "cells are nodes, adjacency
is 4-directional." Then pick BFS (shortest) or DFS (connectivity).
Interviewers grade the modelling sentence as much as the code.""",
            """from collections import deque

def num_islands(grid):
    if not grid:
        return 0
    rows, cols, count = len(grid), len(grid[0]), 0
    def flood(r, c):
        if not (0 <= r < rows and 0 <= c < cols) or grid[r][c] != '1':
            return
        grid[r][c] = '#'                       # mark visited in place
        flood(r + 1, c); flood(r - 1, c)
        flood(r, c + 1); flood(r, c - 1)
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == '1':
                count += 1
                flood(r, c)
    return count

def shortest_path_binary_matrix(grid):
    n = len(grid)
    if grid[0][0] or grid[n - 1][n - 1]:
        return -1
    queue = deque([(0, 0, 1)])
    grid[0][0] = 1
    while queue:
        r, c, dist = queue.popleft()
        if (r, c) == (n - 1, n - 1):
            return dist
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nr, nc = r + dr, c + dc
                if 0 <= nr < n and 0 <= nc < n and grid[nr][nc] == 0:
                    grid[nr][nc] = 1
                    queue.append((nr, nc, dist + 1))
    return -1

print(num_islands([list('11110'), list('11010'), list('11000'), list('00000')]))  # 1""",
            """Implement multi-source BFS for `rotting-oranges` (minutes until
no fresh orange, or -1). Then solve the judged problem
`number-of-islands` both with DFS and with BFS.
Practice: /practice/problems/number-of-islands""",
        ),
        (
            "python-dp",
            "Dynamic programming: state, transition, base case",
            "Memoized recursion first, tabulation for speed, rolling arrays for space.",
            """**Why this matters.** DP is the most feared interview topic and
the most formulaic once you see the structure. Every DP problem asks:
define the state (what subproblem?), the transition (how do smaller
states combine?), the base cases. Climbing stairs, house robber, coin
change, LIS, edit distance, knapsack — all the same three lines with
different states.

**The two styles.** *Top-down* (memoized recursion): write the naive
recursion, add `@lru_cache`. It only computes reachable states and
reads naturally — start here, always. *Bottom-up* (tabulation): fill a
table from base cases upward; same time, often better constants, and it
unlocks the space optimisation: if `dp[i]` needs only `dp[i-1]` (and
maybe `dp[i-2]`), keep rolling variables instead of the table
(`O(n)` → `O(1)` space). House robber collapses to two variables;
that collapse is a standard follow-up.

**Recognising DP.** Optimal substructure (optimal solution built from
optimal sub-solutions) plus overlapping subproblems (naive recursion
repeats work). Trigger phrases: "in how many ways", "minimum/maximum
cost", "can you reach/partition", counting with constraints. If choices
at each step are small and the future depends only on a compact state
(index, remaining sum, last choice), it is probably DP. If the state
space explodes, think greedy or backtracking instead.

**Classic states.** 1D index (`dp[i]` = best up to i: stairs, robber,
decode ways). 2D grid/intervals (`dp[i][j]`: unique paths, LCS, edit
distance, palindromic substrings). Subset-sum boolean (`can[i][s]`:
partition, coin change variants). Knapsack (value with weight limit).
Learn one canonical per family and map new problems onto them.

**Common mistakes.** Wrong base cases (off-by-one on empty prefix —
`dp[0]` usually means "empty input"); iterating in an order that reads
unfilled cells; forgetting the "do nothing / skip" transition; state too
big (add a dimension only when the future truly needs it); recursion
without memoization (exponential) or memoization with unhashable state
(use tuples).

**Interview angle.** Start top-down on the board ("the recursion is
obvious, memoize it"), then offer bottom-up with the space cut. Stating
"time O(states × transition), space O(states)" unprompted is the mark
of someone who has internalised it.""",
            """from functools import lru_cache

def coin_change(coins, amount):
    @lru_cache(maxsize=None)
    def dp(remaining):                    # state: amount left
        if remaining == 0:
            return 0                    # base: exact change, no coins
        if remaining < 0:
            return float('inf')         # base: overshot, impossible
        return 1 + min(dp(remaining - c) for c in coins)
    ans = dp(amount)
    return -1 if ans == float('inf') else ans

def coin_change_bottom_up(coins, amount):
    INF = amount + 1
    table = [INF] * (amount + 1)
    table[0] = 0
    for value in range(1, amount + 1):    # transition over smaller states
        for coin in coins:
            if coin <= value:
                table[value] = min(table[value], table[value - coin] + 1)
    return -1 if table[amount] > amount else table[amount]

print(coin_change([1, 2, 5], 11))         # 3  (5+5+1)
print(coin_change_bottom_up([2], 3))      # -1""",
            """Solve `house-robber` top-down, then bottom-up with O(1) space
(two rolling variables). Then solve the judged problem `coin-change`
and explain why greedy fails on coins [1, 3, 4], amount 6.
Practice: /practice/problems/coin-change""",
        ),
        (
            "python-interview-mastery",
            "Google-level problem solving: the method",
            "Clarify, brute force, optimise, code, test — on purpose, every time.",
            """**Why this matters.** Hard interviews are not won by knowing
more algorithms — they are won by method. The same five steps solve Two
Sum and trapping rain water; what changes is only which pattern you
reach for in step three. This module makes the method explicit so you
can rehearse it until it is automatic.

**The five steps.** (1) *Clarify*: restate the problem, pin examples,
ask about empties, sizes, sortedness, mutability ("may I modify the
input?"). Two minutes here saves twenty. (2) *Brute force*: state the
naive solution and its complexity out loud — it proves understanding
and sets the bar. (3) *Optimise*: hunt the wasted work. An inner search
loop wants a hash map; overlapping scans want two pointers or a window;
"extreme of a stream" wants a heap; repeated subproblems want memo;
"kth / boundary" wants binary search on the answer. Name the pattern
before coding. (4) *Code*: small helpers, named variables, invariant in
a comment. (5) *Test*: trace the given examples plus empty, single,
all-same, and max-size inputs by hand.

**The pattern atlas (memorise the triggers).** Complement/frequency →
hash map. Sorted pairs/triples → two pointers. Substring/subarray with
constraint → sliding window. Nested/matched → stack. Levels/shortest →
BFS. Connectivity/cycles/order → DFS/topo/union-find. "K smallest/
largest" → heap. "In how many ways / min cost" → DP. "Smallest x with
property P" → binary search on answer. "Choose/explore/unchoose" →
backtracking. Every hard problem you will meet is one of these, or two
composed.

**Behave like an engineer.** State complexity before and after. Handle
edges without being asked. When stuck, simplify: solve n=3 by hand and
generalise; solve 1D before 2D; assume sorted, then remove the
assumption. Talk continuously — interviewers cannot credit silent
brilliance. And practise aloud with a timer; silent practice does not
transfer.

**Common mistakes.** Coding before clarifying (solves the wrong
problem); jumping to DP before checking hash/two-pointer/window
(overkill); memorised solutions recited without adaptation (fails the
follow-up twist); no complexity statement; untested edge cases.

**The honest truth.** Method plus ~120 solved problems across the atlas
beats raw talent. Track which patterns you miss, drill those, and redo
each miss after a week. That loop is the whole game.""",
            """def trap_rain_water(height):
    # Two pointers: the lower side decides, because water is bounded by min(l, r).
    left, right = 0, len(height) - 1
    left_max = right_max = water = 0
    while left < right:
        if height[left] < height[right]:
            left_max = max(left_max, height[left])
            water += left_max - height[left]
            left += 1
        else:
            right_max = max(right_max, height[right])
            water += right_max - height[right]
            right -= 1
    return water

print(trap_rain_water([0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]))  # 6
# Complexity: O(n) time, O(1) space. Brute force was O(n²): for each bar,
# scan both sides for the max. The pointers remove the re-scan.""",
            """Solve `trapping-rain-water` three ways: brute force O(n²), DP
with precomputed maxima O(n)/O(n), then two pointers O(n)/O(1) — and
explain each transition as if to an interviewer. Then attempt the
judged hard problem of the same name.
Practice: /practice/problems/trapping-rain-water""",
        ),
    ]
}

#: Module slug -> judged problem slug for the "code what you learned" button.
MODULE_PRACTICE: dict[str, str] = {
    "python-complexity-big-o": "binary-search",
    "python-strings-deep": "valid-palindrome",
    "python-lists-deep": "move-zeroes",
    "python-dicts-sets": "two-sum",
    "python-recursion": "climb-stairs",
    "python-sorting-searching": "merge-intervals",
    "python-stacks-queues": "valid-parentheses",
    "python-linked-lists": "reverse-linked-list",
    "python-trees-heaps": "max-depth-binary-tree",
    "python-graphs": "number-of-islands",
    "python-dp": "coin-change",
    "python-interview-mastery": "trapping-rain-water",
}

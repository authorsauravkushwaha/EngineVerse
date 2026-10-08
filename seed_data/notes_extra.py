"""Per-topic note content that the core topic tables leave out.

The topic entries in ``topics_core`` and ``topics_cse`` carry the thirteen
section bodies, but four of them were left empty for most topics:

    derivation   3 of 48 topics had one
    industry     3 of 48
    formula     21 of 48
    example     43 of 48

Rather than editing two large topic tables, the gaps are filled here keyed by
topic slug, and ``section_body`` falls back to this module. A key that matches
no topic is an error at seed time, not a silent no-op — the same rule the
diagram and flashcard builders follow.

Content rules:

* A derivation must derive something. Where a topic has no mathematics, the
  section derives the cost or the invariant that governs it, which is the
  equivalent argument; nothing is invented to fill the box.
* Formulas use the same shape as ``topic["formula"]`` so ``formula_body()``
  renders them identically — name, latex, variables with symbol/meaning/unit,
  and the conditions under which they hold.
* Industry sections describe what practitioners actually do, including where
  that differs from the textbook version.
"""

from __future__ import annotations

#: topic slug -> markdown derivation
DERIVATIONS: dict[str, str] = {}

#: topic slug -> markdown industry note
INDUSTRY: dict[str, str] = {}

#: topic slug -> formula dict, same shape as ``topic["formula"]``
FORMULAS: dict[str, dict] = {}

#: topic slug -> example dict, same shape as ``topic["example"]``
EXAMPLES: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Data structures and programming
# ---------------------------------------------------------------------------

DERIVATIONS.update({
    "arrays": """Indexed access is a single multiply and an add, and it is worth
showing why that is all it takes.

An array is one contiguous block, so element *i* starts exactly *i* element-widths
past the base address:

$$\\text{addr}(a[i]) = \\text{base} + i \\times w$$

where $w$ is `sizeof(element)`. Both `base` and `w` are known before the program
runs, and $i$ is the only input, so the address is computed in constant time
with no search.

**Why a growing array is amortised O(1) despite copying.** Suppose the capacity
doubles each time it fills. Reaching $n$ elements requires copies of size
$1 + 2 + 4 + \\dots + n$, a geometric series:

$$\\sum_{k=0}^{\\log_2 n} 2^{k} = 2n - 1$$

So $n$ appends cost under $2n$ operations in total, which is $O(1)$ per append
*on average*. The word amortised is doing real work: any single append that
triggers the resize is $O(n)$.""",

    "linked-lists": """The cost of finding an element follows from where the nodes live.

A node holds a value and a pointer to the next node. Nothing records *where* a
node is except the node before it, so the only way to reach the $k$-th node is
to start at the head and follow $k$ pointers:

$$T(k) = T(k-1) + O(1), \\qquad T(0) = O(1)$$

Unrolling gives $T(k) = O(k)$, and for a value that could be anywhere in a list
of $n$ nodes the expected cost is

$$E[\\text{search}] = \\frac{1}{n}\\sum_{k=1}^{n} k = \\frac{n+1}{2} = O(n)$$

**Why insertion at the head is still O(1).** It needs two pointer writes and
touches no other node, because no other node points *at* the head except the
head pointer itself. This asymmetry — O(1) to add, O(n) to find — is the whole
design trade-off, and it is why a linked list is the wrong choice when the
workload is mostly lookup.""",

    "stacks-queues": """Both structures are O(1) per operation, but the stack's guarantee
needs an amortised argument.

**Queue.** With a circular buffer, `front` and `rear` are indices that wrap
modulo the capacity, so enqueue and dequeue each move one index:

$$\\text{rear} \\leftarrow (\\text{rear} + 1) \\bmod C$$

No element is ever shifted, so both are $O(1)$ worst case, not just on average.

**Stack on a dynamic array.** Push is O(1) except when the array is full, which
triggers a doubling copy. Across $n$ pushes the total copy work is
$1 + 2 + 4 + \\dots + n = 2n - 1$, so

$$\\text{amortised cost per push} = \\frac{2n - 1}{n} < 2 = O(1)$$

**The recursion depth bound.** A stack frame is allocated per call and freed on
return, so depth equals the number of calls that have not yet returned. A
recursion with no reachable base case never returns, and depth grows until the
frame limit — which is why the failure mode is a stack overflow rather than a
wrong answer.""",

    "binary-trees-traversals": """Two relations govern every binary tree: how many nodes fit at a
given height, and what a traversal costs.

**Nodes at a height.** The root is at height 0 and has one node. Every node has
at most two children, so height $h$ holds at most $2^{h}$ nodes:

$$N(h) = \\sum_{i=0}^{h} 2^{i} = 2^{h+1} - 1$$

Inverting gives the minimum height for $n$ nodes:

$$h_{\\min} = \\lceil \\log_2 (n+1) \\rceil - 1$$

**Traversal cost.** Every visit does $O(1)$ work plus one recursive call per
child. With $n$ nodes there are $n-1$ edges, so the total call count is
$O(n)$ — a traversal is linear no matter how the tree is shaped.

**Why in-order sorts a BST.** In-order recurses left, visits, recurses right. By
the BST invariant every value in the left subtree is smaller, so all of them are
printed before the node, and by the same argument all larger values are printed
after. The output is sorted by construction, with no comparison step.""",

    "binary-search-trees": """Search cost follows from how much of the tree each comparison
eliminates.

At each node the target is compared once and one entire subtree is discarded, so
the remaining candidates halve:

$$T(h) = T(h-1) + O(1), \\qquad T(0) = O(1) \\;\\Rightarrow\\; T(h) = O(h)$$

For a balanced tree $h = \\lceil \\log_2 (n+1) \\rceil$, giving $O(\\log n)$.

**The degenerate case.** Insert keys in ascending order. Each new key is larger
than every existing one, so it always becomes a right child, and the tree has
height $n-1$:

$$T(n) = O(n)$$

It has become a linked list. This is not a corner case — sorted input is common
— which is exactly why self-balancing trees exist. An AVL tree enforces that the
heights of the two subtrees of any node differ by at most one, which bounds
height at

$$h \\le 1.44 \\log_2 (n+2)$$

and restores $O(\\log n)$ regardless of insertion order.""",

    "graphs-traversals": """Traversal cost is set by the representation, not by the algorithm.

Both BFS and DFS visit each vertex once and examine each edge once, using a
`visited` set to avoid re-entering a cycle:

$$T = O(|V|) \\cdot c_{\\text{visit}} + O(|E|) \\cdot c_{\\text{edge}}$$

**Adjacency list.** Every edge appears in exactly one list (twice if
undirected), so scanning all lists touches $O(|E|)$ entries and the total is

$$T = O(|V| + |E|)$$

**Adjacency matrix.** Testing whether a vertex has any unvisited neighbour means
scanning a full row of length $|V|$, and this is done for every vertex:

$$T = O(|V|^2)$$

which is worse whenever $|E| \\ll |V|^2$ — that is, for sparse graphs, which are
the common case.

**Why BFS finds shortest paths.** BFS finishes every vertex at distance $d$
before starting distance $d+1$, because a queue serves nodes in the order they
were discovered. So the first time a vertex is reached is along a shortest path.
DFS has no such property; it reaches vertices in depth-first order, which says
nothing about distance.""",

    "hash-tables": """The average-case guarantee is a statement about the load factor.

Let $n$ be the number of keys and $m$ the number of buckets. Define

$$\\alpha = \\frac{n}{m}$$

**Expected chain length.** Assume the hash function is uniform, so each key
lands in any given bucket with probability $1/m$. For a specific key, the
expected number of *other* keys sharing its bucket is

$$E[\\text{collisions}] = (n-1) \\cdot \\frac{1}{m} = \\frac{n-1}{m} \\approx \\alpha$$

So a lookup hashes once, reaches the bucket, then scans about $\\alpha$ entries:

$$T_{\\text{lookup}} = O(1 + \\alpha)$$

**Why this is O(1).** If resizing keeps $\\alpha$ bounded by a constant —
typically the table doubles when $\\alpha$ exceeds about 0.75 — then
$O(1 + \\alpha) = O(1)$. The constant is a design choice, not a law.

**Why the worst case is O(n).** If the hash function maps every key to one
bucket, $\\alpha = n$ and the bucket is a linked list. A uniform hash is
therefore not an optimisation; it is the assumption the whole data structure
rests on.""",

    "heaps-priority-queues": """Three costs matter, and the third surprises people.

**Sift-down is O(log n).** A heap is a complete binary tree, so its height is
$h = \\lfloor \\log_2 n \\rfloor$. Sifting moves a node down at most one level per
step:

$$T_{\\text{sift}} = O(h) = O(\\log n)$$

**Heapsort is O(n log n).** Extracting the max swaps the root with the last
element and sifts down, costing $O(\\log n)$, done $n$ times:

$$T = \\sum_{k=1}^{n} O(\\log k) = O(n \\log n)$$

**Building the heap is O(n), not O(n log n).** Sifting is called on every
internal node, but a node at height $h$ costs $O(h)$ and there are about
$n / 2^{h+1}$ such nodes:

$$T = \\sum_{h=0}^{\\log n} \\frac{n}{2^{h+1}} \\cdot O(h)
  = O\\!\\left(n \\sum_{h=0}^{\\infty} \\frac{h}{2^{h}}\\right) = O(n)$$

because $\\sum h / 2^{h}$ converges to 2. Most nodes sit near the bottom and
have almost nowhere to sift, which is where the saving comes from. Building
bottom-up is therefore strictly better than inserting $n$ elements one at a
time.""",

    "recursion-backtracking": """Recursion cost comes from the recurrence, and backtracking cost
from the size of the tree it searches.

**Cost of a linear recursion.** For factorial,

$$T(n) = T(n-1) + O(1), \\qquad T(1) = O(1)$$

Unrolling gives $T(n) = O(n)$, and the peak stack depth is also $n$, since every
frame is live until the base case returns. Depth, not just time, is the
constraint.

**Divide-and-conquer via the master theorem.** For a recurrence
$T(n) = aT(n/b) + O(n^d)$:

$$T(n) = \\begin{cases} O(n^d) & d > \\log_b a \\\\ O(n^d \\log n) & d = \\log_b a \\\\ O(n^{\\log_b a}) & d < \\log_b a \\end{cases}$$

Merge sort has $a = 2$, $b = 2$, $d = 1$, so $\\log_2 2 = 1 = d$ and the middle
case applies: $O(n \\log n)$.

**Backtracking.** The search tree has branching factor $b$ and depth $d$, so up
to $b^d$ nodes. Pruning is the only thing that makes this tractable: a bound
that rules out a partial solution removes its whole subtree, which is why the
quality of the bound decides whether the search finishes.""",

    "dynamic-programming": """DP cost is the size of the table times the work per cell, and the
method only pays off when subproblems overlap.

**Tabulation.** If the state has $k$ dimensions of sizes $n_1, \\dots, n_k$ and
each cell costs $O(1)$ to compute from already-filled cells:

$$T = O\\!\\left(\\prod_{i=1}^{k} n_i\\right)$$

For the 0/1 knapsack with $n$ items and capacity $W$ the table is $n \\times W$
and each cell is a max of two values, giving $O(nW)$.

**Why memoised recursion matches it.** Without caching, the same subproblem is
recomputed once per path that reaches it. The number of *distinct* subproblems
is the table size, so caching reduces the work to one computation per distinct
subproblem plus one lookup per call:

$$T_{\\text{memo}} = O(\\text{distinct subproblems}) = O(nW)$$

**The condition that makes it worth using.** If subproblems do not overlap, the
distinct count equals the total count and caching saves nothing while costing a
hash lookup per call. Testing for overlap before reaching for DP is the first
step, not an afterthought.""",

    "sorting-complexity": """The $n \\log n$ barrier for comparison sorts is provable, not
empirical.

**Decision-tree argument.** Any comparison sort decides its output by comparing
pairs of elements, so its behaviour is a binary tree whose leaves are the
possible output permutations. There are $n!$ permutations, so at least $n!$
leaves are needed. A binary tree of height $h$ has at most $2^h$ leaves:

$$2^h \\ge n! \\;\\Rightarrow\\; h \\ge \\log_2 (n!)$$

By Stirling's approximation $\\log_2 (n!) = \\Theta(n \\log n)$, so

$$h = \\Omega(n \\log n)$$

Since the worst-case number of comparisons equals the tree height, no
comparison sort can beat $O(n \\log n)$ in the worst case. Merge sort, heap sort
and quicksort (on average) meet the bound, which is why they are the standard
choices.

**Escaping the bound.** Counting and radix sort do not compare elements; they
use the keys as indices. With keys bounded by $k$, counting sort runs in
$O(n + k)$, which is linear when $k = O(n)$. The bound only applies to
comparison-based methods.""",

    "control-flow-conditionals-loops": """Branching has a measurable complexity, and it is worth deriving
because it is what linters and test-coverage tools report.

**Cyclomatic complexity.** For a control-flow graph with $E$ edges, $N$ nodes
and $P$ connected components:

$$M = E - N + 2P$$

For a single routine $P = 1$, so $M = E - N + 2$. Equivalently, $M$ equals one
plus the number of binary decisions, because each decision adds one edge and one
node:

$$M = 1 + \\text{decision points}$$

**Why this predicts test effort.** $M$ is the number of linearly independent
paths through the routine, so it is a lower bound on the test cases needed for
path coverage. A routine with ten nested conditions has $M = 11$ but
$2^{10} = 1024$ total paths — which is why path coverage is usually replaced by
branch coverage in practice.

**Loop termination.** A `while` loop terminates only if its condition eventually
becomes false. If no statement inside the body changes anything the condition
depends on, the condition's truth value is invariant and the loop never exits.
That is the whole of the infinite-loop argument, and it is checkable by
inspection.""",

    "variables-data-types-operators": """The range of an integer type falls straight out of its width.

**Signed range.** A $b$-bit two's-complement integer uses one bit for the sign,
so the remaining $b-1$ bits give

$$-2^{b-1} \\le x \\le 2^{b-1} - 1$$

For $b = 32$: $-2{,}147{,}483{,}648$ to $2{,}147{,}483{,}647$. The negative side
extends one further because two's complement has a single representation of zero.

**Unsigned range.** All $b$ bits carry magnitude:

$$0 \\le x \\le 2^{b} - 1$$

**Why 0.1 cannot be stored exactly in binary.** A binary fraction represents
sums of negative powers of two. $0.1 = 1/10$, and 10 has a factor of 5, so no
finite sum of powers of two equals it:

$$0.1_{10} = 0.0\\overline{0011}_2$$

The bar means it repeats forever, so it must be rounded. Accumulating rounded
values accumulates error, which is why monetary amounts are stored as integer
counts of the smallest unit rather than as floats.

**Operator precedence** is not arbitrary: it mirrors mathematics, with
multiplicative operators binding tighter than additive ones, so `a + b * c`
parses as `a + (b * c)` without parentheses.""",
})

INDUSTRY.update({
    "arrays": """Arrays are the default for a reason that has nothing to do with
asymptotics: they are contiguous, and contiguous memory is cache-friendly. A
linear scan over an array pulls in a whole cache line at a time, so a loop over
a million integers runs close to memory bandwidth, while the same loop over a
linked list of nodes scattered across the heap is often an order of magnitude
slower despite identical big-O.

In practice this shows up as NumPy arrays and Arrow columnar buffers rather than
lists of objects. Column stores keep one field of every record adjacent, so a
query touching two columns of ten million rows reads two contiguous ranges
instead of ten million scattered objects. The asymptotic complexity is the
same; the wall-clock difference is not.

The resize cost is handled by growth factors. Most implementations double, but
Go's slices and Java's ArrayList grow by smaller factors under some conditions
because doubling wastes up to half the allocated memory, and in a
long-running service that waste is real.""",

    "linked-lists": """Linked lists survive in production mainly where insertion and
deletion dominate and lookup is rare. The classic case is the operating system
kernel: free lists of available memory blocks, run queues of runnable threads,
and inode caches are all linked structures, because blocks are constantly being
allocated and released and are never searched by index.

The most common application-level use is the LRU cache, where a doubly linked
list holds entries in access order and a hash table maps key to node. Removal
from the middle is O(1) given the node pointer, which an array cannot offer.
Redis, the Linux page cache and most database buffer pools use some form of this.

Outside those cases a linked list is usually the wrong choice on modern
hardware. The pointer chasing defeats the prefetcher, and each node carries an
extra word of pointer plus allocator overhead — for 8-byte payloads that is a
100% tax. Benchmarks that show arrays beating linked lists by 10x on traversal
are measuring cache behaviour, not algorithmic efficiency.""",

    "stacks-queues": """Both are everywhere, and in production the queue matters far more
than the stack, because a queue is how one component hands work to another
without blocking on it.

Message brokers — RabbitMQ, Kafka, SQS — are queues at system scale. They exist
because the producer and consumer run at different speeds and must not be
coupled. The hard part in practice is not the data structure but the guarantees
around it: at-least-once versus exactly-once delivery, dead-letter queues for
messages that repeatedly fail, and back-pressure so a slow consumer does not
cause unbounded memory growth.

The stack is mostly implicit. Every function call uses the hardware stack, and
the two failure modes engineers actually meet are stack overflow from unbounded
recursion on user-supplied input, and stack exhaustion in threaded servers where
each thread reserves a megabyte or more. That is a large part of why async and
coroutine-based servers replaced one-thread-per-connection designs.

Priority queues backed by heaps run task schedulers, event-driven simulations,
and Dijkstra's shortest path in routing engines.""",

    "binary-trees-traversals": """Trees are how hierarchical data is stored, and the traversal order
usually encodes meaning rather than being an implementation detail.

A compiler walks its abstract syntax tree in post-order to evaluate: children
first, then the operator. The same order is used by expression evaluators and by
build systems resolving dependencies. Pre-order is the natural choice for
serialising a tree, because the root appears before its children, so a reader
can rebuild the structure in one pass. Level-order is what a DOM renderer uses
to paint parent containers before children.

File systems are trees with hard links making them general graphs, which is why
`du` and `rm -r` need cycle detection. The DOM, JSON documents and XML are all
trees, which is why XPath and CSS selectors are tree queries.

The traversal choice is also a performance decision: a recursive traversal needs
stack depth proportional to tree height, so on a degenerate tree of a million
nodes it will overflow. Production parsers iterate with an explicit stack for
exactly that reason.""",

    "binary-search-trees": """The textbook BST is rarely used directly, because unbalanced input
is common. What ships is a self-balancing variant.

Databases use B-trees and B+ trees rather than binary ones. A B+ tree node holds
hundreds of keys, so the tree is three or four levels deep for a billion rows —
and since each level is typically one disk page, that is three or four I/O
operations. A binary tree of the same size would be about thirty levels deep,
which is thirty page reads. Node fan-out, not comparison count, is what matters
when storage is involved.

In memory, C++ `std::map` uses a red-black tree and Java `TreeMap` does too.
They are chosen over hash maps when ordered iteration or range queries are
needed, which a hash map cannot provide.

Skewed input is a real failure mode. Loading sorted data into an unbalanced BST
turns it into a list, and the resulting latency cliff is a classic production
incident. Skipping the balancing because "the data is random" is a bet that the
data stays random.""",

    "graphs-traversals": """Graph algorithms are load-bearing infrastructure, and the
representation choice usually matters more than the algorithm.

Routing protocols are the canonical use. OSPF runs Dijkstra over a graph of
routers, and BGP reasons about paths across autonomous systems. Build systems
resolve dependency graphs and detect cycles with DFS — a circular import is
literally a cycle in that graph. Package managers, task schedulers and
spreadsheet recalculation all do topological sort.

Social and recommendation systems run BFS-like traversals for friend
suggestions and reachability, usually bounded to two or three hops because the
graph is enormous.

Sparse graphs dominate in practice, so adjacency lists win over matrices. A
matrix for a million-node graph needs a terabyte; a list needs memory
proportional to the edge count. The exception is dense graphs and GPU work,
where the regular memory layout of a matrix allows parallelism that a list
cannot.""",

    "hash-tables": """Hash tables are the most-used data structure in production
software, and most of the engineering effort goes into the hash function and
the collision policy rather than the table.

Hash joins are how databases join two large tables: hash the smaller side into
memory, then stream the larger side through it. This turns an $O(nm)$ nested
loop into roughly $O(n + m)$ and is one of the single biggest query-performance
levers.

Cryptographic hashing for integrity and deduplication uses the same structure
with a very different hash function. Content-addressable storage — Git objects,
Docker layers, backup deduplication — names each blob by its hash, so identical
content is stored once. That is a hash table used as a filesystem index.

The adversarial case matters for anything exposed to the network. If an
attacker can choose keys that all collide, they can force $O(n)$ lookups and
turn a fast service into a denial of service. This has been exploited against
web frameworks through crafted form parameters, which is why production hash
functions are randomised per process.""",

    "heaps-priority-queues": """Priority queues are how schedulers decide what runs next, and the
heap is usually the right implementation.

Operating system schedulers use multi-level feedback queues rather than a single
heap, because they need several priority classes with different time quanta, but
within each level the selection is a priority queue. Event-driven simulators —
network simulators, discrete-event models of a factory — keep scheduled events
in a heap and pop the earliest, which is the whole of the simulation loop.

Dijkstra's algorithm and A* both depend on a priority queue, so their
performance is the priority queue's performance. Using a binary heap gives
$O((V + E) \\log V)$; a Fibonacci heap improves the asymptotics but the constant
factors mean the binary heap usually wins in practice.

Top-k queries are the most common application-level use: keep a min-heap of size
$k$ and stream the data, giving $O(n \\log k)$ with $O(k)$ memory. That is how
"trending" and "most frequent" features are computed over data that does not fit
in memory.""",

    "recursion-backtracking": """Recursion is the natural way to write tree and grammar algorithms,
and backtracking is how constraint problems get solved when no better method is
known.

Compilers and interpreters are recursive-descent parsers: one function per
grammar rule, each calling the others. That is readable and fast enough, but it
is vulnerable to stack exhaustion on deeply nested input, so production parsers
bound nesting depth explicitly — a real CVE class.

Backtracking powers regex engines, SAT solvers, configuration finders and route
planners. The engineering work is almost entirely in the pruning. A naive
backtracking search over a schedule is intractable; the same search with a good
bound and variable-ordering heuristic finishes in seconds. Constraint solvers
are essentially backtracking with sophisticated propagation.

The practical warning is stack depth. A recursion whose depth is proportional to
input size will overflow on input an attacker controls. Converting to an
explicit stack is the standard fix, and it also removes the per-call frame
overhead.""",

    "dynamic-programming": """DP appears in production wherever an optimal sequence of decisions
must be found and the subproblems repeat.

Sequence alignment is the clearest example: the diff algorithm in Git and in
every code review tool is a variant of longest common subsequence. Genomic
alignment tools use the same recurrence over sequences millions of bases long,
which is why they need banded and parallel variants of the basic table fill.

Resource allocation is the knapsack: cutting stock in manufacturing, bin packing
in logistics, and memory allocation all use it or a relaxation of it. Route
planning uses shortest-path DP, and Viterbi decoding — used in speech
recognition, error-correcting codes and part-of-speech tagging — is DP over a
trellis.

The practical limit is table size. A two-dimensional table over $n$ items and
capacity $W$ needs $O(nW)$ memory, which is fine for $W = 10^4$ and impossible
for $W = 10^{12}$. The standard responses are rolling arrays when only the
previous row is needed, and reformulating the state to reduce a dimension.""",

    "sorting-complexity": """Real systems sort data too large to fit in memory, which changes
everything about the choice of algorithm.

Databases use external merge sort: read a chunk that fits in memory, sort it,
write it out, and merge the sorted runs. Merging is sequential I/O, which is
what disks and object storage are good at, and the merge can be parallelised
across runs. The comparison count is still $O(n \\log n)$ but the I/O pattern
matters more than the comparisons.

Quicksort is the usual in-memory default, but production implementations are
introsort: quicksort that switches to heapsort when the recursion gets too deep,
guaranteeing $O(n \\log n)$ worst case and removing the quadratic blowup on
adversarial input. Choosing the pivot well — median-of-three, or a random pivot
— is what keeps the average case real.

For small arrays, insertion sort beats everything because of low constant
factors and cache behaviour, which is why most library sorts switch to it below
about sixteen elements. That hybrid is a reminder that asymptotics describe
large inputs and say nothing about the ones you actually have.""",

    "control-flow-conditionals-loops": """Control flow is where correctness and testability are decided, and
the tooling around it is mature.

Cyclomatic complexity is not academic: it is a standard gate in static analysis.
Teams commonly fail a build above ten or fifteen per function, because past that
the number of paths makes review and testing ineffective. It is also used to
prioritise refactoring — the highest-complexity functions in a codebase are
reliably the ones with the most defects.

Branch coverage is the practical target rather than path coverage, since path
coverage is exponential. A suite with 100% branch coverage can still miss
bugs in how branches interact, which is why mutation testing exists: it injects
faults and checks whether the suite catches them, giving a much more honest
measure of test quality than coverage percentage.

The most common real defect here is an off-by-one in a loop bound or a condition
that can never change. Compilers warn about the obvious ones; fuzzing finds the
rest, which is why it is standard practice on parsers and protocol handlers.""",

    "variables-data-types-operators": """Type choice is a correctness decision more often than a performance
one, and the mistakes are well documented.

Money is the canonical case. Floating-point cannot represent decimal fractions
exactly, so accumulating prices or interest in a `float` or `double` produces
rounding errors that show up as a balance off by a cent. Every serious system
stores money as an integer count of the smallest unit, or uses a decimal type.
This is a recurring source of real financial bugs.

Integer overflow is the other. A 32-bit signed counter overflows at about 2.1
billion, and history includes routers failing after 2^32 seconds of uptime and
timestamps breaking in 2038. Languages differ: C and C++ wrap silently on
unsigned overflow and invoke undefined behaviour on signed, while Rust panics in
debug builds. Knowing what your language does is not optional.

Serialisation and endianness matter at system boundaries. A struct written on a
little-endian machine and read on a big-endian one has its bytes reversed, which
is why network protocols define byte order explicitly and why formats like
Protocol Buffers encode fields with explicit tags rather than relying on memory
layout.""",
})

FORMULAS.update({
    "binary-trees-traversals": {
        "name": "Nodes and height of a binary tree",
        "latex": "N(h) = 2^{h+1} - 1 \\qquad h_{\\min} = \\lceil \\log_2 (n+1) \\rceil - 1",
        "variables": [
            {"s": "N(h)", "n": "maximum nodes in a tree of height h", "u": "count"},
            {"s": "h", "n": "height, counting the root as level 0", "u": "levels"},
            {"s": "n", "n": "number of nodes present", "u": "count"},
            {"s": "h_{\\min}", "n": "minimum height needed for n nodes", "u": "levels"},
        ],
        "conditions": "Maximum node count holds only for a perfect tree, where every "
                      "level is completely filled. Real trees are sparser, so their "
                      "height is larger for the same n.",
    },
    "linked-lists": {
        "name": "Expected cost of an unordered search",
        "latex": "E[\\text{search}] = \\frac{1}{n}\\sum_{k=1}^{n} k = \\frac{n+1}{2} = O(n)",
        "variables": [
            {"s": "n", "n": "number of nodes in the list", "u": "count"},
            {"s": "k", "n": "position of the target, counting from the head", "u": "count"},
        ],
        "conditions": "Assumes the target is present and equally likely to be at any "
                      "position. A miss costs n comparisons, since the whole list must "
                      "be walked to reach NULL.",
    },
    "hash-tables": {
        "name": "Load factor and expected lookup cost",
        "latex": "\\alpha = \\frac{n}{m} \\qquad T_{\\text{lookup}} = O(1 + \\alpha)",
        "variables": [
            {"s": "\\alpha", "n": "load factor", "u": "dimensionless"},
            {"s": "n", "n": "number of stored keys", "u": "count"},
            {"s": "m", "n": "number of buckets", "u": "count"},
        ],
        "conditions": "Assumes the hash function distributes keys uniformly. Lookup is "
                      "O(1) only while resizing keeps alpha bounded by a constant; "
                      "without resizing alpha grows without limit.",
    },
    "heaps-priority-queues": {
        "name": "Heap height and the build-heap bound",
        "latex": "h = \\lfloor \\log_2 n \\rfloor \\qquad T_{\\text{build}} = O(n) \\qquad T_{\\text{sort}} = O(n \\log n)",
        "variables": [
            {"s": "h", "n": "height of the heap", "u": "levels"},
            {"s": "n", "n": "number of elements", "u": "count"},
            {"s": "T_{\\text{build}}", "n": "cost of building from an unordered array", "u": "operations"},
            {"s": "T_{\\text{sort}}", "n": "cost of repeatedly extracting the extreme", "u": "operations"},
        ],
        "conditions": "Building bottom-up is O(n); inserting elements one at a time is "
                      "O(n log n). The difference matters for large inputs.",
    },
    "stacks-queues": {
        "name": "Amortised cost of a push on a doubling array",
        "latex": "\\frac{1}{n}\\sum_{k=0}^{\\log_2 n} 2^{k} = \\frac{2n - 1}{n} < 2 = O(1)",
        "variables": [
            {"s": "n", "n": "number of push operations", "u": "count"},
            {"s": "2^{k}", "n": "size of the k-th copy when the array doubles", "u": "elements"},
        ],
        "conditions": "Amortised, not worst case. An individual push that triggers a "
                      "resize costs O(n). Real-time systems that cannot tolerate that "
                      "spike preallocate instead.",
    },
    "recursion-backtracking": {
        "name": "Master theorem for divide-and-conquer recurrences",
        "latex": "T(n) = aT(n/b) + O(n^d) \\;\\Rightarrow\\; "
                 "\\begin{cases} O(n^d) & d > \\log_b a \\\\ O(n^d \\log n) & d = \\log_b a \\\\ "
                 "O(n^{\\log_b a}) & d < \\log_b a \\end{cases}",
        "variables": [
            {"s": "a", "n": "number of subproblems created", "u": "count"},
            {"s": "b", "n": "factor by which the input shrinks", "u": "ratio"},
            {"s": "d", "n": "exponent of the work done outside the recursion", "u": "dimensionless"},
        ],
        "conditions": "Applies to recurrences of exactly this form. Merge sort has "
                      "a = 2, b = 2, d = 1, which lands in the middle case and gives "
                      "O(n log n).",
    },
    "dynamic-programming": {
        "name": "Cost of a tabulated DP",
        "latex": "T = O\\!\\left(\\prod_{i=1}^{k} n_i\\right) \\cdot c_{\\text{cell}}",
        "variables": [
            {"s": "k", "n": "number of state dimensions", "u": "count"},
            {"s": "n_i", "n": "size of the i-th state dimension", "u": "count"},
            {"s": "c_{\\text{cell}}", "n": "work to fill one cell from its dependencies", "u": "operations"},
        ],
        "conditions": "Correct only when every cell depends on cells already filled, so "
                      "the table can be traversed in one direction. Cyclic dependencies "
                      "need an iterative solver instead.",
    },
    "control-flow-conditionals-loops": {
        "name": "Cyclomatic complexity",
        "latex": "M = E - N + 2P = 1 + D",
        "variables": [
            {"s": "M", "n": "cyclomatic complexity", "u": "dimensionless"},
            {"s": "E", "n": "edges in the control-flow graph", "u": "count"},
            {"s": "N", "n": "nodes in the control-flow graph", "u": "count"},
            {"s": "P", "n": "connected components (1 for a single routine)", "u": "count"},
            {"s": "D", "n": "number of binary decision points", "u": "count"},
        ],
        "conditions": "A lower bound on the test cases needed for path coverage. Total "
                      "paths grow as 2^D, which is why branch coverage is used in "
                      "practice instead.",
    },
    "variables-data-types-operators": {
        "name": "Integer range and memory footprint",
        "latex": "-2^{b-1} \\le x \\le 2^{b-1} - 1 \\quad (\\text{signed}) \\qquad "
                 "0 \\le x \\le 2^{b} - 1 \\quad (\\text{unsigned})",
        "variables": [
            {"s": "b", "n": "width of the type", "u": "bits"},
            {"s": "x", "n": "representable value", "u": "count"},
        ],
        "conditions": "Assumes two's complement, which every mainstream architecture "
                      "uses. Signed overflow is undefined behaviour in C and C++, so "
                      "the bound describes what is representable rather than what the "
                      "language guarantees on wraparound.",
    },
    "ip-addressing-subnetting": {
        "name": "Usable hosts and subnet mask from the prefix length",
        "latex": "H = 2^{(32 - p)} - 2 \\qquad S = 2^{(p - p_{\\text{net}})}",
        "variables": [
            {"s": "H", "n": "usable host addresses per subnet", "u": "count"},
            {"s": "p", "n": "prefix length (the number after the slash)", "u": "bits"},
            {"s": "S", "n": "number of subnets created by borrowing bits", "u": "count"},
            {"s": "p_{\\text{net}}", "n": "original network prefix length", "u": "bits"},
        ],
        "conditions": "IPv4. The minus two removes the network address and the broadcast "
                      "address. For IPv6 the host space is 128 - p, and the two "
                      "reserved addresses are not subtracted the same way.",
    },
    "indexes-query-performance": {
        "name": "B-tree depth and index versus scan cost",
        "latex": "d = \\lceil \\log_{f} n \\rceil \\qquad "
                 "T_{\\text{index}} = O(\\log_f n) \\;\\;\\text{vs}\\;\\; T_{\\text{scan}} = O(n)",
        "variables": [
            {"s": "d", "n": "tree depth, in levels", "u": "levels"},
            {"s": "f", "n": "fan-out, keys per node", "u": "count"},
            {"s": "n", "n": "number of indexed rows", "u": "count"},
        ],
        "conditions": "Depth equals the number of page reads, so it is the real cost. A "
                      "fan-out of 100 reaches a billion rows in about five levels. The "
                      "index is only worth using if it selects a small fraction of the "
                      "table.",
    },
    "normalization": {
        "name": "Functional dependency and the normal-form tests",
        "latex": "X \\rightarrow Y \\qquad "
                 "\\text{1NF: atomic} \\;\\; \\text{2NF: no partial} \\;\\; \\text{3NF: no transitive}",
        "variables": [
            {"s": "X \\rightarrow Y", "n": "Y is functionally determined by X", "u": "relation"},
            {"s": "X", "n": "determinant, usually a key or part of one", "u": "attribute set"},
            {"s": "Y", "n": "dependent attribute", "u": "attribute"},
        ],
        "conditions": "A partial dependency needs a composite primary key to exist. A "
                      "transitive dependency is X to B to C, meaning C is really a fact "
                      "about B and should live in B's table.",
    },
    "osi-tcp-ip-models": {
        "name": "Header overhead as a fraction of the frame",
        "latex": "\\eta = \\frac{P}{P + H_{\\text{tcp}} + H_{\\text{ip}} + H_{\\text{link}}}",
        "variables": [
            {"s": "\\eta", "n": "goodput efficiency", "u": "fraction"},
            {"s": "P", "n": "payload bytes", "u": "bytes"},
            {"s": "H_{\\text{tcp}}", "n": "TCP header, typically 20", "u": "bytes"},
            {"s": "H_{\\text{ip}}", "n": "IP header, typically 20", "u": "bytes"},
            {"s": "H_{\\text{link}}", "n": "Ethernet header and trailer, 18", "u": "bytes"},
        ],
        "conditions": "With a 1500-byte MTU the overhead is about 58 bytes, giving "
                      "roughly 96% efficiency. Small payloads are much worse, which is "
                      "why Nagle's algorithm and TCP segmentation offload exist.",
    },
    "synchronisation-semaphores": {
        "name": "Semaphore operations and the bounded-buffer invariant",
        "latex": "\\text{wait}(S):\\; S \\leftarrow S - 1,\\; \\text{block if } S < 0 \\qquad "
                 "\\text{signal}(S):\\; S \\leftarrow S + 1,\\; \\text{wake a waiter}",
        "variables": [
            {"s": "S", "n": "semaphore value; negative means waiters are blocked", "u": "count"},
        ],
        "conditions": "wait and signal must be atomic. A bounded buffer uses two "
                      "counting semaphores, empty and full, plus a mutex; taking them in "
                      "the wrong order deadlocks.",
    },
    "processes-threads": {
        "name": "Context-switch and throughput cost",
        "latex": "T_{\\text{total}} = n \\cdot (t_{\\text{work}} + t_{\\text{switch}}) \\qquad "
                 "\\text{efficiency} = \\frac{t_{\\text{work}}}{t_{\\text{work}} + t_{\\text{switch}}}",
        "variables": [
            {"s": "n", "n": "number of slices executed", "u": "count"},
            {"s": "t_{\\text{work}}", "n": "useful work per slice", "u": "s"},
            {"s": "t_{\\text{switch}}", "n": "cost of one context switch", "u": "s"},
        ],
        "conditions": "A process switch also flushes the address-space state and usually "
                      "the TLB, so it costs more than a thread switch. Shrinking the "
                      "time quantum raises throughput only until switch overhead "
                      "dominates.",
    },
    "file-systems": {
        "name": "Internal fragmentation and inode capacity",
        "latex": "E[\\text{waste}] = \\frac{B}{2} \\quad \\text{per file} \\qquad "
                 "\\text{blocks} = \\lceil \\text{size} / B \\rceil",
        "variables": [
            {"s": "B", "n": "block size, commonly 4096", "u": "bytes"},
            {"s": "E[\\text{waste}]", "n": "expected unused bytes in the last block", "u": "bytes"},
        ],
        "conditions": "Assumes file sizes are uniformly distributed within a block. A "
                      "filesystem holding a million 100-byte files wastes about half its "
                      "space; smaller blocks reduce waste but enlarge the block map and "
                      "increase metadata I/O.",
    },
    "transactions-acid": {
        "name": "Throughput cost of serialisable isolation",
        "latex": "T_{\\text{serial}} \\le T_{\\text{committed}} \\qquad "
                 "\\text{conflict rate} \\propto \\frac{\\text{rows touched}}{\\text{rows in table}}",
        "variables": [
            {"s": "T", "n": "transactions per second", "u": "1/s"},
        ],
        "conditions": "The inequality holds because SERIALIZABLE forbids interleavings "
                      "that weaker levels allow. Hot rows are the usual bottleneck: a "
                      "single counter row serialises every transaction that touches it, "
                      "which is why sharded counters exist.",
    },
    "sql-joins-aggregation": {
        "name": "Cost of the three join strategies",
        "latex": "T_{\\text{nested}} = O(nm) \\qquad "
                 "T_{\\text{hash}} = O(n + m) \\qquad "
                 "T_{\\text{merge}} = O(n \\log n + m \\log m)",
        "variables": [
            {"s": "n, m", "n": "row counts of the two inputs", "u": "count"},
        ],
        "conditions": "Hash join needs the smaller side to fit in memory, otherwise it "
                      "spills to disk in partitions. Merge join needs both inputs sorted "
                      "on the join key, which is often already true if an index supplies "
                      "the order.",
    },
    "deadlocks": {
        "name": "The four necessary conditions and Banker's safety test",
        "latex": "\\text{deadlock} \\iff \\text{ME} \\wedge \\text{HW} \\wedge \\text{NP} \\wedge \\text{CW}",
        "variables": [
            {"s": "\\text{ME}", "n": "mutual exclusion - a resource is held by one thread", "u": "condition"},
            {"s": "\\text{HW}", "n": "hold and wait - a thread holds one and waits for another", "u": "condition"},
            {"s": "\\text{NP}", "n": "no preemption - a resource cannot be taken away", "u": "condition"},
            {"s": "\\text{CW}", "n": "circular wait - a cycle in the wait-for graph", "u": "condition"},
        ],
        "conditions": "All four must hold simultaneously, so breaking any one prevents "
                      "deadlock entirely. Banker's algorithm grants a request only if the "
                      "resulting state is safe, meaning some order exists in which every "
                      "thread can finish.",
    },
    "design-patterns": {
        "name": "Coupling as a cost model",
        "latex": "C_{\\text{change}} \\propto \\text{fan-in}(m) \\times \\text{depth of dependency}",
        "variables": [
            {"s": "C_{\\text{change}}", "n": "effort to change a module", "u": "relative"},
            {"s": "\\text{fan-in}(m)", "n": "number of modules that depend on m", "u": "count"},
        ],
        "conditions": "The reason patterns exist: they reduce fan-in on the parts most "
                      "likely to change. Observer removes the need for a subject to know "
                      "its listeners; Strategy removes a chain of conditionals from the "
                      "call site.",
    },
    "encapsulation-inheritance-polymorphism": {
        "name": "Method dispatch cost",
        "latex": "t_{\\text{virtual}} = t_{\\text{direct}} + t_{\\text{vtable}} \\qquad "
                 "t_{\\text{vtable}} \\approx 1\\text{ indirect load}",
        "variables": [
            {"s": "t_{\\text{vtable}}", "n": "cost of resolving through the vtable", "u": "ns"},
        ],
        "conditions": "Virtual dispatch is usually negligible, but it also blocks "
                      "inlining, and inlining is worth far more than the lookup. Hot "
                      "loops over millions of small calls are where the difference shows, "
                      "which is why some languages devirtualise when the concrete type is "
                      "known.",
    },
    "software-process-models-testing": {
        "name": "Defect escape and the cost-of-fix curve",
        "latex": "C_{\\text{fix}}(\\text{phase}) \\approx C_0 \\cdot k^{\\,\\Delta\\text{phase}} \\qquad "
                 "\\text{DRE} = \\frac{D_{\\text{found}}}{D_{\\text{found}} + D_{\\text{escaped}}}",
        "variables": [
            {"s": "C_{\\text{fix}}", "n": "cost to fix a defect", "u": "relative"},
            {"s": "k", "n": "escalation factor per phase, commonly 3 to 10", "u": "ratio"},
            {"s": "\\text{DRE}", "n": "defect removal effectiveness", "u": "fraction"},
        ],
        "conditions": "The curve is empirical but consistent across studies. DRE above "
                      "about 0.85 is generally considered good; below 0.7 the process is "
                      "leaking most defects to users.",
    },
    "tcp-flow-control": {
        "name": "Congestion window growth and the bandwidth-delay product",
        "latex": "W \\leftarrow 2W \\; (\\text{slow start}) \\qquad W \\leftarrow W + 1 \\; (\\text{avoidance}) "
                 "\\qquad W \\leftarrow W/2 \\; (\\text{loss})",
        "variables": [
            {"s": "W", "n": "congestion window", "u": "segments"},
            {"s": "BDP", "n": "bytes in flight needed to fill the link, B x RTT", "u": "bytes"},
            {"s": "MSS", "n": "maximum segment size, typically 1460", "u": "bytes"},
        ],
        "conditions": "Additive increase with multiplicative decrease, which is what lets "
                      "independent flows converge on a fair share of a link without "
                      "coordinating. If W times MSS is smaller than the bandwidth-delay "
                      "product the link cannot be filled no matter how fast it is - the "
                      "reason a small default window caps throughput on long-fat links.",
    },
    "cache-memory-locality": {
        "name": "Average memory access time",
        "latex": "T_{\\text{avg}} = h \\cdot t_{\\text{cache}} + (1 - h) \\cdot t_{\\text{miss}}",
        "variables": [
            {"s": "T_{\\text{avg}}", "n": "average access time", "u": "ns"},
            {"s": "h", "n": "hit rate", "u": "fraction"},
            {"s": "t_{\\text{cache}}", "n": "cache access time, about 1", "u": "ns"},
            {"s": "t_{\\text{miss}}", "n": "cost of a miss, about 80 to main memory", "u": "ns"},
        ],
        "conditions": "At a 99% hit rate the average is about 1.8 ns; at 90% it is about "
                      "8.9 ns. That fivefold swing is why locality, not raw clock speed, "
                      "usually decides performance.",
    },
    "concrete-mix-design-workability": {
        "name": "Water-cement ratio and Abrams' law",
        "latex": "f_c = \\frac{A}{B^{\\,w/c}} \\qquad "
                 "w/c = \\frac{m_w}{m_c} \\qquad V_{\\text{voids}} \\propto (w/c - 0.25)",
        "variables": [
            {"s": "f_c", "n": "compressive strength", "u": "MPa"},
            {"s": "w/c", "n": "water to cement ratio by mass", "u": "dimensionless"},
            {"s": "m_w, m_c", "n": "mass of water and cement", "u": "kg"},
            {"s": "A, B", "n": "constants for the aggregate and curing conditions", "u": "-"},
        ],
        "conditions": "Abrams' law holds for a given set of materials, workmanship and "
                      "curing. Only about 0.25 of water is needed for hydration; the "
                      "excess leaves pores behind, and porosity is what reduces strength.",
    },
    "equilibrium-of-forces-free-body-diagrams": {
        "name": "Static equilibrium conditions",
        "latex": "\\sum \\vec{F} = 0 \\qquad \\sum \\vec{M} = 0 \\qquad "
                 "\\sum F_x = 0, \\; \\sum F_y = 0, \\; \\sum M_z = 0",
        "variables": [
            {"s": "\\vec{F}", "n": "force", "u": "N"},
            {"s": "\\vec{M}", "n": "moment about a point", "u": "N m"},
        ],
        "conditions": "Planar problems give three independent equations, which solves up "
                      "to three unknowns. More unknowns than equations means the structure "
                      "is statically indeterminate and needs deformation compatibility to "
                      "solve.",
    },
    "kirchhoffs-laws": {
        "name": "Kirchhoff's current and voltage laws",
        "latex": "\\sum_{k} I_k = 0 \\quad (\\text{node}) \\qquad "
                 "\\sum_{k} V_k = 0 \\quad (\\text{loop})",
        "variables": [
            {"s": "I_k", "n": "current in branch k, signed by direction", "u": "A"},
            {"s": "V_k", "n": "voltage across element k, signed by traversal", "u": "V"},
        ],
        "conditions": "KCL is conservation of charge and holds at every node. KVL is "
                      "conservation of energy and holds around every closed loop, "
                      "provided the changing magnetic flux through the loop is negligible "
                      "- otherwise Faraday's law adds an EMF term.",
    },
    "boolean-algebra-karnaugh-maps": {
        "name": "Boolean identities and grouping rules",
        "latex": "A + \\bar{A} = 1 \\qquad A \\cdot \\bar{A} = 0 \\qquad "
                 "\\overline{A + B} = \\bar{A} \\cdot \\bar{B} \\qquad \\text{group size} = 2^k",
        "variables": [
            {"s": "A, B", "n": "Boolean variables", "u": "0 or 1"},
            {"s": "k", "n": "group size exponent", "u": "dimensionless"},
        ],
        "conditions": "De Morgan's laws convert between sum-of-products and "
                      "product-of-sums. Karnaugh groups must be powers of two and may wrap "
                      "around the edges, because rows and columns use Gray code so "
                      "neighbours differ in exactly one variable.",
    },
    "material-energy-balances": {
        "name": "General balance equation",
        "latex": "\\text{IN} - \\text{OUT} + \\text{GEN} - \\text{CONS} = \\text{ACC}",
        "variables": [
            {"s": "\\text{IN}, \\text{OUT}", "n": "mass or energy crossing the boundary", "u": "kg/s or W"},
            {"s": "\\text{GEN}, \\text{CONS}", "n": "generated or consumed by reaction", "u": "kg/s or W"},
            {"s": "\\text{ACC}", "n": "accumulation inside the boundary", "u": "kg/s or W"},
        ],
        "conditions": "At steady state accumulation is zero. Mass balances are written "
                      "per species because total mass is conserved but individual species "
                      "are not when reaction occurs. Energy balances must be consistent "
                      "about which reference state the enthalpies use.",
    },
})

EXAMPLES.update({
    "sorting-complexity": {
        "problem": "A service sorts 10,000 records in 40 ms using quicksort. "
                   "Estimate how long 1,000,000 records will take, and say what could "
                   "make the estimate wrong.",
        "approach": "Use the n log n growth rate to scale the measured time, then "
                    "consider what the asymptotic model ignores: memory hierarchy, "
                    "constant factors, and the worst-case pivot behaviour.",
        "solution": "**Step 1 - the ratio.**\n"
                    "$$\\frac{n_2 \\log n_2}{n_1 \\log n_1} = "
                    "\\frac{10^6 \\cdot \\log_2 10^6}{10^4 \\cdot \\log_2 10^4} "
                    "= \\frac{10^6 \\times 19.9}{10^4 \\times 13.3} \\approx 149$$\n\n"
                    "**Step 2 - the estimate.**\n"
                    "$$40\\ \\text{ms} \\times 149 \\approx 6.0\\ \\text{s}$$\n\n"
                    "**Step 3 - what breaks the estimate.** One million records no longer "
                    "fit in cache, so each comparison costs more than it did at ten "
                    "thousand. Real time will exceed 6 s, often noticeably.\n\n"
                    "**Step 4 - the worst case.** If the input is already sorted and the "
                    "pivot is the first element, quicksort degenerates to $O(n^2)$:\n"
                    "$$\\frac{(10^6)^2}{(10^4)^2} = 10^4 \\;\\Rightarrow\\; 40\\ \\text{ms} "
                    "\\times 10^4 = 400\\ \\text{s}$$",
        "answer": "About 6 seconds on the n log n model, but more in practice because of "
                  "cache misses. With a pathological pivot it becomes roughly 400 seconds "
                  "- which is why production sorts use introsort or a randomised pivot.",
    },
    "file-systems": {
        "problem": "A directory holds 10,000 files averaging 4,100 bytes each. The block "
                   "size is 4,096 bytes. How much space is actually used, and how much is "
                   "wasted?",
        "approach": "Each file is allocated whole blocks, so compute blocks per file, "
                    "multiply out, and compare with the real data size.",
        "solution": "**Step 1 - blocks per file.**\n"
                    "$$\\lceil 4100 / 4096 \\rceil = 2 \\text{ blocks}$$\n\n"
                    "**Step 2 - space allocated.**\n"
                    "$$10{,}000 \\times 2 \\times 4096 = 81.92\\ \\text{MB}$$\n\n"
                    "**Step 3 - space actually used.**\n"
                    "$$10{,}000 \\times 4100 = 41.0\\ \\text{MB}$$\n\n"
                    "**Step 4 - the waste.**\n"
                    "$$81.92 - 41.0 = 40.9\\ \\text{MB}, \\text{ about } 50\\%$$\n\n"
                    "Each file overshoots one block boundary by 4 bytes and so consumes a "
                    "second block almost entirely empty.",
        "answer": "81.9 MB allocated against 41 MB of data - roughly half wasted. "
                  "Shrinking the block size to 1,024 bytes would cut the waste to about "
                  "12%, at the cost of a larger block map and more metadata I/O.",
    },
    "effective-stress-bearing-capacity": {
        "problem": "A 6 m thick clay layer has a total unit weight of 18 kN/m3 above the "
                   "water table at 2 m depth, and a saturated unit weight of 20 kN/m3 below "
                   "it. Find the effective vertical stress at 6 m depth.",
        "approach": "Total stress is the weight of everything above. Below the water table "
                    "use the buoyant unit weight, or subtract pore pressure from the total. "
                    "Effective stress is the difference.",
        "solution": "**Step 1 - total stress.**\n"
                    "$$\\sigma_v = (18 \\times 2) + (20 \\times 4) = 36 + 80 = 116\\ \\text{kPa}$$\n\n"
                    "**Step 2 - pore water pressure at 6 m.** The water table is at 2 m, so "
                    "the depth of water is 4 m:\n"
                    "$$u = \\gamma_w \\times 4 = 9.81 \\times 4 = 39.2\\ \\text{kPa}$$\n\n"
                    "**Step 3 - effective stress.**\n"
                    "$$\\sigma'_v = 116 - 39.2 = 76.8\\ \\text{kPa}$$\n\n"
                    "**Cross-check with the buoyant weight.**\n"
                    "$$\\sigma'_v = (18 \\times 2) + (20 - 9.81) \\times 4 "
                    "= 36 + 40.8 = 76.8\\ \\text{kPa}$$",
        "answer": "76.8 kPa effective vertical stress, confirmed by both routes. Only this "
                  "value enters a bearing-capacity or settlement calculation - using the "
                  "total 116 kPa would overestimate the ground's capacity by about half.",
    },
    "maxwells-equations": {
        "problem": "A circular loop of radius 0.10 m sits in a uniform magnetic field "
                   "perpendicular to its plane. The field falls from 0.50 T to 0.10 T in "
                   "0.20 s. Find the induced EMF, and its direction.",
        "approach": "Apply Faraday's law: the EMF equals the negative rate of change of "
                   "flux. Use Lenz's law for the direction.",
        "solution": "**Step 1 - the area.**\n"
                    "$$A = \\pi r^2 = \\pi (0.10)^2 = 0.0314\\ \\text{m}^2$$\n\n"
                    "**Step 2 - the change in flux.** The field is perpendicular, so "
                    "$\\Phi = BA$:\n"
                    "$$\\Delta\\Phi = (0.10 - 0.50) \\times 0.0314 = -0.01257\\ \\text{Wb}$$\n\n"
                    "**Step 3 - Faraday's law.**\n"
                    "$$\\mathcal{E} = -\\frac{\\Delta\\Phi}{\\Delta t} "
                    "= -\\frac{-0.01257}{0.20} = +0.0628\\ \\text{V}$$\n\n"
                    "**Step 4 - direction.** The flux into the loop is decreasing, so the "
                    "induced current creates a field that opposes that decrease - into the "
                    "plane. By the right-hand rule the current is clockwise as seen from "
                    "the side the field enters.",
        "answer": "62.8 mV, driving a clockwise current that tries to maintain the falling "
                  "flux. This is the principle behind a generator: rotate the loop instead "
                  "of changing the field and the EMF becomes sinusoidal.",
    },
    "per-unit-system-fault-analysis": {
        "problem": "A 50 MVA, 132 kV system has a generator with subtransient reactance "
                   "0.20 pu on its own 50 MVA base. Find the three-phase fault current at "
                   "the generator terminals.",
        "approach": "On a common base the fault current in per unit is simply 1/Z. Convert "
                   "to amps using the base current at that voltage.",
        "solution": "**Step 1 - the bases match**, so no conversion is needed: "
                    "$Z = 0.20$ pu.\n\n"
                    "**Step 2 - fault current in per unit.**\n"
                    "$$I_{pu} = \\frac{1}{Z_{pu}} = \\frac{1}{0.20} = 5.0\\ \\text{pu}$$\n\n"
                    "**Step 3 - base current.**\n"
                    "$$I_{base} = \\frac{S_{base}}{\\sqrt{3} \\, V_{base}} "
                    "= \\frac{50 \\times 10^6}{\\sqrt{3} \\times 132 \\times 10^3} "
                    "= 218.7\\ \\text{A}$$\n\n"
                    "**Step 4 - the actual fault current.**\n"
                    "$$I_f = 5.0 \\times 218.7 = 1093\\ \\text{A}$$",
        "answer": "About 1.09 kA, five times the rated current. Note that the reactance was "
                  "already on the right base; if the generator had been rated at 20 MVA the "
                  "reactance would first need converting with "
                  "$Z_{new} = Z_{old} \\times (S_{new}/S_{old})$, which is the step most "
                  "often forgotten.",
    },
})


# ---------------------------------------------------------------------------
# Access
# ---------------------------------------------------------------------------

def derivation(slug: str) -> str:
    return DERIVATIONS.get(slug, "")


def industry(slug: str) -> str:
    return INDUSTRY.get(slug, "")


def formula(slug: str) -> dict | None:
    return FORMULAS.get(slug)


def example(slug: str) -> dict | None:
    return EXAMPLES.get(slug)


def unknown_keys(known_topics: set[str]) -> dict[str, list[str]]:
    """Content keyed to a topic that does not exist, by field.

    Called by the seeder so a renamed or removed topic shows up as an error
    naming the stale key rather than as content that silently stops rendering.
    """
    return {
        name: sorted(set(table) - known_topics)
        for name, table in (("derivation", DERIVATIONS), ("industry", INDUSTRY),
                            ("formula", FORMULAS), ("example", EXAMPLES))
        if set(table) - known_topics
    }


# ---------------------------------------------------------------------------
# Systems, networks and databases - derivations and industry practice
# ---------------------------------------------------------------------------

DERIVATIONS.update({
    "cpu-scheduling": """Average waiting time is what a scheduling policy is judged on, and
it can be computed exactly.

**Definition.** Waiting time is the time a process spends in the ready queue,
which is turnaround minus service:

$$W_i = T_i - B_i, \\qquad \\bar{W} = \\frac{1}{n}\\sum_{i=1}^{n} W_i$$

**First-come first-served.** With bursts $b_1, b_2, \\dots, b_n$ arriving in
that order, process $i$ waits for everything before it:

$$W_i = \\sum_{j<i} b_j \\;\\Rightarrow\\; \\bar{W} = \\frac{1}{n}\\sum_{i=1}^{n}\\sum_{j<i} b_j$$

**Why SJF is optimal.** Consider any schedule where a shorter job runs after a
longer one. Swapping them reduces the shorter job's wait by the longer burst and
increases the longer job's wait by the shorter burst. Since the shorter burst is
smaller, the net change is negative, so total wait falls. Repeating this until no
such pair remains yields shortest-job-first, which is therefore minimal.

**Why SJF is unusable as stated.** It requires knowing each burst in advance,
which is not available. Real schedulers predict it from history with an
exponential average:

$$\\tau_{n+1} = \\alpha t_n + (1 - \\alpha)\\tau_n$$

weighting recent behaviour by $\\alpha$, typically about 0.5.""",

    "deadlocks": """Deadlock is a graph property, and that is what makes it detectable.

**The wait-for graph.** Vertices are threads, and an edge $T_i \\to T_j$ means
$T_i$ waits for a resource $T_j$ holds. A thread blocked on a held resource
cannot proceed until the holder releases it, so a cycle means every thread in it
is waiting on another that is itself waiting:

$$T_1 \\to T_2 \\to \\dots \\to T_k \\to T_1 \\;\\Rightarrow\\; \\text{deadlock}$$

Conversely, if the graph is acyclic there is always a thread with no outgoing
edge; it can finish and release, so progress continues. Deadlock is therefore
*exactly* the presence of a cycle, which a DFS detects in $O(|V| + |E|)$.

**Banker's algorithm.** Rather than detecting, it avoids: a request is granted
only if the resulting state is *safe*, meaning some ordering of the remaining
threads lets each finish. Checking safety is the same as repeatedly finding a
thread whose needs are met by currently available resources:

$$T = O(n^2 m)$$

for $n$ threads and $m$ resource types, which is why it is applied at request
time rather than continuously.

**The cheap prevention.** Impose a total order on resources and require every
thread to acquire in that order. Then all edges point in one direction, so no
cycle can exist — the proof is one line, and the rule costs nothing at runtime.""",

    "memory-management-paging": """Address translation and the cost of the page table both follow from
the split.

**Translation.** A logical address is divided into a page number $p$ and an
offset $d$. With page size $2^s$, the offset is the low $s$ bits and the page
number the rest:

$$\\text{physical} = f \\times 2^{s} + d, \\qquad f = \\text{page\\_table}[p]$$

**Page table size.** With $n$-bit addresses and page size $2^s$ there are
$2^{n-s}$ pages, each needing an entry of $e$ bytes:

$$\\text{table size} = 2^{n-s} \\cdot e$$

For $n = 48$ and $s = 12$ that is $2^{36}$ entries — 512 GB at 8 bytes each. A
flat table is impossible, which is why real systems use a multi-level table that
allocates only the branches actually referenced.

**Why the TLB matters.** Every memory access needs a translation, so without a
cache the cost doubles. With a TLB of hit rate $h$, hit time $t_h$ and miss
penalty $t_m$:

$$t_{\\text{eff}} = h \\cdot t_h + (1-h)(t_h + t_m)$$

At $h = 0.99$ the overhead is about 1%; at $h = 0.90$ it exceeds 10%. The TLB
hit rate is why large pages exist — one entry covers more memory.""",

    "cache-memory-locality": """The speed of a memory hierarchy is a weighted average, and it is
extremely sensitive to the hit rate.

**Average access time.** With hit rate $h$, cache time $t_c$ and miss time
$t_m$ (which includes going to the lower level):

$$T = h\\,t_c + (1-h)(t_c + t_m) = t_c + (1-h)\\,t_m$$

The second form shows the cost directly: every miss adds the full miss penalty,
weighted by how often misses occur.

**Why the sensitivity is nonlinear.** Take $t_c = 1$ ns and $t_m = 80$ ns:

$$h = 0.99 \\Rightarrow T = 1 + 0.01 \\times 80 = 1.8\\ \\text{ns}$$
$$h = 0.90 \\Rightarrow T = 1 + 0.10 \\times 80 = 9.0\\ \\text{ns}$$

Losing nine percentage points of hit rate makes memory five times slower. No
algorithmic improvement at that scale is available, which is why locality is the
primary lever.

**Spatial locality pays because of the line.** A cache line of $L$ bytes brings
$L / w$ words for the price of one miss, where $w$ is the word size. Sequential
access therefore converts $n$ misses into $n w / L$, a reduction by the line
size — typically eightfold for 64-byte lines.""",

    "indexes-query-performance": """Index cost is the tree depth, and depth grows logarithmically in
fan-out rather than in two.

**B-tree depth.** A node holds $f$ keys and has $f+1$ children, so a tree of
depth $d$ indexes up to $f^d$ rows:

$$d = \\lceil \\log_f n \\rceil$$

With $f = 100$ and $n = 10^9$:

$$d = \\lceil \\log_{100} 10^9 \\rceil = \\lceil 4.5 \\rceil = 5$$

Five page reads. A binary tree over the same data would need
$\\log_2 10^9 \\approx 30$. Fan-out, not comparison count, is what makes B-trees
suitable for storage.

**When the index loses.** An index scan costs one random read per matching row,
plus the descent. A sequential scan costs one read per page. The index wins while

$$\\text{selectivity} \\times n < \\frac{n}{\\text{rows per page}}$$

which is why a query returning most of the table is faster without the index,
and why the planner estimates selectivity before choosing.""",

    "sql-joins-aggregation": """The three join strategies have different cost shapes, and the
planner picks between them on that basis.

**Nested loop.** For each of $n$ rows in the outer input, scan $m$ rows:

$$T = n \\cdot m$$

**Hash join.** Build a hash table on the smaller input in $O(m)$, then probe it
once per outer row at $O(1)$ expected:

$$T = O(n + m)$$

provided the build side fits in memory. If it does not, it is partitioned and
each partition joined separately, adding a pass over both inputs.

**Merge join.** Sort both inputs, then walk them together:

$$T = O(n \\log n + m \\log m)$$

but if either input is already sorted on the join key — an index can supply the
order — the sort disappears and the cost is $O(n + m)$ with no hash table to
build. That is why an index on a join column helps even when the index is not
used to filter.

**Aggregation.** `GROUP BY` needs one pass to group and one to aggregate, so
$O(n)$ after the grouping key is available, either by hashing or by reading a
sorted input. `WHERE` filters rows before this; `HAVING` filters groups after,
which is why `HAVING` cannot use an index on the filtered column.""",

    "normalization": """The anomaly argument is what justifies the normal forms, and it is
countable.

**Setup.** Suppose a relation stores student, course, lecturer and the
lecturer's office, with the dependencies

$$\\text{student}, \\text{course} \\rightarrow \\text{lecturer} \\qquad
  \\text{lecturer} \\rightarrow \\text{office}$$

**Update anomaly.** The office is a fact about the lecturer, but it is stored
once per student enrolled with that lecturer. If lecturer $L$ teaches $k$
students, changing the office requires $k$ updates:

$$\\text{writes} = \\sum_{L} k_L = |\\text{enrolments}|$$

Missing one leaves the relation internally inconsistent — two different offices
for the same lecturer — which no constraint will catch, because nothing says the
office depends on the lecturer.

**Insertion anomaly.** A newly hired lecturer with no students cannot be
recorded at all, because the primary key would be null.

**Deletion anomaly.** If the last student withdraws, the row goes and the
lecturer's office disappears with it.

**The fix.** Splitting into `lecturer(lecturer, office)` and
`enrolment(student, course, lecturer)` makes each fact appear once. That is the
definition of 3NF: every non-key attribute depends on the key, the whole key and
nothing but the key.""",

    "ip-addressing-subnetting": """Subnetting is arithmetic on the prefix length, and the two reserved
addresses are what make the usable count non-obvious.

**Host space.** With prefix length $p$ there are $32 - p$ host bits, giving

$$2^{32-p} \\text{ addresses per subnet}$$

The first is the network address (all host bits zero) and the last the broadcast
address (all host bits one). Neither can be assigned, so

$$H = 2^{32-p} - 2$$

For $p = 26$: $2^6 - 2 = 62$ usable hosts. For $p = 30$: $2^2 - 2 = 2$, which is
why point-to-point links use a /30. For $p = 31$ the formula gives zero, which
is why RFC 3021 defines a special case for point-to-point links.

**Number of subnets.** Borrowing $b$ bits from the host portion multiplies the
subnet count:

$$S = 2^{b}$$

and reduces the host count by the same factor, since $b$ bits move from one side
to the other. That trade-off is the whole design decision.

**Why a wrong mask breaks local traffic first.** Two hosts decide whether to
communicate directly by masking the destination with their own prefix. If the
masks disagree they can disagree about whether the destination is on-link, and
one will send to the gateway while the other expects a direct reply — which is
why a misconfigured mask produces one-way failures rather than an obvious
error.""",

    "osi-tcp-ip-models": """Encapsulation overhead is fixed per packet, so it hurts small
payloads disproportionately.

**Overhead.** A TCP segment carries a 20-byte TCP header and is wrapped in a
20-byte IP header and an 18-byte Ethernet header plus trailer:

$$H = 20 + 20 + 18 = 58\\ \\text{bytes}$$

**Efficiency.** With payload $P$:

$$\\eta = \\frac{P}{P + 58}$$

For a 1460-byte payload, $\\eta = 1460/1518 \\approx 96\\%$. For a 40-byte
payload — a typical acknowledgement — $\\eta = 40/98 \\approx 41\\%$, so most of
the packet is headers.

**Why this drives design.** A protocol that sends many small messages pays the
overhead repeatedly. This is the justification for Nagle's algorithm, which
coalesces small writes, and for batching in application protocols. It also
explains MTU discovery: a larger MTU amortises the same 58 bytes over more data.

**The layering argument.** Each layer adds its header without knowing the
payload's meaning, so a change in one layer does not require changes in another.
That is why IPv6 could replace IPv4 at layer 3 without touching TCP at layer 4 —
the separation is what makes the protocol stack evolvable.""",

    "tcp-flow-control": """The congestion window's growth rate determines how fast a flow
recovers, and the BDP determines what it must reach.

**Slow start.** The window doubles every round trip, so after $k$ round trips

$$W_k = W_0 \\cdot 2^{k}$$

Reaching a window of $W$ takes

$$k = \\log_2 (W / W_0)$$

round trips — logarithmic, which is why the phase is short despite being
exponential.

**Congestion avoidance.** Growth becomes one segment per round trip:

$$W_k = W_{\\text{ss}} + k$$

which is linear, so recovering a halved window takes about $W/2$ round trips.
The asymmetry — fast up, slow up after a loss — is deliberate: it probes quickly
when there is spare capacity and backs off gently when there is not.

**The bandwidth-delay product.** To keep a link of bandwidth $B$ busy for a
round trip of $RTT$, that much data must be in flight:

$$BDP = B \\times RTT$$

If $W \\cdot \\text{MSS} < BDP$ the sender waits for acknowledgements before the
pipe is full, and throughput is capped at

$$\\frac{W \\cdot \\text{MSS}}{RTT} < B$$

regardless of how fast the link is. On a 1 Gb/s link with 100 ms RTT the BDP is
about 12 MB, far above the historical 64 KB window limit — which is exactly why
window scaling was added.""",

    "transactions-acid": """Isolation levels trade anomaly prevention against concurrency, and
the trade is quantifiable.

**The cost of serialisability.** Under SERIALIZABLE, conflicting transactions
cannot overlap. If a fraction $c$ of transactions conflict and each takes $t$,
the throughput falls toward

$$T \\approx \\frac{1}{t + c \\cdot t} = \\frac{1}{t(1 + c)}$$

while READ COMMITTED allows the non-conflicting overlap and reaches closer to
$n/t$ on $n$ cores.

**Hot rows are the worst case.** If every transaction updates the same row, they
serialise completely regardless of how many cores exist:

$$T = \\frac{1}{t}$$

independent of $n$. This is why a single global counter caps a system's
throughput, and why sharded counters — splitting one counter across $k$ rows and
summing on read — restore parallelism at the cost of an approximate read.

**Durability's cost.** A commit is not complete until the write-ahead log
reaches stable storage, because a crash after acknowledgement would lose a
transaction the client was told succeeded. Group commit amortises this by
batching several transactions into one flush, which is why throughput rises with
concurrency even though each individual commit still waits for a flush.""",

    "processes-threads": """The cost difference between a process and a thread switch comes from
what has to be replaced.

**Thread switch.** Same address space, so only registers and the stack pointer
change:

$$t_{\\text{thread}} \\approx 1\\text{–}2\\ \\mu s$$

**Process switch.** The page-table base register changes, which invalidates the
TLB because virtual addresses now mean something different:

$$t_{\\text{process}} = t_{\\text{thread}} + t_{\\text{TLB refill}}$$

Refilling the TLB is not a one-time cost: the new process's working set must be
re-walked, so the first accesses after the switch miss. The measured cost is
typically several microseconds plus a warm-up period.

**Why the shared heap is a liability.** Two threads writing the same location
without synchronisation can interleave at instruction level. A non-atomic
`count += 1` compiles to load, add, store; if both threads load before either
stores, one increment is lost:

$$\\text{expected lost updates} > 0 \\quad \\text{for unsynchronised shared writes}$$

That is the race condition, and it is why shared memory requires locks while
separate processes do not — a process cannot address another's memory, so the
interleaving is impossible by construction rather than by discipline.""",

    "synchronisation-semaphores": """The semaphore's correctness rests entirely on atomicity, and that
is worth making precise.

**The operations.**

$$\\text{wait}(S): S \\leftarrow S - 1;\\ \\text{if } S < 0 \\text{ then block}$$
$$\\text{signal}(S): S \\leftarrow S + 1;\\ \\text{if } S \\le 0 \\text{ then wake one}$$

$S$ counts available resources; a negative value's magnitude is the number of
blocked threads.

**Why atomicity is not optional.** Compiled, `S -= 1` is load, decrement,
store. If two threads execute this with $S = 1$:

$$\\text{both load } 1 \\to \\text{both compute } 0 \\to \\text{both store } 0$$

so both believe they acquired the resource and both enter the critical section.
The mutex has failed while appearing to work — which is why hardware provides
test-and-set or compare-and-swap as a single uninterruptible instruction.

**Bounded buffer invariant.** With a buffer of size $N$:

$$\\text{empty} + \\text{full} = N \\quad \\text{at all times}$$

The producer waits on `empty` and signals `full`; the consumer does the reverse.
Acquiring the mutex *before* the counting semaphore deadlocks, because a thread
would hold the lock while blocked — the ordering rule is the subtle part.""",

    "file-systems": """The three indirections each exist to solve a specific problem, and
the costs are computable.

**Directory to inode.** A directory entry maps a name to an inode number. Lookup
cost is the cost of finding the entry, which for a hashed directory is $O(1)$
and for a linear one is $O(n)$ in the number of entries — the reason directories
with a million files were historically slow.

**Inode to blocks.** With direct pointers $d$ and singly indirect blocks of
fan-out $f$, a file can reach

$$\\text{size} = \\left(d + f + f^2 + f^3\\right) \\times B$$

With $d = 12$, $f = 1024$ and $B = 4096$ that is about 4 TB. The multi-level
structure is why small files need one read and huge files are still supported.

**Internal fragmentation.** A file of size $s$ occupies

$$\\lceil s / B \\rceil \\times B \\quad \\text{bytes}$$

so the expected waste per file, assuming sizes are uniformly distributed within
a block, is

$$E[\\text{waste}] = \\frac{B}{2}$$

Halving the block size halves the waste but doubles the number of block-map
entries and the metadata I/O. File systems resolve this with extents (allocating
runs of contiguous blocks) and with small-file packing, rather than by choosing
a single block size.""",

    "design-patterns": """Patterns are justified by the cost of change, and that cost can be
made explicit.

**Setup.** Let $m$ be a module, $\\text{fan-in}(m)$ the number of modules that
depend on it, and $\\Delta$ the change being made. If the change alters $m$'s
interface, every dependent must be revisited:

$$C(\\Delta) \\propto \\text{fan-in}(m)$$

**What Observer removes.** Without it, a subject must name its listeners
explicitly, so adding a listener means editing the subject:

$$C(\\text{add listener}) = O(\\text{edit subject} + \\text{retest subject})$$

With Observer, listeners register themselves and the subject only knows the
listener interface, so

$$C(\\text{add listener}) = O(\\text{write new listener})$$

and the subject is untouched. The dependency is inverted, which is the actual
content of the pattern.

**What Strategy removes.** A chain of conditionals selecting an algorithm puts
the choice at the call site, so every new algorithm edits every call site. With
Strategy the choice is a constructor argument, so the call sites are closed for
modification.

**The honest caveat.** A pattern adds indirection, and indirection costs a
reader. Singleton in particular is a global object in disguise: it cannot be
replaced in a test without a seam, which is why dependency injection is usually
the better answer to the same problem.""",

    "encapsulation-inheritance-polymorphism": """The three ideas have different justifications, and only one of them
is about code volume.

**Encapsulation.** A public field can be set to any representable value, so an
invariant such as $0 \\le \\text{balance}$ cannot be enforced by the type. A
method can check before assigning:

$$\\text{invariant enforced} \\iff \\text{all writes go through the method}$$

which is only achievable if the field is private. That is the real argument —
not ceremony, but the only way to make an invariant unbreakable from outside.

**Inheritance.** A subclass reuses an interface and optionally an
implementation. The cost is coupling: a change to the base class can break any
subclass, so

$$C(\\text{change base}) \\propto \\text{number of subclasses}$$

This is why deep hierarchies are fragile and why composition is preferred when
only code reuse, not interface substitution, is wanted.

**Polymorphism.** One call site, behaviour chosen at runtime from the object's
actual type. The mechanism is a dispatch table indexed by method:

$$t_{\\text{virtual}} = t_{\\text{direct}} + t_{\\text{indirect load}}$$

The lookup is cheap, but it also prevents inlining, and inlining is usually
worth more than the lookup it blocks. That is why JITs devirtualise when the
concrete type is monomorphic — the same source code compiles to a direct call
when only one implementation is ever seen.""",

    "limits-continuity": """The epsilon-delta definition makes "approaches" precise, and the
algebra of limits follows from it.

**Definition.** $\\lim_{x \\to a} f(x) = L$ means

$$\\forall \\varepsilon > 0,\\ \\exists \\delta > 0 : 0 < |x - a| < \\delta \\Rightarrow |f(x) - L| < \\varepsilon$$

The clause $0 < |x - a|$ is what allows $f$ to be undefined at $a$ — the limit
describes the approach, never the arrival.

**Why the removable discontinuity still has a limit.** For
$f(x) = (x^2 - 1)/(x - 1)$ the function is undefined at $x = 1$, but for
$x \\ne 1$:

$$f(x) = \\frac{(x-1)(x+1)}{x-1} = x + 1$$

so as $x \\to 1$, $f(x) \\to 2$. The limit exists and equals 2 while $f(1)$ does
not exist at all.

**Continuity requires three things.**

$$\\lim_{x \\to a} f(x) \\text{ exists}, \\qquad f(a) \\text{ exists}, \\qquad \\lim_{x \\to a} f(x) = f(a)$$

Failing any one gives a discontinuity: a hole, a jump, or an asymptote.

**One-sided limits.** The two-sided limit exists only when

$$\\lim_{x \\to a^-} f(x) = \\lim_{x \\to a^+} f(x)$$

At a jump they differ, so no limit exists. This is why the derivative is
undefined at a corner: the difference quotient has different left and right
limits there.""",

    "software-process-models-testing": """The economics of process choice come from when feedback arrives,
and the cost curve is empirical but consistent.

**Cost of a late defect.** Studies across many projects find the cost of fixing
a defect rises by a roughly constant factor per phase:

$$C(\\text{phase}) \\approx C_0 \\cdot k^{\\Delta \\text{phase}}, \\qquad k \\approx 3\\text{–}10$$

So a requirements error found in production costs tens to hundreds of times what
it would have cost in review. Iteration shortens the distance between writing
and finding, which is the entire economic argument for agile over waterfall.

**Test effectiveness.** Defect removal effectiveness is

$$\\text{DRE} = \\frac{D_{\\text{found before release}}}{D_{\\text{found before release}} + D_{\\text{found after}}}$$

Above about 0.85 is generally good. Below 0.7 the process is shipping most of
its defects.

**Why coverage is a weak proxy.** Statement coverage counts executed lines, but
a test with no assertions executes lines and checks nothing, so it raises
coverage while catching nothing. Mutation testing measures whether the suite
actually detects injected faults, which is a strictly stronger signal — and it is
why a high coverage number should not be read as a quality claim.""",

    "boolean-algebra-karnaugh-maps": """The map works because adjacency in Gray code is adjacency in the
algebra, and that connection is provable.

**The key identity.** For any Boolean variable $A$:

$$A + \\bar{A} = 1$$

So a term appearing with $A$ and the same term with $\\bar{A}$ collapses:

$$TA + T\\bar{A} = T(A + \\bar{A}) = T$$

The variable $A$ disappears entirely. This is the whole mechanism of
simplification.

**Why Gray code.** Adjacent cells in a Karnaugh map must differ in exactly one
variable, so that grouping them applies the identity above. Binary ordering
fails: 01 and 10 differ in two bits. Gray code orders

$$00,\\ 01,\\ 11,\\ 10$$

so consecutive entries differ by one bit, and the wraparound from 10 back to 00
also differs by one bit — which is why groups may cross the map edge.

**Why group sizes are powers of two.** A group of $2^k$ adjacent cells eliminates
$k$ variables, since each doubling applies the identity once more:

$$\\text{group } 2^k \\Rightarrow \\text{term loses } k \\text{ literals}$$

A group of three cells is not rectangular in this coordinate system and
corresponds to no single product term, which is why it is not allowed.""",
})

INDUSTRY.update({
    "cpu-scheduling": """Real schedulers do not run a textbook algorithm; they run
multi-level feedback queues, because no single policy serves interactive and
batch work at once.

Linux's CFS uses a virtual runtime and a red-black tree rather than a fixed
quantum, so a process that has run less gets to run next — proportional sharing
without explicit priorities per class. Interactive work stays responsive
because it accumulates virtual runtime slowly.

The engineering problems are rarely the algorithm. They are priority inversion
(a low-priority thread holds a lock a high-priority thread needs, solved by
priority inheritance), CPU affinity (keeping a thread on one core so its cache
stays warm, which can matter more than the scheduling decision), and the
tickless kernel (avoiding timer interrupts so an idle machine actually idles).

For latency-critical work the answer is usually to leave the general scheduler
entirely: real-time classes, CPU isolation, or a dedicated core. General-purpose
schedulers optimise throughput and fairness, which is the opposite of a hard
latency guarantee.""",

    "deadlocks": """Deadlock is handled differently depending on whether it can be
tolerated, and most systems choose detection and recovery over prevention.

Databases are the clear example. PostgreSQL and MySQL both run a wait-for graph
check periodically, find a cycle, and abort one transaction — the victim. They
accept that deadlocks happen because preventing them would require every
transaction to declare its locks up front, which is impractical. The guidance to
developers is to lock tables in a consistent order, which removes the cycles
without any runtime cost.

Operating systems mostly ignore the problem. The classic dining philosophers
setup is a teaching device; real kernels rarely deadlock because they acquire
few resources at once and use lock ordering conventions. Where they do, the
result is a hang and a crash dump.

The practical engineering rule is lock ordering. Give every lock a rank, always
acquire in ascending rank, and cycles become impossible by construction. It is
enforced by convention and review, sometimes by static analysis, and violations
show up as rare hangs that are extremely hard to reproduce — which is why the
convention is worth being strict about.""",

    "memory-management-paging": """Everything about modern memory management follows from the cost of a
TLB miss, which is why huge pages exist.

A 4 KB page means a process using 16 GB needs four million entries. No TLB holds
that, so the hit rate collapses and every access pays a page walk. Huge pages —
2 MB or 1 GB — cut the entry count by three orders of magnitude and are standard
for databases, JVMs with large heaps and anything touching large buffers. The
trade-off is internal fragmentation: a 2 MB page wastes up to 2 MB per mapping.

The out-of-memory killer is the other production reality. Linux overcommits
memory, promising more virtual address space than exists, on the assumption that
not all of it will be used. When that assumption fails the OOM killer scores
processes and kills one. This is why containers need memory limits set
deliberately, and why a JVM heap sized to the container limit behaves very
differently from one sized to the host.

Copy-on-write is what makes fork cheap and what lets a dozen processes share one
copy of a library until one of them writes. Without it, every process spawn
would copy the whole address space.""",

    "cache-memory-locality": """Cache behaviour, not algorithmic complexity, is usually what
decides performance in real numerical and systems code.

The canonical demonstration is matrix multiplication: the naive triple loop
accesses one matrix by column, which strides across memory and defeats the
prefetcher. Loop tiling — processing a block that fits in cache before moving on
— routinely gives a several-fold speedup with the same operation count. BLAS
libraries are essentially carefully tuned tile loops.

False sharing is the multiprocessing version of the same problem. Two threads
writing different variables that share a cache line cause the line to bounce
between cores, and throughput collapses. Padding hot per-thread counters to a
line boundary fixes it. This is invisible in the source and only shows up in a
profiler.

The practical rules are: iterate in memory order, keep hot data small and
contiguous, prefer arrays of structs over structs of arrays when only a few
fields are touched, and measure with a profiler that reports cache misses rather
than guessing from the source.""",

    "indexes-query-performance": """Indexing is the highest-leverage change available in most database
work, and the mistakes are well known.

The first is indexing everything. Every index is a second copy of the data that
must be maintained on write, so a write-heavy table with six indexes can spend
more time maintaining them than doing useful work. The second is indexing a
low-cardinality column — a boolean or a status field — where the index selects
half the table and the planner correctly ignores it.

Composite index column order matters and is often got wrong. An index on
`(a, b)` serves queries filtering on `a`, or on `a` and `b`, but not on `b`
alone, because the leftmost prefix is what the tree is sorted by.

Covering indexes are the advanced move: include the columns a query reads so it
never touches the table at all. For a hot query this can be a large win, at the
cost of a wider index.

The reliable process is to read the query plan, not to guess. `EXPLAIN ANALYZE`
shows the estimated and actual row counts, and a large gap between them means
the statistics are stale — which is fixed by analysing the table, not by adding
an index.""",

    "sql-joins-aggregation": """Query performance work is mostly about giving the planner the
information and the shapes it needs.

The most common failure is a join on columns with different types or collations.
The planner cannot use an index across an implicit cast, so what should be an
index lookup becomes a scan. This is invisible in the SQL and only appears in
the plan.

Aggregation at scale is usually pushed down rather than done at the end:
aggregate within each partition first, then combine. This is the whole basis of
MapReduce and of columnar engines, and it works because sum, count, min and max
are all decomposable. Average is too, if you carry sum and count separately —
averaging averages is wrong, and it is a recurring bug in reporting code.

`WHERE` versus `HAVING` is a performance decision as well as a correctness one.
Filtering before grouping reduces the rows that must be grouped; filtering after
groups everything and then discards. Pushing a predicate into `WHERE` when it
applies to individual rows is usually a large win.

The general discipline is the same as for indexes: read the plan, check that
estimated row counts match actual, and fix the statistics before reaching for a
rewrite.""",

    "normalization": """Normalization is the default for transactional systems and
deliberately abandoned for analytics, and knowing which side you are on is the
real skill.

OLTP databases are normalized to 3NF because they are write-heavy and
correctness-critical: one place per fact means one write and no inconsistency.
OLAP warehouses are denormalized into star schemas — a central fact table
surrounded by dimension tables — because reads dominate and joins are the
expensive part. A star schema trades duplicate dimension data for far fewer
joins per query.

The middle ground is where most real systems live. A normalized core with
carefully chosen denormalized read models — a materialized view, a cache, a
search index — gives correctness where it matters and speed where it is needed.
The cost is that the read model can lag, so anything user-visible must tolerate
eventual consistency.

The mistake to avoid is denormalizing to fix a slow query without first checking
the plan. A missing index or stale statistics cause far more slowness than
normalization does, and denormalizing introduces a consistency problem that does
not go away.""",

    "ip-addressing-subnetting": """Address planning is done once and lived with for years, so the
decisions are made on growth rather than current need.

The standard practice is to allocate on boundaries that make future splits easy.
A /24 per site allows splitting into two /25s or four /26s later without
renumbering. Allocating exactly what is needed today — a /28 for twelve hosts —
guarantees a painful renumber when the site grows.

NAT changed the economics. Private ranges (10/8, 172.16/12, 192.168/16) mean
internal addressing no longer consumes public space, so most organisations use
10/8 internally and plan freely. Public addresses are now mostly reached through
NAT or a load balancer, which also means the address a server sees is not the
client's — a constant source of bugs in logging, rate limiting and geolocation.

IPv6 adoption is partial but real, and the planning rule inverts: with 128 bits
there is no reason to conserve, so the guidance is to allocate generously —
typically a /64 per link regardless of host count, because that is what stateless
autoconfiguration requires. Subnetting for address conservation is an IPv4 habit
that has no place in IPv6.

The operational detail that bites people is that a /31 is valid for
point-to-point links under RFC 3021 but not under the usual formula, and that
DHCP relay must be configured per subnet or clients on remote segments get
nothing.""",

    "osi-tcp-ip-models": """The layered model is how the internet stays evolvable, and the
layer where a problem lives determines who can fix it.

The most common production confusion is diagnosing at the wrong layer. A
firewall dropping ICMP makes a host look unreachable at layer 3 when it is
serving traffic fine at layer 7. `ping` failing tells you about ICMP policy, not
about the service. The discipline is to test each layer: link with `arp`,
reachability with `ping`, transport with a TCP connect, application with an
actual request.

Load balancers make the layer distinction concrete. A layer-4 balancer forwards
TCP connections without reading the payload, so it is fast and protocol-agnostic
but cannot route on URL. A layer-7 balancer terminates TLS, reads HTTP and can
route on path or header — far more capable, and far more expensive per
connection. Knowing which one you have explains what is and is not possible.

Encapsulation overhead is a real design constraint at scale. Protocols that send
many small messages pay 58 bytes of headers per message, which is why batching
and binary formats like Protocol Buffers are used for internal traffic, and why
gRPC multiplexes many calls over one TCP connection.

The model also explains why IPv6 took so long: replacing layer 3 requires every
device on the path to support both, because a packet must traverse routers that
may not understand it.""",

    "tcp-flow-control": """TCP tuning is mostly about long-distance and high-bandwidth links,
where the defaults were set for a much smaller internet.

The bandwidth-delay product is the number that matters. A 10 Gb/s link with
100 ms RTT has a BDP of about 125 MB, so a connection needs a window that large
to fill it. Default socket buffers are far smaller, which is why a transfer
between continents is often a fraction of the link speed no matter how fast the
link is. Raising the buffer limits — and enabling window scaling, which is on by
default now — is the fix.

Bufferbloat is the modern problem. Oversized buffers in consumer routers hold
packets for seconds, so latency under load climbs into the hundreds of
milliseconds. TCP interprets the resulting loss as congestion and backs off, but
by then the delay damage is done. This is why active queue management and
BBR-style congestion control, which probe for bandwidth and RTT directly rather
than inferring from loss, have largely replaced loss-based algorithms on long-fat
paths.

The practical warnings: don't disable Nagle's algorithm globally to fix latency
—it exists to prevent tinygram floods; don't assume loss means congestion on a
wireless link, because radio errors look identical to TCP; and measure with
`iperf3` before and after any change, since TCP behaviour is hard to reason
about from first principles.""",

    "transactions-acid": """Isolation level is a performance dial, and the default is often
chosen without anyone deciding.

Most databases default to READ COMMITTED or REPEATABLE READ rather than
SERIALIZABLE, because full serialisation costs throughput. That means anomalies
are possible by default: a report run twice can give different answers if
another transaction commits in between. Whether that matters is a business
question, not a technical one, and it is worth asking explicitly.

Hot rows are the usual throughput ceiling. A single counter — a global sequence,
a daily total, an inventory count — serialises every transaction that touches
it, so throughput is capped regardless of hardware. Sharding the counter across
k rows and summing on read restores parallelism, at the cost of an approximate
read while writes are in flight.

The write-ahead log is why durability has a floor. Group commit batches several
transactions into one fsync, which is why throughput improves with concurrency
even though each commit still waits for a flush. Disabling `fsync` for
performance is the classic way to lose data on a power cut, and it is a decision
that should never be made quietly.

For distributed systems the trade is starker: cross-node transactions need
two-phase commit, which blocks if the coordinator fails. Most large systems
avoid them entirely and design for eventual consistency with idempotent
operations instead.""",

    "processes-threads": """The process-versus-thread choice is now usually made on isolation
and failure containment rather than raw performance.

The clearest example is the browser. Chrome runs each tab and each extension in
its own process, so a crash or a memory leak in one cannot take down the others,
and the operating system enforces the boundary. The cost is memory — every
process has its own copy of the runtime — which is why browsers are memory
hungry and why they pool processes for same-site tabs.

Servers went the other way and then partly back. One-thread-per-connection is
simple but does not scale past a few thousand connections, so event loops with
coroutines took over: Node, nginx, asyncio. They handle tens of thousands of
concurrent connections in one process, but a single blocking call stalls
everything, which is why the discipline around not blocking is strict.

Containers changed the calculus again. A container is a process with isolated
namespaces and resource limits, so it gives much of the isolation of a VM at the
cost of a process. The modern default is one process per container, with
isolation handled outside the application — which is why the old
many-threads-in-one-process design is less common than it was.

The one thing that has not changed: shared mutable state is the source of races,
and the cheapest fix is usually to stop sharing rather than to add a lock.""",

    "synchronisation-semaphores": """Almost no application code uses raw semaphores now; the primitives
are wrapped, and the bugs moved up a level.

The standard toolkit is the mutex, the condition variable, the read-write lock
and the atomic. Semaphores survive where a counted resource is genuinely being
modelled — a connection pool limiting concurrent database connections is
literally a counting semaphore, and so is a bounded work queue.

The dominant bug class is no longer forgetting to lock; it is lock ordering and
holding a lock too long. Inconsistent lock acquisition order deadlocks under
concurrency that testing rarely reproduces, which is why the rule is to give
locks a global order and always acquire ascending. Holding a lock across a
network call or a disk read serialises everything behind it and shows up as
latency that no profiler attributes to the lock.

The modern answer is often to avoid shared state entirely. Actor models and
message passing give each unit of work its own state and communicate by
sending, so there is nothing to lock. Go's guidance — do not communicate by
sharing memory, share memory by communicating — is this idea in one line, and it
is why so much concurrent code now looks like channels rather than locks.

Where shared state is unavoidable, the discipline is: keep critical sections
short, never call out to unknown code while holding a lock, and test with a
race detector rather than hoping.""",

    "file-systems": """File system choice is driven by the workload and by what you can
afford to lose, and the differences are large.

Journaling is the default for general-purpose systems — ext4, XFS, NTFS. A
journal records intent before the change, so a crash leaves either the old
state or the new one, never a mixture. The cost is writing some data twice,
which is why databases often disable the file system journal and rely on their
own write-ahead log instead.

Copy-on-write systems — ZFS, Btrfs — never overwrite in place, which gives
snapshots and checksums essentially for free, and detects silent corruption that
a traditional file system cannot see. The trade is fragmentation on random
writes, which is why databases on ZFS need careful tuning.

The operational realities that matter more than the choice: `fsync` semantics
are the difference between durable and merely written, and applications that
care must call it explicitly. Directory performance still degrades with millions
of entries on some file systems. And the space reported free can differ from the
space available, because of reserved blocks and delayed allocation — which is why
"disk full" errors sometimes arrive when `df` shows free space.

For networked and cloud storage the inode and metadata costs dominate. A
workload of a million tiny files is often far slower and more expensive than a
thousand large ones holding the same bytes.""",

    "cache-memory-locality": """The concepts generalize past the CPU cache, and that is where they
are usually applied in application work.

Application-level caching is the same trade-off with different numbers. A Redis
lookup is microseconds versus milliseconds for a database round trip, so the hit
rate decides the cost. The invalidation problem is the hard part: a cache that
can serve stale data must either expire entries or be told when the underlying
data changes, and the second is where most cache bugs live.

Database buffer pools are caches over pages, and their hit rate is the single
best predictor of query latency. A working set that fits in the pool runs
entirely in memory; one that does not turns every query into disk I/O. This is
why memory sizing for a database is about working-set size rather than total
data size.

CDNs are caches at the network layer, with the same invalidation problem at a
much larger scale — which is why cache-busting filenames and short TTLs on HTML
with long TTLs on hashed assets is the standard pattern.

The unifying lesson is that every cache introduces a second copy of the truth
and a window in which they disagree. The design question is never whether to
cache but how long the disagreement is acceptable, and what happens when it is
detected.""",

    "limits-continuity": """Limits are not an abstraction engineers skip; they are how
numerical methods are made safe, and where they break is where bugs live.

The first practical use is small-angle and Taylor approximations. For small $x$,
$\\sin x \\approx x$ and $e^x \\approx 1 + x$, both of which come straight from
the limit definition of the derivative. Control engineers linearise around an
operating point for exactly this reason, and the approximation is valid only
while the perturbation stays small — a fact that is easy to forget when a
controller is pushed outside its design range.

The second is numerical differentiation. The derivative is defined as a limit,
but a computer cannot take one, so it uses a finite step:

$$f'(x) \\approx \\frac{f(x+h) - f(x)}{h}$$

As $h$ shrinks the truncation error falls, but the floating-point rounding error
grows, because the two terms in the numerator become nearly equal and their
difference loses significant digits. There is an optimal $h$ around the square
root of machine epsilon, and choosing $h$ far smaller makes the answer worse —
a genuinely counterintuitive failure that appears in simulation code.

The third is convergence of iterative methods. Newton-Raphson and every
fixed-point iteration depend on the sequence having a limit, and they diverge or
oscillate when the conditions fail. Checking convergence rather than assuming it
is the difference between a solver that works and one that silently returns
nonsense.""",

    "design-patterns": """Patterns are vocabulary for design review, and their value in a
team is mostly communicative.

Saying "use an Observer here" conveys a whole structure in one word, which makes
design discussion faster and code review more precise. That is the strongest
practical argument for knowing them, stronger than any claim about code quality.

The ones that appear constantly in real systems: Strategy and Command behind
plugin and job systems; Observer behind event buses and reactive frameworks;
Factory and Builder behind object construction in frameworks where the concrete
type is decided by configuration; Adapter behind every integration layer that
reconciles two APIs; Facade behind SDKs that hide a complicated backend.

The equally important lesson is over-application. The original book's examples
were in C++ and Smalltalk, and many patterns exist to work around the absence of
a feature. In a language with first-class functions, Strategy is often just a
function argument; in one with duck typing, Adapter is often unnecessary. Adding
a pattern where the language already provides the mechanism adds indirection and
nothing else.

Singleton deserves particular caution. It is a global object that cannot be
substituted in a test, and it creates hidden dependencies that the type system
does not show. Dependency injection solves the same problem — one instance,
controlled lifetime — without those costs, which is why it is the modern
default.""",

    "encapsulation-inheritance-polymorphism": """Object-oriented design in production is mostly about where the
seams are, and the language features are secondary.

The most valuable habit is programming to an interface rather than an
implementation. A function that takes a `PaymentGateway` interface can be tested
with a fake, and a new provider can be added without touching the caller. This
is polymorphism used for testability rather than for cleverness, and it is the
single change that most improves a codebase's evolvability.

Deep inheritance hierarchies are the classic failure. A base class accumulates
behaviour that some subclasses do not want, so it grows flags and hooks until
changing it risks breaking everything below. The usual repair is composition:
extract the behaviour into a collaborator and inject it. The rule of thumb —
prefer composition over inheritance — exists because this failure is so common.

Encapsulation pays off most at module boundaries. A well-chosen public
interface lets the internals change without affecting callers, which is what
makes refactoring possible at all. Exposing internal types in a public API is
the mistake that locks a design in place.

The performance question is mostly settled: virtual dispatch is cheap, but it
blocks inlining, and in hot loops over millions of small calls that matters.
JITs devirtualise when only one implementation is ever seen, so idiomatic code
usually gets the direct call for free. Profile before restructuring for it.""",

    "software-process-models-testing": """The practices that actually reduce defects are measurable, and they
are not the ones most often debated.

Code review catches a large share of defects before test, and its value is at
least as much in knowledge sharing as in bug finding. The evidence is consistent
across studies: reviewed code has fewer escaped defects, and the effect is
strongest on design-level problems that no test would find.

Continuous integration shortens the feedback loop to minutes, which is the whole
point. A build broken for a day is expensive to untangle; broken for five
minutes it is trivial. The discipline that makes it work is small, frequent
commits and a fast test suite — which is why test speed is a feature.

Trunk-based development with feature flags removes the long-lived branch and the
painful merge, and it decouples deploying from releasing, so a change can reach
production dark and be enabled gradually. That is also the safest rollback
mechanism available: turning a flag off is faster and lower-risk than reverting
a deployment.

The testing pyramid still holds: many fast unit tests, fewer integration tests,
a small number of end-to-end tests. Inverting it produces a suite that is slow
and flaky, and a slow flaky suite gets ignored, which is worse than none.

The metric worth tracking is escaped defects and time to restore, not lines of
code or commit counts. The second in particular is what tells you whether the
rest of the process is working.""",

    "concrete-mix-design-workability": """Mix design in practice is dominated by admixtures, which is where
the textbook treatment stops and the real work begins.

Superplasticisers are the key tool: they disperse cement particles so the mix
flows at a much lower water content. This is what makes high-strength concrete
possible at all, since strength is governed by the water-cement ratio and
workability would otherwise force too much water. Self-compacting concrete, which
flows into congested reinforcement without vibration, is essentially a
superplasticiser plus a viscosity modifier.

Supplementary cementitious materials — fly ash, slag, silica fume — replace part
of the cement. They reduce cost and the carbon footprint, and they usually
improve long-term strength and durability, but they slow early strength gain.
That trade matters on a programme: a slab that reaches stripping strength a day
later changes the schedule.

The site realities are what cause failures. Adding water to improve workability
is the most common one, and it silently reduces strength. Aggregate moisture
varies with weather, so the batch water must be adjusted or the actual
water-cement ratio drifts. Curing is routinely cut short, and concrete that dries
too early never reaches its design strength no matter how good the mix was.

Testing is by cube or cylinder at 7 and 28 days, and the 7-day result is used to
predict the 28-day one. Non-destructive methods — rebound hammer, ultrasonic
pulse velocity — give an indication on existing structures but are not a
substitute for cores when the result matters.""",

    "maxwells-equations": """Maxwell's equations are the design basis for essentially all of
electrical and communications engineering, and different subsets do different
jobs.

Circuit design uses the quasi-static approximation, where the fields are assumed
to settle instantly. This is valid while the physical size of the circuit is
small compared with the wavelength — roughly below a tenth of it. At 1 GHz the
wavelength is 30 cm, so above about 3 cm a PCB trace stops being a wire and
becomes a transmission line, and the full field treatment is required. That
transition is what signal-integrity engineering is about.

Antenna design is Faraday and Ampere-Maxwell working together: an accelerating
charge produces a changing field that sustains itself and propagates. The
radiation pattern, gain and impedance all follow from solving the equations for
a given geometry, which is what simulation tools do.

Waveguides, optical fibres and photonic devices are solved from the same
equations with boundary conditions. The cutoff frequency of a waveguide falls
straight out of them.

The practical engineering consequence is the speed of light as a hard limit. In
a distributed system, a 1000 km round trip takes about 6.7 ms in fibre no matter
how the software is written. Consensus protocols, synchronous replication and
high-frequency trading all run into this, and it is why geographic redundancy and
low latency are in direct conflict.""",
})


# ---------------------------------------------------------------------------
# Core engineering - derivations and industry practice
# ---------------------------------------------------------------------------

DERIVATIONS.update({
    "kirchhoffs-laws": """Both laws are conservation principles, and both can be derived from
Maxwell's equations in the circuit limit.

**KCL from charge conservation.** Current is charge flow, so the net current
into a region equals the rate of charge accumulation inside it:

$$\\sum_k I_k = -\\frac{dQ_{\\text{inside}}}{dt}$$

A circuit node is modelled as having no volume, so it cannot store charge and
the right side is zero:

$$\\sum_k I_k = 0$$

This is why KCL fails at high frequency: a real junction has capacitance and does
store charge, so the sum is not zero once the rate of change matters.

**KVL from energy conservation.** The electrostatic field is conservative, so
the work done moving a charge around a closed path is zero:

$$\\oint \\vec{E} \\cdot d\\vec{l} = 0 \\;\\Rightarrow\\; \\sum_k V_k = 0$$

By Faraday's law the general statement is
$\\oint \\vec{E} \\cdot d\\vec{l} = -d\\Phi_B/dt$, so KVL holds only when the
changing magnetic flux through the loop is negligible. A loop enclosing a
transformer core violates it — which is exactly why the induced EMF appears as a
separate source term in circuit analysis rather than being absorbed into the
loop sum.

**Counting independent equations.** For a network with $n$ nodes and $b$
branches, KCL gives $n-1$ independent equations (the last follows from the
others, since all current leaving one node must arrive somewhere) and KVL gives
$b - n + 1$ from the independent loops. Together that is $b$ equations for $b$
unknown branch currents, which is why the system is solvable.""",

    "transformers": """The turns ratio comes from Faraday's law applied to a shared flux,
and the power relation follows from assuming no loss.

**The induced voltage.** The same flux $\\Phi$ links both windings, so by
Faraday's law each turn has the same induced EMF $e = -d\\Phi/dt$. With $N_1$
and $N_2$ turns:

$$V_1 = N_1 \\frac{d\\Phi}{dt}, \\qquad V_2 = N_2 \\frac{d\\Phi}{dt}$$

Dividing eliminates the flux entirely:

$$\\frac{V_1}{V_2} = \\frac{N_1}{N_2}$$

This is why the ratio depends only on turns, not on core material or frequency —
though frequency does set the flux density the core must carry.

**The current ratio.** An ideal transformer stores no energy, so input power
equals output power:

$$V_1 I_1 = V_2 I_2 \\;\\Rightarrow\\; \\frac{I_1}{I_2} = \\frac{N_2}{N_1}$$

Current transforms inversely to voltage. There is no way around this: stepping
voltage up necessarily steps current down, and the product is preserved.

**Why high voltage for transmission.** Line loss is

$$P_{\\text{loss}} = I^2 R = \\left(\\frac{P}{V}\\right)^{2} R$$

so doubling the transmission voltage quarters the loss for the same power
delivered. That single relation is the reason national grids run at hundreds of
kilovolts and step down only near the user.

**Why it needs AC.** A steady DC current produces constant flux, so
$d\\Phi/dt = 0$ and no voltage is induced in the secondary. Switching DC on and
off works — that is what a switched-mode power supply does — but a plain DC
supply does nothing.""",

    "ac-circuits-power-factor": """The three powers come from separating the instantaneous product of
voltage and current into an average and an oscillating part.

**Setup.** With $v = V_m \\sin \\omega t$ and $i = I_m \\sin(\\omega t - \\phi)$:

$$p(t) = vi = V_m I_m \\sin \\omega t \\sin(\\omega t - \\phi)$$

Using the product-to-sum identity:

$$p(t) = \\frac{V_m I_m}{2}\\left[\\cos\\phi - \\cos(2\\omega t - \\phi)\\right]$$

**The two terms.** The first is constant; the second oscillates at twice the
supply frequency and averages to zero over a cycle. Averaging:

$$P = \\frac{V_m I_m}{2}\\cos\\phi = V_{\\text{rms}} I_{\\text{rms}} \\cos\\phi$$

which is the real power in watts.

**The three quantities.**

$$S = V_{\\text{rms}} I_{\\text{rms}} \\quad (\\text{VA}), \\qquad "
"P = S\\cos\\phi \\quad (\\text{W}), \\qquad Q = S\\sin\\phi \\quad (\\text{VAR})$$

and they satisfy

$$S^2 = P^2 + Q^2$$

which is the power triangle. $\\cos\\phi$ is the power factor by definition.

**Why utilities charge for it.** The cable must carry the full apparent current
$I = S/V$, so a load at $\\cos\\phi = 0.7$ draws

$$\\frac{1}{0.7} \\approx 1.43$$

times the current for the same real power. The conductors, transformers and
switchgear are all sized on current, so the extra 43% is real cost that does no
work. Correcting to unity with a capacitor bank supplies $Q$ locally and removes
it from the network.""",

    "convolution-lti-systems": """The convolution integral follows from linearity and time
invariance alone — nothing else about the system is assumed.

**Decompose the input.** Any signal can be written as a sum of scaled, shifted
impulses:

$$x(t) = \\int_{-\\infty}^{\\infty} x(\\tau)\\,\\delta(t - \\tau)\\, d\\tau$$

**Apply linearity.** The response to a sum is the sum of the responses, and
scaling carries through, so

$$y(t) = \\int_{-\\infty}^{\\infty} x(\\tau)\\, \\mathcal{S}\\{\\delta(t-\\tau)\\}\\, d\\tau$$

**Apply time invariance.** The response to $\\delta(t - \\tau)$ is the impulse
response shifted by $\\tau$, that is $h(t - \\tau)$. Substituting:

$$y(t) = \\int_{-\\infty}^{\\infty} x(\\tau)\\, h(t - \\tau)\\, d\\tau = (x * h)(t)$$

So $h$ completely characterises the system. Nothing about capacitors, masses or
pipes entered the argument.

**Causality.** A physical system cannot respond before it is driven, so
$h(t) = 0$ for $t < 0$, and the integral's upper limit becomes $t$:

$$y(t) = \\int_{-\\infty}^{t} x(\\tau) h(t-\\tau)\\, d\\tau$$

**Stability.** The output is bounded for every bounded input exactly when

$$\\int_{-\\infty}^{\\infty} |h(t)|\\, dt < \\infty$$

which is a testable condition on $h$ alone.

**Why the transform helps.** Taking the Fourier transform turns convolution into
multiplication, $Y(\\omega) = X(\\omega)H(\\omega)$, so filtering becomes
arithmetic. That single property is why the frequency domain is the natural
place to design filters.""",

    "semiconductors-pn-junctions": """The diode equation comes from balancing drift and diffusion across
the junction.

**The built-in potential.** In equilibrium the diffusion current from the
concentration gradient exactly cancels the drift current from the field. Setting
them equal and integrating across the junction gives

$$V_{bi} = \\frac{kT}{q} \\ln\\!\\left(\\frac{N_A N_D}{n_i^2}\\right)$$

which is about 0.7 V for silicon at room temperature. This is the barrier that
an applied voltage must overcome.

**Under forward bias.** Applying $V$ lowers the barrier to $V_{bi} - V$, so the
diffusion current grows exponentially while the drift current is unchanged:

$$I = I_s \\left(e^{qV/kT} - 1\\right)$$

The thermal voltage $kT/q$ is about 26 mV at room temperature, so the current
roughly multiplies by ten for every 60 mV of forward bias. That steepness is why
a diode appears to "turn on" at a threshold rather than conducting gradually.

**Under reverse bias.** $V$ is negative, the exponential term vanishes, and

$$I \\approx -I_s$$

a tiny leakage current set by thermally generated carriers. It roughly doubles
for every 10 K rise in temperature, which is why semiconductor devices are
specified with a maximum junction temperature.

**Breakdown.** Beyond a critical reverse field the junction conducts heavily, by
Zener tunnelling in heavily doped junctions or avalanche multiplication in
lightly doped ones. This is a controlled effect in a Zener diode and a
destructive one in an ordinary rectifier.""",

    "stress-strain-hookes-law": """Hooke's law is the linear term of a more general relation, and its
limit is where the atomic picture takes over.

**The atomic origin.** Atoms in a solid sit at a separation where attractive and
repulsive forces balance. The interatomic potential $U(r)$ has a minimum at the
equilibrium spacing $r_0$. For a small displacement $x$ from that minimum:

$$U(r_0 + x) \\approx U(r_0) + \\frac{1}{2}k x^2$$

because the first derivative vanishes at the minimum. The force is therefore
proportional to displacement, which at the continuum level is stress
proportional to strain:

$$\\sigma = E\\varepsilon$$

The cubic and higher terms in the expansion are what make real materials
nonlinear at large strain.

**From the definition of stress and strain.**

$$\\sigma = \\frac{F}{A}, \\qquad \\varepsilon = \\frac{\\Delta L}{L} \\;\\Rightarrow\\; "
"\\Delta L = \\frac{FL}{AE}$$

which is the form used for deflection calculations. The product $AE/L$ is the
axial stiffness, analogous to a spring constant.

**Strain energy.** The area under the linear portion is the energy stored per
unit volume:

$$u = \\int_0^{\\varepsilon} \\sigma\\, d\\varepsilon = \\frac{1}{2}E\\varepsilon^2 "
"= \\frac{\\sigma^2}{2E}$$

This is what a spring releases, and it is why a material with a high elastic
limit stores more energy before yielding.

**The limit of validity.** The proportional limit is typically within a fraction
of a percent of strain for metals. Past yield, dislocations move and the
deformation becomes permanent, so the linear relation no longer describes
anything — which is why elastic analysis is only the first stage of a structural
calculation.""",

    "fluid-statics-manometry": """The hydrostatic equation comes from a force balance on a fluid
element, and everything in fluid statics follows from it.

**The balance.** Take a small element of height $dz$ and area $A$. Pressure acts
on both faces and weight acts downward, so equilibrium requires

$$pA - (p + dp)A - \\rho g A\\, dz = 0 \\;\\Rightarrow\\; \\frac{dp}{dz} = -\\rho g$$

**Integrate for an incompressible fluid.** With $\\rho$ constant:

$$p_2 - p_1 = -\\rho g (z_2 - z_1) = \\rho g h$$

where $h$ is the depth below the reference. Pressure grows linearly with depth
because the weight of fluid above grows linearly with depth.

**The manometer reading.** Balancing the unknown pressure against a column of
manometer fluid:

$$P + \\rho_1 g h_1 = P_{\\text{atm}} + \\rho_2 g h_2$$

so the gauge pressure is

$$P_{\\text{gauge}} = \\rho_2 g h_2 - \\rho_1 g h_1$$

Only the *difference* in height between the two arms appears, which is why
adding fluid equally to both arms changes nothing.

**Why mercury.** A given pressure supports a column of height $h = p/(\\rho g)$.
For one atmosphere:

$$h_{\\text{water}} = \\frac{101325}{1000 \\times 9.81} \\approx 10.3\\ \\text{m}, "
"\\qquad h_{\\text{Hg}} = \\frac{101325}{13600 \\times 9.81} \\approx 0.76\\ \\text{m}$$

A 10-metre water column is impractical; 760 mm of mercury fits on a bench, which
is the historical reason for the unit.

**Gauge versus absolute.** A manometer open to the atmosphere reads gauge
pressure. Absolute pressure is

$$P_{\\text{abs}} = P_{\\text{gauge}} + P_{\\text{atm}}$$

and confusing the two is a common and expensive error, particularly in
thermodynamic calculations where absolute pressure is required.""",

    "first-law-energy-balance": """The first law is a statement that energy is a state function, and
the derivation makes clear why heat and work are not.

**The statement.** For a closed system:

$$\\Delta U = Q - W$$

where $Q$ is heat added and $W$ is work done *by* the system.

**Why U is a state function.** Joule's experiments showed that the same change
of state can be produced by different combinations of heat and work — stirring
adiabatically raises the temperature exactly as much as adding the equivalent
heat. Since the end state depends only on where the system started and ended,
not on the path, there must be a property whose change equals the net energy
added:

$$\\Delta U = \\oint \\delta Q - \\oint \\delta W \\quad \\text{for any path between the same states}$$

**Why Q and W are path functions.** For a cyclic process the system returns to
its start, so $\\Delta U = 0$ and

$$\\oint \\delta Q = \\oint \\delta W$$

Heat in equals work out, but neither is individually zero, and both depend on how
the cycle is traversed. That is why $\\delta Q$ and $\\delta W$ are written with
an inexact differential while $dU$ is exact.

**The work term for a gas.** For a quasi-static expansion against pressure:

$$W = \\int_{V_1}^{V_2} p\\, dV$$

which is the area under the path on a $p$-$V$ diagram — visibly path-dependent.

**Special cases.** Adiabatic: $Q = 0$, so $\\Delta U = -W$ and the work comes
from internal energy, which is why an expanding gas cools. Constant volume:
$W = 0$, so $\\Delta U = Q$. Constant pressure: $Q = \\Delta H$, which is why
enthalpy is defined as $H = U + pV$ — it makes the common case a simple
difference.""",

    "equilibrium-of-forces-free-body-diagrams": """The equilibrium equations come from Newton's laws applied to a body
at rest, and their number determines what is solvable.

**From Newton's second law.** For a rigid body:

$$\\sum \\vec{F} = m\\vec{a}, \\qquad \\sum \\vec{M}_G = I_G \\alpha$$

At rest both accelerations are zero, so

$$\\sum \\vec{F} = 0, \\qquad \\sum \\vec{M} = 0$$

**Resolving in the plane.** A two-dimensional problem gives three independent
scalar equations:

$$\\sum F_x = 0, \\qquad \\sum F_y = 0, \\qquad \\sum M_z = 0$$

**What this means for solvability.** Three equations solve up to three unknowns.
A simply supported beam has a pin (two reactions) and a roller (one) — exactly
three, so it is statically determinate and solvable by equilibrium alone. Add a
third support and there are four unknowns against three equations: statically
indeterminate, and the solution requires deformation compatibility, which is
where material stiffness enters.

**Choosing the moment point.** Taking moments about a point where unknown forces
act eliminates them from that equation, which is the standard technique for
reducing simultaneous equations. Any point may be used — the result is the same
— but a well-chosen one does the algebra for you.

**Why the free-body diagram is not optional.** The equations above apply to the
forces *on* the body. A force the body exerts on something else must not appear,
and a contact that is forgotten leaves the balance unsolvable. Drawing the
isolation first is what makes it possible to check that every contact is
accounted for and no extra force has been invented.""",

    "effective-stress-bearing-capacity": """Effective stress is the part of the total load carried by the soil
skeleton, and the derivation shows why water carries the rest.

**The balance at a plane.** Consider a horizontal plane at depth $z$ with total
area $A$. The total vertical force is the weight of everything above:

$$\\sigma_v = \\sum_i \\gamma_i z_i$$

That force is shared between the water in the pores and the contacts between
grains. The water carries the pore pressure:

$$u = \\gamma_w z_w$$

where $z_w$ is the depth below the water table. The remainder passes through the
grain contacts, which is what gives soil its strength:

$$\\sigma'_v = \\sigma_v - u$$

**Terzaghi's principle.** This is the effective stress principle, and it holds
because water cannot carry shear. Only the grain-to-grain contacts can, so
shear strength and volume change depend on $\\sigma'$ alone:

$$\\tau_f = c' + \\sigma' \\tan\\phi'$$

**Why buoyant weight below the water table.** Substituting
$\\sigma_v = \\gamma z$ and $u = \\gamma_w z$ below the water table:

$$\\sigma' = \\gamma z - \\gamma_w z = (\\gamma - \\gamma_w) z = \\gamma' z$$

so the buoyant unit weight $\\gamma'$ is the right quantity to use, not the
saturated one. Using $\\gamma_{\\text{sat}}$ overestimates effective stress and
therefore the ground's capacity.

**Why it explains quicksand.** If upward seepage raises $u$ until it equals
$\\sigma_v$, then $\\sigma' = 0$ and the soil has no shear strength at all. The
critical gradient is

$$i_c = \\frac{\\gamma'}{\\gamma_w}$$

which for typical soils is close to 1. Excavations that drain into themselves
fail by exactly this mechanism, which is why dewatering is designed with a
factor of safety on the gradient.""",

    "per-unit-system-fault-analysis": """The per-unit system is a change of units chosen so that transformer
ratios cancel, and the cancellation is easy to show.

**Definitions.** With a base power $S_b$ and base voltage $V_b$:

$$Z_b = \\frac{V_b^2}{S_b}, \\qquad I_b = \\frac{S_b}{\\sqrt{3} V_b}, \\qquad "
"Z_{pu} = \\frac{Z_{\\text{actual}}}{Z_b}$$

**Why the turns ratio disappears.** A transformer's impedance referred to the
primary is $Z_1$; referred to the secondary it is

$$Z_2 = Z_1 \\left(\\frac{N_2}{N_1}\\right)^{2} = Z_1 \\left(\\frac{V_2}{V_1}\\right)^{2}$$

But the base impedance also scales as $V^2$, since $Z_b = V_b^2/S_b$ with the
same $S_b$ on both sides:

$$Z_{b2} = Z_{b1} \\left(\\frac{V_2}{V_1}\\right)^{2}$$

Dividing, the ratio cancels entirely:

$$Z_{2,pu} = \\frac{Z_2}{Z_{b2}} = \\frac{Z_1 (V_2/V_1)^2}{Z_{b1}(V_2/V_1)^2} = Z_{1,pu}$$

So the same per-unit impedance applies on either side. That is the whole point:
the transformer disappears from the arithmetic.

**Changing base.** Equipment nameplates give impedance on the equipment's own
rating, so it must be converted:

$$Z_{\\text{new}} = Z_{\\text{old}} \\times \\frac{S_{\\text{new}}}{S_{\\text{old}}} "
"\\times \\left(\\frac{V_{\\text{old}}}{V_{\\text{new}}}\\right)^{2}$$

Omitting this step is the most common error in a fault study, and it produces a
fault current that is wrong by the ratio of the ratings.

**The fault current.** On the common base, with the pre-fault voltage at 1.0 pu:

$$I_{f,pu} = \\frac{1}{Z_{pu}}, \\qquad I_f = I_{f,pu} \\times I_b$$

A three-phase fault needs only the positive-sequence network, which is why it is
both the largest and the simplest case to compute.""",

    "material-energy-balances": """The balance equation is a statement of conservation applied to a
chosen region, and every term exists because of something physical.

**Derivation from conservation.** For any extensive quantity $X$ in a region:

$$\\frac{dX}{dt} = \\underbrace{\\sum \\dot{X}_{\\text{in}}}_{\\text{in}} "
"- \\underbrace{\\sum \\dot{X}_{\\text{out}}}_{\\text{out}} "
"+ \\underbrace{\\dot{X}_{\\text{gen}} - \\dot{X}_{\\text{cons}}}_{\\text{reaction}}$$

**Total mass.** Mass is neither created nor destroyed in chemical processes, so
the generation terms vanish:

$$\\frac{dm}{dt} = \\sum \\dot{m}_{\\text{in}} - \\sum \\dot{m}_{\\text{out}}$$

At steady state $dm/dt = 0$ and this becomes simply IN = OUT, which is the
starting point of nearly every design calculation.

**Per species.** Individual species *are* created and destroyed by reaction, so
for species $i$:

$$\\frac{dn_i}{dt} = \\sum \\dot{n}_{i,\\text{in}} - \\sum \\dot{n}_{i,\\text{out}} + \\nu_i r$$

where $\\nu_i$ is the stoichiometric coefficient and $r$ the rate of reaction.
This is why a balance is written per species: total mass is conserved, but a
component is not.

**Energy.** Taking $X$ as energy and using the first law:

$$\\frac{dE}{dt} = \\sum \\dot{m}\\left(h + \\frac{u^2}{2} + gz\\right)_{\\text{in}} "
"- \\sum \\dot{m}\\left(h + \\frac{u^2}{2} + gz\\right)_{\\text{out}} + \\dot{Q} - \\dot{W}_s$$

For most process equipment the kinetic and potential terms are small against the
enthalpy, leaving $\\Delta H = Q - W_s$.

**The critical convention.** Enthalpy is only defined up to a reference state, so
every stream's enthalpy must be measured from the *same* reference — typically
the elements at 25 °C. Mixing references produces a balance that is wrong by a
constant offset and gives no obvious error, which is why specifying the basis is
part of the calculation and not a footnote.""",

    "concrete-mix-design-workability": """Abrams' law relates strength to the water-cement ratio, and the
mechanism is porosity.

**The empirical law.** For a given set of materials and curing conditions:

$$f_c = \\frac{A}{B^{\\,w/c}}$$

where $A$ and $B$ are constants for the aggregate and the curing regime. Strength
falls as the ratio rises, which is the single most important relation in mix
design.

**Why.** Cement hydration needs about

$$w/c \\approx 0.25$$

to complete the chemical reaction. Any water beyond that occupies space; when it
evaporates it leaves a pore. So the capillary porosity is roughly proportional
to the excess water:

$$\\text{porosity} \\propto (w/c - 0.25)$$

and strength falls as porosity rises, because a pore is both a void carrying no
load and a stress concentrator.

**The workability conflict.** More water makes the mix easier to place, so the
site is pushed toward a higher ratio and the design toward a lower one. That
tension is the whole problem of mix design, and admixtures resolve it: a
superplasticiser disperses the cement particles so the mix flows at a low water
content, giving workability and strength together.

**The design method.** Choose the target mean strength, which is the specified
characteristic strength plus a margin for variability:

$$f_{\\text{target}} = f_{ck} + 1.65 s$$

for 5% of results to fall below the characteristic value, where $s$ is the
standard deviation of the plant's production. Convert that to a maximum
water-cement ratio using the strength relation, check durability limits (which
often govern in aggressive exposure), then adjust for aggregate moisture — the
step most often missed, since wet aggregate contributes water the batch has
already counted.""",
})

INDUSTRY.update({
    "kirchhoffs-laws": """Circuit analysis at scale is done by machine, and the methods are
built directly on these two laws.

SPICE — and every simulator descended from it — formulates modified nodal
analysis, which writes KCL at every node and adds branch equations for voltage
sources. The result is a sparse linear system solved at each time step. So the
law taught by hand is literally the code that runs inside every analogue design
tool.

The practical skill is knowing when the lumped model stops applying. KVL assumes
no changing flux through the loop, which fails at high frequency or near
magnetics. A PCB trace longer than about a tenth of the signal wavelength is a
transmission line, not a wire, and KVL applied across it gives a wrong answer.
This is the boundary where circuit theory hands over to signal-integrity
engineering.

Ground is where KCL meets reality. A "ground" node is not an ideal zero-ohm
reference: it has impedance, so current flowing through it produces a voltage
that appears as noise elsewhere. That is why analogue and digital grounds are
separated and joined at one point, and why measuring with a long ground lead on
an oscilloscope picks up noise that is not in the circuit.

The most common practical error is sign convention. Assigning current directions
arbitrarily is fine — a wrong guess gives a negative answer — but changing
convention partway through a calculation gives a wrong one that looks plausible.""",

    "transformers": """Transformer engineering in practice is about losses, heat and
lifetime, none of which appear in the ideal model.

Losses come in two kinds. Copper loss is $I^2 R$ in the windings and varies with
load. Iron loss is hysteresis and eddy currents in the core and is roughly
constant, since it depends on flux density and frequency, not load. The total
efficiency curve therefore peaks at the load where the two are equal, which is
usually well below full load — a detail that matters when sizing a transformer
for a duty cycle rather than a peak.

Cooling decides rating. The same core and windings carry more power with forced
oil circulation than with natural convection, so ratings are quoted per cooling
class. Winding temperature, not current, is what ages the insulation, and the
rule of thumb is that every 6 K above the design temperature halves the
insulation life. This is why load guides are based on hot-spot temperature rather
than on nameplate current.

Inrush current is a real operational problem. Energising a transformer at the
wrong point on the voltage wave can drive the core into saturation, drawing many
times rated current for several cycles. This is why differential protection must
distinguish inrush from an internal fault — usually by looking for second
harmonic content — or it will trip on every energisation.

Harmonics from non-linear loads cause extra eddy-current loss that rises with
the square of the harmonic order, so a transformer supplying rectifiers and
variable-speed drives must be derated or specified with a K-factor. This has
become the normal case rather than the exception in commercial buildings.""",

    "ac-circuits-power-factor": """Power factor correction is a standard commercial practice, and it is
usually driven by the tariff rather than by the physics.

Industrial loads are inductive — motors and transformers dominate — so the
power factor typically sits around 0.8 lagging. Utilities charge a penalty below
about 0.9 or 0.95, because they must size cables, transformers and switchgear on
apparent current while billing for real power. Installing a capacitor bank
supplies the reactive power locally, removes the penalty, and reduces losses in
the site's own distribution.

The sizing is straightforward but the application is not. Overcorrecting makes
the power factor leading, which raises the voltage and can be worse than
lagging. Capacitors also resonate with system inductance at a particular
frequency, and if that is near a harmonic present in the supply the result is
amplified distortion and failed capacitors. This is why modern installations use
detuned reactors in series with the capacitors, and why a harmonic survey
usually precedes the installation.

With variable-speed drives the situation changes again. A drive's rectifier draws
current in pulses, so the displacement power factor can be near unity while the
true power factor is poor because of harmonics. Correcting with capacitors does
nothing here; the fix is an active front end or a line reactor.

The measurement distinction matters: displacement power factor is $\\cos\\phi$ at
the fundamental, while true power factor includes harmonic distortion. A meter
reading one and a tariff specifying the other is a source of genuine billing
disputes.""",

    "convolution-lti-systems": """Convolution is the working model behind filters, equalisers and
channel estimators, and in practice almost all of it happens in the frequency
domain.

Designing a filter means choosing $h$ so that $H(\\omega)$ has the wanted shape.
A low-pass filter keeps the low frequencies and attenuates the rest; the
transition sharpness costs filter order, and the order costs delay and
computational work. That trade — sharpness versus latency — is the central
decision in audio, radio and control filtering alike.

Direct convolution costs $O(NM)$ for an input of length $N$ and a filter of
length $M$, which becomes expensive for long filters. Overlap-add with the FFT
reduces this to roughly $O(N \\log M)$ and is what real implementations use.

In communications, the received signal is the transmitted one convolved with the
channel, so recovering the data means estimating the channel's impulse response
and inverting it — equalisation. A known training sequence is sent, the response
is measured, and the equaliser is built from it. This is why a modem takes a
moment to sync.

The limit on all of it is the LTI assumption. A power amplifier driven into
compression, a loud cone at high excursion, or a wireless channel that changes
faster than the symbol rate all break linearity or time invariance, and no
amount of convolution modelling will fix that. Recognising when the assumption
fails is the actual engineering judgement.""",

    "semiconductors-pn-junctions": """The pn junction is the building block of nearly every active device,
and its limits set the limits of the systems built from it.

The exponential current-voltage relation is why a diode has a "turn-on" voltage
rather than a gradual onset, and why that voltage is temperature dependent —
roughly 2 mV per kelvin for silicon. That drift is a nuisance in precision
circuits and a feature in temperature sensors, which are often just a
transistor junction measured carefully.

Temperature is the governing constraint everywhere. Reverse leakage roughly
doubles every 10 K, and the maximum junction temperature is typically 150 °C for
silicon. Exceeding it does not fail the device immediately; it degrades it over
time, which is why thermal design is a reliability question rather than a
performance one. This is the real reason power electronics are built around heat
sinks and thermal interface materials.

Breakdown is used deliberately in Zener diodes for voltage reference and
clamping, and destructively avoided elsewhere. The distinction is doping: a
heavily doped junction breaks down by tunnelling at a well-defined low voltage
and recovers; a lightly doped one avalanches at a high voltage and may be
damaged by the energy dissipated.

Photovoltaics and LEDs are the same junction run in reverse. A solar cell uses
light-generated carriers separated by the built-in field; an LED injects
carriers that recombine and emit. Both are limited by the same physics that
governs the diode, which is why cell efficiency and LED wall-plug efficiency are
both far below the thermodynamic limits — the gap is recombination and
resistive loss.""",

    "stress-strain-hookes-law": """Elastic analysis is the first stage of every structural calculation,
and the code requirements around it are where the real work is.

Design codes do not use the yield stress directly; they divide by a partial
safety factor to get a design strength, and separately factor the loads upward.
The result is that a structure is designed to remain elastic under factored
loads, with a defined margin before yield. The factors differ by material and by
consequence of failure, which is why a hospital and a shed are not designed to
the same numbers.

Deflection usually governs before strength. A floor joist may carry the load
comfortably but sag enough to crack finishes or alarm occupants, so serviceability
limits — span over a few hundred — often decide the member size rather than
stress. Checking strength alone is a common and visible mistake.

Fatigue is what the elastic analysis does not cover. A stress well below yield,
repeated enough times, will still cause failure, because cracks grow from
microscopic defects. This is why aircraft and bridges are designed against an
S-N curve and inspected on a schedule rather than calculated once. The stress
range, not the peak, is the governing quantity.

Material variability is handled statistically. Steel is tightly controlled, so
the partial factor is modest; concrete is produced on site and varies
considerably, so its factor is larger and it is tested by cubes or cylinders at
7 and 28 days. Assuming a nominal strength without checking the test results is
how real failures happen.""",

    "fluid-statics-manometry": """Hydrostatic pressure governs dam design, foundation excavation and
anything submerged, and getting the reference right is where mistakes happen.

Dams are the clearest application. Pressure grows linearly with depth, so the
resultant force acts at one third of the height from the base, not at the
midpoint. That overturning moment is what the dam's weight and shape must resist,
which is why gravity dams are triangular in section. Uplift pressure under the
base reduces the effective weight and is a leading cause of dam failure, so
drainage galleries are designed in deliberately.

In geotechnical work the water table is the dominant variable. Raising it
reduces effective stress and therefore bearing capacity, while seepage gradients
can liquefy soil entirely. Excavations that fail usually do so through water
rather than through the soil's strength being exceeded, which is why dewatering
design is central rather than incidental.

The gauge-versus-absolute distinction is a recurring error with real
consequences. Thermodynamic relations — the ideal gas law, steam tables,
compressible flow — all require absolute pressure. Using a gauge reading there
gives an answer that is wrong by about 101 kPa, and at low pressures that is a
large relative error.

In instrumentation, differential pressure transmitters are the workhorse for
level and flow measurement precisely because only the difference matters. The
installation detail that causes trouble is the impulse lines: trapped gas in a
liquid line or condensate in a gas line shifts the zero and produces a plausible
but wrong reading.""",

    "first-law-energy-balance": """Energy balances are the basis of every thermal system's efficiency,
and the accounting conventions are where errors creep in.

Heat exchangers are the most common calculation: an energy balance across each
stream gives $\\dot{m} c_p \\Delta T$ on each side, and equating them with the
log-mean temperature difference sizes the unit. Fouling reduces the coefficient
over time, so the design includes a fouling factor — the margin that decides how
long the unit performs before cleaning.

The sign convention is a genuine source of error. Some texts write
$dU = Q + W$ with $W$ as work done *on* the system, others $dU = Q - W$ with
$W$ done *by* it. Both are correct; mixing them gives an answer wrong by twice
the work term. Reading the convention before using a formula is not pedantry.

Efficiency definitions differ by device and are frequently confused. A heat
engine's thermal efficiency is $W/Q_{in}$ and is bounded by Carnot. A heat
pump's coefficient of performance is $Q_{out}/W$ and can exceed one — which
looks like a violation until it is clear that a COP is not an efficiency. A
boiler efficiency above 100% on a lower heating value basis is similarly a
convention, not a miracle.

Exergy analysis is what engineers reach for when efficiency alone is misleading.
It accounts for the quality of energy, not just the quantity, so it identifies
where useful work is actually destroyed — usually in combustion and in
heat transfer across a large temperature difference. It is standard in power
generation and increasingly in process design.""",

    "equilibrium-of-forces-free-body-diagrams": """Free-body diagrams are not an academic exercise; they are the
starting point of every structural calculation, and software does not remove the
need.

Finite element analysis produces equilibrium-satisfying results whether or not
the model is right, so the diagram remains the check. A reaction that does not
equal the applied load, or a moment at a pinned support, means the boundary
conditions are wrong — and the software will happily report a detailed stress
field regardless. Hand-checking the global equilibrium of an FEA result is
standard practice for exactly this reason.

Statically indeterminate structures are the norm rather than the exception.
Continuous beams, portal frames and moment-resisting connections all have more
unknowns than equilibrium equations, so their internal forces depend on relative
stiffness. That has a real consequence: a stiffer member attracts more load, so
changing a section size changes the force distribution, which is why iteration
is normal in structural design.

The assumption of rigidity is where models most often go wrong. Real connections
are semi-rigid, foundations settle, and temperature changes induce forces in
redundant structures. A pinned connection that is actually partly fixed develops
moments the design did not allow for — a classic cause of unexpected cracking.

The discipline that prevents most errors is unchanged: isolate the body, include
every contact and the self-weight, and check that the number of unknowns matches
the number of available equations before solving.""",

    "effective-stress-bearing-capacity": """Effective stress is the foundation of geotechnical design, and water
control is where most failures actually originate.

Bearing capacity is computed from effective stress and the shear strength
parameters $c'$ and $\\phi'$. The Terzaghi equation gives the ultimate capacity,
which is then divided by a factor of safety — commonly 3 for foundations. Using
total stress here overestimates capacity substantially, because it counts pore
pressure as though the soil skeleton carried it.

Consolidation is the slow consequence of the same principle. Loading saturated
clay raises the pore pressure immediately, and the load transfers to the soil
skeleton only as the water drains. Settlement therefore continues for years,
which is why buildings on clay are monitored after completion and why the
leaning of some structures is a drainage problem rather than a structural one.

Excavation failures are usually water failures. Seepage into a dig raises the
pore pressure and reduces effective stress; past the critical gradient the soil
loses strength entirely and the base heaves. Sheet piles, wellpoints and
grout curtains are all ways of controlling this, and the design is checked on the
gradient rather than on the wall's strength.

Liquefaction is the extreme case. Cyclic loading from an earthquake raises pore
pressure faster than it can drain, effective stress approaches zero, and the
ground behaves as a liquid. This is why seismic design includes a liquefaction
assessment based on soil type, density and water-table depth — it is the
mechanism behind a large proportion of earthquake damage to otherwise sound
structures.""",

    "per-unit-system-fault-analysis": """Fault studies are a regulatory requirement, not an academic
exercise, and their output sets the specification of real equipment.

Protection settings come directly from the fault current. A circuit breaker must
interrupt the maximum prospective fault current at its location, and a relay
must operate fast enough to protect the cable downstream. Both ratings are
chosen from the study, so an error propagates into hardware that cannot be
changed cheaply later.

The calculations use subtransient reactance for the first few cycles — the
highest current, which decides breaker interrupting capacity — and transient or
synchronous reactance for later times, when the current has decayed. Using the
wrong one gives a rating that is either unsafe or unnecessarily expensive.

The base conversion is where studies go wrong most often. Equipment nameplates
give impedance on the equipment's own rating, and every contribution must be
converted to one common base before they can be added. Missing this produces a
fault current wrong by the ratio of the ratings, and it is not obvious in the
output.

Asymmetrical faults are more common than symmetrical ones, and need all three
sequence networks. A single line-to-ground fault is usually the most frequent,
while a three-phase fault is usually the largest. Both are calculated, and they
govern different equipment ratings.

Arc flash assessment has become a separate requirement. It converts the same
fault current into incident energy at a working distance, which determines the
personal protective equipment category and the warning labels on the panel — a
safety obligation with legal force in many jurisdictions.""",

    "material-energy-balances": """Material and energy balances are how a process is designed, and how
a plant's performance is audited once it is running.

In design, the balance closes around every unit operation and determines
stream flows, which then size pumps, heat exchangers, columns and vessels. The
recycle stream is the part that makes it iterative: the output of a separator
feeds back to the reactor, so the flows cannot be solved in one pass and the
calculation converges by iteration. Getting the tear stream right is the
practical skill.

In operation, the balance becomes a diagnostic. If the measured inputs and
outputs do not close, something is unaccounted for — a leak, an unmeasured
stream, or an instrument drifting. A closing balance is the basis of the
efficiency figures that decide whether a plant is performing, so the
measurement quality matters as much as the arithmetic.

The convention that causes the most trouble is the enthalpy reference state.
Enthalpy is only defined relative to a reference, and every stream must use the
same one. Mixing a steam-table basis with a heat-of-formation basis produces a
balance that is off by a large constant and shows no obvious symptom — the
numbers look reasonable and the duty calculation is wrong.

The energy side increasingly drives decisions rather than following them. Heat
integration — pinching the hot and cold streams so one's waste heats the other —
can cut utility consumption substantially, and it is found by plotting the
composite curves rather than by optimising exchangers individually. That
analysis starts from the same balances.""",

    "concrete-mix-design-workability": """Mix design in practice is dominated by admixtures and by
variability, which is where the textbook treatment stops.

Superplasticisers are the key tool. They disperse the cement particles so the
mix flows at a much lower water content, which is what makes high-strength
concrete possible at all — strength is governed by the water-cement ratio, and
without an admixture workability would force too much water. Self-compacting
concrete, which flows through congested reinforcement without vibration, is
essentially a superplasticiser plus a viscosity modifier.

Supplementary cementitious materials replace part of the cement. Fly ash and
slag reduce cost and the carbon footprint and usually improve long-term strength
and durability, but they slow early strength gain. That trade matters on a
programme: a slab reaching stripping strength a day later changes the schedule,
so the decision is commercial as much as technical.

The site realities cause most failures. Adding water to improve workability is
the most common, and it silently reduces strength. Aggregate moisture varies
with weather, so the batch water must be adjusted or the actual ratio drifts.
Curing is routinely cut short, and concrete that dries early never reaches its
design strength however good the mix was.

Quality control is statistical, not deterministic. Cubes or cylinders are tested
at 7 and 28 days, and the characteristic strength is the value below which only
5% of results fall. A plant with high variability must therefore target a much
higher mean strength to meet the same specification — which is why consistency of
production is worth as much as the mix itself.""",

    "boolean-algebra-karnaugh-maps": """Karnaugh maps are how a human minimises a small logic function, and
automated tools took over everything larger.

The map is practical up to about four or five variables. Beyond that it stops
being something a person can see, and synthesis tools — Espresso, and the logic
minimisation inside every FPGA toolchain — handle functions with thousands of
terms. So the skill matters for understanding what the tool does and for small
glue logic, not for designing a processor.

What still matters in real design is hazard avoidance, which the map makes
visible. Two adjacent product terms that differ in one variable can produce a
brief glitch as the signal propagates, because the paths have different delays.
Adding a redundant term that covers the overlap removes the hazard. In
combinational logic feeding a clock, such a glitch can be latched and become a
real fault — which is why the extra term is sometimes worth the gate.

In FPGAs the picture changes again. Logic is mapped onto lookup tables of four
or six inputs, so minimisation in the classical sense matters less than how the
function packs into those tables. The synthesis tool optimises for table count
and routing, which is not the same objective as gate count.

The practical warnings: don't hand-minimise a function you are going to describe
in HDL — write the behaviour and let the tool work; do use the map when
debugging why a combinational output glitches; and remember that Gray-code
ordering and edge wraparound are what make the map work, since binary ordering
would break the adjacency the whole method depends on.""",
})

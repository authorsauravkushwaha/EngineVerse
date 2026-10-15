"""Book-depth C modules: memory, pointers, algorithms and interview mastery.

C is where abstractions end: every list is a malloc, every string a buffer
with a length you track, every "reference" a pointer you can print. This
book teaches algorithms the C way — array decay, manual stacks, linked
structures from malloc, qsort/bsearch, hash tables from scratch, trees,
graphs, DP and bit tricks — plus a method module for systems-flavoured
interviews. Compile everything with -Wall -Wextra; run tests under
AddressSanitizer.
"""

from __future__ import annotations

BOOK_MODULES: dict[str, list[tuple]] = {
    "c": [
        (
            "c-complexity-big-o",
            "Big-O in C: counting work and bytes",
            "Growth rates, cache reality, and why allocation counts as cost.",
            """**Why this matters.** C gives you the machine with no padding,
so complexity analysis here is physical: an `O(n²)` scan thrashes cache,
a malloc per element fragments the heap, a `strlen` in a loop condition
re-scans every iteration (the classic quadratic nobody sees). Learn to
count both steps and bytes — C interviews grade both.

**Growth first.** `O(1)` indexing, `O(log n)` halving, `O(n)` scans,
`O(n log n)` qsort, `O(n²)` pairs. Analyse loops, then price the calls
inside: `strlen` is `O(n)` (call once, store it), `strcat` in a loop is
quadratic (track the end pointer), `memmove` of k bytes is `O(k)`,
`qsort` averages `O(n log n)`. State space too: auxiliary arrays are
`O(n)`, in-place with a few indices is `O(1)`, recursion depth d is
`O(d)` stack — and C stacks are small (8MB typical; deep recursion
segfaults where Java throws).

**Memory is the second complexity.** Every malloc has metadata and
fragmentation cost; per-node malloc for a million nodes is slow and
wasteful versus a single arena/pool. Realloc doubling amortises growth
like C++ vectors — implement it once to believe it. `sizeof` is your
friend: `n * sizeof *p` (not `sizeof(int)` — types change, the
dereference does not). Count peak live bytes, not just big-O.

**Cache: the hidden constant.** Sequential array access is ~10x faster
than pointer-chasing a linked list at scale — same Big-O, different
universe. Interviews rarely demand cache analysis, but "arrays beat
lists for scans" said once, correctly, marks you as someone who has
measured.

**Common mistakes.** `strlen` in loop conditions; `strcat` chains;
recursion depth on long inputs; claiming `O(1)` while mallocing per
call; ignoring `const` (it documents and enables optimisation);
measuring -O0 and concluding C is slow (always -O2 for timings).

**Interview angle.** Open with time and peak space, naming allocations:
"O(n) time, O(1) besides the output — no mallocs in the loop." That
sentence is the C interview in miniature.""",
            """#include <stdio.h>
#include <string.h>
#include <time.h>

/* O(n^2): strlen re-scans on every iteration. */
static int slow_count(const char *s, char want) {
    int count = 0;
    for (size_t i = 0; i < strlen(s); i++)
        if (s[i] == want) count++;
    return count;
}

/* O(n): one scan, length hoisted. */
static int fast_count(const char *s, char want) {
    int count = 0;
    size_t n = strlen(s);
    for (size_t i = 0; i < n; i++)
        if (s[i] == want) count++;
    return count;
}

int main(void) {
    static char buf[200000];
    memset(buf, 'a', sizeof buf - 1);
    for (int trial = 0; trial < 2; trial++) {
        clock_t start = clock();
        int c = trial ? fast_count(buf, 'a') : slow_count(buf, 'a');
        double ms = (clock() - start) * 1000.0 / CLOCKS_PER_SEC;
        printf("%s count=%d %.1f ms\\n", trial ? "fast" : "slow", c, ms);
    }
    return 0;
}""",
            """Compile with -O2 and confirm slow/fast differ by orders of
magnitude. Then solve the judged problem `binary-search` (in the judge)
and state its time and stack space.
Practice: /practice/problems/binary-search""",
        ),
        (
            "c-strings-deep",
            "Strings: buffers, lengths and string.h done right",
            "NUL termination, bounded copies, and two-pointer text patterns.",
            """**Why this matters.** C strings are a convention — bytes ending
in `'\\0'` — with no length attached. Every overflow, truncation and
read-past-end in history lives here. Master bounded functions, explicit
lengths and in-place two-pointer patterns, and you master the most
dangerous corner of the language.

**The rules.** A string of n chars needs n+1 bytes. `strlen` counts
before the NUL (`O(n)` — hoist it). `strcpy/strcat/sprintf` are
unbounded: prefer `snprintf(dst, sizeof dst, ...)`, `strncpy` with
manual NUL (it does not always terminate — set `dst[size-1] = 0`
yourself), `strncat`, `memcpy/memmove` with explicit lengths.
`strcmp/strncmp` compare; `strchr/strstr` search; `strtok` mutates and
keeps static state (not reentrant — `strtok_r` or hand-rolled parsing).
Read with `fgets` (bounded) or `getline` (allocates), never `gets`
(removed from the language for cause).

**Lengths travel with buffers.** Professional C passes `(char *buf,
size_t cap)` everywhere and returns status, not strings. `snprintf`'s
return (would-have-written length) detects truncation: `if ((size_t)rc
>= cap) truncated`. This discipline — length as data — prevents the
entire overflow class.

**Text patterns.** Palindrome: indices from both ends, skipping
non-alnum via `isalnum`/`tolower` from `<ctype.h>` (pass `unsigned
char` — negative char values are UB in ctype). Anagram over `a-z`:
`int count[26]`. In-place reverse/rotate with swaps. Parsing: walk with
a pointer, `strtol` with endptr checks (never `atoi` — no errors).

**Common mistakes.** Forgetting +1 for NUL; `strncpy` without manual
termination; `sizeof(ptr)` instead of buffer size after decay; ctype
with plain char; `strcat` loops (quadratic); comparing with `==`
(pointer comparison — use strcmp).

**Interview angle.** Every string solution should name its bounds:
"output needs n+1; I snprintf into cap." Then the algorithm. Safety
first, pointers second — that order is the senior signal.""",
            """#include <ctype.h>
#include <stdio.h>
#include <string.h>

static int is_palindrome(const char *s) {
    size_t left = 0, right = strlen(s);
    if (right == 0) return 1;
    right--;
    while (left < right) {
        unsigned char a = (unsigned char)s[left];
        unsigned char b = (unsigned char)s[right];
        if (!isalnum(a)) { left++; continue; }
        if (!isalnum(b)) { right--; continue; }
        if (tolower(a) != tolower(b)) return 0;
        left++; right--;
    }
    return 1;
}

int main(void) {
    char line[128];
    /* Bounded read + bounded copy demo. */
    snprintf(line, sizeof line, "%s", "A man, a plan, a canal: Panama");
    printf("%d\\n", is_palindrome(line));           /* 1 */
    printf("%d\\n", is_palindrome("race a car"));   /* 0 */
    return 0;
}""",
            """Write `reverse_words(char *s)` reversing word order in place
(reverse whole, then each word). Then solve the judged problem
`valid-palindrome`. Practice: /practice/problems/valid-palindrome""",
        ),
        (
            "c-arrays-deep",
            "Arrays: decay, sizeof and in-place mastery",
            "Why arrays are not pointers, and the read/write pointer technique.",
            """**Why this matters.** Arrays in C are contiguous memory with a
compile-time length that evaporates the moment you pass them to a
function ("decay" to pointer). Every in-place algorithm — dedup,
partition, rotate, merge — depends on understanding exactly what an
array parameter is and is not.

**Decay and sizeof.** `int a[10]` in the defining scope: `sizeof a` is
`10 * sizeof(int)`. Passed to `f(int *p)`, it is a pointer: `sizeof p`
is 8. Consequence: always pass the length (`f(a, n)`), and compute
counts at the definition site (`sizeof a / sizeof a[0]`). `int a[n]`
(VLA) exists in C99 (optional in C11+) — fine for small scratch, never
for untrusted n (stack overflow). `static int a[N]` for fixed tables.

**In-place technique.** Read/write pointers with the invariant "before
write: final". Remove-duplicates-sorted, move-zeroes, remove-element:
one pass, `O(1)` space. Partition (Lomuto/Hoare) underlies quicksort
and quickselect. Rotation by reversal. Merge-two-sorted from the end
when the buffer has tail space (avoids overwrite). Two pointers inward
for pair sums on sorted data. State the invariant aloud — it is the
proof and the grade.

**Multidimensional.** `int m[R][C]` is contiguous row-major; `m[i][j]`
is `*(m + i*C + j)`. Pass as `f(size_t r, size_t c, int m[r][c])` (C99
VLA parameters) or flatten with explicit indexing. `int **` is NOT a 2D
array (scattered rows) — know the difference cold; interviews probe it.

**Common mistakes.** sizeof after decay; off-by-one on last valid index
(n-1, not n); `a[i]` with signed/unsigned mixups (use size_t, compare
carefully); returning stack arrays (dangling — malloc or caller buffer);
`memcpy` on overlap (use memmove).

**Interview angle.** Signature first: `int dedup(int *a, size_t n)` with
contract "returns new length; first k valid". Then invariant, then code.
C array problems are graded on contracts and bounds, not cleverness.""",
            """#include <stdio.h>

/* Invariant: a[0..write) holds kept items. Returns new length. */
static size_t remove_duplicates(int *a, size_t n) {
    if (n == 0) return 0;
    size_t write = 1;
    for (size_t read = 1; read < n; read++) {
        if (a[read] != a[read - 1]) a[write++] = a[read];
    }
    return write;
}

static void reverse(int *a, size_t lo, size_t hi) {
    while (lo < hi) {
        int t = a[lo]; a[lo++] = a[hi]; a[hi--] = t;
    }
}

static void rotate_right(int *a, size_t n, size_t k) {
    if (n == 0) return;
    k %= n;
    reverse(a, 0, n - 1);
    reverse(a, 0, k - 1);
    reverse(a, k, n - 1);
}

int main(void) {
    int a[] = {0, 0, 1, 1, 1, 2, 3, 3};
    size_t n = sizeof a / sizeof a[0];
    size_t k = remove_duplicates(a, n);
    printf("len=%zu:", k);
    for (size_t i = 0; i < k; i++) printf(" %d", a[i]);
    printf("\\n");
    int b[] = {1, 2, 3, 4, 5};
    rotate_right(b, 5, 2);
    for (size_t i = 0; i < 5; i++) printf("%d ", b[i]); /* 4 5 1 2 3 */
    printf("\\n");
    return 0;
}""",
            """Implement Lomuto partition and quickselect for kth smallest
(average O(n)). Then solve the judged problem `move-zeroes` in place.
Practice: /practice/problems/move-zeroes""",
        ),
        (
            "c-recursion-stack",
            "Recursion and the call stack: frames you can picture",
            "Base cases, stack frames, and why depth is a budget.",
            """**Why this matters.** In C, recursion is not abstract — each
call pushes a frame (return address, saved registers, locals) onto a
small stack. Seeing recursion as stack discipline explains base cases,
depth limits, tail calls and why iteration often wins. Trees, DFS and
divide-and-conquer all live here.

**Frames and progress.** A call allocates a frame; return frees it.
Depth d with frame size f uses ~d·f bytes; default stacks (~8MB) hold
roughly 10⁵–10⁶ small frames — deep linear recursion (linked-list
length via recursion on 10⁶ nodes) segfaults. Every recursion needs:
base case(s) that return without recursing, and progress shrinking
toward them on every path. No progress = stack overflow, the C name for
infinite recursion.

**Where recursion fits.** Tree walks (depth = height; fine balanced),
divide-and-conquer (depth log n; mergesort/quicksort), backtracking
(depth = choices; N-Queens with an explicit board), DFS on small graphs.
Where it does not: long linear chains (iterate), hot loops (call
overhead + no cache benefit), untrusted depth (attacker-controlled
nesting → crash; cap depth explicitly).

**Tail calls and optimization.** A call in tail position *may* be
compiled to a jump (-O2, simple shapes) — but C does not guarantee TCO,
so never rely on it for correctness. Write iterative for depth you
cannot bound; keep recursion for naturally shallow structure (log n,
small trees).

**Memoization in C.** Arrays with sentinel init (`-1` = uncomputed),
or hash tables for sparse states. Fibonacci: naive `O(φⁿ)` calls →
`O(n)` with memo. State the table size as space. `static` memo inside
functions persists across calls (document it; not thread-safe).

**Common mistakes.** Missing base case; progress on only some paths;
stack-allocated giant locals per frame (huge frames = shallow limit);
recursing on untrusted depth; forgetting `return` on the recursive
path (garbage return, warning you ignored — use -Wall).

**Interview angle.** State depth and frame cost: "depth is height h,
O(h) stack; O(n) worst skewed." Offer the explicit-stack iterative
version. In C, stack accounting is systems literacy.""",
            """#include <stdio.h>

static long fib_memo(int n, long *memo) {
    if (n < 2) return n;              /* base cases */
    if (memo[n] != -1) return memo[n];
    return memo[n] = fib_memo(n - 1, memo) + fib_memo(n - 2, memo);
}

/* Iterative: O(1) space, no depth risk. */
static long fib_iter(int n) {
    if (n < 2) return n;
    long a = 0, b = 1;
    for (int i = 2; i <= n; i++) {
        long c = a + b;
        a = b; b = c;
    }
    return b;
}

int main(void) {
    long memo[93];
    for (int i = 0; i < 93; i++) memo[i] = -1;
    printf("%ld %ld\\n", fib_memo(90, memo), fib_iter(90));
    return 0;
}""",
            """Write factorial recursively and iteratively; disassemble both
with -O2 (objdump -d) and find the loop vs call. Then solve the judged
problem `climb-stairs`. Practice: /practice/problems/climb-stairs""",
        ),
        (
            "c-sorting-searching",
            "qsort, bsearch and binary search by hand",
            "Comparators, overflow-safe midpoints, and search-on-the-answer.",
            """**Why this matters.** C's standard sorting is one function —
`qsort` — with a comparator you write, and searching is `bsearch` or
your own loop. Interviews test whether you can wield both: order data
to unlock two pointers/merging, then binary search for boundaries.
Comparator bugs and midpoint overflow are the classic C traps.

**qsort.** `qsort(base, n, sizeof *base, cmp)` with `int cmp(const void
*a, const void *b)`. Cast inside: `int x = *(const int *)a;` then
`return (x > y) - (x < y);` — never `return x - y` (overflow). Average
`O(n log n)`, worst `O(n²)` (glibc uses mergesort fallback for large —
know your libc). Not stable. For structs, compare field by field. `qsort_r`
(GNU/BSD, differing signatures — portability wart) passes context.

**bsearch and hand-rolled.** `bsearch(&key, base, n, size, cmp)` needs
sorted data and the same comparator — returns pointer or NULL. But most
interview variants (first/last occurrence, rotated, sqrt, "smallest
feasible") need custom loops: invariant "answer in [lo, hi] if any",
`mid = lo + (hi - lo) / 2` (overflow-safe — `(lo+hi)/2` overflows near
INT_MAX, the famous bug), strict shrinking, unsigned care (`hi = mid -
1` underflows at 0 with size_t — use signed or half-open ranges).

**Search on the answer.** "Minimum x with feasible(x)" where feasibility
is monotone: koko bananas, ship capacity, split-array-largest-sum.
Binary search the value range, greedy-check each mid. Recognising
monotonicity is the whole trick — state it explicitly.

**Common mistakes.** Comparator overflow; comparator inconsistency
(must be strict weak ordering — qsort misbehaves otherwise); bsearch on
unsorted; size_t underflow in `hi = mid - 1`; forgetting `sizeof *base`;
assuming stability.

**Interview angle.** Write the comparator carefully, narrating overflow
safety. For binary search, state the invariant and the termination
argument. C interviewers watch integer discipline like hawks.""",
            """#include <stdio.h>
#include <stdlib.h>

static int cmp_int(const void *a, const void *b) {
    int x = *(const int *)a, y = *(const int *)b;
    return (x > y) - (x < y);   /* overflow-safe three-way */
}

/* First index with a[i] >= target, or -1. Answer in [lo, hi] if any. */
static long lower_bound(const int *a, long n, int target) {
    long lo = 0, hi = n - 1, ans = -1;
    while (lo <= hi) {
        long mid = lo + (hi - lo) / 2;
        if (a[mid] >= target) { ans = mid; hi = mid - 1; }
        else lo = mid + 1;
    }
    return ans;
}

int main(void) {
    int a[] = {5, 2, 8, 2, 1};
    qsort(a, 5, sizeof *a, cmp_int);
    for (int i = 0; i < 5; i++) printf("%d ", a[i]); /* 1 2 2 5 8 */
    printf("\\nlower_bound 2 -> %ld\\n", lower_bound(a, 5, 2)); /* 1 */
    int key = 8;
    int *found = bsearch(&key, a, 5, sizeof *a, cmp_int);
    printf("bsearch 8 -> %s\\n", found ? "yes" : "no");
    return 0;
}""",
            """Implement integer sqrt via binary search (floor, no libm).
Then solve the judged problem `search-rotated` (rotated sorted array).
Practice: /practice/problems/search-rotated""",
        ),
        (
            "c-linked-lists",
            "Linked lists from malloc: nodes, ownership, cycles",
            "Build, rewire and free with dummy heads and fast/slow pointers.",
            """**Why this matters.** Linked lists in C are manual: every node
a malloc, every removal a free, every mistake a leak or use-after-free.
That pain teaches ownership — who allocates, who frees, who owns the
`.next` — the core systems skill. Interviews test rewiring discipline
plus leak-free code (run under ASan/Valgrind to prove it).

**Build and free.** `Node *n = malloc(sizeof *n); if (!n) die();`
(check every malloc). Insert after p: `n->next = p->next; p->next = n;`
(new node first). Free whole list iteratively (recursion depth = length
→ stack risk). Ownership rule: the list owns its nodes; functions either
borrow (print, find) or take/return ownership (push returns new head or
takes `Node **head`). Document which.

**The three tricks.** *Dummy/sentinel* (`Node dummy = {0, head}`) kills
head-change special cases; return `dummy.next`. *Fast/slow*: meet iff
cycle (`==` on pointers); slow at middle when fast ends. *Reversal*:
`prev/cur/nxt`, `O(1)` space. Merge-two-sorted with dummy tail reusing
nodes. Partition around x with two dummy chains joined.

**Doubly-linked and intrusive.** Prev pointers enable `O(1)` delete
given the node. Real systems use intrusive lists (node embedded in the
struct, `container_of`) — mention awareness; interviews rarely demand
it. For LRU, hash + doubly-linked is the expected design (hash in C:
see next module).

**Common mistakes.** Lost `.next` (save first); use-after-free (free
then touch); double free; leaking on early return (one cleanup path);
cyclic test lists leaking by design (break cycle first); `free` without
NULL-ing shared copies (dangling).

**Interview angle.** Narrate ownership: "caller owns the returned list;
must free." Code with NULL guards, check mallocs, and offer the ASan
command. Leak-free + correct on first reasoning is the C hiring bar.""",
            """#include <stdio.h>
#include <stdlib.h>

typedef struct Node { int value; struct Node *next; } Node;

static Node *build(const int *values, size_t n) {
    Node dummy = {0, NULL}, *tail = &dummy;
    for (size_t i = 0; i < n; i++) {
        Node *node = malloc(sizeof *node);
        if (!node) { perror("malloc"); exit(1); }
        node->value = values[i];
        node->next = NULL;
        tail->next = node;
        tail = node;
    }
    return dummy.next;   /* caller owns; must free_list */
}

static Node *reverse(Node *head) {
    Node *prev = NULL;
    while (head) {                 /* before prev: reversed */
        Node *nxt = head->next;    /* 1. save */
        head->next = prev;         /* 2. redirect */
        prev = head; head = nxt;   /* 3. advance */
    }
    return prev;
}

static void free_list(Node *head) {
    while (head) {
        Node *nxt = head->next;
        free(head);
        head = nxt;
    }
}

int main(void) {
    int values[] = {1, 2, 3, 4, 5};
    Node *list = build(values, 5);
    list = reverse(list);
    for (Node *p = list; p; p = p->next) printf("%d ", p->value);
    printf("\\n");
    free_list(list);
    return 0;
}
/* gcc -Wall -Wextra -fsanitize=address,undefined list.c && ./a.out */""",
            """Write `has_cycle` (Floyd) and `middle` (fast/slow). Compile
with -fsanitize=address,undefined and confirm zero reports. Then solve
the judged problem `reverse-linked-list`.
Practice: /practice/problems/reverse-linked-list""",
        ),
        (
            "c-stacks-queues",
            "Stacks and queues in C: arrays, deques and BFS",
            "Bounded stacks, ring buffers, monotonic patterns and level order.",
            """**Why this matters.** C has no Stack class — you build stacks
from arrays (with capacity!) and queues from ring buffers or linked
lists. That construction teaches the semantics deeply: LIFO vs FIFO,
overflow as a real error, and BFS as queue discipline. Parentheses,
next-greater and level traversals are the payoffs.

**Array stack.** `int buf[CAP]; size_t top;` push checks `top < CAP`
(overflow is an error, not growth — or realloc-double for dynamic).
Pop checks `top > 0`. All `O(1)`. Valid parentheses: push openers,
match closers, empty at end. RPN evaluation: numbers push, operators
pop-apply-push. Min-stack: parallel min array or packed pairs.

**Ring-buffer queue.** `buf[CAP]; head, tail, count;` indices modulo
CAP; full when `count == CAP`, empty when 0. `O(1)` both ends, no
shifts, no per-item malloc — the embedded default. BFS uses it (or a
growable deque) for level order: seed, pop-front, push-back unvisited.

**Monotonic stack.** Indices with decreasing values answer next-greater
for all in `O(n)`: while current beats stack top, pop and record.
Temperatures, stock spans, largest rectangle (with width accounting).
Each index pushed/popped once — the complexity proof in one sentence.

**Common mistakes.** Overflow/underflow unchecked (the #1 C stack bug);
`top` as int going negative (use size_t + count checks, or signed with
care); VLAs for untrusted capacity (malloc instead); queue full vs
empty ambiguity (track count, not just head==tail); recursion where an
explicit stack was required (depth!).

**Interview angle.** State capacity and overflow policy up front:
"bounded stack, returns error on overflow" vs "growing via doubling."
Then the algorithm. Bounds-first is the C way, and interviewers notice
when it comes naturally.""",
            """#include <stdio.h>

#define CAP 1024

typedef struct { int data[CAP]; size_t top; } Stack;
typedef struct { int data[CAP]; size_t head, count; } Queue;

static int stack_push(Stack *s, int v) {
    if (s->top >= CAP) return -1;       /* overflow is an error */
    s->data[s->top++] = v;
    return 0;
}

static int is_valid(const char *s) {
    Stack st = {{0}, 0};
    for (; *s; s++) {
        if (*s == '(' || *s == '[' || *s == '{') {
            if (stack_push(&st, *s)) return 0;
        } else {
            if (st.top == 0) return 0;
            int open = st.data[--st.top];
            if ((*s == ')' && open != '(') || (*s == ']' && open != '[') ||
                (*s == '}' && open != '{')) return 0;
        }
    }
    return st.top == 0;
}

/* Ring queue push/pop, O(1), no shifts. */
static int queue_push(Queue *q, int v) {
    if (q->count >= CAP) return -1;
    q->data[(q->head + q->count) % CAP] = v;
    q->count++;
    return 0;
}

int main(void) {
    printf("%d %d\\n", is_valid("()[]{}"), is_valid("([)]")); /* 1 0 */
    Queue q = {{0}, 0, 0};
    queue_push(&q, 7);
    printf("queued=%zu\\n", q.count);
    (void)q;
    return 0;
}""",
            """Implement next-greater-element with an index stack in O(n).
Then solve the judged problem `valid-parentheses`.
Practice: /practice/problems/valid-parentheses""",
        ),
        (
            "c-hash-tables",
            "Hash tables from scratch: chaining, probing, patterns",
            "Build one to understand O(1); then use the patterns everywhere.",
            """**Why this matters.** C has no dict — you build hashing from
arrays, pointers and a hash function. Doing so once teaches what
`O(1) average` really means (good distribution + load control), and the
patterns (complement, frequency, seen) solve dozens of interview
problems. Even when interviews allow "assume a hash map", having built
one shows depth.

**Design.** Array of buckets, size power of two (mask instead of modulo:
`h & (cap - 1)`). Hash strings with FNV-1a or djb2 (short, good
avalanche); hash ints with splitmix/finalizer (identity hashes cluster).
Collision strategy: *chaining* (linked lists per bucket — simple, no
probe logic, malloc per entry) or *open addressing* (linear probing in
the array — cache friendly, needs tombstones for delete). Load factor >
0.7 → double and rehash. These four decisions are the whole design
space — state them in interviews.

**Minimal chaining table.** Buckets `Node **table`; put: hash, find-or-
prepend; get: hash, walk chain with `strcmp`; delete: unlink + free.
`O(1)` average when chains stay short; `O(n)` worst adversarial. Free
walks every bucket (write `table_free` carefully — leaks hide here).

**The patterns (same as everywhere).** Complement (two sum: need =
target - x in table?), frequency (count then decide), seen (visited
set for repeats/cycles). Fixed alphabets: skip hashing, use `int[26]`/
`int[128]` — faster and simpler, a beloved follow-up.

**Common mistakes.** Bad hash (identity on clustered keys); no rehash
(chains grow → O(n) silently); modulo on power-of-two with weak low
bits (mask needs good low bits — finalizer!); freeing keys you do not
own (strdup on insert, free on delete — pick a rule); `==` on strings
in chains (strcmp!).

**Interview angle.** "I'll assume a hash map — chaining, FNV, rehash at
0.7" shows you know what you are assuming. If asked to build it, the
skeleton above plus careful free is the pass. Mention worst-case
adversarial input once, then move on.""",
            """#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct Entry { char *key; int value; struct Entry *next; } Entry;
typedef struct { Entry **buckets; size_t cap; } Table;

static unsigned long hash_str(const char *s) {  /* djb2 */
    unsigned long h = 5381;
    while (*s) h = h * 33 + (unsigned char)*s++;
    return h;
}

static Table *table_new(size_t cap) {
    Table *t = malloc(sizeof *t);
    t->cap = cap;
    t->buckets = calloc(cap, sizeof *t->buckets);
    return t;
}

static void table_put(Table *t, const char *key, int value) {
    size_t i = hash_str(key) % t->cap;
    for (Entry *e = t->buckets[i]; e; e = e->next) {
        if (strcmp(e->key, key) == 0) { e->value = value; return; }
    }
    Entry *e = malloc(sizeof *e);
    e->key = strdup(key); e->value = value;
    e->next = t->buckets[i]; t->buckets[i] = e;
}

static int table_get(Table *t, const char *key, int *out) {
    for (Entry *e = t->buckets[hash_str(key) % t->cap]; e; e = e->next) {
        if (strcmp(e->key, key) == 0) { *out = *e; return 1; }
    }
    return 0;
}

static void table_free(Table *t) {
    for (size_t i = 0; i < t->cap; i++) {
        Entry *e = t->buckets[i];
        while (e) { Entry *n = e->next; free(e->key); free(e); e = n; }
    }
    free(t->buckets); free(t);
}

int main(void) {
    Table *t = table_new(16);
    table_put(t, "two", 2); table_put(t, "seven", 7);
    int v = 0;
    printf("%d %d\\n", table_get(t, "seven", &v), v); /* 1 7 */
    printf("%d\\n", table_get(t, "missing", &v));     /* 0 */
    table_free(t);
    return 0;
}""",
            """Add rehash-on-growth (double at load 0.75) and `table_del`
with correct unlink+free. Then solve the judged problem `two-sum`
(complement pattern). Practice: /practice/problems/two-sum""",
        ),
        (
            "c-trees-heaps",
            "Trees and heaps in C: malloc'd nodes, array heaps",
            "BST order, traversals, and binary heaps in plain arrays.",
            """**Why this matters.** Trees in C are nodes you malloc and must
free (postorder — children before parents, or you leak). Heaps are
arrays with index arithmetic. Both appear in systems interviews: BSTs
for ordered data, heaps for top-k and schedulers, tries for prefixes.
Pointer + array thinking combined.

**Binary trees.** `typedef struct T { int v; struct T *l, *r; } T;`
Insert/search/delete `O(h)`. Traversals: inorder (sorted for BST),
preorder (copy/serialize), postorder (free safely, heights), level
order (queue — see stacks module). Max depth: `1 + max(l, r)`. BST
validate with (min, max) bounds threaded down (local checks are wrong).
Free: postorder, every node, NULL after (in parent). No GC — draw who
frees what.

**Heaps in arrays.** `a[0]` min; children of i at `2i+1, 2i+2`; parent
at `(i-1)/2`. Push: append + sift up. Pop: swap root/last, shrink, sift
down. `O(log n)` both; heapify `O(n)`. Top-k via size-k heap (`O(n log
k)`); kth largest; merge-k-sorted with a heap of heads. Implement once
with a `Heap { int *d; size_t n, cap; }` + doubling — then you own it.

**Tries (bonus, high value).** Array-of-26 (or map) children + end flag;
insert/search/prefix in `O(L)` key length. Autocomplete, word break
pruning, IP routing. Malloc per node is fine for interviews; pools for
production. Mention it when "prefix" appears — interviewers light up.

**Common mistakes.** Forgetting free (leak every node); use-after-free
in delete-restructure; recursion depth on skewed trees (balance or
iterate); heap index arithmetic off-by-one (0- vs 1-based — pick one,
prove parent/child); BST delete's two-child case (successor swap, then
delete successor — practice it).

**Interview angle.** State height caveat always: "O(h); O(log n) if
balanced." For heaps: "k small, so O(n log k) beats qsort." Draw the
tree, number the heap array — C interviewers trust hand-traced indices.""",
            """#include <stdio.h>
#include <stdlib.h>

typedef struct T { int v; struct T *l, *r; } T;

static T *insert(T *root, int v) {
    if (!root) {
        T *n = malloc(sizeof *n);
        n->v = v; n->l = n->r = NULL;
        return n;
    }
    if (v < root->v) root->l = insert(root->l, v);
    else if (v > root->v) root->r = insert(root->r, v);
    return root;
}

static int height(T *root) {
    if (!root) return 0;
    int l = height(root->l), r = height(root->r);
    return 1 + (l > r ? l : r);
}

static void free_tree(T *root) {   /* postorder: children first */
    if (!root) return;
    free_tree(root->l); free_tree(root->r);
    free(root);
}

/* Min-heap push onto array heap of size *n (capacity checked by caller). */
static void heap_push(int *h, size_t *n, int v) {
    size_t i = (*n)++;
    h[i] = v;
    while (i > 0) {                /* sift up */
        size_t p = (i - 1) / 2;
        if (h[p] <= h[i]) break;
        int t = h[p]; h[p] = h[i]; h[i] = t;
        i = p;
    }
}

int main(void) {
    T *root = NULL;
    int values[] = {5, 3, 7, 2, 4, 6, 8};
    for (size_t i = 0; i < 7; i++) root = insert(root, values[i]);
    printf("height=%d\\n", height(root));   /* 3 */
    free_tree(root);
    int h[16]; size_t n = 0;
    for (int i = 0; i < 7; i++) heap_push(h, &n, values[i]);
    printf("min=%d\\n", h[0]);               /* 2 */
    return 0;
}""",
            """Write `heap_pop` (sift down) and `kth_largest` via a size-k
heap. Then solve the judged problem `max-depth-binary-tree`.
Practice: /practice/problems/max-depth-binary-tree""",
        ),
        (
            "c-graphs",
            "Graphs in C: adjacency, grids, BFS and DFS",
            "Matrices vs lists, flood fill, shortest paths and union-find.",
            """**Why this matters.** Graphs in C force representation choices:
adjacency matrices (`O(V²)` space, `O(1)` edge query) vs adjacency lists
(`O(V+E)` space, neighbour iteration). Grids are implicit graphs with
zero allocation. BFS/DFS, topo sort and union-find complete the toolkit
for networks, maps and dependencies.

**Representations.** Matrix: `int adj[V][V]` or bitset — dense graphs,
Floyd-Warshall, small V. Lists: `int *nbr[V]` with counts (or linked) —
sparse graphs, `O(V+E)` traversal. Grids: the grid IS the graph;
neighbours computed `(r±1, c±1)` with bounds checks; visited via
separate `bool` array or in-place mark (mutating input needs caller
consent). Edge lists for union-find/Kruskal.

**BFS/DFS.** BFS with ring queue: shortest unweighted paths, level
order, multi-source (enqueue all sources at 0 — rotting oranges).
DFS recursive (depth risk on big grids — `rows*cols` frames worst!) or
explicit stack: connectivity, islands, cycle detect (colours
white/grey/black; grey revisit = back edge), topo order (finish-time
descending). Both `O(V+E)`; grids `O(R·C)`.

**Topo and union-find.** Kahn's: indegree array + zero-queue + peel;
processed < V ⟺ cycle. Union-find: parent/rank arrays, find with path
halving, union by rank — near `O(1)`; components, redundant edges,
Kruskal MST. Implement union-find from memory — it is 30 lines and
endlessly useful.

**Common mistakes.** DFS recursion on huge grids (stack overflow —
iterate); no visited (exponential/cycles); directed vs undirected edge
insertion; matrix for sparse graphs (memory blowup); forgetting
disconnected components (outer loop over all V); in-place grid marks
when caller needs the grid.

**Interview angle.** "Nodes are X, edges are Y; BFS because unweighted
shortest" — the modelling sentence first. Complexity `O(V+E)` with what
V and E are here. C interviewers additionally ask allocation: "visited
is one R·C bool array" — say it.""",
            """#include <stdio.h>

/* Union-find with path halving + union by rank. */
static int find(int *parent, int x) {
    while (parent[x] != x) {
        parent[x] = parent[parent[x]];
        x = parent[x];
    }
    return x;
}

static void unite(int *parent, int *rank, int a, int b) {
    a = find(parent, a); b = find(parent, b);
    if (a == b) return;
    if (rank[a] < rank[b]) parent[a] = b;
    else if (rank[a] > rank[b]) parent[b] = a;
    else { parent[b] = a; rank[a]++; }
}

static int provinces(int n, int is_conn[3][3]) {
    int parent[3], rank[3] = {0, 0, 0};
    for (int i = 0; i < n; i++) parent[i] = i;
    for (int i = 0; i < n; i++)
        for (int j = i + 1; j < n; j++)
            if (is_conn[i][j]) unite(parent, rank, i, j);
    int count = 0;
    for (int i = 0; i < n; i++) if (find(parent, i) == i) count++;
    return count;
}

int main(void) {
    int m[3][3] = {{1, 1, 0}, {1, 1, 0}, {0, 0, 1}};
    printf("provinces=%d\\n", provinces(3, m)); /* 2 */
    return 0;
}""",
            """Implement Kahn's topo sort (indegree + queue); detect cycles
by count. Then solve the judged problem `number-of-islands`.
Practice: /practice/problems/number-of-islands""",
        ),
        (
            "c-dp-bitwise",
            "DP and bit tricks: tables plus XOR thinking",
            "State/transition/base in arrays, and bits as data structures.",
            """**Why this matters.** DP in C is tables you allocate and fill —
no decorators, just loops and sentinel init. Bitwise ops are C's home
turf: flags, masks, XOR cancellation, power-of-two checks. Together
they cover optimization problems and the "clever C" questions (single
number, counting bits, missing number) that interviews love.

**DP in C.** 1D: `dp[n+1]` with `dp[0]` base, fill ascending (stairs,
robber, coin change). 2D: `dp[r+1][c+1]` row-major (unique paths, edit
distance, LCS). Subset-sum boolean tables. Space cuts: rolling rows/
variables when transitions look back fixed distance (robber → two
ints). `malloc` tables sized `(n+1)`, init sentinels (`-1`/INF), free
after. VLA for small trusted n only. State time as "states × transition
cost", space as "live table".

**Bitwise core.** `& | ^ ~ << >>`. Masks: test bit `x & (1u << k)`;
set `x |= ...`; clear `x &= ~...`; toggle `^=`. XOR cancels (`a ^ a =
0`, `a ^ 0 = a`) → single number, missing number (`xor 0..n ^ xor
array`). `x & (x-1)` clears lowest set bit → popcount loop, power-of-two
check (`x && !(x & (x-1))`). Shifts: left into sign / overshift / negative
shift are UB — use unsigned, guard widths. `uint32_t` + `<stdint.h>`
everywhere.

**Bits as structures.** Bitset membership for small universes (26
letters in one `uint32_t`); state compression in DP (TSP/bitmask);
Bloom-filter intuition (k hashes into m bits). Gray codes, Hamming
distance (`__builtin_popcount(x ^ y)`), reversals — know the builtins
(`__builtin_popcount/clz/ctz`) and their UB edges (zero input!).

**Common mistakes.** Signed shifts/overflow (UB — unsigned!); `1 << 31`
on 32-bit int (UB — `1u`/`1ul`); `~` precedence surprises (parenthesize);
DP base/init errors (empty prefix!); fill order reading garbage; int
overflow in counting (use long/unsigned long, state bounds).

**Interview angle.** For XOR solutions, prove cancellation in one line.
For DP, draw the table and point at the cells each transition reads.
"Bits first, table second" — try the `O(1)`-space bit insight before
the table; offering both orders is senior.""",
            """#include <stdio.h>
#include <stdint.h>

/* Single number: pairs cancel under XOR. O(n)/O(1). */
static int single_number(const int *a, size_t n) {
    int ans = 0;
    for (size_t i = 0; i < n; i++) ans ^= a[i];
    return ans;
}

/* Popcount via lowest-bit clearing. */
static int popcount32(uint32_t x) {
    int c = 0;
    while (x) { x &= x - 1; c++; }
    return c;
}

/* Robber, O(1) space. */
static int rob(const int *a, size_t n) {
    int prev2 = 0, prev1 = 0;
    for (size_t i = 0; i < n; i++) {
        int cur = prev1 > prev2 + a[i] ? prev1 : prev2 + a[i];
        prev2 = prev1; prev1 = cur;
    }
    return prev1;
}

int main(void) {
    int a[] = {4, 1, 2, 1, 2};
    printf("single=%d popcount=%d rob=%d\\n",
        single_number(a, 5), popcount32(0b101101u), rob((int[]){2,7,9,3,1}, 5));
    return 0;
}""",
            """Solve `missing-number` (0..n) three ways: sum formula, XOR,
binary search on sorted — compare overflow risk. Then solve the judged
problem `single-number`. Practice: /practice/problems/single-number""",
        ),
        (
            "c-interview-mastery",
            "Systems interview method: contracts, bounds, proof",
            "Clarify, brute force, bound memory, code defensively, verify with sanitizers.",
            """**Why this matters.** C interviews grade what other languages
forgive: contracts (who allocates? who frees? what are valid inputs?),
bounds (every index proven < length), and verification (warnings clean,
sanitizers silent). The five-step method adapts: each step gains a
systems question. Master it and you interview as an engineer, not a
coder.

**The five steps, C-flavoured.** (1) Clarify + contract: examples,
ranges, NULL/empty validity, ownership ("caller-provided buffer or
malloc inside?"), failure policy (return code vs sentinel). Write the
signature with `const` and sizes first. (2) Brute force with time AND
peak bytes + allocation count. (3) Optimise by pattern (hash→build or
assume-and-state; two pointers; window; stack; BFS/DFS; heap; DP;
binary search on answer) — and re-check bounds per pattern. (4) Code
defensively: NULL checks, size checks, `snprintf`, checked malloc,
`size_t` discipline, no recursion on untrusted depth. (5) Verify: trace
examples + NULL/empty/single/max by hand, then compile `-Wall -Wextra
-Werror -fsanitize=address,undefined` and run. Sanitizer-clean is the
C equivalent of "all tests pass" — say the command.

**The atlas (C triggers).** Inner search → hash (build chaining, or
`int[128]` for bytes). Sorted pairs → two pointers. Constrained
subarray → window with counts. Nested → bounded stack. Levels/shortest
→ ring-queue BFS. Connectivity/order → DFS/topo/union-find. k-extreme
→ array heap. Counting/optimum → DP table + space cut. Boundary → binary
search with overflow-safe mid. Bits → XOR/masks first.

**Behave senior.** `-Wall -Wextra -Werror` always; `const` on inputs;
`sizeof *p` not `sizeof(type)`; `restrict` where true (mention, do not
abuse); `assert` for impossible states (documents + debuggable);
valgrind/ASan/UBSan as routine, not rescue; `errno`/`perror` on syscall
failure.

**Common mistakes.** Coding before contracting (wrong ownership);
ignoring malloc failure; `int` for sizes (overflow — size_t); recursion
on attacker depth; "works on my machine" without sanitizers; silent
coding (narrate bounds!).

**Rehearsal.** 100+ problems with C implementations, every one
sanitizer-clean; reimplement vector/hash/heap/queue/union-find from
memory monthly. That discipline is the offer.""",
            """#include <stdio.h>

/* Trapping rain water, O(n)/O(1). Bounds: read-only scan, no allocation. */
static int trap(const int *h, size_t n) {
    if (h == NULL || n == 0) return 0;
    size_t left = 0, right = n - 1;
    int lmax = 0, rmax = 0, water = 0;
    while (left < right) {
        if (h[left] < h[right]) {
            if (h[left] > lmax) lmax = h[left];
            else water += lmax - h[left];
            left++;
        } else {
            if (h[right] > rmax) rmax = h[right];
            else water += rmax - h[right];
            right--;
        }
    }
    return water;
}

int main(void) {
    int h[] = {0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1};
    printf("%d\\n", trap(h, sizeof h / sizeof h[0])); /* 6 */
    return 0;
}
/* gcc -Wall -Wextra -Werror -fsanitize=address,undefined trap.c */""",
            """Solve trapping-rain-water three ways (brute O(n²), DP O(n)/O(n),
two-pointer O(n)/O(1)), all sanitizer-clean. Then solve the judged hard
problem of the same name. Practice: /practice/problems/trapping-rain-water""",
        ),
    ]
}

#: Module slug -> judged problem slug for the "code what you learned" button.
MODULE_PRACTICE: dict[str, str] = {
    "c-complexity-big-o": "binary-search",
    "c-strings-deep": "valid-palindrome",
    "c-arrays-deep": "move-zeroes",
    "c-recursion-stack": "climb-stairs",
    "c-sorting-searching": "search-rotated",
    "c-linked-lists": "reverse-linked-list",
    "c-stacks-queues": "valid-parentheses",
    "c-hash-tables": "two-sum",
    "c-trees-heaps": "max-depth-binary-tree",
    "c-graphs": "number-of-islands",
    "c-dp-bitwise": "single-number",
    "c-interview-mastery": "trapping-rain-water",
}

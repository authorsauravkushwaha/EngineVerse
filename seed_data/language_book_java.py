"""Book-depth Java modules: data structures, algorithms and interview mastery.

Mirrors the Python book's arc — complexity, strings, arrays, hashing,
recursion, sorting, stacks, linked lists, trees, heaps, graphs, DP, and a
method module — but teaches the Java way: static types, the Collections
framework, generics, and the idioms interviewers expect in Java code
(StringBuilder, ArrayList, HashMap, PriorityQueue, ArrayDeque).

Each module ends with a runnable example and one judged problem to code.
"""

from __future__ import annotations

BOOK_MODULES: dict[str, list[tuple]] = {
    "java": [
        (
            "java-complexity-big-o",
            "Big-O in Java: growth rates and collection costs",
            "Analyse loops, and memorise what each Collection operation really costs.",
            """**Why this matters.** Java interviews open with complexity before
code: "what is the time and space of your approach?" The answer decides
whether you may proceed. Big-O counts growth — `O(1)` constant, `O(log n)`
halving, `O(n)` linear, `O(n log n)` sorting, `O(n²)` pairs — and Java's
collections each publish their costs. Knowing that `ArrayList.get` is
`O(1)` while `LinkedList.get` is `O(n)` is not trivia; it is the
difference between passing and timing out.

**Analyse the loops.** Single loop over n: `O(n)`. Nested loops: `O(n²)`.
Halving (`i *= 2`, binary search): `O(log n)`. Sequential phases add —
keep the dominant term. Then price the operations inside: `ArrayList.add`
amortised `O(1)`, `add(0, x)` `O(n)`; `HashMap.get/put` `O(1)` average;
`TreeMap` `O(log n)`; `PriorityQueue` offer/poll `O(log n)`;
`Collections.sort` `O(n log n)`; `String.contains` on length-m text `O(n·m)`.
Most Java timeouts are a hidden `O(n)` inside a loop — `list.remove(0)`,
`str +=` in a loop (quadratic string building — use StringBuilder).

**Space in a GC world.** Extra lists/maps are `O(n)` space; in-place on
the input is `O(1)` (plus `O(h)`/`O(d)` recursion stack you must count —
interviewers always ask). Autoboxing (`int` ↔ `Integer`) costs objects;
in hot loops over millions of items it shows. Streams are elegant but
each intermediate op is a pass — fine, but count the passes.

**Common mistakes.** Quoting average case as worst (HashMap degrades on
adversarial hashes — mention it, then move on); forgetting sort cost
dominates (`O(n log n)` solution "with a small scan" is still `n log n`);
measuring on tiny inputs; ignoring GC/boxing in "constant space" claims
when you boxed n Integers.

**Interview angle.** Open with: "Brute force O(n²)/O(1); with a HashMap,
O(n)/O(n)." Java interviewers expect the collections named precisely —
say ArrayList, not "list"; HashMap, not "map". Precision signals fluency.""",
            """import java.util.*;

public class ComplexityDemo {
    // O(n²) time, O(1) space
    static boolean hasDuplicateBrute(int[] a) {
        for (int i = 0; i < a.length; i++)
            for (int j = i + 1; j < a.length; j++)
                if (a[i] == a[j]) return true;
        return false;
    }

    // O(n) time, O(n) space
    static boolean hasDuplicateFast(int[] a) {
        Set<Integer> seen = new HashSet<>();
        for (int x : a) {
            if (!seen.add(x)) return true;  // add returns false if present
        }
        return false;
    }

    public static void main(String[] args) {
        int[] data = new int[20000];
        for (int i = 0; i < data.length; i++) data[i] = i;
        for (String name : new String[]{"brute", "fast"}) {
            long start = System.nanoTime();
            boolean r = name.equals("brute") ? hasDuplicateBrute(data) : hasDuplicateFast(data);
            System.out.printf("%s -> %b in %.1f ms%n", name, r,
                (System.nanoTime() - start) / 1e6);
        }
    }
}""",
            """Time both methods at n = 30,000 and confirm the gap grows
superlinearly. Then solve the judged problem `binary-search` in Java
style (or Python in the judge) and state why it is O(log n).
Practice: /practice/problems/binary-search""",
        ),
        (
            "java-strings-deep",
            "Strings: immutability, StringBuilder and text patterns",
            "Why String is final, and the two-pointer/window patterns on text.",
            """**Why this matters.** `String` is immutable in Java — every
`+` in a loop allocates, making naive concatenation quadratic. The
professional rule is absolute: loop-built text goes through
`StringBuilder`. Beyond that, string problems (palindromes, anagrams,
windows) are half of all interview questions, and Java's `charAt`,
`substring` and `toCharArray` are the tools.

**Immutability and the pool.** String literals are interned — `"hi" ==
"hi"` is true for literals (same pooled object) but `new String("hi")
== "hi"` is false. Always compare content with `equals`, never `==`.
Immutability buys thread safety and hash stability (Strings are ideal
HashMap keys). `substring` copies in modern JDKs (it shared the array
until Java 7u6 — a famous memory-leak source). `split` takes a regex
(`split("\\.")` for dots — the double backslash is real).

**The patterns.** Two pointers from both ends for palindromes (`O(1)`
space). Sliding window for longest-substring problems (expand right,
jump left past the duplicate via a last-index map). Frequency arrays
`int[26]` or `int[128]` for anagrams over a fixed alphabet — faster
than a HashMap and a favourite "can you do it without hashing?"
follow-up. Normalise first: `Character.toLowerCase`,
`Character.isLetterOrDigit`.

**StringBuilder discipline.** `append` in loops, `reverse()` for
reversal, `toString()` once at the end. Capacity doubles amortised —
`O(1)` per append. `String.join("-", parts)` and `String.format` cover
the rest. In interviews, reaching for StringBuilder unprompted reads as
trained.

**Common mistakes.** `==` on Strings; `+=` in loops; `substring` index
confusion (end-exclusive); regex in `split`/`replaceAll` when
`replace` (literal) was meant; forgetting `charAt` returns char, and
`'a' + 1` is int arithmetic (cast back).

**Interview angle.** State normalisation first: "ignoring case and
non-alphanumerics." Then pointers or window. Mention StringBuilder
before the interviewer asks — it pre-empts the follow-up.""",
            """public class StringDeep {
    static boolean isPalindrome(String text) {
        int left = 0, right = text.length() - 1;
        while (left < right) {
            char a = text.charAt(left), b = text.charAt(right);
            if (!Character.isLetterOrDigit(a)) { left++; continue; }
            if (!Character.isLetterOrDigit(b)) { right--; continue; }
            if (Character.toLowerCase(a) != Character.toLowerCase(b)) return false;
            left++; right--;
        }
        return true;
    }

    static boolean isAnagram(String a, String b) {
        if (a.length() != b.length()) return false;
        int[] count = new int[26];
        for (int i = 0; i < a.length(); i++) {
            count[Character.toLowerCase(a.charAt(i)) - 'a']++;
            count[Character.toLowerCase(b.charAt(i)) - 'a']--;
        }
        for (int c : count) if (c != 0) return false;
        return true;
    }

    public static void main(String[] args) {
        System.out.println(isPalindrome("A man, a plan, a canal: Panama")); // true
        System.out.println(isAnagram("Listen", "Silent"));                  // true
        System.out.println(new StringBuilder("hello").reverse());           // olleh
    }
}""",
            """Write `lengthOfLongestSubstring` with a sliding window and a
last-index array in O(n). Then solve the judged problem
`valid-palindrome` and compare approaches with the editorial.
Practice: /practice/problems/valid-palindrome""",
        ),
        (
            "java-arrays-arraylist",
            "Arrays and ArrayList: contiguous storage and in-place skill",
            "Fixed arrays vs growing lists, and the read/write pointer technique.",
            """**Why this matters.** Arrays are the foundation every other
structure is built on, and in-place array manipulation is the most
tested basic skill: dedup sorted, move zeroes, rotate, merge. Java gives
you both raw arrays (`int[]`, fixed, fast, primitives) and `ArrayList`
(growing, objects, rich API). Interviews use both — know when each fits.

**Arrays vs ArrayList.** `int[]` holds primitives contiguously: cache
friendly, zero boxing, `Arrays.sort`/`binarySearch`/`fill`/`copyOf`
cover the basics. Length is fixed — "append" means allocate bigger and
copy (`O(n)`). `ArrayList<Integer>` grows amortised `O(1)` per add but
boxes every int; `get/set` are `O(1)`; `add(0, x)`/`remove(0)` are `O(n)`
shifts. Default: ArrayList for building, arrays for fixed-size speed and
for signatures (`int[]` in, modified in place).

**In-place technique.** The read/write pointer pair: read scans every
slot, write marks where the next kept item goes, with the invariant
"everything before write is final". Remove-duplicates-sorted,
move-zeroes, remove-element all collapse to this shape in `O(n)`/`O(1)`.
Rotation uses reversal (`reverse whole, reverse parts`) — memorise it.
Two pointers from both ends handle sorted-squares and pair sums without
extra space.

**Sorting and searching.** `Arrays.sort(int[])` is dual-pivot quicksort
(`O(n log n)` average); `Arrays.sort(Object[])` is Timsort (stable).
`Arrays.binarySearch` returns index or `-(insertion point) - 1` — decode
it correctly. `Comparator.comparing` + `thenComparing` build multi-level
orders for objects. `List.of`/`Arrays.asList` make fixed-size lists
(`asList` allows set but not add — a classic trap).

**Common mistakes.** `==` on arrays (compares references — use
`Arrays.equals`); `asList` then `add` (UnsupportedOperationException);
`remove` overload confusion (`remove(0)` removes index 0, `remove((Integer) 0)`
removes value 0); losing the invariant mid-loop; forgetting `newLength`
return conventions for in-place problems.

**Interview angle.** Ask "may I modify the input, and must it stay
sorted?" Then state the invariant before coding. In-place array code
with a stated invariant is the clearest seniority signal at this level.""",
            """import java.util.*;

public class ArraysDeep {
    // Invariant: nums[0..write) holds the kept items, in order.
    static int removeDuplicates(int[] nums) {
        if (nums.length == 0) return 0;
        int write = 1;
        for (int read = 1; read < nums.length; read++) {
            if (nums[read] != nums[read - 1]) nums[write++] = nums[read];
        }
        return write;
    }

    static int[] sortedSquares(int[] nums) {
        int n = nums.length, out[] = new int[n];
        int lo = 0, hi = n - 1;
        for (int i = n - 1; i >= 0; i--) {   // fill largest first
            if (Math.abs(nums[lo]) > Math.abs(nums[hi])) out[i] = nums[lo] * nums[lo++];
            else out[i] = nums[hi] * nums[hi--];
        }
        return out;
    }

    public static void main(String[] args) {
        int[] a = {0, 0, 1, 1, 1, 2, 3, 3};
        int n = removeDuplicates(a);
        System.out.println(n + " " + Arrays.toString(Arrays.copyOf(a, n)));
        System.out.println(Arrays.toString(sortedSquares(new int[]{-4, -1, 0, 3, 10})));
    }
}""",
            """Implement `rotate(nums, k)` in O(1) space via three reversals.
Then solve the judged problem `sorted-squares` and explain why filling
from the largest end keeps it O(n).
Practice: /practice/problems/sorted-squares""",
        ),
        (
            "java-hashmap-hashset",
            "HashMap and HashSet: hashing in Java",
            "equals/hashCode contracts, and the complement/frequency/seen patterns.",
            """**Why this matters.** HashMap is the single highest-leverage
class in Java interviews. Two Sum, anagrams, first-unique, longest
consecutive, group-by — all `O(n)` through hashing. But Java demands you
respect the contract: equal objects must hash equally, or your map
silently loses entries. This module teaches the patterns and the
contract together.

**The contract.** Override `equals` and `hashCode` together, always.
`HashMap.get` hashes the key, finds the bucket, then `equals`-scans the
chain (treeified past 8 collisions — `O(log n)` worst per bucket in
modern JDKs). Mutable keys are a landmine: mutate a key after insertion
and its bucket is wrong forever. Prefer Strings, Integers, records, or
immutable custom keys. `null` key is allowed (one, in bucket 0);
`Hashtable`/`ConcurrentHashMap` differ — know which you need.

**The three patterns.** *Complement* (Two Sum: need `target - x` already
mapped to its index — check before inserting so an element never pairs
with itself). *Frequency* (`merge(key, 1, Integer::sum)` or
`getOrDefault`; anagrams compare frequency maps). *Seen* (HashSet for
duplicates, visited states, longest-consecutive starts). `computeIfAbsent`
builds grouping maps (`Map<String, List<String>>`) in one line.

**Ordering variants.** `LinkedHashMap` preserves insertion order (LRU
caches with `accessOrder=true, removeEldestEntry`); `TreeMap` sorts by
key (`O(log n)`, needs Comparable or Comparator). Reach for them only
when order is required — plain HashMap is faster.

**Common mistakes.** Forgetting `hashCode` when overriding `equals`
(map finds nothing); mutable keys; iterating and modifying (use
`iterator.remove()` or collect-then-remove); `get` returning null
ambiguity (use `containsKey` or `getOrDefault`); autoboxing `null`
Integer to int (NullPointerException).

**Interview angle.** "HashMap buys O(n) time for O(n) space" — then the
follow-up: fixed alphabet? Use `int[26]`. Sorted input? Two pointers
save the space. Naming the cheaper alternative unprompted is what
distinguishes good from great.""",
            """import java.util.*;

public class HashDeep {
    static int[] twoSum(int[] nums, int target) {
        Map<Integer, Integer> seen = new HashMap<>();  // value -> index
        for (int i = 0; i < nums.length; i++) {
            int need = target - nums[i];
            if (seen.containsKey(need)) return new int[]{seen.get(need), i};
            seen.put(nums[i], i);
        }
        return new int[0];
    }

    static List<List<String>> groupAnagrams(String[] words) {
        Map<String, List<String>> groups = new HashMap<>();
        for (String w : words) {
            char[] chars = w.toCharArray();
            Arrays.sort(chars);
            groups.computeIfAbsent(new String(chars), k -> new ArrayList<>()).add(w);
        }
        return new ArrayList<>(groups.values());
    }

    public static void main(String[] args) {
        System.out.println(Arrays.toString(twoSum(new int[]{2, 7, 11, 15}, 9)));
        System.out.println(groupAnagrams(new String[]{"eat", "tea", "tan", "ate", "nat", "bat"}));
    }
}""",
            """Solve `contains-duplicate` three ways (brute, sort, HashSet)
and time them at n = 100,000. Then solve the judged problem `two-sum`.
Practice: /practice/problems/two-sum""",
        ),
        (
            "java-recursion",
            "Recursion in Java: base cases and memoization",
            "Self-similar problems, stack depth, and top-down DP with maps/arrays.",
            """**Why this matters.** Trees, backtracking and DP are recursion
in Java clothing. The shape is universal — base case, reduction,
progress — but Java adds its flavour: explicit memo arrays, helper
methods with accumulators, and `StackOverflowError` as the hard wall
(typically ~10k frames default; deep skewed trees need iteration).

**The template.** Public method validates and delegates to a private
helper carrying state (`helper(node, ...)`, `dfs(r, c, ...)`). Base
cases first (null node, out of bounds, target reached). Recursive step
combines smaller answers. Progress must be visible: smaller n, deeper
index, marked-visited cell. Trace `fact(3)` once, then trust the
contract ("this call returns the right answer for smaller input").

**Memoization, Java style.** `int[] memo` initialised to a sentinel
(-1 for "uncomputed" when answers are non-negative), or
`Map<State, Answer>` for complex states. Fibonacci collapses from
`O(φⁿ)` to `O(n)`; climbing stairs likewise. `HashMap` memo with a
record/encoded key handles 2D states. Always ask: "do subproblems
overlap?" — if yes, memoize; if no (mergesort halves), do not.

**Backtracking.** Choose → explore → unchoose, with a shared mutable
path (`StringBuilder`, `List`, board array) mutated and restored.
Subsets, permutations, N-Queens, word search: all the same skeleton.
Prune early (invalid prefix? stop) — pruning is where exponentials
become tractable.

**Common mistakes.** Missing base case (StackOverflowError); no
progress; forgetting to unchoose (state leaks across branches);
recomputing shared subproblems (no memo); exponential blowup accepted
silently (state the count: "2ⁿ subsets, unavoidable, but each in O(n)
to copy"); recursion for simple loops (iteration is clearer and
stack-safe).

**Interview angle.** State depth: "recursion depth is tree height —
O(log n) balanced, O(n) skewed; each frame is O(1)." Offer iterative
with ArrayDeque as the follow-up. Java interviewers particularly
reward explicit stack/space accounting.""",
            """import java.util.*;

public class RecursionDeep {
    // Top-down with memo: O(n) time, O(n) space (memo + stack).
    static long fib(int n, long[] memo) {
        if (n < 2) return n;
        if (memo[n] != -1) return memo[n];
        return memo[n] = fib(n - 1, memo) + fib(n - 2, memo);
    }

    // Backtracking skeleton: all subsets.
    static void subsets(int[] nums, int i, List<Integer> path, List<List<Integer>> out) {
        if (i == nums.length) { out.add(new ArrayList<>(path)); return; }
        path.add(nums[i]);            // choose
        subsets(nums, i + 1, path, out);
        path.remove(path.size() - 1); // unchoose
        subsets(nums, i + 1, path, out);
    }

    public static void main(String[] args) {
        long[] memo = new long[101];
        Arrays.fill(memo, -1);
        System.out.println(fib(90, memo));   // 2880067194370816120
        List<List<Integer>> out = new ArrayList<>();
        subsets(new int[]{1, 2, 3}, 0, new ArrayList<>(), out);
        System.out.println(out.size() + " subsets");  // 8
    }
}""",
            """Write climbing-stairs top-down with memo, then bottom-up with
two variables. Then solve the judged problem `climb-stairs`.
Practice: /practice/problems/climb-stairs""",
        ),
        (
            "java-sorting-searching",
            "Sorting and searching: order as a tool",
            "Comparators, binary search, and search-on-the-answer.",
            """**Why this matters.** `Arrays.sort` and `Collections.sort` are
`O(n log n)` Timsort (stable for objects); binary search is `O(log n)`.
The interview skill is seeing when order unlocks the problem: pairs and
intervals want sorting; "first/last/smallest feasible" wants binary
search; "kth" wants quickselect or a heap. Java's Comparator machinery
makes custom orders painless — learn it once, use it everywhere.

**Comparators.** `Comparator.comparing(Student::grade).thenComparing(Student::name)`,
`Comparator.comparingInt(a -> a[0])`, `.reversed()`. For arrays:
`Arrays.sort(pairs, (a, b) -> a[0] != b[0] ? a[0] - b[0] : a[1] - b[1])`
— but subtraction overflows on extremes; prefer `Integer.compare`.
Lambdas capturing effectively-final variables keep sorts readable.
`List.sort(cmp)` sorts in place; `stream().sorted()` returns new.

**Binary search.** `Arrays.binarySearch`/`Collections.binarySearch`
return index or `-(insertion point) - 1`. Hand-rolled when the predicate
is custom: maintain "answer in [lo, hi]", `mid = lo + (hi - lo) / 2`
(overflow-safe — interviewers check this), shrink strictly. Variants:
first/last occurrence (keep searching left/right after a hit), rotated
array (one half is always sorted — find it), peak, integer sqrt, and
*search on the answer* (koko bananas, ship capacity, split array:
"smallest x with feasible(x)" — binary search the range, greedy-check
each mid).

**Common mistakes.** Overflow in `(lo + hi) / 2` and in comparator
subtraction; `binarySearch` on unsorted data; misreading the negative
return; forgetting stability needs (Timsort has it, primitive quicksort
does not); sorting when a linear pass sufficed (`O(n)` max vs sort).

**Interview angle.** "Sorting costs O(n log n) — worth it here because
..." is the sentence. For binary search, write the invariant as a
comment. For search-on-answer, name the monotonic predicate explicitly:
feasibility must flip exactly once.""",
            """import java.util.*;

public class SortSearch {
    // First index with value >= target, or -1 if none.
    static int lowerBound(int[] a, int target) {
        int lo = 0, hi = a.length - 1, ans = -1;
        while (lo <= hi) {                       // answer in [lo, hi] if any
            int mid = lo + (hi - lo) / 2;
            if (a[mid] >= target) { ans = mid; hi = mid - 1; }
            else lo = mid + 1;
        }
        return ans;
    }

    public static void main(String[] args) {
        int[][] pairs = {{1, 3}, {2, 6}, {8, 10}, {15, 18}};
        Arrays.sort(pairs, Comparator.comparingInt(a -> a[0]));
        System.out.println(Arrays.deepToString(pairs));
        System.out.println(lowerBound(new int[]{1, 2, 2, 2, 5}, 2)); // 1
        System.out.println(Arrays.binarySearch(new int[]{1, 3, 5}, 4)); // -3
    }
}""",
            """Implement integer `sqrt(x)` via binary search (floor). Then
solve the judged problem `merge-intervals`: sort by start, merge once.
Practice: /practice/problems/merge-intervals""",
        ),
        (
            "java-stacks-queues",
            "Stacks, queues and priority queues",
            "ArrayDeque for LIFO/FIFO, monotonic stacks, and heaps for top-k.",
            """**Why this matters.** `ArrayDeque` is Java's_stack and queue
(`Stack` is legacy — never use it; `LinkedList` works but ArrayDeque is
faster). Parentheses, next-greater, temperatures, BFS levels, top-k —
one deque and one priority queue cover them all.

**Stacks.** `push/pop/peek` on ArrayDeque, all amortised `O(1)`.
Valid parentheses: push openers, match closers against the top, empty
at end. Monotonic stack: maintain increasing order to answer "next
greater" for every element in one `O(n)` pass — each element pushed and
popped once. Largest rectangle and daily temperatures are the same
discipline with area/day-count bookkeeping. Expression evaluation (RPN:
push numbers, apply operators) is the third classic.

**Queues and BFS.** `offer/poll/peek` (null-safe) vs `add/remove/element`
(throwing) — know both families. BFS seeds a queue with starts, polls,
enqueues unvisited neighbours; level order falls out by processing
`size()` nodes per layer. `PriorityQueue` is a min-heap (`O(log n)`
offer/poll, `O(1)` peek): top-k via a size-k heap (`O(n log k)`),
merge-k-sorted, kth largest. Max-heap via `Comparator.reverseOrder()`
or negated keys. Tuples need explicit comparators (arrays compare by
reference — always supply one).

**Common mistakes.** Using legacy `Stack`; `pop/peek` on empty deque
(NoSuchElementException — guard or use poll/peek-null forms); `PriorityQueue`
iteration order confusion (only `peek/poll` are ordered — iteration is
arbitrary); forgetting visited sets in BFS; `ArrayDeque` forbids nulls
(unlike LinkedList).

**Interview angle.** Trigger phrases: "most recent unmatched" → stack;
"in layers / shortest" → BFS queue; "k extreme" → size-k heap. State
"each element enters and leaves once" for the O(n) monotonic argument —
that sentence is the proof.""",
            """import java.util.*;

public class StacksQueues {
    static boolean isValid(String s) {
        Map<Character, Character> pairs = Map.of(')', '(', ']', '[', '}', '{');
        Deque<Character> stack = new ArrayDeque<>();
        for (char ch : s.toCharArray()) {
            if (pairs.containsKey(ch)) {
                if (stack.isEmpty() || stack.pop() != pairs.get(ch)) return false;
            } else stack.push(ch);
        }
        return stack.isEmpty();
    }

    static int[] nextGreater(int[] a) {
        int[] ans = new int[a.length];
        Arrays.fill(ans, -1);
        Deque<Integer> stack = new ArrayDeque<>();   // indices, decreasing values
        for (int i = 0; i < a.length; i++) {
            while (!stack.isEmpty() && a[i] > a[stack.peek()]) ans[stack.pop()] = a[i];
            stack.push(i);
        }
        return ans;
    }

    static int kthLargest(int[] nums, int k) {
        PriorityQueue<Integer> heap = new PriorityQueue<>();  // min-heap of size k
        for (int x : nums) {
            heap.offer(x);
            if (heap.size() > k) heap.poll();
        }
        return heap.peek();
    }

    public static void main(String[] args) {
        System.out.println(isValid("()[]{}") + " " + isValid("([)]"));
        System.out.println(Arrays.toString(nextGreater(new int[]{2, 1, 2, 4, 3})));
        System.out.println(kthLargest(new int[]{3, 2, 1, 5, 6, 4}, 2)); // 5
    }
}""",
            """Solve `daily-temperatures` with a monotonic stack. Then solve
the judged problem `valid-parentheses` and the heap problem
`kth-largest`. Practice: /practice/problems/valid-parentheses""",
        ),
        (
            "java-linked-lists",
            "Linked lists: nodes, dummy heads, fast and slow",
            "Pointer discipline with references: reverse, cycle, middle, merge.",
            """**Why this matters.** Java interviews test linked lists to see
reference discipline: rewire without losing the chain. `LinkedList` the
class exists but interviews make you build nodes (`class ListNode`) and
operate on `.next` directly. Dummy heads, fast/slow pointers and
in-place reversal are the complete toolkit.

**Nodes and wiring.** `class ListNode { int val; ListNode next; }`.
Insert after p: `n.next = p.next; p.next = n;` — new node first, or the
tail is orphaned. Delete after p: `p.next = p.next.next` (null-guarded).
Every bug is a lost reference: save `next` before redirecting. Helpers
`build(int[])` and `toList(head)` make every test one line.

**The three tricks.** *Dummy head* (`new ListNode(0, head)`) absorbs
"what if head changes?" for removal, merge, partition — return
`dummy.next`. *Fast/slow*: fast advances two, slow one — meet iff cycle
(Floyd; `==` on references, not equals); slow reaches middle when fast
finishes (second middle on even lengths — state your convention).
*Reversal*: `prev/cur/nxt`, redirect-then-advance, `O(1)` space.
Merge-two-sorted reuses nodes with a dummy tail. Reorder/partition
compose these primitives.

**Common mistakes.** Losing `next` before redirect; returning stale
head; null dereference at list end (`fast != null && fast.next != null`
guards); `==` vs `equals` confusion (nodes: identity with `==`);
recursion depth on long lists (iterative wins); forgetting dummy → off-
by-one on head removal.

**Interview angle.** Draw boxes, move arrows, narrate the invariant:
"before prev: reversed; cur: next." Slow correct beats fast lost —
interviewers watch the discipline, and Java's explicit references make
every step visible. Mention `O(1)` space explicitly.""",
            """public class LinkedDeep {
    static class ListNode {
        int val; ListNode next;
        ListNode(int v) { val = v; }
        ListNode(int v, ListNode n) { val = v; next = n; }
    }

    static ListNode reverse(ListNode head) {
        ListNode prev = null, cur = head;
        while (cur != null) {          // before prev: reversed
            ListNode nxt = cur.next;  // 1. save rest
            cur.next = prev;          // 2. redirect
            prev = cur; cur = nxt;    // 3. advance
        }
        return prev;
    }

    static boolean hasCycle(ListNode head) {
        ListNode slow = head, fast = head;
        while (fast != null && fast.next != null) {
            slow = slow.next; fast = fast.next.next;
            if (slow == fast) return true;   // identity, not equals
        }
        return false;
    }

    static ListNode middle(ListNode head) {
        ListNode slow = head, fast = head;
        while (fast != null && fast.next != null) { slow = slow.next; fast = fast.next.next; }
        return slow;
    }

    public static void main(String[] args) {
        ListNode h = new ListNode(1, new ListNode(2, new ListNode(3, new ListNode(4))));
        System.out.println(middle(h).val);            // 3 (second middle)
        ListNode r = reverse(h);
        StringBuilder sb = new StringBuilder();
        for (ListNode p = r; p != null; p = p.next) sb.append(p.val);
        System.out.println(sb);                       // 4321
        System.out.println(hasCycle(h));              // false
    }
}""",
            """Write `mergeTwoSorted(l1, l2)` reusing nodes with a dummy head.
Then solve the judged problem `middle-of-linked-list` and explain the
fast/slow invariant. Practice: /practice/problems/middle-of-linked-list""",
        ),
        (
            "java-trees-heaps",
            "Trees and heaps: traversals and priority",
            "BST order, DFS/BFS walks, and PriorityQueue for streaming extremes.",
            """**Why this matters.** Trees test recursive thinking over
branching structure; heaps test "extreme of a stream" thinking. Java
pairs them naturally: `TreeNode` classes with clean recursion, and
`PriorityQueue` with comparators for top-k, merge-k and scheduling.

**Traversals.** Preorder (node, left, right — serialize/copy), inorder
(left, node, right — sorted for BST), postorder (children first —
heights, deletion, diameter), level order (BFS queue — row by row,
right-side view, zigzag). Max depth is postorder: `1 + max(l, r)`.
Symmetry mirrors subtrees. Diameter tracks `l + r` during height
computation. BST validation threads (min, max) bounds down — the naive
"left < node < right locally" check is wrong (must hold against all
ancestors).

**BST operations.** Search/insert/delete `O(h)`: `O(log n)` balanced,
`O(n)` skewed. `TreeMap`/`TreeSet` are red-black (`O(log n)`
guaranteed) — mention them when balance matters. Kth smallest via
inorder counter (or augmented sizes); LCA via BST order (split point);
validate with long bounds (int extremes overflow comparisons).

**Heaps.** `PriorityQueue` min-heap: offer/poll `O(log n)`, peek `O(1)`.
Top-k: size-k heap, `O(n log k)`. Kth largest, top-k frequent (heap of
entries by count), merge-k-sorted (heap of list heads), task scheduler,
running median (max-heap low half + min-heap high half, rebalance).
Custom objects need comparators — arrays compare by reference, always
supply `(a, b) -> ...`.

**Common mistakes.** Null base case forgotten; depth vs level confusion;
BST validation without ancestor bounds; heap comparator overflow
(`a - b` — use `Integer.compare`); iterating a PQ expecting order (only
poll is ordered); recursion on skewed trees (iterative + stack).

**Interview angle.** Name the traversal and why before coding. For BST,
say the height caveat. For heaps, say "k << n so O(n log k) beats
sorting." Draw the tree — always.""",
            """import java.util.*;

public class TreesHeaps {
    static class TreeNode {
        int val; TreeNode left, right;
        TreeNode(int v) { val = v; }
    }

    static int maxDepth(TreeNode root) {
        if (root == null) return 0;
        return 1 + Math.max(maxDepth(root.left), maxDepth(root.right));
    }

    static boolean isSymmetric(TreeNode a, TreeNode b) {
        if (a == null || b == null) return a == b;
        return a.val == b.val && isSymmetric(a.left, b.right) && isSymmetric(a.right, b.left);
    }

    static int kthLargest(int[] nums, int k) {
        PriorityQueue<Integer> heap = new PriorityQueue<>();
        for (int x : nums) {
            heap.offer(x);
            if (heap.size() > k) heap.poll();
        }
        return heap.peek();
    }

    public static void main(String[] args) {
        TreeNode root = new TreeNode(1);
        root.left = new TreeNode(2); root.right = new TreeNode(2);
        root.left.left = new TreeNode(3); root.right.right = new TreeNode(3);
        System.out.println(maxDepth(root));                    // 3
        System.out.println(isSymmetric(root.left, root.right)); // true
        System.out.println(kthLargest(new int[]{3, 2, 1, 5, 6, 4}, 2)); // 5
    }
}""",
            """Write level-order traversal (BFS, list per level). Then solve
the judged problem `symmetric-tree` and state its mirror invariant.
Practice: /practice/problems/symmetric-tree""",
        ),
        (
            "java-graphs",
            "Graphs: BFS, DFS, topo sort and union-find",
            "Adjacency lists, grid floods, shortest paths and course schedules.",
            """**Why this matters.** Graphs are connection problems: networks,
grids, prerequisites, friendships. Java solutions follow one of four
shapes — BFS shortest path, DFS connectivity/cycles, Kahn's topo sort,
union-find components — and interviewers recognise the shape instantly.
Model first ("nodes are cells, edges 4-directional"), then pick.

**Representations.** `Map<Integer, List<Integer>>` or `List<List<Integer>>`
adjacency for sparse graphs; `int[][]` grids as implicit graphs (neighbours
computed, visited marked in a `boolean[][]` or in place); edge lists for
union-find/Kruskal. Build adjacency once, traverse many times.

**BFS and DFS.** BFS (ArrayDeque): shortest path unweighted, level by
level — rotting oranges (multi-source: enqueue all sources at dist 0),
grid distance, word ladder. DFS (recursive or explicit stack):
connectivity, islands counting, cycle detection (three colours: WHITE/
GREY/BLACK — grey revisit means back edge), path existence. Both `O(V +
E)`; grids `O(rows × cols)`. Recursion depth on big grids → iterative.

**Topo sort and union-find.** Course schedule: Kahn's (indegree zero
queue, peel, count — processed < n means cycle) or DFS finishing order
reversed. Union-find with path compression + union by rank: near-`O(1)`
amortised; provinces, redundant connection, accounts merge. Java: parent/
rank arrays, `find` with halving.

**Common mistakes.** No visited set (cycles loop forever); single BFS
from node 0 on disconnected graphs (loop all nodes); directed vs
undirected confusion (add both edges only when undirected); mutating the
input grid the caller still needs; recursion overflow; indegree array
sized wrong.

**Interview angle.** The modelling sentence is half the grade: "cells
are nodes; BFS gives shortest because edges weigh 1." Then complexity
`O(V + E)` unprompted. For topo, state both Kahn and DFS options and
pick one.""",
            """import java.util.*;

public class GraphsDeep {
    // Kahn's topological sort: returns order, or empty if a cycle exists.
    static int[] topoOrder(int n, int[][] prereqs) {
        List<List<Integer>> adj = new ArrayList<>();
        for (int i = 0; i < n; i++) adj.add(new ArrayList<>());
        int[] indegree = new int[n];
        for (int[] p : prereqs) { adj.get(p[1]).add(p[0]); indegree[p[0]]++; }
        Deque<Integer> queue = new ArrayDeque<>();
        for (int i = 0; i < n; i++) if (indegree[i] == 0) queue.offer(i);
        int[] order = new int[n];
        int filled = 0;
        while (!queue.isEmpty()) {
            int u = queue.poll();
            order[filled++] = u;
            for (int v : adj.get(u)) if (--indegree[v] == 0) queue.offer(v);
        }
        return filled == n ? order : new int[0];
    }

    static int islands(char[][] grid) {
        int count = 0;
        for (int r = 0; r < grid.length; r++)
            for (int c = 0; c < grid[0].length; c++)
                if (grid[r][c] == '1') { count++; flood(grid, r, c); }
        return count;
    }

    static void flood(char[][] g, int r, int c) {
        if (r < 0 || c < 0 || r >= g.length || c >= g[0].length || g[r][c] != '1') return;
        g[r][c] = '#';
        flood(g, r + 1, c); flood(g, r - 1, c); flood(g, r, c + 1); flood(g, r, c - 1);
    }

    public static void main(String[] args) {
        System.out.println(Arrays.toString(topoOrder(4, new int[][]{{1,0},{2,0},{3,1},{3,2}})));
        System.out.println(islands(new char[][]{"11110".toCharArray(), "11010".toCharArray(),
            "11000".toCharArray(), "00000".toCharArray()})); // 1
    }
}""",
            """Implement union-find with path compression and union by rank;
use it to count provinces. Then solve the judged problem
`course-schedule` (can all courses finish?).
Practice: /practice/problems/course-schedule""",
        ),
        (
            "java-dp",
            "Dynamic programming: state, transition, table",
            "Memoized recursion first, tabulation with rolling arrays after.",
            """**Why this matters.** DP is Java interviews' hardest regular
topic — and the most formulaic. State, transition, base case: climbing
stairs, robber, coin change, LIS, LCS, edit distance, knapsack all share
the skeleton. Java's explicit arrays make tables visible, which actually
helps: you can see the order you must fill.

**Top-down first.** Write the recursion, memoize with an array (sentinel
-1/flag) or HashMap for sparse states. `dp(i)` = answer for prefix/state
i; transition tries the choices; base cases ground it. Climbing stairs:
`dp(n) = dp(n-1) + dp(n-2)`. Robber: `dp(i) = max(dp(i-1), dp(i-2) +
nums[i])`. Coin change: `dp(x) = 1 + min(dp(x - c))`. Only reachable
states compute — often fewer than the full table.

**Bottom-up and the space cut.** Fill from base cases in dependency
order (i ascending when dp[i] needs smaller i; 2D row by row). Then
compress: if row i needs only row i-1 (unique paths, edit distance),
keep two rows (`O(n)` space); if dp[i] needs i-1, i-2 (stairs, robber),
keep two variables (`O(1)`). The compression is a standard follow-up —
practise offering it.

**Recognising DP.** "In how many ways / min-max cost / can you" +
small choices + compact future-state (index, remainder, last-taken).
1D index, 2D grid/interval/string-pair, subset-sum boolean, knapsack
(weight limit) — learn one canonical each. No overlapping subproblems?
It is divide-and-conquer, not DP — do not memoize needlessly.

**Common mistakes.** Base cases off by one (empty prefix is dp[0]);
size tables n+1); wrong fill order (reading unfilled cells); int
overflow on counting (use long); sentinel collisions (-1 valid answer?
use boolean visited + value, or null Integer); exponential recursion
accepted without memo.

**Interview angle.** "States × transition cost" for time, "states" for
space — state both. Start top-down on the board, offer bottom-up + space
cut. Java's typed arrays make the table concrete; point at the cells
your transition reads.""",
            """import java.util.*;

public class DpDeep {
    // Bottom-up coin change, O(amount * coins) time, O(amount) space.
    static int coinChange(int[] coins, int amount) {
        int INF = amount + 1;
        int[] table = new int[amount + 1];
        Arrays.fill(table, INF);
        table[0] = 0;
        for (int value = 1; value <= amount; value++)
            for (int coin : coins)
                if (coin <= value)
                    table[value] = Math.min(table[value], table[value - coin] + 1);
        return table[amount] > amount ? -1 : table[amount];
    }

    // House robber, O(1) space: only prev two states matter.
    static int rob(int[] nums) {
        int prev2 = 0, prev1 = 0;
        for (int x : nums) {
            int cur = Math.max(prev1, prev2 + x);
            prev2 = prev1; prev1 = cur;
        }
        return prev1;
    }

    public static void main(String[] args) {
        System.out.println(coinChange(new int[]{1, 2, 5}, 11)); // 3
        System.out.println(rob(new int[]{2, 7, 9, 3, 1}));      // 12
    }
}""",
            """Solve longest-increasing-subsequence in O(n²), then state how
patience sorting reaches O(n log n). Then solve the judged problem
`house-robber` both top-down and rolling.
Practice: /practice/problems/house-robber""",
        ),
        (
            "java-interview-mastery",
            "Google-level problem solving in Java",
            "Clarify, brute force, optimise, code, test — with Java precision.",
            """**Why this matters.** Hard interviews reward method over memory.
Five steps, every problem: clarify, brute force, optimise, code, test.
Java adds its own grading axis — types, collections named precisely,
null/edge handling, complexity stated with the exact structure costs.
This module turns the method into rehearsal.

**The five steps, Java-flavoured.** (1) Clarify: examples, empties,
ranges ("n up to?"), sortedness, mutability, nulls ("can the array/TreeNode
be null?"). (2) Brute force aloud with complexity — sets the bar and
proves comprehension. (3) Optimise by pattern: inner search → HashMap/
HashSet; sorted pairs → two pointers; constrained subarray → window;
nested → ArrayDeque stack; levels/shortest → BFS; connectivity/order →
DFS/topo/union-find; k-extreme → PriorityQueue; counting/optimising →
DP; boundary/feasibility → binary search on answer. (4) Code with
helpers, final locals, invariant comments. (5) Trace examples + null/
empty/single/dupe/max by hand.

**Design problems (LRU and friends).** Java OOP interviews love
implementations: LRU cache (HashMap + doubly-linked list, or
LinkedHashMap in 5 lines — know both, code the manual one when asked),
MinStack (stack of (value, current-min) pairs), Trie (arrays of 26 +
isEnd), time-based store (HashMap + TreeMap floorEntry). State per-op
complexity as you declare each method.

**Behave senior.** `Objects.requireNonNull`, guard clauses, early
returns, no magic numbers, overflow-safe mid, `long` for counting,
`StringBuilder` for building. Talk while coding — narrate the invariant
and the next three lines. When stuck: shrink to n=3, solve by hand,
generalise; assume sorted, then lift it.

**Common mistakes.** Silent coding (ungradeable); leaping to DP before
hash/two-pointer/window; reciting memorised code that breaks on the
twist; ignoring nulls/overflow until prompted; no dry-run; streams
everywhere in hot paths (fine, but know the cost).

**Rehearsal plan.** 120 problems across the atlas, aloud, timed; log
misses by pattern; redo misses weekly. LRU from scratch monthly until
boring. That loop manufactures the "effortless" candidates.""",
            """import java.util.*;

public class LruMastery {
    // O(1) get/put: HashMap for lookup, doubly-linked list for recency.
    static class LRUCache {
        static class Node { int key, value; Node prev, next; Node(int k, int v) { key = k; value = v; } }
        private final int capacity;
        private final Map<Integer, Node> map = new HashMap<>();
        private final Node head = new Node(-1, -1), tail = new Node(-1, -1);

        LRUCache(int capacity) {
            this.capacity = capacity;
            head.next = tail; tail.prev = head;
        }
        private void detach(Node n) { n.prev.next = n.next; n.next.prev = n.prev; }
        private void attachFront(Node n) { n.next = head.next; n.prev = head; head.next.prev = n; head.next = n; }

        int get(int key) {
            Node n = map.get(key);
            if (n == null) return -1;
            detach(n); attachFront(n);
            return n.value;
        }
        void put(int key, int value) {
            Node n = map.get(key);
            if (n != null) { n.value = value; detach(n); attachFront(n); return; }
            if (map.size() == capacity) { Node lru = tail.prev; detach(lru); map.remove(lru.key); }
            Node fresh = new Node(key, value);
            map.put(key, fresh); attachFront(fresh);
        }
    }

    public static void main(String[] args) {
        LRUCache c = new LRUCache(2);
        c.put(1, 1); c.put(2, 2);
        System.out.println(c.get(1)); // 1
        c.put(3, 3);                  // evicts 2
        System.out.println(c.get(2)); // -1
    }
}""",
            """Implement MinStack (push/pop/top/getMin in O(1)) with pairs.
Then solve the judged hard problem `lru-cache`, first with
LinkedHashMap, then with the manual list above.
Practice: /practice/problems/lru-cache""",
        ),
    ]
}

#: Module slug -> judged problem slug for the "code what you learned" button.
MODULE_PRACTICE: dict[str, str] = {
    "java-complexity-big-o": "binary-search",
    "java-strings-deep": "valid-palindrome",
    "java-arrays-arraylist": "sorted-squares",
    "java-hashmap-hashset": "two-sum",
    "java-recursion": "climb-stairs",
    "java-sorting-searching": "merge-intervals",
    "java-stacks-queues": "valid-parentheses",
    "java-linked-lists": "middle-of-linked-list",
    "java-trees-heaps": "symmetric-tree",
    "java-graphs": "course-schedule",
    "java-dp": "house-robber",
    "java-interview-mastery": "lru-cache",
}

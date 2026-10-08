"""Community threads for the seeded database.

The community page shipped rendering "No discussions yet - start the first one."
on a fresh install, because nothing seeded ``discussions``, ``comments`` or
``votes``. A forum with no posts in it is not a feature a visitor can evaluate,
and every thread here is deliberately anchored to a topic that exists so the
"asked about <topic>" link resolves instead of dangling.

Conventions the seeder relies on:

* ``author`` and each reply's ``author`` are demo usernames, not user ids.
* ``topic`` is a topic slug; the seeder resolves it and fails loudly if it is
  unknown rather than dropping the row.
* ``days_ago`` is relative to seeding time, so the ordering and the "3 days ago"
  labels stay believable whenever the database is rebuilt.
"""
from __future__ import annotations

#: One entry per thread. ``accepted`` marks the reply that resolved it.
THREADS: list[dict] = [
    {
        "author": "asha",
        "kind": "doubt",
        "topic": "deadlocks",
        "tags": ["operating-systems", "deadlocks", "exam"],
        "title": "Why does the bankerman's algorithm need a 'safe' state rather than just checking for a cycle?",
        "body": (
            "I can detect a deadlock with a resource-allocation graph, so why does the banker's "
            "algorithm bother computing whether a safe sequence exists?\n\n"
            "My guess is that a safe state is about *avoidance* - refusing a request now so we never "
            "reach a deadlock - while the graph only tells me I am already stuck. Is that the whole "
            "story?"
        ),
        "days_ago": 9,
        "resolved": True,
        "replies": [
            {
                "author": "profsharma",
                "days_ago": 9,
                "upvotes": 14,
                "accepted": True,
                "body": (
                    "Exactly right, and the distinction is worth memorising because exams ask it "
                    "backwards.\n\n"
                    "- **Detection** answers \"am I deadlocked now?\" - it is reactive, and once the "
                    "answer is yes you must kill a process or preempt a resource.\n"
                    "- **Avoidance** answers \"if I grant this request, can every process still "
                    "finish in *some* order?\" - it is proactive. The safe sequence is that order.\n\n"
                    "The key insight is that an unsafe state is not yet a deadlock. It means a "
                    "deadlock is *possible* if the processes make unlucky requests. The banker's "
                    "algorithm trades throughput for that guarantee: it makes a process wait even "
                    "though nothing is wrong yet.\n\n"
                    "In practice almost nothing runs banker's algorithm - you would have to declare "
                    "maximum claims up front, which real programs cannot do. Databases do the "
                    "opposite and use detection plus victim selection, because a rolled-back "
                    "transaction is cheap compared to a stalled server."
                ),
            },
            {
                "author": "ravi",
                "days_ago": 8,
                "upvotes": 5,
                "accepted": False,
                "body": (
                    "The thing that made it click for me: safe means \"there exists at least one "
                    "order\". It does not mean every order works. So you only need to find one "
                    "sequence, which is why the algorithm is a greedy scan over unfinished processes."
                ),
            },
        ],
    },
    {
        "author": "ravi",
        "kind": "question",
        "topic": "indexes-query-performance",
        "tags": ["dbms", "postgres", "interview"],
        "title": "My query got slower after adding an index. How is that possible?",
        "body": (
            "Added `CREATE INDEX ON orders (status)` and a report query went from 210 ms to 1.4 s. "
            "The column has four distinct values across 40 million rows. `EXPLAIN ANALYZE` shows an "
            "index scan where it used to show a sequential scan."
        ),
        "days_ago": 7,
        "resolved": True,
        "replies": [
            {
                "author": "profsharma",
                "days_ago": 7,
                "upvotes": 19,
                "accepted": True,
                "body": (
                    "Your index is worse than useless for that predicate, and the planner is being "
                    "tricked by it.\n\n"
                    "With four distinct values over 40M rows, `status = 'shipped'` probably matches "
                    "millions of rows. Reading them through an index means one random page fetch per "
                    "matching row, then a heap visit for each. A sequential scan reads the same data "
                    "in large ordered chunks. Random I/O loses badly.\n\n"
                    "Two rules of thumb:\n"
                    "1. An index pays off when it selects a *small fraction* of the table - "
                    "roughly under 5-10%. Above that, sequential wins.\n"
                    "2. Low-cardinality columns (status, boolean flags, country) are poor index "
                    "candidates on their own.\n\n"
                    "What actually helps here is a **partial index**: "
                    "`CREATE INDEX ON orders (created_at) WHERE status = 'pending'`. It is tiny, it "
                    "stays in cache, and it only covers the rows you query. If you must index "
                    "status, make it composite with the column you sort or filter on next."
                ),
            },
            {
                "author": "asha",
                "days_ago": 6,
                "upvotes": 7,
                "accepted": False,
                "body": (
                    "Also check `ANALYZE orders;` after a bulk load. If the statistics are stale the "
                    "planner guesses row counts and can pick the index for a predicate that matches "
                    "half the table."
                ),
            },
            {
                "author": "priya",
                "days_ago": 5,
                "upvotes": 3,
                "accepted": False,
                "body": (
                    "Worth knowing the index is not free either: every INSERT and UPDATE to `status` "
                    "now maintains a second structure. On a write-heavy table that is a real cost "
                    "even for the queries that do benefit."
                ),
            },
        ],
    },
    {
        "author": "priya",
        "kind": "doubt",
        "topic": "bernoullis-equation",
        "tags": ["fluid-mechanics", "derivations"],
        "title": "Where exactly do the assumptions in Bernoulli's equation get used in the derivation?",
        "body": (
            "The textbook lists incompressible, inviscid, steady, along a streamline - and then the "
            "derivation looks like it only integrates Euler's equation. Which step needs which "
            "assumption? I keep losing marks for not stating them."
        ),
        "days_ago": 6,
        "resolved": True,
        "replies": [
            {
                "author": "profsharma",
                "days_ago": 6,
                "upvotes": 16,
                "accepted": True,
                "body": (
                    "Each assumption buys you one step:\n\n"
                    "- **Inviscid** lets you drop the viscous term and start from Euler's equation "
                    "instead of Navier-Stokes. This is the big one.\n"
                    "- **Steady** removes the local acceleration term, so the velocity field does "
                    "not change with time and the integration is path-independent in time.\n"
                    "- **Incompressible** makes density constant, so it comes out of the pressure "
                    "integral as a factor instead of needing an equation of state.\n"
                    "- **Along a streamline** is needed because the constant of integration can "
                    "differ between streamlines. Drop this one and the equation only holds for "
                    "irrotational flow, where the constant is global.\n\n"
                    "The one people forget in viva: **no shaft work and no heat transfer**. A pump "
                    "between your two points invalidates the plain form; you need the extended "
                    "energy equation with a head term."
                ),
            },
            {
                "author": "ravi",
                "days_ago": 5,
                "upvotes": 6,
                "accepted": False,
                "body": (
                    "Practical check for when it stops being valid: air below roughly Mach 0.3 is "
                    "fine as incompressible (density change under 5%). Above that you need the "
                    "compressible form. And near a solid boundary the inviscid assumption fails "
                    "inside the boundary layer even at low speed."
                ),
            },
        ],
    },
    {
        "author": "asha",
        "kind": "project",
        "topic": "transactions-acid",
        "tags": ["dbms", "project", "design"],
        "title": "Booking system: how do I stop two users from taking the same seat without locking the whole table?",
        "body": (
            "Building the ticket-booking project. Under load two requests both read the seat as "
            "free and both insert a booking. `SELECT ... FOR UPDATE` on the whole `seats` table "
            "works but serialises everyone. What is the standard approach?"
        ),
        "days_ago": 5,
        "resolved": True,
        "replies": [
            {
                "author": "profsharma",
                "days_ago": 5,
                "upvotes": 21,
                "accepted": True,
                "body": (
                    "Never rely on read-then-write across two statements - that is a textbook "
                    "write-skew race. Three approaches, in the order I would reach for them:\n\n"
                    "**1. A unique constraint, and let the database be the referee.**\n"
                    "`CREATE UNIQUE INDEX one_booking_per_seat ON bookings (show_id, seat_no) "
                    "WHERE status = 'confirmed';`\n"
                    "Both transactions insert; exactly one commits, the other gets a unique "
                    "violation you catch and turn into \"that seat was just taken\". This is correct "
                    "even if every other guard fails, so do this regardless.\n\n"
                    "**2. Lock the row, not the table.**\n"
                    "`SELECT ... FROM seats WHERE id = ? FOR UPDATE` locks one seat row. Other "
                    "seats proceed in parallel. Your version serialised everything because the lock "
                    "was taken too broadly.\n\n"
                    "**3. Compare-and-set in a single statement.**\n"
                    "`UPDATE seats SET status='held', held_by=? WHERE id=? AND status='free'` and "
                    "check the affected-row count. One statement, so no interleaving is possible. "
                    "Zero rows updated means someone beat you.\n\n"
                    "Do 1 always. Add 3 for the hot path - it is one round trip and cannot race. "
                    "Reach for 2 only when you need to hold the lock across several statements, and "
                    "keep that transaction short or you will build a queue behind it."
                ),
            },
            {
                "author": "ravi",
                "days_ago": 4,
                "upvotes": 8,
                "accepted": False,
                "body": (
                    "Add a `held_until` timestamp so an abandoned cart releases the seat. Otherwise "
                    "a user who closes the tab has locked it forever and support will hear about it "
                    "before you do."
                ),
            },
            {
                "author": "priya",
                "days_ago": 4,
                "upvotes": 4,
                "accepted": False,
                "body": (
                    "One thing that bit me on the same project: retry the transaction on a "
                    "serialisation failure rather than surfacing it. Postgres will abort with "
                    "SQLSTATE 40001 under `SERIALIZABLE`, and that is expected, not an error."
                ),
            },
        ],
    },
    {
        "author": "ravi",
        "kind": "question",
        "topic": "cpu-scheduling",
        "tags": ["operating-systems", "numericals"],
        "title": "Round robin quantum: why does average waiting time dip and then rise again?",
        "body": (
            "Plotting average waiting time against quantum size gives a U shape. Too small is bad, "
            "too large is bad. I understand the ends but not why there is a clean minimum somewhere "
            "in the middle."
        ),
        "days_ago": 5,
        "resolved": False,
        "replies": [
            {
                "author": "profsharma",
                "days_ago": 4,
                "upvotes": 11,
                "accepted": False,
                "body": (
                    "Two different costs are fighting.\n\n"
                    "Shrink the quantum and every process finishes sooner *relative to the others*, "
                    "so turnaround improves - but you pay a context switch every quantum. Switches "
                    "are not free: TLB flushes, cold caches, scheduler overhead. Below a few "
                    "milliseconds you are spending more time switching than running.\n\n"
                    "Grow the quantum and switching becomes negligible, but the queue behind the "
                    "running process lengthens. At the limit the quantum exceeds every burst and "
                    "round robin degenerates into FCFS - no preemption at all, so a short job "
                    "stuck behind a long one waits for the whole of it.\n\n"
                    "The minimum is where marginal switching cost equals marginal queueing cost. "
                    "Real systems pick 1-10 ms, which is comfortably above switch cost (tens of "
                    "microseconds) and below typical interactive response expectations."
                ),
            },
            {
                "author": "asha",
                "days_ago": 3,
                "upvotes": 4,
                "accepted": False,
                "body": (
                    "For the numerical: the trick is that a process re-entering the ready queue goes "
                    "to the *back*. Draw the Gantt chart rather than trying to reason about it "
                    "algebraically - with five processes it is faster and you cannot drop a burst."
                ),
            },
        ],
    },
    {
        "author": "priya",
        "kind": "discussion",
        "topic": "dynamic-programming",
        "tags": ["dsa", "interview", "patterns"],
        "title": "How do you actually recognise a DP problem in an interview, rather than after seeing the solution?",
        "body": (
            "I can solve them once I know it is DP. I cannot tell beforehand. Every guide says "
            "\"optimal substructure and overlapping subproblems\" which is true and completely "
            "unusable under pressure."
        ),
        "days_ago": 4,
        "resolved": True,
        "replies": [
            {
                "author": "profsharma",
                "days_ago": 4,
                "upvotes": 24,
                "accepted": True,
                "body": (
                    "Use three concrete tells instead of the definition:\n\n"
                    "**1. The question asks for a count, a minimum, a maximum, or a yes/no - not an "
                    "enumeration.** \"How many ways\", \"cheapest cost\", \"is it possible\". If it "
                    "wanted every solution listed, DP would be the wrong tool because the output "
                    "itself is exponential.\n\n"
                    "**2. You can describe a decision at each step.** At position i you either take "
                    "it or skip it. That binary choice with a recursive cost is the shape of nearly "
                    "every DP.\n\n"
                    "**3. Your brute force re-computes the same sub-answer.** Write the naive "
                    "recursion first - genuinely, on paper. If two branches call the function with "
                    "identical arguments, you have overlapping subproblems and memoisation is a "
                    "mechanical next step.\n\n"
                    "The workflow that works under pressure: brute-force recursion, then add a "
                    "memo table, then - only if they ask - flip it to bottom-up. Each step is a "
                    "small, safe edit. Trying to jump straight to the iterative table is where "
                    "people freeze, because you have to derive the order before you understand the "
                    "problem."
                ),
            },
            {
                "author": "ravi",
                "days_ago": 3,
                "upvotes": 9,
                "accepted": False,
                "body": (
                    "Adding a heuristic that has never failed me: if the constraints are around "
                    "n <= 20 it is probably backtracking or bitmask, n <= 2000 suggests O(n^2) DP, "
                    "and n <= 10^5 or higher means you need O(n log n) or a greedy/DP with a "
                    "clever state. The constraint tells you the intended complexity, which tells "
                    "you the technique."
                ),
            },
            {
                "author": "asha",
                "days_ago": 2,
                "upvotes": 6,
                "accepted": False,
                "body": (
                    "Name the state out loud before writing code: \"dp[i] = the minimum cost to "
                    "reach index i\". If you cannot state what one cell means in a sentence, the "
                    "recurrence will not come. Half of my wrong attempts were me starting to code "
                    "before I could say that."
                ),
            },
        ],
    },
    {
        "author": "asha",
        "kind": "doubt",
        "topic": "stress-strain-hookes-law",
        "tags": ["som", "lab", "derivations"],
        "title": "Why is the stress-strain curve for mild steel drawn with a distinct yield plateau but aluminium has none?",
        "body": (
            "In the lab our mild steel specimen showed a clear upper and lower yield point, then a "
            "flat region. The aluminium specimen curved smoothly with no obvious yield. Same "
            "machine, same procedure."
        ),
        "days_ago": 4,
        "resolved": True,
        "replies": [
            {
                "author": "profsharma",
                "days_ago": 3,
                "upvotes": 12,
                "accepted": True,
                "body": (
                    "It is a materials difference, not a testing artefact, and it comes down to how "
                    "dislocations are pinned.\n\n"
                    "Low-carbon steel has interstitial carbon and nitrogen atoms that cluster "
                    "around dislocations - Cottrell atmospheres. Breaking a dislocation free of "
                    "that atmosphere needs a higher stress, which is the **upper yield point**. Once "
                    "free, it moves at a lower stress and many dislocations unlock at once, which "
                    "is the **lower yield point** and the flat plateau that follows (Luder's "
                    "bands propagating along the gauge length).\n\n"
                    "Aluminium has no equivalent interstitial pinning, so dislocations mobilise "
                    "gradually and continuously. There is no sudden unlock, hence no plateau.\n\n"
                    "That is precisely why we use the **0.2% proof stress** convention for "
                    "aluminium and most non-ferrous alloys: with no visible yield point you need a "
                    "reproducible definition, so you draw a line parallel to the elastic slope "
                    "offset by 0.2% strain and read the intersection."
                ),
            },
            {
                "author": "ravi",
                "days_ago": 2,
                "upvotes": 5,
                "accepted": False,
                "body": (
                    "Worth noting for the lab report: if you unload and immediately reload mild "
                    "steel the yield point disappears, because the dislocations are already free. "
                    "It returns after ageing. Examiners like that detail because it shows you "
                    "understood the mechanism rather than the curve."
                ),
            },
        ],
    },
    {
        "author": "ravi",
        "kind": "question",
        "topic": "synchronisation-semaphores",
        "tags": ["operating-systems", "concurrency"],
        "title": "Mutex vs binary semaphore - our professor says they are different but the code looks identical",
        "body": (
            "Both take values 0 and 1, both are acquired and released. Every explanation I read "
            "says \"ownership\" but I cannot see what that changes in practice."
        ),
        "days_ago": 3,
        "resolved": True,
        "replies": [
            {
                "author": "profsharma",
                "days_ago": 3,
                "upvotes": 17,
                "accepted": True,
                "body": (
                    "Ownership is not a detail, it is the whole difference, and it changes who is "
                    "allowed to release.\n\n"
                    "A **mutex** has an owner. The thread that locked it is the only thread that may "
                    "unlock it. That makes priority inheritance possible - if a low-priority thread "
                    "holds a lock a high-priority thread needs, the kernel can temporarily boost the "
                    "holder. Without an owner there is nobody to boost, and you get unbounded "
                    "priority inversion.\n\n"
                    "A **binary semaphore** has no owner. Any thread can signal it. That is what "
                    "makes it usable for signalling between threads: thread A waits, thread B "
                    "signals when an interrupt arrives or a buffer fills. A mutex cannot express "
                    "that at all.\n\n"
                    "So the rule: **mutex to protect a critical section, semaphore to signal an "
                    "event.** If your code has one thread locking and a *different* thread "
                    "unlocking, you are using a semaphore whether you called it a mutex or not - "
                    "and if the API enforced ownership, it would have thrown."
                ),
            },
            {
                "author": "priya",
                "days_ago": 2,
                "upvotes": 7,
                "accepted": False,
                "body": (
                    "The practical version in C: `pthread_mutex_t` will return EPERM if you unlock "
                    "from the wrong thread with an error-checking mutex type. POSIX semaphores will "
                    "happily let any thread post. Same shape, different contract, and only one of "
                    "them catches the mistake."
                ),
            },
        ],
    },
    {
        "author": "priya",
        "kind": "discussion",
        "topic": "ip-addressing-subnetting",
        "tags": ["networks", "placement", "numericals"],
        "title": "Subnetting shortcut that survived three campus interviews",
        "body": (
            "Sharing what worked for me, since I kept making arithmetic errors doing it the long "
            "way under time pressure."
        ),
        "days_ago": 3,
        "resolved": False,
        "replies": [
            {
                "author": "priya",
                "days_ago": 3,
                "upvotes": 13,
                "accepted": False,
                "body": (
                    "Memorise the eight values of the fourth octet for a /24-/32 mask: 0, 128, 192, "
                    "224, 240, 248, 252, 254, 255. Then:\n\n"
                    "- **Block size** = 256 - mask octet. For /27 the octet is 224, so blocks are "
                    "32 wide: 0, 32, 64, 96...\n"
                    "- **Usable hosts** = 2^(32-prefix) - 2. For /27 that is 32 - 2 = 30.\n"
                    "- To find which subnet an address is in, divide the octet by the block size "
                    "and drop the remainder.\n\n"
                    "The -2 is the network and broadcast address. Interviewers specifically watch "
                    "for it, and forgetting it is the single most common wrong answer."
                ),
            },
            {
                "author": "asha",
                "days_ago": 2,
                "upvotes": 5,
                "accepted": False,
                "body": (
                    "One caveat worth saying out loud in an interview: /31 has 2^1 - 2 = 0 usable "
                    "hosts by that formula, but RFC 3021 defines it as valid for point-to-point "
                    "links with both addresses usable. Mentioning that exception reads as depth "
                    "rather than pedantry."
                ),
            },
        ],
    },
    {
        "author": "asha",
        "kind": "question",
        "topic": "convolution-lti-systems",
        "tags": ["signals", "maths"],
        "title": "When should I convolve in time versus multiply in frequency?",
        "body": (
            "Both give the same answer for an LTI system. Is it purely a convenience choice or is "
            "there a correctness reason to prefer one?"
        ),
        "days_ago": 2,
        "resolved": True,
        "replies": [
            {
                "author": "profsharma",
                "days_ago": 2,
                "upvotes": 10,
                "accepted": True,
                "body": (
                    "For an exam question with a short impulse response, time-domain convolution is "
                    "faster and shows your working. For anything long, the frequency domain wins on "
                    "cost: convolution is O(N*M) while an FFT-based approach is O(N log N).\n\n"
                    "But the reason that actually matters in practice is **what each representation "
                    "makes visible**. Convolution hides the frequency behaviour entirely; the "
                    "transfer function H(jw) tells you immediately whether the system is a low-pass "
                    "filter, where its poles are, and therefore whether it is stable. If the "
                    "question is about stability or filtering, go to the frequency domain - you "
                    "will read the answer off the pole locations instead of grinding through an "
                    "integral.\n\n"
                    "One caveat: the equivalence requires the transform to exist. For a system that "
                    "is not BIBO stable the Fourier transform may not converge, and you need "
                    "Laplace with a region of convergence. That is exactly the case where "
                    "time-domain convolution still works but frequency-domain multiplication "
                    "silently gives you nonsense."
                ),
            },
        ],
    },
    {
        "author": "ravi",
        "kind": "doubt",
        "topic": "memory-management-paging",
        "tags": ["operating-systems", "exam"],
        "title": "Effective access time with a TLB - I keep getting the weighting wrong",
        "body": (
            "Is it `h * (t + m) + (1 - h) * (t + 2m)` or `h * m + (1 - h) * (t + 2m)`? Textbooks "
            "differ and my answers are off by the TLB lookup time."
        ),
        "days_ago": 2,
        "resolved": True,
        "replies": [
            {
                "author": "profsharma",
                "days_ago": 1,
                "upvotes": 15,
                "accepted": True,
                "body": (
                    "Both forms appear in textbooks because they model different hardware, so state "
                    "your assumption and you cannot be marked down.\n\n"
                    "**Parallel lookup** - the TLB and the page table are searched at the same "
                    "time, so a hit costs just the memory access `m`:\n"
                    "`EAT = h * m + (1 - h) * (t + 2m)`\n\n"
                    "**Sequential lookup** - you check the TLB first and only go to the page table "
                    "on a miss, so a hit still costs `t + m`:\n"
                    "`EAT = h * (t + m) + (1 - h) * (t + 2m)`\n\n"
                    "Where `t` is TLB lookup time, `m` is memory access time, `h` is hit ratio, and "
                    "`2m` on a miss is one access for the page table entry plus one for the data.\n\n"
                    "Two things that lose marks: forgetting that a miss costs *two* memory "
                    "accesses, and forgetting that multi-level paging makes it three or more. If "
                    "the question says two-level paging, a miss is `3m`."
                ),
            },
            {
                "author": "priya",
                "days_ago": 1,
                "upvotes": 4,
                "accepted": False,
                "body": (
                    "Sanity check that catches most arithmetic slips: as h approaches 1 the EAT "
                    "must approach a single memory access. If your formula tends to 2m at h = 1, "
                    "you have double-counted somewhere."
                ),
            },
        ],
    },
    {
        "author": "priya",
        "kind": "project",
        "topic": "sql-joins-aggregation",
        "tags": ["dbms", "project"],
        "title": "Getting a per-group top-N without a window function on old MySQL",
        "body": (
            "The project brief pins us to MySQL 5.7 for the deployment target, so `ROW_NUMBER() "
            "OVER (PARTITION BY ...)` is unavailable. I need the three latest orders per customer."
        ),
        "days_ago": 2,
        "resolved": False,
        "replies": [
            {
                "author": "profsharma",
                "days_ago": 1,
                "upvotes": 9,
                "accepted": False,
                "body": (
                    "The classic pre-window-function trick is a correlated count: a row is in the "
                    "top three of its group if fewer than three rows in the same group sort ahead "
                    "of it.\n\n"
                    "```sql\n"
                    "SELECT o.*\n"
                    "FROM orders o\n"
                    "WHERE (\n"
                    "  SELECT COUNT(*) FROM orders o2\n"
                    "  WHERE o2.customer_id = o.customer_id\n"
                    "    AND (o2.created_at > o.created_at\n"
                    "         OR (o2.created_at = o.created_at AND o2.id > o.id))\n"
                    ") < 3;\n"
                    "```\n\n"
                    "The `id` tiebreaker is not optional. Without it, two orders with identical "
                    "timestamps both see the same count and you get four rows, or you drop one "
                    "non-deterministically. Make the ordering a total order and the result is "
                    "reproducible.\n\n"
                    "Watch the cost: it is O(n^2) within each group. With an index on "
                    "`(customer_id, created_at, id)` it is acceptable for moderate data. If you "
                    "outgrow it, the right answer is to upgrade the target rather than to keep "
                    "fighting the query."
                ),
            },
        ],
    },
    {
        "author": "asha",
        "kind": "discussion",
        "topic": "transformers",
        "tags": ["electrical", "lab"],
        "title": "Open-circuit test on the LV side, short-circuit test on the HV side - why the swap?",
        "body": (
            "We always do OC on the low-voltage winding and SC on the high-voltage winding. Our "
            "lab manual states it without justifying it and I want to know the real reason."
        ),
        "days_ago": 1,
        "resolved": True,
        "replies": [
            {
                "author": "profsharma",
                "days_ago": 1,
                "upvotes": 13,
                "accepted": True,
                "body": (
                    "Both choices are about keeping the instruments in a safe and readable range.\n\n"
                    "**Open-circuit on the LV side:** the test needs rated voltage to establish "
                    "correct core flux, and it measures core loss. Applying rated voltage to the LV "
                    "winding means your supply only has to reach, say, 230 V instead of 11 kV. The "
                    "HV winding is left open, and the flux - set by V/f on the excited winding - is "
                    "the same either way, so the core loss you measure is valid.\n\n"
                    "**Short-circuit on the HV side:** this test measures copper loss and needs "
                    "rated *current*, at a small fraction of rated voltage. Rated current on the HV "
                    "side is the smaller of the two currents, so your ammeter and supply handle it "
                    "easily. Doing it on the LV side would mean pushing the much larger LV current "
                    "through the instruments.\n\n"
                    "The symmetry is the point: OC wants rated *voltage*, so use the low-voltage "
                    "winding. SC wants rated *current*, so use the high-current... which is the "
                    "low-voltage side's counterpart - the HV winding carries less current. Each "
                    "test is done where the quantity you are controlling is the smaller one."
                ),
            },
            {
                "author": "ravi",
                "days_ago": 1,
                "upvotes": 6,
                "accepted": False,
                "body": (
                    "Related detail worth knowing: in the SC test the applied voltage is only a few "
                    "percent of rated, so core flux is tiny and core loss is negligible. That is "
                    "why you can attribute the whole measured wattage to copper loss. If you "
                    "applied rated voltage with the secondary shorted, you would destroy the "
                    "transformer."
                ),
            },
        ],
    },
    {
        "author": "ravi",
        "kind": "doubt",
        "topic": "hash-tables",
        "tags": ["dsa", "interview"],
        "title": "Why is load factor 0.75 the default in HashMap?",
        "body": (
            "Java uses 0.75, and every source says \"it is a tradeoff\" without quantifying "
            "anything. Is there a derivation or is it just a tuned constant?"
        ),
        "days_ago": 1,
        "resolved": True,
        "replies": [
            {
                "author": "profsharma",
                "days_ago": 1,
                "upvotes": 11,
                "accepted": True,
                "body": (
                    "There is a real argument, and the Java documentation actually cites it.\n\n"
                    "Under a uniform hash and Poisson-distributed bucket occupancy, at a load factor "
                    "of 0.5 roughly 0.5 * 0.78 = 39% of buckets are empty - you are wasting more "
                    "than a third of the array. Push to 1.0 and collisions become frequent enough "
                    "that chains lengthen and lookups degrade towards O(n).\n\n"
                    "At 0.75 the Poisson calculation gives an expected chain length near 0.5, with "
                    "the probability of eight or more entries in a bucket around six in ten "
                    "million. That is the number that matters for modern implementations: it is why "
                    "Java can convert a long bucket to a red-black tree at threshold 8 and expect "
                    "never to do it in normal operation.\n\n"
                    "So 0.75 is not arbitrary - it is the point where space waste is tolerable "
                    "(25% of the array) while long chains stay vanishingly rare. It also plays "
                    "nicely with power-of-two capacities: doubling from 16 keeps the resize "
                    "thresholds integral."
                ),
            },
        ],
    },
    {
        "author": "priya",
        "kind": "question",
        "topic": "material-energy-balances",
        "tags": ["chemical", "process"],
        "title": "Recycle stream problems - should I solve the overall balance or the mixing point?",
        "body": (
            "Recycle and purge problems take me twenty minutes because I set up equations at the "
            "wrong boundary every time."
        ),
        "days_ago": 1,
        "resolved": False,
        "replies": [
            {
                "author": "profsharma",
                "days_ago": 0,
                "upvotes": 8,
                "accepted": False,
                "body": (
                    "Always start with the **overall** balance around the entire process, ignoring "
                    "the internal recycle entirely. The recycle is internal, so it does not appear "
                    "in the overall balance, and you can usually solve for the fresh feed and the "
                    "product directly.\n\n"
                    "Then move inward: balance around the mixing point, then the separator. By the "
                    "time you reach the recycle stream you already know most of the unknowns and it "
                    "falls out algebraically.\n\n"
                    "The mistake that costs the twenty minutes is writing equations at the mixing "
                    "point first, where the recycle flow is an unknown appearing on both sides. You "
                    "end up with a simultaneous system you did not need.\n\n"
                    "And check yourself with the invariant: at steady state, accumulation is zero, "
                    "so whatever enters as fresh feed must leave as product, purge, or waste. If "
                    "your numbers do not close on that, an arithmetic slip happened somewhere and "
                    "no amount of re-deriving the recycle will find it."
                ),
            },
        ],
    },
    {
        "author": "asha",
        "kind": "discussion",
        "topic": "design-patterns",
        "tags": ["oop", "interview"],
        "title": "Singleton gets a bad reputation. When is it genuinely the right call?",
        "body": (
            "Every article I read says singleton is an anti-pattern and to use dependency "
            "injection instead. But our OS lab needs exactly one scheduler instance, and faking it "
            "feels more artificial than the pattern."
        ),
        "days_ago": 0,
        "resolved": False,
        "replies": [
            {
                "author": "profsharma",
                "days_ago": 0,
                "upvotes": 12,
                "accepted": False,
                "body": (
                    "The criticism is narrower than the articles suggest. The problem is not "
                    "\"exactly one instance\" - it is **global mutable state accessed through a "
                    "hidden dependency**. If a class calls `Config.getInstance()` internally, "
                    "nothing in its signature reveals that dependency, so you cannot substitute it "
                    "in a test and you cannot tell what the class touches by reading its interface.\n\n"
                    "So the distinction that matters:\n\n"
                    "- **Enforce the cardinality where it is a real constraint** - a hardware "
                    "handle, a connection pool, a kernel scheduler. That is legitimate.\n"
                    "- **But still inject the instance** rather than fetching it. Construct the "
                    "single object once at startup and pass it in. You keep the guarantee and you "
                    "keep testability.\n\n"
                    "For your scheduler: one instance is correct. Have the constructor take its "
                    "dependencies and let the composition root own the single object. That is the "
                    "version nobody objects to.\n\n"
                    "The genuinely bad case is a singleton holding mutable per-request state. Then "
                    "you have a data race under concurrency and tests that leak into each other, "
                    "and no amount of careful initialisation saves you."
                ),
            },
        ],
    },
]

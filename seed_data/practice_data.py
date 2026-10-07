"""Daily Practice Problem bank.

Each entry: (subject, title, difficulty, statement, options, correct_index, explanation, tags, year_hint)
Options are shown in order; `correct` is the 0-based index.
"""


def q(subject, title, difficulty, statement, options, correct, explanation, tags, source="EngineVerse Bank"):
    return {
        "subject": subject,
        "title": title,
        "difficulty": difficulty,
        "statement": statement,
        "options": options,
        "correct": correct,
        "explanation": explanation,
        "tags": tags,
        "source": source,
    }


QUESTIONS = [
    # ---------------------------------------------------------------- DSA
    q("data-structures-algorithms", "Worst case of quicksort", "easy",
      "What is the worst-case time complexity of quicksort, and when does it occur?",
      ["O(n log n), when the array is random",
       "O(n^2), when the pivot is always the smallest or largest element",
       "O(n), when the array is already sorted with a randomised pivot",
       "O(log n), when the array has all distinct elements"],
      1,
      "If the pivot consistently ends up at an extreme, one partition holds n-1 elements and the recursion "
      "depth becomes n, giving T(n) = T(n-1) + O(n) = O(n^2). A already-sorted array with a fixed first-element "
      "pivot is the classic trigger; randomised or median-of-three pivot selection makes this vanishingly rare.",
      ["quicksort", "complexity", "sorting"]),

    q("data-structures-algorithms", "Balanced BST height", "easy",
      "An AVL tree contains 15 nodes. What is the minimum possible height (counting the root as height 0)?",
      ["2", "3", "4", "5"],
      1,
      "A perfectly balanced tree with 15 nodes has 4 levels: 1 + 2 + 4 + 8 = 15, so the height counting the root "
      "as 0 is 3.",
      ["avl", "tree", "height"]),

    q("data-structures-algorithms", "Heap insertion cost", "medium",
      "Inserting an element into a binary heap of n elements has worst-case complexity of:",
      ["O(1)", "O(log n)", "O(n)", "O(n log n)"],
      1,
      "The new element is placed at the next leaf and sifted up. The tree height is floor(log2 n), so at most "
      "that many swaps occur. Amortised analysis does not improve on this worst case.",
      ["heap", "priority-queue"]),

    q("data-structures-algorithms", "Graph traversal memory", "medium",
      "For a dense graph with n vertices and O(n^2) edges, which representation makes BFS asymptotically fastest?",
      ["Adjacency list", "Adjacency matrix", "Edge list", "It makes no difference"],
      0,
      "BFS touches each edge once. An adjacency list visits exactly the edges that exist, O(V + E). An adjacency "
      "matrix scans all n columns per vertex, giving O(V^2) even when E is much smaller. For a truly dense graph "
      "the two coincide, but the list is never worse and is strictly better in the common sparse case.",
      ["graph", "bfs", "representation"]),

    q("data-structures-algorithms", "Dynamic programming structure", "hard",
      "Which property must a problem have for a top-down memoised DP to be correct AND efficient?",
      ["Optimal substructure only",
       "Overlapping subproblems only",
       "Both optimal substructure and overlapping subproblems",
       "Neither - memoisation works on any recursion"],
      2,
      "Optimal substructure guarantees that combining optimal sub-solutions yields an optimal solution, which is "
      "what makes caching answers sound. Overlapping subproblems is what makes caching worthwhile; without it you "
      "have merely added a dictionary to a divide-and-conquer algorithm.",
      ["dp", "memoization"]),

    q("data-structures-algorithms", "Amortised analysis of a dynamic array", "medium",
      "Appending n items to an initially empty dynamic array that doubles when full has total cost:",
      ["O(n^2)", "O(n log n)", "O(n)", "O(log n)"],
      2,
      "The copies form the geometric series 1 + 2 + 4 + ... + n < 2n, so the total work including all reallocations "
      "is O(n) - an amortised O(1) per append.",
      ["amortized", "array", "complexity"]),

    # ---------------------------------------------------------------- OS
    q("operating-systems", "Thrashing cause", "medium",
      "A system is thrashing. Which change is most likely to help immediately?",
      ["Increase the time-slice length",
       "Reduce the degree of multiprogramming",
       "Disable the paging file",
       "Switch from LRU to FIFO page replacement"],
      1,
      "Thrashing occurs when too many processes compete for too few frames, so each spends more time faulting "
      "than executing. Lowering the degree of multiprogramming gives the remaining processes enough resident "
      "pages to make progress.",
      ["paging", "thrashing", "memory"]),

    q("operating-systems", "Deadlock conditions", "medium",
      "Which of the four Coffman conditions is the only one commonly broken in practice by an operating system?",
      ["Mutual exclusion", "Hold and wait", "No preemption", "Circular wait"],
      3,
      "Mutual exclusion is intrinsic to the resource. Breaking hold-and-wait or no-preemption usually makes the "
      "system unusable. Imposing a total order on resource acquisition removes circular wait and is the technique "
      "actually used in kernels and databases.",
      ["deadlock", "concurrency"]),

    q("operating-systems", "Context switch vs mode switch", "easy",
      "What is the key difference between a mode switch and a context switch?",
      ["They are the same thing",
       "A mode switch changes CPU privilege level; a context switch also saves and restores process state",
       "A context switch is faster than a mode switch",
       "A mode switch changes the running process"],
      1,
      "Every system call causes a mode switch. A context switch happens only when the scheduler picks a different "
      "process, and it must save registers, the program counter and the stack pointer - which is why it costs "
      "thousands of cycles compared with a few hundred for a mode switch.",
      ["scheduling", "cpu"]),

    q("operating-systems", "Banker's algorithm", "hard",
      "The Banker's algorithm is a deadlock strategy that belongs to which category?",
      ["Prevention", "Avoidance", "Detection and recovery", "Ostrich"],
      1,
      "It grants a request only if the resulting state remains safe, so it avoids entering an unsafe state. It "
      "needs advance knowledge of maximum demand, which is why real systems rarely implement it in full.",
      ["deadlock", "bankers"]),

    # ---------------------------------------------------------------- DBMS
    q("dbms", "Normalisation anomaly", "medium",
      "A relation R(A, B, C) has functional dependencies A -> B and B -> C, with A as the primary key. Which normal form does it violate?",
      ["1NF", "2NF", "3NF", "BCNF only"],
      2,
      "A -> B -> C is a transitive dependency on a non-prime attribute, which violates 3NF. Decomposing into "
      "R1(A,B) and R2(B,C) removes the anomaly.",
      ["normalization", "fd"]),

    q("dbms", "Index type for range queries", "easy",
      "Which index structure supports efficient range scans over an ordered key?",
      ["Hash index", "B+ tree", "Bitmap index", "Inverted index"],
      1,
      "A hash index destroys ordering, so it answers equality only. A B+ tree keeps keys sorted and links its "
      "leaves, giving O(log n) descent followed by a sequential leaf scan.",
      ["indexing", "btree"]),

    q("dbms", "Isolation level", "hard",
      "Which isolation level prevents phantom reads in the SQL standard?",
      ["Read uncommitted", "Read committed", "Repeatable read", "Serializable"],
      3,
      "Repeatable read locks rows that were read but not the gaps between them, so new matching rows can still "
      "appear. Serializable is the level that prevents phantoms, usually via predicate locking or SSI.",
      ["transactions", "isolation", "concurrency"]),

    q("dbms", "ACID - what does D guarantee?", "easy",
      "Durability in ACID guarantees that:",
      ["A transaction sees a consistent snapshot",
       "Once committed, changes survive a crash",
       "Concurrent transactions do not interfere",
       "All statements in a transaction succeed or none do"],
      1,
      "Durability is implemented with write-ahead logging: the log record reaches stable storage before the commit "
      "is acknowledged, so recovery can replay it after a crash.",
      ["acid", "wal"]),

    # ---------------------------------------------------------------- NETWORKS
    q("computer-networks", "Subnet mask arithmetic", "medium",
      "How many usable host addresses does the prefix 192.168.10.0/28 provide?",
      ["16", "14", "15", "30"],
      1,
      "/28 leaves 4 host bits: 2^4 = 16 addresses, minus the network address and the broadcast address, giving "
      "14 usable hosts.",
      ["subnetting", "ipv4"]),

    q("computer-networks", "TCP vs UDP", "easy",
      "Which protocol is the right choice for a live voice call that can tolerate occasional packet loss?",
      ["TCP, because it guarantees delivery",
       "UDP, because retransmission would arrive too late to be useful",
       "Either is equivalent",
       "ICMP"],
      1,
      "Real-time media is delay-bounded. A packet retransmitted after its playout deadline is worthless, so the "
      "reliability machinery of TCP costs latency without benefit. RTP over UDP is the standard choice.",
      ["tcp", "udp", "realtime"]),

    q("computer-networks", "Slow start behaviour", "hard",
      "During TCP slow start, the congestion window:",
      ["Grows linearly per RTT", "Grows exponentially per RTT", "Stays constant", "Halves every RTT"],
      1,
      "Every ACK that acknowledges new data increases cwnd by one MSS, and the number of outstanding segments "
      "doubles each RTT - hence 'slow' start means starting small, not growing slowly. Congestion avoidance then "
      "switches to linear growth.",
      ["tcp", "congestion"]),

    # ---------------------------------------------------------------- MATHEMATICS
    q("engineering-mathematics-1", "Limit evaluation", "medium",
      "Evaluate lim (x->0) of sin(3x) / x.",
      ["0", "1", "3", "Does not exist"],
      2,
      "Write sin(3x)/x = 3 * sin(3x)/(3x). As x -> 0 the second factor tends to 1, so the limit is 3.",
      ["limits", "calculus"]),

    q("engineering-mathematics-2", "Laplace transform", "medium",
      "What is the Laplace transform of t^2?",
      ["2/s^2", "2/s^3", "1/s^3", "s^2/2"],
      1,
      "L{t^n} = n!/s^(n+1). With n = 2, that is 2!/s^3 = 2/s^3.",
      ["laplace", "transforms"]),

    q("engineering-mathematics-3", "Eigenvalue trace property", "easy",
      "The sum of the eigenvalues of a square matrix equals:",
      ["Its determinant", "Its trace", "Its rank", "Zero"],
      1,
      "The trace is the sum of the diagonal entries and also the sum of the eigenvalues, while the determinant is "
      "the product of the eigenvalues.",
      ["linear-algebra", "eigenvalues"]),

    q("discrete-mathematics", "Counting with repetition", "medium",
      "How many 4-digit numbers can be formed from {1,2,3,4,5} if repetition is allowed and the number must be even?",
      ["125", "250", "625", "500"],
      1,
      "The last digit must be 2 or 4 (2 choices); each of the other three positions has 5 choices. "
      "5 x 5 x 5 x 2 = 250.",
      ["combinatorics", "counting"]),

    q("probability-statistics", "Bayes' theorem", "hard",
      "A test for a disease with 1% prevalence has 99% sensitivity and 5% false positive rate. Given a positive result, the probability of actually having the disease is closest to:",
      ["99%", "67%", "50%", "17%"],
      3,
      "Per 10,000 people: 100 are ill and 99 test positive; of the 9,900 healthy, 495 test positive falsely. "
      "So 99 / (99 + 495) = 0.167, about 17%. This base-rate neglect is why screening tests are repeated.",
      ["bayes", "probability"]),

    # ---------------------------------------------------------------- PHYSICS / CHEM
    q("engineering-physics", "Photoelectric effect", "medium",
      "Increasing the intensity of light below the threshold frequency on a metal surface produces:",
      ["More electrons with higher kinetic energy",
       "No photoelectrons at all",
       "More electrons with the same kinetic energy",
       "Electrons after a measurable time delay"],
      1,
      "Emission depends on the photon energy h*nu exceeding the work function. Below threshold, no number of "
      "photons can eject an electron - the observation that intensity does not help was the key evidence for "
      "quantisation.",
      ["quantum", "photoelectric"]),

    q("engineering-chemistry", "Electrochemistry", "medium",
      "In a galvanic cell, oxidation occurs at the:",
      ["Cathode, which is positive", "Anode, which is negative",
       "Cathode, which is negative", "Anode, which is positive"],
      1,
      "Oxidation always occurs at the anode (the two vowels pair). In a galvanic cell the anode is the negative "
      "electrode because electrons are released there; in an electrolytic cell the anode is positive but oxidation "
      "still happens there.",
      ["electrochemistry", "galvanic"]),

    # ---------------------------------------------------------------- FLUIDS
    q("fluid-mechanics", "Bernoulli applicability", "medium",
      "Bernoulli's equation is NOT valid for which flow?",
      ["Steady, incompressible, inviscid flow along a streamline",
       "Flow through a long pipe with significant friction",
       "Irrotational flow in an open channel",
       "Flow through a Venturi meter"],
      1,
      "Friction converts mechanical energy into heat, so the mechanical energy sum is no longer constant. The "
      "engineering fix is the extended Bernoulli equation with an added head-loss term.",
      ["bernoulli", "fluid", "energy"]),

    q("fluid-mechanics", "Reynolds number", "easy",
      "Flow in a circular pipe is generally laminar when the Reynolds number is:",
      ["Below 2,300", "Between 2,300 and 4,000", "Above 4,000", "Independent of velocity"],
      0,
      "Re = rho*v*D/mu compares inertial to viscous forces. Below roughly 2,300 viscous damping suppresses "
      "disturbances; above 4,000 the flow is fully turbulent; between is the transitional band.",
      ["reynolds", "laminar", "turbulent"]),

    q("thermodynamics", "Carnot efficiency", "medium",
      "A Carnot engine operates between 500 K and 300 K. Its efficiency is:",
      ["40%", "60%", "30%", "100%"],
      0,
      "eta = 1 - T_L/T_H = 1 - 300/500 = 0.4. Temperatures must be in kelvin; using Celsius here gives a nonsense "
      "answer greater than 1.",
      ["carnot", "second-law", "efficiency"]),

    q("strength-of-materials", "Section modulus", "medium",
      "Doubling the depth of a rectangular beam section (width unchanged) changes its section modulus by a factor of:",
      ["2", "4", "8", "16"],
      1,
      "Z = b*d^2/6, so Z is proportional to d^2. Doubling d quadruples Z, which is why I-beams put material far "
      "from the neutral axis.",
      ["bending", "section-modulus"]),

    # ---------------------------------------------------------------- ECE / EEE
    q("digital-electronics", "Universal gates", "easy",
      "Which pair of gates is sufficient to implement any Boolean function?",
      ["AND and OR", "NAND and NOR", "XOR and AND", "OR and NOT only"],
      1,
      "NAND alone and NOR alone are each functionally complete: any of AND, OR and NOT can be built from either. "
      "That is why CMOS standard-cell libraries are built around them.",
      ["gates", "boolean"]),

    q("signals-systems", "Nyquist sampling", "easy",
      "A signal contains frequencies up to 4 kHz. The minimum sampling rate to avoid aliasing is:",
      ["4 kHz", "6 kHz", "8 kHz", "16 kHz"],
      2,
      "The Nyquist-Shannon theorem requires at least twice the highest frequency component: 2 x 4 kHz = 8 kHz. "
      "Telephone audio is sampled at exactly this rate.",
      ["sampling", "nyquist"]),

    q("circuit-theory", "Thevenin equivalent", "medium",
      "The Thevenin resistance seen from two terminals is found by:",
      ["Shorting all voltage sources and opening all current sources",
       "Opening all voltage sources and shorting all current sources",
       "Dividing open-circuit voltage by short-circuit current",
       "Both the first and the third method"],
      3,
      "Zeroing independent sources (voltage to short, current to open) gives R_th directly. Alternatively, "
      "R_th = V_oc / I_sc. Both are valid; the first fails only when dependent sources are present, in which case "
      "the second method or a test source is needed.",
      ["thevenin", "network-theorems"]),

    q("electrical-machines-1", "Transformer rating", "easy",
      "Transformers are rated in kVA rather than kW because:",
      ["kVA is easier to measure",
       "Copper loss depends on current and core loss on voltage, neither of which depends on power factor",
       "kW is not a valid electrical unit",
       "It is purely a historical convention"],
      1,
      "Heating in a transformer is set by voltage (core loss) and current (copper loss). The manufacturer cannot "
      "know the load's power factor, so the rating is given as the apparent power the machine can safely carry.",
      ["transformer", "rating"]),

    q("power-systems", "Transmission voltage", "medium",
      "Why is electrical power transmitted at high voltage?",
      ["To reduce the cost of conductors only",
       "Because losses scale with the square of current, and higher voltage means lower current for the same power",
       "Because high voltage is safer",
       "To increase the power factor"],
      1,
      "P = VI, so doubling the voltage halves the current, and I^2R losses fall to a quarter. That is the whole "
      "economic justification for the extra cost of insulation and substations.",
      ["transmission", "losses"]),

    # ---------------------------------------------------------------- CIVIL / CHEMICAL
    q("soil-mechanics", "Effective stress", "medium",
      "At a depth of 5 m below ground with the water table at the surface and saturated unit weight 20 kN/m^3, the effective stress is approximately:",
      ["100 kPa", "51 kPa", "49 kPa", "0 kPa"],
      1,
      "Total stress = 20 x 5 = 100 kPa. Pore pressure = 9.81 x 5 = 49 kPa. Effective stress = 100 - 49 = 51 kPa.",
      ["effective-stress", "geotech"]),

    q("process-calculations", "Tie component", "medium",
      "In a dryer balance, why is the dry solid chosen as the tie component?",
      ["Because it is the heaviest stream",
       "Because it passes through unchanged, linking the feed and product directly",
       "Because it is easy to weigh",
       "Because water cannot be measured"],
      1,
      "A tie component does not react or evaporate, so its mass is identical on both sides of the balance. That "
      "single equation links the two streams and removes one unknown immediately.",
      ["mass-balance", "tie-component"]),

    q("engineering-mechanics-fy", "Two-force member", "easy",
      "In a pin-jointed truss with loads applied only at the joints, each member is a:",
      ["Beam in bending", "Two-force member carrying axial load only",
       "Cantilever", "Torsion member"],
      1,
      "With no load between the pins, equilibrium requires the two end forces to be equal, opposite and collinear "
      "with the member axis - so the member is in pure tension or compression.",
      ["statics", "truss"]),

    q("basic-electrical", "Power factor correction", "medium",
      "Adding a capacitor bank in parallel with an inductive industrial load will:",
      ["Increase the real power consumed",
       "Reduce the supply current for the same real power",
       "Reduce the load voltage",
       "Increase the reactive power drawn from the supply"],
      1,
      "The capacitor supplies reactive power locally, so less reactive current flows through the supply cables. "
      "Real power is unchanged, apparent power falls, and I^2R losses in the feeder drop with the square of the "
      "current reduction.",
      ["power-factor", "capacitor", "ac"]),

    q("programming-fundamentals", "Recursion base case", "easy",
      "What happens if a recursive function has no reachable base case?",
      ["It returns None", "It raises a stack overflow error",
       "It runs forever without error", "The compiler rejects it"],
      1,
      "Each call consumes a stack frame. Without a base case the frames accumulate until the interpreter's "
      "recursion limit or the process stack limit is hit, producing RecursionError in Python or a segfault in C.",
      ["recursion", "stack"]),
]


# =============================================================================
# CODING PROBLEMS
# =============================================================================

def problem(slug, title, difficulty, xp, statement, examples, topics, company,
            signature, stub, solution, tests, hints, editorial, minutes=20):
    """tests: list of dicts {input, expected, stdin?}."""
    return {
        "slug": slug, "title": title, "difficulty": difficulty, "xp": xp,
        "statement": statement, "examples": examples, "topics": topics, "company": company,
        "signature": signature, "stub": stub, "solution": solution, "tests": tests,
        "hints": hints, "editorial": editorial, "minutes": minutes,
    }


CODING_PROBLEMS = [
    problem(
        "two-sum", "Two Sum", "easy", 30,
        "Given an array of integers `nums` and an integer `target`, return the **indices** of the two numbers "
        "that add up to `target`. You may assume exactly one solution exists and you may not use the same element "
        "twice. The answer may be returned in any order.\n\n"
        "Write a function `two_sum(nums, target)` that returns a list of two indices.",
        [
            {"input": "nums = [2, 7, 11, 15], target = 9", "output": "[0, 1]",
             "explain": "nums[0] + nums[1] = 2 + 7 = 9, so we return [0, 1]."},
            {"input": "nums = [3, 2, 4], target = 6", "output": "[1, 2]"},
            {"input": "nums = [3, 3], target = 6", "output": "[0, 1]"},
        ],
        ["array", "hash-table"], "Amazon, Google, Microsoft, Adobe",
        {"python": "def two_sum(nums, target):", "java": "public static int[] twoSum(int[] nums, int target)",
         "javascript": "function twoSum(nums, target) {", "cpp": "std::vector<int> twoSum(std::vector<int>& nums, int target) {"},
        {"python": "def two_sum(nums, target):\n    # Write your solution here\n    pass\n",
         "java": "import java.util.*;\n\nclass Solution {\n    public static int[] twoSum(int[] nums, int target) {\n        // Write your solution here\n        return new int[0];\n    }\n}\n",
         "javascript": "function twoSum(nums, target) {\n  // Write your solution here\n  return [];\n}\n",
         "cpp": "#include <bits/stdc++.h>\nusing namespace std;\n\nclass Solution {\npublic:\n    vector<int> twoSum(vector<int>& nums, int target) {\n        // Write your solution here\n        return {};\n    }\n};\n"},
        {"python": (
            "def two_sum(nums, target):\n"
            "    seen = {}\n"
            "    for i, value in enumerate(nums):\n"
            "        need = target - value\n"
            "        if need in seen:\n"
            "            return [seen[need], i]\n"
            "        seen[value] = i\n"
            "    return []\n"),
         "java": (
            "import java.util.*;\n\n"
            "class Solution {\n"
            "    public static int[] twoSum(int[] nums, int target) {\n"
            "        Map<Integer, Integer> seen = new HashMap<>();\n"
            "        for (int i = 0; i < nums.length; i++) {\n"
            "            int need = target - nums[i];\n"
            "            if (seen.containsKey(need)) {\n"
            "                return new int[]{seen.get(need), i};\n"
            "            }\n"
            "            seen.put(nums[i], i);\n"
            "        }\n"
            "        return new int[0];\n"
            "    }\n"
            "}\n"),
         "javascript": (
            "function twoSum(nums, target) {\n"
            "  const seen = new Map();\n"
            "  for (let i = 0; i < nums.length; i++) {\n"
            "    const need = target - nums[i];\n"
            "    if (seen.has(need)) return [seen.get(need), i];\n"
            "    seen.set(nums[i], i);\n"
            "  }\n"
            "  return [];\n"
            "}\n")},
        [
            {"input": "[2, 7, 11, 15]\n9", "expected": "[0, 1]"},
            {"input": "[3, 2, 4]\n6", "expected": "[1, 2]"},
            {"input": "[3, 3]\n6", "expected": "[0, 1]"},
            {"input": "[-1, -2, -3, -4, -5]\n-8", "expected": "[2, 4]"},
            {"input": "[0, 4, 3, 0]\n0", "expected": "[0, 3]"},
        ],
        ["A brute force solution checks every pair. What is its time complexity?",
         "If you know one number, how can you find its complement in constant time?",
         "Store each value you have seen in a hash map from value to index."],
        "The brute force approach is O(n^2): for each index i, scan every later index j. The insight is that for "
        "each element x you only need to know whether target - x has already appeared. A hash map from value to "
        "index answers that in O(1) expected time, giving a single O(n) pass with O(n) extra space. Store the "
        "index rather than a boolean so you can report positions, and check before inserting so an element is "
        "never paired with itself.",
    ),

    problem(
        "reverse-linked-list", "Reverse Linked List", "easy", 30,
        "Given the head of a singly linked list, reverse the list and return the new head.\n\n"
        "Implement `reverse_list(head)` where each node has `.value` and `.next`. Return `None` for an empty list.",
        [
            {"input": "1 -> 2 -> 3 -> 4 -> 5", "output": "5 -> 4 -> 3 -> 2 -> 1"},
            {"input": "1 -> 2", "output": "2 -> 1"},
            {"input": "[]", "output": "[]"},
        ],
        ["linked-list", "recursion", "pointers"], "Apple, Bloomberg, Oracle",
        {"python": "def reverse_list(head):"},
        {"python": (
            "class ListNode:\n"
            "    def __init__(self, value=0, nxt=None):\n"
            "        self.value = value\n"
            "        self.next = nxt\n"
            "\n"
            "\n"
            "def build(values):\n"
            "    dummy = ListNode()\n"
            "    tail = dummy\n"
            "    for v in values:\n"
            "        tail.next = ListNode(v)\n"
            "        tail = tail.next\n"
            "    return dummy.next\n"
            "\n"
            "\n"
            "def to_list(head):\n"
            "    out = []\n"
            "    while head:\n"
            "        out.append(head.value)\n"
            "        head = head.next\n"
            "    return out\n"
            "\n"
            "\n"
            "def reverse_list(head):\n"
            "    # Write your solution here\n"
            "    pass\n")},
        {"python": (
            "def reverse_list(head):\n"
            "    previous = None\n"
            "    current = head\n"
            "    while current:\n"
            "        following = current.next\n"
            "        current.next = previous\n"
            "        previous = current\n"
            "        current = following\n"
            "    return previous\n")},
        [
            {"input": "1 2 3 4 5", "expected": "5 4 3 2 1", "wrap": "list"},
            {"input": "1 2", "expected": "2 1", "wrap": "list"},
            {"input": "", "expected": "", "wrap": "list"},
            {"input": "7", "expected": "7", "wrap": "list"},
        ],
        ["How many pointers do you need to reverse one link without losing the rest of the list?",
         "Draw three boxes on paper and move the arrows by hand before writing code.",
         "The loop invariant: everything before `previous` is already reversed."],
        "Iteratively walk the list keeping three references: previous, current and the next node. Redirect "
        "current.next to previous, then advance. When current becomes None, previous is the new head. This is "
        "O(n) time and O(1) space. The recursive version is elegant but uses O(n) stack depth, which overflows "
        "for long lists - a real concern in production code.",
    ),

    problem(
        "valid-parentheses", "Valid Parentheses", "easy", 30,
        "Given a string `s` containing just the characters `(`, `)`, `{`, `}`, `[` and `]`, determine whether the "
        "string is valid. A string is valid when every opening bracket is closed by the same type of bracket and "
        "brackets close in the correct order.\n\nImplement `is_valid(s)` returning a boolean.",
        [
            {"input": "()", "output": "true"},
            {"input": "()[]{}", "output": "true"},
            {"input": "(]", "output": "false"},
            {"input": "([)]", "output": "false"},
        ],
        ["stack", "string"], "Facebook, Google, Uber",
        {"python": "def is_valid(s):"},
        {"python": "def is_valid(s):\n    # Write your solution here\n    pass\n"},
        {"python": (
            "def is_valid(s):\n"
            "    pairs = {')': '(', ']': '[', '}': '{'}\n"
            "    stack = []\n"
            "    for ch in s:\n"
            "        if ch in pairs:\n"
            "            if not stack or stack.pop() != pairs[ch]:\n"
            "                return False\n"
            "        else:\n"
            "            stack.append(ch)\n"
            "    return not stack\n")},
        [
            {"input": "()", "expected": "True"},
            {"input": "()[]{}", "expected": "True"},
            {"input": "(]", "expected": "False"},
            {"input": "([)]", "expected": "False"},
            {"input": "{[]}", "expected": "True"},
            {"input": "(", "expected": "False"},
            {"input": "", "expected": "True"},
        ],
        ["Which data structure naturally matches the most recently opened bracket?",
         "What two conditions make a closing bracket invalid?",
         "What must be true about the stack when the string ends?"],
        "A stack is the exact structure: opening brackets are pushed, and a closing bracket must match whatever "
        "is on top. A closing bracket is invalid if the stack is empty or the top does not match. At the end the "
        "stack must be empty, otherwise there are unclosed brackets. Time O(n), space O(n). The same pattern "
        "powers syntax checkers and expression parsers in real compilers.",
    ),

    problem(
        "binary-search", "Binary Search", "easy", 30,
        "Given a sorted array `nums` of distinct integers and a `target`, return the index of `target` if present, "
        "otherwise return -1. Your algorithm must run in O(log n).\n\nImplement `search(nums, target)`.",
        [
            {"input": "nums = [-1,0,3,5,9,12], target = 9", "output": "4"},
            {"input": "nums = [-1,0,3,5,9,12], target = 2", "output": "-1"},
        ],
        ["binary-search", "divide-and-conquer"], "Google, LinkedIn, Salesforce",
        {"python": "def search(nums, target):"},
        {"python": "def search(nums, target):\n    # Write your solution here\n    pass\n"},
        {"python": (
            "def search(nums, target):\n"
            "    left, right = 0, len(nums) - 1\n"
            "    while left <= right:\n"
            "        middle = (left + right) // 2\n"
            "        if nums[middle] == target:\n"
            "            return middle\n"
            "        if nums[middle] < target:\n"
            "            left = middle + 1\n"
            "        else:\n"
            "            right = middle - 1\n"
            "    return -1\n")},
        [
            {"input": "-1 0 3 5 9 12\n9", "expected": "4"},
            {"input": "-1 0 3 5 9 12\n2", "expected": "-1"},
            {"input": "5\n5", "expected": "0"},
            {"input": "2 5\n2", "expected": "0"},
            {"input": "1 2 3 4 5 6 7 8 9 10\n10", "expected": "9"},
        ],
        ["What invariant does the search window maintain?",
         "Why is `left <= right` correct but `left < right` not, for this variant?",
         "In a language with fixed-width integers, how can `(left + right) // 2` fail?"],
        "Maintain the invariant that the target, if present, lies within [left, right]. Compare the middle "
        "element and discard half the range each step, giving O(log n). The classic bug is an off-by-one in the "
        "loop condition or the update; using left <= right with middle +/- 1 keeps the window strictly shrinking "
        "and guarantees termination. In Java or C, `left + (right - left) / 2` avoids integer overflow.",
    ),

    problem(
        "merge-sorted-arrays", "Merge Sorted Array", "easy", 30,
        "Given two sorted arrays, return a new sorted array containing all elements of both.\n\n"
        "Implement `merge_sorted(a, b)` returning a list.",
        [
            {"input": "a = [1,3,5], b = [2,4,6]", "output": "[1,2,3,4,5,6]"},
            {"input": "a = [], b = [1]", "output": "[1]"},
        ],
        ["array", "two-pointers", "merge-sort"], "Microsoft, Indeed",
        {"python": "def merge_sorted(a, b):"},
        {"python": "def merge_sorted(a, b):\n    # Write your solution here\n    pass\n"},
        {"python": (
            "def merge_sorted(a, b):\n"
            "    result = []\n"
            "    i = j = 0\n"
            "    while i < len(a) and j < len(b):\n"
            "        if a[i] <= b[j]:\n"
            "            result.append(a[i])\n"
            "            i += 1\n"
            "        else:\n"
            "            result.append(b[j])\n"
            "            j += 1\n"
            "    result.extend(a[i:])\n"
            "    result.extend(b[j:])\n"
            "    return result\n")},
        [
            {"input": "1 3 5\n2 4 6", "expected": "1 2 3 4 5 6", "wrap": "two-lists"},
            {"input": "\n1", "expected": "1", "wrap": "two-lists"},
            {"input": "1 2 3\n", "expected": "1 2 3", "wrap": "two-lists"},
            {"input": "-5 0 7\n-3 -3 9", "expected": "-5 -3 -3 0 7 9", "wrap": "two-lists"},
        ],
        ["Compare the two front elements. What should you do with the smaller one?",
         "What happens when one array runs out first?"],
        "Walk both arrays with two pointers, always emitting the smaller front element. When one array is "
        "exhausted, append the remainder of the other. This is the merge step of merge sort: O(n + m) time and "
        "O(n + m) space, and it is stable if you break ties in favour of the left array.",
    ),

    problem(
        "fizzbuzz", "FizzBuzz", "easy", 20,
        "Return a list of strings for the integers from 1 to `n`. For multiples of three print `Fizz`, for "
        "multiples of five print `Buzz`, and for multiples of both print `FizzBuzz`. Otherwise print the number "
        "as a string.\n\nImplement `fizz_buzz(n)`.",
        [{"input": "n = 5", "output": "['1','2','Fizz','4','Buzz']"},
         {"input": "n = 15", "output": "[... 'FizzBuzz'] at 15"}],
        ["math", "simulation"], "Every screening round ever held",
        {"python": "def fizz_buzz(n):"},
        {"python": "def fizz_buzz(n):\n    # Write your solution here\n    pass\n"},
        {"python": (
            "def fizz_buzz(n):\n"
            "    out = []\n"
            "    for i in range(1, n + 1):\n"
            "        if i % 15 == 0:\n"
            "            out.append('FizzBuzz')\n"
            "        elif i % 3 == 0:\n"
            "            out.append('Fizz')\n"
            "        elif i % 5 == 0:\n"
            "            out.append('Buzz')\n"
            "        else:\n"
            "            out.append(str(i))\n"
            "    return out\n")},
        [
            {"input": "5", "expected": "1 2 Fizz 4 Buzz", "wrap": "lines"},
            {"input": "15", "expected": "1 2 Fizz 4 Buzz Fizz 7 8 Fizz Buzz 11 Fizz 13 14 FizzBuzz", "wrap": "lines"},
            {"input": "1", "expected": "1", "wrap": "lines"},
        ],
        ["Check divisibility by 15 first - why does order matter here?"],
        "The order of checks matters: testing 15 (or equivalently 3 and 5 together) before the individual cases "
        "prevents 'Fizz' from swallowing the multiples of 15. A common production-grade variant builds the string "
        "by concatenation so new rules can be added without restructuring the conditionals.",
    ),

    problem(
        "maximum-subarray", "Maximum Subarray", "medium", 50,
        "Given an integer array `nums`, find the contiguous subarray with the largest sum and return that sum.\n\n"
        "Implement `max_sub_array(nums)`. The array may contain negative numbers and the answer may be negative.",
        [
            {"input": "[-2,1,-3,4,-1,2,1,-5,4]", "output": "6", "explain": "The subarray [4,-1,2,1] sums to 6."},
            {"input": "[1]", "output": "1"},
            {"input": "[-3,-1,-2]", "output": "-1"},
        ],
        ["dynamic-programming", "divide-and-conquer", "kadane"], "Google, Amazon, Apple",
        {"python": "def max_sub_array(nums):"},
        {"python": "def max_sub_array(nums):\n    # Write your solution here\n    pass\n"},
        {"python": (
            "def max_sub_array(nums):\n"
            "    best = current = nums[0]\n"
            "    for value in nums[1:]:\n"
            "        current = max(value, current + value)\n"
            "        best = max(best, current)\n"
            "    return best\n")},
        [
            {"input": "-2 1 -3 4 -1 2 1 -5 4", "expected": "6"},
            {"input": "1", "expected": "1"},
            {"input": "-3 -1 -2", "expected": "-1"},
            {"input": "5 4 -1 7 8", "expected": "23"},
            {"input": "-1", "expected": "-1"},
        ],
        ["At each position, what is the best subarray that ENDS there?",
         "When is it better to start a fresh subarray than to extend the previous one?",
         "Can you do it in one pass with constant extra space?"],
        "Kadane's algorithm keeps the best sum of a subarray ending at each index. That value is either the "
        "element alone or the element plus the previous best - so `current = max(x, current + x)`. Track the "
        "global maximum alongside it. O(n) time, O(1) space. Initialise with the first element rather than zero "
        "so an all-negative array returns its largest (least negative) value.",
    ),

    problem(
        "lru-cache", "LRU Cache", "hard", 80,
        "Design a data structure that follows the Least Recently Used eviction policy. Implement a class "
        "`LRUCache` with a constructor taking `capacity`, a `get(key)` method returning the value or -1, and a "
        "`put(key, value)` method that inserts or updates and evicts the least recently used entry when the "
        "capacity is exceeded. Both operations must run in O(1) average time.",
        [
            {"input": "LRUCache(2); put(1,1); put(2,2); get(1); put(3,3); get(2)", "output": "1 then -1"},
        ],
        ["hash-table", "linked-list", "design"], "Amazon, Microsoft, Snapchat, Netflix",
        {"python": "class LRUCache:"},
        {"python": (
            "class LRUCache:\n"
            "    def __init__(self, capacity):\n"
            "        pass\n"
            "\n"
            "    def get(self, key):\n"
            "        pass\n"
            "\n"
            "    def put(self, key, value):\n"
            "        pass\n")},
        {"python": (
            "from collections import OrderedDict\n"
            "\n"
            "\n"
            "class LRUCache:\n"
            "    def __init__(self, capacity):\n"
            "        self.capacity = capacity\n"
            "        self.store = OrderedDict()\n"
            "\n"
            "    def get(self, key):\n"
            "        if key not in self.store:\n"
            "            return -1\n"
            "        self.store.move_to_end(key)\n"
            "        return self.store[key]\n"
            "\n"
            "    def put(self, key, value):\n"
            "        if key in self.store:\n"
            "            self.store.move_to_end(key)\n"
            "        self.store[key] = value\n"
            "        if len(self.store) > self.capacity:\n"
            "            self.store.popitem(last=False)\n")},
        [
            {"input": "2\nput 1 1\nput 2 2\nget 1\nput 3 3\nget 2\nget 3", "expected": "1 -1 3", "wrap": "lru"},
            {"input": "1\nput 2 1\nget 2\nput 3 2\nget 2\nget 3", "expected": "1 -1 2", "wrap": "lru"},
        ],
        ["Which two data structures, combined, give O(1) lookup AND O(1) reordering?",
         "Where in the order should a freshly accessed key go?",
         "Python's OrderedDict already maintains insertion order - use it."],
        "You need constant-time lookup (hash map) plus constant-time move-to-front and eviction (doubly linked "
        "list). Hand-rolling the linked list with a hash map from key to node is the interview-expected answer. "
        "In production, Python's OrderedDict, Java's LinkedHashMap with accessOrder=true, or a language cache "
        "library does exactly this. The same structure underpins CPU cache replacement, database buffer pools and "
        "CDN eviction.",
    ),

    problem(
        "detect-cycle", "Linked List Cycle", "easy", 30,
        "Given the head of a linked list, determine whether the list contains a cycle. A cycle exists if some node "
        "can be reached again by following `next` pointers.\n\nImplement `has_cycle(head)` returning a boolean.",
        [
            {"input": "3 -> 2 -> 0 -> -4 -> (back to node 2)", "output": "true"},
            {"input": "1 -> 2", "output": "false"},
        ],
        ["linked-list", "two-pointers"], "Microsoft, Oracle, Yahoo",
        {"python": "def has_cycle(head):"},
        {"python": (
            "class ListNode:\n"
            "    def __init__(self, value=0, nxt=None):\n"
            "        self.value = value\n"
            "        self.next = nxt\n"
            "\n"
            "\n"
            "def has_cycle(head):\n"
            "    # Write your solution here\n"
            "    pass\n")},
        {"python": (
            "def has_cycle(head):\n"
            "    slow = fast = head\n"
            "    while fast and fast.next:\n"
            "        slow = slow.next\n"
            "        fast = fast.next.next\n"
            "        if slow is fast:\n"
            "            return True\n"
            "    return False\n")},
        [
            {"input": "1 2 3 2", "expected": "True", "wrap": "cycle"},
            {"input": "1 2", "expected": "False", "wrap": "cycle"},
            {"input": "1 1", "expected": "True", "wrap": "cycle"},
            {"input": "", "expected": "False", "wrap": "cycle"},
        ],
        ["Can you detect a cycle without modifying the list or using extra memory?",
         "Imagine two runners on a circular track, one twice as fast."],
        "Floyd's tortoise and hare: advance one pointer by one step and another by two. In an acyclic list the "
        "fast pointer reaches the end; in a cyclic list the two must eventually meet, because the gap closes by "
        "one each iteration. O(n) time, O(1) space - strictly better than the hash-set approach, which costs "
        "O(n) memory.",
    ),

    problem(
        "longest-substring", "Longest Substring Without Repeating Characters", "medium", 50,
        "Given a string `s`, return the length of the longest substring that contains no repeated characters.\n\n"
        "Implement `length_of_longest_substring(s)`.",
        [
            {"input": "abcabcbb", "output": "3", "explain": "The answer is 'abc' with length 3."},
            {"input": "bbbbb", "output": "1"},
            {"input": "pwwkew", "output": "3"},
        ],
        ["sliding-window", "hash-table", "string"], "Amazon, Bloomberg, Adobe",
        {"python": "def length_of_longest_substring(s):"},
        {"python": "def length_of_longest_substring(s):\n    # Write your solution here\n    pass\n"},
        {"python": (
            "def length_of_longest_substring(s):\n"
            "    last = {}\n"
            "    start = best = 0\n"
            "    for index, ch in enumerate(s):\n"
            "        if ch in last and last[ch] >= start:\n"
            "            start = last[ch] + 1\n"
            "        last[ch] = index\n"
            "        best = max(best, index - start + 1)\n"
            "    return best\n")},
        [
            {"input": "abcabcbb", "expected": "3"},
            {"input": "bbbbb", "expected": "1"},
            {"input": "pwwkew", "expected": "3"},
            {"input": "", "expected": "0"},
            {"input": "dvdf", "expected": "3"},
        ],
        ["Maintain a window with no duplicates. When you see a duplicate, where must the left edge move?",
         "Store the last index of each character instead of removing characters one by one."],
        "Slide a window [start, index] over the string, keeping a map from character to its most recent index. On "
        "a repeat inside the window, jump start past that occurrence rather than shrinking one step at a time - "
        "that is what turns an O(n^2) solution into O(n). The `last[ch] >= start` guard prevents an out-of-window "
        "occurrence from dragging start backwards, which is the bug in most first attempts.",
    ),

    problem(
        "coin-change", "Coin Change", "medium", 50,
        "Given an array of coin denominations and a total `amount`, return the fewest coins needed to make that "
        "amount, or -1 if it cannot be made. You have an unlimited supply of each coin.\n\n"
        "Implement `coin_change(coins, amount)`.",
        [
            {"input": "coins = [1,2,5], amount = 11", "output": "3", "explain": "5 + 5 + 1 = 11, three coins."},
            {"input": "coins = [2], amount = 3", "output": "-1"},
            {"input": "coins = [1], amount = 0", "output": "0"},
        ],
        ["dynamic-programming", "breadth-first-search"], "Google, Uber, Airbnb",
        {"python": "def coin_change(coins, amount):"},
        {"python": "def coin_change(coins, amount):\n    # Write your solution here\n    pass\n"},
        {"python": (
            "def coin_change(coins, amount):\n"
            "    unreachable = amount + 1\n"
            "    table = [unreachable] * (amount + 1)\n"
            "    table[0] = 0\n"
            "    for value in range(1, amount + 1):\n"
            "        for coin in coins:\n"
            "            if coin <= value:\n"
            "                table[value] = min(table[value], table[value - coin] + 1)\n"
            "    return -1 if table[amount] > amount else table[amount]\n")},
        [
            {"input": "1 2 5\n11", "expected": "3"},
            {"input": "2\n3", "expected": "-1"},
            {"input": "1\n0", "expected": "0"},
            {"input": "186 419 83 408\n6249", "expected": "20"},
        ],
        ["Greedy does not work - why not? Try coins [1, 3, 4] with amount 6.",
         "Define dp[x] as the fewest coins for amount x. How does dp[x] relate to smaller amounts?",
         "Initialise unreachable states to amount + 1, not infinity, so the comparison stays simple."],
        "Greedy fails: with coins [1,3,4] and amount 6, greedy picks 4+1+1 but the optimum is 3+3. Build a bottom-up "
        "table where dp[x] = 1 + min(dp[x - coin]) over all usable coins, with dp[0] = 0. Time is O(amount x |coins|) "
        "and space O(amount). This is an unbounded knapsack in disguise, and the same table answers every amount "
        "up to the target in one pass.",
    ),

    problem(
        "level-order-traversal", "Binary Tree Level Order Traversal", "medium", 50,
        "Given the root of a binary tree, return the level order traversal of its node values - that is, all nodes "
        "at depth 0, then depth 1, and so on, each level as its own list.\n\nImplement `level_order(root)` "
        "returning a list of lists.",
        [
            {"input": "    3\n   / \\\n  9  20\n     / \\\n    15  7", "output": "[[3],[9,20],[15,7]]"},
        ],
        ["tree", "breadth-first-search", "binary-tree"], "Amazon, LinkedIn, Bloomberg",
        {"python": "def level_order(root):"},
        {"python": (
            "class TreeNode:\n"
            "    def __init__(self, value=0, left=None, right=None):\n"
            "        self.value = value\n"
            "        self.left = left\n"
            "        self.right = right\n"
            "\n"
            "\n"
            "def build(values):\n"
            "    \"\"\"Build a tree from a level-order list using None for missing nodes.\"\"\"\n"
            "    if not values:\n"
            "        return None\n"
            "    from collections import deque\n"
            "    root = TreeNode(values[0])\n"
            "    queue = deque([root])\n"
            "    index = 1\n"
            "    while queue and index < len(values):\n"
            "        node = queue.popleft()\n"
            "        if index < len(values):\n"
            "            if values[index] is not None:\n"
            "                node.left = TreeNode(values[index])\n"
            "                queue.append(node.left)\n"
            "            index += 1\n"
            "        if index < len(values):\n"
            "            if values[index] is not None:\n"
            "                node.right = TreeNode(values[index])\n"
            "                queue.append(node.right)\n"
            "            index += 1\n"
            "    return root\n"
            "\n"
            "\n"
            "def level_order(root):\n"
            "    # Write your solution here\n"
            "    pass\n")},
        {"python": (
            "from collections import deque\n"
            "\n"
            "\n"
            "def level_order(root):\n"
            "    if not root:\n"
            "        return []\n"
            "    result = []\n"
            "    queue = deque([root])\n"
            "    while queue:\n"
            "        level = []\n"
            "        for _ in range(len(queue)):\n"
            "            node = queue.popleft()\n"
            "            level.append(node.value)\n"
            "            if node.left:\n"
            "                queue.append(node.left)\n"
            "            if node.right:\n"
            "                queue.append(node.right)\n"
            "        result.append(level)\n"
            "    return result\n")},
        [
            {"input": "3 9 20 None None 15 7", "expected": "[[3], [9, 20], [15, 7]]", "wrap": "tree"},
            {"input": "1", "expected": "[[1]]", "wrap": "tree"},
            {"input": "", "expected": "[]", "wrap": "tree"},
        ],
        ["BFS processes nodes level by level. How do you know when one level ends?",
         "Snapshot the queue size at the start of each iteration - that is exactly the width of the current level."],
        "Standard BFS with one refinement: capture len(queue) before draining, then process exactly that many "
        "nodes. That boundary is what separates levels. Time O(n), space O(w) where w is the maximum width - for a "
        "balanced tree that is O(n), which matters when choosing BFS over DFS on very wide trees.",
    ),

    problem(
        "dijkstra-shortest-path", "Shortest Path (Dijkstra)", "hard", 80,
        "Given a weighted directed graph as an adjacency list `graph` mapping a node to a list of "
        "`(neighbour, weight)` pairs, a `start` node and an `end` node, return the length of the shortest path. "
        "Return -1 if no path exists. All weights are non-negative.\n\nImplement `shortest_path(graph, start, end)`.",
        [
            {"input": "graph = {'A': [('B', 1), ('C', 4)], 'B': [('C', 2), ('D', 5)], 'C': [('D', 1)], 'D': []}, "
                     "start = 'A', end = 'D'", "output": "4"},
        ],
        ["graph", "dijkstra", "heap", "greedy"], "Google, Uber, Flipkart",
        {"python": "def shortest_path(graph, start, end):"},
        {"python": "def shortest_path(graph, start, end):\n    # Write your solution here\n    pass\n"},
        {"python": (
            "import heapq\n"
            "\n"
            "\n"
            "def shortest_path(graph, start, end):\n"
            "    distances = {start: 0}\n"
            "    heap = [(0, start)]\n"
            "    while heap:\n"
            "        cost, node = heapq.heappop(heap)\n"
            "        if node == end:\n"
            "            return cost\n"
            "        if cost > distances.get(node, float('inf')):\n"
            "            continue\n"
            "        for neighbour, weight in graph.get(node, []):\n"
            "            candidate = cost + weight\n"
            "            if candidate < distances.get(neighbour, float('inf')):\n"
            "                distances[neighbour] = candidate\n"
            "                heapq.heappush(heap, (candidate, neighbour))\n"
            "    return -1\n")},
        [
            {"input": "A:B1,C4\nB:C2,D5\nC:D1\nD:\nA\nD", "expected": "4", "wrap": "graph"},
            {"input": "A:B2\nB:\nA\nB", "expected": "2", "wrap": "graph"},
            {"input": "A:B1\nB:\nC:A1\nA\nC", "expected": "-1", "wrap": "graph"},
        ],
        ["Greedy choice: which node's distance is final the moment you first reach it?",
         "A min-heap lets you always extract the currently closest unvisited node.",
         "Why can stale entries remain in the heap, and how do you ignore them?"],
        "Dijkstra repeatedly settles the closest unsettled node; with non-negative weights that distance is final "
        "once popped. A binary heap gives O((V + E) log V). Lazy deletion - skipping a popped entry whose cost "
        "exceeds the recorded distance - avoids the cost of a decrease-key operation. Bellman-Ford is required "
        "when negative weights appear, and A* adds a heuristic to steer the search.",
    ),
]

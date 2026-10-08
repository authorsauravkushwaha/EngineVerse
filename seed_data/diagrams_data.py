"""Per-topic diagrams for EngineVerse notes.

Every entry here is a *scene* for `engineverse.diagrams`, not markup: a list of
primitives with numbers and plain strings. `diagrams.render()` validates it and
rebuilds the SVG, so nothing in this file can inject script and a malformed
entry raises at seed time instead of drawing a half-diagram.

Each topic gets one diagram chosen to answer the question a student actually
asks first, with two to four hotspots that expand the part worth explaining.
The six hand-written diagrams that shipped earlier are replaced by these so
every topic uses one code path.

Canvas is 640 wide. Height varies with what is being drawn.
"""

from __future__ import annotations

from backend.engineverse import diagrams as D
from backend.engineverse.diagrams import arrow, box, hotspot, label, polyline

INK = "#334155"
MUTED = "#64748b"
BLUE = "#4f7cff"
GREEN = "#10b981"
RED = "#ef4444"
AMBER = "#f59e0b"
VIOLET = "#8b5cf6"
FILL_SOFT = "#eef2ff"
FILL_GREEN = "#ecfdf5"
FILL_AMBER = "#fffbeb"


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

def _arrays():
    cells = []
    for i in range(6):
        cells += box(60 + i * 72, 90, 72, 56, str([4, 9, 1, 7, 3, 8][i]),
                     fill=FILL_SOFT, stroke=BLUE, size=16, rx=2)
        cells.append(label(60 + i * 72 + 36, 168, str(i), size=12,
                           anchor="middle", fill=MUTED))
    cells.append(label(60, 74, "index", size=11, fill=MUTED))
    return {
        "title": "An array is one contiguous block, so an index is just an offset",
        "caption": "Every element sits next to the last, which is what makes indexed "
                   "access a single multiply and add.",
        "label": "Array of six integers stored in consecutive memory, with index labels below",
        "width": 640, "height": 230,
        "objects": cells + [
            arrow(24, 118, 56, 118, stroke=INK),
            label(6, 106, "base", size=11, fill=INK),
            label(60, 200, "address of a[i] = base + i * size_of(element)",
                  size=14, weight=600, fill=INK),
            label(60, 218, "size_of(int) = 4 bytes, so a[3] sits at base + 12 - no search needed",
                  size=11.5, fill=MUTED),
        ],
        "hotspots": [
            hotspot(276, 90, 72, 56, "a[3] in O(1)",
                    "The address is computed, not found. Jump straight to base + 3*4 and read. "
                    "This is the whole advantage an array has over a linked list."),
            hotspot(420, 90, 72, 56, "No spare room",
                    "Appending past the last cell needs a bigger block and a full copy, which is "
                    "why amortised append is O(1) but a single resize can be O(n)."),
        ],
    }


def _linked_lists():
    out = []
    values = [10, 20, 30]
    for i, value in enumerate(values):
        x = 120 + i * 170
        out += box(x, 100, 92, 52, str(value), fill=FILL_SOFT, stroke=BLUE, size=16, rx=4)
        out += box(x + 92, 100, 44, 52, "", stroke=BLUE, rx=4)
        out.append(label(x + 114, 130, "*", size=15, anchor="middle", fill=BLUE))
        if i < len(values) - 1:
            out.append(arrow(x + 136, 126, x + 170, 126, stroke=INK))
    out.append(arrow(460 + 136 - 170, 126, 640 - 120, 126, stroke=INK))
    out += box(640 - 118, 100, 76, 52, "NULL", fill="#f1f5f9", stroke=MUTED, size=13)
    out.append(arrow(30, 126, 116, 126, stroke=GREEN))
    out.append(label(12, 114, "head", size=12, fill=GREEN, weight=600))
    return {
        "title": "Each node carries its own pointer to the next",
        "caption": "Nodes can sit anywhere in memory; the chain is the pointers, not the layout.",
        "label": "Singly linked list of three nodes ending in NULL, with a head pointer",
        "width": 640, "height": 230,
        "objects": out + [
            label(120, 84, "value", size=11, fill=MUTED),
            label(212, 84, "next", size=11, fill=MUTED),
            label(120, 190, "Insert at the head: point the new node at the old head, then move head. O(1).",
                  size=12.5, fill=INK),
            label(120, 208, "Find a value: follow pointers from the head until you hit it or NULL. O(n).",
                  size=12.5, fill=MUTED),
        ],
        "hotspots": [
            hotspot(290, 100, 44, 52, "The next pointer",
                    "This single field is what makes the structure a list. Losing it orphans every "
                    "node after it, which is why deletion must copy the pointer before freeing."),
            hotspot(12, 100, 100, 52, "head",
                    "The only handle on the list. If head is lost the whole chain leaks, because "
                    "nothing else references the first node."),
        ],
    }


def _stacks_queues():
    out = []
    for i, value in enumerate(["C", "B", "A"]):
        out += box(60, 70 + i * 52, 120, 52, value, fill=FILL_SOFT, stroke=BLUE, size=15, rx=3)
    out += box(60, 70 + 3 * 52, 120, 4, "", stroke="#cbd5e1", rx=1)
    out.append(label(120, 254, "stack - LIFO", size=13, anchor="middle", weight=600, fill=INK))
    out.append(arrow(200, 96, 186, 96, stroke=GREEN))
    out.append(label(206, 100, "push / pop", size=11, fill=GREEN))
    out.append(arrow(40, 96, 54, 96, stroke=RED))
    out.append(label(4, 88, "top", size=11, fill=RED))

    for i, value in enumerate(["1", "2", "3"]):
        out += box(330 + i * 92, 70, 92, 52, value, fill=FILL_GREEN, stroke=GREEN, size=15, rx=3)
    out.append(label(468, 148, "queue - FIFO", size=13, anchor="middle", weight=600, fill=INK))
    out.append(arrow(300, 96, 326, 96, stroke=GREEN))
    out.append(label(268, 88, "enqueue", size=11, fill=GREEN))
    out.append(arrow(610, 96, 636, 96, stroke=RED))
    out.append(label(600, 132, "dequeue", size=11, fill=RED, anchor="end"))
    out.append(label(330, 58, "front", size=11, fill=MUTED))
    out.append(label(580, 58, "rear", size=11, fill=MUTED))
    return {
        "title": "A stack serves the newest item first; a queue serves the oldest",
        "caption": "Same cells, opposite ends. Which end you remove from is the entire difference.",
        "label": "A stack with push and pop at the top beside a queue with enqueue at the rear and dequeue at the front",
        "width": 640, "height": 270,
        "objects": out + [
            label(60, 190, "Stack: undo history, call frames, bracket matching, DFS.", size=12, fill=INK),
            label(330, 190, "Queue: print spooling, CPU scheduling, BFS, buffers.", size=12, fill=INK),
            label(60, 214, "Both are O(1) per operation - neither one searches.", size=12, fill=MUTED),
        ],
        "hotspots": [
            hotspot(60, 70, 120, 52, "Top of the stack",
                    "Push and pop both touch only this cell, which is why both are O(1). A recursion "
                    "with no base case keeps pushing here until the frame limit is hit."),
            hotspot(330, 70, 92, 52, "Front of the queue",
                    "The element that has waited longest leaves first. Fairness is the property, and "
                    "it is why a queue is the right shape for a scheduler."),
        ],
    }


def _binary_trees():
    nodes = {"r": (300, 60), "l": (190, 140), "rr": (410, 140), "ll": (120, 220), "lr": (260, 220)}
    edges = [("r", "l"), ("r", "rr"), ("l", "ll"), ("l", "lr")]
    out = []
    for parent, child in edges:
        px, py = nodes[parent]
        cx, cy = nodes[child]
        out.append({"kind": "line", "x1": px, "y1": py + 18, "x2": cx, "y2": cy - 18,
                    "stroke": MUTED, "width": 1.4})
    for key, (x, y) in nodes.items():
        out += {"r": [], "l": [], "rr": [], "ll": [], "lr": []}[key]
        out += box(x - 22, y - 18, 44, 36, str({"r": 1, "l": 2, "rr": 3, "ll": 4, "lr": 5}[key]),
                   fill=FILL_SOFT, stroke=BLUE, size=14, rx=18)
    order = [("ll", 4), ("l", 2), ("lr", 5), ("r", 1), ("rr", 3)]
    for i, (key, value) in enumerate(order):
        x, y = nodes[key]
        out.append(label(x + 30, y + 5, f"{i + 1}", size=12, fill=GREEN, weight=700))
    return {
        "title": "In-order walks left subtree, then node, then right subtree",
        "caption": "Green numbers show the visit order: 4, 2, 5, 1, 3.",
        "label": "Binary tree of five nodes with in-order traversal visit numbers",
        "width": 640, "height": 300,
        "objects": out + [
            label(60, 278, "In-order   4 2 5 1 3     - sorted output on a binary search tree",
                  size=13, weight=600, fill=GREEN),
            label(60, 296, "Pre-order  1 2 4 5 3     Post-order 4 5 2 3 1     Level-order 1 2 3 4 5",
                  size=11.5, fill=MUTED),
        ],
        "hotspots": [
            hotspot(98, 202, 44, 36, "Visited first",
                    "In-order recurses as far left as it can before printing anything. The leftmost "
                    "node of a BST is therefore its smallest element."),
            hotspot(278, 42, 44, 36, "Root printed fourth",
                    "The root waits until its whole left subtree is done. On a BST that means every "
                    "smaller value has already been printed, so the output comes out sorted."),
        ],
    }


def _bst():
    nodes = {50: (300, 56), 30: (190, 130), 70: (410, 130), 20: (120, 204), 40: (258, 204)}
    out = []
    for parent, child in [(50, 30), (50, 70), (30, 20), (30, 40)]:
        px, py = nodes[parent]
        cx, cy = nodes[child]
        out.append({"kind": "line", "x1": px, "y1": py + 18, "x2": cx, "y2": cy - 18,
                    "stroke": MUTED, "width": 1.4})
    for value, (x, y) in nodes.items():
        on_path = value in (50, 30, 40)
        out += box(x - 22, y - 18, 44, 36, str(value),
                   fill=FILL_AMBER if on_path else FILL_SOFT,
                   stroke=AMBER if on_path else BLUE, size=14, rx=18)
    out.append(label(150, 50, "left subtree: all < 50", size=11.5, fill=MUTED))
    out.append(label(430, 50, "right subtree: all > 50", size=11.5, fill=MUTED))
    out.append(arrow(330, 90, 360, 108, stroke=AMBER, width=2.4))
    out.append(arrow(214, 158, 236, 176, stroke=AMBER, width=2.4))
    return {
        "title": "Searching a BST discards half the remaining tree at every step",
        "caption": "Looking for 40: 40 < 50 go left, 40 > 30 go right, found. Three comparisons.",
        "label": "Binary search tree with the search path to 40 highlighted in amber",
        "width": 640, "height": 280,
        "objects": out + [
            label(60, 254, "The invariant is the whole data structure: left < node < right, at every node.",
                  size=12.5, weight=600, fill=INK),
            label(60, 272, "Height h gives O(h) search. Balanced h = log n; a sorted insert degenerates to O(n).",
                  size=11.5, fill=MUTED),
        ],
        "hotspots": [
            hotspot(278, 38, 44, 36, "One comparison halves the search",
                    "Comparing with 50 rules out the entire right subtree at once. That is the same "
                    "reasoning as binary search on a sorted array, applied to a tree."),
            hotspot(236, 186, 44, 36, "Degenerate case",
                    "Insert 1, 2, 3, 4, 5 in order and every node becomes a right child. The tree "
                    "turns into a linked list and search falls back to O(n) - which is what AVL and "
                    "red-black trees exist to prevent."),
        ],
    }


def _graphs():
    nodes = {"A": (90, 70), "B": (220, 50), "C": (180, 160), "D": (330, 110), "E": (430, 60), "F": (400, 190)}
    edges = [("A", "B"), ("A", "C"), ("B", "D"), ("C", "D"), ("D", "E"), ("D", "F"), ("C", "F")]
    out = []
    for u, v in edges:
        ux, uy = nodes[u]
        vx, vy = nodes[v]
        out.append({"kind": "line", "x1": ux, "y1": uy, "x2": vx, "y2": vy,
                    "stroke": MUTED, "width": 1.3})
    bfs_order = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6}
    for key, (x, y) in nodes.items():
        out += box(x - 18, y - 18, 36, 36, key, fill=FILL_SOFT, stroke=BLUE, size=13, rx=18)
        out.append(label(x + 22, y - 8, str(bfs_order[key]), size=11, fill=GREEN, weight=700))
    return {
        "title": "BFS visits by distance from the start; DFS dives as deep as it can",
        "caption": "Green numbers are BFS order from A. DFS would go A, B, D, C, F, E instead.",
        "label": "Undirected graph of six nodes with breadth-first visit order from A",
        "width": 640, "height": 270,
        "objects": out + [
            label(60, 240, "BFS uses a queue and finds the shortest path in an unweighted graph.",
                  size=12.5, weight=600, fill=GREEN),
            label(60, 258, "DFS uses a stack (or recursion) and is the basis of cycle detection and topological sort.",
                  size=11.5, fill=MUTED),
        ],
        "hotspots": [
            hotspot(312, 92, 36, 36, "Why D comes before E",
                    "D is one edge from B and C, both of which are one edge from A, so D is at distance 2. "
                    "E is at distance 3. BFS finishes an entire distance level before starting the next."),
            hotspot(72, 52, 36, 36, "The visited set",
                    "A graph has cycles, so without marking visited nodes BFS would loop forever between "
                    "A and B. This is the one thing that separates graph traversal from tree traversal."),
        ],
    }


def _hash_tables():
    out = []
    for i, key in enumerate(["cat", "dog", "owl", "emu"]):
        y = 50 + i * 40
        out += box(40, y, 78, 32, key, fill=FILL_SOFT, stroke=BLUE, size=12, rx=4)
        out.append(arrow(122, y + 16, 176, y + 16, stroke=MUTED, width=1.3))
    out += box(180, 66, 120, 32, "hash(key) % 4", fill="#f8fafc", stroke=MUTED, size=12)
    for i in range(4):
        y = 46 + i * 46
        out += box(360, y, 52, 34, str(i), fill="#f1f5f9", stroke=MUTED, size=12, rx=3)
    out += box(412, 46, 96, 34, "cat", fill=FILL_SOFT, stroke=BLUE, size=12, rx=3)
    out += box(412, 92, 96, 34, "dog", fill=FILL_SOFT, stroke=BLUE, size=12, rx=3)
    out += box(412, 138, 96, 34, "owl  ->  emu", fill=FILL_AMBER, stroke=AMBER, size=12, rx=3)
    out.append(arrow(300, 82, 356, 63, stroke=MUTED, width=1.3))
    out.append(arrow(300, 122, 356, 109, stroke=MUTED, width=1.3))
    out.append(arrow(300, 162, 356, 155, stroke=MUTED, width=1.3))
    out.append(arrow(300, 202, 356, 160, stroke=AMBER, width=1.6))
    return {
        "title": "A hash turns the key into a bucket index, so lookup skips the search",
        "caption": "cat, dog and owl land in their own buckets. emu hashes to the same bucket as owl "
                   "and chains behind it.",
        "label": "Hash table with four keys hashing into four buckets, one collision chained",
        "width": 640, "height": 250,
        "objects": out + [
            label(40, 224, "Average lookup O(1): compute the bucket, read it. No comparison until the bucket is reached.",
                  size=12, weight=600, fill=INK),
            label(40, 242, "Worst case O(n): every key in one bucket. A good hash spread is what prevents that.",
                  size=11.5, fill=MUTED),
        ],
        "hotspots": [
            hotspot(412, 138, 96, 34, "Collision chain",
                    "Two different keys mapped to bucket 2. Chaining keeps both by linking them, so "
                    "lookup in that bucket degrades to a short scan. Open addressing would probe the "
                    "next free slot instead."),
            hotspot(180, 66, 120, 32, "The hash function",
                    "Everything depends on this spreading keys evenly. A hash that returns key length "
                    "would put every three-letter key in the same bucket and destroy the O(1)."),
        ],
    }


def _heaps():
    nodes = {90: (300, 56), 70: (190, 126), 80: (410, 126), 30: (120, 196), 50: (258, 196)}
    out = []
    for parent, child in [(90, 70), (90, 80), (70, 30), (70, 50)]:
        px, py = nodes[parent]
        cx, cy = nodes[child]
        out.append({"kind": "line", "x1": px, "y1": py + 18, "x2": cx, "y2": cy - 18,
                    "stroke": MUTED, "width": 1.4})
    for value, (x, y) in nodes.items():
        out += box(x - 22, y - 18, 44, 36, str(value),
                   fill=FILL_AMBER if value == 90 else FILL_SOFT,
                   stroke=AMBER if value == 90 else BLUE, size=14, rx=18)
    values = [90, 70, 80, 30, 50]
    for i, value in enumerate(values):
        out += box(120 + i * 62, 250, 62, 34, str(value), fill="#f8fafc", stroke=MUTED, size=13, rx=3)
        out.append(label(120 + i * 62 + 31, 298, str(i), size=10.5, anchor="middle", fill=MUTED))
    return {
        "title": "A max-heap keeps the largest value at the root, stored as a flat array",
        "caption": "The tree is only a way of reading the array: a node at index i has children at "
                   "2i+1 and 2i+2.",
        "label": "Max-heap shown as a tree and as the underlying array",
        "width": 640, "height": 320,
        "objects": out + [
            label(60, 240, "Parent at i, children at 2i+1 and 2i+2 - no pointers needed.",
                  size=12, weight=600, fill=INK),
        ],
        "hotspots": [
            hotspot(278, 38, 44, 36, "Root is the max",
                    "The only guarantee a heap makes is parent >= child. It does not sort the rest, "
                    "which is exactly what a priority queue needs: peek and pop are the only operations "
                    "that must be fast."),
            hotspot(438, 250, 62, 34, "Why an array",
                    "A complete binary tree has no gaps, so indices alone encode the shape. That is "
                    "why heapsort needs O(1) extra space where mergesort needs O(n)."),
        ],
    }


def _recursion():
    out = []
    frames = [("fact(3)", 40), ("fact(2)", 96), ("fact(1)", 152)]
    for name, x in frames:
        out += box(x, 60, 108, 46, name, fill=FILL_SOFT, stroke=BLUE, size=13, rx=4)
    for i in range(2):
        out.append(arrow(frames[i][1] + 108, 83, frames[i + 1][1], 83, stroke=MUTED))
    out.append(label(40, 46, "call stack grows", size=11, fill=MUTED))
    out.append(arrow(262, 120, 210, 140, stroke=GREEN))
    out.append(arrow(206, 120, 152, 140, stroke=GREEN))
    out.append(arrow(150, 120, 96, 140, stroke=GREEN))
    out.append(label(40, 158, "returns 1 -> 2 -> 6", size=11.5, fill=GREEN))
    out += box(360, 60, 240, 108, "", fill=FILL_AMBER, stroke=AMBER, rx=6)
    out.append(label(376, 86, "No reachable base case:", size=13, weight=600, fill=INK))
    out.append(label(376, 108, "fact(3) -> fact(4) -> fact(5) ...", size=12, fill=INK))
    out.append(label(376, 130, "frames accumulate with no return,", size=12, fill=INK))
    out.append(label(376, 150, "so the stack overflows.", size=12, weight=600, fill=RED))
    return {
        "title": "Recursion trades stack frames for a smaller problem",
        "caption": "Each call waits on the next; unwinding carries the results back up.",
        "label": "Call stack for factorial of 3 unwinding, beside a stack overflow from a missing base case",
        "width": 640, "height": 230,
        "objects": out + [
            label(40, 196, "Base case is what makes it terminate; the recursive case must move toward it.",
                  size=12, weight=600, fill=INK),
            label(40, 214, "Backtracking is recursion plus undoing the last choice before trying the next.",
                  size=11.5, fill=MUTED),
        ],
        "hotspots": [
            hotspot(152, 60, 108, 46, "The base case",
                    "fact(1) returns immediately instead of calling again. Without a frame that returns, "
                    "nothing ever unwinds and the stack grows until the limit."),
            hotspot(360, 60, 240, 108, "Stack overflow",
                    "Every call needs its own frame for arguments and the return address. Deep recursion "
                    "on a large input can exhaust the stack even when the logic is correct - which is "
                    "why a linear scan is often rewritten as a loop."),
        ],
    }


def _dynamic_programming():
    out = []
    out.append(label(60, 44, "dp[i][j] = max( dp[i-1][j],  value[i] + dp[i-1][j-weight[i]] )",
                     size=13.5, weight=600, fill=INK))
    for r in range(4):
        for c in range(6):
            value = (r * 6 + c) % 7 + 1
            out += box(120 + c * 66, 70 + r * 44, 66, 44, str(value),
                       fill=FILL_SOFT if (r, c) != (3, 5) else FILL_AMBER,
                       stroke=BLUE if (r, c) != (3, 5) else AMBER, size=13, rx=3)
    out.append(arrow(318, 158, 448, 196, stroke=GREEN, width=1.8))
    out.append(arrow(252, 202, 448, 210, stroke=GREEN, width=1.8))
    out.append(label(120, 268, "Green arrows: the answer at the corner is built from cells already solved.",
                     size=12.5, weight=600, fill=GREEN))
    return {
        "title": "Dynamic programming fills a table so each subproblem is solved once",
        "caption": "Each cell depends only on cells above it, so filling row by row never recomputes.",
        "label": "A four by six dynamic programming table with dependency arrows into the final cell",
        "width": 640, "height": 300,
        "objects": out + [
            label(120, 288, "Memoised recursion and bottom-up tabulation compute the same values; "
                           "tabulation just avoids the call stack.", size=11.5, fill=MUTED),
        ],
        "hotspots": [
            hotspot(450, 202, 66, 44, "The answer",
                    "The bottom-right cell holds the solution to the original problem. Everything else "
                    "in the table exists only to make this one cell cheap to reach."),
            hotspot(120, 114, 66, 44, "Overlapping subproblems",
                    "This is the condition that makes DP worth using. If subproblems do not overlap, "
                    "caching them saves nothing and plain recursion is simpler."),
        ],
    }


def _sorting():
    out = [{"kind": "axis", "x": 70, "y": 40, "w": 400, "h": 180, "ticks": 6, "stroke": INK}]

    def curve(fn, colour, width=2.4):
        return polyline([(70 + n * 10, 220 - min(178, fn(n))) for n in range(1, 41)],
                        stroke=colour, width=width)

    out += [
        curve(lambda n: n * n * 0.10, RED),
        curve(lambda n: n * (n ** 0.5) * 0.16, AMBER),
        curve(lambda n: n * 2.6, GREEN),
        polyline([(70 + n * 10, 220 - 26 * (n ** 0.5)) for n in range(1, 41)], stroke=BLUE, width=2.0),
        label(470, 70, "n^2   bubble, insertion", size=12, fill=RED),
        label(470, 100, "n log n   merge, heap, quick", size=12, fill=AMBER),
        label(470, 130, "n   counting, radix", size=12, fill=GREEN),
        label(470, 160, "log n   binary search", size=12, fill=BLUE),
        label(70, 250, "n (input size) ->", size=11.5, fill=MUTED),
        label(24, 130, "operations", size=11.5, fill=MUTED, rotate=-90, anchor="middle"),
    ]
    return {
        "title": "Growth rate, not the constant, decides which sort survives a large input",
        "caption": "At n = 10 both curves look alike. At n = 1,000,000 the quadratic one is around a "
                   "trillion operations and the n log n one is around twenty million.",
        "label": "Comparison of quadratic, n log n, linear and logarithmic growth curves",
        "width": 640, "height": 290,
        "objects": out + [
            label(70, 270, "Quicksort is n log n on average but n^2 in the worst case - "
                           "which is why a good pivot matters.", size=11.5, fill=MUTED),
        ],
        "hotspots": [
            hotspot(360, 40, 110, 90, "Where the curves separate",
                    "Small inputs hide the difference because the constant factors dominate. Benchmarking "
                    "a sort on a hundred elements tells you almost nothing about its behaviour on a million."),
            hotspot(70, 200, 60, 20, "Why log n feels instant",
                    "A binary search over a billion sorted items takes about 30 comparisons, because log2 "
                    "of a billion is roughly 30. That is the practical payoff of keeping data sorted."),
        ],
    }


DIAGRAMS = {
    "arrays": _arrays,
    "linked-lists": _linked_lists,
    "stacks-queues": _stacks_queues,
    "binary-trees-traversals": _binary_trees,
    "binary-search-trees": _bst,
    "graphs-traversals": _graphs,
    "hash-tables": _hash_tables,
    "heaps-priority-queues": _heaps,
    "recursion-backtracking": _recursion,
    "dynamic-programming": _dynamic_programming,
    "sorting-complexity": _sorting,
}


def build(slug: str) -> dict:
    """The scene for a topic, or a KeyError naming what is missing."""
    try:
        return DIAGRAMS[slug]()
    except KeyError:
        raise KeyError(f"topic {slug!r} has no diagram authored in diagrams_data.DIAGRAMS") from None


def all_slugs() -> list[str]:
    return sorted(DIAGRAMS)


# ---------------------------------------------------------------------------
# Operating systems, networks, databases, programming
# ---------------------------------------------------------------------------

def _processes_threads():
    out = []
    out += box(40, 60, 250, 150, "", fill="#f8fafc", stroke=MUTED, rx=8)
    out.append(label(56, 82, "Process A", size=13, weight=600, fill=INK))
    out.append(label(56, 102, "own address space", size=11, fill=MUTED))
    out += box(60, 116, 96, 40, "Thread 1", fill=FILL_SOFT, stroke=BLUE, size=12, rx=4)
    out += box(176, 116, 96, 40, "Thread 2", fill=FILL_SOFT, stroke=BLUE, size=12, rx=4)
    out += box(60, 164, 212, 32, "shared heap / globals", fill=FILL_AMBER, stroke=AMBER, size=11.5, rx=4)
    out += box(350, 60, 250, 150, "", fill="#f8fafc", stroke=MUTED, rx=8)
    out.append(label(366, 82, "Process B", size=13, weight=600, fill=INK))
    out.append(label(366, 102, "separate address space", size=11, fill=MUTED))
    out += box(370, 116, 212, 40, "Thread 1", fill=FILL_SOFT, stroke=BLUE, size=12, rx=4)
    out += box(370, 164, 212, 32, "its own heap", fill="#f1f5f9", stroke=MUTED, size=11.5, rx=4)
    out.append({"kind": "line", "x1": 320, "y1": 60, "x2": 320, "y2": 210,
                "stroke": RED, "width": 1.6, "dash": "6 5"})
    return {
        "title": "Threads inside a process share memory; processes do not",
        "caption": "That shared heap is what makes threads cheap to create and expensive to get right.",
        "label": "Two processes, one with two threads sharing a heap, separated by an isolation boundary",
        "width": 640, "height": 250,
        "objects": out + [
            label(40, 232, "Crossing the dashed line needs IPC. Crossing within a process needs a lock.",
                  size=12, weight=600, fill=INK),
        ],
        "hotspots": [
            hotspot(60, 164, 212, 32, "The shared heap",
                    "Both threads read and write the same bytes with no protection. That is the source of "
                    "every race condition, and the reason a mutex exists."),
            hotspot(312, 60, 16, 150, "Process boundary",
                    "A crash in B cannot corrupt A, because A cannot address B's memory at all. That "
                    "isolation is why browsers run each tab as its own process."),
        ],
    }


def _cpu_scheduling():
    out = []
    rows = [("FCFS  P1 P2 P3", 0, [(0, 24, "P1", BLUE), (24, 16, "P2", GREEN), (40, 8, "P3", AMBER)]),
            ("SJF   P3 P2 P1", 60, [(0, 8, "P3", AMBER), (8, 16, "P2", GREEN), (24, 24, "P1", BLUE)]),
            ("RR q=8", 120, [(0, 8, "P1", BLUE), (8, 8, "P2", GREEN), (16, 8, "P3", AMBER),
                             (24, 8, "P1", BLUE), (32, 8, "P2", GREEN), (40, 8, "P1", BLUE)])]
    for name, y, blocks in rows:
        out.append(label(70, y + 42, name, size=12, weight=600, fill=INK))
        for start, length, tag, colour in blocks:
            x = 190 + start * 8
            out += box(x, y + 24, length * 8, 30, tag,
                       fill="#eef2ff" if colour is BLUE else "#ecfdf5" if colour is GREEN else FILL_AMBER,
                       stroke=colour, size=11, rx=3)
    avg = [("FCFS", 0, "avg wait 16"), ("SJF", 60, "avg wait 8.7  - optimal"), ("RR q=8", 120, "avg wait 13.3 - fair")]
    for name, y, note in avg:
        out.append(label(190, y + 70, note, size=11.5, fill=GREEN if "optimal" in note else MUTED))
    return {
        "title": "The same three jobs finish in a different order under each policy",
        "caption": "P1 needs 24 ms, P2 16 ms, P3 8 ms. Shortest job first minimises average waiting time.",
        "label": "Gantt charts comparing first come first served, shortest job first and round robin",
        "width": 640, "height": 250,
        "objects": out + [
            label(70, 222, "SJF is provably optimal for average wait, but it needs to know burst lengths "
                           "in advance - so real schedulers predict them.", size=11.5, fill=MUTED),
        ],
        "hotspots": [
            hotspot(190, 84, 64, 30, "Convoy effect",
                    "Under FCFS a long job at the head of the queue holds up everything behind it. "
                    "Two short jobs that arrive later wait for all 24 ms of P1."),
            hotspot(190, 204, 64, 30, "The time quantum",
                    "Too small and the CPU spends its time context switching; too large and round robin "
                    "degenerates into FCFS. The quantum is a fairness-versus-overhead dial."),
        ],
    }


def _deadlocks():
    out = []
    out += box(110, 60, 130, 46, "Thread 1\nholds R1", fill=FILL_SOFT, stroke=BLUE, size=12, rx=6)
    out += box(400, 60, 130, 46, "Thread 2\nholds R2", fill=FILL_GREEN, stroke=GREEN, size=12, rx=6)
    out += box(110, 180, 130, 46, "R1", fill="#f1f5f9", stroke=MUTED, size=13, rx=6)
    out += box(400, 180, 130, 46, "R2", fill="#f1f5f9", stroke=MUTED, size=13, rx=6)
    out.append(arrow(240, 96, 396, 196, stroke=RED, width=2.2))
    out.append(arrow(400, 96, 244, 196, stroke=RED, width=2.2))
    out.append(label(300, 150, "waits for R2", size=11.5, fill=RED, anchor="middle"))
    out.append(label(300, 168, "waits for R1", size=11.5, fill=RED, anchor="middle"))
    out.append(label(60, 250, "Circular wait: neither thread can proceed, and neither will ever release.",
                     size=12.5, weight=600, fill=RED))
    return {
        "title": "A deadlock is a cycle in the wait-for graph",
        "caption": "Each thread holds one resource and waits for the other. Nothing external can break it.",
        "label": "Two threads each holding one resource and waiting for the other, forming a cycle",
        "width": 640, "height": 290,
        "objects": out + [
            label(60, 270, "All four conditions must hold: mutual exclusion, hold and wait, no preemption, "
                           "circular wait. Break any one and deadlock is impossible.", size=11.5, fill=MUTED),
        ],
        "hotspots": [
            hotspot(300, 140, 130, 40, "The cycle",
                    "Detecting deadlock is finding a cycle in a directed graph. Banker's algorithm avoids "
                    "it by refusing any request that could create one."),
            hotspot(110, 180, 130, 46, "Break it by ordering",
                    "The simplest real fix: make every thread acquire R1 before R2. With a global lock "
                    "order no cycle can ever form, because the wait-for graph stays acyclic."),
        ],
    }


def _paging():
    out = []
    for i in range(4):
        out += box(60, 50 + i * 44, 130, 36, f"Page {i}", fill=FILL_SOFT, stroke=BLUE, size=12, rx=3)
    out.append(label(60, 40, "logical address space", size=11.5, fill=MUTED))
    out += box(250, 60, 130, 130, "", fill="#f8fafc", stroke=MUTED, rx=6)
    out.append(label(262, 80, "page table", size=11.5, fill=MUTED))
    for i, frame in enumerate([2, 0, 3, 1]):
        out += box(262, 90 + i * 24, 106, 20, f"{i} -> frame {frame}", stroke="#cbd5e1", size=10.5, rx=2)
    frames = [("Frame 0", "Page 1"), ("Frame 1", "Page 3"), ("Frame 2", "Page 0"), ("Frame 3", "Page 2")]
    out.append(label(440, 40, "physical memory", size=11.5, fill=MUTED))
    for i, (name, page) in enumerate(frames):
        out += box(440, 50 + i * 44, 150, 36, f"{name}: {page}", fill=FILL_GREEN, stroke=GREEN, size=11.5, rx=3)
    out.append(arrow(190, 68, 258, 100, stroke=MUTED))
    out.append(arrow(370, 100, 436, 158, stroke=GREEN))
    return {
        "title": "Paging breaks the requirement that a program be contiguous in memory",
        "caption": "Page 0 lives in frame 2 and page 1 in frame 0. The page table is the translation.",
        "label": "Four logical pages mapped through a page table into four physical frames out of order",
        "width": 640, "height": 250,
        "objects": out + [
            label(60, 232, "physical address = frame number * page size + offset within the page",
                  size=12.5, weight=600, fill=INK),
        ],
        "hotspots": [
            hotspot(250, 60, 130, 130, "The page table",
                    "One entry per page, looked up on nearly every memory access. That cost is why the "
                    "TLB caches recent translations, and why a TLB miss is expensive."),
            hotspot(440, 138, 150, 36, "Internal fragmentation",
                    "A page is allocated whole, so a process needing one extra byte still consumes a full "
                    "frame. Smaller pages waste less but need a longer page table."),
        ],
    }


def _synchronisation():
    out = []
    out += box(60, 50, 150, 130, "", fill="#f8fafc", stroke=MUTED, rx=6)
    out.append(label(72, 70, "Thread A", size=12, weight=600, fill=INK))
    out += box(76, 82, 118, 30, "wait(S)", fill=FILL_SOFT, stroke=BLUE, size=12, rx=3)
    out += box(76, 120, 118, 46, "critical\nsection", fill=FILL_AMBER, stroke=AMBER, size=12, rx=3)
    out += box(430, 50, 150, 130, "", fill="#f8fafc", stroke=MUTED, rx=6)
    out.append(label(442, 70, "Thread B", size=12, weight=600, fill=INK))
    out += box(446, 82, 118, 30, "wait(S)", fill="#f1f5f9", stroke=RED, size=12, rx=3)
    out += box(446, 120, 118, 46, "blocked", fill="#fef2f2", stroke=RED, size=12, rx=3)
    out += box(270, 96, 100, 44, "S = 1", fill=FILL_GREEN, stroke=GREEN, size=13, rx=22)
    out.append(arrow(210, 118, 266, 118, stroke=BLUE))
    out.append(arrow(442, 118, 374, 118, stroke=RED))
    out.append(label(270, 160, "mutex", size=11.5, anchor="middle", fill=GREEN, weight=600))
    out.append(label(76, 188, "signal(S)", size=12, fill=GREEN))
    out.append(arrow(135, 176, 300, 144, stroke=GREEN, width=1.8))
    return {
        "title": "A semaphore admits one thread at a time into the critical section",
        "caption": "A takes the token and enters. B blocks at wait(S) until A signals.",
        "label": "Two threads contending for a binary semaphore guarding a critical section",
        "width": 640, "height": 240,
        "objects": out + [
            label(60, 216, "wait() decrements and blocks if the result is negative; signal() increments and wakes a waiter.",
                  size=12, weight=600, fill=INK),
            label(60, 232, "A counting semaphore with value N admits N threads, which is how a bounded buffer works.",
                  size=11.5, fill=MUTED),
        ],
        "hotspots": [
            hotspot(270, 96, 100, 44, "The token",
                    "The whole guarantee rests on wait and signal being atomic. If two threads could both "
                    "read S as 1 and both decrement it, both would enter and the mutex would be useless."),
            hotspot(446, 120, 118, 46, "Blocked, not spinning",
                    "B is taken off the CPU rather than looping. That is the difference between a "
                    "semaphore and a spinlock, and it matters whenever the wait is longer than a "
                    "context switch."),
        ],
    }


def _file_systems():
    out = []
    out += box(60, 46, 150, 40, "/home/asha", fill=FILL_SOFT, stroke=BLUE, size=12, rx=4)
    out += box(60, 110, 150, 40, "notes.txt", fill=FILL_GREEN, stroke=GREEN, size=12, rx=4)
    out += box(60, 174, 150, 40, "photo.jpg", fill=FILL_GREEN, stroke=GREEN, size=12, rx=4)
    out += box(270, 46, 120, 40, "inode 12", fill="#f8fafc", stroke=MUTED, size=12, rx=4)
    out += box(270, 110, 120, 40, "inode 47", fill="#f8fafc", stroke=MUTED, size=12, rx=4)
    out += box(270, 174, 120, 40, "inode 48", fill="#f8fafc", stroke=MUTED, size=12, rx=4)
    for i, blocks in enumerate([["B3", "B4"], ["B9"], ["B1", "B2", "B7"]]):
        for j, b in enumerate(blocks):
            out += box(440 + j * 56, 46 + i * 64, 52, 36, b, fill=FILL_AMBER, stroke=AMBER, size=11, rx=3)
    for y in (66, 130, 194):
        out.append(arrow(210, y, 266, y, stroke=MUTED))
        out.append(arrow(390, y - 20 + 20, 436, y - 20 + 20, stroke=MUTED))
    return {
        "title": "A file name is a directory entry pointing at an inode pointing at blocks",
        "caption": "Three indirections, and each one exists to solve a different problem.",
        "label": "Directory entries mapped to inodes mapped to scattered data blocks on disk",
        "width": 640, "height": 260,
        "objects": out + [
            label(60, 236, "The directory holds the name; the inode holds the metadata and block list; "
                           "the blocks hold the bytes.", size=12.5, weight=600, fill=INK),
            label(60, 254, "A hard link is a second directory entry for the same inode - two names, one file.",
                  size=11.5, fill=MUTED),
        ],
        "hotspots": [
            hotspot(270, 110, 120, 40, "The inode",
                    "Permissions, owner, size and the block list all live here, not in the directory. "
                    "Deleting a name decrements the link count; the blocks are freed only when it reaches zero."),
            hotspot(496, 174, 52, 36, "Scattered blocks",
                    "A file's blocks need not be adjacent, so a file can grow without moving. The cost is "
                    "seek time, which is what fragmentation measures and defragmentation fixes."),
        ],
    }


def _osi():
    layers = [("Application", "HTTP, DNS, SMTP", "#4f7cff"),
              ("Transport", "TCP, UDP - ports, reliability", "#6366f1"),
              ("Network", "IP - logical addressing, routing", "#8b5cf6"),
              ("Data link", "MAC - framing, switch, error check", "#a855f7"),
              ("Physical", "copper, fibre, radio - raw bits", "#c084fc")]
    out = []
    for i, (name, detail, colour) in enumerate(layers):
        y = 44 + i * 40
        out += box(70, y, 190, 34, name, fill="#eef2ff", stroke=colour, size=12.5, rx=4)
        out.append(label(274, y + 22, detail, size=11.5, fill=MUTED))
        if i < len(layers) - 1:
            out.append({"kind": "line", "x1": 165, "y1": y + 34, "x2": 165, "y2": y + 40,
                        "stroke": MUTED, "width": 1.2})
    out.append(arrow(40, 60, 40, 220, stroke=GREEN, width=2.2))
    out.append(label(28, 140, "send", size=11.5, fill=GREEN, rotate=-90, anchor="middle"))
    out.append(arrow(610, 220, 610, 60, stroke=AMBER, width=2.2))
    out.append(label(622, 140, "receive", size=11.5, fill=AMBER, rotate=90, anchor="middle"))
    return {
        "title": "Each layer adds its own header and only talks to the layer beside it",
        "caption": "Sending walks down, receiving walks up. A switch reads layer 2; a router reads layer 3.",
        "label": "Five layer stack from application down to physical with encapsulation direction arrows",
        "width": 640, "height": 280,
        "objects": out + [
            label(70, 262, "Encapsulation: data + TCP header -> + IP header -> + frame header and trailer -> bits.",
                  size=12, weight=600, fill=INK),
            label(70, 278, "The TCP/IP model collapses these five into four by merging the bottom two.",
                  size=11.5, fill=MUTED),
        ],
        "hotspots": [
            hotspot(70, 84, 190, 34, "Transport layer",
                    "This is where a port number appears, which is how one machine runs a browser and an "
                    "SSH session at the same time. TCP adds sequencing and retransmission here; UDP does not."),
            hotspot(70, 124, 190, 34, "Network layer",
                    "IP addresses live here and are hierarchical, which is what makes routing scalable. "
                    "A router forwards on this layer and never looks above it."),
        ],
    }


def _ip_addressing():
    out = []
    out.append(label(60, 50, "192.168.1.130 / 26", size=17, weight=700, fill=INK))
    octets = [("192", 60), ("168", 190), ("1", 320), ("130", 450)]
    for text, x in octets:
        out += box(x, 66, 120, 40, text, fill=FILL_SOFT, stroke=BLUE, size=14, rx=4)
    out.append(label(182, 92, ".", size=22, fill=MUTED))
    out.append(label(312, 92, ".", size=22, fill=MUTED))
    out.append(label(442, 92, ".", size=22, fill=MUTED))
    out += box(60, 130, 350, 26, "network bits (26)", fill=FILL_AMBER, stroke=AMBER, size=11.5, rx=3)
    out += box(410, 130, 160, 26, "host bits (6)", fill=FILL_GREEN, stroke=GREEN, size=11.5, rx=3)
    out.append(label(60, 186, "2^6 = 64 addresses  -  2 reserved  =  62 usable hosts",
                     size=13.5, weight=600, fill=GREEN))
    out.append(label(60, 208, "network 192.168.1.128   broadcast 192.168.1.191   mask 255.255.255.192",
                     size=11.5, fill=MUTED))
    return {
        "title": "The prefix length is the split between who you are and where you are",
        "caption": "A /26 leaves 6 host bits, so 64 addresses per subnet and 62 that a device can use.",
        "label": "The address 192.168.1.130 with a slash 26 prefix split into network and host bits",
        "width": 640, "height": 250,
        "objects": out + [
            label(60, 232, "Subnetting borrows host bits for more networks; supernetting gives them back.",
                  size=11.5, fill=MUTED),
        ],
        "hotspots": [
            hotspot(410, 130, 160, 26, "Host bits",
                    "Every host bit doubles the address space but halves the number of subnets. Choosing "
                    "the prefix is choosing where that trade-off sits."),
            hotspot(60, 130, 350, 26, "Network bits",
                    "Routers match on these bits alone. Two addresses with the same network portion are on "
                    "the same link and never leave it, which is why a wrong mask breaks local traffic first."),
        ],
    }


def _tcp_flow_control():
    out = [{"kind": "axis", "x": 80, "y": 40, "w": 420, "h": 170, "ticks": 8, "stroke": INK}]
    out.append(polyline([(80 + i * 30, 210 - min(165, 22 * i + (i // 5) * 14)) for i in range(1, 15)],
                        stroke=BLUE, width=2.4))
    out.append(polyline([(80 + i * 30, 210 - min(165, 22 * i)) for i in range(1, 6)] +
                        [(80 + 5 * 30, 210 - 110), (80 + 6 * 30, 210 - 60), (80 + 7 * 30, 210 - 80)] +
                        [(80 + i * 30, 210 - min(165, 40 + 22 * (i - 7))) for i in range(8, 15)],
                        stroke=RED, width=2.2))
    out.append(label(500, 70, "cwnd", size=12, fill=BLUE))
    out.append(label(500, 92, "loss", size=12, fill=RED))
    out.append(label(80, 240, "round trips ->", size=11.5, fill=MUTED))
    out.append(arrow(230, 100, 230, 150, stroke=RED, width=2))
    out.append(label(236, 96, "packet lost: cwnd halved", size=11, fill=RED))
    return {
        "title": "TCP finds the available bandwidth by probing, not by being told",
        "caption": "Slow start doubles the window each round trip; congestion avoidance then grows it "
                   "linearly and halves it on loss.",
        "label": "TCP congestion window growing exponentially then linearly, halving after a loss",
        "width": 640, "height": 280,
        "objects": out + [
            label(80, 260, "Additive increase, multiplicative decrease: this is what makes many TCP flows "
                           "share a link fairly.", size=12, weight=600, fill=INK),
            label(80, 278, "Flow control (the receiver's advertised window) is separate from congestion "
                           "control (the network's capacity).", size=11.5, fill=MUTED),
        ],
        "hotspots": [
            hotspot(80, 130, 120, 80, "Slow start",
                    "Exponential, despite the name, because the window doubles every round trip. It stops "
                    "at the slow-start threshold, not when it is slow."),
            hotspot(210, 90, 60, 80, "The loss signal",
                    "TCP infers congestion from a missing acknowledgement. On a lossy wireless link that "
                    "inference is wrong, and the window collapses for no good reason."),
        ],
    }


def _normalization():
    out = []
    stages = [("1NF", "atomic values,\nno repeating groups", 40),
              ("2NF", "1NF + no partial\ndependency on a\ncomposite key", 240),
              ("3NF", "2NF + no transitive\ndependency\n(A->B->C)", 440)]
    for name, detail, x in stages:
        out += box(x, 60, 160, 92, "", fill=FILL_SOFT, stroke=BLUE, rx=6)
        out.append(label(x + 80, 86, name, size=15, anchor="middle", weight=700, fill=BLUE))
        for i, line in enumerate(detail.split("\n")):
            out.append(label(x + 80, 108 + i * 15, line, size=11, anchor="middle", fill=INK))
    out.append(arrow(204, 106, 236, 106, stroke=MUTED))
    out.append(arrow(404, 106, 436, 106, stroke=MUTED))
    return {
        "title": "Each normal form removes one specific way the same fact can be stored twice",
        "caption": "Normalisation is not about tidiness; it is about there being exactly one place to "
                   "update a fact.",
        "label": "The three main normal forms shown as a progression of boxes",
        "width": 640, "height": 250,
        "objects": out + [
            label(40, 186, "Unnormalised: student, course, lecturer and lecturer's office in one row.",
                  size=12, fill=MUTED),
            label(40, 208, "Change the office and you must find every row for that lecturer - "
                           "miss one and the database disagrees with itself.", size=12, weight=600, fill=RED),
            label(40, 230, "In 3NF the office lives in one lecturer row, referenced by key.", size=12, fill=GREEN),
        ],
        "hotspots": [
            hotspot(240, 60, 160, 92, "Partial dependency",
                    "Only 2NF catches this. It needs a composite primary key: if lecturer depends on "
                    "course alone, it is stored once per student and the duplication returns."),
            hotspot(440, 60, 160, 92, "Transitive dependency",
                    "A determines B and B determines C, so C is really a fact about B. Storing C beside A "
                    "means updating it everywhere A appears."),
        ],
    }


def _indexes():
    out = [{"kind": "axis", "x": 80, "y": 40, "w": 400, "h": 170, "ticks": 8, "stroke": INK}]
    out.append(polyline([(80 + i * 25, 210 - min(165, 4 * i)) for i in range(1, 17)], stroke=RED, width=2.4))
    out.append(polyline([(80 + i * 25, 210 - min(165, 26 * (i ** 0.5) * 0.9)) for i in range(1, 17)],
                        stroke=GREEN, width=2.4))
    out.append(label(490, 70, "full table scan", size=12, fill=RED))
    out.append(label(490, 92, "B-tree index", size=12, fill=GREEN))
    out.append(label(80, 240, "rows in the table ->", size=11.5, fill=MUTED))
    out.append(label(24, 130, "rows examined", size=11.5, fill=MUTED, rotate=-90, anchor="middle"))
    return {
        "title": "An index turns a scan of every row into a descent of a shallow tree",
        "caption": "On a million rows a full scan examines a million. A B-tree with fan-out 100 needs "
                   "about three.",
        "label": "Rows examined for a full table scan versus a B-tree index as the table grows",
        "width": 640, "height": 280,
        "objects": out + [
            label(80, 260, "The index is a second copy of the data, kept sorted. Every INSERT and UPDATE "
                           "pays to maintain it.", size=12, weight=600, fill=INK),
            label(80, 278, "So an index speeds reads and slows writes - which is why you index what you "
                           "filter on, not everything.", size=11.5, fill=MUTED),
        ],
        "hotspots": [
            hotspot(380, 40, 100, 90, "Where the gap opens",
                    "On a small table the scan is barely slower and the index is pure overhead. The "
                    "planner knows this and will ignore an index that is not worth using."),
            hotspot(80, 190, 100, 20, "Logarithmic depth",
                    "Depth grows as log of the row count to the base of the fan-out. Adding another level "
                    "takes a hundred times more rows, so trees stay three or four deep in practice."),
        ],
    }


def _sql_joins():
    out = []
    for cx, name in [(210, "orders"), (430, "customers")]:
        out += box(cx - 90, 50, 180, 150, "", fill="#f8fafc", stroke=MUTED, rx=8)
        out.append(label(cx, 72, name, size=13, anchor="middle", weight=600, fill=INK))
    out.append(label(210, 130, "INNER JOIN", size=13, anchor="middle", weight=700, fill=BLUE))
    out.append(label(210, 152, "only matched rows", size=11, anchor="middle", fill=MUTED))
    out.append(label(430, 130, "LEFT JOIN", size=13, anchor="middle", weight=700, fill=GREEN))
    out.append(label(430, 152, "all left rows, NULLs for misses", size=11, anchor="middle", fill=MUTED))
    out += box(150, 168, 120, 22, "", fill=FILL_SOFT, stroke=BLUE, rx=11)
    out += box(370, 168, 120, 22, "", fill=FILL_GREEN, stroke=GREEN, rx=11)
    out += box(336, 168, 120, 22, "", fill="none", stroke=GREEN, rx=11)
    return {
        "title": "The join type decides what happens to a row that has no match",
        "caption": "INNER drops it. LEFT keeps it and fills the missing side with NULL.",
        "label": "Inner join and left join shown as overlapping sets",
        "width": 640, "height": 250,
        "objects": out + [
            label(60, 226, "GROUP BY collapses rows into one per key; an aggregate then summarises each group.",
                  size=12, weight=600, fill=INK),
            label(60, 244, "WHERE filters rows before grouping, HAVING filters groups after. "
                           "Mixing them up is the classic mistake.", size=11.5, fill=RED),
        ],
        "hotspots": [
            hotspot(296, 158, 48, 42, "The overlap",
                    "An INNER JOIN returns only rows present on both sides. A customer who never ordered "
                    "disappears from the result entirely - which is often the bug in a revenue report."),
            hotspot(336, 158, 120, 42, "The unmatched side",
                    "A LEFT JOIN keeps that customer with NULLs. Counting those NULLs is how you find "
                    "customers who never bought anything."),
        ],
    }


def _transactions():
    out = []
    letters = [("A", "Atomic", "all of it or none of it"),
               ("C", "Consistent", "rules hold before and after"),
               ("I", "Isolated", "concurrent work cannot interleave"),
               ("D", "Durable", "committed means it survives a crash")]
    for i, (letter, name, detail) in enumerate(letters):
        x = 40 + i * 148
        out += box(x, 60, 138, 96, "", fill=FILL_SOFT, stroke=BLUE, rx=6)
        out.append(label(x + 69, 92, letter, size=22, anchor="middle", weight=700, fill=BLUE))
        out.append(label(x + 69, 116, name, size=12.5, anchor="middle", weight=600, fill=INK))
        out.append(label(x + 69, 136, " ".join(detail.split()[:3]), size=10.5, anchor="middle", fill=MUTED))
        out.append(label(x + 69, 149, " ".join(detail.split()[3:]), size=10.5, anchor="middle", fill=MUTED))
    return {
        "title": "ACID is four separate promises a transaction makes",
        "caption": "They are enforced by different machinery: undo logs, constraints, locks, and the write-ahead log.",
        "label": "The four ACID properties shown as labelled cards",
        "width": 640, "height": 240,
        "objects": out + [
            label(40, 192, "Transfer 500: debit one account, credit another. A crash between them must not "
                           "leave money created or destroyed.", size=12, weight=600, fill=INK),
            label(40, 214, "Durability is the one people forget: COMMIT must reach stable storage before "
                           "the client is told it succeeded.", size=11.5, fill=MUTED),
        ],
        "hotspots": [
            hotspot(40, 60, 138, 96, "Atomicity",
                    "Implemented with an undo log. If anything fails, every change is rolled back in "
                    "reverse, so a partial transfer is never visible."),
            hotspot(336, 60, 138, 96, "Isolation",
                    "The weakest of the four in practice. READ COMMITTED still permits some anomalies; "
                    "SERIALIZABLE prevents them but serialises the work, which costs throughput."),
        ],
    }


def _control_flow():
    out = []
    out += box(250, 40, 140, 38, "start", fill="#f1f5f9", stroke=MUTED, size=12, rx=19)
    out += box(250, 104, 140, 52, "score >= 50 ?", fill=FILL_AMBER, stroke=AMBER, size=12.5, rx=6)
    out += box(90, 190, 150, 40, "print pass", fill=FILL_GREEN, stroke=GREEN, size=12, rx=6)
    out += box(400, 190, 150, 40, "print fail", fill="#fef2f2", stroke=RED, size=12, rx=6)
    out.append(arrow(320, 78, 320, 100, stroke=MUTED))
    out.append(arrow(262, 156, 176, 186, stroke=GREEN))
    out.append(arrow(378, 156, 464, 186, stroke=RED))
    out.append(label(200, 176, "true", size=11.5, fill=GREEN, weight=600))
    out.append(label(424, 176, "false", size=11.5, fill=RED, weight=600))
    out += box(250, 258, 140, 34, "end", fill="#f1f5f9", stroke=MUTED, size=12, rx=17)
    out.append(arrow(165, 230, 258, 254, stroke=MUTED))
    out.append(arrow(475, 230, 382, 254, stroke=MUTED))
    return {
        "title": "A branch picks exactly one path, then both paths rejoin",
        "caption": "Every condition has two exits. Missing the rejoin is what turns an if-statement into "
                   "an infinite loop.",
        "label": "Flowchart of a pass or fail decision with both branches rejoining at end",
        "width": 640, "height": 320,
        "objects": out + [
            label(60, 310, "A loop is the same shape with the rejoin pointing back up, plus a condition "
                           "that eventually becomes false.", size=12, fill=MUTED),
        ],
        "hotspots": [
            hotspot(250, 104, 140, 52, "The condition",
                    "Evaluated once, and it must be a boolean. A common bug is assignment (=) where "
                    "comparison (==) was meant, which is truthy and always takes the same branch."),
            hotspot(250, 258, 140, 34, "The rejoin",
                    "Both branches must reach here. In a while loop this point jumps back to the condition "
                    "instead - and if the condition never changes, the loop never exits."),
        ],
    }


def _variables():
    out = []
    out += box(60, 60, 130, 44, "count", fill=FILL_SOFT, stroke=BLUE, size=13, rx=4)
    out.append(label(125, 50, "name", size=10.5, anchor="middle", fill=MUTED))
    out.append(arrow(196, 82, 246, 82, stroke=MUTED))
    out += box(250, 60, 120, 44, "42", fill=FILL_AMBER, stroke=AMBER, size=15, rx=4)
    out.append(label(310, 50, "value", size=10.5, anchor="middle", fill=MUTED))
    out.append(arrow(376, 82, 426, 82, stroke=MUTED))
    out += box(430, 60, 160, 44, "int  (4 bytes)", fill=FILL_GREEN, stroke=GREEN, size=12.5, rx=4)
    out.append(label(510, 50, "type", size=10.5, anchor="middle", fill=MUTED))
    out.append(label(60, 140, "The type decides how those 4 bytes are read:", size=12.5, weight=600, fill=INK))
    for i, (name, note) in enumerate([("int", "whole numbers, 32-bit signed"),
                                      ("float", "approximate, never exact for 0.1"),
                                      ("char", "one byte, often a small int"),
                                      ("bool", "one bit of meaning, one byte stored")]):
        y = 158 + i * 26
        out += box(60, y, 90, 22, name, fill="#f8fafc", stroke=MUTED, size=11, rx=3)
        out.append(label(162, y + 16, note, size=11.5, fill=MUTED))
    return {
        "title": "A variable binds a name to a typed location in memory",
        "caption": "The type is not decoration: it says how wide the slot is and how to interpret the bits.",
        "label": "A variable shown as name, value and type, with a table of common types",
        "width": 640, "height": 290,
        "objects": out + [
            label(60, 274, "float cannot represent 0.1 exactly, so money should never be a float - "
                           "use an integer count of cents.", size=11.5, fill=RED),
        ],
        "hotspots": [
            hotspot(430, 60, 160, 44, "Why the type matters",
                    "The same four bytes read as an int give 1078530011; read as a float they give 3.14. "
                    "The bits are identical - only the interpretation differs."),
            hotspot(60, 60, 130, 44, "The name",
                    "A name is a compile-time handle, not something that exists at runtime. Two variables "
                    "can point at the same memory, which is what aliasing is."),
        ],
    }


def _cache_locality():
    out = []
    for i, (name, time, colour) in enumerate([("register", "< 1 ns", GREEN), ("L1 cache", "~1 ns", GREEN),
                                              ("L2 cache", "~4 ns", BLUE), ("L3 cache", "~15 ns", BLUE),
                                              ("main memory", "~80 ns", AMBER), ("SSD", "~100 us", RED)]):
        y = 46 + i * 34
        width = 90 + i * 66
        out += box(150, y, width, 28, name, fill="#f8fafc", stroke=colour, size=12, rx=4)
        out.append(label(160 + width, y + 19, time, size=11.5, fill=colour, weight=600))
    out.append(label(60, 258, "Each step down is roughly an order of magnitude slower.",
                     size=12, weight=600, fill=INK))
    out.append(label(60, 276, "A cache line pulls 64 bytes at once, so the element beside the one you "
                              "asked for arrives free.", size=11.5, fill=MUTED))
    return {
        "title": "Memory is a hierarchy, and the gap between levels is enormous",
        "caption": "One access to main memory costs about as much as a hundred to L1.",
        "label": "Memory hierarchy from register down to SSD with typical access times",
        "width": 640, "height": 300,
        "objects": out,
        "hotspots": [
            hotspot(150, 216, 420, 28, "Main memory",
                    "This is the wall. Two loops doing the same number of additions can differ tenfold "
                    "purely because one walks an array in stride order and the other does not."),
            hotspot(150, 46, 90, 28, "Register and L1",
                    "Loop tiling and keeping hot data small exist to stay at this level. Spatial locality "
                    "(nearby addresses) and temporal locality (reused addresses) are what the hardware bets on."),
        ],
    }


def _design_patterns():
    out = []
    for name, detail, x in [("Creational", "how objects are made\nSingleton, Factory,\nBuilder", 40),
                            ("Structural", "how objects fit together\nAdapter, Facade,\nDecorator", 240),
                            ("Behavioural", "how objects talk\nObserver, Strategy,\nIterator", 440)]:
        out += box(x, 60, 160, 108, "", fill=FILL_SOFT, stroke=BLUE, rx=6)
        out.append(label(x + 80, 86, name, size=13.5, anchor="middle", weight=700, fill=BLUE))
        for i, line in enumerate(detail.split("\n")):
            out.append(label(x + 80, 110 + i * 16, line, size=11, anchor="middle", fill=INK))
    return {
        "title": "A pattern is a named answer to a recurring design problem",
        "caption": "The three families differ in what they solve: creating objects, composing them, or "
                   "coordinating them.",
        "label": "The three design pattern families with representative examples",
        "width": 640, "height": 240,
        "objects": out + [
            label(40, 202, "Observer: a subject keeps a list of listeners and notifies them on change. "
                           "This is how a UI updates when data changes.", size=12, weight=600, fill=INK),
            label(40, 222, "Strategy: swap an algorithm behind one interface, chosen at runtime rather "
                           "than hard-coded in a chain of if-statements.", size=11.5, fill=MUTED),
        ],
        "hotspots": [
            hotspot(440, 60, 160, 108, "Behavioural",
                    "These solve coupling between objects. Observer removes the need for a subject to "
                    "know who is listening, which is what makes it extensible."),
            hotspot(40, 60, 160, 108, "Creational",
                    "Singleton is the one to be careful with: it is a global object in disguise, and it "
                    "makes code hard to test because the instance cannot be replaced."),
        ],
    }


def _oop():
    out = []
    out += box(220, 40, 200, 86, "", fill=FILL_SOFT, stroke=BLUE, rx=6)
    out.append(label(320, 62, "class Animal", size=13, anchor="middle", weight=700, fill=BLUE))
    out.append(label(320, 84, "+ name: str", size=11.5, anchor="middle", fill=INK))
    out.append(label(320, 102, "+ speak() -> str", size=11.5, anchor="middle", fill=INK))
    for name, x in [("Dog", 100), ("Cat", 340)]:
        out += box(x, 186, 200, 60, "", fill=FILL_GREEN, stroke=GREEN, rx=6)
        out.append(label(x + 100, 208, name, size=13, anchor="middle", weight=700, fill=GREEN))
        out.append(label(x + 100, 228, "speak() -> woof / meow", size=11, anchor="middle", fill=INK))
        out.append({"kind": "line", "x1": x + 100, "y1": 186, "x2": 320, "y2": 126,
                    "stroke": MUTED, "width": 1.4})
    out += box(470, 40, 150, 86, "", fill="none", stroke=MUTED, rx=6)
    out.append(label(545, 62, "private", size=12, anchor="middle", weight=600, fill=INK))
    out.append(label(545, 84, "fields hidden,", size=10.5, anchor="middle", fill=MUTED))
    out.append(label(545, 99, "accessed by method", size=10.5, anchor="middle", fill=MUTED))
    return {
        "title": "Inheritance shares an interface; polymorphism picks the implementation at runtime",
        "caption": "Calling speak() on an Animal reference runs Dog's or Cat's version, decided by the "
                   "actual object.",
        "label": "An Animal class with Dog and Cat subclasses overriding speak, plus an encapsulation note",
        "width": 640, "height": 290,
        "objects": out + [
            label(60, 268, "Encapsulation: hide the fields, expose methods. Inheritance: reuse an interface. "
                           "Polymorphism: one call, many behaviours.", size=12, weight=600, fill=INK),
            label(60, 286, "Prefer composition over inheritance when you only want to reuse code, not an "
                           "interface.", size=11.5, fill=MUTED),
        ],
        "hotspots": [
            hotspot(320, 186, 200, 60, "The override",
                    "Dog replaces speak() rather than adding to it. The compiler resolves the method from "
                    "the object's real type, which is late binding."),
            hotspot(470, 40, 150, 86, "Encapsulation",
                    "A setter can validate; a public field cannot. That is the real reason to hide fields, "
                    "not ceremony - an invariant you cannot break from outside."),
        ],
    }


def _software_process():
    out = []
    steps = [("Requirements", 40), ("Design", 168), ("Implement", 296), ("Test", 424)]
    for name, x in steps:
        out += box(x, 60, 116, 44, name, fill=FILL_SOFT, stroke=BLUE, size=12, rx=5)
    for i in range(3):
        out.append(arrow(steps[i][1] + 116, 82, steps[i + 1][1], 82, stroke=MUTED))
    out.append(arrow(482, 104, 482, 150, stroke=GREEN))
    out.append({"kind": "line", "x1": 482, "y1": 150, "x2": 98, "y2": 150, "stroke": GREEN, "width": 1.8})
    out.append(arrow(98, 150, 98, 108, stroke=GREEN))
    out.append(label(290, 142, "feedback loop - defects found late cost most to fix",
                     size=11.5, anchor="middle", fill=GREEN, weight=600))
    out.append(label(40, 196, "Waterfall: one pass through, each phase signed off before the next.", size=12, fill=INK))
    out.append(label(40, 216, "Agile: the same phases in short iterations, so feedback arrives weekly.", size=12, fill=INK))
    return {
        "title": "Every process model is a different answer to when feedback arrives",
        "caption": "The phases are the same. What changes is how long a mistake survives before someone finds it.",
        "label": "Four phase software lifecycle with a feedback loop returning from test to requirements",
        "width": 640, "height": 260,
        "objects": out + [
            label(40, 238, "A requirements error found in testing costs far more than one found in review, "
                           "because everything downstream was built on it.", size=11.5, fill=MUTED),
        ],
        "hotspots": [
            hotspot(424, 60, 116, 44, "Test",
                    "Testing is not a phase you finish; it is evidence. Coverage tells you what was "
                    "executed, never what was checked - a test with no assertion passes forever."),
            hotspot(40, 130, 500, 30, "The feedback loop",
                    "This arrow is the whole argument for iteration. Shortening it is what continuous "
                    "integration is for."),
        ],
    }


def _limits():
    out = [{"kind": "axis", "x": 80, "y": 40, "w": 420, "h": 170, "ticks": 8, "stroke": INK}]
    out.append(polyline([(80 + i * 14, 210 - 130 + 130 / (1 + (i - 8) ** 2 / 6)) for i in range(0, 22)],
                        stroke=BLUE, width=2.4))
    out.append({"kind": "line", "x1": 80, "y1": 80, "x2": 500, "y2": 80,
                "stroke": MUTED, "width": 1, "dash": "5 5"})
    out.append(label(506, 84, "y = 1", size=11.5, fill=MUTED))
    out.append({"kind": "circle", "cx": 192, "cy": 210, "r": 5, "fill": "#ffffff", "stroke": RED, "width": 2})
    out.append(label(192, 236, "hole at x = 1", size=11, anchor="middle", fill=RED))
    out.append(arrow(150, 190, 184, 202, stroke=RED, width=1.6))
    out.append(arrow(234, 190, 200, 202, stroke=RED, width=1.6))
    return {
        "title": "A limit is where the function is heading, not what it equals",
        "caption": "(x^2 - 1)/(x - 1) is undefined at x = 1, yet the limit as x approaches 1 is 2. "
                   "The hole is real; the limit still exists.",
        "label": "A curve with a removable discontinuity at x equals 1, with arrows approaching from both sides",
        "width": 640, "height": 280,
        "objects": out + [
            label(80, 260, "Continuous at a point means the limit exists, the function is defined there, "
                           "and the two are equal.", size=12, weight=600, fill=INK),
            label(80, 278, "Break any one of the three and you have a discontinuity - a hole, a jump, or "
                           "an asymptote.", size=11.5, fill=MUTED),
        ],
        "hotspots": [
            hotspot(172, 190, 40, 40, "The hole",
                    "Substituting x = 1 gives 0/0, which is undefined. Factor first: (x-1)(x+1)/(x-1) = x+1, "
                    "so the limit is 2. The function and its limit disagree at exactly one point."),
            hotspot(80, 120, 90, 40, "Left and right must agree",
                    "A limit exists only if both one-sided limits exist and are equal. At a jump they "
                    "differ, so no limit exists - which is why the derivative is undefined at a corner."),
        ],
    }


DIAGRAMS.update({
    "processes-threads": _processes_threads,
    "cpu-scheduling": _cpu_scheduling,
    "deadlocks": _deadlocks,
    "memory-management-paging": _paging,
    "synchronisation-semaphores": _synchronisation,
    "file-systems": _file_systems,
    "osi-tcp-ip-models": _osi,
    "ip-addressing-subnetting": _ip_addressing,
    "tcp-flow-control": _tcp_flow_control,
    "normalization": _normalization,
    "indexes-query-performance": _indexes,
    "sql-joins-aggregation": _sql_joins,
    "transactions-acid": _transactions,
    "control-flow-conditionals-loops": _control_flow,
    "variables-data-types-operators": _variables,
    "cache-memory-locality": _cache_locality,
    "design-patterns": _design_patterns,
    "encapsulation-inheritance-polymorphism": _oop,
    "software-process-models-testing": _software_process,
    "limits-continuity": _limits,
})


# ---------------------------------------------------------------------------
# Core engineering: electrical, electronics, mechanical, civil, chemical
# ---------------------------------------------------------------------------

def _kirchhoffs():
    out = []
    nodes = [(120, 70), (300, 70), (480, 70), (120, 200), (300, 200), (480, 200)]
    for (x1, y1), (x2, y2) in [((120, 70), (300, 70)), ((300, 70), (480, 70)),
                               ((120, 200), (300, 200)), ((300, 200), (480, 200)),
                               ((120, 70), (120, 200)), ((480, 70), (480, 200))]:
        out.append({"kind": "line", "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                    "stroke": INK, "width": 2})
    out.append({"kind": "line", "x1": 300, "y1": 70, "x2": 300, "y2": 200, "stroke": INK, "width": 2})
    for x, y in nodes:
        out.append({"kind": "circle", "cx": x, "cy": y, "r": 4, "fill": INK, "stroke": INK, "width": 1})
    out += box(270, 108, 60, 30, "R2", fill=FILL_SOFT, stroke=BLUE, size=12, rx=3)
    out += box(180, 52, 60, 30, "R1", fill=FILL_SOFT, stroke=BLUE, size=12, rx=3)
    out += box(360, 52, 60, 30, "R3", fill=FILL_SOFT, stroke=BLUE, size=12, rx=3)
    out.append(arrow(150, 60, 180, 60, stroke=GREEN))
    out.append(label(150, 50, "I1", size=12, fill=GREEN, weight=700))
    out.append(arrow(320, 60, 356, 60, stroke=GREEN))
    out.append(label(330, 50, "I2", size=12, fill=GREEN, weight=700))
    out.append(arrow(288, 170, 288, 130, stroke=AMBER))
    out.append(label(266, 180, "I3", size=12, fill=AMBER, weight=700))
    out += box(90, 108, 60, 40, "12 V", fill=FILL_AMBER, stroke=AMBER, size=12, rx=4)
    out.append({"kind": "line", "x1": 120, "y1": 108, "x2": 120, "y2": 70, "stroke": INK, "width": 2})
    out.append({"kind": "line", "x1": 120, "y1": 148, "x2": 120, "y2": 200, "stroke": INK, "width": 2})
    out.append(label(300, 236, "KCL at the centre node:  I1 + I2 = I3",
                     size=14, anchor="middle", weight=700, fill=INK))
    return {
        "title": "Current arriving at a node must equal current leaving it",
        "caption": "KCL is conservation of charge; KVL is conservation of energy round a loop.",
        "label": "Circuit with three resistors and three branch currents meeting at a central node",
        "width": 640, "height": 270,
        "objects": out + [
            label(60, 258, "KVL: the voltages round any closed loop sum to zero, taking sign from the "
                           "direction you walk it.", size=11.5, fill=MUTED),
        ],
        "hotspots": [
            hotspot(280, 96, 40, 54, "The node",
                    "Charge cannot accumulate at a junction, so what flows in must flow out. Writing KCL "
                    "at every node but one gives you the independent current equations."),
            hotspot(90, 108, 60, 40, "The source",
                    "Walking the loop clockwise, a source traversed from - to is a rise and counts positive. "
                    "Getting this sign convention backwards is the single most common error in mesh analysis."),
        ],
    }


def _ac_power_factor():
    out = [{"kind": "axis", "x": 70, "y": 40, "w": 420, "h": 160, "ticks": 8, "stroke": INK}]
    out.append(polyline([(70 + i * 12, 120 - 70 * (2 * 3.14159 * i / 60)) for i in range(0, 45)],
                        stroke=BLUE, width=2.4))
    out.append(polyline([(70 + i * 12, 120 - 52 * ((2 * 3.14159 * i / 60) - 0.9)) for i in range(0, 45)],
                        stroke=RED, width=2.2, dash="6 4"))
    out.append(label(496, 70, "voltage", size=12, fill=BLUE))
    out.append(label(496, 92, "current", size=12, fill=RED))
    out.append(arrow(140, 176, 210, 176, stroke=AMBER, width=2))
    out.append(label(150, 196, "phase lag phi", size=11.5, fill=AMBER, weight=600))
    return {
        "title": "A lagging current means the supply delivers power the load gives back",
        "caption": "Real power is V I cos(phi). At a power factor of 0.7 the cable carries 43% more "
                   "current for the same useful work.",
        "label": "Voltage and current waveforms out of phase, with the phase lag marked",
        "width": 640, "height": 260,
        "objects": out + [
            label(70, 226, "P = V I cos(phi)   real power, watts", size=13, weight=700, fill=INK),
            label(70, 244, "Q = V I sin(phi)   reactive power, VAR   |   S = V I   apparent power, VA",
                  size=11.5, fill=MUTED),
        ],
        "hotspots": [
            hotspot(140, 168, 80, 20, "The phase lag",
                    "An inductor's current lags its voltage by 90 degrees. Motors and transformers are "
                    "inductive, which is why industrial loads run at a poor power factor."),
            hotspot(70, 60, 420, 60, "Why utilities charge for it",
                    "The extra current still heats the cable and the transformer even though it does no "
                    "work. Capacitor banks supply the reactive power locally so the grid does not have to."),
        ],
    }


def _transformers():
    out = []
    out += box(60, 70, 110, 110, "", fill=FILL_SOFT, stroke=BLUE, rx=4)
    for i in range(4):
        out.append({"kind": "arc", "cx": 115, "cy": 92 + i * 22, "r": 11, "a0": 0, "a1": 180,
                    "stroke": BLUE, "width": 2})
    out.append(label(115, 200, "primary  N1", size=12, anchor="middle", fill=BLUE, weight=600))
    out += box(186, 60, 16, 130, "", fill="#e2e8f0", stroke=MUTED, rx=2)
    out += box(202, 60, 16, 130, "", fill="#e2e8f0", stroke=MUTED, rx=2)
    out.append(label(202, 210, "iron core", size=11, anchor="middle", fill=MUTED))
    out += box(234, 70, 110, 110, "", fill=FILL_GREEN, stroke=GREEN, rx=4)
    for i in range(8):
        out.append({"kind": "arc", "cx": 289, "cy": 80 + i * 11, "r": 6, "a0": 0, "a1": 180,
                    "stroke": GREEN, "width": 1.6})
    out.append(label(289, 200, "secondary  N2", size=12, anchor="middle", fill=GREEN, weight=600))
    out.append(arrow(40, 125, 56, 125, stroke=AMBER))
    out.append(label(14, 118, "V1", size=13, fill=AMBER, weight=700))
    out.append(arrow(348, 125, 372, 125, stroke=AMBER))
    out += box(376, 90, 60, 70, "", fill="#fffbeb", stroke=AMBER, rx=4)
    out.append(label(406, 128, "load", size=12, anchor="middle", fill=INK))
    out.append(label(452, 118, "V2", size=13, fill=AMBER, weight=700))
    out.append(label(60, 246, "V1 / V2 = N1 / N2      and, for an ideal transformer,  V1 I1 = V2 I2",
                     size=13.5, weight=700, fill=INK))
    return {
        "title": "A transformer trades voltage for current through a shared magnetic flux",
        "caption": "More turns on the secondary raises the voltage and lowers the current in the same "
                   "proportion. No power is created.",
        "label": "Transformer with primary and secondary windings on an iron core driving a load",
        "width": 640, "height": 280,
        "objects": out + [
            label(60, 266, "The core is laminated to cut eddy-current loss, and it only works on AC - "
                           "a steady DC current produces no changing flux.", size=11.5, fill=MUTED),
        ],
        "hotspots": [
            hotspot(186, 60, 32, 130, "The iron core",
                    "It channels almost all of the primary's flux through the secondary. Leakage flux "
                    "that misses the core is what makes a real transformer imperfect under load."),
            hotspot(376, 90, 60, 70, "Why high voltage for transmission",
                    "Stepping up to 400 kV cuts the current for the same power, and losses are I squared R. "
                    "Stepping down near the user makes it safe to use."),
        ],
    }


def _pn_junction():
    out = []
    out += box(90, 70, 200, 110, "", fill="#eef2ff", stroke=BLUE, rx=4)
    out += box(290, 70, 200, 110, "", fill=FILL_GREEN, stroke=GREEN, rx=4)
    out.append(label(190, 60, "p-type", size=13, anchor="middle", weight=700, fill=BLUE))
    out.append(label(390, 60, "n-type", size=13, anchor="middle", weight=700, fill=GREEN))
    for i in range(4):
        out.append({"kind": "circle", "cx": 130 + i * 40, "cy": 100 + (i % 2) * 50, "r": 9,
                    "fill": "none", "stroke": BLUE, "width": 1.6})
    for i in range(4):
        out.append({"kind": "circle", "cx": 330 + i * 40, "cy": 100 + (i % 2) * 50, "r": 5,
                    "fill": GREEN, "stroke": GREEN, "width": 1.6})
    out += box(272, 70, 36, 110, "", fill=FILL_AMBER, stroke=AMBER, rx=2)
    out.append(label(290, 200, "depletion\nregion", size=11, anchor="middle", fill=AMBER))
    out.append(arrow(250, 125, 270, 125, stroke=AMBER, width=2))
    out.append(label(290, 232, "built-in field opposes further diffusion", size=11.5,
                     anchor="middle", fill=MUTED))
    return {
        "title": "Diffusion leaves behind a region with no free carriers",
        "caption": "Electrons cross into the p side and holes into the n side, leaving fixed ions that "
                   "set up an opposing field.",
        "label": "A pn junction with holes on the left, electrons on the right and a depletion region between",
        "width": 640, "height": 280,
        "objects": out + [
            label(90, 258, "Forward bias narrows the region and current flows. Reverse bias widens it "
                           "and almost no current flows.", size=12, weight=600, fill=INK),
            label(90, 276, "That one-way behaviour is the diode, and it is the basis of the transistor, "
                           "the LED and the solar cell.", size=11.5, fill=MUTED),
        ],
        "hotspots": [
            hotspot(272, 70, 36, 110, "The depletion region",
                    "No free carriers here, so it acts as an insulator. Its width is what the applied "
                    "voltage controls, and that control is the whole device."),
            hotspot(330, 100, 9, 9, "Free electrons",
                    "Doping added these. In silicon doped with phosphorus each donor gives one extra "
                    "electron, raising conductivity by orders of magnitude for a tiny amount of dopant."),
        ],
    }


def _boolean_kmap():
    out = []
    out.append(label(60, 50, "F = A B + A B'   simplifies to   F = A", size=14, weight=700, fill=INK))
    for r in range(2):
        for c in range(2):
            value = 1 if c == 1 else 0
            out += box(140 + c * 110, 80 + r * 80, 110, 80, str(value),
                       fill=FILL_GREEN if value else "#f8fafc",
                       stroke=GREEN if value else MUTED, size=22, rx=4)
    out.append(label(195, 74, "B=0", size=11.5, anchor="middle", fill=MUTED))
    out.append(label(305, 74, "B=1", size=11.5, anchor="middle", fill=MUTED))
    out.append(label(128, 126, "A=0", size=11.5, anchor="end", fill=MUTED))
    out.append(label(128, 206, "A=1", size=11.5, anchor="end", fill=MUTED))
    out += box(250, 156, 224, 84, "", fill="none", stroke=AMBER, rx=8)
    out.append(label(490, 176, "group of 2", size=12, fill=AMBER, weight=600))
    out.append(label(490, 196, "B changes, so B", size=11.5, fill=MUTED))
    out.append(label(490, 212, "drops out of the term", size=11.5, fill=MUTED))
    out.append(label(60, 268, "Group sizes must be powers of two: 1, 2, 4, 8. Bigger groups mean fewer "
                              "terms in the result.", size=12, weight=600, fill=INK))
    return {
        "title": "A Karnaugh map turns Boolean algebra into spotting adjacent groups",
        "caption": "Adjacent cells differ in exactly one variable, so grouping them cancels that variable.",
        "label": "A two variable Karnaugh map with a group of two cells circled",
        "width": 640, "height": 300,
        "objects": out + [
            label(60, 288, "Rows and columns use Gray code, not binary, so that neighbours differ by one bit.",
                  size=11.5, fill=MUTED),
        ],
        "hotspots": [
            hotspot(250, 156, 224, 84, "The group",
                    "Both cells hold 1 and they differ only in B. Whatever B is, the output is 1 whenever "
                    "A is 1 - so B is redundant and the expression collapses to F = A."),
            hotspot(140, 80, 110, 80, "A zero cell",
                    "Left out of every group. Grouping only the ones gives the sum-of-products form; "
                    "grouping the zeros instead gives product-of-sums."),
        ],
    }


def _per_unit_fault():
    out = []
    out.append(label(60, 46, "Z_pu = Z_actual / Z_base      where  Z_base = (V_base)^2 / S_base",
                     size=13, weight=700, fill=INK))
    out += box(60, 76, 130, 44, "Generator\n11 kV", fill=FILL_SOFT, stroke=BLUE, size=12, rx=5)
    out += box(250, 76, 130, 44, "Transformer\n11 / 132 kV", fill="#f8fafc", stroke=MUTED, size=12, rx=5)
    out += box(440, 76, 140, 44, "Line  132 kV", fill=FILL_GREEN, stroke=GREEN, size=12, rx=5)
    out.append(arrow(194, 98, 246, 98, stroke=MUTED))
    out.append(arrow(384, 98, 436, 98, stroke=MUTED))
    out.append({"kind": "line", "x1": 510, "y1": 120, "x2": 510, "y2": 168, "stroke": RED, "width": 2})
    out.append({"kind": "line", "x1": 494, "y1": 168, "x2": 526, "y2": 168, "stroke": RED, "width": 2})
    out.append(label(536, 172, "three-phase fault", size=11.5, fill=RED, weight=600))
    out.append(label(60, 206, "On a common base, every transformer turns ratio disappears from the "
                              "arithmetic.", size=12.5, weight=600, fill=GREEN))
    out.append(label(60, 226, "I_fault = 1 / Z_pu  in per-unit, then multiply by I_base to get amps.",
                     size=12, fill=INK))
    return {
        "title": "Per-unit removes transformer ratios from the calculation",
        "caption": "Everything is expressed as a fraction of a chosen base, so equipment on different "
                   "voltage levels can be compared directly.",
        "label": "A generator, transformer and line on one per-unit base with a three-phase fault at the end",
        "width": 640, "height": 270,
        "objects": out + [
            label(60, 250, "A symmetrical three-phase fault is the largest and the simplest: only the "
                           "positive-sequence network is needed.", size=11.5, fill=MUTED),
        ],
        "hotspots": [
            hotspot(250, 76, 130, 44, "The transformer",
                    "In actual ohms its two sides have different impedances. In per-unit on a consistent "
                    "base they are the same number, which is the entire point of the system."),
            hotspot(494, 120, 40, 48, "The fault",
                    "Fault current is set by the impedance between the source and the fault. Adding "
                    "reactance limits it, which is why a reactor is sometimes inserted deliberately."),
        ],
    }


def _maxwells():
    out = []
    rows = [("Gauss (E)", "div E = rho / eps0", "Charge is the source of electric field"),
            ("Gauss (B)", "div B = 0", "No magnetic monopole: field lines always close"),
            ("Faraday", "curl E = -dB/dt", "A changing magnetic field makes an electric field"),
            ("Ampere-Maxwell", "curl B = mu0 J + mu0 eps0 dE/dt", "Current, or a changing E, makes a magnetic field")]
    for i, (name, eq, meaning) in enumerate(rows):
        y = 50 + i * 48
        out += box(60, y, 150, 40, name, fill=FILL_SOFT, stroke=BLUE, size=12, rx=4)
        out.append(label(224, y + 25, eq, size=13, weight=600, fill=INK))
        out.append(label(224, y + 40, meaning, size=10.5, fill=MUTED))
    out.append(label(60, 250, "The last two coupled together are what let a field sustain itself and "
                              "travel - that solution is light.", size=12, weight=600, fill=GREEN))
    return {
        "title": "Four equations from which all of classical electromagnetism follows",
        "caption": "Two say what sources a field; two say how a changing field creates the other one.",
        "label": "The four Maxwell equations in differential form with a plain-language meaning for each",
        "width": 640, "height": 290,
        "objects": out + [
            label(60, 270, "Combining Faraday and Ampere-Maxwell gives a wave equation with speed "
                           "1/sqrt(mu0 eps0) - which is the measured speed of light.", size=11.5, fill=MUTED),
        ],
        "hotspots": [
            hotspot(60, 146, 560, 40, "Faraday's law",
                    "This is how a generator works: rotate a coil in a magnetic field, the flux through it "
                    "changes, and an EMF appears. The minus sign is Lenz's law - the induced field opposes "
                    "the change that made it."),
            hotspot(60, 194, 560, 40, "The displacement current",
                    "The term Maxwell added. Without it a charging capacitor would break Ampere's law, "
                    "because no actual charge crosses the gap. Adding it is what predicted radio waves."),
        ],
    }


def _bernoulli():
    out = []
    out.append(polyline([(40, 80), (200, 80), (260, 110), (380, 110), (440, 80), (600, 80)],
                        stroke=INK, width=2))
    out.append(polyline([(40, 190), (200, 190), (260, 160), (380, 160), (440, 190), (600, 190)],
                        stroke=INK, width=2))
    out += box(260, 110, 120, 50, "", fill=FILL_AMBER, stroke=AMBER, rx=2)
    for x, y, size in [(110, 130, 26), (320, 130, 40), (520, 130, 26)]:
        out.append(arrow(x - size / 2, y, x + size / 2, y, stroke=GREEN, width=2))
    out.append(label(110, 118, "v low", size=11, anchor="middle", fill=GREEN))
    out.append(label(320, 100, "v high", size=11, anchor="middle", fill=GREEN, weight=700))
    out.append(label(520, 118, "v low", size=11, anchor="middle", fill=GREEN))
    out.append(label(110, 176, "p high", size=11, anchor="middle", fill=BLUE))
    out.append(label(320, 176, "p low", size=11, anchor="middle", fill=BLUE, weight=700))
    out.append(label(520, 176, "p high", size=11, anchor="middle", fill=BLUE))
    out.append(label(60, 226, "P + 1/2 rho v^2 + rho g h  =  constant along a streamline",
                     size=14, weight=700, fill=INK))
    return {
        "title": "Where the pipe narrows the fluid speeds up and the pressure falls",
        "caption": "Continuity forces the speed up; Bernoulli then forces the static pressure down. "
                   "Energy is conserved, not created.",
        "label": "A venturi tube with velocity and pressure marked at the wide and narrow sections",
        "width": 640, "height": 260,
        "objects": out + [
            label(60, 248, "Valid for steady, incompressible, inviscid flow along one streamline. "
                           "Real fluids lose energy to friction, which is why a discharge coefficient is applied.",
                  size=11, fill=MUTED),
        ],
        "hotspots": [
            hotspot(260, 110, 120, 50, "The throat",
                    "Smallest area, so by continuity the velocity is highest here, and Bernoulli then puts "
                    "the static pressure at its minimum. A carburettor uses exactly this to draw fuel in."),
            hotspot(40, 80, 160, 110, "The three heads",
                    "Pressure head, velocity head and elevation head trade against each other. A pitot tube "
                    "measures the difference between total and static pressure to read airspeed."),
        ],
    }


def _manometry():
    out = []
    out.append({"kind": "line", "x1": 200, "y1": 60, "x2": 200, "y2": 190, "stroke": INK, "width": 2})
    out.append({"kind": "line", "x1": 400, "y1": 60, "x2": 400, "y2": 190, "stroke": INK, "width": 2})
    out.append({"kind": "line", "x1": 200, "y1": 190, "x2": 400, "y2": 190, "stroke": INK, "width": 2})
    out += box(196, 120, 208, 74, "", fill="#dbeafe", stroke=BLUE, rx=2)
    out.append(label(300, 162, "manometer fluid", size=11.5, anchor="middle", fill=BLUE))
    out.append({"kind": "line", "x1": 196, "y1": 120, "x2": 260, "y2": 120, "stroke": BLUE, "width": 1.4})
    out.append({"kind": "line", "x1": 340, "y1": 96, "x2": 404, "y2": 96, "stroke": BLUE, "width": 1.4})
    out += box(120, 108, 70, 26, "", fill=FILL_AMBER, stroke=AMBER, rx=3)
    out.append(label(30, 126, "h", size=14, fill=AMBER, weight=700))
    out.append(arrow(228, 106, 228, 120, stroke=AMBER))
    out.append(label(300, 84, "P + rho g h  =  P_atm", size=14, anchor="middle", weight=700, fill=INK))
    out.append(label(300, 226, "Pressure grows linearly with depth, because the weight of fluid above "
                               "grows linearly with depth.", size=12, anchor="middle", fill=MUTED))
    return {
        "title": "A manometer measures pressure as a height of fluid",
        "caption": "Balance the unknown pressure against a column of known density and read the height.",
        "label": "A U-tube manometer with a height difference h between the two arms",
        "width": 640, "height": 260,
        "objects": out + [
            label(60, 250, "1 atm supports about 10.3 m of water but only 760 mm of mercury - "
                           "which is why mercury was used.", size=11.5, fill=MUTED),
        ],
        "hotspots": [
            hotspot(196, 96, 144, 30, "The height difference",
                    "Only the difference matters, not the absolute level. Adding fluid to both arms equally "
                    "changes nothing, which is why the reading is robust."),
            hotspot(120, 108, 70, 26, "Gauge versus absolute",
                    "If one arm is open to the atmosphere the reading is gauge pressure. Add 101.325 kPa "
                    "for absolute - confusing the two is a common and expensive error."),
        ],
    }


def _entropy():
    out = [{"kind": "axis", "x": 80, "y": 40, "w": 400, "h": 170, "ticks": 6, "stroke": INK}]
    out.append(polyline([(80 + i * 12, 200 - 8 * i) for i in range(0, 15)], stroke=BLUE, width=2.4))
    out.append({"kind": "line", "x1": 260, "y1": 84, "x2": 260, "y2": 200,
                "stroke": GREEN, "width": 1.6, "dash": "5 4"})
    out.append(label(266, 80, "reversible: area under the curve is heat", size=11, fill=GREEN))
    out.append(label(490, 70, "T", size=13, fill=INK))
    out.append(label(80, 238, "S (entropy) ->", size=11.5, fill=MUTED))
    out.append(label(24, 130, "T", size=11.5, fill=MUTED, rotate=-90, anchor="middle"))
    return {
        "title": "Entropy of an isolated system never decreases",
        "caption": "Heat flows hot to cold on its own because that direction increases total entropy. "
                   "The reverse would need work put in.",
        "label": "A temperature-entropy diagram with a reversible process and the heat as the area under it",
        "width": 640, "height": 280,
        "objects": out + [
            label(80, 258, "dS = dQ_rev / T     - the same heat added at a lower temperature produces more entropy.",
                  size=13, weight=700, fill=INK),
            label(80, 278, "This is why no engine can convert all its heat into work: some must be "
                           "rejected to raise the surroundings' entropy.", size=11.5, fill=MUTED),
        ],
        "hotspots": [
            hotspot(80, 60, 180, 140, "Why the arrow points one way",
                    "There are vastly more disordered arrangements than ordered ones. A gas spreading to "
                    "fill a room is not forbidden by energy conservation - it is simply overwhelmingly "
                    "more likely than the reverse."),
            hotspot(260, 84, 4, 116, "Area is heat",
                    "On a T-S diagram the area under a reversible path is the heat transferred. That is "
                    "what makes the Carnot cycle a rectangle and its efficiency easy to read off."),
        ],
    }


def _first_law():
    out = []
    out += box(230, 90, 180, 110, "", fill=FILL_SOFT, stroke=BLUE, rx=8)
    out.append(label(320, 130, "SYSTEM", size=15, anchor="middle", weight=700, fill=BLUE))
    out.append(label(320, 154, "internal energy U", size=12, anchor="middle", fill=INK))
    out.append(arrow(120, 145, 226, 145, stroke=RED, width=2.6))
    out.append(label(70, 132, "Q in", size=14, fill=RED, weight=700))
    out.append(label(58, 168, "heat added", size=11, fill=MUTED))
    out.append(arrow(414, 145, 540, 145, stroke=GREEN, width=2.6))
    out.append(label(548, 132, "W out", size=14, fill=GREEN, weight=700))
    out.append(label(548, 168, "work done by", size=11, fill=MUTED))
    out.append(label(320, 60, "dU = Q - W", size=19, anchor="middle", weight=700, fill=INK))
    out.append(label(320, 232, "Energy is accounted for, never created. What enters as heat and leaves "
                               "as work stays behind as internal energy.", size=12,
                     anchor="middle", fill=MUTED))
    return {
        "title": "The first law is a balance sheet for energy",
        "caption": "Heat in minus work out equals the change in stored energy. Nothing else can happen.",
        "label": "A control mass with heat entering, work leaving and internal energy stored",
        "width": 640, "height": 270,
        "objects": out + [
            label(60, 258, "Sign convention matters: many texts write dU = Q + W where W is work done ON "
                           "the system. Read the convention before using a formula.", size=11.5, fill=RED),
        ],
        "hotspots": [
            hotspot(230, 90, 180, 110, "Internal energy",
                    "A state property: it depends only on where the system is, not on how it got there. "
                    "Q and W are path quantities, which is why they cannot be added without the balance."),
            hotspot(414, 145, 126, 20, "Work out",
                    "For a gas this is P dV. In an adiabatic expansion no heat enters, so the work comes "
                    "entirely out of internal energy and the gas cools."),
        ],
    }


def _free_body():
    out = []
    out += box(250, 130, 140, 70, "block", fill=FILL_SOFT, stroke=BLUE, size=13, rx=4)
    out.append({"kind": "line", "x1": 80, "y1": 200, "x2": 560, "y2": 200, "stroke": INK, "width": 2.4})
    out.append(arrow(320, 130, 320, 60, stroke=GREEN, width=2.6))
    out.append(label(330, 66, "N  normal", size=12, fill=GREEN, weight=600))
    out.append(arrow(320, 200, 320, 268, stroke=RED, width=2.6))
    out.append(label(330, 268, "W = mg", size=12, fill=RED, weight=600))
    out.append(arrow(390, 165, 480, 165, stroke=AMBER, width=2.6))
    out.append(label(486, 170, "F applied", size=12, fill=AMBER, weight=600))
    out.append(arrow(250, 190, 180, 190, stroke=VIOLET, width=2.2))
    out.append(label(110, 186, "f friction", size=12, fill=VIOLET, weight=600))
    return {
        "title": "Isolate the body, then draw every force acting on it - and nothing else",
        "caption": "Forces the body exerts on something else do not belong here. That is the most common "
                   "mistake in a free-body diagram.",
        "label": "A block on a surface with weight, normal reaction, applied force and friction drawn as vectors",
        "width": 640, "height": 300,
        "objects": out + [
            label(60, 290, "Equilibrium means the vector sum is zero: sum F = 0 and sum M = 0. "
                           "Resolve along two perpendicular axes and solve.", size=12, weight=600, fill=INK),
        ],
        "hotspots": [
            hotspot(250, 130, 140, 70, "The isolated body",
                    "Everything touching it can exert a force, and gravity acts whether or not anything "
                    "touches it. Miss a contact and the balance will not close."),
            hotspot(180, 176, 80, 24, "Friction",
                    "It opposes the direction of impending motion, not necessarily the applied force. "
                    "Its maximum is mu N, so a heavier block can resist more push."),
        ],
    }


def _stress_strain():
    out = [{"kind": "axis", "x": 80, "y": 40, "w": 420, "h": 180, "ticks": 8, "stroke": INK}]
    out.append(polyline([(80 + i * 4, 220 - i * 12) for i in range(0, 9)], stroke=BLUE, width=2.6))
    out.append(polyline([(80 + i * 4, 220 - 108 - (i - 9) * 2.4) for i in range(9, 20)], stroke=BLUE, width=2.6))
    out.append(polyline([(80 + i * 4, 220 - 132 + (i - 20) * 1.2) for i in range(20, 34)], stroke=BLUE, width=2.6))
    out.append(polyline([(80 + i * 4, 220 - 149 + (i - 34) * 8) for i in range(34, 46)], stroke=BLUE, width=2.6))
    out.append({"kind": "line", "x1": 116, "y1": 112, "x2": 80, "y2": 112, "stroke": GREEN, "width": 1.4, "dash": "4 3"})
    out.append(label(80, 106, "proportional limit", size=10.5, fill=GREEN))
    out.append({"kind": "circle", "cx": 160, "cy": 88, "r": 4, "fill": AMBER, "stroke": AMBER, "width": 1})
    out.append(label(168, 80, "yield", size=10.5, fill=AMBER, weight=600))
    out.append({"kind": "circle", "cx": 216, "cy": 71, "r": 4, "fill": RED, "stroke": RED, "width": 1})
    out.append(label(224, 64, "ultimate", size=10.5, fill=RED, weight=600))
    out.append(label(270, 150, "necking", size=10.5, fill=MUTED))
    out.append(label(500, 70, "stress", size=12, fill=INK))
    out.append(label(80, 240, "strain ->", size=11.5, fill=MUTED))
    out.append(label(24, 130, "stress", size=11.5, fill=MUTED, rotate=-90, anchor="middle"))
    return {
        "title": "Hooke's law holds only up to the proportional limit",
        "caption": "Below it, stress is proportional to strain and the material springs back. Past yield "
                   "the deformation is permanent.",
        "label": "A stress-strain curve for mild steel with proportional limit, yield, ultimate strength and necking marked",
        "width": 640, "height": 280,
        "objects": out + [
            label(80, 260, "sigma = E epsilon, where E is Young's modulus - the stiffness, not the strength.",
                  size=12.5, weight=700, fill=INK),
            label(80, 278, "The area under the curve up to fracture is toughness: how much energy the "
                           "material absorbs before it fails.", size=11.5, fill=MUTED),
        ],
        "hotspots": [
            hotspot(80, 112, 40, 108, "The linear region",
                    "The slope here is E. Steel and aluminium can have similar strength but very different "
                    "E, so they deflect differently under the same load."),
            hotspot(216, 71, 10, 10, "Ultimate strength",
                    "The peak load the material carries. After this the cross-section necks locally, so the "
                    "nominal stress falls even though the true stress is still rising."),
        ],
    }


def _soil_stress():
    out = []
    for i in range(4):
        out += box(140, 50 + i * 46, 340, 46, "", fill="#f1f5f9" if i % 2 else "#e2e8f0",
                   stroke=MUTED, rx=2)
        out.append(label(310, 78 + i * 46, f"layer {i + 1}: gamma = {16 + i} kN/m^3",
                         size=11.5, anchor="middle", fill=MUTED))
    out.append({"kind": "line", "x1": 100, "y1": 234, "x2": 520, "y2": 234, "stroke": BLUE, "width": 2.2})
    out.append(label(530, 238, "water table", size=11.5, fill=BLUE, weight=600))
    out.append(label(60, 264, "sigma_total = sum (gamma_i * z_i)        sigma_eff = sigma_total - u",
                     size=13.5, weight=700, fill=INK))
    out.append(arrow(80, 60, 80, 226, stroke=RED, width=2.4))
    out.append(label(40, 150, "stress grows with depth", size=11, fill=RED, rotate=-90, anchor="middle"))
    return {
        "title": "Only effective stress carries load; water carries the rest",
        "caption": "Total stress is the weight above. Pore water pressure supports part of it. The "
                   "remainder, pressing grain on grain, is what gives soil its strength.",
        "label": "A layered soil profile with a water table and the effective stress relation",
        "width": 640, "height": 300,
        "objects": out + [
            label(60, 286, "Below the water table use the buoyant unit weight, because the water already "
                           "supports part of the soil.", size=11.5, fill=MUTED),
        ],
        "hotspots": [
            hotspot(100, 226, 420, 20, "The water table",
                    "Raising it reduces effective stress and the ground loses strength. That is the "
                    "mechanism behind a quicksand condition and a major cause of excavation failure."),
            hotspot(140, 188, 340, 46, "The bearing layer",
                    "Bearing capacity is computed from effective stress and the shear-strength parameters. "
                    "Using total stress here overestimates what the ground can carry."),
        ],
    }


def _concrete_mix():
    out = []
    for i, (name, pct, colour) in enumerate([("cement", 12, BLUE), ("water", 14, "#38bdf8"),
                                             ("fine aggregate", 26, AMBER), ("coarse aggregate", 48, GREEN)]):
        y = 50 + i * 46
        out += box(60, y, 300 * pct / 48, 34, "", fill="#f8fafc", stroke=colour, rx=4)
        out += box(60, y, 300 * pct / 48, 34, name, fill="#f8fafc", stroke=colour, size=12, rx=4)
        out.append(label(70 + 300 * pct / 48, y + 22, f"{pct}%", size=12, fill=colour, weight=600))
    out.append(label(60, 250, "water / cement ratio is the single biggest control on strength",
                     size=13, weight=700, fill=INK))
    out.append(label(60, 270, "more water makes it easier to place but weaker and more porous once it "
                              "cures", size=11.5, fill=MUTED))
    return {
        "title": "The water-cement ratio trades workability against strength",
        "caption": "Only about 0.25 of water is needed for hydration. Anything above that leaves pores "
                   "behind when it evaporates.",
        "label": "Typical concrete proportions by volume with a note on the water cement ratio",
        "width": 640, "height": 300,
        "objects": out + [
            label(60, 290, "Slump measures workability: a low slump is stiff, a high slump flows. "
                           "Adding water to raise it on site silently reduces strength.", size=11.5, fill=RED),
        ],
        "hotspots": [
            hotspot(60, 96, 88, 34, "Water",
                    "The temptation on site is to add water so the concrete pours more easily. Every extra "
                    "litre raises the ratio and cuts strength - which is why admixtures are used instead."),
            hotspot(300, 142, 300, 34, "Aggregates",
                    "They carry most of the load and resist shrinkage. A well-graded mix of sizes packs "
                    "more densely, leaving fewer voids for cement paste to fill."),
        ],
    }


def _material_energy():
    out = []
    out += box(240, 100, 160, 90, "", fill=FILL_SOFT, stroke=BLUE, rx=8)
    out.append(label(320, 132, "PROCESS", size=14, anchor="middle", weight=700, fill=BLUE))
    out.append(label(320, 156, "reactor / column", size=11.5, anchor="middle", fill=MUTED))
    out.append(arrow(60, 145, 236, 145, stroke=GREEN, width=2.6))
    out.append(label(60, 132, "feed", size=12.5, fill=GREEN, weight=600))
    out.append(arrow(404, 128, 560, 128, stroke=AMBER, width=2.6))
    out.append(label(566, 124, "product", size=12.5, fill=AMBER, weight=600))
    out.append(arrow(404, 162, 560, 162, stroke=RED, width=2.2))
    out.append(label(566, 168, "waste", size=12.5, fill=RED, weight=600))
    out.append(arrow(140, 250, 240, 194, stroke=VIOLET, width=2))
    out.append(label(70, 258, "recycle", size=11.5, fill=VIOLET, weight=600))
    out.append(label(320, 60, "IN = OUT + ACCUMULATION", size=16, anchor="middle", weight=700, fill=INK))
    return {
        "title": "Every balance starts by drawing the boundary and counting what crosses it",
        "caption": "Mass and energy are conserved, so anything unaccounted for is a stream you have "
                   "forgotten to draw.",
        "label": "A process block with feed, product, waste and recycle streams around a conservation balance",
        "width": 640, "height": 300,
        "objects": out + [
            label(60, 282, "At steady state accumulation is zero and the balance becomes IN = OUT, which "
                           "is what most design calculations assume.", size=11.5, fill=MUTED),
        ],
        "hotspots": [
            hotspot(240, 100, 160, 90, "Choose the boundary first",
                    "Around the whole plant, or around one unit? A wider boundary hides internal recycle "
                    "and makes the algebra far simpler. Choosing badly is the usual reason a balance "
                    "becomes unsolvable."),
            hotspot(404, 150, 156, 24, "Two outlet streams",
                    "Splitting the outflow means you need one more relation to solve - usually a specified "
                    "conversion or a separation efficiency. Without it the system is underdetermined."),
        ],
    }


def _convolution():
    out = [{"kind": "axis", "x": 80, "y": 40, "w": 400, "h": 150, "ticks": 8, "stroke": INK}]
    out.append(polyline([(80 + i * 12, 190 - 70 * (2.718 ** (-i / 5))) for i in range(0, 26)],
                        stroke=BLUE, width=2.4))
    out.append(polyline([(80 + i * 12, 190 - 90 * (2.718 ** (-i / 5)) * (1 - 2.718 ** (-i / 7)))
                         for i in range(0, 26)], stroke=GREEN, width=2.4))
    out.append(label(490, 70, "input x(t)", size=12, fill=BLUE))
    out.append(label(490, 92, "output y(t)", size=12, fill=GREEN))
    out.append(label(80, 226, "t ->", size=11.5, fill=MUTED))
    out.append(label(60, 252, "y(t) = (x * h)(t) = integral of x(tau) h(t - tau) d tau",
                     size=14, weight=700, fill=INK))
    out.append(label(60, 272, "Flip h, slide it across x, multiply and integrate at each position.",
                     size=12, fill=MUTED))
    return {
        "title": "An LTI system's output is the input smeared by its impulse response",
        "caption": "Know h(t) and you can predict the response to any input, because any input is a sum "
                   "of shifted impulses.",
        "label": "An input signal and the smoothed output of a linear time-invariant system",
        "width": 640, "height": 300,
        "objects": out + [
            label(60, 292, "In the frequency domain convolution becomes multiplication: Y(w) = X(w) H(w). "
                           "That is why the Fourier and Laplace transforms are so useful.",
                  size=11.5, fill=GREEN, weight=600),
        ],
        "hotspots": [
            hotspot(80, 60, 120, 130, "The impulse response",
                    "h(t) is the complete description of an LTI system. Everything it will ever do to any "
                    "signal is contained in that one function."),
            hotspot(300, 60, 180, 130, "The smearing",
                    "The output at time t depends on past inputs, weighted by h. That memory is exactly "
                    "what a filter is - and causality means h is zero for negative time."),
        ],
    }


DIAGRAMS.update({
    "kirchhoffs-laws": _kirchhoffs,
    "ac-circuits-power-factor": _ac_power_factor,
    "transformers": _transformers,
    "semiconductors-pn-junctions": _pn_junction,
    "boolean-algebra-karnaugh-maps": _boolean_kmap,
    "per-unit-system-fault-analysis": _per_unit_fault,
    "maxwells-equations": _maxwells,
    "bernoullis-equation": _bernoulli,
    "fluid-statics-manometry": _manometry,
    "entropy-the-second-law": _entropy,
    "first-law-energy-balance": _first_law,
    "equilibrium-of-forces-free-body-diagrams": _free_body,
    "stress-strain-hookes-law": _stress_strain,
    "effective-stress-bearing-capacity": _soil_stress,
    "concrete-mix-design-workability": _concrete_mix,
    "material-energy-balances": _material_energy,
    "convolution-lti-systems": _convolution,
})

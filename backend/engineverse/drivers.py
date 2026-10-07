"""stdin/stdout harnesses ("wrappers") appended to a submission before it runs.

A coding problem's stub only *declares* an entry point - ``def two_sum(nums, target)``
or ``class LRUCache``.  Nothing calls it, so running the submission verbatim would
always print nothing and fail every test.

Each problem therefore names a *wrapper* (``coding_problems.wrapper``).  The judge
appends the matching driver, which:

    1. reads stdin using the convention documented on the problem page,
    2. parses it into the entry point's arguments,
    3. calls the entry point,
    4. prints the result in the exact form the expected output uses.

Adding a new problem shape means adding one wrapper here - the judge, the editor
and the test cases are untouched.  The wrapper name is stored in the database, so
new problems are data, not code.

Only Python drivers are executable in this sandbox; see ``java_driver`` for the
equivalent Java source used by the Java runner in CI.
"""

from __future__ import annotations

import re

# Every wrapper the platform knows about.  Kept explicit so the editor can show
# the I/O convention and the seeder can validate a problem's wrapper.
WRAPPERS = (
    "raw",
    "list-target",
    "int-list-int",
    "int-list",
    "string-bool",
    "string-int",
    "two-lists",
    "lines",
    "linked-list",
    "cycle",
    "tree",
    "graph",
    "lru",
)

# How each wrapper feeds the entry point, shown on the problem page.
WRAPPER_DOCS = {
    "raw": "Read stdin yourself and print the answer.",
    "list-target": "Line 1: a list, e.g. `[2, 7, 11, 15]`. Line 2: an integer.",
    "int-list-int": "Line 1: space-separated integers. Line 2: an integer.",
    "int-list": "One line of space-separated integers.",
    "string-bool": "One line of text.",
    "string-int": "One line of text.",
    "two-lists": "Line 1: space-separated integers. Line 2: space-separated integers.",
    "lines": "One line: an integer count.",
    "linked-list": "One line of space-separated integers, built into a linked list.",
    "cycle": "Values followed by the value of the node the tail links back to. "
             "If no node has that value, the list is acyclic.",
    "tree": "Level-order values separated by spaces, using `None` for a missing node.",
    "graph": "One `Node:Neighbour1w1,Neighbour2w2` line per node, then the start "
             "node, then the end node.",
    "lru": "Line 1: capacity. Then one `put k v` or `get k` command per line; "
           "every `get` result is printed, space-separated.",
}

_ENTRY_RE = re.compile(r"^\s*(?:def|class)\s+([A-Za-z_][A-Za-z0-9_]*)")

# Node/tree types the harness carries itself, so a submission still runs even if
# the learner deleted the helper classes that ship in the stub.  Private names
# keep them out of the way of the learner's own code.
_EV_NODE = """class _EvNode:
    __slots__ = ("value", "next")
    def __init__(self, value=0, nxt=None):
        self.value = value
        self.next = nxt"""


def entrypoint(signature: str | None, fallback: str = "solution") -> str:
    """Pulls the callable name out of a stored stub signature."""
    if signature:
        match = _ENTRY_RE.match(signature)
        if match:
            return match.group(1)
    return fallback


def _python_body(wrapper: str, entry: str) -> str | None:
    """Returns the driver body for a wrapper, or None for 'raw'."""
    if wrapper == "raw":
        return None

    if wrapper == "list-target":
        return f"""
import sys as _sys, ast as _ast
_d = _sys.stdin.read().split("\\n")
_a = _ast.literal_eval(_d[0].strip()) if _d and _d[0].strip() else []
_b = int(_d[1].strip()) if len(_d) > 1 and _d[1].strip() else 0
print({entry}(_a, _b))
"""

    if wrapper == "int-list-int":
        return f"""
import sys as _sys
_d = _sys.stdin.read().split("\\n")
_a = [int(x) for x in _d[0].split()] if _d and _d[0].strip() else []
_b = int(_d[1].strip()) if len(_d) > 1 and _d[1].strip() else 0
print({entry}(_a, _b))
"""

    if wrapper == "int-list":
        return f"""
import sys as _sys
_a = [int(x) for x in _sys.stdin.read().split()]
print({entry}(_a))
"""

    if wrapper == "string-bool":
        return f"""
import sys as _sys
print(bool({entry}(_sys.stdin.read().split("\\n")[0])))
"""

    if wrapper == "string-int":
        return f"""
import sys as _sys
print({entry}(_sys.stdin.read().split("\\n")[0]))
"""

    if wrapper == "two-lists":
        return f"""
import sys as _sys
_d = _sys.stdin.read().split("\\n")
_a = [int(x) for x in _d[0].split()] if len(_d) > 0 and _d[0].strip() else []
_b = [int(x) for x in _d[1].split()] if len(_d) > 1 and _d[1].strip() else []
print(" ".join(str(v) for v in {entry}(_a, _b)))
"""

    if wrapper == "lines":
        return f"""
import sys as _sys
_n = int((_sys.stdin.read().strip() or "0"))
print(" ".join(str(v) for v in {entry}(_n)))
"""

    if wrapper == "linked-list":
        return f"""
import sys as _sys


{_EV_NODE}


def _ev_build(values):
    dummy = _EvNode()
    tail = dummy
    for value in values:
        tail.next = _EvNode(value)
        tail = tail.next
    return dummy.next


def _ev_dump(head):
    out = []
    while head:
        out.append(head.value)
        head = head.next
    return out


_h = _ev_build([int(x) for x in _sys.stdin.read().split()])
_r = {entry}(_h)
print(" ".join(str(v) for v in (_ev_dump(_r) if _r is not None else [])))
"""

    if wrapper == "cycle":
        # Convention: the values of the list, then the value of the node the tail
        # links back to.  No node carrying that value means the list is acyclic.
        return f"""
import sys as _sys


{_EV_NODE}


_t = _sys.stdin.read().split()
_vals = [int(x) for x in _t[:-1]] if len(_t) > 1 else []
_target = int(_t[-1]) if _t else None
_nodes = [_EvNode(v) for v in _vals]
for _i in range(len(_nodes) - 1):
    _nodes[_i].next = _nodes[_i + 1]
if _nodes and _target is not None:
    for _n in _nodes:
        if _n.value == _target:
            _nodes[-1].next = _n
            break
_h = _nodes[0] if _nodes else None
print(bool({entry}(_h)))
"""

    if wrapper == "tree":
        return f"""
import sys as _sys
from collections import deque as _ev_deque


class _EvTree:
    __slots__ = ("value", "left", "right")
    def __init__(self, value=0, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right


def _ev_build(values):
    if not values:
        return None
    root = _EvTree(values[0])
    queue = _ev_deque([root])
    index = 1
    while queue and index < len(values):
        node = queue.popleft()
        if index < len(values):
            if values[index] is not None:
                node.left = _EvTree(values[index])
                queue.append(node.left)
            index += 1
        if index < len(values):
            if values[index] is not None:
                node.right = _EvTree(values[index])
                queue.append(node.right)
            index += 1
    return root


_t = _sys.stdin.read().split()
_v = [None if x == "None" else int(x) for x in _t]
print({entry}(_ev_build(_v)))
"""

    if wrapper == "graph":
        return f"""
import sys as _sys, re as _re
_g, _rest = {{}}, []
for _line in _sys.stdin.read().split("\\n"):
    if ":" in _line:
        _node, _, _edges = _line.partition(":")
        _adj = []
        for _e in _edges.split(","):
            _m = _re.match(r"^([A-Za-z0-9_]+?)(-?\\d+)$", _e.strip())
            if _m:
                _adj.append((_m.group(1), int(_m.group(2))))
        _g[_node.strip()] = _adj
    elif _line.strip():
        _rest.append(_line.strip())
_s = _rest[0] if _rest else ""
_e = _rest[1] if len(_rest) > 1 else ""
print({entry}(_g, _s, _e))
"""

    if wrapper == "lru":
        return f"""
import sys as _sys
_d = _sys.stdin.read().split("\\n")
_c = {entry}(int(_d[0].strip()) if _d and _d[0].strip() else 0)
_out = []
for _line in _d[1:]:
    _p = _line.split()
    if not _p:
        continue
    if _p[0] == "put" and len(_p) >= 3:
        _c.put(int(_p[1]), int(_p[2]))
    elif _p[0] == "get" and len(_p) >= 2:
        _out.append(str(_c.get(int(_p[1]))))
print(" ".join(_out))
"""

    return None


def python_driver(wrapper: str, entry: str) -> str:
    body = _python_body(wrapper, entry)
    if not body:
        return ""
    return "\n\n# ---- EngineVerse harness (appended by the judge) ----\n" + body.strip() + "\n"


def compose(language: str, code: str, wrapper: str, signature: str | None) -> str:
    """Returns the program the judge should actually execute."""
    wrapper = (wrapper or "raw").strip() or "raw"
    if language == "python":
        return code.rstrip("\n") + python_driver(wrapper, entrypoint(signature))
    # Other languages run the submission verbatim; their stubs already contain a
    # main() that performs the same job as these drivers.
    return code


def java_driver(wrapper: str, entry: str) -> str:
    """Java equivalent of :func:`python_driver`.

    Used by the Java sandbox runner (``sandbox-java``) where the submission is a
    class body rather than a script.  Returns an empty string for ``raw``.
    """
    if wrapper in ("raw", ""):
        return ""
    if wrapper == "int-list-int":
        return f"""
    // ---- EngineVerse harness ----
    public static void main(String[] args) throws Exception {{
        java.io.BufferedReader br = new java.io.BufferedReader(new java.io.InputStreamReader(System.in));
        String l1 = br.readLine(); String l2 = br.readLine();
        java.util.List<Integer> a = new java.util.ArrayList<>();
        if (l1 != null && !l1.isBlank()) for (String t : l1.trim().split("\\\\s+")) a.add(Integer.parseInt(t));
        int b = (l2 == null || l2.isBlank()) ? 0 : Integer.parseInt(l2.trim());
        System.out.println(new Solution().{entry}(a, b));
    }}
"""
    return ""

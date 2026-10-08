"""The coding judge end to end.

These tests run real code in the real sandbox, so they are the strongest
evidence that the platform evaluates submissions rather than pretending to.
"""
from __future__ import annotations

import pytest

from engineverse import coding, db
from engineverse.drivers import WRAPPERS, WRAPPER_DOCS, compose, entrypoint, python_driver
from engineverse.judge import evaluate, outputs_match, provider_info, run_custom

# Reference solutions, keyed by problem slug.
SOLUTIONS = {
    "two-sum": """
def two_sum(nums, target):
    seen = {}
    for i, value in enumerate(nums):
        need = target - value
        if need in seen:
            return [seen[need], i]
        seen[value] = i
    return []
""",
    "reverse-linked-list": """
def reverse_list(head):
    previous = None
    current = head
    while current:
        following = current.next
        current.next = previous
        previous = current
        current = following
    return previous
""",
    "valid-parentheses": """
def is_valid(s):
    pairs = {')': '(', ']': '[', '}': '{'}
    stack = []
    for ch in s:
        if ch in pairs:
            if not stack or stack.pop() != pairs[ch]:
                return False
        else:
            stack.append(ch)
    return not stack
""",
    "binary-search": """
def search(nums, target):
    left, right = 0, len(nums) - 1
    while left <= right:
        middle = (left + right) // 2
        if nums[middle] == target:
            return middle
        if nums[middle] < target:
            left = middle + 1
        else:
            right = middle - 1
    return -1
""",
    "merge-sorted-arrays": """
def merge_sorted(a, b):
    result, i, j = [], 0, 0
    while i < len(a) and j < len(b):
        if a[i] <= b[j]:
            result.append(a[i]); i += 1
        else:
            result.append(b[j]); j += 1
    result.extend(a[i:]); result.extend(b[j:])
    return result
""",
    "fizzbuzz": """
def fizz_buzz(n):
    out = []
    for i in range(1, n + 1):
        if i % 15 == 0: out.append('FizzBuzz')
        elif i % 3 == 0: out.append('Fizz')
        elif i % 5 == 0: out.append('Buzz')
        else: out.append(str(i))
    return out
""",
    "maximum-subarray": """
def max_sub_array(nums):
    best = current = nums[0]
    for value in nums[1:]:
        current = max(value, current + value)
        best = max(best, current)
    return best
""",
    "lru-cache": """
from collections import OrderedDict


class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.store = OrderedDict()

    def get(self, key):
        if key not in self.store:
            return -1
        self.store.move_to_end(key)
        return self.store[key]

    def put(self, key, value):
        if key in self.store:
            self.store.move_to_end(key)
        self.store[key] = value
        if len(self.store) > self.capacity:
            self.store.popitem(last=False)
""",
    "detect-cycle": """
def has_cycle(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow is fast:
            return True
    return False
""",
    "longest-substring": """
def length_of_longest_substring(s):
    last = {}
    start = best = 0
    for index, ch in enumerate(s):
        if ch in last and last[ch] >= start:
            start = last[ch] + 1
        last[ch] = index
        best = max(best, index - start + 1)
    return best
""",
    "coin-change": """
def coin_change(coins, amount):
    unreachable = amount + 1
    table = [unreachable] * (amount + 1)
    table[0] = 0
    for value in range(1, amount + 1):
        for coin in coins:
            if coin <= value:
                table[value] = min(table[value], table[value - coin] + 1)
    return -1 if table[amount] >= unreachable else table[amount]
""",
    "level-order-traversal": """
from collections import deque


def level_order(root):
    if not root:
        return []
    out = []
    queue = deque([root])
    while queue:
        level = []
        for _ in range(len(queue)):
            node = queue.popleft()
            level.append(node.value)
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        out.append(level)
    return out
""",
    "dijkstra-shortest-path": """
import heapq


def shortest_path(graph, start, end):
    distances = {start: 0}
    heap = [(0, start)]
    while heap:
        cost, node = heapq.heappop(heap)
        if node == end:
            return cost
        if cost > distances.get(node, float('inf')):
            continue
        for neighbour, weight in graph.get(node, []):
            total = cost + weight
            if total < distances.get(neighbour, float('inf')):
                distances[neighbour] = total
                heapq.heappush(heap, (total, neighbour))
    return -1
""",
}


# Every test here reads the seeded catalogue.
pytestmark = pytest.mark.usefixtures("seeded")

#: Whether this host can isolate a submission at all. GitHub-hosted runners and
#: most container runtimes block unprivileged user namespaces, so `unshare` fails
#: with EPERM. The sandbox refuses to execute anything in that case, which is
#: correct - but it means these tests have nothing to assert, so they skip
#: rather than fail. Skipping is honest here: the behaviour under test cannot be
#: produced on the host, and TestSandboxRefusesWithoutIsolation below covers the
#: refusal itself on every host including those.
_CAN_ISOLATE = bool(provider_info().get("have_namespace"))

requires_isolation = pytest.mark.skipif(
    not _CAN_ISOLATE,
    reason="host cannot create an unprivileged user namespace; the sandbox "
           "refuses to run submissions, so there is nothing to exercise",
)


def _wrapper(slug: str) -> str:
    row = db.query_one("SELECT wrapper FROM coding_problems WHERE slug = ?", slug)
    assert row is not None, f"problem {slug} is not seeded"
    return row["wrapper"]


class TestDriverComposition:
    def test_raw_wrapper_appends_nothing(self):
        code = "print(1)"
        assert compose("python", code, "raw", None) == code

    def test_non_python_is_left_verbatim(self):
        """Only Python is driven here; other stubs carry their own main()."""
        code = "public class Main {}"
        assert compose("java", code, "int-list-int", "int search()") == code

    @pytest.mark.parametrize(
        ("signature", "expected"),
        [
            ("def two_sum(nums, target):", "two_sum"),
            ("class LRUCache:", "LRUCache"),
            ("  def  search(nums, target) -> int:", "search"),
            (None, "solution"),
            ("not a signature", "solution"),
        ],
    )
    def test_entrypoint_detection(self, signature, expected):
        assert entrypoint(signature) == expected

    def test_every_wrapper_is_documented(self):
        assert set(WRAPPER_DOCS) == set(WRAPPERS)

    def test_every_seeded_problem_uses_a_known_wrapper(self):
        for row in db.query("SELECT slug, wrapper FROM coding_problems"):
            assert row["wrapper"] in WRAPPERS, f"{row['slug']} has unknown wrapper {row['wrapper']}"

    def test_drivers_use_private_names(self):
        """The harness must not shadow a name the learner might also define."""
        for wrapper in WRAPPERS:
            driver = python_driver(wrapper, "solution")
            for line in driver.splitlines():
                if line.startswith("def ") or line.startswith("class "):
                    name = line.split()[1].split("(")[0].rstrip(":")
                    assert name.startswith("_"), f"{wrapper} defines public name {name}"


@requires_isolation
class TestSandbox:
    def test_provider_is_reported(self):
        info = provider_info()
        assert info["name"] == "local-sandbox"
        assert info["available"] is True

    def test_python_hello_world(self):
        result = run_custom("python", "print('engineverse')", "")
        assert result.status == "accepted"
        assert result.stdout.strip() == "engineverse"

    def test_stdout_is_captured(self):
        result = run_custom("python", "print(6 * 7)", "")
        assert result.stdout.strip() == "42"

    def test_stdin_is_delivered(self):
        result = run_custom("python", "print(int(input()) * 2)", "21\n")
        assert result.stdout.strip() == "42"

    def test_runtime_error_is_reported_not_swallowed(self):
        result = run_custom("python", "raise ValueError('boom')", "")
        assert result.status == "runtime_error"
        assert "boom" in result.stderr

    def test_syntax_error_is_a_compile_error(self):
        result = run_custom("python", "def (:", "")
        assert result.status == "compile_error"

    @pytest.mark.slow
    def test_infinite_loop_hits_the_deadline(self):
        result = run_custom("python", "while True:\n    pass", "")
        assert result.status == "timeout"

    def test_unsupported_language_is_refused_cleanly(self):
        result = run_custom("brainfuck", "++++", "")
        assert result.status == "unsupported_language"

    def test_submission_cannot_read_the_app_secret(self):
        """The child environment is scrubbed, so secrets are unreachable."""
        result = run_custom(
            "python",
            "import os\nprint(repr(os.environ.get('ENGINEVERSE_SECRET')))",
            "",
        )
        assert result.status == "accepted"
        assert "None" in result.stdout

    def test_submission_cannot_open_a_socket(self):
        code = (
            "import socket\n"
            "s = socket.socket()\n"
            "try:\n"
            "    s.connect(('1.1.1.1', 80))\n"
            "    print('connected')\n"
            "except OSError as e:\n"
            "    print('blocked:', type(e).__name__)\n"
        )
        result = run_custom("python", code, "")
        assert "connected" not in result.stdout, "the sandbox must not allow outbound connections"


@requires_isolation
class TestEvaluation:
    def test_all_passing_cases_are_accepted(self):
        cases = [
            {"id": "1", "input": "1\n", "expected": "1", "is_sample": True},
            {"id": "2", "input": "2\n", "expected": "2"},
        ]
        evaluation = evaluate("python", "print(input())", cases)
        assert evaluation.status == "accepted"
        assert evaluation.passed == 2
        assert evaluation.total == 2

    def test_a_wrong_answer_is_wrong_answer_not_a_crash(self):
        cases = [{"id": "1", "input": "1\n", "expected": "2"}]
        evaluation = evaluate("python", "print(input())", cases)
        assert evaluation.status == "wrong_answer"
        assert evaluation.passed == 0

    def test_trailing_whitespace_does_not_fail_a_correct_answer(self):
        assert outputs_match("42\n\n", "42")
        assert outputs_match("42\r\n", "42")
        assert outputs_match("42   ", "42")

    def test_leading_whitespace_is_still_significant(self):
        """Indentation carries meaning in some answers, so it must not be ignored."""
        assert not outputs_match("  42", "42")

    def test_a_genuinely_different_answer_fails(self):
        assert not outputs_match("43", "42")

    def test_compile_error_stops_early(self):
        cases = [{"id": str(i), "input": "", "expected": "x"} for i in range(5)]
        evaluation = evaluate("python", "def (:", cases)
        assert evaluation.status == "compile_error"
        assert len(evaluation.cases) == 1, "a compile error should not be retried per case"


@requires_isolation
class TestReferenceSolutions:
    """Every seeded problem must be solvable through the real judge.

    This is the test that catches a wrapper drifting away from its test data.
    """

    @pytest.mark.slow
    @pytest.mark.parametrize("slug", sorted(SOLUTIONS))
    def test_reference_solution_is_accepted(self, slug):
        cases = coding.testcases_for(slug)
        assert cases, f"{slug} has no test cases"
        program = coding._program(slug, "python", SOLUTIONS[slug])
        evaluation = evaluate("python", program, cases)
        assert evaluation.status == "accepted", (
            f"{slug} ({_wrapper(slug)}) failed: "
            + "; ".join(f"{c.input!r} expected {c.expected!r} got {c.actual!r}" for c in evaluation.cases if not c.passed)
        )
        assert evaluation.passed == evaluation.total

    @pytest.mark.slow
    def test_a_broken_submission_is_rejected(self):
        """Guards against a harness that passes everything regardless of the code."""
        cases = coding.testcases_for("two-sum")
        assert cases
        program = coding._program("two-sum", "python", "def two_sum(nums, target):\n    return []\n")
        evaluation = evaluate("python", program, cases)
        assert evaluation.status != "accepted"
        assert evaluation.passed < evaluation.total


@requires_isolation
class TestSandboxLimits:
    """The limits must actually be enforced.

    They used to be applied with ``ulimit`` inside the generated shell script.
    /bin/sh is dash on Debian-family images and dash implements neither
    ``ulimit -u`` nor ``-t``, so those two lines failed with "Illegal option",
    the ``2>/dev/null || true`` swallowed it, and the child ran with an
    unbounded RLIMIT_NPROC. A fork bomb then exhausted the host and the
    application server was killed along with the submission.
    """

    @pytest.fixture()
    def provider(self):
        from engineverse.judge.local import LocalSandboxProvider

        local = LocalSandboxProvider()
        if not local.supports("python"):
            pytest.skip("no python interpreter available to the judge")
        return local

    def test_the_child_receives_a_process_limit(self, provider):
        result = provider.run(
            "python",
            "import resource\n"
            "soft, hard = resource.getrlimit(resource.RLIMIT_NPROC)\n"
            "print(soft)\n",
            "",
        )
        assert result.stdout.strip(), result.stderr
        assert int(result.stdout.strip()) < 100_000, (
            f"RLIMIT_NPROC is effectively unbounded: {result.stdout.strip()}"
        )

    def test_the_child_receives_a_cpu_limit(self, provider):
        result = provider.run(
            "python",
            "import resource\nprint(resource.getrlimit(resource.RLIMIT_CPU)[0])\n",
            "",
        )
        assert result.stdout.strip(), result.stderr
        assert int(result.stdout.strip()) > 0, "RLIMIT_CPU is 0, i.e. unlimited"

    def test_the_child_receives_an_address_space_limit(self, provider):
        result = provider.run(
            "python",
            "import resource\nprint(resource.getrlimit(resource.RLIMIT_AS)[0])\n",
            "",
        )
        assert result.stdout.strip(), result.stderr
        assert int(result.stdout.strip()) > 0, "RLIMIT_AS is unlimited"

    def test_a_fork_bomb_is_contained_and_does_not_outlive_its_timeout(self, provider):
        """Runs in a subprocess so a regression cannot take the test worker down."""
        import os
        import time

        before = _count_processes_for(os.getuid())
        started = time.monotonic()
        result = provider.run("python", "import os\nwhile True: os.fork()\n", "", timeout_ms=4000)
        elapsed = time.monotonic() - started

        assert result.status in ("timeout", "runtime_error"), result.status
        # The verdict has to come back on the deadline. Reading output from
        # pipes rather than files let the grandchildren of a fork bomb hold the
        # pipe open and push this past 50s; see _read_capped in judge/local.py.
        assert elapsed < 30, f"the fork bomb ran for {elapsed:.1f}s"

        # SIGKILL to a process group is delivered asynchronously and the killed
        # processes linger as zombies until reaped, so a single sample taken the
        # instant run() returns counts corpses rather than a leak. Poll instead:
        # the assertion is that the tree is gone, not that it vanished in zero
        # milliseconds. Five seconds is far longer than the ~0.2s measured.
        deadline = time.monotonic() + 5
        after = _count_processes_for(os.getuid())
        while after > before and time.monotonic() < deadline:
            time.sleep(0.1)
            after = _count_processes_for(os.getuid())
        assert after <= before, (
            f"the fork bomb left {after - before} processes behind after 5s"
        )

    def test_a_memory_bomb_is_refused(self, provider):
        result = provider.run(
            "python", 'x = []\nwhile True: x.append("A" * 10**7)\n', "", timeout_ms=6000
        )
        assert result.status in ("runtime_error", "timeout"), result.status

    def test_a_legitimate_solution_still_runs(self, provider):
        """Guards against tightening the limits until real code cannot run."""
        result = provider.run(
            "python",
            "def two_sum(nums, target):\n"
            "    seen = {}\n"
            "    for i, n in enumerate(nums):\n"
            "        if target - n in seen:\n"
            "            return [seen[target - n], i]\n"
            "        seen[n] = i\n"
            "    return []\n",
            "",
            timeout_ms=10_000,
        )
        assert result.status == "accepted", f"{result.status}: {result.stderr[:200]}"

    def test_stdout_is_still_captured(self, provider):
        result = provider.run("python", "print('hello from the judge')\n", "", timeout_ms=8000)
        assert "hello from the judge" in result.stdout

    def test_the_secret_never_reaches_the_child(self, provider):
        result = provider.run(
            "python",
            'import os\nprint(os.environ.get("ENGINEVERSE_SECRET", "<absent>"))\n',
            "",
        )
        assert "<absent>" in result.stdout, result.stdout


def _count_processes_for(uid: int) -> int:
    """Counts live processes owned by uid; returns 0 where /proc is unavailable."""
    import os

    if not os.path.isdir("/proc"):
        return 0
    total = 0
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            with open(f"/proc/{entry}/status", "rb") as handle:
                for line in handle:
                    if line.startswith(b"Uid:"):
                        if int(line.split()[1]) == uid:
                            total += 1
                        break
        except OSError:
            continue
    return total


@requires_isolation
class TestSandboxFilesystemIsolation:
    """A submission must not be able to reach the application tree.

    The child previously ran with the application's own uid, so submitted code
    could list the checkout, read the source and write files into it. An empty
    tmpfs is mounted over the repository inside the sandbox's mount namespace.
    """

    @pytest.fixture()
    def provider(self):
        from engineverse.judge.local import LocalSandboxProvider

        local = LocalSandboxProvider()
        if not local.supports("python"):
            pytest.skip("no python interpreter available to the judge")
        return local

    def test_the_application_tree_is_not_readable(self, provider):
        from engineverse.judge.local import APP_ROOT

        if not provider._have_mount_ns:
            pytest.skip("this host does not allow an unprivileged mount namespace")
        result = provider.run(
            "python",
            "import os\n"
            "try:\n"
            f"    print('LISTED', os.listdir({str(APP_ROOT)!r}))\n"
            "except OSError as exc:\n"
            "    print('HIDDEN', type(exc).__name__)\n",
            "",
        )
        # Either the directory is gone entirely, or it is an empty tmpfs. Both
        # mean the checkout cannot be read; a listing means the mount failed.
        assert "LISTED" not in result.stdout or result.stdout.strip().endswith("[]"), (
            f"a submission can still list the checkout: {result.stdout.strip()}"
        )

    def test_the_home_directory_is_not_writable(self, provider):
        """The checkout is not the only thing the application user can write."""
        from pathlib import Path

        if not provider._have_mount_ns:
            pytest.skip("this host does not allow an unprivileged mount namespace")
        home = Path.home().resolve()
        marker = home / "_judge_home_probe.txt"
        if marker.exists():
            marker.unlink()
        provider.run(
            "python",
            f"open({str(marker)!r}, 'w').write('pwned')\nprint('attempted')\n",
            "",
        )
        assert not marker.exists(), "a submission wrote into the application user's home"

    def test_a_source_file_cannot_be_read(self, provider):
        from engineverse.judge.local import APP_ROOT

        if not provider._have_mount_ns:
            pytest.skip("this host does not allow an unprivileged mount namespace")
        target = APP_ROOT / "backend" / "main.py"
        result = provider.run(
            "python",
            "try:\n"
            f"    print(open({str(target)!r}).read(20))\n"
            "except OSError as exc:\n"
            "    print('BLOCKED', type(exc).__name__)\n",
            "",
        )
        assert "BLOCKED" in result.stdout, f"a submission read the source: {result.stdout!r}"

    def test_a_write_into_the_repository_does_not_land(self, provider, tmp_path):
        from engineverse.judge.local import APP_ROOT

        if not provider._have_mount_ns:
            pytest.skip("this host does not allow an unprivileged mount namespace")
        marker = APP_ROOT / "_judge_write_probe.txt"
        if marker.exists():
            marker.unlink()
        provider.run(
            "python",
            f"open({str(marker)!r}, 'w').write('pwned')\nprint('attempted')\n",
            "",
        )
        assert not marker.exists(), "a submission wrote a file into the repository"

    def test_the_mount_is_probed_not_assumed(self, provider):
        """The provider must report what the host actually supports."""
        assert hasattr(provider, "_have_mount_ns")
        assert isinstance(provider._have_mount_ns, bool)


class TestSandboxRefusesWithoutIsolation:
    """The fallback path that must never run code.

    Runs on every host, which is the point: this is the behaviour a runner that
    *cannot* isolate is relying on, so it cannot be tested only where isolation
    works. The old code ran the submission as a bare `timeout sh run.sh` here -
    untrusted code on the application server with the real filesystem and
    network.
    """

    def _provider(self, have_namespace: bool):
        from engineverse.judge.local import LocalSandboxProvider

        provider = LocalSandboxProvider()
        provider._have_namespace = have_namespace
        return provider

    def test_no_namespace_means_no_execution(self):
        provider = self._provider(False)
        result = provider.run("python", "print('this must not run')", "")
        assert result.status == "sandbox_unavailable"
        assert "this must not run" not in result.stdout, "the submission was executed"
        assert result.exit_code is None, "a child process was spawned"

    def test_the_reason_is_explained(self):
        provider = self._provider(False)
        result = provider.run("python", "print(1)", "")
        assert "namespace" in result.stderr.lower()

    def test_available_tracks_the_host(self):
        assert self._provider(False).available is False
        assert self._provider(True).available is True

    def test_present_but_forbidden_binaries_are_detected(self):
        """The exact GitHub-hosted-runner case.

        `unshare` is installed there, so a `shutil.which` check passes, but the
        call fails with EPERM because unprivileged user namespaces are blocked.
        That combination made the provider report itself available and then fail
        every submission at runtime - which is why CI was red for 100 runs while
        nothing about the judge had regressed.
        """
        import subprocess
        from unittest.mock import patch

        from engineverse.judge.local import LocalSandboxProvider

        def forbidden(*args, **kwargs):
            return subprocess.CompletedProcess(
                args[0], 1, b"",
                b"unshare: write failed /proc/self/uid_map: Operation not permitted",
            )

        with patch("shutil.which", return_value="/usr/bin/unshare"), \
                patch("subprocess.run", forbidden):
            provider = LocalSandboxProvider()
            assert provider._have_namespace is False, "a forbidden unshare was treated as usable"
            assert provider.available is False
            assert provider.run("python", "print('x')", "").status == "sandbox_unavailable"

    def test_other_languages_refuse_too(self):
        provider = self._provider(False)
        for language in ("javascript", "c", "cpp", "bash"):
            assert provider.run(language, "", "").status in (
                "sandbox_unavailable", "unsupported_language"
            ), f"{language} was executed without isolation"

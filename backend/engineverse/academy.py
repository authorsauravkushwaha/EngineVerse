"""Read-only academy views over the existing language-module model.

No execution, learner persistence or grading occurs here. A malformed authored
payload falls back to the legacy reader rather than claiming verified coverage.
"""
from __future__ import annotations

import json
import logging

from . import db
from .lesson_schema import SECTION_TITLES, validate_unit

log = logging.getLogger(__name__)

LEVELS = (
    'Absolute beginner', 'Core programming', 'Data structures and algorithms',
    'Language mastery', 'Software engineering', 'Advanced problem solving',
    'Projects and career readiness',
)

# Syllabus goals, NOT claims of delivered or verified lesson coverage.
SYLLABI = {
    'python': (
        'Interpreter, REPL, indentation, values, conversion and input errors.',
        'Branching, iteration, functions/scope, recursion, lists, dictionaries and modules.',
        'Bounds, hashing assumptions, deque/heapq, trees, graphs, windows and dynamic programming.',
        'Iterators/generators, decorators, context managers, data model, MRO, protocols, descriptors; distinguish CPython details.',
        'venv/packaging, pytest/mocking, logging/profiling, JSON/HTTP/SQL, security and asyncio/thread/process trade-offs.',
        'Invariant proofs, amortized analysis, backtracking/pruning, graph optimization and profiling large inputs.',
        'Adjustment-report CLI → tested CSV analyzer → authenticated API; code review and timed interview explanations.',
    ),
    'c': (
        'Preprocessing, compilation/linking, basic I/O, types and conversions; distinguish UB, unspecified and implementation-defined behavior.',
        'Control flow, functions, arrays/strings, pointers, explicit lengths, headers and separate compilation.',
        'Manual lists/stacks/queues, hash tables, trees/graphs, sorting/search and checked allocation costs.',
        'Storage duration/linkage, pointer arithmetic/aliasing, const, structs/unions, callbacks, lifetime and ownership contracts.',
        'Modular APIs, errno/error paths, file I/O, make, tests, debugger, sanitizers, portability and defensive parsing.',
        'Algorithm proofs, bounded arithmetic, bit operations, cache-aware layout and profile-led optimization.',
        'Expense CLI → file contact manager → bounded ring-log/index library; leak tests and API review.',
    ),
    'cpp': (
        'C++17 toolchain, fundamental types, expressions, input/output and warnings; label later-version features.',
        'Conditions/loops, functions, references, std::array/vector/string and library algorithms.',
        'Complexity, STL container trade-offs, heaps, trees, graph traversal, windows and dynamic programming.',
        'RAII/lifetime, copy/move/value categories, smart ownership, templates/concepts (C++20), ranges (C++20), forwarding and exceptions.',
        'CMake/dependencies, tests/sanitizers, API design, composition, files/serialization, mutexes/atomics and data races.',
        'Correctness proofs, amortized bounds, advanced graphs/strings, competitive constraints and measured optimization.',
        'Task CLI → searchable file index → concurrent bounded work queue; resource-safety review and interview drills.',
    ),
    'java': (
        'JDK/JVM, source/bytecode execution, primitives/references, expressions, main and stack traces.',
        'Branches/loops, methods, arrays/strings, classes, interfaces, scope and recursion.',
        'Collection complexity, maps/sets, queues/heaps, trees/graphs, search and dynamic programming.',
        'Generics/type erasure, exceptions/resources, records, lambdas/streams, annotations/reflection and JVM/GC boundaries.',
        'Maven/Gradle, JUnit/mocking, JDBC/transactions, HTTP APIs, authorization, logging/profiling, executors and virtual threads (Java 21).',
        'Invariants, large-input parsing, overflow, concurrency reasoning, advanced algorithm design and review.',
        'Quiz CLI → JDBC inventory → tested booking service; transaction races, observability and interview simulations.',
    ),
    'csharp': (
        'SDK/.NET/assemblies, C# syntax and explicit version floors, values/references, null and I/O.',
        'Control flow, methods, arrays/strings, classes/structs, collections and recursion.',
        'Complexity, Dictionary assumptions, Queue/Stack/PriorityQueue (.NET 6), trees/graphs and DP.',
        'Generics, delegates/events, LINQ/yield, records/patterns, nullable annotations, IDisposable and reflection.',
        'Unit/integration tests, DI, ASP.NET Core HTTP APIs, database transactions, authorization, async/tasks/cancellation and profiling.',
        'Proofs, range/overflow policies, large inputs, allocation costs, async versus parallel work and advanced patterns.',
        'Adjustment CLI → file-backed task manager → secured task API; cancellation, tests and reviewable portfolio documentation.',
    ),
    'javascript': (
        'ECMAScript versus browser/Node host APIs, values/coercion, console, modules and errors.',
        'Control flow, closures/functions, arrays/maps/sets, objects and safe input conversion.',
        'Number limits, complexity, hash maps, stacks/queues, graph traversal, windows and DP.',
        'Prototype model, this, iterables/generators, promises, event loop and async error propagation.',
        'npm lockfiles, tests, DOM accessibility, HTTP/JSON, parameterized SQL, authorization and worker boundaries.',
        'Invariants, Unicode/string assumptions, nonblocking performance, advanced search and memory profiling.',
        'Quiz → accessible revision dashboard → tested API client/service; race/error tests and interview reasoning.',
    ),
    'typescript': (
        'TypeScript compilation versus JavaScript execution, strict mode, annotations, narrowing and external input.',
        'Unions, control flow, typed functions/collections, modules and reusable interfaces.',
        'Bounds and number limits, typed maps/heaps, graph state, binary search and DP.',
        'Generics/constraints, discriminated unions, mapped/conditional types, variance and runtime validation.',
        'Dependency/config hygiene, tests, typed HTTP contracts, database boundaries, async cancellation and secure APIs.',
        'Prove runtime invariants separately from assignability; large data, advanced patterns and traceable error models.',
        'Typed calculator → validated API client → tested task dashboard; contract review and interview practice.',
    ),
    'go': (
        'Go tools/modules, packages, zero values, int widths, fmt input/output and compile errors.',
        'for/range, functions, slices/maps, structs/interfaces, pointers and explicit error values.',
        'Complexity, map assumptions, slices as queues, container/heap, trees/graphs and DP.',
        'Value copies, slice backing arrays, interface nil pitfalls, generics (Go 1.18), defer and resource lifetime.',
        'go test/race, contexts, goroutines/channels, synchronization, HTTP/SQL, transactions and structured observability.',
        'Invariant proofs, amortized allocation, goroutine leak debugging, bounded concurrency and benchmarks.',
        'Report CLI → file analyzer → cancellable health-check service; load limits and interview drills.',
    ),
    'rust': (
        'Cargo/rustc, types/mutability, expressions, I/O and compiler diagnostics.',
        'Control flow, functions, Vec/String, ownership/borrowing, slices and Result.',
        'Complexity, HashMap assumptions, VecDeque/BinaryHeap, trees/graphs, search and DP.',
        'Lifetimes, traits/generics, iterators, enums/patterns, Drop/RAII, smart pointers and unsafe contracts.',
        'Cargo tests/docs/clippy, error boundaries, serialization/files/HTTP/SQL, Send/Sync, threads and async runtime choices.',
        'Proofs, allocation/copy costs, advanced graphs, borrow-friendly data layouts and profiling.',
        'Task CLI → streaming log scanner → bounded concurrent processor; failure injection and code review.',
    ),
    'sql': (
        'SQLite dialect, relational records, SELECT, NULL and three-valued logic; tool/database safety.',
        'WHERE, grouping, aggregates, joins, subqueries, constraints and deterministic ordering.',
        'Relational algorithms, index/B-tree intuition, join cardinality, query plans and recursive traversal; not imperative DSA syntax.',
        'Window functions/CTEs, NULL semantics, keys, transactions/isolation and dialect-specific types.',
        'Schema migrations, parameterized queries, access control, integrity, backup/recovery and query tests.',
        'Plan analysis, index trade-offs, correlated-query rewrites, large-data reports and transaction anomalies.',
        'Expense queries → inventory reporting → audited multi-table reporting database; explain plans and review transactions.',
    ),
}


def decode_unit(module: dict) -> dict | None:
    raw = module.get('lesson_data')
    if not raw:
        return None
    try:
        unit = json.loads(raw) if isinstance(raw, str) else raw
        if not isinstance(unit, dict):
            return None
        validate_unit(unit)
        if unit['language'] != module['language_id']:
            return None
        return unit
    except (ValueError, TypeError, KeyError, AttributeError):
        log.warning('Invalid structured lesson for module %s; using legacy fallback', module.get('slug'))
        return None


def syllabus(language: str) -> list[dict]:
    return [{'level': i + 1, 'title': title, 'goals': goals}
            for i, (title, goals) in enumerate(zip(LEVELS, SYLLABI.get(language, ())))]


def lesson(language_id: str, slug: str) -> dict | None:
    return db.query_one('SELECT * FROM language_modules WHERE language_id = ? AND slug = ?', language_id, slug)


def coverage(modules: list[dict]) -> dict:
    return {'structured': sum(decode_unit(module) is not None for module in modules), 'total': len(modules)}

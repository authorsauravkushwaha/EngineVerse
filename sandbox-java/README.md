# EngineVerse Java sandbox

The isolated runner for learner-submitted code. It is a **separate JVM process**
that the Python web server shells out to — the web server never loads or executes
a user class in its own process.

```
web server (Python)                     sandbox (JVM)
────────────────────                    ─────────────
judge/java_bridge.py  ──stdin JSON──►   Main.java
                                          └─ Runner.java
                                               ├─ javac (ToolProvider API)
                                               └─ child JVM ── runs the submission
                      ◄─stdout JSON──   verdict
```

## Why a child process per submission

Learner code can call `System.exit`, spawn threads that never stop, or exhaust
the heap. Running it inside the web server — or even inside the sandbox's own
heap — lets any of those take the service down. A child process can be
force-killed at the deadline, has its own heap ceiling, and leaves nothing
behind once it exits.

## Protocol

One JSON object in, one JSON verdict out. Nothing else is written to stdout,
because the bridge parses the **last** line of stdout as the verdict.

Request:

```json
{"language":"java","code":"public class Main {...}","stdin":"21\n","timeoutMs":3000,"memoryKb":262144}
```

Verdict:

```json
{"status":"accepted","stdout":"42\n","stderr":"","exitCode":0,"runtimeMs":118,"memoryKb":262144}
```

`status` is one of `accepted`, `compile_error`, `runtime_error`, `timeout`,
`unsupported_language`, `internal_error` — the same vocabulary the Python judge
uses, so a verdict from either runner is interchangeable.

## Defence in depth

| Layer | Where | Guarantee |
|---|---|---|
| Process isolation | `Runner.execute` | Submission runs in a child JVM, never in the sandbox's heap |
| Wall-clock deadline | `Process.waitFor(timeoutMs)` + `destroyForcibly()` | A `while(true)` cannot outlive the deadline |
| Heap / stack ceiling | `-Xmx`, `-Xss`, `-XX:MaxMetaspaceSize` | An allocation bomb is an OOM kill, not a host problem |
| Empty environment | `ProcessBuilder.environment().clear()` | No parent secret is reachable via `System.getenv()` |
| Minimal working dir | one temp dir per run, deleted in `finally` | Nothing persists between submissions |
| Security policy (opt-in) | `ENGINEVERSE_SANDBOX_POLICY=1` | No `SocketPermission`, so no outbound network |
| No third-party deps | `pom.xml` | JUnit is test-scope only; JSON is parsed by `Json.java` |

Process-level isolation is **not** a substitute for OS-level containment. A
production deployment should additionally run this sandbox as a non-root user
inside a container or user namespace — see `deploy/Dockerfile.sandbox`.

## Building and testing

Requires **JDK 21+** and **Maven 3.9+**. A JRE is not enough: the sandbox
compiles submissions through the `ToolProvider` compiler API.

```bash
cd sandbox-java
./build.sh          # mvn package + a smoke test of the built jar
mvn test            # unit + end-to-end sandbox tests
```

Then point the web server at it:

```bash
export JUDGE=java
export JAVA_SANDBOX_JAR=sandbox-java/target/engineverse-sandbox.jar
```

`RunnerTest` is skipped automatically when only a JRE is present.

## Status in this checkout

The Java sources, `pom.xml` and tests are complete, but **this workspace has no
JDK installed** — `javac` is not on `PATH` and none is installable here. The
code has therefore not been compiled locally. `.github/workflows/java.yml`
compiles it and runs `mvn test` on a JDK 21 runner, so it is verified on every
push. Until that job is green, `LocalSandboxProvider.supports("java")` returns
`False` and Java problems report `unsupported_language` rather than failing
silently.

## Layout

```
sandbox-java/
├── pom.xml                     JDK 21, zero runtime dependencies
├── build.sh                    package + smoke test
└── src
    ├── main/java/dev/engineverse/sandbox/
    │   ├── Main.java           entry point; JSON in, verdict out
    │   ├── Runner.java         compile + run in a killable child JVM
    │   ├── Verdict.java        result record, matching the Python statuses
    │   └── Json.java           dependency-free JSON reader/writer
    └── test/java/dev/engineverse/sandbox/
        ├── JsonTest.java
        └── RunnerTest.java     end-to-end: hello world, stdin, compile error,
                                runtime error, timeout, class-name detection
```

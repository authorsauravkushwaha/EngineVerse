package dev.engineverse.sandbox;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Assumptions;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;

/**
 * End-to-end tests of the sandbox. These need a real JDK (they invoke
 * {@code javac} through the ToolProvider API) and are skipped on a JRE.
 */
class RunnerTest {

    private final Runner runner = new Runner(null, false);

    private static void requireJdk() {
        Assumptions.assumeTrue(
                javax.tools.ToolProvider.getSystemJavaCompiler() != null,
                "a JDK is required to run the sandbox tests");
    }

    @Test
    @Timeout(60)
    void runsAHelloWorldSubmission() {
        requireJdk();
        Verdict verdict = runner.run("public class Main { public static void main(String[] a) { System.out.println(42); } }",
                "", 10_000, 262_144);
        assertEquals("accepted", verdict.status(), verdict.stderr());
        assertEquals("42\n", verdict.stdout());
        assertEquals(0, verdict.exitCode());
    }

    @Test
    @Timeout(60)
    void readsStdin() {
        requireJdk();
        String code = """
                import java.io.*;
                public class Main {
                    public static void main(String[] a) throws Exception {
                        BufferedReader r = new BufferedReader(new InputStreamReader(System.in));
                        int x = Integer.parseInt(r.readLine().trim());
                        System.out.println(x * 2);
                    }
                }
                """;
        Verdict verdict = runner.run(code, "21\n", 10_000, 262_144);
        assertEquals("accepted", verdict.status(), verdict.stderr());
        assertEquals("42\n", verdict.stdout());
    }

    @Test
    @Timeout(60)
    void reportsCompileErrors() {
        requireJdk();
        Verdict verdict = runner.run("public class Main { public static void main(String[] a) { int x = ; } }",
                "", 10_000, 262_144);
        assertEquals("compile_error", verdict.status());
        assertFalse(verdict.stderr().isBlank(), "compiler diagnostics should be surfaced");
    }

    @Test
    @Timeout(60)
    void reportsRuntimeErrors() {
        requireJdk();
        String code = """
                public class Main {
                    public static void main(String[] a) {
                        throw new IllegalStateException("boom");
                    }
                }
                """;
        Verdict verdict = runner.run(code, "", 10_000, 262_144);
        assertEquals("runtime_error", verdict.status());
        assertTrue(verdict.stderr().contains("boom"), "the exception message should reach the learner");
    }

    @Test
    @Timeout(60)
    void killsASubmissionThatNeverFinishes() {
        requireJdk();
        String code = "public class Main { public static void main(String[] a) { while (true) { } } }";
        long started = System.nanoTime();
        Verdict verdict = runner.run(code, "", 1_500, 262_144);
        long elapsedMs = java.util.concurrent.TimeUnit.NANOSECONDS.toMillis(System.nanoTime() - started);
        assertEquals("timeout", verdict.status());
        assertTrue(elapsedMs < 15_000, "the deadline must be enforced, took " + elapsedMs + "ms");
    }

    @Test
    void reportsWhetherTheSecurityPolicyCanBeEnforced() {
        // True on JDK 21, false on JDK 24+. The matrix covers both, so this
        // pins the boundary rather than merely asserting it is a boolean.
        assertEquals(Runtime.version().feature() < 24, Runner.policySupported());
    }

    @Test
    void findsTheDeclaredClassName() {
        assertEquals("Solution", Runner.detectClassName("class Solution { }", "Main"));
        assertEquals("Greeter", Runner.detectClassName("public class Greeter {}", "Main"));
        assertEquals("Main", Runner.detectClassName("interface Only {}", "Main"));
    }
}

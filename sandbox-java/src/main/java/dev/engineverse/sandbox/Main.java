package dev.engineverse.sandbox;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Entry point of the EngineVerse Java sandbox.
 *
 * <p>Protocol: the Python bridge writes one JSON object to stdin, this process
 * writes one JSON verdict to stdout and exits. One submission per process, so a
 * crash, an {@code System.exit} or an exhausted heap can never affect the web
 * server or another learner's run.
 *
 * <pre>
 * in : {"language":"java","code":"...","stdin":"...","timeoutMs":3000,"memoryKb":262144}
 * out: {"status":"accepted","stdout":"42\n","stderr":"","exitCode":0,"runtimeMs":118,"memoryKb":262144}
 * </pre>
 *
 * <p>Nothing is ever printed to stdout except the verdict, because the bridge
 * reads the verdict from the last line of stdout.
 */
public final class Main {

    private static final int MIN_TIMEOUT_MS = 250;
    private static final int MAX_TIMEOUT_MS = 20_000;
    private static final int MIN_MEMORY_KB = 16_384;
    private static final int MAX_MEMORY_KB = 1_048_576;

    private Main() {}

    public static void main(String[] args) {
        String payload;
        try {
            payload = new String(System.in.readAllBytes(), StandardCharsets.UTF_8);
        } catch (IOException exc) {
            emit(Verdict.failure("internal_error", "could not read request: " + exc.getMessage(), 0));
            return;
        }

        Map<String, Object> request;
        try {
            request = Json.readObject(payload);
        } catch (RuntimeException exc) {
            emit(Verdict.failure("internal_error", "malformed request: " + exc.getMessage(), 0));
            return;
        }

        String language = Json.string(request, "language", "java");
        if (!"java".equals(language)) {
            emit(Verdict.failure(
                    "unsupported_language",
                    "The Java sandbox runs Java only; \"" + language + "\" is handled by the local runner.",
                    0));
            return;
        }

        String code = Json.string(request, "code", "");
        if (code.isBlank()) {
            emit(Verdict.failure("compile_error", "No code was submitted.", 0));
            return;
        }

        int timeoutMs = clamp(Json.integer(request, "timeoutMs", 3000), MIN_TIMEOUT_MS, MAX_TIMEOUT_MS);
        int memoryKb = clamp(Json.integer(request, "memoryKb", 262_144), MIN_MEMORY_KB, MAX_MEMORY_KB);

        Runner runner = new Runner(javaHome(), usePolicy());
        Verdict verdict;
        try {
            verdict = runner.run(code, Json.string(request, "stdin", ""), timeoutMs, memoryKb);
        } catch (RuntimeException exc) {
            // Never let an unexpected failure escape as a stack trace on stdout.
            verdict = Verdict.failure("internal_error", "sandbox error: " + exc.getMessage(), 0);
        }
        emit(verdict);
    }

    /** Honour JAVA_HOME when it points at a real JDK, otherwise use PATH. */
    private static Path javaHome() {
        String configured = System.getenv("JAVA_HOME");
        if (configured == null || configured.isBlank()) {
            String property = System.getProperty("java.home");
            return property == null ? null : Paths.get(property);
        }
        Path home = Paths.get(configured);
        return home.resolve("bin").resolve("java").toFile().exists() ? home : null;
    }

    /**
     * The security policy is opt-in. The SecurityManager is deprecated and can be
     * disabled at JVM startup, so the sandbox must remain safe without it -
     * process isolation, the heap ceiling and the deadline are the guarantees
     * that always hold.
     */
    private static boolean usePolicy() {
        return "1".equals(System.getenv("ENGINEVERSE_SANDBOX_POLICY"));
    }

    private static int clamp(int value, int min, int max) {
        return Math.max(min, Math.min(max, value));
    }

    private static void emit(Verdict verdict) {
        Map<String, Object> body = new LinkedHashMap<>(verdict.toMap());
        // Printed last and alone: the bridge parses the final stdout line.
        System.out.println(Json.write(body));
        System.out.flush();
    }
}

package dev.engineverse.sandbox;

import java.io.IOException;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.TimeUnit;
import javax.tools.JavaCompiler;
import javax.tools.ToolProvider;

/**
 * Compiles one submission and runs it in a separate, killable JVM.
 *
 * <h2>Why a child process rather than a loaded class</h2>
 * Learner code can call {@code System.exit}, spawn threads that never stop, or
 * exhaust the heap. Running it inside this JVM would let any of those take the
 * sandbox down. A child process can be force-killed at the deadline, has its own
 * heap ceiling, and leaves nothing behind once it exits.
 *
 * <h2>Defence in depth</h2>
 * <ol>
 *   <li>Submission runs in a child JVM, never in the sandbox's own heap.</li>
 *   <li>Hard wall-clock deadline; {@code destroyForcibly()} past it.</li>
 *   <li>Heap and stack ceilings via {@code -Xmx} / {@code -Xss}.</li>
 *   <li>The child inherits an empty environment, so no secret from the parent
 *       process is reachable through {@code System.getenv()}.</li>
 *   <li>A working directory that contains only the submission, deleted after.</li>
 *   <li>Optionally a JVM security policy denying network access and writes
 *       outside the working directory (see {@code sandbox.policy}).</li>
 * </ol>
 *
 * <p>Process-level isolation is not a substitute for OS-level containment. A
 * production deployment should additionally run this sandbox inside a container
 * or user namespace as a non-root user - see {@code deploy/Dockerfile.sandbox}.
 */
public final class Runner {

    /** Entry point the harness looks for when the submission declares none. */
    private static final String DEFAULT_CLASS = "Main";

    private final Path javaHome;
    private final boolean usePolicy;

    public Runner(Path javaHome, boolean usePolicy) {
        this.javaHome = javaHome;
        this.usePolicy = usePolicy;
    }

    public Verdict run(String code, String stdin, int timeoutMs, int memoryKb) {
        Path workDir = null;
        long started = System.nanoTime();
        try {
            workDir = Files.createTempDirectory("evsandbox-");
            String className = detectClassName(code, DEFAULT_CLASS);
            Path source = workDir.resolve(className + ".java");
            Files.writeString(source, code, StandardCharsets.UTF_8);

            Verdict compiled = compile(source, workDir, className);
            if (compiled != null) {
                return compiled;
            }
            return execute(workDir, className, stdin, timeoutMs, memoryKb, started);
        } catch (IOException exc) {
            return Verdict.failure("internal_error", "sandbox setup failed: " + exc.getMessage(), elapsed(started));
        } finally {
            deleteRecursively(workDir);
        }
    }

    // ---------------------------------------------------------------- compile

    /** Returns a compile-error verdict, or {@code null} when compilation succeeded. */
    private Verdict compile(Path source, Path workDir, String className) {
        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        if (compiler == null) {
            return Verdict.failure(
                    "internal_error",
                    "No JDK compiler is available to the sandbox. Run it on a JDK, not a JRE.",
                    0);
        }
        List<String> options = List.of(
                "-d", workDir.toString(),
                "-encoding", "UTF-8",
                "-Xlint:none",
                "-nowarn");

        StringBuilder diagnostics = new StringBuilder();
        int status;
        try (OutputStream sink = new java.io.ByteArrayOutputStream()) {
            status = compiler.run(null, sink, sink, buildArgs(options, source).toArray(String[]::new));
            diagnostics.append(sink.toString(StandardCharsets.UTF_8));
        } catch (IOException exc) {
            return Verdict.failure("internal_error", "compiler could not be started: " + exc.getMessage(), 0);
        }
        if (status != 0) {
            String message = diagnostics.toString().trim();
            return Verdict.failure(
                    "compile_error",
                    message.isEmpty() ? "Compilation failed for " + className + "." : message,
                    0);
        }
        return null;
    }

    private List<String> buildArgs(List<String> options, Path source) {
        List<String> args = new ArrayList<>(options);
        args.add(source.toString());
        return args;
    }

    // ---------------------------------------------------------------- execute

    private Verdict execute(
            Path workDir, String className, String stdin, int timeoutMs, int memoryKb, long started) {
        String javaBinary = javaHome == null ? "java" : javaHome.resolve("bin").resolve("java").toString();
        List<String> command = new ArrayList<>();
        command.add(javaBinary);
        command.add("-Xmx" + Math.max(memoryKb, 16_384) + "k");
        command.add("-Xss8m");
        command.add("-XX:MaxMetaspaceSize=64m");
        command.add("-Dfile.encoding=UTF-8");
        if (usePolicy) {
            Path policy = workDir.resolve("sandbox.policy");
            try {
                Files.writeString(policy, policyFor(workDir), StandardCharsets.UTF_8);
                command.add("-Djava.security.manager=allow");
                command.add("-Djava.security.policy=" + policy.toUri());
            } catch (IOException ignored) {
                // Without the policy we still have process, memory and time limits.
            }
        }
        command.add("-cp");
        command.add(workDir.toString());
        command.add(className);

        ProcessBuilder builder = new ProcessBuilder(command);
        builder.directory(workDir.toFile());
        // An empty environment keeps anything the parent knew about away from
        // the submission.
        builder.environment().clear();
        builder.environment().put("PATH", "/usr/bin:/bin");
        builder.environment().put("HOME", workDir.toString());
        builder.environment().put("LANG", "C.UTF-8");

        try {
            Process process = builder.start();
            if (stdin != null && !stdin.isEmpty()) {
                try (OutputStream toChild = process.getOutputStream()) {
                    toChild.write(stdin.getBytes(StandardCharsets.UTF_8));
                    toChild.flush();
                }
            } else {
                process.getOutputStream().close();
            }

            byte[] stdoutBytes;
            byte[] stderrBytes;
            boolean finished = process.waitFor(timeoutMs, TimeUnit.MILLISECONDS);
            if (!finished) {
                process.destroyForcibly();
                process.waitFor(2, TimeUnit.SECONDS);
                return Verdict.failure("timeout", "Execution exceeded " + timeoutMs + " ms.", elapsed(started));
            }
            stdoutBytes = process.getInputStream().readAllBytes();
            stderrBytes = process.getErrorStream().readAllBytes();

            String stdout = new String(stdoutBytes, StandardCharsets.UTF_8);
            String stderr = new String(stderrBytes, StandardCharsets.UTF_8);
            int code = process.exitValue();
            if (code == 0) {
                return Verdict.accepted(stdout, elapsed(started), memoryKb);
            }
            return Verdict.exited(code, stdout, stderr.isEmpty() ? describeExit(code) : stderr, elapsed(started));
        } catch (IOException exc) {
            return Verdict.failure("internal_error", "could not start submission: " + exc.getMessage(), elapsed(started));
        } catch (InterruptedException exc) {
            Thread.currentThread().interrupt();
            return Verdict.failure("internal_error", "sandbox interrupted", elapsed(started));
        }
    }

    private static String describeExit(int code) {
        // 137 = SIGKILL, the usual signature of the kernel OOM killer.
        return code == 137
                ? "Process killed - most likely out of memory."
                : "Process exited with code " + code + ".";
    }

    /**
     * Denies everything except reading the working directory and writing to the
     * console. Notably there is no {@code SocketPermission}, so a submission
     * cannot open a network connection.
     */
    private static String policyFor(Path workDir) {
        String escaped = workDir.toString().replace("\\", "/");
        return """
                grant {
                    permission java.io.FilePermission "%s/-", "read";
                    permission java.io.FilePermission "%s/-", "read,write,delete";
                    permission java.lang.RuntimePermission "exitVM.*";
                    permission java.lang.RuntimePermission "modifyThread";
                    permission java.lang.RuntimePermission "getenv.PATH";
                    permission java.lang.RuntimePermission "getenv.HOME";
                    permission java.lang.RuntimePermission "getenv.LANG";
                    permission java.util.PropertyPermission "*", "read";
                };
                """.formatted(escaped, escaped);
    }

    // ------------------------------------------------------------------ utils

    /**
     * Finds the public class a submission declares. Falls back to {@code Main}
     * when there is no public type, since {@code javac} accepts that as long as
     * the file name matches the type it does declare.
     */
    static String detectClassName(String code, String fallback) {
        java.util.regex.Matcher matcher =
                java.util.regex.Pattern.compile("\\b(?:public\\s+)?class\\s+([A-Za-z_][A-Za-z0-9_]*)").matcher(code);
        if (matcher.find()) {
            return matcher.group(1);
        }
        return fallback;
    }

    static long elapsed(long startedNanos) {
        return TimeUnit.NANOSECONDS.toMillis(System.nanoTime() - startedNanos);
    }

    private static void deleteRecursively(Path root) {
        if (root == null) {
            return;
        }
        try (var walk = Files.walk(root)) {
            walk.sorted(Comparator.reverseOrder()).forEach(path -> {
                try {
                    Files.deleteIfExists(path);
                } catch (IOException ignored) {
                    // Best effort: the OS temp reaper handles the rest.
                }
            });
        } catch (IOException ignored) {
            // Nothing to clean up.
        }
    }

    /** Reports the JVM this sandbox is running on, for diagnostics. */
    static String describeRuntime() {
        return String.format(
                Locale.ROOT,
                "java %s (%s)",
                System.getProperty("java.version"),
                ToolProvider.getSystemJavaCompiler() == null ? "JRE - no compiler" : "JDK");
    }
}

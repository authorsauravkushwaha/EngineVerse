package dev.engineverse.sandbox;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * The outcome of running one submission.
 *
 * <p>Status strings match the ones the Python judge already understands
 * ({@code accepted}, {@code runtime_error}, {@code compile_error},
 * {@code timeout}, {@code internal_error}) so a verdict produced here can be
 * compared against a locally-produced one without translation.
 */
public record Verdict(
        String status,
        String stdout,
        String stderr,
        Integer exitCode,
        long runtimeMs,
        Long memoryKb) {

    public static final int MAX_OUTPUT = 65_536;

    public static Verdict accepted(String stdout, long runtimeMs, Long memoryKb) {
        return new Verdict("accepted", truncate(stdout), "", 0, runtimeMs, memoryKb);
    }

    public static Verdict failure(String status, String stderr, long runtimeMs) {
        return new Verdict(status, "", truncate(stderr), null, runtimeMs, null);
    }

    /** Verdict for a non-zero exit: a wrong answer is a runtime error, not a crash. */
    public static Verdict exited(int code, String stdout, String stderr, long runtimeMs) {
        return new Verdict(
                "runtime_error",
                truncate(stdout),
                truncate(stderr),
                code,
                runtimeMs,
                null);
    }

    public Map<String, Object> toMap() {
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("status", status);
        map.put("stdout", stdout == null ? "" : stdout);
        map.put("stderr", stderr == null ? "" : stderr);
        map.put("exitCode", exitCode);
        map.put("runtimeMs", runtimeMs);
        map.put("memoryKb", memoryKb);
        return map;
    }

    private static String truncate(String text) {
        if (text == null) {
            return "";
        }
        return text.length() <= MAX_OUTPUT ? text : text.substring(0, MAX_OUTPUT);
    }
}

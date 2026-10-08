package dev.engineverse.sandbox;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.LinkedHashMap;
import java.util.Map;
import org.junit.jupiter.api.Test;

class JsonTest {

    @Test
    void readsTheShapeTheBridgeSends() {
        Map<String, Object> request =
                Json.readObject("{\"language\":\"java\",\"code\":\"class Main{}\",\"timeoutMs\":3000}");
        assertEquals("java", Json.string(request, "language", ""));
        assertEquals("class Main{}", Json.string(request, "code", ""));
        assertEquals(3000, Json.integer(request, "timeoutMs", 0));
    }

    @Test
    void fallsBackForMissingKeys() {
        Map<String, Object> request = Json.readObject("{}");
        assertEquals("java", Json.string(request, "language", "java"));
        assertEquals(1500, Json.integer(request, "timeoutMs", 1500));
    }

    @Test
    void unescapesControlCharactersInCode() {
        // Submissions routinely contain newlines, tabs and quotes.
        Map<String, Object> request =
                Json.readObject("{\"code\":\"System.out.println(\\\"hi\\\");\\n\\tint x = 1;\"}");
        assertEquals("System.out.println(\"hi\");\n\tint x = 1;", Json.string(request, "code", ""));
    }

    @Test
    void roundTripsUnicodeVerbatim() {
        Map<String, Object> request = Json.readObject("{\"code\":\"// \u09ac\u09be\u0982\u09b2\u09be \\u00e9\"}");
        String code = Json.string(request, "code", "");
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("stderr", code);
        assertTrue(Json.write(out).contains(code), "unicode must survive a write/read round trip");
    }

    @Test
    void escapesControlCharactersOnWrite() {
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("stdout", "line one\nline two\t\"quoted\"");
        String json = Json.write(out);
        assertEquals("{\"stdout\":\"line one\\nline two\\t\\\"quoted\\\"\"}", json);
        assertEquals("line one\nline two\t\"quoted\"", Json.string(Json.readObject(json), "stdout", ""));
    }

    @Test
    void writesNullsAsJsonNull() {
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("exitCode", null);
        assertEquals("{\"exitCode\":null}", Json.write(out));
    }

    @Test
    void rejectsNonObjectPayloads() {
        assertThrows(IllegalArgumentException.class, () -> Json.readObject("[1,2,3]"));
        assertThrows(IllegalArgumentException.class, () -> Json.readObject("not json"));
        assertThrows(IllegalArgumentException.class, () -> Json.readObject("{\"unterminated\":"));
    }

    @Test
    void readsNestedObjectsAndArrays() {
        Map<String, Object> request =
                Json.readObject("{\"meta\":{\"a\":1},\"list\":[1,2,3],\"flag\":true,\"none\":null}");
        assertEquals(4, request.size());
        assertEquals(Boolean.TRUE, request.get("flag"));
        assertTrue(request.get("meta") instanceof Map);
        assertTrue(request.get("list") instanceof java.util.List);
    }
}

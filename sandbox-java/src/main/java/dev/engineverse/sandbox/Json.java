package dev.engineverse.sandbox;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * A tiny, dependency-free JSON reader and writer.
 *
 * <p>The sandbox deliberately pulls in no third-party libraries: it runs
 * untrusted code, so every extra class on the classpath is extra attack surface
 * and extra supply-chain risk. The bridge only ever exchanges flat objects with
 * string/number/boolean values, which is all this needs to handle.
 */
public final class Json {

    private Json() {}

    // ------------------------------------------------------------------ parse

    public static Map<String, Object> readObject(String text) {
        Parser parser = new Parser(text == null ? "" : text);
        parser.skipWhitespace();
        Object value = parser.readValue();
        if (!(value instanceof Map)) {
            throw new IllegalArgumentException("expected a JSON object");
        }
        @SuppressWarnings("unchecked")
        Map<String, Object> map = (Map<String, Object>) value;
        return map;
    }

    public static String string(Map<String, Object> map, String key, String fallback) {
        Object value = map.get(key);
        return value == null ? fallback : String.valueOf(value);
    }

    public static int integer(Map<String, Object> map, String key, int fallback) {
        Object value = map.get(key);
        if (value instanceof Number number) {
            return number.intValue();
        }
        if (value instanceof String text && !text.isBlank()) {
            try {
                return (int) Double.parseDouble(text);
            } catch (NumberFormatException ignored) {
                return fallback;
            }
        }
        return fallback;
    }

    // ------------------------------------------------------------------ write

    public static String write(Map<String, Object> map) {
        StringBuilder out = new StringBuilder("{");
        boolean first = true;
        for (Map.Entry<String, Object> entry : map.entrySet()) {
            if (!first) {
                out.append(',');
            }
            first = false;
            quote(out, entry.getKey());
            out.append(':');
            writeValue(out, entry.getValue());
        }
        return out.append('}').toString();
    }

    private static void writeValue(StringBuilder out, Object value) {
        if (value == null) {
            out.append("null");
        } else if (value instanceof Number || value instanceof Boolean) {
            out.append(value);
        } else {
            quote(out, String.valueOf(value));
        }
    }

    private static void quote(StringBuilder out, String text) {
        out.append('"');
        for (int i = 0; i < text.length(); i++) {
            char c = text.charAt(i);
            switch (c) {
                case '"' -> out.append("\\\"");
                case '\\' -> out.append("\\\\");
                case '\n' -> out.append("\\n");
                case '\r' -> out.append("\\r");
                case '\t' -> out.append("\\t");
                case '\b' -> out.append("\\b");
                case '\f' -> out.append("\\f");
                default -> {
                    if (c < 0x20) {
                        out.append(String.format("\\u%04x", (int) c));
                    } else {
                        out.append(c);
                    }
                }
            }
        }
        out.append('"');
    }

    // ----------------------------------------------------------------- parser

    private static final class Parser {
        private final String text;
        private int index;

        Parser(String text) {
            this.text = text;
        }

        void skipWhitespace() {
            while (index < text.length() && Character.isWhitespace(text.charAt(index))) {
                index++;
            }
        }

        Object readValue() {
            skipWhitespace();
            if (index >= text.length()) {
                throw new IllegalArgumentException("unexpected end of JSON");
            }
            char c = text.charAt(index);
            return switch (c) {
                case '{' -> readObjectValue();
                case '[' -> readArrayValue();
                case '"' -> readString();
                case 't', 'f' -> readBoolean();
                case 'n' -> readNull();
                default -> readNumber();
            };
        }

        private Map<String, Object> readObjectValue() {
            Map<String, Object> map = new LinkedHashMap<>();
            index++; // consume '{'
            skipWhitespace();
            if (peek() == '}') {
                index++;
                return map;
            }
            while (true) {
                skipWhitespace();
                String key = readString();
                skipWhitespace();
                expect(':');
                map.put(key, readValue());
                skipWhitespace();
                char c = next();
                if (c == '}') {
                    return map;
                }
                if (c != ',') {
                    throw new IllegalArgumentException("expected ',' or '}' at " + index);
                }
            }
        }

        private List<Object> readArrayValue() {
            List<Object> list = new ArrayList<>();
            index++; // consume '['
            skipWhitespace();
            if (peek() == ']') {
                index++;
                return list;
            }
            while (true) {
                list.add(readValue());
                skipWhitespace();
                char c = next();
                if (c == ']') {
                    return list;
                }
                if (c != ',') {
                    throw new IllegalArgumentException("expected ',' or ']' at " + index);
                }
            }
        }

        private String readString() {
            expect('"');
            StringBuilder out = new StringBuilder();
            while (true) {
                char c = next();
                if (c == '"') {
                    return out.toString();
                }
                if (c != '\\') {
                    out.append(c);
                    continue;
                }
                char escape = next();
                switch (escape) {
                    case '"' -> out.append('"');
                    case '\\' -> out.append('\\');
                    case '/' -> out.append('/');
                    case 'n' -> out.append('\n');
                    case 'r' -> out.append('\r');
                    case 't' -> out.append('\t');
                    case 'b' -> out.append('\b');
                    case 'f' -> out.append('\f');
                    case 'u' -> {
                        if (index + 4 > text.length()) {
                            throw new IllegalArgumentException("bad \\u escape");
                        }
                        out.append((char) Integer.parseInt(text.substring(index, index + 4), 16));
                        index += 4;
                    }
                    default -> throw new IllegalArgumentException("bad escape \\" + escape);
                }
            }
        }

        private Boolean readBoolean() {
            if (text.startsWith("true", index)) {
                index += 4;
                return Boolean.TRUE;
            }
            if (text.startsWith("false", index)) {
                index += 5;
                return Boolean.FALSE;
            }
            throw new IllegalArgumentException("expected boolean at " + index);
        }

        private Object readNull() {
            if (text.startsWith("null", index)) {
                index += 4;
                return null;
            }
            throw new IllegalArgumentException("expected null at " + index);
        }

        private Double readNumber() {
            int start = index;
            if (peek() == '-' || peek() == '+') {
                index++;
            }
            while (index < text.length()
                    && "0123456789.eE+-".indexOf(text.charAt(index)) >= 0) {
                index++;
            }
            return Double.parseDouble(text.substring(start, index));
        }

        private char peek() {
            if (index >= text.length()) {
                throw new IllegalArgumentException("unexpected end of JSON");
            }
            return text.charAt(index);
        }

        private char next() {
            char c = peek();
            index++;
            return c;
        }

        private void expect(char expected) {
            char c = next();
            if (c != expected) {
                throw new IllegalArgumentException("expected '" + expected + "' but found '" + c + "'");
            }
        }
    }
}

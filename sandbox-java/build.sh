#!/usr/bin/env bash
#
# Builds the EngineVerse Java sandbox into target/engineverse-sandbox.jar.
#
# The Python web server locates that jar via the JAVA_SANDBOX_JAR setting
# (default: sandbox-java/target/engineverse-sandbox.jar), so running this script
# is all that is needed to switch the judge from the local runner to the JVM one.
#
# Requires: JDK 21+ and Maven 3.9+.
set -euo pipefail

cd "$(dirname "$0")"

if ! command -v mvn >/dev/null 2>&1; then
  echo "error: Maven is not installed. Install Maven 3.9+ or run ./build.sh inside deploy/Dockerfile.sandbox." >&2
  exit 1
fi

if ! command -v javac >/dev/null 2>&1; then
  echo "error: no JDK on PATH. A JRE is not enough - the sandbox compiles submissions." >&2
  exit 1
fi

MAJOR=$(javac -version 2>&1 | awk '{print $2}' | cut -d. -f1)
if [ "${MAJOR:-0}" -lt 21 ]; then
  echo "error: JDK 21 or newer is required (found $(javac -version 2>&1))." >&2
  exit 1
fi

echo "==> Building the EngineVerse sandbox"
mvn -q -DskipTests package

JAR="target/engineverse-sandbox.jar"
if [ ! -f "$JAR" ]; then
  echo "error: build finished but $JAR is missing." >&2
  exit 1
fi

echo "==> Built $JAR"

# Smoke-test the artifact: a trivial submission must come back accepted.
echo "==> Smoke test"
printf '%s' '{"language":"java","code":"public class Main { public static void main(String[] a) { System.out.println(42); } }","stdin":"","timeoutMs":10000,"memoryKb":262144}' \
  | java -Xmx256m -jar "$JAR" | tee /tmp/ev-sandbox-smoke.json | grep -q '"status":"accepted"' \
  || { echo "error: smoke test did not return accepted:" >&2; cat /tmp/ev-sandbox-smoke.json >&2; exit 1; }

echo "==> OK"

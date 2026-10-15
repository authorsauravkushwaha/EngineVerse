#!/usr/bin/env python3
"""Execute TRUSTED authored academy examples, never learner submissions.

This is a developer content check, not a public execution service or sandbox.
Missing toolchains are reported as SKIP; incorrect output/compilation is FAIL.
Use --require-all to make unavailable compilers fail CI on a provisioned host.
"""
from __future__ import annotations

import argparse
import bisect
import itertools
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / 'backend'):
    sys.path.insert(0, str(path))
from seed_data.academy import UNITS, PROFILES, validate_unit


def tool(language):
    if language == 'sql':
        return 'sqlite3 (Python standard library)'
    if language == 'python':
        return sys.executable
    if language == 'typescript':
        local = ROOT / '.toolchain/typescript/node_modules/.bin/tsc'
        return str(local) if local.exists() else shutil.which('tsc')
    return shutil.which({'c': 'gcc', 'cpp': 'g++', 'java': 'javac', 'csharp': 'dotnet',
                         'javascript': 'node', 'go': 'go', 'rust': 'rustc'}[language])


def run(command, directory, stdin=''):
    result = subprocess.run(command, cwd=directory, input=stdin, text=True,
                            capture_output=True, timeout=40)
    if result.returncode:
        raise AssertionError(f'{command[0]} exited {result.returncode}: {result.stderr[:2000]}')
    return result.stdout.replace('\r\n', '\n')


def execute(language, code, inputs):
    """Compile once, execute trusted text for each disclosed fixture."""
    if language == 'sql':
        with sqlite3.connect(':memory:') as conn:
            statements = [s.strip() for s in code.split(';') if s.strip()]
            for statement in statements[:-1]:
                conn.execute(statement)
            return ['\n'.join(str(row[0]) for row in conn.execute(statements[-1])) + '\n']
    with tempfile.TemporaryDirectory(prefix='ev-authored-') as temp:
        directory = Path(temp)
        extension = PROFILES[language]['extension']
        filename = 'Main.java' if language == 'java' else f'lesson.{extension}'
        (directory / filename).write_text(code)
        compiler = tool(language)
        if language in ('c', 'cpp'):
            run([compiler, '-std=c17' if language == 'c' else '-std=c++17',
                 '-Wall', '-Wextra', '-Werror', filename, '-o', 'lesson'], directory)
            command = [str(directory / 'lesson')]
        elif language == 'java':
            run([compiler, '--release', '17', filename], directory)
            command = [shutil.which('java'), '-cp', temp, 'Main']
        elif language == 'typescript':
            run([compiler, '--strict', '--target', 'ES2022', filename], directory)
            command = [shutil.which('node'), 'lesson.js']
        elif language == 'csharp':
            # A supported installed SDK chooses its own default target framework.
            run([compiler, 'new', 'console', '--no-restore', '--force'], directory)
            (directory / 'lesson.cs').rename(directory / 'Program.cs')
            run([compiler, 'build', '--nologo', '-o', 'compiled'], directory)
            command = [compiler, str(directory / 'compiled' / (directory.name + '.dll'))]
        elif language == 'go':
            run([compiler, 'build', '-o', 'lesson', filename], directory)
            command = [str(directory / 'lesson')]
        elif language == 'rust':
            run([compiler, '--edition=2021', filename, '-o', 'lesson'], directory)
            command = [str(directory / 'lesson')]
        else:
            command = [compiler, filename]
        return [run(command, directory, stdin) for stdin in inputs]


def bounds_fixtures():
    return [(list(values), target)
            for n in range(5)
            for values in itertools.combinations_with_replacement((-1, 0, 1), n)
            for target in (-2, -1, 0, 1, 2)]


def bounds_harness(language, source):
    fixtures = bounds_fixtures()
    # Keep the authored function unchanged, replace only its sample main/calls.
    if language == 'python':
        prefix = source.split('print(lower_bound')[0]
        calls = [f'print(lower_bound({values!r}, {target}))' for values, target in fixtures]
        return prefix + '\n'.join(calls)
    if language == 'java':
        prefix = source.split('    public static void main')[0]
        calls = [f'System.out.println(lowerBound(new int[]{{{",".join(map(str, values))}}}, {target}));'
                 for values, target in fixtures]
        return prefix + 'public static void main(String[] args) {\n' + '\n'.join(calls) + '\n}}'
    if language == 'csharp':
        prefix = source.split('Console.WriteLine')[0]
        calls = [f'Console.WriteLine(LowerBound(new int[]{{{",".join(map(str, values))}}}, {target}));'
                 for values, target in fixtures]
        return prefix + '\n'.join(calls)
    prefix = source.split('int main(')[0]
    calls = []
    for i, (values, target) in enumerate(fixtures):
        if language == 'cpp':
            calls.append('std::cout << lower_bound_index({' + ','.join(map(str, values)) + f'}}, {target}) << \'\\n\';')
        elif values:
            calls.append(f'const int a{i}[] = {{{",".join(map(str, values))}}}; '
                         f'printf("%zu\\n", lower_bound(a{i}, {len(values)}, {target}));')
        else:
            calls.append(f'printf("%zu\\n", lower_bound(NULL, 0, {target}));')
    return prefix + 'int main(void) {\n' + '\n'.join(calls) + '\nreturn 0;\n}'


def verify_unit(slug, unit):
    validate_unit(unit)
    language = unit['language']
    compiler = tool(language)
    if not compiler:
        return {'unit': slug, 'status': 'SKIP', 'detail': f'{language} toolchain unavailable', 'checks': 0}
    checks = 0
    try:
        for example in unit['code_examples']:
            if example['expected'] is not None:
                assert execute(language, example['code'], ['']) == [example['expected']], 'example output mismatch'
                checks += 1
        if unit['kind'] == 'bounds':
            assert execute(language, unit['reference'], ['']) == ['3\n0\n'], 'reference demo mismatch'
            checks += 1
            expected = ''.join(f'{bisect.bisect_left(values, target)}\n' for values, target in bounds_fixtures())
            assert execute(language, bounds_harness(language, unit['reference']), ['']) == [expected], 'boundary oracle mismatch'
            checks += len(bounds_fixtures())
        elif language == 'sql':
            assert execute(language, unit['reference'], ['']) == ['12\n']
            checks += 1
            query = [statement.strip() for statement in unit['reference'].split(';') if statement.strip()][-1]
            with sqlite3.connect(':memory:') as conn:
                conn.execute('CREATE TABLE adjustments(id INTEGER PRIMARY KEY, amount INTEGER NOT NULL)')
                for values in ([], [-2, 0, 5, 7], [5, 5], [-5, 0], [1000000] * 1000):
                    conn.execute('DELETE FROM adjustments')
                    conn.executemany('INSERT INTO adjustments(amount) VALUES (?)', [(x,) for x in values])
                    assert conn.execute(query).fetchone()[0] == sum(x for x in values if x > 0)
                    checks += 1
                # Reject realistic wrong approaches using counterexamples.
                assert conn.execute('SELECT SUM(DISTINCT amount) FROM adjustments').fetchone()[0] != 1000000000
                checks += 1
        elif language == 'typescript':
            code = unit['reference']
            for test in unit['tests']:
                values = list(map(int, test['input'].split()))[1:]
                code += f'console.log(positiveTotal({json.dumps(values)}));\n'
            assert execute(language, code, ['']) == [''.join(test['expected'] for test in unit['tests'])]
            checks += len(unit['tests'])
        else:
            tests = unit['tests']
            actual = execute(language, unit['reference'], [t['input'] for t in tests])
            assert actual == [t['expected'] for t in tests], 'reference fixture mismatch'
            checks += len(tests)
        return {'unit': slug, 'status': 'PASS', 'detail': str(compiler), 'checks': checks}
    except (AssertionError, subprocess.SubprocessError, OSError) as exc:
        return {'unit': slug, 'status': 'FAIL', 'detail': str(exc), 'checks': checks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--require-all', action='store_true')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    results = [verify_unit(slug, unit) for slug, unit in UNITS.items()]
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for result in results:
            print(f"{result['status']:4} {result['unit']}: {result['checks']} checks; {result['detail']}")
        print(f"{sum(r['checks'] for r in results)} checks; "
              f"{sum(r['status'] == 'PASS' for r in results)} units passed; "
              f"{sum(r['status'] == 'SKIP' for r in results)} skipped")
    return int(any(r['status'] == 'FAIL' or (args.require_all and r['status'] == 'SKIP') for r in results))


if __name__ == '__main__':
    raise SystemExit(main())

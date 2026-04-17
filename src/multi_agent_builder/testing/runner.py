from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys

from ..models import TestFailure, TestReport


class ValidationRunner:
    """Runs generated validation suites in a subprocess for isolation."""

    @staticmethod
    def _count_tests(file_path: Path) -> int:
        return len(re.findall(r"^\s*def test_", file_path.read_text(encoding="utf-8"), flags=re.MULTILINE))

    def run(self, prototype_dir: Path) -> TestReport:
        compile_result = subprocess.run(
            [sys.executable, "-m", "compileall", "app"],
            cwd=prototype_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        test_result = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
            cwd=prototype_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        raw_output = "\n".join(
            [
                compile_result.stdout,
                compile_result.stderr,
                test_result.stdout,
                test_result.stderr,
            ]
        ).strip()
        failures = self._parse_failures(test_result.stdout + "\n" + test_result.stderr)
        unit_tests = self._count_tests(prototype_dir / "tests" / "test_service.py")
        integration_tests = self._count_tests(prototype_dir / "tests" / "test_api.py")
        passed = compile_result.returncode == 0 and test_result.returncode == 0
        if not passed and not failures:
            failures = [
                TestFailure(
                    suite="validation",
                    test_name="subprocess",
                    message="Validation subprocess failed",
                    traceback=raw_output,
                )
            ]
        return TestReport(
            passed=passed,
            unit_tests=unit_tests,
            integration_tests=integration_tests,
            failures=failures,
            raw_output=raw_output,
        )

    def _parse_failures(self, output: str) -> list[TestFailure]:
        pattern = re.compile(r"^(FAIL|ERROR): (?P<name>test_[^\s]+) \((?P<suite>[^)]+)\)", re.MULTILINE)
        failures = []
        for match in pattern.finditer(output):
            failures.append(
                TestFailure(
                    suite=match.group("suite"),
                    test_name=match.group("name"),
                    message=match.group(1),
                    traceback=output,
                )
            )
        return failures


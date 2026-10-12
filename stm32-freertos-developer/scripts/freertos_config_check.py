#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FreeRTOSConfig.h configuration file validation tool

Features:
- Checks the key configuration macro definitions in FreeRTOSConfig.h
- Validates the validity of the configuration values
- Outputs the result in JSON format (convenient for CI integration)
- Supports command-line arguments and standard input

Usage:
    python freertos_config_check.py FreeRTOSConfig.h
    python freertos_config_check.py FreeRTOSConfig.h --json
    cat FreeRTOSConfig.h | python freertos_config_check.py --stdin

Author: STM32 + FreeRTOS Agent Skill
"""

import re
import sys
import json
import argparse
from typing import Dict, List, Optional, Tuple, Any, Sequence
from dataclasses import dataclass, asdict
from enum import Enum


class CheckStatus(Enum):
    """Status of a check result"""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIP = "skip"


@dataclass
class ConfigCheck:
    """Result of a single configuration check"""
    name: str           # Macro name
    expected: str       # Expected value
    actual: Optional[str]  # Actual value
    status: str         # pass/fail/warning/skip
    message: str        # Explanation


@dataclass
class CheckResult:
    """Overall check result"""
    file: str
    checks: List[Dict[str, Any]]
    summary: Dict[str, int]


class FreeRTOSConfigChecker:
    """FreeRTOSConfig.h configuration file checker"""

    # Required configuration items and their expected values
    REQUIRED_CHECKS = [
        ("configUSE_PREEMPTION", "1", "Enable preemptive scheduling"),
        ("configUSE_PORT_OPTIMISED_TASK_SELECTION", "1", "Use hardware priority selection"),
        ("configTICK_RATE_HZ", None, "System tick frequency (usually 1000)"),
    ]

    # Recommended configuration items and their expected values
    RECOMMENDED_CHECKS = [
        ("configUSE_IDLE_HOOK", "1", "Enable the idle task hook (used for low power)"),
        ("configUSE_TICK_HOOK", "0", "Disable the tick hook (unless it is required)"),
        ("configCHECK_FOR_STACK_OVERFLOW", "2", "Enable stack overflow detection"),
        ("configUSE_TRACE_FACILITY", "1", "Enable the trace facility"),
        ("configUSE_STATS_FORMATTING_FUNCTIONS", "1", "Enable the statistics formatting functions"),
        ("configGENERATE_RUN_TIME_STATS", "0", "Run-time statistics (can be enabled while debugging)"),
        ("configUSE_CO_ROUTINES", "0", "Disable co-routines (tasks are recommended)"),
        ("configMAX_PRIORITIES", None, "Maximum number of task priorities (usually 32)"),
        ("configMINIMAL_STACK_SIZE", None, "Minimum stack size (usually 128)"),
        ("configTOTAL_HEAP_SIZE", None, "Dynamic allocation heap size (set according to requirements)"),
    ]

    # Optional configuration items and their expected values
    OPTIONAL_CHECKS = [
        ("configUSE_MUTEXES", "1", "Enable mutexes"),
        ("configUSE_RECURSIVE_MUTEXES", "1", "Enable recursive mutexes"),
        ("configUSE_COUNTING_SEMAPHORES", "1", "Enable counting semaphores"),
        ("configUSE_TASK_NOTIFICATIONS", "1", "Enable task notifications"),
        ("configUSE_TIMERS", "1", "Enable software timers"),
        ("configTIMER_TASK_PRIORITY", None, "Timer task priority"),
        ("configTIMER_QUEUE_LENGTH", None, "Timer queue length"),
        ("configTIMER_TASK_STACK_DEPTH", None, "Timer task stack depth"),
        ("configUSE_TICKLESS_IDLE", "0", "Disable Tickless low power (extra configuration is required)"),
        ("configCPU_CLOCK_HZ", None, "CPU clock frequency"),
        ("configSYSTICK_CLOCK_HZ", None, "SysTick clock frequency"),
        ("configKERNEL_INTERRUPT_PRIORITY", None, "Kernel interrupt priority"),
        ("configMAX_SYSCALL_INTERRUPT_PRIORITY", None, "Maximum syscall interrupt priority"),
        ("configASSERT(x)", None, "Assertion definition"),
    ]

    # Disabled configuration items
    DISABLED_CHECKS: List[Tuple[str, Optional[str], str]] = [
        ("configUSE_16_BIT_TICKS", "0", "Disable 16-bit ticks (must be 0)"),
    ]

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.checks: List[ConfigCheck] = []

    def parse_config_file(self, content: str) -> Dict[str, str]:
        """
        Parse the contents of a FreeRTOSConfig.h file

        Args:
            content: File contents as a string

        Returns:
            Dictionary of macro definitions {macro name: value}
        """
        defines = {}

        # Match #define macro definitions
        pattern = r'^\s*#\s*define\s+(\w+)(?:\s+([^\/\n]+))?'
        for match in re.finditer(pattern, content, re.MULTILINE):
            name = match.group(1)
            value = match.group(2)
            if value:
                # Clean up the value
                value = value.strip()
                # Remove trailing comments
                comment_idx = value.find('//')
                if comment_idx >= 0:
                    value = value[:comment_idx].strip()
                defines[name] = value

        return defines

    def check_value(self, name: str, expected: Optional[str],
                    actual: Optional[str]) -> Tuple[CheckStatus, str]:
        """
        Check a configuration value

        Args:
            name: Macro name
            expected: Expected value (None means it only has to exist)
            actual: Actual value

        Returns:
            (status, explanation)
        """
        if actual is None:
            return CheckStatus.FAIL, f"Macro {name} is not defined"

        # Handle special expected values
        if expected is None:
            # It only has to exist
            return CheckStatus.PASS, f"{name} = {actual}"

        # Exact match
        if actual == expected:
            return CheckStatus.PASS, f"{name} = {actual}"

        # Numeric match (handles base prefixes)
        try:
            if actual.startswith(('0x', '0X')):
                actual_int = int(actual, 16)
            elif actual.startswith('0') and len(actual) > 1:
                actual_int = int(actual, 8)
            else:
                actual_int = int(actual)

            if expected.startswith(('0x', '0X')):
                expected_int = int(expected, 16)
            else:
                expected_int = int(expected)

            if actual_int == expected_int:
                return CheckStatus.PASS, f"{name} = {actual}"
        except ValueError:
            pass

        # Value mismatch
        if expected in ('0', '1'):
            return CheckStatus.FAIL, f"{name} should be {expected}, but it is {actual}"
        else:
            return CheckStatus.WARNING, f"the recommended value of {name} is {expected}, but it is {actual}"

    def run_checks(self, defines: Dict[str, str],
                   check_list: Sequence[Tuple[str, Optional[str], str]],
                   category: str) -> None:
        """
        Run a group of checks

        Args:
            defines: Dictionary of macro definitions
            check_list: List of check items
            category: Check category (used for the output)
        """
        for name, expected, description in check_list:
            actual = defines.get(name)

            status, message = self.check_value(name, expected, actual)

            if status == CheckStatus.FAIL and actual is None:
                message = f"{description}: {message}"

            self.checks.append(ConfigCheck(
                name=name,
                expected=str(expected) if expected else "defined",
                actual=actual,
                status=status.value,
                message=message
            ))

            if self.verbose and status != CheckStatus.PASS:
                print(f"[{category}] {name}: {message}")

    def check_config(self, content: str, filename: str = "FreeRTOSConfig.h") -> CheckResult:
        """
        Perform the complete configuration check

        Args:
            content: File contents
            filename: File name (used for the output)

        Returns:
            Check result
        """
        defines = self.parse_config_file(content)
        self.checks = []

        # Run all the checks
        self.run_checks(defines, self.REQUIRED_CHECKS, "required")
        self.run_checks(defines, self.RECOMMENDED_CHECKS, "recommended")
        self.run_checks(defines, self.OPTIONAL_CHECKS, "optional")
        self.run_checks(defines, self.DISABLED_CHECKS, "disabled")

        # Calculate the summary
        summary = {
            "passed": sum(1 for c in self.checks if c.status == "pass"),
            "failed": sum(1 for c in self.checks if c.status == "fail"),
            "warnings": sum(1 for c in self.checks if c.status == "warning"),
            "skipped": sum(1 for c in self.checks if c.status == "skip"),
            "total": len(self.checks)
        }

        # Build the result
        result = CheckResult(
            file=filename,
            checks=[asdict(c) for c in self.checks],
            summary=summary
        )

        return result

    def print_result(self, result: CheckResult) -> None:
        """Print the result in a human-readable form"""
        print(f"\n{'='*60}")
        print(f"FreeRTOSConfig.h check result: {result.file}")
        print(f"{'='*60}")

        # Print the summary
        summary = result.summary
        print(f"\nSummary: passed={summary['passed']}, "
              f"failed={summary['failed']}, "
              f"warnings={summary['warnings']}, "
              f"total={summary['total']}")

        # Print the detailed information
        print(f"\nDetailed results:")
        print("-" * 60)

        # Print the failures first
        for check in result.checks:
            if check["status"] == "fail":
                self._print_check(check, "❌")

        # Then print the warnings
        for check in result.checks:
            if check["status"] == "warning":
                self._print_check(check, "⚠️")

        # Finally print the passes
        passed_count = 0
        for check in result.checks:
            if check["status"] == "pass":
                passed_count += 1
                if passed_count <= 10:  # Only show the first 10
                    self._print_check(check, "✅")

        if passed_count > 10:
            print(f"... plus {passed_count - 10} checks that passed")

        print("-" * 60)

        # Print the recommendations
        failed_checks = [c for c in result.checks if c["status"] == "fail"]
        if failed_checks:
            print(f"\nSuggested fixes:")
            for check in failed_checks:
                print(f"  - {check['name']}: {check['message']}")

    def _print_check(self, check: Dict, icon: str) -> None:
        """Print a single check result"""
        print(f"{icon} {check['name']}")
        print(f"   expected: {check['expected']}, actual: {check['actual']}")
        print(f"   note: {check['message']}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="FreeRTOSConfig.h configuration file validation tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s FreeRTOSConfig.h
  %(prog)s FreeRTOSConfig.h --json
  %(prog)s FreeRTOSConfig.h --verbose
  cat FreeRTOSConfig.h | %(prog)s --stdin
        """
    )

    parser.add_argument("filename", nargs="?", help="Path to the configuration file")
    parser.add_argument("--json", action="store_true",
                        help="Output JSON format")
    parser.add_argument("--stdin", action="store_true",
                        help="Read from standard input")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Verbose output")
    parser.add_argument("--output", "-o", help="Write the output to a file")

    args = parser.parse_args()

    # Read the configuration file
    content = ""

    if args.stdin:
        content = sys.stdin.read()
        filename = "<stdin>"
    elif args.filename:
        try:
            with open(args.filename, "r", encoding="utf-8") as f:
                content = f.read()
            filename = args.filename
        except FileNotFoundError:
            print(f"Error: file not found: {args.filename}")
            sys.exit(1)
        except Exception as e:
            print(f"Error: failed to read the file: {e}")
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)

    # Check the file contents
    if not content.strip():
        print("Error: the configuration file is empty")
        sys.exit(1)

    # Run the checks
    checker = FreeRTOSConfigChecker(verbose=args.verbose)
    result = checker.check_config(content, filename)

    # Output the result
    if args.json:
        # JSON format output
        output = json.dumps(asdict(result), indent=2, ensure_ascii=False)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
        else:
            print(output)
    else:
        # Human-readable format
        checker.print_result(result)

        # If an output file was specified
        if args.output:
            output = json.dumps(asdict(result), indent=2, ensure_ascii=False)
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"\nResult saved to: {args.output}")

    # Return the exit code
    if result.summary["failed"] > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()

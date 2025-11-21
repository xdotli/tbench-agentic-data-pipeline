#!/usr/bin/env python3
"""
Simple Harbor + Claude Code test on existing Harbor format task.

This directly tests the existing Harbor task without waiting for SDK agents.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime


def find_harbor_tasks():
    """Find all Harbor format tasks."""
    shared_workspace = Path("shared_workspace/data_points")
    harbor_tasks = []

    for task_dir in shared_workspace.iterdir():
        if not task_dir.is_dir():
            continue

        # Check Harbor format
        has_instruction = (task_dir / "instruction.md").exists()
        has_task_toml = (task_dir / "task.toml").exists()
        has_environment = (task_dir / "environment").exists()
        has_solution = (task_dir / "solution").exists()
        has_tests = (task_dir / "tests").exists()

        if all([has_instruction, has_task_toml, has_environment, has_solution, has_tests]):
            harbor_tasks.append(task_dir)
            print(f"✓ Found Harbor task: {task_dir.name}")

    return harbor_tasks


def validate_harbor_task(task_dir):
    """Validate Harbor task structure."""
    print(f"\n{'─'*60}")
    print(f"Validating: {task_dir.name}")
    print(f"{'─'*60}")

    try:
        result = subprocess.run(
            ["harbor", "tasks", "validate", str(task_dir)],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(Path.cwd())
        )

        if result.returncode == 0:
            print("✅ Validation PASSED")
            return True
        else:
            print(f"❌ Validation FAILED")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_with_claude_code(task_dir, api_key):
    """Test task with Harbor + Claude Code."""
    print(f"\n{'─'*60}")
    print(f"Testing with Claude Code: {task_dir.name}")
    print(f"{'─'*60}")

    try:
        # Set up environment
        env = os.environ.copy()
        env["ANTHROPIC_API_KEY"] = api_key

        # Run harbor agents run
        result = subprocess.run(
            [
                "harbor",
                "agents",
                "run",
                "claude-code",
                "--model", "anthropic/claude-sonnet-4-5",
                "--task", str(task_dir)
            ],
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
            env=env,
            cwd=str(Path.cwd())
        )

        print(f"\nReturn code: {result.returncode}")
        print(f"\nOutput (last 100 lines):")
        print("\n".join(result.stdout.split("\n")[-100:]))

        if result.stderr:
            print(f"\nStderr (last 50 lines):")
            print("\n".join(result.stderr.split("\n")[-50:]))

        # Check for success indicators
        passed = result.returncode == 0 or "PASSED" in result.stdout or "reward" in result.stdout.lower()

        return {
            "passed": passed,
            "returncode": result.returncode,
            "output_lines": len(result.stdout.split("\n"))
        }

    except subprocess.TimeoutExpired:
        print("⏱️  Test timed out after 10 minutes")
        return {"passed": False, "returncode": -1, "error": "timeout"}
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"passed": False, "returncode": -1, "error": str(e)}


def main():
    """Main test function."""
    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ERROR: ANTHROPIC_API_KEY not set")
        print("Usage: export ANTHROPIC_API_KEY=sk-ant-... && python simple_harbor_test.py")
        sys.exit(1)

    print("\n" + "="*60)
    print("Harbor + Claude Code Test")
    print("="*60 + "\n")

    results = {
        "start_time": datetime.now().isoformat(),
        "validations": [],
        "tests": [],
        "pass_rate": 0.0
    }

    # Find Harbor tasks
    print("🔍 Finding Harbor tasks...")
    harbor_tasks = find_harbor_tasks()

    if not harbor_tasks:
        print("❌ No Harbor format tasks found")
        sys.exit(1)

    print(f"\nFound {len(harbor_tasks)} Harbor task(s)\n")

    # Validate each task
    print("\n" + "="*60)
    print("VALIDATION PHASE")
    print("="*60)

    for task_dir in harbor_tasks:
        valid = validate_harbor_task(task_dir)
        results["validations"].append({
            "task": task_dir.name,
            "valid": valid
        })

    # Test each task with Claude Code
    print("\n" + "="*60)
    print("TESTING PHASE")
    print("="*60)

    for task_dir in harbor_tasks:
        test_result = test_with_claude_code(task_dir, api_key)
        results["tests"].append({
            "task": task_dir.name,
            **test_result
        })

    # Calculate pass rate
    if results["tests"]:
        passed_count = sum(1 for t in results["tests"] if t["passed"])
        total_count = len(results["tests"])
        results["pass_rate"] = (passed_count / total_count) * 100
    else:
        passed_count = 0
        total_count = 0

    results["end_time"] = datetime.now().isoformat()

    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60 + "\n")

    print(f"Tasks Found: {len(harbor_tasks)}")
    print(f"Validations Passed: {sum(1 for v in results['validations'] if v['valid'])}/{len(results['validations'])}")
    print(f"Tests Passed: {passed_count}/{total_count}")
    print(f"\nPASS RATE: {results['pass_rate']:.1f}%")

    # Detailed results
    print(f"\nDetailed Results:")
    for test in results["tests"]:
        status = "✅ PASS" if test["passed"] else "❌ FAIL"
        print(f"  {status} {test['task']} (return code: {test['returncode']})")

    # Save results
    results_file = Path("harbor_test_results.json")
    results_file.write_text(json.dumps(results, indent=2))
    print(f"\nResults saved to: {results_file}")

    return 0 if passed_count == total_count else 1


if __name__ == "__main__":
    sys.exit(main())

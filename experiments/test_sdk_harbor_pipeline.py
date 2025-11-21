#!/usr/bin/env python3
"""
Test SDK v2 with Harbor format - Create tasks and test with Claude Code

This script:
1. Uses SDK idea agent to create 1 draft from seed task
2. Uses SDK Harbor builder agent to create Harbor format task
3. Tests the Harbor task with Claude Code
4. Reports pass rate

Usage:
    export ANTHROPIC_API_KEY=sk-ant-api03-...
    python test_sdk_harbor_pipeline.py
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Import SDK Harbor runner
from sdk_harbor_runner import HarborPipeline


async def run_idea_agent_once():
    """Run idea agent once to create a single draft task."""
    print("\n" + "="*80)
    print("STEP 1: Running SDK Idea Agent")
    print("="*80 + "\n")

    pipeline = HarborPipeline()
    result = await pipeline.run_idea_agent("test_idea_agent")

    return result


async def run_harbor_builder_once():
    """Run Harbor builder agent once to create a Harbor format task."""
    print("\n" + "="*80)
    print("STEP 2: Running SDK Harbor Builder Agent")
    print("="*80 + "\n")

    pipeline = HarborPipeline()
    result = await pipeline.run_builder_agent("test_harbor_builder")

    return result


def find_harbor_tasks():
    """Find all Harbor format tasks in shared workspace."""
    shared_workspace = Path("shared_workspace/data_points")
    harbor_tasks = []

    for task_dir in shared_workspace.iterdir():
        if not task_dir.is_dir():
            continue

        # Check if it has Harbor format (instruction.md, task.toml, etc.)
        has_instruction = (task_dir / "instruction.md").exists()
        has_task_toml = (task_dir / "task.toml").exists()
        has_environment = (task_dir / "environment").exists()
        has_solution = (task_dir / "solution").exists()
        has_tests = (task_dir / "tests").exists()

        if has_instruction and has_task_toml and has_environment and has_solution and has_tests:
            harbor_tasks.append(task_dir)

    return harbor_tasks


def validate_harbor_task(task_dir):
    """Validate a Harbor format task."""
    print(f"\n{'='*80}")
    print(f"Validating Harbor task: {task_dir.name}")
    print(f"{'='*80}\n")

    try:
        result = subprocess.run(
            ["harbor", "tasks", "validate", str(task_dir)],
            capture_output=True,
            text=True,
            timeout=30
        )

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        return result.returncode == 0
    except Exception as e:
        print(f"Error validating: {e}")
        return False


def test_with_harbor_claude_code(task_dir):
    """Test a Harbor task using Claude Code."""
    print(f"\n{'='*80}")
    print(f"Testing with Harbor + Claude Code: {task_dir.name}")
    print(f"{'='*80}\n")

    try:
        # Run harbor with Claude Code agent
        result = subprocess.run(
            [
                "harbor",
                "agents",
                "run",
                "claude-code",
                "--model", "anthropic/claude-sonnet-4-5",
                "--task", str(task_dir),
                "--env", f"ANTHROPIC_API_KEY={os.getenv('ANTHROPIC_API_KEY')}"
            ],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        # Check if test passed (reward score > 0)
        # Parse output for results
        passed = "PASSED" in result.stdout or result.returncode == 0

        return {
            "passed": passed,
            "output": result.stdout,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        print("⏱️  Test timed out after 5 minutes")
        return {"passed": False, "output": "Timeout", "returncode": -1}
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return {"passed": False, "output": str(e), "returncode": -1}


async def main():
    """Main test pipeline."""
    import os

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ERROR: ANTHROPIC_API_KEY not set")
        print("Set it with: export ANTHROPIC_API_KEY=sk-ant-api03-...")
        sys.exit(1)

    print("\n" + "🚀 "*40)
    print("SDK v2 + Harbor + Claude Code Test Pipeline")
    print("🚀 "*40 + "\n")

    results = {
        "start_time": datetime.now().isoformat(),
        "idea_agent": None,
        "builder_agent": None,
        "validations": [],
        "tests": [],
        "pass_rate": 0.0
    }

    # Step 1: Run idea agent
    print("\n📝 Creating draft task with SDK idea agent...")
    idea_result = await run_idea_agent_once()
    results["idea_agent"] = idea_result

    if idea_result["status"] != "success":
        print(f"❌ Idea agent failed: {idea_result}")
        return results

    # Step 2: Run Harbor builder agent
    print("\n🔨 Building Harbor format task with SDK builder agent...")
    builder_result = await run_harbor_builder_once()
    results["builder_agent"] = builder_result

    if builder_result["status"] != "success":
        print(f"❌ Builder agent failed: {builder_result}")
        return results

    # Step 3: Find all Harbor tasks
    print("\n🔍 Finding Harbor format tasks...")
    harbor_tasks = find_harbor_tasks()
    print(f"Found {len(harbor_tasks)} Harbor format tasks")

    # Step 4: Validate tasks
    print("\n✅ Validating Harbor tasks...")
    for task_dir in harbor_tasks:
        valid = validate_harbor_task(task_dir)
        results["validations"].append({
            "task": task_dir.name,
            "valid": valid
        })

    # Step 5: Test with Claude Code (limit to first task for speed)
    print("\n🧪 Testing with Harbor + Claude Code...")
    test_tasks = harbor_tasks[:1]  # Test just one for now

    for task_dir in test_tasks:
        test_result = test_with_harbor_claude_code(task_dir)
        results["tests"].append({
            "task": task_dir.name,
            "passed": test_result["passed"],
            "returncode": test_result["returncode"]
        })

    # Calculate pass rate
    if results["tests"]:
        passed_count = sum(1 for t in results["tests"] if t["passed"])
        results["pass_rate"] = (passed_count / len(results["tests"])) * 100

    results["end_time"] = datetime.now().isoformat()

    # Print summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80 + "\n")

    print(f"Idea Agent: {results['idea_agent']['status']}")
    print(f"Builder Agent: {results['builder_agent']['status']}")
    print(f"\nValidations: {len(results['validations'])} tasks")
    for v in results["validations"]:
        status = "✅" if v["valid"] else "❌"
        print(f"  {status} {v['task']}")

    print(f"\nTests Run: {len(results['tests'])} tasks")
    for t in results["tests"]:
        status = "✅ PASS" if t["passed"] else "❌ FAIL"
        print(f"  {status} {t['task']}")

    print(f"\n{'='*80}")
    print(f"PASS RATE: {results['pass_rate']:.1f}% ({sum(1 for t in results['tests'] if t['passed'])}/{len(results['tests'])})")
    print(f"{'='*80}\n")

    # Save results
    results_file = Path("test_results.json")
    results_file.write_text(json.dumps(results, indent=2))
    print(f"Results saved to: {results_file}")

    return results


if __name__ == "__main__":
    asyncio.run(main())

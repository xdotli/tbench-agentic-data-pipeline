#!/usr/bin/env python3
"""
Analyze Harbor test results and provide detailed failure analysis.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict


def analyze_job_results(job_dir):
    """Analyze results from a Harbor job."""
    job_path = Path(job_dir)
    result_file = job_path / "result.json"

    if not result_file.exists():
        print(f"❌ No result.json found in {job_dir}")
        return None

    with open(result_file) as f:
        results = json.load(f)

    return results


def analyze_trial_details(job_dir):
    """Get detailed information about each trial."""
    job_path = Path(job_dir)
    trials = []

    # Find all trial directories
    for trial_dir in job_path.iterdir():
        if not trial_dir.is_dir() or trial_dir.name in ["result.json"]:
            continue

        trial_info = {
            "task_name": trial_dir.name.rsplit("__", 1)[0],
            "trial_id": trial_dir.name,
            "path": str(trial_dir)
        }

        # Check for trajectory file
        trajectory_file = trial_dir / "agent" / "trajectory.json"
        if trajectory_file.exists():
            with open(trajectory_file) as f:
                trajectory = json.load(f)
                trial_info["trajectory_length"] = len(trajectory.get("messages", []))
                trial_info["has_trajectory"] = True
        else:
            trial_info["has_trajectory"] = False

        # Check for reward file (try both locations)
        reward_file = trial_dir / "verifier" / "reward.txt"
        if not reward_file.exists():
            reward_file = trial_dir / "logs" / "verifier" / "reward.txt"

        if reward_file.exists():
            reward_content = reward_file.read_text().strip()
            try:
                trial_info["reward"] = float(reward_content)
            except:
                trial_info["reward"] = 0.0
                trial_info["reward_error"] = reward_content
        else:
            trial_info["reward"] = None
            trial_info["reward_missing"] = True

        # Check for test output (try both locations)
        test_output = trial_dir / "verifier" / "test-stdout.txt"
        if not test_output.exists():
            test_output = trial_dir / "logs" / "verifier" / "stdout.txt"
        if test_output.exists():
            trial_info["test_output"] = test_output.read_text()[-1000:]  # Last 1000 chars

        trials.append(trial_info)

    return trials


def generate_report(job_dir):
    """Generate comprehensive report."""
    print("\n" + "="*80)
    print("HARBOR TEST RESULTS ANALYSIS")
    print("="*80 + "\n")

    results = analyze_job_results(job_dir)
    if not results:
        return

    # Overall statistics
    stats = results.get("stats", {})
    print(f"Job ID: {results.get('id')}")
    print(f"Started: {results.get('started_at')}")
    print(f"Finished: {results.get('finished_at')}")
    print(f"\nTotal Trials: {stats.get('n_trials', 0)}")
    print(f"Errors: {stats.get('n_errors', 0)}")

    # Get detailed trial info
    trials = analyze_trial_details(job_dir)

    # Analyze rewards
    rewards = defaultdict(list)
    passed = []
    failed = []
    errors = []

    for trial in trials:
        reward = trial.get("reward")
        if reward is None:
            errors.append(trial)
        elif reward > 0:
            passed.append(trial)
            rewards[reward].append(trial)
        else:
            failed.append(trial)
            rewards[reward].append(trial)

    # Calculate pass rate
    total = len(trials)
    n_passed = len(passed)
    n_failed = len(failed)
    n_errors = len(errors)
    pass_rate = (n_passed / total * 100) if total > 0 else 0

    print(f"\n{'='*80}")
    print(f"PASS RATE: {pass_rate:.1f}% ({n_passed}/{total})")
    print(f"{'='*80}")
    print(f"\n✅ Passed: {n_passed}")
    print(f"❌ Failed: {n_failed}")
    print(f"⚠️  Errors: {n_errors}")

    # Reward distribution
    print(f"\n{'='*80}")
    print("REWARD DISTRIBUTION")
    print(f"{'='*80}")
    for reward in sorted(rewards.keys(), reverse=True):
        count = len(rewards[reward])
        print(f"  Reward {reward}: {count} tasks")
        for trial in rewards[reward][:3]:  # Show first 3
            print(f"    - {trial['task_name']}")
        if len(rewards[reward]) > 3:
            print(f"    ... and {len(rewards[reward]) - 3} more")

    # Failure analysis
    if failed:
        print(f"\n{'='*80}")
        print(f"FAILURE ANALYSIS ({len(failed)} tasks)")
        print(f"{'='*80}\n")

        for i, trial in enumerate(failed[:10], 1):  # Show first 10 failures
            print(f"{i}. {trial['task_name']}")
            print(f"   Reward: {trial.get('reward', 'N/A')}")

            if trial.get("test_output"):
                # Extract failure reason from test output
                output = trial["test_output"]
                lines = output.split("\n")

                # Look for common failure patterns
                if "FAILED" in output:
                    failed_lines = [l for l in lines if "FAILED" in l or "AssertionError" in l]
                    if failed_lines:
                        print(f"   Reason: {failed_lines[0][:100]}")
                elif "Error" in output:
                    error_lines = [l for l in lines if "Error" in l]
                    if error_lines:
                        print(f"   Reason: {error_lines[0][:100]}")
                else:
                    # Show last few lines
                    print(f"   Last output: {lines[-1][:100] if lines else 'N/A'}")
            else:
                print(f"   Reason: No test output available")

            print()

        if len(failed) > 10:
            print(f"... and {len(failed) - 10} more failures")

    # Error analysis
    if errors:
        print(f"\n{'='*80}")
        print(f"ERROR ANALYSIS ({len(errors)} tasks)")
        print(f"{'='*80}\n")

        for i, trial in enumerate(errors[:5], 1):
            print(f"{i}. {trial['task_name']}")
            if trial.get("reward_missing"):
                print(f"   Error: Reward file not found (test harness issue)")
            elif trial.get("reward_error"):
                print(f"   Error: Invalid reward value: {trial.get('reward_error')}")
            print()

    # Success analysis
    if passed:
        print(f"\n{'='*80}")
        print(f"SUCCESS ANALYSIS ({len(passed)} tasks)")
        print(f"{'='*80}\n")

        for i, trial in enumerate(passed[:10], 1):
            print(f"{i}. {trial['task_name']}")
            print(f"   Reward: {trial.get('reward')}")
            print()

    # Save detailed results
    output_file = Path(job_dir) / "detailed_analysis.json"
    output_data = {
        "summary": {
            "total": total,
            "passed": n_passed,
            "failed": n_failed,
            "errors": n_errors,
            "pass_rate": pass_rate
        },
        "passed_tasks": [t["task_name"] for t in passed],
        "failed_tasks": [{"name": t["task_name"], "reward": t.get("reward")} for t in failed],
        "error_tasks": [{"name": t["task_name"], "reason": t.get("reward_error", "reward_missing")} for t in errors]
    }

    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"\n📊 Detailed analysis saved to: {output_file}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_harbor_results.py <job_directory>")
        sys.exit(1)

    job_dir = sys.argv[1]
    generate_report(job_dir)

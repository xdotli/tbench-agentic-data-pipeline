#!/usr/bin/env python3
"""
Process all 10 seed tasks through the complete SDK v2 pipeline.

This script:
1. Runs idea agent on all 10 seed tasks (creates ~5 drafts each = 50 drafts)
2. Runs Harbor builder agent on each draft (creates 50 Harbor tasks)
3. Reports progress and final statistics

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...
    python process_all_10_tasks.py
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Import SDK Harbor runner
from sdk_harbor_runner import HarborPipeline


class BatchProcessor:
    """Process multiple seed tasks through the SDK pipeline."""

    def __init__(self):
        self.workspace_dir = Path(__file__).parent
        self.results = {
            "start_time": datetime.now().isoformat(),
            "seed_tasks_processed": 0,
            "draft_tasks_created": 0,
            "harbor_tasks_created": 0,
            "idea_agent_runs": [],
            "builder_agent_runs": [],
            "errors": []
        }

    def get_pending_seed_tasks(self):
        """Get all pending seed tasks from task manager."""
        import subprocess
        result = subprocess.run(
            ["python", "data_pipeline.py", "list", "--type", "seed_dp", "--status", "pending"],
            capture_output=True,
            text=True,
            cwd=str(self.workspace_dir)
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data.get("tasks", [])
        return []

    def get_pending_draft_tasks(self):
        """Get all pending draft tasks from task manager."""
        import subprocess
        result = subprocess.run(
            ["python", "data_pipeline.py", "list", "--type", "draft_dp", "--status", "pending"],
            capture_output=True,
            text=True,
            cwd=str(self.workspace_dir)
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data.get("tasks", [])
        return []

    async def process_idea_agent_once(self, seed_task_id):
        """Run idea agent once to process a seed task."""
        print(f"\n{'='*80}")
        print(f"🎨 Processing Seed Task: {seed_task_id}")
        print(f"{'='*80}\n")

        pipeline = HarborPipeline()

        try:
            result = await pipeline.run_idea_agent(f"batch_idea_{seed_task_id}")

            self.results["idea_agent_runs"].append({
                "seed_task_id": seed_task_id,
                "status": result["status"],
                "messages": result.get("messages", 0),
                "timestamp": datetime.now().isoformat()
            })

            if result["status"] == "success":
                self.results["seed_tasks_processed"] += 1
                print(f"✅ Seed task {seed_task_id} processed successfully")
            else:
                print(f"❌ Seed task {seed_task_id} failed: {result}")
                self.results["errors"].append({
                    "type": "idea_agent",
                    "task_id": seed_task_id,
                    "error": result.get("error", "Unknown")
                })

            return result

        except Exception as e:
            print(f"❌ Exception processing {seed_task_id}: {e}")
            self.results["errors"].append({
                "type": "idea_agent",
                "task_id": seed_task_id,
                "error": str(e)
            })
            return {"status": "error", "error": str(e)}

    async def process_builder_agent_once(self, draft_task_id):
        """Run Harbor builder agent once to process a draft task."""
        print(f"\n{'='*80}")
        print(f"🔨 Building Harbor Task: {draft_task_id}")
        print(f"{'='*80}\n")

        pipeline = HarborPipeline()

        try:
            result = await pipeline.run_builder_agent(f"batch_builder_{draft_task_id}")

            self.results["builder_agent_runs"].append({
                "draft_task_id": draft_task_id,
                "status": result["status"],
                "messages": result.get("messages", 0),
                "timestamp": datetime.now().isoformat()
            })

            if result["status"] == "success":
                self.results["harbor_tasks_created"] += 1
                print(f"✅ Harbor task {draft_task_id} built successfully")
            else:
                print(f"❌ Draft task {draft_task_id} failed: {result}")
                self.results["errors"].append({
                    "type": "builder_agent",
                    "task_id": draft_task_id,
                    "error": result.get("error", "Unknown")
                })

            return result

        except Exception as e:
            print(f"❌ Exception building {draft_task_id}: {e}")
            self.results["errors"].append({
                "type": "builder_agent",
                "task_id": draft_task_id,
                "error": str(e)
            })
            return {"status": "error", "error": str(e)}

    async def run_idea_agents_batch(self, limit=10):
        """Run idea agents on multiple seed tasks."""
        print(f"\n{'🎨'*40}")
        print("PHASE 1: IDEA GENERATION")
        print(f"{'🎨'*40}\n")

        seed_tasks = self.get_pending_seed_tasks()
        print(f"Found {len(seed_tasks)} pending seed tasks")

        if limit:
            seed_tasks = seed_tasks[:limit]
            print(f"Processing first {limit} tasks")

        for i, task in enumerate(seed_tasks, 1):
            print(f"\n--- Seed Task {i}/{len(seed_tasks)} ---")
            await self.process_idea_agent_once(task["id"])

            # Brief pause between tasks
            await asyncio.sleep(2)

        print(f"\n✅ Phase 1 Complete: {self.results['seed_tasks_processed']}/{len(seed_tasks)} succeeded")

    async def run_builder_agents_batch(self, limit=None):
        """Run builder agents on multiple draft tasks."""
        print(f"\n{'🔨'*40}")
        print("PHASE 2: HARBOR TASK BUILDING")
        print(f"{'🔨'*40}\n")

        draft_tasks = self.get_pending_draft_tasks()
        print(f"Found {len(draft_tasks)} pending draft tasks")

        if limit:
            draft_tasks = draft_tasks[:limit]
            print(f"Processing first {limit} tasks")

        for i, task in enumerate(draft_tasks, 1):
            print(f"\n--- Draft Task {i}/{len(draft_tasks)} ---")
            await self.process_builder_agent_once(task["id"])

            # Brief pause between tasks
            await asyncio.sleep(2)

        print(f"\n✅ Phase 2 Complete: {self.results['harbor_tasks_created']}/{len(draft_tasks)} succeeded")

    def save_results(self):
        """Save processing results."""
        self.results["end_time"] = datetime.now().isoformat()

        results_file = self.workspace_dir / "batch_processing_results.json"
        results_file.write_text(json.dumps(self.results, indent=2))
        print(f"\n📊 Results saved to: {results_file}")

    def print_summary(self):
        """Print final summary."""
        print(f"\n{'='*80}")
        print("📊 BATCH PROCESSING SUMMARY")
        print(f"{'='*80}\n")

        print(f"Seed Tasks Processed: {self.results['seed_tasks_processed']}")
        print(f"Draft Tasks Created: {len(self.results['idea_agent_runs'])}")
        print(f"Harbor Tasks Built: {self.results['harbor_tasks_created']}")
        print(f"Total Errors: {len(self.results['errors'])}")

        if self.results['errors']:
            print(f"\n⚠️  Errors:")
            for err in self.results['errors'][:5]:  # Show first 5
                print(f"  - {err['type']}: {err['task_id']} - {err['error'][:100]}")

        print(f"\nTotal Idea Agent Runs: {len(self.results['idea_agent_runs'])}")
        idea_success = sum(1 for r in self.results['idea_agent_runs'] if r['status'] == 'success')
        print(f"  Success: {idea_success}/{len(self.results['idea_agent_runs'])}")

        print(f"\nTotal Builder Agent Runs: {len(self.results['builder_agent_runs'])}")
        builder_success = sum(1 for r in self.results['builder_agent_runs'] if r['status'] == 'success')
        print(f"  Success: {builder_success}/{len(self.results['builder_agent_runs'])}")


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Process all seed tasks through SDK v2 pipeline")
    parser.add_argument(
        "--seed-limit",
        type=int,
        default=10,
        help="Number of seed tasks to process (default: 10)"
    )
    parser.add_argument(
        "--draft-limit",
        type=int,
        default=None,
        help="Number of draft tasks to build (default: all pending)"
    )
    parser.add_argument(
        "--phase",
        choices=["idea", "builder", "both"],
        default="both",
        help="Which phase to run (default: both)"
    )

    args = parser.parse_args()

    # Check API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ERROR: ANTHROPIC_API_KEY not set")
        print("Set it with: export ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)

    processor = BatchProcessor()

    print("\n" + "🚀 "*40)
    print("SDK v2 Batch Processing Pipeline")
    print("🚀 "*40)

    try:
        if args.phase in ["idea", "both"]:
            await processor.run_idea_agents_batch(limit=args.seed_limit)

        if args.phase in ["builder", "both"]:
            await processor.run_builder_agents_batch(limit=args.draft_limit)

        processor.print_summary()
        processor.save_results()

        print("\n✅ Batch processing complete!")
        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Processing interrupted by user")
        processor.print_summary()
        processor.save_results()
        return 1
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        processor.save_results()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

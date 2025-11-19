#!/usr/bin/env python3
"""
Harbor Format Data Pipeline Runner

Runs the data generation pipeline with SDK agents, outputting Harbor eval format.

Key difference from training data pipeline:
- Build-then-break approach (working code first, then introduce bugs)
- Outputs Harbor format (instruction.md, task.toml, environment/, solution/, tests/)
- Trivial solution generation (restore working files)

Usage:
    python sdk_harbor_runner.py --agent idea        # Run idea agent only
    python sdk_harbor_runner.py --agent builder     # Run builder agent only (Harbor format)
    python sdk_harbor_runner.py --agent all         # Run full pipeline

Requirements:
    pip install claude-agent-sdk
    export ANTHROPIC_API_KEY="sk-ant-..."
"""

import asyncio
import sys
import os
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Import Claude SDK
try:
    from claude_agent_sdk import ClaudeAgentOptions, query
except ImportError:
    print("❌ ERROR: claude-agent-sdk not installed")
    print("Install with: pip install claude-agent-sdk")
    sys.exit(1)

class HarborPipeline:
    """
    Faithful SDK implementation of Harbor format data pipeline.

    Uses build-then-break approach for easier solution generation.
    """

    def __init__(self):
        self.workspace_dir = Path(__file__).parent.resolve()
        load_dotenv(self.workspace_dir / ".env")

    async def run_idea_agent(self, agent_id: str = "harbor_idea_agent"):
        """
        Run idea generation agent (same as training data pipeline).

        The idea agent workflow is identical for both formats.
        """
        print(f"\n{'='*80}")
        print(f"🎨 IDEA GENERATION AGENT ({agent_id})")
        print(f"{'='*80}\n")

        workflow_file = self.workspace_dir / "agents/idea_agent_workspace/workflow_instructions.md"
        workflow_instructions = workflow_file.read_text()

        prompt = f"""You are an Idea Generation Agent in the data generation pipeline.

{workflow_instructions}

**Your task**: Execute the complete workflow starting from Step 1.

**Working directory**: {self.workspace_dir}

Start working now. Follow the workflow exactly."""

        options = ClaudeAgentOptions(
            model="sonnet",
            cwd=str(self.workspace_dir),
            allowed_tools=["Bash", "Read", "Write", "Glob", "Grep", "Edit"],
        )

        print(f"🤖 Starting idea agent...")

        messages = []
        try:
            async for message in query(prompt=prompt, options=options):
                messages.append(message)

                if hasattr(message, 'content'):
                    for block in message.content:
                        if hasattr(block, 'text') and block.text:
                            lines = block.text.split('\n')
                            for line in lines[:2]:
                                if line.strip():
                                    print(f"   💡 {line[:80]}...")
                                    break

            print(f"\n✅ Idea agent completed ({len(messages)} messages)")
            return {"status": "success", "messages": len(messages)}

        except Exception as e:
            print(f"\n❌ Error: {e}")
            return {"status": "error", "error": str(e)}

    async def run_builder_agent(self, agent_id: str = "harbor_builder_agent"):
        """
        Run Harbor builder agent using build-then-break workflow.

        Key differences from training data builder:
        1. Build WORKING implementation first
        2. Store in solution/reference/
        3. Create broken version in environment/
        4. Generate trivial solution/solve.sh
        5. Output Harbor format structure
        """
        print(f"\n{'='*80}")
        print(f"🔨 HARBOR BUILDER AGENT ({agent_id})")
        print(f"📦 MODE: Build-Then-Break → Harbor Format")
        print(f"{'='*80}\n")

        workflow_file = self.workspace_dir / "agents/dp_builder_workspace/workflow_instructions_harbor.md"
        workflow_instructions = workflow_file.read_text()

        prompt = f"""You are a Datapoint Builder Agent creating Harbor evaluation tasks.

{workflow_instructions}

**Your task**: Execute the complete Harbor workflow starting from getting your next draft task.

**Working directory**: {self.workspace_dir}

**CRITICAL - Build-Then-Break Approach**:
1. Get next draft task: `python data_pipeline.py next --task-type draft_dp`
2. Read draft_spec.md from shared_workspace/data_points/{{task_id}}/
3. Build WORKING implementation first (all tests pass)
4. Store working code in solution/reference/
5. Create broken version by introducing strategic bug
6. Copy broken code to environment/
7. Generate trivial solution/solve.sh (just restore files)
8. Create instruction.md (1-3 sentence task description)
9. Create task.toml (metadata from draft_spec)
10. Create tests/test.sh (writes /logs/verifier/reward.txt)
11. Create environment/Dockerfile
12. Validate with `~/.local/bin/harbor tasks validate shared_workspace/data_points/{{task_id}}/`
13. Complete task: `python data_pipeline.py complete {{task_id}} --status completed`

**Harbor structure in shared_workspace/data_points/{{task_id}}/:**
```
├── instruction.md          # 1-3 sentence task
├── task.toml              # Metadata
├── environment/           # Broken code
│   ├── Dockerfile
│   └── [app files]
├── solution/
│   ├── solve.sh           # Restoration script
│   └── reference/         # Working implementation
│       └── [correct files]
└── tests/
    ├── test.sh            # Test runner
    └── test_outputs.py    # Python tests
```

**Example solution/solve.sh**:
```bash
#!/bin/bash
cp /solution/reference/checkout.py /workspace/app/checkout.py
pkill -f uvicorn && /workspace/start.sh &
```

Start working now. Follow the Harbor workflow exactly."""

        options = ClaudeAgentOptions(
            model="sonnet",
            cwd=str(self.workspace_dir),
            allowed_tools=["Bash", "Read", "Write", "Glob", "Grep", "Edit"],
        )

        print(f"🤖 Starting Harbor builder agent...")

        messages = []
        try:
            async for message in query(prompt=prompt, options=options):
                messages.append(message)

                if hasattr(message, 'content'):
                    for block in message.content:
                        if hasattr(block, 'text') and block.text:
                            lines = block.text.split('\n')
                            for line in lines[:2]:
                                if line.strip():
                                    print(f"   🔧 {line[:80]}...")
                                    break

            print(f"\n✅ Harbor builder agent completed ({len(messages)} messages)")
            return {"status": "success", "messages": len(messages)}

        except Exception as e:
            print(f"\n❌ Error: {e}")
            return {"status": "error", "error": str(e)}

async def main():
    parser = argparse.ArgumentParser(description="Run Harbor format data pipeline with SDK agents")
    parser.add_argument(
        "--agent",
        choices=["idea", "builder", "all"],
        required=True,
        help="Which agent to run"
    )
    parser.add_argument(
        "--agent-id",
        type=str,
        default=None,
        help="Custom agent ID (optional)"
    )

    args = parser.parse_args()

    # Check API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ERROR: ANTHROPIC_API_KEY not set")
        print("Set it in .env file or: export ANTHROPIC_API_KEY='sk-ant-...'")
        sys.exit(1)

    pipeline = HarborPipeline()

    print(f"\n{'🚀 '*40}")
    print(f"HARBOR FORMAT DATA PIPELINE - SDK Runner")
    print(f"{'🚀 '*40}\n")
    print(f"Mode: Build-Then-Break → Harbor Eval Format")
    print(f"Workspace: {pipeline.workspace_dir}")
    print(f"Agent: {args.agent}")
    print()

    results = {}

    if args.agent in ["idea", "all"]:
        agent_id = args.agent_id or "harbor_idea_agent"
        results["idea"] = await pipeline.run_idea_agent(agent_id)

    if args.agent in ["builder", "all"]:
        agent_id = args.agent_id or "harbor_builder_agent"
        results["builder"] = await pipeline.run_builder_agent(agent_id)

    # Print summary
    print(f"\n{'='*80}")
    print(f"📊 PIPELINE SUMMARY")
    print(f"{'='*80}\n")

    for agent_type, result in results.items():
        status_emoji = "✅" if result["status"] == "success" else "❌"
        print(f"{status_emoji} {agent_type.upper()}: {result['status']}")
        if "messages" in result:
            print(f"   Messages: {result['messages']}")
        if "error" in result:
            print(f"   Error: {result['error']}")

    print()

if __name__ == "__main__":
    asyncio.run(main())

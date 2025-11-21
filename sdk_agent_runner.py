#!/usr/bin/env python3
"""
Faithful SDK Implementation of the 3-Stage Data Generation Pipeline

This implementation properly follows the actual pipeline workflow:
- Uses task manager (data_pipeline.py) for task coordination
- Uses shared_workspace for all file operations
- Uses specialized tools (get_task_parameters.py, create_dp.py, etc.)
- Follows exact agent workflow instructions
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from claude_agent_sdk import query, ClaudeAgentOptions

# Load environment
load_dotenv()


class FaithfulSDKPipeline:
    """
    Faithful implementation following actual pipeline structure.
    """

    def __init__(self, workspace_dir: str = None):
        if workspace_dir is None:
            workspace_dir = str(Path(__file__).parent)
        self.workspace_dir = Path(workspace_dir)

    async def run_idea_agent(self, agent_id: str = "sdk_idea_agent"):
        """
        Run idea generation agent following workflow_instructions.md exactly.

        Workflow:
        1. Get next seed task from task manager
        2. Analyze seed DP (deep analysis)
        3. Get task parameters (n, multiplier)
        4. Brainstorm n×multiplier ideas
        5. Get refinement criteria
        6. Select best n ideas
        7. Create draft specifications in shared_workspace
        8. Complete seed task
        """
        print(f"\n{'='*80}")
        print(f"🎨 IDEA GENERATION AGENT ({agent_id})")
        print(f"{'='*80}\n")

        # Read the complete workflow instructions
        workflow_file = self.workspace_dir / "agents/idea_agent_workspace/workflow_instructions.md"
        workflow_instructions = workflow_file.read_text()

        # Build the agent prompt with full instructions
        prompt = f"""You are an Idea Generation Agent in the data generation pipeline.

{workflow_instructions}

**Your task**: Execute the complete workflow starting from Step 1.

**Working directory**: {self.workspace_dir}

**Important**:
- Use `python data_pipeline.py next --task-type seed_dp` to get your task
- Use `python get_task_parameters.py` to get n and multiplier
- Use `python get_idea_refinement_details.py` for refinement criteria
- Create draft specs in `shared_workspace/data_points/{{task_id}}/draft_spec.md`
- Use `python data_pipeline.py create-task --type draft_dp --parent {{parent_id}} --data "{{data}}"` for each draft
- Complete the seed task when done: `python data_pipeline.py complete {{task_id}} --status completed`

Start working now. Follow the workflow steps exactly."""

        options = ClaudeAgentOptions(
            model="sonnet",
            cwd=str(self.workspace_dir),
            allowed_tools=["Bash", "Read", "Write", "Glob", "Grep", "Edit"],
        )

        print(f"🤖 Starting idea agent with full workflow instructions...")

        messages = []
        try:
            async for message in query(prompt=prompt, options=options):
                messages.append(message)

                # Print progress
                if hasattr(message, 'content'):
                    for block in message.content:
                        if hasattr(block, 'text') and block.text:
                            lines = block.text.split('\n')
                            for line in lines[:2]:
                                if line.strip():
                                    print(f"   💭 {line[:80]}...")
                                    break

            print(f"\n✅ Idea agent completed ({len(messages)} messages)")
            return {"status": "success", "messages": len(messages)}

        except Exception as e:
            print(f"\n❌ Error: {e}")
            return {"status": "error", "error": str(e)}

    async def run_builder_agent(self, agent_id: str = "sdk_builder_agent"):
        """
        Run datapoint builder agent following workflow_instructions.md exactly.

        Workflow:
        1. Get next draft task from task manager
        2. Read draft specification from shared_workspace
        3. Build complete datapoint (prompt.md, dockerfile, tests.py, weights.json, files/)
        4. Validate using validate_datapoint.py
        5. Fix issues and re-validate
        6. Add to review queue using add_dp_to_review.py
        7. Complete draft task
        """
        print(f"\n{'='*80}")
        print(f"🔨 DATAPOINT BUILDER AGENT ({agent_id})")
        print(f"{'='*80}\n")

        workflow_file = self.workspace_dir / "agents/dp_builder_workspace/workflow_instructions.md"
        workflow_instructions = workflow_file.read_text()

        prompt = f"""You are a Datapoint Builder Agent in the data generation pipeline.

{workflow_instructions}

**Your task**: Execute the complete workflow starting from getting your next draft task.

**Working directory**: {self.workspace_dir}

**Important**:
- Use `python data_pipeline.py next --task-type draft_dp` to get your task
- Read draft spec from `shared_workspace/data_points/{{task_id}}/draft_spec.md`
- Create ALL files directly in `shared_workspace/data_points/{{task_id}}/`
- Use `python shared_tools/validate_datapoint.py --datapoint-dir shared_workspace/data_points/{{task_id}}` to validate
- Use `python agents/dp_builder_workspace/add_dp_to_review.py --datapoint-dir shared_workspace/data_points/{{task_id}}` when done
- Complete the draft task: `python data_pipeline.py complete {{task_id}} --status completed`

Start working now. Follow the workflow exactly."""

        options = ClaudeAgentOptions(
            model="sonnet",
            cwd=str(self.workspace_dir),
            allowed_tools=["Bash", "Read", "Write", "Glob", "Grep", "Edit"],
        )

        print(f"🤖 Starting builder agent with full workflow instructions...")

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

            print(f"\n✅ Builder agent completed ({len(messages)} messages)")
            return {"status": "success", "messages": len(messages)}

        except Exception as e:
            print(f"\n❌ Error: {e}")
            return {"status": "error", "error": str(e)}

    async def run_review_agent(self, agent_id: str = "sdk_review_agent"):
        """
        Run quality review agent following workflow_instructions.md exactly.

        Workflow:
        1. Get next review task from task manager
        2. Read datapoint using read_datapoint.py
        3. Review quality (thorough checks)
        4. Edit files in shared_workspace if needed
        5. Re-validate after edits
        6. Approve (approve_datapoint.py) or cancel (cancel_datapoint.py)
        7. Complete review task
        """
        print(f"\n{'='*80}")
        print(f"🔍 QUALITY REVIEW AGENT ({agent_id})")
        print(f"{'='*80}\n")

        workflow_file = self.workspace_dir / "agents/review_agent_workspace/workflow_instructions.md"
        workflow_instructions = workflow_file.read_text()

        prompt = f"""You are a Quality Review Agent in the data generation pipeline.

{workflow_instructions}

**Your task**: Execute the complete workflow starting from getting your next review task.

**Working directory**: {self.workspace_dir}

**Important**:
- Use `python data_pipeline.py next --task-type review_datapoint` to get your task
- Use `python agents/review_agent_workspace/read_datapoint.py --datapoint-id {{datapoint_id}}` to read it
- Edit files directly in `shared_workspace/data_points/{{datapoint_id}}/` if needed
- Use `python shared_tools/validate_datapoint.py --datapoint-dir shared_workspace/data_points/{{datapoint_id}}` after edits
- Use `python agents/review_agent_workspace/show_categories_tags.py` to see available categories
- Approve: `python agents/review_agent_workspace/approve_datapoint.py --datapoint-id {{datapoint_id}} --categories "..." --tags "..."`
- Or cancel: `python agents/review_agent_workspace/cancel_datapoint.py --datapoint-id {{datapoint_id}} --reason "..."`
- Complete the review task: `python data_pipeline.py complete {{task_id}} --status completed`

Start working now. Follow the workflow exactly."""

        options = ClaudeAgentOptions(
            model="sonnet",
            cwd=str(self.workspace_dir),
            allowed_tools=["Bash", "Read", "Write", "Glob", "Grep", "Edit"],
        )

        print(f"🤖 Starting review agent with full workflow instructions...")

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
                                    print(f"   📝 {line[:80]}...")
                                    break

            print(f"\n✅ Review agent completed ({len(messages)} messages)")
            return {"status": "success", "messages": len(messages)}

        except Exception as e:
            print(f"\n❌ Error: {e}")
            return {"status": "error", "error": str(e)}


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Faithful SDK Pipeline Implementation")
    parser.add_argument(
        "--agent",
        choices=["idea", "builder", "review", "all"],
        default="all",
        help="Which agent to run"
    )

    args = parser.parse_args()

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ERROR: ANTHROPIC_API_KEY not set")
        print("Set it in .env file or: export ANTHROPIC_API_KEY='sk-ant-...'")
        sys.exit(1)

    pipeline = FaithfulSDKPipeline()

    print(f"\n🚀 Starting Faithful SDK Pipeline")
    print(f"   Mode: {args.agent}")
    print(f"   Workspace: {pipeline.workspace_dir}\n")

    if args.agent == "idea" or args.agent == "all":
        result = await pipeline.run_idea_agent()
        print(f"\nIdea agent result: {result}")

    if args.agent == "builder" or args.agent == "all":
        result = await pipeline.run_builder_agent()
        print(f"\nBuilder agent result: {result}")

    if args.agent == "review" or args.agent == "all":
        result = await pipeline.run_review_agent()
        print(f"\nReview agent result: {result}")

    print(f"\n✅ Pipeline execution complete")


if __name__ == "__main__":
    asyncio.run(main())

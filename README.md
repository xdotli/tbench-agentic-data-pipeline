# Terminal Bench Agentic Data Pipeline

Generate high-quality evaluation tasks in Harbor format using automated multi-agent pipeline.

## What This Does

Generates **repository-level backend engineering tasks** for evaluating coding agents:
- Real-world scenarios from actual open source repos and issues
- Multi-file codebases (>1,000 LOC, >5 files)
- Non-trivial bugs requiring exploration and problem-solving
- Harbor format with build-then-break approach

## Quick Start

### 1. Create Seed Tasks

First, create seed task specifications with your desired language distribution:

```bash
# Default: 10 tasks (60% Python, 20% TypeScript, 10% JavaScript, 10% Go)
cd experiments && PYTHONPATH=.. python create_seed_tasks.py

# Custom: 50 tasks with different distribution
cd experiments && PYTHONPATH=.. python create_seed_tasks.py --count 50 \
    --python 50 --typescript 30 --javascript 10 --go 10

# Python-only
cd experiments && PYTHONPATH=.. python create_seed_tasks.py --count 20 --python 100

# Include Rust and Java
cd experiments && PYTHONPATH=.. python create_seed_tasks.py --count 30 \
    --python 40 --typescript 20 --go 15 --rust 15 --java 10
```

### 2. Generate Harbor Tasks

Set your API key and run the SDK builder agent:

```bash
export ANTHROPIC_API_KEY="your-key"

# Generate one Harbor format task
python sdk_harbor_runner.py --agent builder

# Generated tasks appear in: shared_workspace/data_points/
```

### Test Generated Task

```bash
harbor run shared_workspace/data_points/your_task/ \
  --agent claude-code \
  --environment docker
```

## Repository Structure

```
.
├── sdk_harbor_runner.py       # Main: Generate Harbor tasks
├── data_pipeline.py           # Task manager for parallel agents
├── agents/                    # Agent workflow instructions
│   ├── idea_agent_workspace/
│   ├── dp_builder_workspace/
│   └── review_agent_workspace/
├── shared_workspace/
│   ├── data_points/           # Generated tasks go here
│   └── validated_tasks/       # 3 reference tasks
├── shared_tools/              # Validation scripts
└── docs/
    ├── HARBOR_SDK_GUIDE.md    # Complete Harbor format guide
    └── ENVIRONMENT_CONFIGURATION.md
```

## Agent Workflow

1. **Idea Agent**: Generates task specifications from seed tasks
2. **Builder Agent**: Builds working code → introduces bugs → packages in Harbor format
3. **Review Agent**: Quality check before approval

Run agents manually:
```bash
# In Claude Code:
"See @agents/dp_builder_workspace/workflow_instructions.md - you are the builder agent, go!"
```

Or use SDK for automation:
```bash
python sdk_harbor_runner.py --agent all
```

## Quality Standards

Tasks must be:
- **Repo-level**: >1,000 LOC across >5 files (NOT single-file)
- **Real-world**: Based on actual open source repos/issues (NOT toy projects)
- **Non-trivial**: Require exploration and understanding (NOT one-line fixes)
- **Backend focus**: API development, databases, testing, debugging

## Task Categories

Focus areas:
- API development (REST, GraphQL, WebSocket)
- Database operations (migrations, query optimization)
- Testing infrastructure (unit, integration tests)
- Debugging/refactoring (race conditions, performance)

## Reference Tasks

Use these 3 as templates:

**auth_token_race_condition** (391 LOC, 5 files)
- JWT refresh race condition
- Non-atomic Redis operations

**fix_async_worker_queue** (150 LOC, 1 file - expand this)
- Async worker bugs
- Multi-bug scenario

**etl_checkpoint_resume_bug** (2,044 LOC, 14 files - perfect)
- ETL checkpoint logic
- Proper repo-level structure

## Documentation

- **[docs/HARBOR_SDK_GUIDE.md](docs/HARBOR_SDK_GUIDE.md)** - Complete Harbor format guide
- **[docs/ENVIRONMENT_CONFIGURATION.md](docs/ENVIRONMENT_CONFIGURATION.md)** - Environment setup
- **Agent instructions** - See `agents/*/workflow_instructions.md`

## Current Status

**Ready:**
- ✅ 3 validated reference tasks
- ✅ SDK automation working
- ✅ Agent instructions updated for real-world focus

**Todo:**
- ⚠️ Replace 7 duplicate tasks in data_points/ with unique implementations
- ⚠️ Generate 50+ tasks for production use

---

**Built with Claude Code** - This multi-agent pipeline was developed using Claude Code

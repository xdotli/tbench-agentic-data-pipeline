# Repository Structure

This document explains the organization of the Terminal Bench Agentic Data Pipeline repository.

## 📁 Directory Overview

```
.
├── 🎯 CORE PIPELINE (SDK Generation)
│   ├── data_pipeline.py              # Main pipeline orchestrator & task manager
│   ├── init_seed_tasks.py            # Initialize seed tasks from Terminal Bench
│   ├── sdk_agent_runner.py           # SDK agent runner for training data format
│   └── sdk_harbor_runner.py          # SDK agent runner for Harbor evaluation format
│
├── 📚 agents/                        # Agent workspace & instructions
│   ├── idea_agent_workspace/         # Idea generation agent tools & instructions
│   ├── dp_builder_workspace/         # Datapoint builder agent tools & instructions
│   └── review_agent_workspace/       # Quality review agent tools & instructions
│
├── 🔧 shared_tools/                  # Validation & utility tools (used by all agents)
│   ├── validate_datapoint.py         # Complete validation suite
│   ├── patch_dp.py                   # Update datapoint components
│   └── patch_additional_files.py     # Manage resource files
│
├── 📦 shared_workspace/              # Common workspace for all agents
│   ├── seed_tasks/                   # Terminal Bench seed tasks
│   ├── data_points/                  # Generated datapoints (draft & approved)
│   └── validated_tasks/              # Production-ready validated tasks
│
├── 🗂️ task_manager/                  # Task coordination & state management
│   └── task_manager.py               # Task manager implementation
│
├── 💾 state/                         # Pipeline state & tracking
│   └── generation_state.json         # Current task states & assignments
│
├── 📊 jobs/                          # Harbor test execution results
│   └── YYYY-MM-DD__HH-MM-SS/         # Timestamped job runs
│
├── 🔬 experiments/                   # Test scripts, demos & archived files
│   ├── archived/                     # Old/obsolete code versions
│   ├── abundant-demo/                # Example Harbor dataset demo
│   ├── sdk-demo-output/              # SDK demo run outputs
│   ├── test_*.py                     # Test scripts
│   ├── analyze_*.py                  # Analysis scripts
│   ├── *.yaml                        # Test configurations
│   └── monitor_*.sh                  # Monitoring scripts
│
├── 📖 docs/                          # Documentation
│   ├── HARBOR_SDK_GUIDE.md           # Complete Harbor format integration guide
│   ├── HANDOFF_CONTEXT.md            # Project handoff context
│   ├── FINAL_COMPLETE_TEST_REPORT.md # Final test report
│   ├── FINAL_SDK_V2_TEST_REPORT.md   # SDK v2 test report
│   └── SDK_V2_HARBOR_TEST_REPORT.md  # Harbor format test report
│
├── 🎨 readme_images/                 # Images used in README
├── 🔨 scripts/                       # Utility scripts
├── 📄 artifacts/                     # Build artifacts
│
└── 📋 Root Files
    ├── README.md                     # Main documentation
    ├── STRUCTURE.md                  # This file
    ├── .env                          # Environment variables (API keys)
    └── .gitignore                    # Git ignore rules
```

---

## 🎯 Core Pipeline Files

### Main Orchestration
- **`data_pipeline.py`** - Central pipeline orchestrator with task manager
  - Coordinates multiple agents working in parallel
  - Prevents duplicate work through atomic task claiming
  - Handles timeouts and failures
  - Usage: `python data_pipeline.py status`

### Initialization
- **`init_seed_tasks.py`** - Imports Terminal Bench tasks as seeds
  - Converts Terminal Bench eval tasks to seed format
  - Usage: `python init_seed_tasks.py <path_to_terminal_bench>`

### SDK Runners (Automated Pipeline)
- **`sdk_agent_runner.py`** - SDK runner for **training data format**
  - Generates datapoints for RL training
  - Format: `prompt.md`, `dockerfile`, `tests.py`, `weights.json`
  - Usage: `./sdk_agent_runner.py --agent builder`

- **`sdk_harbor_runner.py`** - SDK runner for **Harbor evaluation format**
  - Generates evaluation tasks using build-then-break approach
  - Format: `instruction.md`, `task.toml`, `environment/`, `solution/`, `tests/`
  - Usage: `./sdk_harbor_runner.py --agent builder`
  - See: `docs/HARBOR_SDK_GUIDE.md` for complete guide

---

## 🤖 Agent Workspaces

Each agent type has dedicated workspace with tools and instructions:

### Idea Generation Agent (`agents/idea_agent_workspace/`)
- **Role**: Analyze seed tasks → Generate creative variations
- **Key Files**:
  - `workflow_instructions.md` - Complete workflow guide
  - `get_task_parameters.py` - Retrieve assigned seed task
  - `get_idea_refinement_details.py` - Get refinement criteria (post-brainstorm)
- **Output**: Draft specifications in `shared_workspace/data_points/`

### Datapoint Builder Agent (`agents/dp_builder_workspace/`)
- **Role**: Build complete executable datapoints from draft specs
- **Key Files**:
  - `workflow_instructions.md` - Training data format workflow
  - `workflow_instructions_harbor.md` - Harbor format workflow (build-then-break)
  - `create_dp.py` - Create new datapoint structure
  - `add_dp_to_review.py` - Submit for quality review
- **Output**: Validated datapoints ready for review

### Quality Review Agent (`agents/review_agent_workspace/`)
- **Role**: Quality check → Edit if needed → Categorize & approve
- **Key Files**:
  - `workflow_instructions.md` - Review workflow guide
  - `approve_datapoint.py` - Approve and categorize datapoint
  - `cancel_datapoint.py` - Reject with reasons
  - `show_categories_tags.py` - Show available categories/tags
- **Output**: Production-ready approved datapoints

---

## 🔧 Shared Tools

Tools available to all agents (in `shared_tools/`):

- **`validate_datapoint.py`** - Complete validation suite
  - Docker build validation
  - Test discovery
  - Fail-first verification
  - Weight validation
  - Usage: `python shared_tools/validate_datapoint.py <datapoint_id>`

- **`patch_dp.py`** - Update datapoint components
  - Modify prompt, dockerfile, tests, weights
  - Usage: `python shared_tools/patch_dp.py <datapoint_id> --prompt "new prompt"`

- **`patch_additional_files.py`** - Manage resource files
  - Add/update files in datapoint
  - Usage: `python shared_tools/patch_additional_files.py <datapoint_id> --add file.py`

---

## 📦 Data & State

### Shared Workspace (`shared_workspace/`)
Common filesystem for agent communication:
- **`seed_tasks/`** - Terminal Bench seed tasks (imported via `init_seed_tasks.py`)
- **`data_points/`** - Generated datapoints (draft → in review → approved)
- **`validated_tasks/`** - Production-ready tasks with example runs

### Task Manager (`task_manager/`)
- **`task_manager.py`** - Coordination system
  - Atomic task claiming
  - Parent-child task tracking
  - Timeout recovery
  - Status monitoring

### State (`state/`)
- **`generation_state.json`** - Current pipeline state
  - Task assignments
  - Agent ownership
  - Completion status
  - Parent-child relationships

### Jobs (`jobs/`)
- Harbor test execution results
- Organized by timestamp
- Contains agent trajectories, test results, rewards

---

## 🔬 Experiments Directory

Testing, demos, and archived code:

### Test Scripts
- `test_sdk_harbor_pipeline.py` - Pipeline integration tests
- `test_api_key.py` - API key validation
- `simple_harbor_test.py` - Simple Harbor format test
- `analyze_harbor_results.py` - Result analysis

### Batch Processing
- `create_10_tasks.py` - Batch task creation
- `process_all_10_tasks.py` - Batch processing script

### Monitoring
- `monitor_progress.sh` - Progress monitoring
- `monitor_and_report.sh` - Monitoring with reporting
- `monitor_log.txt`, `last_check.txt`, `last_error_count.txt` - Monitoring state

### Configurations
- `harbor_config.yaml` - Basic Harbor config
- `harbor_config_all_tasks.yaml` - Full task config
- `sdk_test_task_ids.json` - Test task IDs

### Results
- `harbor_test_results.json` - Harbor test results
- `test_results.json` - General test results

### Demos
- **`abundant-demo/`** - Complete example Harbor dataset
  - Contains 3 validated tasks: toyhash-length-extension, bind9_dns, fix-async-worker-queue
  - Shows proper Harbor format structure
  - Includes successful test runs

- **`sdk-demo-output/`** - SDK pipeline run outputs
  - Historical SDK execution results
  - Debugging artifacts

### Archived
- **`archived/`** - Old code versions
  - `sdk_demo_simple.py.OLD` - Previous SDK demo version
  - `sdk_pipeline.py.OLD` - Previous pipeline version

---

## 📖 Documentation

### Main Guides
- **`README.md`** (root) - Main project documentation
  - Overview of multi-agent pipeline
  - Architecture & workflow
  - Getting started guide
  - Backend engineering focus

- **`STRUCTURE.md`** (this file) - Repository organization guide

### Technical Documentation (`docs/`)
- **`HARBOR_SDK_GUIDE.md`** - Complete Harbor format integration guide
  - Build-then-break approach explained
  - Usage instructions
  - Troubleshooting
  - Production deployment

- **`HANDOFF_CONTEXT.md`** - Project context & handoff notes
  - Development history
  - Key decisions
  - Integration points

### Test Reports (`docs/`)
- **`FINAL_COMPLETE_TEST_REPORT.md`** - Final comprehensive test report
- **`FINAL_SDK_V2_TEST_REPORT.md`** - SDK v2 test results
- **`SDK_V2_HARBOR_TEST_REPORT.md`** - Harbor format test results

---

## 🚀 Quick Start Guide

### 1. Initialize Pipeline
```bash
# Install dependencies
uv sync

# Set API key
export ANTHROPIC_API_KEY="sk-ant-..."

# Initialize seed tasks
python init_seed_tasks.py <path_to_terminal_bench>
```

### 2. Run Agents Manually (Claude Code)
```bash
# Idea Agent
"See @agents/idea_agent_workspace/workflow_instructions.md - you are the idea generation agent, go!"

# Builder Agent (training data format)
"See @agents/dp_builder_workspace/workflow_instructions.md - you are the datapoint builder agent, go!"

# Builder Agent (Harbor format)
"See @agents/dp_builder_workspace/workflow_instructions_harbor.md - you are the Harbor builder agent, go!"

# Review Agent
"See @agents/review_agent_workspace/workflow_instructions.md - you are the quality review agent, go!"
```

### 3. Run Automated SDK Pipeline
```bash
# Generate training data format
./sdk_agent_runner.py --agent builder

# Generate Harbor evaluation format
./sdk_harbor_runner.py --agent builder

# Run full pipeline (idea → builder)
./sdk_harbor_runner.py --agent all
```

### 4. Check Pipeline Status
```bash
# View task manager status
python data_pipeline.py status

# Get next available task
python data_pipeline.py next --task-type draft_dp
```

### 5. Test Generated Tasks (Harbor format)
```bash
# Run Harbor test
harbor run \
  -p shared_workspace/data_points/draft_dp_XXX/ \
  -m anthropic/claude-sonnet-4-5 \
  -a claude-code \
  --env docker
```

---

## 🔄 Pipeline Workflow

```
Terminal Bench Tasks
    ↓
[init_seed_tasks.py] → seed_tasks/
    ↓
[Idea Agent] → Draft Specs in data_points/
    ↓
[Builder Agent] → Complete Datapoints
    ↓
[Review Agent] → Approved Datapoints
    ↓
validated_tasks/ (Production Ready)
```

### Task Manager Flow
1. Agent calls `get_next_task()` → Task Manager assigns atomically
2. Agent processes independently
3. Agent calls `complete_task()` with results
4. Task Manager creates child tasks if needed
5. Repeat

---

## 📋 File Naming Conventions

### Datapoints
- **Draft**: `draft_dp_<id>/` - Initial builder output
- **In Review**: Same directory, marked in task manager
- **Approved**: Same directory + metadata, moved to `validated_tasks/`

### Task IDs
- **Seed**: Uses Terminal Bench task IDs
- **Draft**: Generated UUID + category
- **Review**: Same as draft ID

### Job Results
- **Timestamp**: `YYYY-MM-DD__HH-MM-SS/`
- **Task Runs**: `<task_id>__<random>/`

---

## 🛠️ Development Workflow

### Adding a New Agent Type
1. Create workspace in `agents/<agent_type>/`
2. Add workflow instructions
3. Add agent-specific tools
4. Update task manager for new task types
5. Create SDK runner if needed

### Adding Validation
1. Add check to `shared_tools/validate_datapoint.py`
2. Update builder workflow instructions
3. Test with existing datapoints

### Modifying Output Format
1. Update workflow instructions in relevant agent workspace
2. Update validation in `shared_tools/`
3. Test generation pipeline
4. Update documentation

---

## 📊 Monitoring & Debugging

### Check Pipeline Health
```bash
# Task manager status
python data_pipeline.py status

# View state file
cat state/generation_state.json | python -m json.tool

# Check for stuck tasks
python data_pipeline.py stuck
```

### Validate Datapoint
```bash
# Run full validation
python shared_tools/validate_datapoint.py draft_dp_XXX

# Check specific aspects
docker build -f shared_workspace/data_points/draft_dp_XXX/dockerfile .
pytest shared_workspace/data_points/draft_dp_XXX/tests.py
```

### Debug Harbor Tests
```bash
# Run with debug output
harbor run -p <path> -m <model> -a claude-code --env docker --debug

# Check logs
cat jobs/<timestamp>/<task>/agent/claude-code.txt
cat jobs/<timestamp>/<task>/verifier/reward.txt
cat jobs/<timestamp>/<task>/result.json
```

---

## 🎯 Key Design Decisions

### Why This Structure?
1. **Clear separation**: Core pipeline vs experiments vs docs
2. **Agent autonomy**: Each agent has dedicated workspace
3. **Shared tools**: Common validation ensures quality
4. **Flat state**: Simple file-based coordination
5. **Debugging**: Easy to inspect all intermediate states

### Directory Principles
- **Root**: Only core pipeline files (clean & focused)
- **agents/**: Agent-specific code (no sharing between agents)
- **shared_tools/**: Cross-agent utilities (used by multiple agents)
- **shared_workspace/**: Data exchange (filesystem-based messaging)
- **experiments/**: Anything not part of core pipeline
- **docs/**: All documentation in one place

---

## 📝 Contributing

When adding new files/features:
1. **Core pipeline?** → Root directory
2. **Agent-specific?** → `agents/<agent_type>/`
3. **Shared utility?** → `shared_tools/`
4. **Test/experiment?** → `experiments/`
5. **Documentation?** → `docs/` or update existing README
6. **Always update this STRUCTURE.md when changing organization**

---

**Last Updated**: 2025-11-19
**Maintained by**: Terminal Bench Pipeline Team

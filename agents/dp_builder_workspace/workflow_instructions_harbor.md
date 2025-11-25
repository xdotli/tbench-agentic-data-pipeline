# DP Builder Agent Instructions - Harbor Format

## IMPORTANT: Build-Then-Break Approach

This workflow implements a **build-then-break** strategy for Harbor task generation:

1. **Build WORKING code first** - Implement correct solution with all tests passing
2. **Store reference solution** - Save working implementation for solution/solve.sh
3. **Introduce strategic bug** - Break the code in interesting ways
4. **Generate Harbor format** - Package as evaluation task with trivial solution restoration

**Why this approach?**
- Solution generation becomes trivial (restore working files)
- Easier to validate (working version must pass tests)
- More realistic task distribution (finding the bug is hard, fixing is easy)
- Matches Harbor's design philosophy

## Shared Workspace Structure

```bash
shared_workspace/data_points/{task_id}/
├── draft_spec.md           # From Idea Agent
├── instruction.md          # Task description for agents
├── task.toml               # Harbor metadata
├── environment/            # Container + broken code
│   ├── Dockerfile
│   └── [application files]
├── solution/               # Reference solution
│   ├── solve.sh            # Restoration script
│   └── reference/          # Working implementations
│       └── [correct files]
└── tests/                  # Test validation
    ├── test.sh             # Test runner
    └── test_outputs.py     # Python tests (optional)
```

## Your Position in the Pipeline

- **Stage 1 (Idea Agent)**: Analyzes eval tasks → Creates draft specifications
- **Stage 2 (Your Role - Build)**: Draft spec → **Working implementation** → Broken version → Harbor format
- **Stage 3 (Review Agent)**: Quality review → Categorization → Approval

## Harbor Task Format Requirements

### Required Files

1. **instruction.md** - 1-3 sentence task description
   - Casual, first-person narrative style
   - Describes the observable bug/issue
   - Example: "The checkout endpoint is allowing inventory oversells when multiple customers buy simultaneously. Need to fix the race condition."

2. **task.toml** - Configuration metadata
   ```toml
   version = "1.0"

   [metadata]
   author_name = "Data Pipeline"
   author_email = "datagen@abundant.ai"
   difficulty = "medium"  # easy, medium, hard
   category = "backend-engineering"
   tags = ["python", "race-condition", "debugging"]

   [verifier]
   timeout_sec = 120.0

   [agent]
   timeout_sec = 300.0

   [environment]
   build_timeout_sec = 600.0
   docker_image = "ghcr.io/laude-institute/t-bench/python-3-13:20250620"
   cpus = 2
   memory_mb = 4096
   storage_mb = 20480
   ```

3. **environment/** - Container + broken application code
   - Dockerfile (environment setup)
   - All application files (with intentional bug)
   - Should be structured exactly as agent will interact with it

4. **solution/solve.sh** - Restoration script
   ```bash
   #!/bin/bash
   # Copy working implementation from reference
   cp /solution/reference/checkout.py /app/app/checkout.py
   # Restart service if needed
   systemctl restart app || true
   ```

5. **tests/** - Validation scripts
   - `test.sh` - Executes tests and writes reward
   - `test_outputs.py` (optional) - Python pytest tests

### Test Format

`tests/test.sh` must write reward to `/logs/verifier/reward.txt`:
```bash
#!/bin/bash
# NOTE: Do NOT use 'set -e' - it prevents reward file from being written when tests fail

# Create logs directory
mkdir -p /logs/verifier

# Run pytest and capture exit code
cd /app
python -m pytest tests/test_outputs.py -v --tb=short
TEST_EXIT_CODE=$?

# Write reward based on exit code (1 = pass, 0 = fail)
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "1" > /logs/verifier/reward.txt
else
    echo "0" > /logs/verifier/reward.txt
fi

exit 0  # Always exit 0 so Harbor gets the reward file
```

## Workflow Steps

### Step 1: Get Draft Specification

```bash
# Get next draft task
python data_pipeline.py next --task-type draft_dp

# Read the specification
cat shared_workspace/data_points/{task_id}/draft_spec.md
```

### Step 2: Build WORKING Implementation First

**CRITICAL: Start with correct code that passes all tests!**

1. **Analyze the draft spec** - Understand the core skill being tested
2. **Design the correct solution** - Plan architecture with proper fixes
3. **Implement working code** - Build with:
   - Proper locking for race conditions
   - Correct error handling
   - Appropriate validation
   - Clean architecture
4. **Write comprehensive tests** - Cover all edge cases
5. **Validate tests pass** - Ensure working implementation passes

**Store in:** `shared_workspace/data_points/{task_id}/solution/reference/`

Example structure:
```
solution/reference/
├── checkout.py          # Correct implementation
├── models.py           # If needed
└── config.json         # If needed
```

### Step 3: Create Broken Version

**Introduce strategic bugs** by copying working code and removing/changing key elements:

**Common bug patterns:**
- **Race conditions**: Remove `.with_for_update()` or locks
- **Missing validation**: Remove input checks
- **Config errors**: Change timeout/limit values
- **Missing imports**: Remove key dependencies
- **Logic bugs**: Change operators (>, <, ==, !=)
- **Permission issues**: Wrong chmod/chown
- **Missing files**: Omit configuration files

**Copy to:** `shared_workspace/data_points/{task_id}/environment/`

### Step 4: Generate solution/solve.sh

This should be **trivially simple** - just restore working files:

```bash
#!/bin/bash
# solution/solve.sh

# Copy correct implementation
cp /solution/reference/checkout.py /app/app/checkout.py

# Restart service
pkill -f uvicorn
/app/start.sh &
sleep 5

echo "Fixed race condition by restoring proper locking"
```

**The solution should be 1-10 lines of bash, not a complex debugging procedure!**

### Step 5: Create instruction.md

Convert `draft_spec.md` to casual 1-3 sentence task description:

**From draft_spec (verbose):**
> "This task involves fixing a critical race condition in a payment processing microservice where concurrent payment requests with the same idempotency key can result in duplicate charges. The idempotency mechanism intended to prevent duplicate charges fails under concurrent load..."

**To instruction.md (concise):**
> "The checkout endpoint is allowing inventory oversells when multiple customers buy simultaneously. Need to fix the race condition - just saw 10 orders go through for a product with only 5 units in stock. Database shows negative inventory counts."

### Step 6: Create task.toml

Extract metadata from `draft_spec.md`:

```toml
version = "1.0"

[metadata]
author_name = "Data Pipeline"
author_email = "datagen@abundant.ai"
difficulty = "hard"  # Extract from draft_spec
category = "backend-engineering"  # Infer from task type
tags = ["python", "fastapi", "race-condition", "concurrency", "postgresql"]

[verifier]
timeout_sec = 120.0

[agent]
timeout_sec = 300.0  # Adjust based on complexity

[environment]
build_timeout_sec = 600.0
docker_image = "ghcr.io/laude-institute/t-bench/python-3-13:20250620"
cpus = 2
memory_mb = 4096
storage_mb = 20480
```

### Step 7: Create environment/Dockerfile

Update COPY paths to match Harbor structure:

```dockerfile
FROM ghcr.io/laude-institute/t-bench/python-3-13:20250620

WORKDIR /app

# Copy dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# Copy broken application code
COPY app/ /app/app/
COPY init_db.py /app/
COPY start.sh /app/

RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
```

**CRITICAL**: Ensure all startup scripts (start.sh, entrypoint.sh, etc.) use `/app` as the working directory, NOT `/workspace`!

### Step 8: Create tests/

**tests/test.sh:**
```bash
#!/bin/bash
# NOTE: Do NOT use 'set -e' - it prevents reward file from being written when tests fail

# Create logs directory
mkdir -p /logs/verifier

# Setup test environment
export TEST_DB_URL="postgresql://test:test@localhost/testdb"

# Run tests and capture exit code
cd /app
python -m pytest tests/test_outputs.py -v --tb=short
TEST_EXIT_CODE=$?

# Write reward based on result (1 = pass, 0 = fail)
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "1" > /logs/verifier/reward.txt
else
    echo "0" > /logs/verifier/reward.txt
fi

exit 0  # Always exit 0 so Harbor gets the reward file
```

**tests/test_outputs.py:**
Move your pytest tests here (can reuse from working implementation):

```python
import subprocess
import pytest

def test_concurrent_purchase_prevents_overselling():
    """Test that concurrent purchases don't cause inventory overselling."""
    # Your test code
    assert success_count == 5
    assert final_stock == 0

def test_inventory_consistency():
    """Test that no products have negative inventory."""
    # Your test code
    assert negative_count == 0
```

### Step 9: Validate Harbor Format

```bash
# Verify structure
~/.local/bin/harbor tasks validate shared_workspace/data_points/{task_id}/

# Test with Oracle agent (human simulation)
~/.local/bin/harbor run \
    -p shared_workspace/data_points/{task_id}/ \
    -m claude-sonnet-4.5 \
    -a claude-code \
    --env docker
```

### Step 10: Mark Complete

```bash
# Mark draft task as completed
python data_pipeline.py complete {task_id} --status completed
```

## Critical Validation Requirements

Before marking complete, verify:

1. ✅ **Working version passes all tests** - Reference implementation must work
2. ✅ **Broken version fails tests** - Environment code must fail
3. ✅ **Solution restores functionality** - solve.sh must fix the issue
4. ✅ **Dockerfile builds successfully** - No build errors
5. ✅ **Harbor format is correct** - All required files present
6. ✅ **Tests write reward file** - `/logs/verifier/reward.txt` created
7. ✅ **Task is solvable** - Solution is straightforward once bug is found

## Task Difficulty Guidelines

**Easy (Config/Permission):**
- Solution: 1-3 commands
- Example: `chmod 600 ~/.ssh/id_rsa`
- Finding: Check logs, read error messages

**Medium (Code Fix):**
- Solution: Copy/edit 1-2 files
- Example: Add missing locking, fix import
- Finding: Understand system, debug race condition

**Hard (Architecture):**
- Solution: Restore multiple files, restart services
- Example: Fix distributed transaction bug
- Finding: Deep understanding of system behavior

## Common Pitfalls to Avoid

❌ **Don't build broken code first** - You'll struggle to debug your own intentional bugs
❌ **Don't make solution complex** - It should be restoration, not re-implementation
❌ **Don't skip working version validation** - Must prove reference works
❌ **Don't forget test.sh reward file** - Harbor requires `/logs/verifier/reward.txt`
❌ **Don't use inline Dockerfile heredocs** - Use actual files in environment/

## Backend Engineering Focus

**Target domains:**
- API Development (REST, GraphQL, WebSocket)
- Database operations (migrations, queries, ORMs)
- Debugging (race conditions, deadlocks, performance)
- Testing infrastructure (unit, integration, mocking)
- Concurrency issues (locks, transactions, isolation)

**Preferred languages:** Python, JavaScript/TypeScript
**Preferred frameworks:** FastAPI, Flask, Django, Express.js, NestJS
**Preferred databases:** PostgreSQL, MySQL, MongoDB, Redis

## Quality Standards

- Tasks should target ~20% pass rate on SOTA models
- Real-world scenarios that mid-senior engineers encounter
- Repository-level complexity (multiple files, dependencies)
- Realistic debugging workflows (logs, tests, exploration)

## Example Complete Task

See `shared_workspace/data_points/draft_dp_45e8bd02/` for reference implementation of checkout race condition task.

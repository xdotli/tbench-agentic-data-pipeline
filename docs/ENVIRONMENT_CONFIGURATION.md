# Harbor Environment Configuration Guide

## Overview

Harbor supports multiple environment types for running agent tasks:
- **docker** (default) - Local Docker containers
- **daytona** - Cloud-based remote environments
- **e2b** - E2B sandboxes
- **modal** - Modal compute
- **runloop** - Runloop environments

## Environment Types Comparison

| Environment Type | Requires API Key | Runs Locally | Use Case |
|-----------------|------------------|--------------|----------|
| `docker` | No | Yes | Default, local testing, development |
| `daytona` | Yes (DAYTONA_API_KEY) | No | Cloud execution, remote agents |
| `e2b` | Yes | No | Sandboxed execution |
| `modal` | Yes | No | Serverless compute |
| `runloop` | Yes | No | Runloop platform |

## The Issue: Daytona API Key Error

### Error Message
```
DaytonaError: API key or JWT token is required
```

### Root Cause
This error occurs when:
1. A job configuration specifies `environment.type = "daytona"`
2. The `DAYTONA_API_KEY` environment variable is not set

### Where It Happens
The error occurs in Harbor's environment setup, specifically in:
```python
# From harbor/environments/daytona.py
class DaytonaEnvironment:
    async def start(self):
        self._daytona = AsyncDaytona()  # This reads DAYTONA_API_KEY
```

The `AsyncDaytona` client requires one of:
- `DAYTONA_API_KEY` environment variable
- `DAYTONA_JWT` environment variable
- Explicit config passed to constructor

## Solution

### Option 1: Use Docker Environment (Recommended for Local Testing)

Change the job configuration from `"type": "daytona"` to `"type": "docker"`:

```json
{
  "environment": {
    "type": "docker",  // Changed from "daytona"
    "force_build": false,
    "delete": true
  }
}
```

Or when running harbor CLI:
```bash
harbor jobs start --env docker -p path/to/task
```

### Option 2: Configure Daytona API Key (For Cloud Execution)

If you need to use Daytona environments:

1. **Get a Daytona API key** from your Daytona account

2. **Create a .env file**:
   ```bash
   cp .env.example .env
   ```

3. **Add your API key to .env**:
   ```bash
   # .env
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   DAYTONA_API_KEY=your-daytona-api-key-here
   ```

4. **Load environment variables** before running harbor:
   ```bash
   # Load .env file
   export $(cat .env | xargs)

   # Or use dotenv
   python -c "from dotenv import load_dotenv; load_dotenv()"

   # Then run harbor
   harbor jobs start --env daytona -p path/to/task
   ```

### Option 3: Set Environment Variable Directly

```bash
export DAYTONA_API_KEY="your-api-key-here"
export DAYTONA_API_URL="https://api.daytona.io"  # Optional
export DAYTONA_TARGET="us"  # Optional

# Then run harbor
harbor jobs start --env daytona -p path/to/task
```

## Affected Tasks

### test_auth_token_task (Failed)
- **Configuration**: `environment.type = "daytona"`
- **Status**: FAILED - Missing DAYTONA_API_KEY
- **Location**: `/Users/suzilewie/benchflow/datagen/.conductor/douala/jobs/test_auth_token_task/config.json`

### test_auth_token_docker (Passed)
- **Configuration**: `environment.type = "docker"`
- **Status**: PASSED - No API key needed
- **Location**: `/Users/suzilewie/benchflow/datagen/.conductor/douala/jobs/test_auth_token_docker/config.json`

### Difference Between Jobs
The ONLY difference between these two jobs was the environment type:
- `test_auth_token_docker` used `docker` → Success
- `test_auth_token_task` used `daytona` → Failed (no API key)

## Fixing Existing Job Configurations

### Check Current Configuration
```bash
# View job config
cat jobs/test_auth_token_task/config.json | grep -A 5 "environment"
```

### Update to Docker Environment
```bash
# Create a new config file with docker environment
cat > jobs/test_auth_token_task/config.json << 'EOF'
{
    "environment": {
        "type": "docker",
        "force_build": false,
        "delete": true
    }
}
EOF
```

### Re-run Failed Job
```bash
# Re-run with docker environment
harbor jobs start \
  --env docker \
  -p shared_workspace/data_points/auth_token_race_condition \
  -a claude-code \
  -m anthropic/claude-sonnet-4-5 \
  --job-name test_auth_token_docker_fixed
```

## Best Practices

### 1. Default to Docker for Development
Use `docker` environment type for:
- Local testing
- Development
- CI/CD pipelines
- When you don't need cloud execution

### 2. Use Daytona for Production/Scale
Use `daytona` environment type when:
- You need cloud execution
- Running at scale
- Need remote agent environments
- Have Daytona API access

### 3. Configuration Files
Always specify environment type explicitly in config files:

```yaml
# harbor_config.yaml
environment:
  type: docker  # or daytona
  force_build: false
  delete: true
```

### 4. Environment Variables
Keep API keys in `.env` file (never commit to git):
```bash
# .env (gitignored)
ANTHROPIC_API_KEY=sk-ant-...
DAYTONA_API_KEY=...  # Only if using daytona
```

## Troubleshooting

### Error: "DaytonaError: API key or JWT token is required"
- **Cause**: Using `daytona` environment without API key
- **Fix**: Either switch to `docker` or set `DAYTONA_API_KEY`

### Error: "docker: command not found"
- **Cause**: Using `docker` environment but Docker not installed
- **Fix**: Install Docker Desktop or switch to `daytona`

### Job Hangs/Times Out
- **Docker**: Check if container is running: `docker ps`
- **Daytona**: Check API status and key validity

### Tests Pass Locally but Fail in Harbor
- Check environment type matches your setup
- Verify all dependencies are in Dockerfile
- Check file paths (Harbor uses different mount points)

## Additional Resources

- **Harbor Documentation**: https://github.com/harbor-ai/harbor
- **Daytona Setup**: https://daytona.io/docs
- **Docker Installation**: https://docs.docker.com/get-docker/

## Summary

The `auth_token_race_condition` task failure was caused by:

1. **What went wrong**: Job configuration specified `environment.type = "daytona"` but `DAYTONA_API_KEY` was not set
2. **Impact**: Task failed immediately during environment setup (before agent even ran)
3. **Why docker worked**: Docker environment doesn't require any API keys
4. **Fix**: Either:
   - Change environment type to `"docker"` (recommended for local testing)
   - Or set `DAYTONA_API_KEY` environment variable (for cloud execution)

This affects ALL tasks that use `daytona` environment type without the API key configured.

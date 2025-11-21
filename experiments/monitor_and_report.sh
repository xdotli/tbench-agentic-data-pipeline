#!/bin/bash

# Harbor Test Monitor - Checks every 5 minutes and reports status

WORKSPACE="/Users/suzilewie/benchflow/datagen/.conductor/accra"
JOBS_DIR="$WORKSPACE/jobs/sdk_v2_all_fixes_complete"
LOG_FILE="$WORKSPACE/monitor_log.txt"

cd "$WORKSPACE" || exit 1

echo "=== Harbor Test Monitor ===" | tee -a "$LOG_FILE"
echo "Time: $(date)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Count completed trials
COMPLETED=$(ls "$JOBS_DIR" 2>/dev/null | grep -c 'draft_dp')
echo "Progress: $COMPLETED/35 tasks started" | tee -a "$LOG_FILE"

# Count exceptions
ERRORS=$(find "$JOBS_DIR" -name "exception.txt" 2>/dev/null | wc -l | tr -d ' ')
echo "Errors: $ERRORS" | tee -a "$LOG_FILE"

# Check if Harbor is still running
if ps aux | grep -v grep | grep -q "harbor run"; then
    echo "Status: Harbor is running" | tee -a "$LOG_FILE"
else
    echo "Status: Harbor has stopped" | tee -a "$LOG_FILE"
fi

echo "" | tee -a "$LOG_FILE"

# If we have new errors since last check, show them
if [ -f "$WORKSPACE/last_error_count.txt" ]; then
    LAST_ERRORS=$(cat "$WORKSPACE/last_error_count.txt")
    if [ "$ERRORS" -gt "$LAST_ERRORS" ]; then
        echo "NEW ERRORS DETECTED!" | tee -a "$LOG_FILE"
        find "$JOBS_DIR" -name "exception.txt" -newer "$WORKSPACE/last_check.txt" 2>/dev/null | while read err_file; do
            task=$(basename $(dirname "$err_file") | cut -d'_' -f1-3)
            echo "  Error in: $task" | tee -a "$LOG_FILE"
        done
        echo "" | tee -a "$LOG_FILE"
    fi
fi

# Update tracking files
echo "$ERRORS" > "$WORKSPACE/last_error_count.txt"
touch "$WORKSPACE/last_check.txt"

# If completed, run analysis
if [ "$COMPLETED" -eq 35 ] && [ -f "$JOBS_DIR/result.json" ]; then
    echo "ALL TESTS COMPLETE! Running analysis..." | tee -a "$LOG_FILE"
    python "$WORKSPACE/analyze_harbor_results.py" "$JOBS_DIR" | tee -a "$LOG_FILE"
    exit 0
fi

echo "Next check in 5 minutes..." | tee -a "$LOG_FILE"
echo "----------------------------------------" | tee -a "$LOG_FILE"

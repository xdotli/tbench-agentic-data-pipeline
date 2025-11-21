#!/bin/bash
# Monitor the batch processing progress

echo "======================================"
echo "SDK v2 Batch Processing Monitor"
echo "======================================"
echo ""

while true; do
    clear
    echo "======================================"
    echo "SDK v2 Batch Processing Monitor"
    echo "Time: $(date)"
    echo "======================================"
    echo ""

    # Show task manager status
    echo "📊 Task Manager Status:"
    python data_pipeline.py status | jq -r '
        "  Total Tasks: \(.total_tasks)",
        "  Pending: \(.status_counts.pending)",
        "  In Progress: \(.status_counts.in_progress)",
        "  Completed: \(.status_counts.completed)",
        "  Failed: \(.status_counts.failed)",
        "",
        "  Seed Tasks: \(.seed_dp_completion_rate)",
        "  Draft Tasks: \(.draft_dp_completion_rate)"
    '

    echo ""
    echo "📁 Harbor Format Tasks:"
    find shared_workspace/data_points -name "instruction.md" 2>/dev/null | wc -l | awk '{print "  Total: " $1}'

    echo ""
    echo "🔄 Refreshing in 30 seconds... (Ctrl+C to stop)"
    sleep 30
done

#!/usr/bin/env python3
"""
Create 10 seed_dp tasks for testing SDK v2 with Harbor format.
"""

import json
import sys
from pathlib import Path
from task_manager.task_manager import TaskManager

def main():
    # Initialize task manager
    state_file = Path(__file__).parent / "state" / "generation_state.json"
    tm = TaskManager(state_file)

    # Define 10 diverse backend engineering tasks
    tasks_data = [
        {
            "task_name": "rate_limiting_api",
            "description": "Implement rate limiting for API endpoints",
            "complexity": "medium",
            "category": "api_security",
            "language": "python"
        },
        {
            "task_name": "jwt_authentication",
            "description": "Add JWT-based authentication to FastAPI service",
            "complexity": "medium",
            "category": "authentication",
            "language": "python"
        },
        {
            "task_name": "database_connection_pooling",
            "description": "Implement efficient database connection pooling",
            "complexity": "medium",
            "category": "database",
            "language": "python"
        },
        {
            "task_name": "async_task_queue",
            "description": "Build async task queue with Celery/Redis",
            "complexity": "hard",
            "category": "distributed_systems",
            "language": "python"
        },
        {
            "task_name": "caching_layer",
            "description": "Add Redis caching layer to reduce database load",
            "complexity": "medium",
            "category": "performance",
            "language": "python"
        },
        {
            "task_name": "webhook_handler",
            "description": "Implement webhook handler with retry logic",
            "complexity": "medium",
            "category": "integrations",
            "language": "python"
        },
        {
            "task_name": "data_validation_middleware",
            "description": "Create middleware for request data validation",
            "complexity": "easy",
            "category": "api_design",
            "language": "python"
        },
        {
            "task_name": "batch_processing",
            "description": "Implement batch processing for large datasets",
            "complexity": "hard",
            "category": "data_processing",
            "language": "python"
        },
        {
            "task_name": "api_versioning",
            "description": "Add API versioning support to existing endpoints",
            "complexity": "medium",
            "category": "api_design",
            "language": "python"
        },
        {
            "task_name": "pagination_system",
            "description": "Implement cursor-based pagination for API",
            "complexity": "medium",
            "category": "api_design",
            "language": "python"
        }
    ]

    print(f"Creating 10 seed_dp tasks for SDK v2 testing...")

    created_count = 0
    task_ids = []

    for task_data in tasks_data:
        try:
            # Create seed_dp task
            task_id = tm.create_task(
                task_type="seed_dp",
                data=task_data
            )

            task_ids.append(task_id)
            print(f"✓ Created task {task_id}: {task_data['task_name']}")
            created_count += 1

        except Exception as e:
            print(f"✗ Error creating {task_data['task_name']}: {e}")

    print(f"\n{'='*60}")
    print(f"Successfully created {created_count}/10 seed_dp tasks")
    print(f"{'='*60}")

    # Show updated status
    summary = tm.get_status_summary()
    print(f"\nUpdated task summary:")
    print(f"  Total tasks: {summary['total_tasks']}")
    print(f"  By type: {json.dumps(summary['type_counts'], indent=4)}")
    print(f"  By status: {json.dumps(summary['status_counts'], indent=4)}")

    # Save task IDs for easy reference
    output_file = Path(__file__).parent / "sdk_test_task_ids.json"
    output_file.write_text(json.dumps({
        "created_at": summary['metadata']['last_updated'],
        "task_ids": task_ids,
        "task_count": len(task_ids)
    }, indent=2))

    print(f"\nTask IDs saved to: {output_file}")

    return 0

if __name__ == "__main__":
    sys.exit(main())

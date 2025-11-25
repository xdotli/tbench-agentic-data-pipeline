#!/usr/bin/env python3
"""
Create 10 seed_dp tasks for testing SDK v2 with Harbor format.
"""

import json
import sys
from pathlib import Path
from task_manager.task_manager import TaskManager

def main():
    # Initialize task manager - use same state file as data_pipeline.py
    state_file = Path(__file__).parent.parent / "state" / "generation_state.json"
    tm = TaskManager(state_file)

    # Define 10 diverse backend engineering tasks
    # Language distribution: 60% Python (6), 30% JavaScript/TypeScript (3), 10% Go (1)
    # Category diversity: query optimization, migrations, testing, memory leaks, validation, refactoring
    tasks_data = [
        # Python tasks (6)
        {
            "task_name": "n_plus_one_query_optimization",
            "description": "Fix N+1 query problem causing slow API responses in Django ORM queries",
            "complexity": "medium",
            "category": "performance",
            "language": "python"
        },
        {
            "task_name": "database_migration_rollback",
            "description": "Fix broken database migration rollback that corrupts data",
            "complexity": "hard",
            "category": "database_migrations",
            "language": "python"
        },
        {
            "task_name": "memory_leak_connection_pool",
            "description": "Debug and fix memory leak in database connection pool cleanup",
            "complexity": "medium",
            "category": "memory_management",
            "language": "python"
        },
        {
            "task_name": "flaky_integration_tests",
            "description": "Fix flaky integration tests with race conditions in test fixtures",
            "complexity": "medium",
            "category": "testing",
            "language": "python"
        },
        {
            "task_name": "circular_import_refactor",
            "description": "Refactor circular dependencies causing import errors in microservice",
            "complexity": "hard",
            "category": "refactoring",
            "language": "python"
        },
        {
            "task_name": "api_validation_bypass",
            "description": "Fix API endpoint accepting invalid input due to missing validation",
            "complexity": "easy",
            "category": "api_security",
            "language": "python"
        },

        # JavaScript/TypeScript tasks (3)
        {
            "task_name": "express_middleware_memory_leak",
            "description": "Fix memory leak in Express.js middleware not releasing event listeners",
            "complexity": "medium",
            "category": "memory_management",
            "language": "typescript"
        },
        {
            "task_name": "prisma_migration_conflict",
            "description": "Resolve Prisma migration conflicts breaking database schema updates",
            "complexity": "medium",
            "category": "database_migrations",
            "language": "typescript"
        },
        {
            "task_name": "jest_mock_cleanup",
            "description": "Fix Jest tests with mock state leaking between test suites",
            "complexity": "easy",
            "category": "testing",
            "language": "javascript"
        },

        # Go task (1)
        {
            "task_name": "goroutine_leak_detection",
            "description": "Debug and fix goroutine leak in HTTP client connection handling",
            "complexity": "hard",
            "category": "memory_management",
            "language": "go"
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

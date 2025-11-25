#!/usr/bin/env python3
"""
Create seed_dp tasks with configurable language/category distribution.

Usage:
    python create_seed_tasks.py --count 10
    python create_seed_tasks.py --count 50 --python 50 --typescript 30 --javascript 10 --go 10
"""

import argparse
import json
import random
import sys
from pathlib import Path
from task_manager.task_manager import TaskManager


# Task pool organized by language and category
TASK_POOL = {
    "python": [
        {
            "task_name": "n_plus_one_query_optimization",
            "description": "Fix N+1 query problem causing slow API responses in Django ORM queries",
            "complexity": "medium",
            "category": "performance"
        },
        {
            "task_name": "database_migration_rollback",
            "description": "Fix broken database migration rollback that corrupts data",
            "complexity": "hard",
            "category": "database_migrations"
        },
        {
            "task_name": "memory_leak_connection_pool",
            "description": "Debug and fix memory leak in database connection pool cleanup",
            "complexity": "medium",
            "category": "memory_management"
        },
        {
            "task_name": "flaky_integration_tests",
            "description": "Fix flaky integration tests with race conditions in test fixtures",
            "complexity": "medium",
            "category": "testing"
        },
        {
            "task_name": "circular_import_refactor",
            "description": "Refactor circular dependencies causing import errors in microservice",
            "complexity": "hard",
            "category": "refactoring"
        },
        {
            "task_name": "api_validation_bypass",
            "description": "Fix API endpoint accepting invalid input due to missing validation",
            "complexity": "easy",
            "category": "api_security"
        },
        {
            "task_name": "sqlalchemy_query_optimization",
            "description": "Optimize slow SQLAlchemy queries with missing indexes and inefficient joins",
            "complexity": "medium",
            "category": "performance"
        },
        {
            "task_name": "celery_task_retry_logic",
            "description": "Fix Celery task retry logic causing duplicate processing",
            "complexity": "medium",
            "category": "distributed_systems"
        },
        {
            "task_name": "flask_session_leak",
            "description": "Debug Flask application session memory leak",
            "complexity": "hard",
            "category": "memory_management"
        },
        {
            "task_name": "pytest_fixture_isolation",
            "description": "Fix pytest fixtures with state leaking between tests",
            "complexity": "easy",
            "category": "testing"
        }
    ],
    "typescript": [
        {
            "task_name": "express_middleware_memory_leak",
            "description": "Fix memory leak in Express.js middleware not releasing event listeners",
            "complexity": "medium",
            "category": "memory_management"
        },
        {
            "task_name": "prisma_migration_conflict",
            "description": "Resolve Prisma migration conflicts breaking database schema updates",
            "complexity": "medium",
            "category": "database_migrations"
        },
        {
            "task_name": "nestjs_circular_dependency",
            "description": "Refactor NestJS circular dependency between services",
            "complexity": "hard",
            "category": "refactoring"
        },
        {
            "task_name": "typeorm_query_optimization",
            "description": "Fix TypeORM N+1 query problem in GraphQL resolver",
            "complexity": "medium",
            "category": "performance"
        },
        {
            "task_name": "express_validation_middleware",
            "description": "Fix Express API accepting malformed JSON payloads",
            "complexity": "easy",
            "category": "api_security"
        }
    ],
    "javascript": [
        {
            "task_name": "jest_mock_cleanup",
            "description": "Fix Jest tests with mock state leaking between test suites",
            "complexity": "easy",
            "category": "testing"
        },
        {
            "task_name": "express_connection_leak",
            "description": "Debug Express server connection pool leak",
            "complexity": "medium",
            "category": "memory_management"
        },
        {
            "task_name": "mongoose_migration_script",
            "description": "Fix MongoDB migration script with data corruption",
            "complexity": "hard",
            "category": "database_migrations"
        },
        {
            "task_name": "node_api_rate_limiting",
            "description": "Fix broken rate limiting allowing unlimited requests",
            "complexity": "medium",
            "category": "api_security"
        }
    ],
    "go": [
        {
            "task_name": "goroutine_leak_detection",
            "description": "Debug and fix goroutine leak in HTTP client connection handling",
            "complexity": "hard",
            "category": "memory_management"
        },
        {
            "task_name": "sql_migration_rollback",
            "description": "Fix database migration rollback leaving orphaned tables",
            "complexity": "medium",
            "category": "database_migrations"
        },
        {
            "task_name": "go_api_validation",
            "description": "Fix API handler accepting invalid request types",
            "complexity": "easy",
            "category": "api_security"
        },
        {
            "task_name": "gorm_query_optimization",
            "description": "Optimize GORM queries with N+1 problem",
            "complexity": "medium",
            "category": "performance"
        }
    ],
    "rust": [
        {
            "task_name": "actix_connection_pool",
            "description": "Fix Actix-web connection pool not releasing connections",
            "complexity": "hard",
            "category": "memory_management"
        },
        {
            "task_name": "diesel_migration_bug",
            "description": "Fix Diesel migration causing schema inconsistency",
            "complexity": "medium",
            "category": "database_migrations"
        }
    ],
    "java": [
        {
            "task_name": "spring_hikari_leak",
            "description": "Debug HikariCP connection pool leak in Spring Boot",
            "complexity": "medium",
            "category": "memory_management"
        },
        {
            "task_name": "hibernate_n_plus_one",
            "description": "Fix Hibernate N+1 query problem in REST API",
            "complexity": "medium",
            "category": "performance"
        }
    ]
}


def parse_args():
    parser = argparse.ArgumentParser(
        description='Create seed_dp tasks with configurable distribution'
    )
    parser.add_argument(
        '--count',
        type=int,
        default=10,
        help='Total number of tasks to create (default: 10)'
    )
    parser.add_argument(
        '--python',
        type=int,
        default=60,
        help='Percentage of Python tasks (default: 60)'
    )
    parser.add_argument(
        '--typescript',
        type=int,
        default=20,
        help='Percentage of TypeScript tasks (default: 20)'
    )
    parser.add_argument(
        '--javascript',
        type=int,
        default=10,
        help='Percentage of JavaScript tasks (default: 10)'
    )
    parser.add_argument(
        '--go',
        type=int,
        default=10,
        help='Percentage of Go tasks (default: 10)'
    )
    parser.add_argument(
        '--rust',
        type=int,
        default=0,
        help='Percentage of Rust tasks (default: 0)'
    )
    parser.add_argument(
        '--java',
        type=int,
        default=0,
        help='Percentage of Java tasks (default: 0)'
    )
    return parser.parse_args()


def select_tasks(count, language_percentages):
    """Select tasks based on language distribution percentages."""
    # Calculate how many tasks per language
    language_counts = {}
    total_percentage = sum(language_percentages.values())

    if total_percentage != 100:
        print(f"⚠️  Warning: Language percentages sum to {total_percentage}%, normalizing to 100%")

    remaining = count
    for lang, percentage in sorted(language_percentages.items(), key=lambda x: x[1], reverse=True):
        if lang not in TASK_POOL or not TASK_POOL[lang]:
            continue
        # Calculate tasks for this language (proportional)
        lang_count = round((percentage / total_percentage) * count)
        lang_count = min(lang_count, len(TASK_POOL[lang]))  # Can't exceed available tasks
        lang_count = min(lang_count, remaining)  # Can't exceed remaining slots
        if lang_count > 0:
            language_counts[lang] = lang_count
            remaining -= lang_count

    # Distribute any remaining tasks to languages with available capacity
    if remaining > 0:
        for lang in language_counts.keys():
            if remaining == 0:
                break
            available = len(TASK_POOL[lang]) - language_counts[lang]
            if available > 0:
                add = min(available, remaining)
                language_counts[lang] += add
                remaining -= add

    # Select random tasks from each language
    selected_tasks = []
    for lang, lang_count in language_counts.items():
        tasks = random.sample(TASK_POOL[lang], lang_count)
        for task in tasks:
            task["language"] = lang
            selected_tasks.append(task)

    # Shuffle to mix languages
    random.shuffle(selected_tasks)

    return selected_tasks, language_counts


def main():
    args = parse_args()

    # Initialize task manager - use same state file as data_pipeline.py
    state_file = Path(__file__).parent.parent / "state" / "generation_state.json"
    tm = TaskManager(state_file)

    # Build language distribution
    language_percentages = {}
    if args.python > 0:
        language_percentages["python"] = args.python
    if args.typescript > 0:
        language_percentages["typescript"] = args.typescript
    if args.javascript > 0:
        language_percentages["javascript"] = args.javascript
    if args.go > 0:
        language_percentages["go"] = args.go
    if args.rust > 0:
        language_percentages["rust"] = args.rust
    if args.java > 0:
        language_percentages["java"] = args.java

    if not language_percentages:
        print("Error: At least one language must have >0 percentage")
        return 1

    # Select tasks
    tasks_data, language_counts = select_tasks(args.count, language_percentages)

    print(f"\n{'='*60}")
    print(f"Creating {len(tasks_data)} seed_dp tasks")
    print(f"{'='*60}")
    print(f"Language distribution:")
    for lang, count in sorted(language_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(tasks_data)) * 100
        print(f"  {lang:12s}: {count:2d} tasks ({percentage:.1f}%)")
    print(f"{'='*60}\n")

    # Create tasks
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
            print(f"✓ Created {task_id}: {task_data['task_name']} ({task_data['language']})")
            created_count += 1

        except Exception as e:
            print(f"✗ Error creating {task_data['task_name']}: {e}")

    print(f"\n{'='*60}")
    print(f"Successfully created {created_count}/{len(tasks_data)} seed_dp tasks")
    print(f"{'='*60}")

    # Show updated status
    summary = tm.get_status_summary()
    print(f"\nTask manager status:")
    print(f"  Total tasks: {summary['total_tasks']}")
    print(f"  By type: {json.dumps(summary['type_counts'], indent=4)}")
    print(f"  By status: {json.dumps(summary['status_counts'], indent=4)}")

    # Save task IDs for easy reference
    output_file = Path(__file__).parent / "sdk_test_task_ids.json"
    output_file.write_text(json.dumps({
        "created_at": summary['metadata']['last_updated'],
        "task_ids": task_ids,
        "task_count": len(task_ids),
        "language_distribution": language_counts
    }, indent=2))

    print(f"\nTask IDs saved to: {output_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

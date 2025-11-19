"""
categories_tags.py - Shared module for valid categories and tags

This module provides the canonical source of valid categories and tags
used throughout the data generation pipeline.
"""

# Valid categories for datapoints - focused on backend software engineering
VALID_CATEGORIES = [
    "api-development",
    "backend-engineering",
    "code-refactoring",
    "database-engineering",
    "debugging",
    "integration-testing",
    "microservices",
    "security",
    "software-engineering",
    "testing-infrastructure",
    "web-development"
]

# Valid tags for datapoints - focused on backend software engineering
VALID_TAGS = [
    # Languages
    "python", "javascript", "typescript",

    # Backend frameworks & libraries
    "express", "fastapi", "flask", "django", "nestjs", "nodejs",

    # API & Web
    "api", "rest-api", "graphql", "websocket", "http", "middleware",
    "routing", "web-server", "microservices", "server-side",

    # Database
    "database", "sql", "nosql", "postgresql", "mysql", "mongodb",
    "redis", "orm", "prisma", "sequelize", "sqlalchemy",
    "query-optimization", "schema-design", "migration", "transactions",

    # Testing
    "unit-testing", "integration-testing", "e2e-testing", "test-automation",
    "pytest", "jest", "mocha", "testing-framework",

    # Development practices
    "debugging", "refactoring", "code-quality", "error-handling",
    "logging", "monitoring", "performance-optimization",

    # DevOps & Infrastructure
    "docker", "containers", "ci-cd", "deployment", "environment-config",

    # Backend patterns & concepts
    "authentication", "authorization", "caching", "async", "concurrency",
    "rate-limiting", "validation", "serialization", "pagination",

    # Tools & Version Control
    "git", "version-control", "package-management", "npm", "pip",

    # Data & Processing
    "data-processing", "json", "csv", "file-operations", "streaming",

    # Security
    "security", "encryption", "jwt", "oauth", "input-validation",

    # System & CLI
    "cli", "automation", "scripting", "build-automation"
]


def validate_category(category: str) -> bool:
    """Check if a category is valid."""
    return category in VALID_CATEGORIES


def validate_tags(tags: str) -> tuple[bool, str]:
    """
    Validate pipe-separated tags string.
    
    Returns:
        (is_valid, error_message)
    """
    if not tags:
        return False, "At least one tag is required"
    
    tag_list = [t.strip() for t in tags.split('|') if t.strip()]
    
    if len(tag_list) == 0:
        return False, "No valid tags provided"
    
    if len(tag_list) > 3:
        return False, f"Too many tags ({len(tag_list)}). Maximum 3 tags allowed."
    
    invalid_tags = [tag for tag in tag_list if tag not in VALID_TAGS]
    if invalid_tags:
        return False, f"Invalid tags: {', '.join(invalid_tags)}"
    
    return True, ""


def get_category_set() -> set[str]:
    """Get categories as a set for fast lookup."""
    return set(VALID_CATEGORIES)


def get_tag_set() -> set[str]:
    """Get tags as a set for fast lookup."""
    return set(VALID_TAGS)
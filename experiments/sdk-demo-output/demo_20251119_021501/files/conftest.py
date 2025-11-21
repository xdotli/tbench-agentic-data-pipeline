"""
Pytest configuration and fixtures for inventory service tests.
"""

import pytest
import os
import time
import logging
import psycopg2
from psycopg2 import sql

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "inventory_test")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

# Kafka configuration
KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:9092")


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment (called once per session)."""
    logger.info("Setting up test environment...")

    # Wait for PostgreSQL to be ready
    max_retries = 30
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database="postgres"
            )
            conn.close()
            logger.info("✓ PostgreSQL is ready")
            break
        except psycopg2.Error as e:
            if attempt == max_retries - 1:
                raise RuntimeError(f"PostgreSQL not ready after {max_retries} attempts: {e}")
            logger.warning(f"Waiting for PostgreSQL... (attempt {attempt + 1}/{max_retries})")
            time.sleep(1)

    # Wait for Kafka to be ready
    for attempt in range(max_retries):
        try:
            from kafka import KafkaProducer
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BROKERS,
                request_timeout_ms=5000
            )
            producer.close()
            logger.info("✓ Kafka is ready")
            break
        except Exception as e:
            if attempt == max_retries - 1:
                logger.warning(f"Kafka not ready after {max_retries} attempts: {e}")
                logger.warning("Continuing with database tests only...")
            else:
                logger.warning(f"Waiting for Kafka... (attempt {attempt + 1}/{max_retries})")
                time.sleep(1)

    yield
    logger.info("Test environment setup complete")


@pytest.fixture(scope="session")
def db_setup():
    """Create test database (called once per session)."""
    logger.info("Creating test database...")

    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database="postgres"
    )
    conn.autocommit = True
    cursor = conn.cursor()

    # Drop test database if it exists
    try:
        cursor.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(
            sql.Identifier(DB_NAME)
        ))
        logger.info(f"Dropped existing database {DB_NAME}")
    except psycopg2.Error as e:
        logger.warning(f"Could not drop database: {e}")

    # Create test database
    cursor.execute(sql.SQL("CREATE DATABASE {}").format(
        sql.Identifier(DB_NAME)
    ))
    logger.info(f"Created database {DB_NAME}")

    cursor.close()
    conn.close()

    yield

    # Cleanup after all tests
    logger.info("Cleaning up test database...")
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database="postgres"
    )
    conn.autocommit = True
    cursor = conn.cursor()

    # Terminate all connections to the test database
    cursor.execute("""
    SELECT pg_terminate_backend(pg_stat_activity.pid)
    FROM pg_stat_activity
    WHERE pg_stat_activity.datname = %s
    AND pid <> pg_backend_pid()
    """, (DB_NAME,))

    # Drop database
    cursor.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(
        sql.Identifier(DB_NAME)
    ))

    cursor.close()
    conn.close()
    logger.info("Test database cleanup complete")


@pytest.fixture(scope="function")
def test_db(db_setup):
    """Get a database connection for a test."""
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

    yield conn

    conn.close()


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "race: mark test as checking for race conditions"
    )
    config.addinivalue_line(
        "markers", "idempotency: mark test as checking idempotent processing"
    )
    config.addinivalue_line(
        "markers", "isolation: mark test as checking transaction isolation"
    )
    config.addinivalue_line(
        "markers", "locking: mark test as checking locking mechanisms"
    )
    config.addinivalue_line(
        "markers", "atomic: mark test as checking atomic operations"
    )
    config.addinivalue_line(
        "markers", "consumer: mark test as checking Kafka consumer behavior"
    )
    config.addinivalue_line(
        "markers", "stress: mark test as a high-load stress test"
    )


def pytest_collection_modifyitems(config, items):
    """Add markers to tests based on class names."""
    for item in items:
        if "RaceCondition" in item.nodeid:
            item.add_marker(pytest.mark.race)
        if "Idempotency" in item.nodeid:
            item.add_marker(pytest.mark.idempotency)
        if "Isolation" in item.nodeid:
            item.add_marker(pytest.mark.isolation)
        if "Locking" in item.nodeid:
            item.add_marker(pytest.mark.locking)
        if "Atomic" in item.nodeid:
            item.add_marker(pytest.mark.atomic)
        if "Consumer" in item.nodeid:
            item.add_marker(pytest.mark.consumer)
        if "Load" in item.nodeid:
            item.add_marker(pytest.mark.stress)

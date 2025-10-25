"""
Database Connection and Session Management

Handles SQLite database initialization and provides session management
for all database operations.
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from dotenv import load_dotenv

from .models import Base

load_dotenv()

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///linelink.db')

# For SQLite, we need special configuration for thread safety
# StaticPool keeps a single connection alive for the application
if DATABASE_URL.startswith('sqlite'):
    engine = create_engine(
        DATABASE_URL,
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
        echo=False  # Set to True for SQL query logging
    )
else:
    engine = create_engine(DATABASE_URL, echo=False)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Thread-safe scoped session
ScopedSession = scoped_session(SessionLocal)


def init_db():
    """
    Initialize database by creating all tables

    This should be called once when the application starts.
    It's safe to call multiple times - existing tables won't be affected.
    """
    try:
        Base.metadata.create_all(bind=engine)
        print("✓ Database tables created successfully")
        return True
    except Exception as e:
        print(f"✗ Error creating database tables: {e}")
        return False


def get_session():
    """
    Get a new database session

    Usage:
        session = get_session()
        try:
            # Do database operations
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    Returns:
        Session: SQLAlchemy session object
    """
    return SessionLocal()


@contextmanager
def get_db():
    """
    Context manager for database sessions

    Automatically handles session lifecycle:
    - Creates session
    - Commits on success
    - Rolls back on error
    - Closes session when done

    Usage:
        with get_db() as db:
            db.add(new_record)
            db.query(Model).filter(...).all()
    """
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def drop_all_tables():
    """
    Drop all tables from database

    WARNING: This deletes all data!
    Only use for testing or during development.
    """
    Base.metadata.drop_all(bind=engine)
    print("⚠ All database tables dropped")


def reset_database():
    """
    Reset database by dropping and recreating all tables

    WARNING: This deletes all data!
    Only use for testing or during development.
    """
    drop_all_tables()
    init_db()
    print("✓ Database reset complete")


# Database health check
def check_database_health():
    """
    Check if database is accessible and tables exist

    Returns:
        dict: Health status information
    """
    try:
        with get_db() as db:
            # Try a simple query
            db.execute(text("SELECT 1"))

        # Check if tables exist
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        return {
            'healthy': True,
            'tables': tables,
            'table_count': len(tables),
            'database_url': DATABASE_URL.split('://')[1] if '://' in DATABASE_URL else DATABASE_URL
        }
    except Exception as e:
        return {
            'healthy': False,
            'error': str(e)
        }


# Example usage
if __name__ == "__main__":
    print("Initializing database...")
    init_db()

    print("\nDatabase health check:")
    health = check_database_health()
    print(f"  Healthy: {health['healthy']}")
    if health['healthy']:
        print(f"  Tables: {', '.join(health['tables'])}")
        print(f"  Database: {health['database_url']}")
    else:
        print(f"  Error: {health.get('error', 'Unknown')}")

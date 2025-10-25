#!/usr/bin/env python3
"""
Database Initialization Script

Run this script to set up the LineLink database.
It will create all necessary tables and optionally populate with test data.

Usage:
    python init_db.py              # Initialize database
    python init_db.py --reset      # Reset database (WARNING: deletes all data)
    python init_db.py --test-data  # Initialize with test data
"""

import sys
import argparse
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, '.')

from database.db import init_db, reset_database, check_database_health
from database.repositories import (
    AlertRepository,
    WeatherRepository,
    LineRatingRepository,
    SystemLogRepository
)
from database.db import get_db


def create_test_data():
    """Create sample data for testing"""
    print("\nCreating test data...")

    with get_db() as db:
        # Create sample weather readings
        for i in range(10):
            timestamp = datetime.utcnow() - timedelta(hours=10-i)
            weather_data = {
                'timestamp': timestamp,
                'temperature': 25 + i * 0.5,  # Gradually increasing temp
                'wind_speed': 6.5 - i * 0.2,  # Gradually decreasing wind
                'wind_direction': 180,
                'description': 'clear sky' if i < 5 else 'few clouds',
                'source': 'test_data',
                'latitude': 21.3099,
                'longitude': -157.8581
            }
            WeatherRepository.save_weather(db, weather_data)
            print(f"  ✓ Created weather reading {i+1}/10")

        # Create sample line rating history
        lines = ['L0', 'L5', 'L12', 'L15']
        for i in range(10):
            timestamp = datetime.utcnow() - timedelta(hours=10-i)
            for line in lines:
                loading = 70 + i * 2.5  # Gradually increasing loading
                rating_data = {
                    'timestamp': timestamp,
                    'line_name': line,
                    'branch_name': f'{line} Test Branch',
                    'rating_amps': 800,
                    'rating_mva': 200,
                    'flow_mva': loading * 2,
                    'loading_pct': loading,
                    'status': 'OK' if loading < 80 else ('WARNING' if loading < 95 else 'CRITICAL'),
                    'voltage_kv': 138,
                    'conductor': '795 ACSR',
                    'mot': 80
                }
                LineRatingRepository.save_rating(db, rating_data)
            print(f"  ✓ Created rating history {i+1}/10 for {len(lines)} lines")

        # Create sample alerts
        alert_data = {
            'line_name': 'L5',
            'branch_name': 'SURF69 TO TURTLE69',
            'severity': 'WARNING',
            'loading_pct': 87.5,
            'rating_mva': 100,
            'flow_mva': 87.5,
            'voltage_kv': 69,
            'predicted_time': datetime.utcnow() + timedelta(hours=2),
            'sent_at': datetime.utcnow(),
            'recipients_sms': '+1234567890',
            'recipients_email': 'test@example.com',
            'temperature': 32.5,
            'wind_speed': 4.2
        }
        AlertRepository.save_alert(db, alert_data)
        print("  ✓ Created sample alert")

        # Create system logs
        log_types = [
            ('INFO', 'startup', 'System initialized successfully'),
            ('INFO', 'api_call', 'Weather data fetched from OpenWeatherMap'),
            ('WARNING', 'calculation', 'High loading detected on line L5'),
            ('ERROR', 'notification', 'Failed to send SMS (test error)')
        ]

        for level, event_type, message in log_types:
            SystemLogRepository.log(
                db,
                level=level,
                event_type=event_type,
                message=message,
                module='test_data',
                function='create_test_data'
            )
        print(f"  ✓ Created {len(log_types)} system logs")

    print("\n✓ Test data created successfully!")


def main():
    parser = argparse.ArgumentParser(description='Initialize LineLink database')
    parser.add_argument('--reset', action='store_true',
                       help='Reset database (WARNING: deletes all data)')
    parser.add_argument('--test-data', action='store_true',
                       help='Populate with test data')
    parser.add_argument('--health-check', action='store_true',
                       help='Only run health check')

    args = parser.parse_args()

    print("="*60)
    print("LineLink Database Initialization")
    print("="*60)

    # Health check only
    if args.health_check:
        print("\nRunning database health check...")
        health = check_database_health()
        print(f"  Status: {'✓ Healthy' if health['healthy'] else '✗ Unhealthy'}")
        if health['healthy']:
            print(f"  Database: {health['database_url']}")
            print(f"  Tables: {health['table_count']}")
            for table in health['tables']:
                print(f"    - {table}")
        else:
            print(f"  Error: {health.get('error', 'Unknown')}")
        return

    # Reset database
    if args.reset:
        print("\n⚠️  WARNING: This will delete ALL data!")
        response = input("Are you sure you want to reset the database? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            return

        print("\nResetting database...")
        reset_database()

    # Initialize database
    else:
        print("\nInitializing database...")
        success = init_db()
        if not success:
            print("✗ Database initialization failed")
            return

    # Add test data
    if args.test_data:
        create_test_data()

    # Final health check
    print("\nRunning health check...")
    health = check_database_health()
    if health['healthy']:
        print("✓ Database is healthy")
        print(f"  Location: {health['database_url']}")
        print(f"  Tables created: {', '.join(health['tables'])}")
    else:
        print("✗ Database health check failed")
        print(f"  Error: {health.get('error', 'Unknown')}")

    print("\n" + "="*60)
    print("Database initialization complete!")
    print("="*60)


if __name__ == "__main__":
    main()

"""
Data Access Layer (Repositories)

Provides clean interfaces for database operations without exposing
raw SQLAlchemy queries to the rest of the application.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from .models import AlertHistory, WeatherReading, LineRatingHistory, SystemLog
from .db import get_db


class AlertRepository:
    """Repository for alert history operations"""

    @staticmethod
    def save_alert(session: Session, alert_data: Dict) -> AlertHistory:
        """
        Save a new alert record

        Args:
            session: Database session
            alert_data: Dictionary with alert information

        Returns:
            AlertHistory: Created alert record
        """
        alert = AlertHistory(**alert_data)
        session.add(alert)
        session.flush()  # Get the ID without committing
        return alert

    @staticmethod
    def get_recent_alerts(session: Session, hours: int = 24) -> List[AlertHistory]:
        """
        Get alerts from the last N hours

        Args:
            session: Database session
            hours: Number of hours to look back

        Returns:
            List of AlertHistory records
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return session.query(AlertHistory).filter(
            AlertHistory.sent_at >= cutoff_time
        ).order_by(desc(AlertHistory.sent_at)).all()

    @staticmethod
    def get_alerts_for_line(session: Session, line_name: str,
                           hours: int = 24) -> List[AlertHistory]:
        """
        Get all alerts for a specific line

        Args:
            session: Database session
            line_name: Name of the transmission line
            hours: Number of hours to look back

        Returns:
            List of AlertHistory records
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return session.query(AlertHistory).filter(
            AlertHistory.line_name == line_name,
            AlertHistory.sent_at >= cutoff_time
        ).order_by(desc(AlertHistory.sent_at)).all()

    @staticmethod
    def get_alert_statistics(session: Session, days: int = 7) -> Dict:
        """
        Get summary statistics about alerts

        Args:
            session: Database session
            days: Number of days to analyze

        Returns:
            Dictionary with statistics
        """
        cutoff_time = datetime.utcnow() - timedelta(days=days)

        total_alerts = session.query(func.count(AlertHistory.id)).filter(
            AlertHistory.sent_at >= cutoff_time
        ).scalar()

        critical_alerts = session.query(func.count(AlertHistory.id)).filter(
            AlertHistory.sent_at >= cutoff_time,
            AlertHistory.severity == 'CRITICAL'
        ).scalar()

        # Most problematic lines
        top_lines = session.query(
            AlertHistory.line_name,
            func.count(AlertHistory.id).label('alert_count')
        ).filter(
            AlertHistory.sent_at >= cutoff_time
        ).group_by(
            AlertHistory.line_name
        ).order_by(
            desc('alert_count')
        ).limit(10).all()

        return {
            'total_alerts': total_alerts,
            'critical_alerts': critical_alerts,
            'warning_alerts': total_alerts - critical_alerts,
            'period_days': days,
            'top_problematic_lines': [
                {'line_name': line, 'count': count}
                for line, count in top_lines
            ]
        }


class WeatherRepository:
    """Repository for weather reading operations"""

    @staticmethod
    def save_weather(session: Session, weather_data: Dict) -> WeatherReading:
        """
        Save a weather reading

        Args:
            session: Database session
            weather_data: Dictionary with weather information

        Returns:
            WeatherReading: Created weather record
        """
        weather = WeatherReading(**weather_data)
        session.add(weather)
        session.flush()
        return weather

    @staticmethod
    def get_latest_weather(session: Session) -> Optional[WeatherReading]:
        """
        Get the most recent weather reading

        Args:
            session: Database session

        Returns:
            Latest WeatherReading or None
        """
        return session.query(WeatherReading).order_by(
            desc(WeatherReading.timestamp)
        ).first()

    @staticmethod
    def get_weather_history(session: Session, hours: int = 24) -> List[WeatherReading]:
        """
        Get weather readings from last N hours

        Args:
            session: Database session
            hours: Number of hours to look back

        Returns:
            List of WeatherReading records
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return session.query(WeatherReading).filter(
            WeatherReading.timestamp >= cutoff_time
        ).order_by(WeatherReading.timestamp).all()

    @staticmethod
    def cleanup_old_weather(session: Session, days: int = 7):
        """
        Delete weather readings older than N days

        Args:
            session: Database session
            days: Delete data older than this many days
        """
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        deleted = session.query(WeatherReading).filter(
            WeatherReading.timestamp < cutoff_time
        ).delete()
        session.commit()
        return deleted


class LineRatingRepository:
    """Repository for line rating history operations"""

    @staticmethod
    def save_rating(session: Session, rating_data: Dict,
                   weather_id: Optional[int] = None) -> LineRatingHistory:
        """
        Save a line rating calculation

        Args:
            session: Database session
            rating_data: Dictionary with rating information
            weather_id: Optional ID of associated weather reading

        Returns:
            LineRatingHistory: Created rating record
        """
        rating = LineRatingHistory(**rating_data, weather_id=weather_id)
        session.add(rating)
        session.flush()
        return rating

    @staticmethod
    def get_rating_history(session: Session, line_name: str,
                          hours: int = 24) -> List[LineRatingHistory]:
        """
        Get rating history for a specific line

        Args:
            session: Database session
            line_name: Name of the transmission line
            hours: Number of hours to look back

        Returns:
            List of LineRatingHistory records
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return session.query(LineRatingHistory).filter(
            LineRatingHistory.line_name == line_name,
            LineRatingHistory.timestamp >= cutoff_time
        ).order_by(LineRatingHistory.timestamp).all()

    @staticmethod
    def get_critical_ratings(session: Session, threshold: float = 95,
                            hours: int = 24) -> List[LineRatingHistory]:
        """
        Get all ratings exceeding a threshold

        Args:
            session: Database session
            threshold: Loading percentage threshold
            hours: Number of hours to look back

        Returns:
            List of critical LineRatingHistory records
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return session.query(LineRatingHistory).filter(
            LineRatingHistory.loading_pct >= threshold,
            LineRatingHistory.timestamp >= cutoff_time
        ).order_by(desc(LineRatingHistory.loading_pct)).all()

    @staticmethod
    def cleanup_old_ratings(session: Session, days: int = 30):
        """
        Delete rating history older than N days

        Args:
            session: Database session
            days: Delete data older than this many days
        """
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        deleted = session.query(LineRatingHistory).filter(
            LineRatingHistory.timestamp < cutoff_time
        ).delete()
        session.commit()
        return deleted


class SystemLogRepository:
    """Repository for system log operations"""

    @staticmethod
    def log(session: Session, level: str, event_type: str, message: str,
            details: Optional[str] = None, module: Optional[str] = None,
            function: Optional[str] = None) -> SystemLog:
        """
        Create a system log entry

        Args:
            session: Database session
            level: Log level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
            event_type: Type of event ('api_call', 'calculation', etc.)
            message: Log message
            details: Optional additional details (can be JSON)
            module: Source module name
            function: Source function name

        Returns:
            SystemLog: Created log record
        """
        log = SystemLog(
            level=level,
            event_type=event_type,
            message=message,
            details=details,
            module=module,
            function=function
        )
        session.add(log)
        session.flush()
        return log

    @staticmethod
    def get_recent_logs(session: Session, hours: int = 24,
                       level: Optional[str] = None) -> List[SystemLog]:
        """
        Get recent log entries

        Args:
            session: Database session
            hours: Number of hours to look back
            level: Optional filter by log level

        Returns:
            List of SystemLog records
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        query = session.query(SystemLog).filter(
            SystemLog.timestamp >= cutoff_time
        )

        if level:
            query = query.filter(SystemLog.level == level)

        return query.order_by(desc(SystemLog.timestamp)).all()

    @staticmethod
    def get_error_summary(session: Session, hours: int = 24) -> Dict:
        """
        Get summary of errors and warnings

        Args:
            session: Database session
            hours: Number of hours to analyze

        Returns:
            Dictionary with error statistics
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        errors = session.query(func.count(SystemLog.id)).filter(
            SystemLog.timestamp >= cutoff_time,
            SystemLog.level == 'ERROR'
        ).scalar()

        warnings = session.query(func.count(SystemLog.id)).filter(
            SystemLog.timestamp >= cutoff_time,
            SystemLog.level == 'WARNING'
        ).scalar()

        return {
            'errors': errors,
            'warnings': warnings,
            'period_hours': hours
        }

    @staticmethod
    def cleanup_old_logs(session: Session, days: int = 30):
        """
        Delete logs older than N days

        Args:
            session: Database session
            days: Delete logs older than this many days
        """
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        deleted = session.query(SystemLog).filter(
            SystemLog.timestamp < cutoff_time
        ).delete()
        session.commit()
        return deleted


# Convenience functions for common operations
def log_info(message: str, **kwargs):
    """Quick helper to log info message"""
    with get_db() as db:
        SystemLogRepository.log(db, 'INFO', kwargs.get('event_type', 'general'),
                               message, **kwargs)


def log_error(message: str, **kwargs):
    """Quick helper to log error message"""
    with get_db() as db:
        SystemLogRepository.log(db, 'ERROR', kwargs.get('event_type', 'error'),
                               message, **kwargs)


def log_warning(message: str, **kwargs):
    """Quick helper to log warning message"""
    with get_db() as db:
        SystemLogRepository.log(db, 'WARNING', kwargs.get('event_type', 'warning'),
                               message, **kwargs)

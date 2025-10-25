"""
SQLAlchemy ORM Models for LineLink Database

Tables:
    - alert_history: Historical record of all alerts sent
    - weather_readings: Cached weather data from API
    - line_rating_history: Historical line rating calculations
    - system_logs: Application event logs
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class AlertHistory(Base):
    """
    Record of alerts sent to operators

    This table tracks when alerts were sent, to whom, and their severity
    to enable:
    - Alert deduplication (don't spam same alert)
    - Analytics on alert frequency
    - Audit trail for compliance
    """
    __tablename__ = 'alert_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    line_name = Column(String(100), nullable=False, index=True)
    branch_name = Column(String(200), nullable=True)
    severity = Column(String(20), nullable=False)  # 'CRITICAL', 'WARNING'
    loading_pct = Column(Float, nullable=False)
    rating_mva = Column(Float, nullable=True)
    flow_mva = Column(Float, nullable=True)
    voltage_kv = Column(Float, nullable=True)

    # When the condition was predicted to occur
    predicted_time = Column(DateTime, nullable=False)

    # When the alert was actually sent
    sent_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Who received the alert
    recipients_sms = Column(Text, nullable=True)  # Comma-separated phone numbers
    recipients_email = Column(Text, nullable=True)  # Comma-separated emails

    # Weather conditions at time of alert
    temperature = Column(Float, nullable=True)
    wind_speed = Column(Float, nullable=True)

    def __repr__(self):
        return (f"<AlertHistory(id={self.id}, line={self.line_name}, "
                f"severity={self.severity}, loading={self.loading_pct:.1f}%)>")


class WeatherReading(Base):
    """
    Cached weather data from OpenWeatherMap API

    Reduces API calls by storing recent readings.
    Also enables historical analysis and trend detection.
    """
    __tablename__ = 'weather_readings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True, default=datetime.utcnow)

    # Weather data
    temperature = Column(Float, nullable=False)  # °C
    wind_speed = Column(Float, nullable=False)  # ft/s
    wind_direction = Column(Float, nullable=True)  # degrees
    description = Column(String(100), nullable=True)

    # Metadata
    source = Column(String(50), default='openweathermap')  # 'openweathermap', 'forecast', 'manual'
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Link to line ratings calculated with this weather
    line_ratings = relationship("LineRatingHistory", back_populates="weather")

    def __repr__(self):
        return (f"<WeatherReading(id={self.id}, temp={self.temperature:.1f}°C, "
                f"wind={self.wind_speed:.1f}ft/s, time={self.timestamp})>")


class LineRatingHistory(Base):
    """
    Historical record of line rating calculations

    Stores calculated ratings over time to enable:
    - Trend analysis
    - Performance optimization
    - ML model training for predictions
    """
    __tablename__ = 'line_rating_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True, default=datetime.utcnow)

    # Line identification
    line_name = Column(String(100), nullable=False, index=True)
    branch_name = Column(String(200), nullable=True)

    # Rating calculation results
    rating_amps = Column(Float, nullable=False)
    rating_mva = Column(Float, nullable=False)
    flow_mva = Column(Float, nullable=False)
    loading_pct = Column(Float, nullable=False)
    status = Column(String(20), nullable=False)  # 'OK', 'WARNING', 'CRITICAL', 'OVERLOAD'

    # Conductor properties
    voltage_kv = Column(Float, nullable=False)
    conductor = Column(String(100), nullable=True)
    mot = Column(Float, nullable=True)  # Maximum Operating Temperature

    # Link to weather conditions
    weather_id = Column(Integer, ForeignKey('weather_readings.id'), nullable=True)
    weather = relationship("WeatherReading", back_populates="line_ratings")

    def __repr__(self):
        return (f"<LineRatingHistory(id={self.id}, line={self.line_name}, "
                f"loading={self.loading_pct:.1f}%, status={self.status})>")


class SystemLog(Base):
    """
    Application event logs

    Records significant events for debugging and monitoring:
    - API errors
    - Calculation failures
    - Alert send attempts
    - Configuration changes
    """
    __tablename__ = 'system_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True, default=datetime.utcnow)

    # Log classification
    level = Column(String(20), nullable=False)  # 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    event_type = Column(String(50), nullable=False, index=True)  # 'api_call', 'calculation', 'alert_sent', etc.

    # Log content
    message = Column(Text, nullable=False)
    details = Column(Text, nullable=True)  # JSON or additional context

    # Source tracking
    module = Column(String(50), nullable=True)  # 'weather', 'calculations', 'alerts', etc.
    function = Column(String(100), nullable=True)

    def __repr__(self):
        return (f"<SystemLog(id={self.id}, level={self.level}, "
                f"type={self.event_type}, time={self.timestamp})>")

"""
LineLink Modules Package

This package contains the core business logic modules for the LineLink
transmission line monitoring system.

Modules:
    - weather: OpenWeatherMap API integration
    - calculations: IEEE-738 line rating calculations
    - alerts: Alert generation and management
    - notifications: SMS and email notification services
"""

__version__ = "1.0.0"
__all__ = ["weather", "calculations", "alerts", "notifications"]

"""
IEEE-738 Standard for Calculating the Current-Temperature Relationship
of Bare Overhead Conductors

This module implements the IEEE-738-2006 standard for calculating the
ampacity (current-carrying capacity) of bare overhead conductors based
on weather conditions and conductor properties.

The calculation balances heat gain (solar, resistive) with heat loss
(convective, radiative) to determine the maximum current before the
conductor reaches its maximum operating temperature.
"""

from .conductor import Conductor, ConductorParams

__version__ = "1.0.0"
__all__ = ["Conductor", "ConductorParams"]

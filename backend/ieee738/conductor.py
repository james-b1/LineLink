"""
IEEE-738 Conductor Rating Calculations

Implements the steady-state thermal rating calculation for overhead
transmission line conductors.
"""

import math
from pydantic import BaseModel, Field
from typing import Literal


class ConductorParams(BaseModel):
    """
    Parameters for IEEE-738 conductor rating calculation

    Environmental Parameters:
        Ta: Ambient temperature (°C)
        WindVelocity: Wind velocity perpendicular to conductor (ft/s)
        WindAngleDeg: Angle between wind and conductor (degrees, typically 90)
        SunTime: Hour of day (0-24) for solar calculations
        Date: Date string (e.g., "21 Jun") for solar angle
        Atmosphere: Atmospheric clarity ('Clear', 'Industrial')
        Elevation: Elevation above sea level (ft)
        Latitude: Geographic latitude (degrees)

    Conductor Properties:
        Diameter: Conductor diameter (inches)
        Emissivity: Surface emissivity (typically 0.8 for weathered ACSR)
        Absorptivity: Solar absorptivity (typically 0.8 for weathered ACSR)
        TLo: Low reference temperature for resistance (°C, typically 25)
        THi: High reference temperature for resistance (°C, typically 50)
        RLo: Resistance at TLo (ohms/ft)
        RHi: Resistance at THi (ohms/ft)
        Tc: Maximum conductor operating temperature (°C)

    Line Properties:
        Direction: Line orientation ('EastWest' or 'NorthSouth')
    """
    # Environmental conditions
    Ta: float = Field(..., description="Ambient temperature (°C)")
    WindVelocity: float = Field(..., description="Wind velocity (ft/s)")
    WindAngleDeg: float = Field(default=90, description="Wind angle (degrees)")
    SunTime: float = Field(..., description="Hour of day (0-24)")
    Date: str = Field(..., description="Date string (e.g., '21 Jun')")
    Atmosphere: Literal['Clear', 'Industrial'] = Field(default='Clear')
    Elevation: float = Field(default=1000, description="Elevation (ft)")
    Latitude: float = Field(..., description="Latitude (degrees)")

    # Conductor surface properties
    Diameter: float = Field(..., description="Conductor diameter (inches)")
    Emissivity: float = Field(default=0.8, description="Surface emissivity")
    Absorptivity: float = Field(default=0.8, description="Solar absorptivity")

    # Conductor electrical properties
    TLo: float = Field(..., description="Low reference temperature (°C)")
    THi: float = Field(..., description="High reference temperature (°C)")
    RLo: float = Field(..., description="Resistance at TLo (ohms/ft)")
    RHi: float = Field(..., description="Resistance at THi (ohms/ft)")

    # Operating limits
    Tc: float = Field(..., description="Maximum conductor temperature (°C)")

    # Line properties
    Direction: Literal['EastWest', 'NorthSouth'] = Field(default='EastWest')


class Conductor:
    """
    IEEE-738 Conductor thermal rating calculator

    This class calculates the maximum steady-state current (ampacity)
    that a conductor can carry before reaching its maximum operating
    temperature, given specific weather and conductor conditions.
    """

    def __init__(self, params: ConductorParams):
        """
        Initialize conductor with parameters

        Args:
            params: ConductorParams object with all required parameters
        """
        self.params = params

    def steady_state_thermal_rating(self) -> float:
        """
        Calculate steady-state thermal rating (ampacity) in Amps

        This implements the IEEE-738 heat balance equation:
        q_c + q_r = q_s + I²R(Tc)

        Where:
            q_c = Convective heat loss
            q_r = Radiative heat loss
            q_s = Solar heat gain
            I = Current (Amps) - what we're solving for
            R(Tc) = Resistance at conductor temperature

        Returns:
            float: Maximum current in Amps
        """
        # Calculate heat loss (cooling)
        q_convection = self._convective_heat_loss()
        q_radiation = self._radiative_heat_loss()
        total_heat_loss = q_convection + q_radiation

        # Calculate solar heat gain
        q_solar = self._solar_heat_gain()

        # Calculate resistance at maximum conductor temperature
        r_tc = self._resistance_at_temperature(self.params.Tc)

        # Solve heat balance for current
        # q_c + q_r = q_s + I²R
        # I² = (q_c + q_r - q_s) / R
        # I = sqrt((q_c + q_r - q_s) / R)

        net_cooling = total_heat_loss - q_solar

        if net_cooling <= 0:
            # No cooling available - conductor would overheat regardless of current
            return 0.0

        if r_tc <= 0:
            # Invalid resistance
            return 0.0

        current_squared = net_cooling / r_tc
        current = math.sqrt(max(0, current_squared))

        return current

    def _convective_heat_loss(self) -> float:
        """
        Calculate convective cooling (W/ft)

        IEEE-738 provides different equations for:
        - Natural convection (low wind)
        - Forced convection (wind > 0)

        Returns:
            float: Convective heat loss in W/ft
        """
        p = self.params

        # Film temperature (average of conductor and ambient)
        t_film = (p.Tc + p.Ta) / 2.0

        # Air properties at film temperature
        density = self._air_density(t_film)
        viscosity = self._air_viscosity(t_film)
        thermal_conductivity = self._air_thermal_conductivity(t_film)

        # Convert diameter from inches to feet
        diameter_ft = p.Diameter / 12.0

        # Reynolds number
        reynolds = (density * p.WindVelocity * diameter_ft) / viscosity

        # Nusselt number (forced convection correlation)
        if reynolds < 1:
            # Natural convection
            nusselt = 0.65
        else:
            # Forced convection
            nusselt = 0.65 + 0.2 * (reynolds ** 0.6)

        # Convective heat transfer coefficient
        h_c = nusselt * thermal_conductivity / diameter_ft

        # Convective heat loss per unit length
        q_c = h_c * math.pi * diameter_ft * (p.Tc - p.Ta)

        return max(0, q_c)

    def _radiative_heat_loss(self) -> float:
        """
        Calculate radiative cooling (W/ft)

        Uses Stefan-Boltzmann law:
        q_r = ε * σ * π * D * (Tc⁴ - Ta⁴)

        Returns:
            float: Radiative heat loss in W/ft
        """
        p = self.params

        # Stefan-Boltzmann constant (W/(m²·K⁴))
        sigma = 5.67e-8

        # Convert temperatures to Kelvin
        tc_kelvin = p.Tc + 273.15
        ta_kelvin = p.Ta + 273.15

        # Convert diameter from inches to meters
        diameter_m = p.Diameter * 0.0254

        # Radiative heat loss per meter
        q_r_per_m = (p.Emissivity * sigma * math.pi * diameter_m *
                     (tc_kelvin**4 - ta_kelvin**4))

        # Convert from W/m to W/ft
        q_r = q_r_per_m * 0.3048

        return max(0, q_r)

    def _solar_heat_gain(self) -> float:
        """
        Calculate solar heat gain (W/ft)

        Depends on:
        - Solar irradiance (based on atmosphere, time of day, season)
        - Conductor absorptivity
        - Conductor projected area

        Returns:
            float: Solar heat gain in W/ft
        """
        p = self.params

        # Simplified solar calculation
        # Full IEEE-738 uses complex solar position algorithms

        # Base solar irradiance (W/m²) - clear day at solar noon
        if p.Atmosphere == 'Clear':
            base_irradiance = 1000
        else:  # Industrial
            base_irradiance = 850

        # Time of day factor (peaks at solar noon ~12:00)
        hour_angle = abs(p.SunTime - 12)
        time_factor = math.cos(math.radians(hour_angle * 15))  # 15°/hour
        time_factor = max(0, time_factor)

        # Seasonal factor (simplified - would normally parse Date)
        # Assume moderate season
        season_factor = 0.9

        # Effective solar irradiance
        solar_irradiance = base_irradiance * time_factor * season_factor

        # Projected area per unit length
        # For a cylinder, projected area = diameter * length
        diameter_m = p.Diameter * 0.0254  # inches to meters
        projected_area_per_m = diameter_m  # m²/m

        # Solar heat gain per meter
        q_s_per_m = p.Absorptivity * solar_irradiance * projected_area_per_m

        # Convert from W/m to W/ft
        q_s = q_s_per_m * 0.3048

        return max(0, q_s)

    def _resistance_at_temperature(self, temp: float) -> float:
        """
        Calculate conductor resistance at given temperature using linear interpolation

        R(T) = RLo + (RHi - RLo) * (T - TLo) / (THi - TLo)

        Args:
            temp: Temperature in °C

        Returns:
            float: Resistance in ohms/ft
        """
        p = self.params

        if p.THi == p.TLo:
            return p.RLo

        slope = (p.RHi - p.RLo) / (p.THi - p.TLo)
        resistance = p.RLo + slope * (temp - p.TLo)

        return max(1e-10, resistance)  # Prevent division by zero

    def _air_density(self, temp_c: float) -> float:
        """
        Air density at temperature (lb/ft³)

        Args:
            temp_c: Temperature in °C

        Returns:
            float: Air density in lb/ft³
        """
        # Ideal gas approximation
        # ρ = P/(R*T) adjusted for elevation

        # Standard air density at sea level, 15°C (lb/ft³)
        rho_0 = 0.0765

        # Temperature correction
        temp_k = temp_c + 273.15
        temp_ref_k = 15 + 273.15

        # Elevation correction (simplified)
        elevation_factor = math.exp(-self.params.Elevation / 30000)

        density = rho_0 * (temp_ref_k / temp_k) * elevation_factor

        return density

    def _air_viscosity(self, temp_c: float) -> float:
        """
        Dynamic viscosity of air (lb/(ft·s))

        Args:
            temp_c: Temperature in °C

        Returns:
            float: Dynamic viscosity in lb/(ft·s)
        """
        # Sutherland's formula approximation
        temp_k = temp_c + 273.15

        # Reference values
        mu_ref = 1.716e-5  # Pa·s at 273K
        t_ref = 273.15
        s = 110.4  # Sutherland constant

        mu_si = mu_ref * ((temp_k / t_ref) ** 1.5) * ((t_ref + s) / (temp_k + s))

        # Convert Pa·s to lb/(ft·s)
        mu = mu_si * 0.0208854

        return mu

    def _air_thermal_conductivity(self, temp_c: float) -> float:
        """
        Thermal conductivity of air (W/(ft·°C))

        Args:
            temp_c: Temperature in °C

        Returns:
            float: Thermal conductivity in W/(ft·°C)
        """
        # Linear approximation
        # k(T) = 0.023 + 0.00007 * T (W/(m·K))

        k_si = 0.023 + 0.00007 * temp_c  # W/(m·K)

        # Convert to W/(ft·°C)
        k = k_si * 0.3048

        return k


# Example usage for testing
if __name__ == "__main__":
    # Example from AEP README: 336.4 ACSR 30/7 ORIOLE
    ambient_defaults = {
        'Ta': 25,
        'WindVelocity': 6.56,  # 2 m/s = 6.56 ft/s
        'WindAngleDeg': 90,
        'SunTime': 12,
        'Date': '12 Jun',
        'Emissivity': 0.8,
        'Absorptivity': 0.8,
        'Direction': 'EastWest',
        'Atmosphere': 'Clear',
        'Elevation': 1000,
        'Latitude': 27,
    }

    MOT = 75  # Maximum operating temperature in °C

    # 336.4 ACSR 30/7 ORIOLE conductor properties
    # Resistance from manufacturer in ohms/mile - convert to ohms/ft
    acsr_oriole = {
        'TLo': 25,
        'THi': 50,
        'RLo': 0.2708 / 5280,  # Convert ohms/mile to ohms/ft
        'RHi': 0.2974 / 5280,
        'Diameter': 0.3705,  # inches (radius * 2)
        'Tc': MOT
    }

    # Combine parameters
    cp = ConductorParams(**ambient_defaults, **acsr_oriole)
    conductor = Conductor(cp)

    # Calculate rating
    rating_amps = conductor.steady_state_thermal_rating()

    print(f"Conductor: 336.4 ACSR 30/7 ORIOLE")
    print(f"Ambient Temperature: {cp.Ta}°C")
    print(f"Wind Speed: {cp.WindVelocity} ft/s")
    print(f"Max Operating Temp: {cp.Tc}°C")
    print(f"Thermal Rating: {rating_amps:.0f} Amps")

    # Convert to MVA at different voltages
    for voltage_kv in [69, 138]:
        voltage = voltage_kv * 1000
        rating_mva = (3 ** 0.5) * rating_amps * voltage * 1e-6
        print(f"Rating at {voltage_kv} kV: {rating_mva:.0f} MVA")

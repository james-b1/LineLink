"""
Line Rating Calculation Module
Wraps IEEE-738 calculations and integrates with grid data
"""

import pandas as pd
import sys
import os
from typing import Dict, List, Tuple
from datetime import datetime

# Add ieee738 to path (adjust based on your structure)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from ieee738 import Conductor, ConductorParams


class LineRatingCalculator:
    """Calculate dynamic line ratings using IEEE-738"""
    
    def __init__(self, data_dir: str = './data'):
        """
        Initialize with grid data
        
        Args:
            data_dir: Path to directory containing CSV files
        """
        self.data_dir = data_dir
        
        # Load data
        self.lines = pd.read_csv(os.path.join(data_dir, 'lines.csv'))
        self.flows = pd.read_csv(os.path.join(data_dir, 'line_flows_nominal.csv'))
        self.conductors = pd.read_csv(os.path.join(data_dir, 'conductor_library.csv'))
        self.buses = pd.read_csv(os.path.join(data_dir, 'buses.csv'))
        
        # Merge flow data into lines
        self.lines = self.lines.merge(self.flows, on='name', how='left')
        
        print(f"Loaded {len(self.lines)} lines, {len(self.conductors)} conductor types")
    
    def calculate_line_rating(self, line_name: str, weather_params: Dict) -> Dict:
        """
        Calculate rating for a single line
        
        Args:
            line_name: Name of the line (e.g., 'L0')
            weather_params: IEEE-738 compatible weather dict
        
        Returns:
            dict: {
                'line_name': str,
                'rating_amps': float,
                'rating_mva': float,
                'flow_mva': float,
                'loading_pct': float,
                'voltage_kv': float,
                'conductor': str,
                'status': str ('OK', 'WARNING', 'CRITICAL', 'OVERLOAD')
            }
        """
        # Get line data
        line = self.lines[self.lines['name'] == line_name].iloc[0]
        
        # Get conductor properties
        conductor_name = line['conductor']
        conductor = self.conductors[self.conductors['ConductorName'] == conductor_name].iloc[0]
        
        # Get voltage from bus
        bus_name = line['bus0']
        voltage_kv = self.buses[self.buses['name'] == bus_name]['v_nom'].iloc[0]
        
        # Build conductor parameters for IEEE-738
        conductor_params = {
            'TLo': 25,
            'THi': 50,
            'RLo': conductor['RES_25C'] / 5280,  # Convert ohms/mile to ohms/ft
            'RHi': conductor['RES_50C'] / 5280,
            'Diameter': conductor['CDRAD_in'] * 2,  # Radius to diameter (lowercase 'in' to match CSV)
            'Tc': line['MOT']  # Maximum Operating Temperature
        }
        
        # Combine with weather parameters
        all_params = {**weather_params, **conductor_params}
        
        try:
            # Calculate rating using IEEE-738
            cp = ConductorParams(**all_params)
            con = Conductor(cp)
            rating_amps = con.steady_state_thermal_rating()
            
            # Convert to MVA
            rating_mva = (3 ** 0.5) * rating_amps * (voltage_kv * 1000) * 1e-6
            
            # Get flow and calculate loading
            flow_mva = line['p0_nominal']
            loading_pct = (flow_mva / rating_mva) * 100
            
            # Determine status
            if loading_pct >= 100:
                status = 'OVERLOAD'
            elif loading_pct >= 95:
                status = 'CRITICAL'
            elif loading_pct >= 80:
                status = 'WARNING'
            else:
                status = 'OK'
            
            return {
                'line_name': line_name,
                'branch_name': line.get('branch_name', line_name),
                'rating_amps': rating_amps,
                'rating_mva': rating_mva,
                'flow_mva': flow_mva,
                'loading_pct': loading_pct,
                'voltage_kv': voltage_kv,
                'conductor': conductor_name,
                'status': status,
                'bus0': line['bus0'],
                'bus1': line['bus1']
            }
        
        except Exception as e:
            print(f"Error calculating rating for {line_name}: {e}")
            return {
                'line_name': line_name,
                'error': str(e),
                'status': 'ERROR'
            }
    
    def calculate_all_lines(self, weather_params: Dict) -> pd.DataFrame:
        """
        Calculate ratings for all lines in the system
        
        Args:
            weather_params: IEEE-738 compatible weather dict
        
        Returns:
            DataFrame with all line ratings
        """
        results = []
        
        for line_name in self.lines['name']:
            result = self.calculate_line_rating(line_name, weather_params)
            if 'error' not in result:
                results.append(result)
        
        df = pd.DataFrame(results)
        
        # Sort by loading percentage (highest first)
        df = df.sort_values('loading_pct', ascending=False)
        
        return df
    
    def get_critical_lines(self, weather_params: Dict, threshold: float = 80) -> pd.DataFrame:
        """
        Get lines that exceed a loading threshold
        
        Args:
            weather_params: Weather conditions
            threshold: Loading percentage threshold (default 80%)
        
        Returns:
            DataFrame of critical lines
        """
        all_ratings = self.calculate_all_lines(weather_params)
        critical = all_ratings[all_ratings['loading_pct'] >= threshold]
        
        return critical
    
    def get_system_health(self, weather_params: Dict) -> Dict:
        """
        Calculate overall system health metrics
        
        Args:
            weather_params: Weather conditions
        
        Returns:
            dict: {
                'total_lines': int,
                'overloaded': int,
                'critical': int (>=95%),
                'warning': int (80-95%),
                'normal': int (<80%),
                'avg_loading': float,
                'max_loading': float,
                'most_stressed_line': str
            }
        """
        df = self.calculate_all_lines(weather_params)
        
        overloaded = len(df[df['loading_pct'] >= 100])
        critical = len(df[(df['loading_pct'] >= 95) & (df['loading_pct'] < 100)])
        warning = len(df[(df['loading_pct'] >= 80) & (df['loading_pct'] < 95)])
        normal = len(df[df['loading_pct'] < 80])
        
        max_loaded_line = df.iloc[0]  # Already sorted by loading_pct
        
        return {
            'total_lines': len(df),
            'overloaded': overloaded,
            'critical': critical,
            'warning': warning,
            'normal': normal,
            'avg_loading': df['loading_pct'].mean(),
            'max_loading': df['loading_pct'].max(),
            'most_stressed_line': max_loaded_line['line_name'],
            'most_stressed_loading': max_loaded_line['loading_pct'],
            'timestamp': datetime.now().isoformat()
        }
    
    def find_first_failure_temp(self, start_temp: float = 20, max_temp: float = 50, 
                                wind_speed: float = 6.56) -> Tuple[float, str]:
        """
        Find the temperature at which the first line overloads
        
        Args:
            start_temp: Starting temperature (°C)
            max_temp: Maximum temperature to test (°C)
            wind_speed: Wind speed to hold constant (ft/s)
        
        Returns:
            tuple: (temperature_at_failure, first_failed_line_name)
        """
        from datetime import datetime
        
        for temp in range(int(start_temp), int(max_temp) + 1):
            weather_params = {
                'Ta': float(temp),
                'WindVelocity': wind_speed,
                'WindAngleDeg': 90,
                'SunTime': 12,  # Noon (worst case)
                'Date': '21 Jun',  # Summer solstice (worst case)
                'Emissivity': 0.8,
                'Absorptivity': 0.8,
                'Direction': 'EastWest',
                'Atmosphere': 'Clear',
                'Elevation': 1000,
                'Latitude': 21.3099
            }
            
            df = self.calculate_all_lines(weather_params)
            overloaded = df[df['loading_pct'] >= 100]
            
            if len(overloaded) > 0:
                first_failed = overloaded.iloc[0]
                return temp, first_failed['line_name']
        
        return max_temp, "None (no failures)"


# Example usage
if __name__ == "__main__":
    # Initialize calculator
    calc = LineRatingCalculator(data_dir='../data')
    
    # Example weather conditions
    weather_params = {
        'Ta': 35,  # 35°C
        'WindVelocity': 6.56,  # 2 m/s
        'WindAngleDeg': 90,
        'SunTime': 14,  # 2 PM
        'Date': '15 Jun',
        'Emissivity': 0.8,
        'Absorptivity': 0.8,
        'Direction': 'EastWest',
        'Atmosphere': 'Clear',
        'Elevation': 1000,
        'Latitude': 21.3099
    }
    
    # Calculate all lines
    print("Calculating ratings for all lines...")
    results = calc.calculate_all_lines(weather_params)
    
    print("\nTop 10 Most Loaded Lines:")
    print(results[['line_name', 'branch_name', 'loading_pct', 'status']].head(10))
    
    # System health
    print("\nSystem Health:")
    health = calc.get_system_health(weather_params)
    for key, value in health.items():
        print(f"  {key}: {value}")
    
    # Find first failure
    print("\nFinding first failure temperature...")
    fail_temp, fail_line = calc.find_first_failure_temp()
    print(f"  First line overloads at {fail_temp}°C: {fail_line}")
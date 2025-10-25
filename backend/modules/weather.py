"""
Weather API Integration Module
Fetches current and forecast weather data from OpenWeatherMap
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List
import os
from dotenv import load_dotenv

load_dotenv()

class WeatherService:
    """Handle all weather API interactions"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENWEATHER_API_KEY')
        self.base_url = "http://api.openweathermap.org/data/2.5"
        self.latitude = float(os.getenv('GRID_LATITUDE', 21.3099))
        self.longitude = float(os.getenv('GRID_LONGITUDE', -157.8581))
        
        if not self.api_key:
            raise ValueError("OPENWEATHER_API_KEY not found in environment variables")
    
    def get_current_weather(self) -> Dict:
        """
        Get current weather conditions
        
        Returns:
            dict: {
                'temperature': float (°C),
                'wind_speed': float (ft/s),
                'wind_direction': float (degrees),
                'timestamp': datetime,
                'description': str
            }
        """
        url = f"{self.base_url}/weather"
        params = {
            'lat': self.latitude,
            'lon': self.longitude,
            'appid': self.api_key,
            'units': 'metric'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Convert wind speed from m/s to ft/s
            wind_speed_ms = data['wind'].get('speed', 0)
            wind_speed_fts = wind_speed_ms * 3.28084
            
            return {
                'temperature': data['main']['temp'],
                'wind_speed': wind_speed_fts,
                'wind_direction': data['wind'].get('deg', 0),
                'timestamp': datetime.fromtimestamp(data['dt']),
                'description': data['weather'][0]['description']
            }
        
        except requests.exceptions.RequestException as e:
            print(f"Error fetching current weather: {e}")
            return self._get_default_weather()
    
    def get_hourly_forecast(self, hours: int = 24) -> List[Dict]:
        """
        Get hourly weather forecast
        
        Args:
            hours: Number of hours to forecast (max 48)
        
        Returns:
            list of dict: [{
                'temperature': float (°C),
                'wind_speed': float (ft/s),
                'wind_direction': float (degrees),
                'timestamp': datetime,
                'hour': int
            }, ...]
        """
        # Note: Free tier only has 5-day/3-hour forecast
        # For hackathon, we'll use the 3-hour forecast and interpolate
        
        url = f"{self.base_url}/forecast"
        params = {
            'lat': self.latitude,
            'lon': self.longitude,
            'appid': self.api_key,
            'units': 'metric'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            forecast = []
            for item in data['list'][:hours//3 + 1]:  # Get enough 3-hour blocks
                wind_speed_ms = item['wind'].get('speed', 0)
                wind_speed_fts = wind_speed_ms * 3.28084
                
                timestamp = datetime.fromtimestamp(item['dt'])
                
                forecast.append({
                    'temperature': item['main']['temp'],
                    'wind_speed': wind_speed_fts,
                    'wind_direction': item['wind'].get('deg', 0),
                    'timestamp': timestamp,
                    'hour': timestamp.hour
                })
            
            return forecast[:hours//3]  # Return requested number of periods
        
        except requests.exceptions.RequestException as e:
            print(f"Error fetching forecast: {e}")
            return self._get_default_forecast(hours)
    
    def format_for_ieee738(self, weather_data: Dict) -> Dict:
        """
        Convert weather data to IEEE-738 compatible format
        
        Args:
            weather_data: Output from get_current_weather()
        
        Returns:
            dict: Parameters ready for IEEE-738 calculation
        """
        timestamp = weather_data['timestamp']
        
        return {
            'Ta': weather_data['temperature'],
            'WindVelocity': weather_data['wind_speed'],
            'WindAngleDeg': 90,  # Simplified: assume perpendicular wind
            'SunTime': timestamp.hour,
            'Date': timestamp.strftime("%d %b"),
            # Constants
            'Emissivity': 0.8,
            'Absorptivity': 0.8,
            'Direction': 'EastWest',
            'Atmosphere': 'Clear',
            'Elevation': 1000,
            'Latitude': self.latitude
        }
    
    def _get_default_weather(self) -> Dict:
        """Return default weather when API fails"""
        return {
            'temperature': 25.0,
            'wind_speed': 6.56,  # 2 m/s
            'wind_direction': 180,
            'timestamp': datetime.now(),
            'description': 'default conditions (API unavailable)'
        }
    
    def _get_default_forecast(self, hours: int) -> List[Dict]:
        """Return default forecast when API fails"""
        forecast = []
        base_time = datetime.now()
        
        for i in range(hours//3):
            timestamp = base_time + timedelta(hours=i*3)
            forecast.append({
                'temperature': 25.0 + (i * 0.5),  # Slight temperature rise
                'wind_speed': 6.56,
                'wind_direction': 180,
                'timestamp': timestamp,
                'hour': timestamp.hour
            })
        
        return forecast


# Example usage
if __name__ == "__main__":
    weather = WeatherService()
    
    # Test current weather
    print("Current Weather:")
    current = weather.get_current_weather()
    print(f"  Temperature: {current['temperature']:.1f}°C")
    print(f"  Wind Speed: {current['wind_speed']:.1f} ft/s")
    print(f"  Conditions: {current['description']}")
    
    # Test forecast
    print("\n24-Hour Forecast:")
    forecast = weather.get_hourly_forecast(24)
    for f in forecast[:5]:  # Show first 5
        print(f"  {f['timestamp'].strftime('%I:%M %p')}: {f['temperature']:.1f}°C, {f['wind_speed']:.1f} ft/s")
    
    # Test IEEE-738 format
    print("\nIEEE-738 Format:")
    ieee_params = weather.format_for_ieee738(current)
    for key, value in ieee_params.items():
        print(f"  {key}: {value}")
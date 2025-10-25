"""
GridGuard Flask Application
Main backend server with API endpoints
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta
import pandas as pd
import os
from dotenv import load_dotenv

# Import our modules
from modules.weather import WeatherService
from modules.calculations import LineRatingCalculator
from modules.alerts import AlertManager
from modules.notifications import NotificationService

load_dotenv()

# Initialize database
from database.db import init_db, check_database_health

# Initialize Flask app
app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)  # Enable CORS for frontend

# Initialize database on startup
init_db()

# Initialize services
weather_service = WeatherService()
calculator = LineRatingCalculator(data_dir='./data')
alert_manager = AlertManager()
notifier = NotificationService()

# Cache for forecast data (refresh every 30 minutes)
forecast_cache = {
    'data': None,
    'timestamp': None,
    'ttl': timedelta(minutes=30)
}


@app.route('/')
def index():
    """Serve the main dashboard"""
    return send_from_directory('../frontend', 'index.html')


@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    db_health = check_database_health()

    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'weather': weather_service.api_key is not None,
            'calculations': len(calculator.lines) > 0,
            'notifications': notifier.twilio_enabled or notifier.sendgrid_enabled,
            'database': db_health['healthy']
        },
        'database': {
            'healthy': db_health['healthy'],
            'tables': db_health.get('tables', []) if db_health['healthy'] else []
        }
    })


@app.route('/api/current-conditions')
def get_current_conditions():
    """Get current weather and line ratings"""
    try:
        # Fetch current weather
        weather = weather_service.get_current_weather()
        weather_params = weather_service.format_for_ieee738(weather)
        
        # Calculate all line ratings
        line_ratings = calculator.calculate_all_lines(weather_params)
        
        # Get system health
        system_health = calculator.get_system_health(weather_params)
        
        # Convert DataFrame to dict for JSON
        lines_data = line_ratings.to_dict('records')
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'weather': {
                'temperature': weather['temperature'],
                'wind_speed': weather['wind_speed'],
                'description': weather['description']
            },
            'system_health': system_health,
            'lines': lines_data,
            'critical_lines': [
                line for line in lines_data 
                if line['loading_pct'] >= alert_manager.critical_threshold
            ]
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/forecast')
def get_forecast():
    """Get 24-hour forecast with line rating predictions"""
    try:
        # Check cache
        if (forecast_cache['data'] and forecast_cache['timestamp'] and 
            datetime.now() - forecast_cache['timestamp'] < forecast_cache['ttl']):
            return jsonify(forecast_cache['data'])
        
        # Fetch forecast
        forecast_weather = weather_service.get_hourly_forecast(hours=24)
        
        forecast_data = []
        for weather in forecast_weather:
            # Convert to IEEE-738 format
            weather_params = weather_service.format_for_ieee738(weather)
            
            # Calculate ratings
            line_ratings = calculator.calculate_all_lines(weather_params)
            
            # Get system health
            health = calculator.get_system_health(weather_params)
            
            forecast_data.append({
                'timestamp': weather['timestamp'].isoformat(),
                'hour': weather['hour'],
                'temperature': weather['temperature'],
                'wind_speed': weather['wind_speed'],
                'system_health': health,
                'lines': line_ratings.to_dict('records')
            })
        
        # Analyze for alerts
        forecast_for_alerts = [
            {
                'timestamp': datetime.fromisoformat(f['timestamp']),
                'hour': f['hour'],
                'lines': pd.DataFrame(f['lines'])
            }
            for f in forecast_data
        ]
        
        alert_analysis = alert_manager.analyze_forecast(forecast_for_alerts)
        
        response = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'forecast': forecast_data,
            'alerts': {
                'critical': alert_analysis['critical_alerts'],
                'warning': alert_analysis['warning_alerts'],
                'summary': alert_analysis['summary'],
                'peak_stress_time': alert_analysis['peak_stress_time'].isoformat() if alert_analysis['peak_stress_time'] else None
            }
        }
        
        # Update cache
        forecast_cache['data'] = response
        forecast_cache['timestamp'] = datetime.now()
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/line/<line_name>')
def get_line_details(line_name):
    """Get detailed information for a specific line"""
    try:
        # Get current conditions
        weather = weather_service.get_current_weather()
        weather_params = weather_service.format_for_ieee738(weather)
        
        # Calculate rating for this line
        line_data = calculator.calculate_line_rating(line_name, weather_params)
        
        if 'error' in line_data:
            return jsonify({
                'success': False,
                'error': f"Line {line_name} not found"
            }), 404
        
        # Get forecast for this line
        forecast_weather = weather_service.get_hourly_forecast(hours=24)
        line_forecast = []
        
        for weather in forecast_weather:
            weather_params = weather_service.format_for_ieee738(weather)
            rating = calculator.calculate_line_rating(line_name, weather_params)
            
            line_forecast.append({
                'timestamp': weather['timestamp'].isoformat(),
                'temperature': weather['temperature'],
                'loading_pct': rating['loading_pct'],
                'rating_mva': rating['rating_mva']
            })
        
        return jsonify({
            'success': True,
            'line': line_data,
            'forecast': line_forecast
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/send-alerts', methods=['POST'])
def send_alerts():
    """Manually trigger alert sending (for testing or manual dispatch)"""
    try:
        # Get forecast and alerts
        forecast_weather = weather_service.get_hourly_forecast(hours=24)
        
        forecast_data = []
        for weather in forecast_weather:
            weather_params = weather_service.format_for_ieee738(weather)
            line_ratings = calculator.calculate_all_lines(weather_params)
            
            forecast_data.append({
                'timestamp': weather['timestamp'],
                'hour': weather['hour'],
                'lines': line_ratings
            })
        
        # Analyze alerts
        alert_analysis = alert_manager.analyze_forecast(forecast_data)
        
        # Combine all alerts
        all_alerts = alert_analysis['critical_alerts'] + alert_analysis['warning_alerts']
        
        if not all_alerts:
            return jsonify({
                'success': True,
                'message': 'No alerts to send',
                'sent': 0
            })
        
        # Format messages
        sms_message = alert_manager.format_alert_message(all_alerts, 'sms')
        email_subject = f"GridGuard Alert: {len(all_alerts)} Line(s) Approaching Limits"
        email_html = alert_manager.format_alert_message(all_alerts, 'email')
        
        # Send notifications
        result = notifier.send_alert(sms_message, email_subject, email_html)
        
        # Mark alerts as sent
        for alert in all_alerts:
            alert_manager.mark_alert_sent(alert['line_name'])
        
        return jsonify({
            'success': True,
            'message': f'Alerts sent successfully',
            'alert_count': len(all_alerts),
            'sms_sent': result['sms']['sent'],
            'email_sent': result['email']['sent'],
            'details': result
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/scenario', methods=['POST'])
def run_scenario():
    """Run custom scenario with user-defined weather conditions"""
    try:
        data = request.json
        
        # Build custom weather parameters
        weather_params = {
            'Ta': data.get('temperature', 25),
            'WindVelocity': data.get('wind_speed', 6.56),
            'WindAngleDeg': 90,
            'SunTime': data.get('hour', 12),
            'Date': data.get('date', datetime.now().strftime("%d %b")),
            'Emissivity': 0.8,
            'Absorptivity': 0.8,
            'Direction': 'EastWest',
            'Atmosphere': 'Clear',
            'Elevation': 1000,
            'Latitude': 21.3099
        }
        
        # Calculate ratings
        line_ratings = calculator.calculate_all_lines(weather_params)
        system_health = calculator.get_system_health(weather_params)
        
        return jsonify({
            'success': True,
            'scenario': data,
            'system_health': system_health,
            'lines': line_ratings.to_dict('records')
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/geojson/lines')
def get_lines_geojson():
    """Get line GIS data with current loading status"""
    try:
        import json
        
        # Load GeoJSON
        with open('./data/oneline_lines.geojson', 'r') as f:
            geojson_data = json.load(f)
        
        # Get current line ratings
        weather = weather_service.get_current_weather()
        weather_params = weather_service.format_for_ieee738(weather)
        line_ratings = calculator.calculate_all_lines(weather_params)
        
        # Create lookup dict
        ratings_dict = {row['line_name']: row for _, row in line_ratings.iterrows()}
        
        # Add loading data to GeoJSON properties
        for feature in geojson_data['features']:
            line_name = feature['properties'].get('Name')
            if line_name in ratings_dict:
                rating_data = ratings_dict[line_name]
                feature['properties']['loading_pct'] = rating_data['loading_pct']
                feature['properties']['status'] = rating_data['status']
                feature['properties']['rating_mva'] = rating_data['rating_mva']
                feature['properties']['flow_mva'] = rating_data['flow_mva']
        
        return jsonify(geojson_data)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/test-notifications', methods=['POST'])
def test_notifications():
    """Test notification system"""
    try:
        result = notifier.test_notifications()
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    print("\n" + "="*60)
    print("LineLink - Transmission Line Stress Predictor")
    print("="*60)

    # Check database
    db_health = check_database_health()
    print(f"\nDatabase: {'✓ Connected' if db_health['healthy'] else '✗ Error'}")
    if db_health['healthy']:
        print(f"  Tables: {', '.join(db_health['tables'])}")

    print(f"\nLoaded {len(calculator.lines)} transmission lines")
    print(f"Weather service: {'✓ Active' if weather_service.api_key else '✗ Not configured'}")
    print(f"SMS alerts: {'✓ Enabled' if notifier.twilio_enabled else '⚠ Disabled'}")
    print(f"Email alerts: {'✓ Enabled' if notifier.sendgrid_enabled else '⚠ Disabled'}")
    print("\nStarting server...")
    print("Dashboard: http://localhost:5001")
    print("API Docs: http://localhost:5001/api/health")
    print("\nPress Ctrl+C to stop\n")

    app.run(debug=True, host='0.0.0.0', port=5001)
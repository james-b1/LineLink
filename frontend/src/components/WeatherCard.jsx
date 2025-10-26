import PropTypes from "prop-types";
import { Thermometer, Wind, CloudRain } from "lucide-react";
import MapView from "./MapView";
import "./WeatherCard.css";

const WeatherCard = ({ weather }) => {
  if (!weather) {
    return (
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Current Weather</h3>
        </div>
        <div className="card-body">
          <p className="text-secondary">No weather data available</p>
        </div>
      </div>
    );
  }

  // Convert wind speed from ft/s to m/s and mph for display
  const windSpeedMs = (weather.wind_speed / 3.28084).toFixed(1);
  const windSpeedMph = (weather.wind_speed * 0.681818).toFixed(1);

  return (
    <div className="card weather-card">
      <div className="card-header">
        <h3 className="card-title">Current Status</h3>
      </div>
      <div className="card-body">
        <div className="weather-grid">
          {/* Temperature */}
          <div className="weather-metric">
            <div className="metric-icon temperature-icon">
              <Thermometer size={24} />
            </div>
            <div className="metric-content">
              <div className="metric-label">Temperature</div>
              <div className="metric-value temperature-value">
                {weather.temperature.toFixed(1)}°C
              </div>
              <div className="metric-secondary">
                {((weather.temperature * 9) / 5 + 32).toFixed(1)}°F
              </div>
            </div>
          </div>

          {/* Wind Speed */}
          <div className="weather-metric">
            <div className="metric-icon wind-icon">
              <Wind size={24} />
            </div>
            <div className="metric-content">
              <div className="metric-label">Wind Speed</div>
              <div className="metric-value wind-value">{windSpeedMs} m/s</div>
              <div className="metric-secondary">
                {windSpeedMph} mph | {weather.wind_speed.toFixed(1)} ft/s
              </div>
            </div>
          </div>

          {/* Conditions */}
          <div className="weather-metric weather-conditions">
            <div className="metric-icon conditions-icon">
              <CloudRain size={24} />
            </div>
            <div className="metric-content">
              <div className="metric-label">Conditions</div>
              <div className="metric-value conditions-value">
                {weather.description.charAt(0).toUpperCase() +
                  weather.description.slice(1)}
              </div>
            </div>
          </div>
        </div>

        {/* Weather Impact Indicator (now inline to save vertical space) */}
        <div className="weather-impact">
          <div className="impact-row">
            <div className="impact-label">Impact on Line Capacity:</div>
            <div className="impact-indicator-inline">
              {weather.temperature > 35 && (
                <span className="impact-warning">
                  High temperature reduces capacity
                </span>
              )}
              {weather.wind_speed < 4.92 && ( // < 1.5 m/s
                <span className="impact-warning">Low wind reduces cooling</span>
              )}
              {weather.temperature <= 35 && weather.wind_speed >= 4.92 && (
                <span className="impact-ok">Favorable conditions</span>
              )}
            </div>
          </div>
        </div>

        {/* Transmission Network Map */}
        <div className="weather-map-section">
          <div className="map-section-header">
            <h4 className="map-section-title">Transmission Network Status</h4>
          </div>
          <MapView />
        </div>
      </div>
    </div>
  );
};

WeatherCard.propTypes = {
  weather: PropTypes.shape({
    temperature: PropTypes.number.isRequired,
    wind_speed: PropTypes.number.isRequired,
    description: PropTypes.string.isRequired,
  }),
};

export default WeatherCard;

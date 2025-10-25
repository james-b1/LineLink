import styles from "./WeatherCard.module.css";

const WeatherCard = ({ weather }) => {
  if (!weather) return null;

  return (
    <div className={styles.card}>
      <h2>Weather</h2>
      <p>
        <strong>Temperature:</strong> {weather.temperature}°C
      </p>
      <p>
        <strong>Wind Speed:</strong> {weather.wind_speed} m/s
      </p>
      <p>
        <strong>Description:</strong> {weather.description}
      </p>
    </div>
  );
};

export default WeatherCard;

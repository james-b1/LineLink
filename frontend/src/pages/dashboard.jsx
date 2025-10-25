import { useEffect, useState, useCallback } from 'react';
import { AlertCircle } from 'lucide-react';
import api from '../api/api.js';
import Header from '../components/layout/Header';
import WeatherCard from '../components/WeatherCard';
import SystemHealthChart from '../components/charts/SystemHealthChart';
import ForecastChart from '../components/charts/ForecastChart';
import LineTable from '../components/LineTable';
import './Dashboard.css';

const Dashboard = () => {
  const [currentData, setCurrentData] = useState(null);
  const [forecastData, setForecastData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);

  // Fetch current conditions
  const fetchCurrentConditions = useCallback(async () => {
    try {
      const response = await api.get('/current-conditions');
      setCurrentData(response.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching current conditions:', err);
      setError('Failed to fetch current conditions');
    }
  }, []);

  // Fetch forecast data
  const fetchForecast = useCallback(async () => {
    try {
      const response = await api.get('/forecast');
      setForecastData(response.data);
    } catch (err) {
      console.error('Error fetching forecast:', err);
      // Don't set error here since current conditions is more critical
    }
  }, []);

  // Fetch all data
  const fetchAllData = useCallback(async (isRefresh = false) => {
    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    try {
      await Promise.all([
        fetchCurrentConditions(),
        fetchForecast()
      ]);
      setLastUpdated(new Date());
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [fetchCurrentConditions, fetchForecast]);

  // Initial data fetch
  useEffect(() => {
    fetchAllData();
  }, [fetchAllData]);

  // Auto-refresh every 5 minutes
  useEffect(() => {
    const interval = setInterval(() => {
      fetchAllData(true);
    }, 5 * 60 * 1000); // 5 minutes

    return () => clearInterval(interval);
  }, [fetchAllData]);

  // Manual refresh handler
  const handleRefresh = () => {
    fetchAllData(true);
  };

  // Get critical lines (loading >= 95%)
  const getCriticalLines = () => {
    if (!currentData?.lines) return [];
    return currentData.lines.filter(line => line.loading_pct >= 95);
  };

  const criticalLines = getCriticalLines();

  // Loading state
  if (loading && !currentData) {
    return (
      <div className="app">
        <Header
          onRefresh={handleRefresh}
          refreshing={false}
          lastUpdated={null}
          systemStatus={null}
        />
        <main className="dashboard-container">
          <div className="loading-container">
            <div className="spinner spinner-lg"></div>
            <p className="text-secondary">Loading dashboard data...</p>
          </div>
        </main>
      </div>
    );
  }

  // Error state
  if (error && !currentData) {
    return (
      <div className="app">
        <Header
          onRefresh={handleRefresh}
          refreshing={refreshing}
          lastUpdated={null}
          systemStatus={{ healthy: false }}
        />
        <main className="dashboard-container">
          <div className="error-container">
            <AlertCircle size={48} className="error-icon" />
            <h2>Failed to Load Data</h2>
            <p className="text-secondary">{error}</p>
            <button onClick={handleRefresh} className="btn btn-primary">
              Retry
            </button>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="app">
      <Header
        onRefresh={handleRefresh}
        refreshing={refreshing}
        lastUpdated={lastUpdated}
        systemStatus={currentData?.system_health}
      />

      <main className="dashboard-container">
        {/* Critical Lines Alert */}
        {criticalLines.length > 0 && (
          <div className="card critical-alert">
            <div className="card-header">
              <h3 className="card-title">
                <AlertCircle size={20} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
                Critical Lines Alert
              </h3>
              <span className="alert-count">{criticalLines.length}</span>
            </div>
            <div className="card-body">
              <ul className="critical-list">
                {criticalLines.map((line, index) => (
                  <li key={line.line_name || index}>
                    <span className="line-name">{line.line_name}</span>
                    <span className="loading-value">
                      {line.loading_pct?.toFixed(1)}% Loading
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Main Dashboard Grid */}
        <div className="dashboard-grid">
          {/* Weather Card */}
          <WeatherCard weather={currentData?.weather} />

          {/* System Health Chart */}
          <SystemHealthChart
            healthData={currentData?.system_health}
            lines={currentData?.lines}
          />

          {/* Forecast Chart */}
          {forecastData && (
            <ForecastChart
              forecastData={forecastData.forecast}
              weather={currentData?.weather}
            />
          )}

          {/* Line Table */}
          <LineTable lines={currentData?.lines} />
        </div>

        {/* Floating Refresh Indicator */}
        {refreshing && (
          <div className="refresh-indicator">
            <div className="spinner"></div>
            <span>Updating data...</span>
          </div>
        )}
      </main>
    </div>
  );
};

export default Dashboard;

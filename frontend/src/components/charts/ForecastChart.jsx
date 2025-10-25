import { useMemo } from 'react';
import PropTypes from 'prop-types';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';
import { format } from 'date-fns';
import './ForecastChart.css';

const ForecastChart = ({ forecastData }) => {
  // Transform data for the chart
  const chartData = useMemo(() => {
    if (!forecastData || !Array.isArray(forecastData)) return [];

    return forecastData.map(item => ({
      time: format(new Date(item.timestamp), 'HH:mm'),
      fullTime: format(new Date(item.timestamp), 'MMM dd, HH:mm'),
      temperature: item.temperature,
      maxLoading: item.system_health?.max_loading || 0,
      avgLoading: item.system_health?.avg_loading || 0,
      criticalCount: (item.system_health?.critical || 0) + (item.system_health?.overloaded || 0),
      warningCount: item.system_health?.warning || 0
    }));
  }, [forecastData]);

  // Custom tooltip
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="custom-tooltip">
          <p className="tooltip-time">{payload[0].payload.fullTime}</p>
          {payload.map((entry, index) => (
            <p key={index} className="tooltip-line" style={{ color: entry.color }}>
              <span className="tooltip-label">{entry.name}:</span>
              <span className="tooltip-value">
                {entry.name === 'Temperature'
                  ? `${entry.value.toFixed(1)}°C`
                  : entry.name.includes('Count')
                  ? `${entry.value} lines`
                  : `${entry.value.toFixed(1)}%`
                }
              </span>
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  if (!chartData || chartData.length === 0) {
    return (
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">24-Hour Forecast</h3>
        </div>
        <div className="card-body">
          <p className="text-secondary">No forecast data available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="card forecast-chart-card">
      <div className="card-header">
        <h3 className="card-title">24-Hour Forecast</h3>
        <div className="chart-legend-custom">
          <span className="legend-item">
            <span className="legend-dot" style={{ backgroundColor: '#F59E0B' }}></span>
            Temperature
          </span>
          <span className="legend-item">
            <span className="legend-dot" style={{ backgroundColor: '#DC2626' }}></span>
            Max Loading
          </span>
          <span className="legend-item">
            <span className="legend-dot" style={{ backgroundColor: '#6B7280' }}></span>
            Avg Loading
          </span>
        </div>
      </div>
      <div className="card-body">
        <ResponsiveContainer width="100%" height={400}>
          <LineChart
            data={chartData}
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-light)" />
            <XAxis
              dataKey="time"
              stroke="var(--text-secondary)"
              style={{ fontSize: '12px' }}
            />
            <YAxis
              yAxisId="left"
              stroke="var(--text-secondary)"
              style={{ fontSize: '12px' }}
              label={{ value: 'Loading (%)', angle: -90, position: 'insideLeft', style: { fill: 'var(--text-secondary)' } }}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              stroke="var(--text-secondary)"
              style={{ fontSize: '12px' }}
              label={{ value: 'Temperature (°C)', angle: 90, position: 'insideRight', style: { fill: 'var(--text-secondary)' } }}
            />
            <Tooltip content={<CustomTooltip />} />

            {/* Critical threshold line */}
            <ReferenceLine
              yAxisId="left"
              y={95}
              stroke="var(--status-critical)"
              strokeDasharray="3 3"
              label={{ value: 'Critical (95%)', position: 'right', fill: 'var(--status-critical)', fontSize: 11 }}
            />

            {/* Warning threshold line */}
            <ReferenceLine
              yAxisId="left"
              y={80}
              stroke="var(--status-warning)"
              strokeDasharray="3 3"
              label={{ value: 'Warning (80%)', position: 'right', fill: 'var(--status-warning)', fontSize: 11 }}
            />

            {/* Lines */}
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="temperature"
              stroke="#F59E0B"
              strokeWidth={2}
              dot={false}
              name="Temperature"
            />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="maxLoading"
              stroke="#DC2626"
              strokeWidth={3}
              dot={false}
              name="Max Loading"
            />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="avgLoading"
              stroke="#6B7280"
              strokeWidth={2}
              dot={false}
              name="Avg Loading"
            />
          </LineChart>
        </ResponsiveContainer>

        {/* Summary Stats */}
        <div className="forecast-summary">
          <div className="summary-stat">
            <span className="stat-label">Peak Loading:</span>
            <span className="stat-value loading-critical">
              {Math.max(...chartData.map(d => d.maxLoading)).toFixed(1)}%
            </span>
          </div>
          <div className="summary-stat">
            <span className="stat-label">Avg Temperature:</span>
            <span className="stat-value">
              {(chartData.reduce((sum, d) => sum + d.temperature, 0) / chartData.length).toFixed(1)}°C
            </span>
          </div>
          <div className="summary-stat">
            <span className="stat-label">Critical Periods:</span>
            <span className="stat-value loading-critical">
              {chartData.filter(d => d.criticalCount > 0).length} hours
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

ForecastChart.propTypes = {
  forecastData: PropTypes.arrayOf(
    PropTypes.shape({
      timestamp: PropTypes.string.isRequired,
      temperature: PropTypes.number.isRequired,
      system_health: PropTypes.shape({
        max_loading: PropTypes.number,
        avg_loading: PropTypes.number,
        critical: PropTypes.number,
        warning: PropTypes.number,
        overloaded: PropTypes.number
      })
    })
  )
};

export default ForecastChart;

import PropTypes from 'prop-types';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import './SystemHealthChart.css';

const SystemHealthChart = ({ healthData }) => {
  if (!healthData) {
    return (
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">System Health</h3>
        </div>
        <div className="card-body">
          <p className="text-secondary">No health data available</p>
        </div>
      </div>
    );
  }

  // Prepare data for the pie chart
  const data = [
    {
      name: 'Normal',
      value: healthData.normal || 0,
      color: 'var(--status-ok)',
      description: '< 80% loading'
    },
    {
      name: 'Warning',
      value: healthData.warning || 0,
      color: 'var(--status-warning)',
      description: '80-95% loading'
    },
    {
      name: 'Critical',
      value: healthData.critical || 0,
      color: 'var(--status-critical)',
      description: '95-100% loading'
    },
    {
      name: 'Overload',
      value: healthData.overloaded || 0,
      color: 'var(--status-overload)',
      description: '> 100% loading'
    }
  ].filter(item => item.value > 0); // Only show segments with values

  const COLORS = data.map(d => d.color);

  // Custom label renderer
  const renderLabel = (entry) => {
    const percent = ((entry.value / healthData.total_lines) * 100).toFixed(0);
    return `${entry.name}: ${percent}%`;
  };

  // Custom tooltip
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="custom-tooltip">
          <p className="tooltip-title" style={{ color: data.color }}>
            {data.name}
          </p>
          <p className="tooltip-value">
            {data.value} lines ({((data.value / healthData.total_lines) * 100).toFixed(1)}%)
          </p>
          <p className="tooltip-description">{data.description}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="card health-chart-card">
      <div className="card-header">
        <h3 className="card-title">System Health Overview</h3>
        <span className="total-lines">{healthData.total_lines} Total Lines</span>
      </div>
      <div className="card-body">
        <div className="health-chart-container">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={2}
                dataKey="value"
                label={renderLabel}
                labelLine={false}
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index]} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>

          {/* Center display of key metric */}
          <div className="chart-center-metric">
            <div className="center-value">{healthData.avg_loading?.toFixed(1) || 0}%</div>
            <div className="center-label">Avg Loading</div>
          </div>
        </div>

        {/* Detailed Stats */}
        <div className="health-stats-grid">
          {data.map((item, index) => (
            <div key={index} className="health-stat">
              <div className="stat-header">
                <span
                  className="stat-indicator"
                  style={{ backgroundColor: item.color }}
                ></span>
                <span className="stat-name">{item.name}</span>
              </div>
              <div className="stat-value-row">
                <span className="stat-count">{item.value}</span>
                <span className="stat-percent">
                  {((item.value / healthData.total_lines) * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* Additional Metrics */}
        <div className="health-metrics">
          <div className="metric-item">
            <span className="metric-label">Peak Loading:</span>
            <span className={`metric-value ${
              healthData.max_loading >= 95
                ? 'loading-critical'
                : healthData.max_loading >= 80
                ? 'loading-warning'
                : 'loading-ok'
            }`}>
              {healthData.max_loading?.toFixed(1) || 0}%
            </span>
          </div>
          <div className="metric-item">
            <span className="metric-label">Most Stressed:</span>
            <span className="metric-value text-secondary">
              {healthData.most_stressed_line || 'N/A'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

SystemHealthChart.propTypes = {
  healthData: PropTypes.shape({
    total_lines: PropTypes.number.isRequired,
    normal: PropTypes.number,
    warning: PropTypes.number,
    critical: PropTypes.number,
    overloaded: PropTypes.number,
    avg_loading: PropTypes.number,
    max_loading: PropTypes.number,
    most_stressed_line: PropTypes.string
  })
};

export default SystemHealthChart;

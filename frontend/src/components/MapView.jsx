import { useState, useEffect } from 'react';
import { MapContainer, TileLayer, GeoJSON, CircleMarker, Popup, Tooltip } from 'react-leaflet';
import PropTypes from 'prop-types';
import api from '../api/api.js';
import 'leaflet/dist/leaflet.css';
import './MapView.css';

const MapView = ({ refreshTrigger }) => {
  const [linesData, setLinesData] = useState(null);
  const [busesData, setBusesData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch map data (refreshes when refreshTrigger changes)
  useEffect(() => {
    const fetchMapData = async () => {
      try {
        setLoading(true);
        const [linesResponse, busesResponse] = await Promise.all([
          api.get('/geojson/lines'),
          api.get('/geojson/buses')
        ]);
        setLinesData(linesResponse.data);
        setBusesData(busesResponse.data);
        setError(null);
      } catch (err) {
        console.error('Error fetching map data:', err);
        setError('Failed to load map data');
      } finally {
        setLoading(false);
      }
    };

    fetchMapData();
  }, [refreshTrigger]); // Re-fetch when refreshTrigger changes

  // Get color based on loading status
  const getLineColor = (loadingPct) => {
    if (!loadingPct && loadingPct !== 0) return '#6B7280'; // Gray if no data
    if (loadingPct >= 100) return '#6B7280'; // Gray for overload
    if (loadingPct >= 95) return '#DC2626';  // Red for critical
    if (loadingPct >= 80) return '#F59E0B';  // Orange for warning
    return '#10B981'; // Green for normal
  };

  // Get bus marker color based on voltage
  const getBusColor = (voltageKv) => {
    return voltageKv === 69 ? '#3B82F6' : '#8B5CF6'; // Blue for 69kV, Purple for others
  };

  // Style function for lines
  const lineStyle = (feature) => {
    const loadingPct = feature.properties.loading_pct;
    return {
      color: getLineColor(loadingPct),
      weight: 3,
      opacity: 0.8
    };
  };

  // Tooltip for lines
  const onEachLine = (feature, layer) => {
    const props = feature.properties;
    const tooltipContent = `
      <div>
        <strong>${props.Name || 'Unknown Line'}</strong><br/>
        Loading: ${props.loading_pct ? props.loading_pct.toFixed(1) : 'N/A'}%<br/>
        Status: ${props.status || 'N/A'}
      </div>
    `;
    layer.bindTooltip(tooltipContent);

    // Detailed popup
    if (props.loading_pct) {
      const popupContent = `
        <div class="map-popup">
          <h4>${props.Name}</h4>
          <table>
            <tr><td>Loading:</td><td><strong>${props.loading_pct.toFixed(1)}%</strong></td></tr>
            <tr><td>Status:</td><td><span class="status-${props.status?.toLowerCase()}">${props.status}</span></td></tr>
            <tr><td>Flow:</td><td>${props.flow_mva ? props.flow_mva.toFixed(1) : 'N/A'} MVA</td></tr>
            <tr><td>Rating:</td><td>${props.rating_mva ? props.rating_mva.toFixed(1) : 'N/A'} MVA</td></tr>
          </table>
        </div>
      `;
      layer.bindPopup(popupContent);
    }
  };

  if (loading) {
    return (
      <div className="map-loading">
        <div className="spinner"></div>
        <p className="text-secondary">Loading map...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="map-error">
        <p className="text-secondary">{error}</p>
      </div>
    );
  }

  return (
    <div className="map-container">
      <MapContainer
        center={[20.9, -157.5]}
        zoom={7}
        style={{ height: '100%', width: '100%' }}
        scrollWheelZoom={false}
      >
        <TileLayer
          attribution='&copy; <a href="https://carto.com/">CartoDB</a>'
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
        />

        {/* Transmission Lines */}
        {linesData && (
          <GeoJSON
            data={linesData}
            style={lineStyle}
            onEachFeature={onEachLine}
          />
        )}

        {/* Bus Markers */}
        {busesData && busesData.features.map((feature, index) => {
          const [lon, lat] = feature.geometry.coordinates;
          const { name, voltage_kv } = feature.properties;

          return (
            <CircleMarker
              key={index}
              center={[lat, lon]}
              radius={5}
              pathOptions={{
                color: getBusColor(voltage_kv),
                fillColor: getBusColor(voltage_kv),
                fillOpacity: 0.8,
                weight: 2
              }}
            >
              <Tooltip>
                <strong>{name}</strong>
              </Tooltip>
              <Popup>
                <div className="bus-popup">
                  <h4>{name}</h4>
                  <p>{voltage_kv} kV</p>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>

      {/* Legend */}
      <div className="map-legend">
        <div className="legend-title">Transmission Lines</div>
        <div className="legend-item">
          <span className="legend-line" style={{ backgroundColor: '#10B981' }}></span>
          <span>Normal (&lt;80%)</span>
        </div>
        <div className="legend-item">
          <span className="legend-line" style={{ backgroundColor: '#F59E0B' }}></span>
          <span>Warning (80-95%)</span>
        </div>
        <div className="legend-item">
          <span className="legend-line" style={{ backgroundColor: '#DC2626' }}></span>
          <span>Critical (95-100%)</span>
        </div>
        <div className="legend-item">
          <span className="legend-line" style={{ backgroundColor: '#6B7280' }}></span>
          <span>Overload (&gt;100%)</span>
        </div>
        <div className="legend-divider"></div>
        <div className="legend-title">Substations</div>
        <div className="legend-item">
          <span className="legend-marker" style={{ backgroundColor: '#3B82F6' }}></span>
          <span>69 kV</span>
        </div>
        <div className="legend-item">
          <span className="legend-marker" style={{ backgroundColor: '#8B5CF6' }}></span>
          <span>Other Voltages</span>
        </div>
      </div>
    </div>
  );
};

MapView.propTypes = {
  refreshTrigger: PropTypes.oneOfType([
    PropTypes.number,
    PropTypes.instanceOf(Date)
  ])
};

export default MapView;

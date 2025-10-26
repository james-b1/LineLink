import { RefreshCw } from "lucide-react";
import PropTypes from "prop-types";
import "./Header.css";
import logo from "../../assets/logo.png";

const Header = ({ onRefresh, refreshing, lastUpdated, systemStatus }) => {
  const formatTime = (date) => {
    if (!date) return "--:--";
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <header className="header">
      <div className="container">
        <div className="header-content">
          {/* Logo/Brand */}
          <div className="header-brand">
            <img src={logo} alt="LineLink Logo" className="header-logo" />
            <h1 className="header-title">LineLink</h1>
          </div>

          {/* Status & Actions */}
          <div className="header-actions">
            {/* System Status */}
            <div className="header-status">
              <div
                className={`status-indicator ${
                  systemStatus?.healthy ? "status-healthy" : "status-error"
                }`}
              >
                <span className="status-dot"></span>
                <span className="status-text">
                  {systemStatus?.healthy ? "Connected" : "Disconnected"}
                </span>
              </div>
              {lastUpdated && (
                <span className="last-updated">
                  Updated {formatTime(lastUpdated)}
                </span>
              )}
            </div>

            {/* Refresh Button */}
            <button
              onClick={onRefresh}
              disabled={refreshing}
              className="btn btn-secondary refresh-btn"
              aria-label="Refresh data"
            >
              <RefreshCw size={18} className={refreshing ? "spinning" : ""} />
              <span className="refresh-text">Refresh</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

Header.propTypes = {
  onRefresh: PropTypes.func.isRequired,
  refreshing: PropTypes.bool,
  lastUpdated: PropTypes.instanceOf(Date),
  systemStatus: PropTypes.shape({
    healthy: PropTypes.bool,
  }),
};

Header.defaultProps = {
  refreshing: false,
  lastUpdated: null,
  systemStatus: { healthy: true },
};

export default Header;

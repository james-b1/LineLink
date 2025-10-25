import React from "react";
import PropTypes from "prop-types";

const SystemHealthCard = ({ health }) => {
  if (!health) return null;

  return (
    <div
      style={{
        border: "1px solid #ccc",
        padding: "1rem",
        marginBottom: "1rem",
      }}
    >
      <h2>System Health</h2>
      <ul>
        {Object.entries(health).map(([key, value]) => (
          <li key={key}>
            <strong>{key}:</strong> {String(value)}
          </li>
        ))}
      </ul>
    </div>
  );
};

SystemHealthCard.propTypes = {
  health: PropTypes.shape({}).isRequired,
};

export default SystemHealthCard;

// src/components/LineTable.jsx
import { useNavigate } from "react-router-dom";

const LineTable = ({ lines }) => {
  const navigate = useNavigate();

  if (!lines || lines.length === 0) return <p>No line data available.</p>;

  const handleRowClick = (lineName) => {
    navigate(`/lines/${lineName}`);
  };

  return (
    <table style={{ borderCollapse: "collapse", width: "100%" }}>
      <thead>
        <tr>
          <th style={{ border: "1px solid #ccc", padding: "0.5rem" }}>
            Line Name
          </th>
          <th style={{ border: "1px solid #ccc", padding: "0.5rem" }}>
            Loading %
          </th>
          <th style={{ border: "1px solid #ccc", padding: "0.5rem" }}>
            Status
          </th>
        </tr>
      </thead>
      <tbody>
        {lines.map((line) => (
          <tr
            key={line.name}
            onClick={() => handleRowClick(line.name)}
            style={{ cursor: "pointer" }}
          >
            <td style={{ border: "1px solid #ccc", padding: "0.5rem" }}>
              {line.name}
            </td>
            <td style={{ border: "1px solid #ccc", padding: "0.5rem" }}>
              {line.loading_pct}
            </td>
            <td style={{ border: "1px solid #ccc", padding: "0.5rem" }}>
              {line.status}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};

export default LineTable;

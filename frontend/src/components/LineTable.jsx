import { useState, useMemo } from 'react';
import { Search, ArrowUp, ArrowDown, ArrowUpDown } from 'lucide-react';
import PropTypes from 'prop-types';
import './LineTable.css';

const LineTable = ({ lines }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortConfig, setSortConfig] = useState({ key: 'loading_pct', direction: 'desc' });
  const [statusFilter, setStatusFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const linesPerPage = 20;

  // Get status badge component
  const StatusBadge = ({ status, loading }) => {
    const getStatusClass = () => {
      if (loading >= 100) return 'status-overload';
      if (loading >= 95) return 'status-critical';
      if (loading >= 80) return 'status-warning';
      return 'status-ok';
    };

    return (
      <span className={`badge ${getStatusClass()}`}>
        {status}
      </span>
    );
  };

  // Sorting function
  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
    setCurrentPage(1); // Reset to first page
  };

  // Get sort icon
  const getSortIcon = (columnKey) => {
    if (sortConfig.key !== columnKey) {
      return <ArrowUpDown size={14} className="sort-icon-inactive" />;
    }
    return sortConfig.direction === 'asc' ? (
      <ArrowUp size={14} className="sort-icon-active" />
    ) : (
      <ArrowDown size={14} className="sort-icon-active" />
    );
  };

  // Filter and sort lines
  const filteredAndSortedLines = useMemo(() => {
    if (!lines || lines.length === 0) return [];

    let processed = [...lines];

    // Apply search filter
    if (searchTerm) {
      processed = processed.filter((line) =>
        (line.line_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
         line.branch_name?.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }

    // Apply status filter
    if (statusFilter !== 'all') {
      processed = processed.filter((line) => {
        if (statusFilter === 'OVERLOAD') return line.loading_pct >= 100;
        if (statusFilter === 'CRITICAL') return line.loading_pct >= 95 && line.loading_pct < 100;
        if (statusFilter === 'WARNING') return line.loading_pct >= 80 && line.loading_pct < 95;
        if (statusFilter === 'OK') return line.loading_pct < 80;
        return true;
      });
    }

    // Apply sorting
    processed.sort((a, b) => {
      let aValue = a[sortConfig.key];
      let bValue = b[sortConfig.key];

      // Handle null/undefined
      if (aValue == null) aValue = '';
      if (bValue == null) bValue = '';

      if (typeof aValue === 'string') {
        return sortConfig.direction === 'asc'
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }

      return sortConfig.direction === 'asc'
        ? aValue - bValue
        : bValue - aValue;
    });

    return processed;
  }, [lines, searchTerm, sortConfig, statusFilter]);

  // Pagination
  const totalPages = Math.ceil(filteredAndSortedLines.length / linesPerPage);
  const startIndex = (currentPage - 1) * linesPerPage;
  const paginatedLines = filteredAndSortedLines.slice(startIndex, startIndex + linesPerPage);

  if (!lines || lines.length === 0) {
    return (
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Transmission Lines</h3>
        </div>
        <div className="card-body">
          <p className="text-secondary">No line data available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="card line-table-card">
      <div className="card-header">
        <h3 className="card-title">Transmission Lines</h3>
        <span className="line-count">{lines.length} lines</span>
      </div>
      <div className="card-body">
        {/* Filters */}
        <div className="table-controls">
          {/* Search */}
          <div className="search-container">
            <Search size={18} className="search-icon" />
            <input
              type="text"
              placeholder="Search by line name..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              className="search-input"
            />
          </div>

          {/* Status Filter */}
          <div className="status-filter">
            {['all', 'OVERLOAD', 'CRITICAL', 'WARNING', 'OK'].map((status) => (
              <button
                key={status}
                onClick={() => {
                  setStatusFilter(status);
                  setCurrentPage(1);
                }}
                className={`filter-btn ${statusFilter === status ? 'filter-btn-active' : ''}`}
              >
                {status === 'all' ? 'All' : status}
              </button>
            ))}
          </div>
        </div>

        {/* Results count */}
        {(searchTerm || statusFilter !== 'all') && (
          <div className="results-info">
            Showing {filteredAndSortedLines.length} of {lines.length} lines
          </div>
        )}

        {/* Table */}
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th onClick={() => handleSort('line_name')} className="sortable-header">
                  <div className="header-content">
                    Line Name
                    {getSortIcon('line_name')}
                  </div>
                </th>
                <th onClick={() => handleSort('branch_name')} className="sortable-header">
                  <div className="header-content">
                    Branch
                    {getSortIcon('branch_name')}
                  </div>
                </th>
                <th onClick={() => handleSort('loading_pct')} className="sortable-header">
                  <div className="header-content">
                    Loading %
                    {getSortIcon('loading_pct')}
                  </div>
                </th>
                <th onClick={() => handleSort('flow_mva')} className="sortable-header">
                  <div className="header-content">
                    Flow (MVA)
                    {getSortIcon('flow_mva')}
                  </div>
                </th>
                <th onClick={() => handleSort('rating_mva')} className="sortable-header">
                  <div className="header-content">
                    Rating (MVA)
                    {getSortIcon('rating_mva')}
                  </div>
                </th>
                <th onClick={() => handleSort('voltage_kv')} className="sortable-header">
                  <div className="header-content">
                    Voltage (kV)
                    {getSortIcon('voltage_kv')}
                  </div>
                </th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {paginatedLines.map((line, index) => (
                <tr key={line.line_name || index}>
                  <td className="line-name-cell">{line.line_name}</td>
                  <td className="branch-name-cell">{line.branch_name}</td>
                  <td>
                    <div className="loading-cell">
                      <span className={`loading-value ${
                        line.loading_pct >= 100 ? 'loading-overload' :
                        line.loading_pct >= 95 ? 'loading-critical' :
                        line.loading_pct >= 80 ? 'loading-warning' : 'loading-ok'
                      }`}>
                        {line.loading_pct?.toFixed(1) || 0}%
                      </span>
                      <div className="loading-bar">
                        <div
                          className={`loading-bar-fill ${
                            line.loading_pct >= 100 ? 'loading-overload' :
                            line.loading_pct >= 95 ? 'loading-critical' :
                            line.loading_pct >= 80 ? 'loading-warning' : 'loading-ok'
                          }`}
                          style={{ width: `${Math.min(line.loading_pct, 100)}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td>{line.flow_mva?.toFixed(1) || 0}</td>
                  <td>{line.rating_mva?.toFixed(1) || 0}</td>
                  <td>{line.voltage_kv?.toFixed(0) || 0}</td>
                  <td>
                    <StatusBadge status={line.status} loading={line.loading_pct} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="pagination">
            <button
              onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
              disabled={currentPage === 1}
              className="btn btn-secondary btn-sm"
            >
              Previous
            </button>
            <span className="pagination-info">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage((prev) => Math.min(totalPages, prev + 1))}
              disabled={currentPage === totalPages}
              className="btn btn-secondary btn-sm"
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

LineTable.propTypes = {
  lines: PropTypes.arrayOf(
    PropTypes.shape({
      line_name: PropTypes.string,
      branch_name: PropTypes.string,
      loading_pct: PropTypes.number,
      flow_mva: PropTypes.number,
      rating_mva: PropTypes.number,
      voltage_kv: PropTypes.number,
      status: PropTypes.string
    })
  )
};

export default LineTable;

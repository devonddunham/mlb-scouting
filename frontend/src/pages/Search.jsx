import { useState } from "react";
import { Link } from "react-router-dom";

function Search() {
  const [searchQuery, setSearchQuery] = useState("");
  const [searchType, setSearchType] = useState("player");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState("");

  const runSearch = (event) => {
    event.preventDefault();
    const trimmed = searchQuery.trim();

    setError("");
    setMessage("");
    setSubmittedQuery(trimmed);

    if (!trimmed) {
      setResults([]);
      return;
    }

    setLoading(true);
    fetch(`/api/search?type=${encodeURIComponent(searchType)}&query=${encodeURIComponent(trimmed)}`)
      .then(async (res) => {
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
        return data;
      })
      .then((data) => {
        setResults(data);
      })
      .catch((err) => {
        setError(err.message);
      })
      .finally(() => {
        setLoading(false);
      });
  };

  const deleteReport = (reportId) => {
    const confirmed = window.confirm("Are you sure you want to delete this report?");
    if (!confirmed) return;

    setError("");
    setMessage("");

    fetch(`/api/reports/${reportId}`, { method: "DELETE" })
      .then(async (res) => {
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
        return data;
      })
      .then(() => {
        setResults((prev) => prev.filter((row) => row.report_id !== reportId));
        setMessage("Report deleted successfully");
      })
      .catch((err) => {
        setError(err.message);
      });
  };

  return (
    <div className="page-container">
      <h1 className="page-title">Search Scouting Reports</h1>

      <form className="search-form" onSubmit={runSearch}>
        <div className="search-panel">
          <input
            className="search-input"
            type="text"
            placeholder="Enter player or scout name..."
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
          />
          <button className="search-button" type="submit" disabled={loading}>
            {loading ? "Searching..." : "Search"}
          </button>
        </div>

        <div className="search-types">
          <label>
            <input
              type="radio"
              name="search-type"
              value="player"
              checked={searchType === "player"}
              onChange={(event) => setSearchType(event.target.value)}
            />
            Player
          </label>
          <label>
            <input
              type="radio"
              name="search-type"
              value="scout"
              checked={searchType === "scout"}
              onChange={(event) => setSearchType(event.target.value)}
            />
            Scout
          </label>
        </div>
      </form>

      {message && <p className="status-success">{message}</p>}
      {error && <p className="status-error">Error: {error}</p>}

      {results.length > 0 && (
        <div className="results-wrap">
          <table className="results-table">
            <thead>
              <tr>
                <th>Player</th>
                <th>Scout</th>
                <th>Year</th>
                <th>Grade</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {results.map((row) => (
                <tr key={row.report_id}>
                  <td>{row.first_name} {row.last_name}</td>
                  <td>{row.scout_name}</td>
                  <td>{row.report_year}</td>
                  <td>{row.overall_grade}</td>
                  <td className="row-actions">
                    <Link className="card-link" to={`/reports/${row.report_id}`}>
                      View / Edit
                    </Link>
                    <button
                      className="danger-button"
                      type="button"
                      onClick={() => deleteReport(row.report_id)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!loading && submittedQuery && !error && results.length === 0 && (
        <p className="page-subtitle">No results found for "{submittedQuery}".</p>
      )}
    </div>
  );
}

export default Search;

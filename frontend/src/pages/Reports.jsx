import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

function Reports() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("/api/reports")
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => {
        setReports(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  return (
    <div className="page-container">
      <h1 className="page-title">Reports</h1>

      {loading && <p>Loading reports...</p>}
      {error && <p>Error: {error}</p>}
      {!loading && !error && reports.length === 0 && <p>No reports found.</p>}

      <div className="card-grid">
        {!loading &&
          !error &&
          reports.map((report) => (
            <div className="baseball-card" key={report.report_id}>
              <h2>{report.first_name} {report.last_name}</h2>
              <p><strong>Scout:</strong> {report.scout_name}</p>
              <p><strong>Grade:</strong> {report.overall_grade}</p>
              <p><strong>Year:</strong> {report.report_date}</p>
              <p><strong>Type:</strong> {report.primary_position === "P" ? "Pitcher" : "Position Player"}</p>
              <Link className="card-link" to={`/reports/${report.report_id}`}>
                View / Edit Stats
              </Link>
            </div>
          ))}
      </div>
    </div>
  );
}

export default Reports;

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

function Reports() {
  const [reports, setReports] = useState([]);
  const [players, setPlayers] = useState([]);
  const [scouts, setScouts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState("");
  const [form, setForm] = useState({
    player_id: "",
    scout_id: "",
    year: new Date().getFullYear(),
  });

  const parseResponse = async (res) => {
    const text = await res.text();
    if (!text) return {};
    try {
      return JSON.parse(text);
    } catch {
      throw new Error(`Server returned non-JSON response (HTTP ${res.status})`);
    }
  };

  useEffect(() => {
    fetch("/api/reports")
      .then(async (res) => {
        const data = await parseResponse(res);
        if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
        return data;
      })
      .then((data) => {
        setReports(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });

    fetch("/api/players")
      .then(async (res) => {
        const data = await parseResponse(res);
        if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
        return data;
      })
      .then(setPlayers)
      .catch(() => {});

    fetch("/api/scouts")
      .then(async (res) => {
        const data = await parseResponse(res);
        if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
        return data;
      })
      .then(setScouts)
      .catch(() => {});
  }, []);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async () => {
    setFormError("");
    if (!form.player_id || !form.scout_id || !form.year) {
      setFormError("Please fill out all fields.");
      return;
    }

    setSubmitting(true);
    try {
      const res = await fetch("/api/reports", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          player_id: parseInt(form.player_id, 10),
          scout_id: parseInt(form.scout_id, 10),
          year: parseInt(form.year, 10),
        }),
      });

      const data = await parseResponse(res);
      if (!res.ok) throw new Error(data.error || "Failed to create report");

      setReports((prev) => [data.report, ...prev]);
      setShowForm(false);
      setForm({ player_id: "", scout_id: "", year: new Date().getFullYear() });
    } catch (err) {
      setFormError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="page-container">
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <h1 className="page-title">Reports</h1>
        <button
          onClick={() => setShowForm(true)}
          style={{
            padding: "10px 20px",
            backgroundColor: "#1a73e8",
            color: "white",
            border: "none",
            borderRadius: "8px",
            cursor: "pointer",
            fontWeight: "bold",
            fontSize: "14px",
          }}
        >
          + Add Report
        </button>
      </div>

      {showForm && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            backgroundColor: "rgba(0,0,0,0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
          }}
        >
          <div
            style={{
              backgroundColor: "white",
              borderRadius: "12px",
              padding: "32px",
              width: "100%",
              maxWidth: "420px",
              boxShadow: "0 8px 32px rgba(0,0,0,0.2)",
            }}
          >
            <h2 style={{ marginTop: 0, marginBottom: "24px" }}>New Report</h2>

            <label
              style={{
                display: "block",
                marginBottom: "6px",
                fontWeight: "bold",
              }}
            >
              Player
            </label>
            <select
              name="player_id"
              value={form.player_id}
              onChange={handleChange}
              style={{
                width: "100%",
                padding: "10px",
                borderRadius: "6px",
                border: "1px solid #ccc",
                marginBottom: "16px",
              }}
            >
              <option value="">Select a player...</option>
              {players.map((p) => (
                <option key={p.player_id} value={p.player_id}>
                  {p.first_name} {p.last_name} ({p.primary_position} - {p.team_id})
                </option>
              ))}
            </select>

            <label
              style={{
                display: "block",
                marginBottom: "6px",
                fontWeight: "bold",
              }}
            >
              Scout
            </label>
            <select
              name="scout_id"
              value={form.scout_id}
              onChange={handleChange}
              style={{
                width: "100%",
                padding: "10px",
                borderRadius: "6px",
                border: "1px solid #ccc",
                marginBottom: "16px",
              }}
            >
              <option value="">Select a scout...</option>
              {scouts.length === 0 && <option disabled>No scouts in database yet</option>}
              {scouts.map((s) => (
                <option key={s.scout_id} value={s.scout_id}>
                  {s.name} ({s.team_name})
                </option>
              ))}
            </select>

            <label
              style={{
                display: "block",
                marginBottom: "6px",
                fontWeight: "bold",
              }}
            >
              Year
            </label>
            <input
              type="number"
              name="year"
              value={form.year}
              onChange={handleChange}
              min="2000"
              max="2035"
              style={{
                width: "100%",
                padding: "10px",
                borderRadius: "6px",
                border: "1px solid #ccc",
                marginBottom: "16px",
                boxSizing: "border-box",
              }}
            />

            {formError && (
              <p style={{ color: "red", marginBottom: "16px", fontSize: "14px" }}>{formError}</p>
            )}

            <div style={{ display: "flex", gap: "12px", justifyContent: "flex-end" }}>
              <button
                onClick={() => {
                  setShowForm(false);
                  setFormError("");
                }}
                style={{
                  padding: "10px 20px",
                  borderRadius: "8px",
                  border: "1px solid #ccc",
                  cursor: "pointer",
                  background: "white",
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleSubmit}
                disabled={submitting}
                style={{
                  padding: "10px 20px",
                  borderRadius: "8px",
                  border: "none",
                  backgroundColor: "#1a73e8",
                  color: "white",
                  cursor: "pointer",
                  fontWeight: "bold",
                }}
              >
                {submitting ? "Creating..." : "Create Report"}
              </button>
            </div>
          </div>
        </div>
      )}

      {loading && <p>Loading reports...</p>}
      {error && <p>Error: {error}</p>}
      {!loading && !error && reports.length === 0 && <p>No reports found. Add one above!</p>}

      <div className="card-grid">
        {!loading &&
          !error &&
          reports.map((report) => (
            <div className="baseball-card" key={report.report_id}>
              <h2>
                {report.first_name} {report.last_name}
              </h2>
              <p>
                <strong>Scout:</strong> {report.scout_name}
              </p>
              <p>
                <strong>Grade:</strong> {report.overall_grade}
              </p>
              <p>
                <strong>Year:</strong> {report.report_date}
              </p>
              <p>
                <strong>Type:</strong> {report.primary_position === "P" ? "Pitcher" : "Position Player"}
              </p>
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

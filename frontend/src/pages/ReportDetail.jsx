import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

const PITCHER_FIELDS = [
  { key: "hard_hit_percentage", label: "Hard Hit Percentage" },
  { key: "out_zone_swing_miss_percentage", label: "Out Zone Miss Percentage" },
  { key: "barrel_percentage", label: "Barrel Percentage" },
  { key: "k_percentage", label: "K Percentage" },
  { key: "bb_percentage", label: "BB Percentage" },
  { key: "whiff_percentage", label: "Whiff Percentage" },
  { key: "gb_percentage", label: "Ground Ball Percentage" },
  { key: "four_seam_velocity", label: "Four-Seam Velocity" },
  { key: "four_seam_spin", label: "Four-Seam Spin" },
];

const POSITION_FIELDS = [
  { key: "exit_velocity", label: "Exit Velocity" },
  { key: "launch_angle", label: "Launch Angle" },
  { key: "xwoba", label: "xwOBA" },
  { key: "xobp", label: "xOBP" },
  { key: "hard_hit_percentage", label: "Hard Hit Percentage" },
  { key: "zone_swing_percentage", label: "Zone Swing Percentage" },
  { key: "zone_swing_miss_percentage", label: "Zone Swing Miss Percentage" },
  { key: "out_zone_swing_percentage", label: "Out Zone Swing Percentage" },
  { key: "out_zone_swing_miss_percentage", label: "Out Zone Swing Miss Percentage" },
];

function ReportDetail() {
  const { reportId } = useParams();
  const navigate = useNavigate();

  const [report, setReport] = useState(null);
  const [formValues, setFormValues] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [editing, setEditing] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");

  useEffect(() => {
    let cancelled = false;

    fetch(`/api/reports/${reportId}`)
      .then(async (res) => {
        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          throw new Error(data.error || `HTTP ${res.status}`);
        }
        return res.json();
      })
      .then((data) => {
        if (cancelled) return;
        setReport(data);
        setFormValues(data.metrics || {});
        setLoading(false);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err.message);
        setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [reportId]);

  const fields = report?.report_type === "pitcher" ? PITCHER_FIELDS : POSITION_FIELDS;

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormValues((prev) => ({ ...prev, [name]: value }));
  };

  const handleSave = (event) => {
    event.preventDefault();
    setSaving(true);
    setError("");
    setStatus("");

    const metricsPayload = {};
    for (const field of fields) {
      metricsPayload[field.key] = formValues[field.key] ?? "";
    }

    fetch(`/api/reports/${reportId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ metrics: metricsPayload }),
    })
      .then(async (res) => {
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
        return data;
      })
      .then((data) => {
        setReport(data.report);
        setFormValues(data.report?.metrics || {});
        setStatus(data.message || "Report updated successfully");
        setEditing(false);
      })
      .catch((err) => {
        setError(err.message);
      })
      .finally(() => {
        setSaving(false);
      });
  };

  const handleDelete = () => {
    const confirmed = window.confirm("Are you sure you want to delete this report?");
    if (!confirmed) return;

    setDeleting(true);
    setError("");
    setStatus("");

    fetch(`/api/reports/${reportId}`, { method: "DELETE" })
      .then(async (res) => {
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
        return data;
      })
      .then(() => {
        navigate("/reports");
      })
      .catch((err) => {
        setError(err.message);
      })
      .finally(() => {
        setDeleting(false);
      });
  };

  if (loading) {
    return (
      <div className="page-container">
        <h1 className="page-title">Report Details</h1>
        <p>Loading report...</p>
      </div>
    );
  }

  if (error && !report) {
    return (
      <div className="page-container">
        <h1 className="page-title">Report Details</h1>
        <p>Error: {error}</p>
        <Link className="card-link" to="/reports">Back to Reports</Link>
      </div>
    );
  }

  return (
    <div className="page-container">
      <h1 className="page-title">Report Details</h1>

      <div className="baseball-card detail-panel">
        <h2>{report.first_name} {report.last_name}</h2>
        <p><strong>Scout:</strong> {report.scout_name}</p>
        <p><strong>Team:</strong> {report.team_name || report.team_id || "N/A"}</p>
        <p><strong>Year:</strong> {report.report_date}</p>
        <p><strong>Grade:</strong> {report.overall_grade}</p>
        <p><strong>Type:</strong> {report.report_type === "pitcher" ? "Pitcher" : "Position Player"}</p>

        <div className="form-actions">
          <Link className="card-link" to="/reports">Back to Reports</Link>
          <button className="search-button" type="button" onClick={() => setEditing((prev) => !prev)}>
            {editing ? "Cancel Edit" : "Edit Metrics"}
          </button>
          <button
            className="danger-button"
            type="button"
            onClick={handleDelete}
            disabled={deleting}
          >
            {deleting ? "Deleting..." : "Delete Report"}
          </button>
        </div>

        {status && <p className="status-success">{status}</p>}
        {error && <p className="status-error">Error: {error}</p>}
      </div>

      <form className="metrics-form" onSubmit={handleSave}>
        <div className="metrics-grid">
          {fields.map((field) => (
            <label className="metric-field" key={field.key}>
              <span>{field.label}</span>
              <input
                type="number"
                step="any"
                name={field.key}
                value={formValues[field.key] ?? ""}
                onChange={handleChange}
                disabled={!editing || saving}
              />
            </label>
          ))}
        </div>

        {editing && (
          <div className="form-actions">
            <button className="search-button" type="submit" disabled={saving}>
              {saving ? "Saving..." : "Save Changes"}
            </button>
          </div>
        )}
      </form>
    </div>
  );
}

export default ReportDetail;

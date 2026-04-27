import { useEffect, useState } from "react";

function Scouts() {
  const [scouts, setScouts] = useState([]);
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState("");
  const [form, setForm] = useState({ name: "", team_id: "" });

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
    fetch("/api/scouts")
      .then(async (res) => {
        const data = await parseResponse(res);
        if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
        return data;
      })
      .then((data) => { setScouts(data); setLoading(false); })
      .catch((err) => { setError(err.message); setLoading(false); });

    fetch("/api/teams")
      .then(async (res) => {
        const data = await parseResponse(res);
        if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
        return data;
      })
      .then(setTeams)
      .catch(() => {});
  }, []);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async () => {
    setFormError("");
    if (!form.name || !form.team_id) {
      setFormError("Please fill out all fields.");
      return;
    }
    setSubmitting(true);
    try {
      const res = await fetch("/api/scouts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: form.name, team_id: form.team_id }),
      });
      const data = await parseResponse(res);
      if (!res.ok) throw new Error(data.error || "Failed to create scout");
      setScouts((prev) => [...prev, data.scout]);
      setShowForm(false);
      setForm({ name: "", team_id: "" });
    } catch (err) {
      setFormError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="page-container">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1 className="page-title">Scouts</h1>
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
          + Add Scout
        </button>
      </div>

      {showForm && (
        <div style={{
          position: "fixed", inset: 0, backgroundColor: "rgba(0,0,0,0.5)",
          display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000,
        }}>
          <div style={{
            backgroundColor: "white", borderRadius: "12px", padding: "32px",
            width: "100%", maxWidth: "420px", boxShadow: "0 8px 32px rgba(0,0,0,0.2)",
          }}>
            <h2 style={{ marginTop: 0, marginBottom: "24px" }}>New Scout</h2>

            <label style={{ display: "block", marginBottom: "6px", fontWeight: "bold" }}>Name</label>
            <input
              type="text"
              name="name"
              value={form.name}
              onChange={handleChange}
              placeholder="e.g. Marcus Hill"
              style={{ width: "100%", padding: "10px", borderRadius: "6px", border: "1px solid #ccc", marginBottom: "16px", boxSizing: "border-box" }}
            />

            <label style={{ display: "block", marginBottom: "6px", fontWeight: "bold" }}>Team</label>
            <select
              name="team_id"
              value={form.team_id}
              onChange={handleChange}
              style={{ width: "100%", padding: "10px", borderRadius: "6px", border: "1px solid #ccc", marginBottom: "16px", boxSizing: "border-box" }}
            >
              <option value="">Select a team...</option>
              {teams.length === 0 && <option disabled>No teams available</option>}
              {teams.map((team) => (
                <option key={team.team_id} value={team.team_id}>
                  {team.team_id} - {team.name}
                </option>
              ))}
            </select>

            {formError && (
              <p style={{ color: "red", marginBottom: "16px", fontSize: "14px" }}>{formError}</p>
            )}

            <div style={{ display: "flex", gap: "12px", justifyContent: "flex-end" }}>
              <button
                onClick={() => { setShowForm(false); setFormError(""); }}
                style={{ padding: "10px 20px", borderRadius: "8px", border: "1px solid #ccc", cursor: "pointer", background: "white" }}
              >
                Cancel
              </button>
              <button
                onClick={handleSubmit}
                disabled={submitting}
                style={{ padding: "10px 20px", borderRadius: "8px", border: "none", backgroundColor: "#1a73e8", color: "white", cursor: "pointer", fontWeight: "bold" }}
              >
                {submitting ? "Creating..." : "Create Scout"}
              </button>
            </div>
          </div>
        </div>
      )}

      {loading && <p>Loading scouts...</p>}
      {error && <p>Error: {error}</p>}
      {!loading && !error && scouts.length === 0 && <p>No scouts found. Add one above!</p>}

      <div className="card-grid">
        {!loading && !error && scouts.map((scout) => (
          <div className="baseball-card" key={scout.scout_id}>
            <h2>{scout.name}</h2>
            <p><strong>Team:</strong> {scout.team_name || scout.team_id || "Unassigned"}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default Scouts;

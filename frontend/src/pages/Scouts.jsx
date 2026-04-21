import { useEffect, useState } from "react";

function Scouts() {
  // state for scouts, loading, and error
  const [scouts, setScouts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("/api/scouts")
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => {
        setScouts(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  return (
    <div className="page-container">
      <h1 className="page-title">Scouts</h1>

      {loading && <p>Loading scouts...</p>}
      {error && <p>Error: {error}</p>}
      {!loading && !error && scouts.length === 0 && <p>No scouts found.</p>}

      <div className="card-grid">
        {!loading &&
          !error &&
          scouts.map((scout) => (
            <div className="baseball-card" key={scout.scout_id}>
              <h2>{scout.name}</h2>
              <p>
                <strong>Team:</strong>{" "}
                {scout.team_name || scout.team_id || "Unassigned"}
              </p>
            </div>
          ))}
      </div>
    </div>
  );
}

export default Scouts;

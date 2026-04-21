import { useEffect, useState } from "react";

function Teams() {
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("/api/teams")
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => {
        setTeams(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  return (
    <div className="page-container">
      <h1 className="page-title">Teams</h1>

      {loading && <p>Loading teams...</p>}
      {error && <p>Error: {error}</p>}
      {!loading && !error && teams.length === 0 && <p>No teams found.</p>}

      <div className="card-grid">
        {!loading &&
          !error &&
          teams.map((team) => (
          <div className="baseball-card" key={team.team_id}>
            <h2>{team.name}</h2>
            <p><strong>Division:</strong> {team.division}</p>
            <p><strong>Code:</strong> {team.team_id}</p>
          </div>
          ))}
      </div>
    </div>
  );
}

export default Teams;

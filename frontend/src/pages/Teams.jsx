function Teams() {
  const sampleTeams = [
    { team_id: "LAD", name: "Dodgers", division: "NL West" },
    { team_id: "ATL", name: "Braves", division: "NL East" },
    { team_id: "NYY", name: "Yankees", division: "AL East" },
  ];

  return (
    <div className="page-container">
      <h1 className="page-title">Teams</h1>
      <p className="page-subtitle">Frontend preview layout until backend API is connected.</p>

      <div className="card-grid">
        {sampleTeams.map((team) => (
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
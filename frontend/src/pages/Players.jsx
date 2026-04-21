import { useEffect, useState } from "react";

function Players() {
  // state for players, loading, and error
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  {
    /* fetch players from API or app.py to get json data */
  }
  useEffect(() => {
    fetch("/api/players")
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => {
        setPlayers(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  return (
    <div className="page-container">
      <h1 className="page-title">Players</h1>

      {loading && <p>Loading players...</p>}
      {error && <p>Error: {error}</p>}
      {!loading && !error && players.length === 0 && <p>No players found.</p>}

      {/* player cards if there isnt a error and we arent loading */}
      <div className="card-grid">
        {!loading &&
          !error &&
          players.map((player) => (
            <div className="baseball-card" key={player.player_id}>
              <h2>
                {player.first_name} {player.last_name}
              </h2>
              <p>
                <strong>Position:</strong> {player.primary_position}
              </p>
              <p>
                <strong>ID:</strong> {player.player_id}
              </p>
            </div>
          ))}
      </div>
    </div>
  );
}

export default Players;

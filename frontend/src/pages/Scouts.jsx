function Scouts() {
  const sampleScouts = [
    { id: 1, name: "Marcus Hill", region: "Southeast" },
    { id: 2, name: "David Cole", region: "West Coast" },
    { id: 3, name: "Jordan Reed", region: "Midwest" },
  ];

  return (
    <div className="page-container">
      <h1 className="page-title">Scouts</h1>
      <p className="page-subtitle">Frontend preview layout until backend API is connected.</p>

      <div className="card-grid">
        {sampleScouts.map((scout) => (
          <div className="baseball-card" key={scout.id}>
            <h2>{scout.name}</h2>
            <p><strong>Region:</strong> {scout.region}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default Scouts;
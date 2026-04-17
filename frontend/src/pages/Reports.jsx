function Reports() {
  const sampleReports = [
    { id: 1, player: "Shohei Ohtani", scout: "Marcus Hill", grade: 80, date: "2026-04-01" },
    { id: 2, player: "Ronald Acuna", scout: "David Cole", grade: 75, date: "2026-04-03" },
    { id: 3, player: "Aaron Judge", scout: "Jordan Reed", grade: 78, date: "2026-04-05" },
  ];

  return (
    <div className="page-container">
      <h1 className="page-title">Reports</h1>
      <p className="page-subtitle">Frontend preview layout until backend API is connected.</p>

      <div className="card-grid">
        {sampleReports.map((report) => (
          <div className="baseball-card" key={report.id}>
            <h2>{report.player}</h2>
            <p><strong>Scout:</strong> {report.scout}</p>
            <p><strong>Grade:</strong> {report.grade}</p>
            <p><strong>Date:</strong> {report.date}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default Reports;
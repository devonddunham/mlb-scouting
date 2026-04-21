function Home() {
  return (
    <div className="page-container">
      <section className="hero">
        <h1 className="page-title">Baseball Scouting Report System</h1>
        <p className="hero-text">
          Review players, organize teams, track scouts, and display scouting reports.
        </p>

        <div className="diamond">
          <div className="base home"></div>
          <div className="base first"></div>
          <div className="base second"></div>
          <div className="base third"></div>
        </div>
      </section>
    </div>
  );
}

export default Home;
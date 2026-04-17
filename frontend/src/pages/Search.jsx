function Search() {
  return (
    <div className="page-container">
      <h1 className="page-title">Search</h1>
      <div className="search-panel">
        <input className="search-input" type="text" placeholder="Search players, scouts, or reports..." />
        <button className="search-button">Search</button>
      </div>
      <p className="page-subtitle">Search UI preview. Backend hookup can be added later.</p>
    </div>
  );
}

export default Search;
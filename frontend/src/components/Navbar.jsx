import { Link } from "react-router-dom";

function Navbar() {
  return (
    <nav className="navbar">
      <div className="nav-brand">⚾ MLB Scouting</div>
      <div className="nav-links">
        <Link to="/">Home</Link>
        <Link to="/players">Players</Link>
        <Link to="/teams">Teams</Link>
        <Link to="/scouts">Scouts</Link>
        <Link to="/reports">Reports</Link>
        <Link to="/search">Search</Link>
      </div>
    </nav>
  );
}

export default Navbar;
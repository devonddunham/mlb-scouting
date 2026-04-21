import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Home from "./pages/Home";
import Players from "./pages/Players";
import Teams from "./pages/Teams";
import Scouts from "./pages/Scouts";
import Reports from "./pages/Reports";
import ReportDetail from "./pages/ReportDetail";
import Search from "./pages/Search";
import "./index.css";

function App() {
  return (
    <Router>
      <div className="app-shell">
        <Navbar />
        <main className="page-wrap">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/players" element={<Players />} />
            <Route path="/teams" element={<Teams />} />
            <Route path="/scouts" element={<Scouts />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/reports/:reportId" element={<ReportDetail />} />
            <Route path="/search" element={<Search />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;

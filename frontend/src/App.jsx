import { Routes, Route, Navigate } from "react-router-dom";
import Login from "./login";
import Home from "./home";
import Dashboard from "./dashboard";
import TournamentsPage from "./pages/TournamentsPage";
import TeamsPage from "./pages/TeamsPage";
import PlayersPage from "./pages/PlayersPage";
import FacultiesPage from "./pages/FacultiesPage";
import ComplexesPage from "./pages/ComplexesPage";
import ReportsPage from "./reports";
import MatchesPage from "./matches";
import SanctionsPage from "./sanctions";

function RutaProtegida({ children, roles }) {
  const token = localStorage.getItem("token");
  const rol = localStorage.getItem("rol");
  if (!token) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(rol)) return <Navigate to="/" replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<RutaProtegida><Home /></RutaProtegida>}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/torneos" element={<TournamentsPage />} />
        <Route path="/equipos" element={<TeamsPage />} />
        <Route path="/jugadores" element={<PlayersPage />} />
        <Route path="/facultades" element={<FacultiesPage />} />
        <Route path="/complejos" element={<ComplexesPage />} />
        <Route path="/partidos" element={<MatchesPage />} />
        <Route path="/sanciones" element={<RutaProtegida roles={["administrador"]}><SanctionsPage /></RutaProtegida>} />
        <Route path="/reportes" element={<ReportsPage />} />
      </Route>
      {/* cualquier otra URL -> a la raíz (que si no hay token, manda al login) */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
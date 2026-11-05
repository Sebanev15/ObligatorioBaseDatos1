import { Routes, Route, Navigate } from "react-router-dom";
import Login from "./login";
import Home, { Dashboard } from "./home";
import ManagementPage from "./management";

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
        <Route path="/torneos" element={<ManagementPage key="torneos" resource="torneos" />} />
        <Route path="/equipos" element={<ManagementPage key="equipos" resource="equipos" />} />
        <Route path="/jugadores" element={<ManagementPage key="jugadores" resource="jugadores" />} />
        <Route path="/facultades" element={<ManagementPage key="facultades" resource="facultades" />} />
        <Route path="/complejos" element={<ManagementPage key="complejos" resource="complejos" />} />
      </Route>
      {/* cualquier otra URL -> a la raíz (que si no hay token, manda al login) */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
import { Routes, Route, Navigate } from "react-router-dom";
import Login from "./login";
import Home from "./home";

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
      <Route
        path="/"
        element={
          <RutaProtegida>
            <Home />
          </RutaProtegida>
        }
      />
      {/* cualquier otra URL -> a la raíz (que si no hay token, manda al login) */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
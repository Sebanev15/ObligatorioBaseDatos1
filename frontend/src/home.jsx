import { useNavigate } from "react-router-dom";

export default function Home() {
  const navigate = useNavigate();
  const rol = localStorage.getItem("rol");

  function cerrarSesion() {
    localStorage.clear();
    navigate("/login");
  }

  return (
    <div>
      <h1>Torneo Interfacultades de Fútbol 5</h1>
      <p>Sesión iniciada como: {rol}</p>
      <button onClick={cerrarSesion}>Cerrar sesión</button>
    </div>
  );
}
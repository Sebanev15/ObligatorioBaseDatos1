import { useNavigate, Outlet } from "react-router-dom";
import Sidebar from "./navigation";

export default function Home() {
  const navigate = useNavigate();
  const rol = localStorage.getItem("rol") || "Usuario";

  function cerrarSesion() {
    localStorage.removeItem("token");
    localStorage.removeItem("rol");
    navigate("/login");
  }

  return (
    <div data-theme="emerald" className="min-h-screen bg-[#F6F7F9] text-base-content">
      <div className="drawer lg:drawer-open">
        <input id="dashboard-drawer" type="checkbox" className="drawer-toggle" />
        <div className="drawer-content flex min-h-screen flex-col">
          <header className="sticky top-0 z-20 flex h-[4.5rem] items-center justify-between border-b border-base-200 bg-base-100/95 px-4 backdrop-blur sm:px-7">
            <div className="flex items-center gap-3">
              <label htmlFor="dashboard-drawer" className="btn btn-ghost btn-square btn-sm lg:hidden" aria-label="Abrir menú">
                <svg aria-hidden="true" viewBox="0 0 24 24" className="size-5" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </label>
              <div>
                <p className="text-xs text-base-content/50">Panel de gestión</p>
                <p className="text-sm font-semibold text-base-content">Fútbol 5 Interfacultades</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className="hidden text-sm capitalize text-base-content/65 sm:inline">{rol}</span>
              <button onClick={cerrarSesion} className="btn btn-ghost btn-sm">Cerrar sesión</button>
            </div>
          </header>
          <main className="mx-auto w-full max-w-[1440px] flex-1 p-4 sm:p-7 lg:p-9">
            <Outlet />
          </main>
        </div>
        <div className="drawer-side z-30">
          <label htmlFor="dashboard-drawer" className="drawer-overlay" aria-label="Cerrar menú" />
          <aside className="min-h-full w-72 border-r border-base-200 bg-base-100"><Sidebar /></aside>
        </div>
      </div>
    </div>
  );
}

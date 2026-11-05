import { useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { apiFetch } from "./api";

const sections = [
  { path: "/", label: "Resumen", icon: "overview", end: true },
  { path: "/torneos", label: "Torneos", icon: "tournament" },
  { path: "/equipos", label: "Equipos", icon: "team" },
  { path: "/jugadores", label: "Jugadores", icon: "player" },
  { path: "/facultades", label: "Facultades", icon: "faculty" },
  { path: "/complejos", label: "Complejos", icon: "venue" },
  { path: "/reportes", label: "Reportes", icon: "reports" },
];

const iconPaths = {
  overview: <><path d="m3 10 9-7 9 7" /><path d="M5 9v11h14V9M9 20v-6h6v6" /></>,
  tournament: <><path d="M8 21h8m-4-4v4" /><path d="M7 4h10v5a5 5 0 0 1-10 0V4Z" /><path d="M7 6H4v2a4 4 0 0 0 4 4m9-6h3v2a4 4 0 0 1-4 4" /></>,
  team: <><circle cx="12" cy="12" r="9" /><path d="m12 7 3 2v4l-3 2-3-2V9l3-2Zm0 0v8m-3-6 6 4m0-4-6 4" /></>,
  player: <><circle cx="12" cy="8" r="4" /><path d="M4 21a8 8 0 0 1 16 0" /></>,
  faculty: <><path d="m3 9 9-5 9 5-9 5-9-5Z" /><path d="M6 11v5c3 3 9 3 12 0v-5m3-2v7" /></>,
  venue: <><path d="M3 21h18M5 21V8l7-4 7 4v13M9 21v-6h6v6" /><path d="M9 10h.01M15 10h.01" /></>,
  reports: <><path d="M4 19V5m0 14h17" /><path d="m7 15 4-4 3 2 6-7" /><path d="M16 6h4v4" /></>,
};

function SectionIcon({ name, className = "size-5" }) {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      {iconPaths[name]}
    </svg>
  );
}

function Sidebar() {
  return (
    <div className="flex h-full flex-col bg-base-100 p-5">
      <NavLink to="/" className="mb-9 flex items-center gap-3 px-1">
        <span className="grid size-11 place-items-center rounded-2xl bg-[#248C7E] text-xs font-bold tracking-wide text-white">TF5</span>
        <span className="leading-tight">
          <span className="block text-sm font-bold text-base-content">Fútbol 5</span>
          <span className="text-xs text-base-content/55">Interfacultades</span>
        </span>
      </NavLink>
      <p className="mb-2 px-3 text-[0.68rem] font-bold uppercase tracking-[0.16em] text-base-content/40">
        Administración
      </p>
      <nav className="flex flex-col gap-1">
        {sections.map((section) => (
          <NavLink
            key={section.path}
            to={section.path}
            end={section.end}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
                isActive
                  ? "bg-[#248C7E] text-white shadow-sm"
                  : "text-base-content/70 hover:bg-base-200 hover:text-base-content"
              }`
            }
          >
            <SectionIcon name={section.icon} />
            {section.label}
          </NavLink>
        ))}
      </nav>
      <div className="mt-auto rounded-2xl bg-[#F6F7F9] p-4">
        <p className="text-sm font-semibold text-base-content">Torneo Interfacultades</p>
        <p className="mt-1 text-xs leading-relaxed text-base-content/60">
          Gestión de equipos, jugadores y competencias.
        </p>
      </div>
    </div>
  );
}

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

function SummaryCard({ title, count, symbol, path, caption }) {
  return (
    <NavLink to={path} className="rounded-2xl border border-base-200 bg-base-100 p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md sm:p-6">
      <span className="grid size-11 place-items-center rounded-xl bg-[#248C7E]/10 text-[#248C7E]">
        <SectionIcon name={symbol} className="size-6" />
      </span>
      <p className="mt-5 text-sm font-medium text-base-content/60">{title}</p>
      <p className="mt-1 text-3xl font-semibold tracking-tight text-base-content">
        {count === null ? <span className="loading loading-dots loading-sm" /> : count}
      </p>
      <p className="mt-2 text-xs text-base-content/45">{caption}</p>
    </NavLink>
  );
}

async function loadCount(endpoint) {
  const response = await apiFetch(endpoint);
  if (!response.ok) throw new Error("No se pudieron cargar los datos.");
  return (await response.json()).length;
}

export function Dashboard() {
  const [counts, setCounts] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    Promise.all([
      loadCount("/api/torneos?limit=200"),
      loadCount("/api/equipos?limit=200"),
      loadCount("/api/jugadores?limit=200"),
      loadCount("/api/facultades?limit=200"),
    ])
      .then(([torneos, equipos, jugadores, facultades]) => {
        if (active) setCounts({ torneos, equipos, jugadores, facultades });
      })
      .catch((err) => {
        if (active) setError(err.message);
      });
    return () => { active = false; };
  }, []);

  return (
    <section>
      <div className="mb-8 flex flex-col gap-2 sm:mb-10">
        <p className="text-sm font-semibold uppercase tracking-[0.14em] text-[#248C7E]">Bienvenido</p>
        <h1 className="!m-0 !text-3xl !font-bold !tracking-tight text-base-content sm:!text-4xl">Resumen general</h1>
        <p className="max-w-2xl text-sm leading-relaxed text-base-content/60 sm:text-base">
          Una vista rápida de las entidades principales del torneo.
        </p>
      </div>
      {error && <div role="alert" className="alert alert-error mb-6"><span>{error}</span></div>}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <SummaryCard title="Torneos" count={counts?.torneos ?? null} symbol="tournament" path="/torneos" caption="Competencias registradas" />
        <SummaryCard title="Equipos" count={counts?.equipos ?? null} symbol="team" path="/equipos" caption="Inscritos en los torneos" />
        <SummaryCard title="Jugadores" count={counts?.jugadores ?? null} symbol="player" path="/jugadores" caption="Jugadores registrados" />
        <SummaryCard title="Facultades" count={counts?.facultades ?? null} symbol="faculty" path="/facultades" caption="Participantes registradas" />
      </div>
      <div className="mt-7 rounded-2xl border border-base-200 bg-base-100 p-6 shadow-sm sm:p-7">
        <h2 className="!mb-2 !text-lg !font-semibold text-base-content">Torneo Interfacultades de Fútbol 5</h2>
        <p className="text-sm text-base-content/55">
          Usá el menú lateral para consultar las competencias, los equipos, los jugadores, las facultades y las sedes.
        </p>
      </div>
    </section>
  );
}

import { NavLink } from "react-router-dom";

const sections = [
  { path: "/", label: "Resumen", icon: "overview", end: true },
  { path: "/torneos", label: "Torneos", icon: "tournament" },
  { path: "/equipos", label: "Equipos", icon: "team" },
  { path: "/jugadores", label: "Jugadores", icon: "player" },
  { path: "/facultades", label: "Facultades", icon: "faculty" },
  { path: "/complejos", label: "Complejos", icon: "venue" },
  { path: "/partidos", label: "Partidos", icon: "matches" },
  { path: "/reportes", label: "Reportes", icon: "reports" },
];

const iconPaths = {
  overview: <><path d="m3 10 9-7 9 7" /><path d="M5 9v11h14V9M9 20v-6h6v6" /></>,
  tournament: <><path d="M8 21h8m-4-4v4" /><path d="M7 4h10v5a5 5 0 0 1-10 0V4Z" /><path d="M7 6H4v2a4 4 0 0 0 4 4m9-6h3v2a4 4 0 0 1-4 4" /></>,
  team: <><circle cx="9" cy="8" r="3" /><circle cx="17" cy="9" r="2.5" /><path d="M3.5 20a5.5 5.5 0 0 1 11 0m.5-4a4.5 4.5 0 0 1 6 4" /></>,
  player: <><circle cx="12" cy="8" r="4" /><path d="M4 21a8 8 0 0 1 16 0" /></>,
  faculty: <><path d="m3 9 9-5 9 5-9 5-9-5Z" /><path d="M6 11v5c3 3 9 3 12 0v-5m3-2v7" /></>,
  venue: <><path d="M3 21h18M5 21V8l7-4 7 4v13M9 21v-6h6v6" /><path d="M9 10h.01M15 10h.01" /></>,
  matches: <><rect x="3" y="4" width="18" height="16" rx="1" /><path d="M12 4v16" /><circle cx="12" cy="12" r="2.5" /></>,
  sanctions: <><rect x="3" y="1" width="14" height="18" rx="2" fill="#F2C94C" /><rect x="7" y="5" width="14" height="18" rx="2" fill="#EB5757" /></>,
  reports: <><path d="M4 19V5m0 14h17" /><path d="m7 15 4-4 3 2 6-7" /><path d="M16 6h4v4" /></>,
};

export function SectionIcon({ name, className = "size-5" }) {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      {iconPaths[name]}
    </svg>
  );
}

export default function Sidebar() {
  const isAdmin = localStorage.getItem("rol") === "administrador";
  const visibleSections = isAdmin
    ? [...sections, { path: "/sanciones", label: "Sanciones", icon: "sanctions" }]
    : sections;

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
        {visibleSections.map((section) => (
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

    </div>
  );
}

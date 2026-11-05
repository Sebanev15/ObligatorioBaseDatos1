import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "./api";

const resources = {
  torneos: {
    title: "Torneos",
    description: "Consultá los campeonatos y su estado.",
    endpoint: "/api/torneos?limit=200",
    columns: [["nombre", "Nombre"], ["anio", "Año"], ["semestre", "Semestre"], ["fecha_inicio", "Inicio"], ["fecha_fin", "Fin"], ["estado", "Estado"]],
    id: "id_torneo",
  },
  equipos: {
    title: "Equipos",
    description: "Equipos registrados por torneo y facultad.",
    endpoint: "/api/equipos?limit=200",
    columns: [["nombre", "Equipo"], ["torneo", "Torneo"], ["facultad", "Facultad"], ["cantidad_jugadores", "Jugadores"]],
    id: "id_equipo",
  },
  jugadores: {
    title: "Jugadores",
    description: "Directorio de jugadores participantes.",
    endpoint: "/api/jugadores?limit=200",
    columns: [["ci", "Cédula"], ["nombre_completo", "Nombre"], ["email", "Correo electrónico"], ["facultad", "Facultad"], ["tipo", "Categoría"]],
    id: "ci",
  },
  facultades: {
    title: "Facultades",
    description: "Facultades que participan en la competencia.",
    endpoint: "/api/facultades?limit=200",
    columns: [["nombre", "Facultad"]],
    id: "id_facultad",
  },
  complejos: {
    title: "Complejos deportivos",
    description: "Sedes y ubicaciones donde se juega.",
    endpoint: "/api/complejos",
    columns: [["nombre", "Complejo"], ["direccion", "Dirección"], ["departamento", "Departamento"]],
    id: "id_complejo",
  },
};

const labels = {
  inscripcion: "Inscripción",
  "en curso": "En curso",
  finalizado: "Finalizado",
  grado: "Grado",
  posgrado: "Posgrado",
  docente: "Docente",
  funcionario: "Funcionario",
};

function repairEncoding(value) {
  let result = value;
  for (let attempt = 0; attempt < 2 && /[ÃÂ]/.test(result); attempt += 1) {
    const bytes = Array.from(result, (character) => character.codePointAt(0));
    if (bytes.some((value) => value > 255)) break;
    try {
      const decoded = new TextDecoder("utf-8", { fatal: true }).decode(new Uint8Array(bytes));
      if (decoded === result) break;
      result = decoded;
    } catch {
      break;
    }
  }
  return result;
}

function display(value) {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value !== "string") return String(value);
  const cleaned = repairEncoding(value.trim());
  if (!cleaned || cleaned === "undefined" || cleaned === "null") return "—";
  return labels[cleaned] || cleaned;
}

function cellValue(row, key) {
  if (key === "nombre_completo") {
    return [row.nombre, row.apellido].filter(Boolean).map(display).join(" ") || "—";
  }
  if (key === "semestre") return `Semestre ${row.semestre}`;
  return display(row[key]);
}

export default function ManagementPage({ resource }) {
  const config = resources[resource];
  const [rows, setRows] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    apiFetch(config.endpoint)
      .then(async (response) => {
        if (!response.ok) {
          const body = await response.json().catch(() => ({}));
          throw new Error(body.detail || "No se pudieron cargar los registros.");
        }
        return response.json();
      })
      .then((data) => {
        if (active) setRows(data);
      })
      .catch((err) => {
        if (active) setError(err.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, [config.endpoint]);

  const visibleRows = useMemo(() => {
    const query = repairEncoding(search.trim()).toLocaleLowerCase();
    if (!query) return rows;
    return rows.filter((row) =>
      config.columns.some(([key]) =>
        cellValue(row, key).toLocaleLowerCase().includes(query),
      ),
    );
  }, [config.columns, rows, search]);

  return (
    <section>
      <div className="mb-7 flex flex-col justify-between gap-5 sm:mb-9 sm:flex-row sm:items-end">
        <div>
          <p className="mb-2 text-sm font-semibold uppercase tracking-[0.14em] text-[#248C7E]">Administración</p>
          <h1 className="!m-0 !text-3xl !font-bold !tracking-tight text-base-content sm:!text-4xl">{config.title}</h1>
          <p className="mt-2 text-sm text-base-content/60 sm:text-base">{config.description}</p>
        </div>
        <div className="rounded-xl border border-base-200 bg-base-100 px-4 py-2.5 text-sm text-base-content/60 shadow-sm">
          {loading ? "Cargando..." : `${visibleRows.length} registros`}
        </div>
      </div>

      <div className="overflow-hidden rounded-2xl border border-base-200 bg-base-100 shadow-sm">
        <div className="flex flex-col gap-4 border-b border-base-200 p-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <div>
            <h2 className="!mb-1 !text-base !font-semibold text-base-content">Listado de {config.title.toLocaleLowerCase()}</h2>
            <p className="text-xs text-base-content/50">Información registrada en el sistema</p>
          </div>
          <label className="input input-bordered flex w-full items-center gap-2 bg-base-100 sm:max-w-xs">
            <svg aria-hidden="true" viewBox="0 0 24 24" className="size-4 shrink-0 opacity-50" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="7" />
              <path d="m20 20-4-4" />
            </svg>
            <input
              type="search"
              className="grow"
              placeholder={`Buscar ${config.title.toLocaleLowerCase()}...`}
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              aria-label={`Buscar ${config.title.toLocaleLowerCase()}`}
            />
          </label>
        </div>

        {error ? (
          <div role="alert" className="alert alert-error m-5 w-auto"><span>{display(error)}</span></div>
        ) : loading ? (
          <div className="flex min-h-56 items-center justify-center gap-3 text-sm text-base-content/55">
            <span className="loading loading-spinner loading-md text-[#248C7E]" />
            Cargando información...
          </div>
        ) : visibleRows.length === 0 ? (
          <div className="flex min-h-56 flex-col items-center justify-center px-6 text-center">
            <p className="font-semibold text-base-content">
              {rows.length ? "No hay resultados para esa búsqueda" : `Todavía no hay ${config.title.toLocaleLowerCase()}`}
            </p>
            <p className="mt-1 text-sm text-base-content/55">
              {rows.length ? "Probá con otro nombre o término." : "Cuando se agreguen registros, aparecerán en este listado."}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="table table-zebra">
              <thead>
                <tr>{config.columns.map(([, title]) => <th key={title}>{title}</th>)}</tr>
              </thead>
              <tbody>
                {visibleRows.map((row) => (
                  <tr key={row[config.id]}>
                    {config.columns.map(([key]) => (
                      <td key={key} className="whitespace-nowrap">
                        {key === "estado" ? (
                          <span className={`badge ${row.estado === "en curso" ? "badge-success" : row.estado === "finalizado" ? "badge-neutral" : "badge-outline"}`}>
                            {cellValue(row, key)}
                          </span>
                        ) : cellValue(row, key)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}

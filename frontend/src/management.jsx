import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "./api";
import { repairEncoding } from "./text";
import { TournamentMatches } from "./matches";

const departments = [
  "Artigas", "Canelones", "Cerro Largo", "Colonia", "Durazno", "Flores",
  "Florida", "Lavalleja", "Maldonado", "Montevideo", "Paysandú", "Río Negro",
  "Rivera", "Rocha", "Salto", "San José", "Soriano", "Tacuarembó", "Treinta y Tres",
];

const types = ["grado", "posgrado", "docente", "funcionario"];
const tournamentStates = ["inscripcion", "en curso", "finalizado"];

const resources = {
  torneos: {
    title: "Torneos",
    endpoint: "/api/torneos?limit=200",
    collection: "/api/torneos",
    id: "id_torneo",
    method: "PATCH",
    columns: [["nombre", "Nombre"], ["anio", "Año"], ["semestre", "Semestre"], ["fecha_inicio", "Inicio"], ["fecha_fin", "Fin"], ["estado", "Estado"]],
    fields: [
      { key: "nombre", label: "Nombre", required: true },
      { key: "anio", label: "Año", type: "number", min: 1, max: 9999, required: true },
      { key: "semestre", label: "Semestre", type: "select", options: ["1", "2"], required: true },
      { key: "fecha_inicio", label: "Fecha de inicio", type: "date", required: true },
      { key: "fecha_fin", label: "Fecha de fin", type: "date", required: true },
      { key: "estado", label: "Etapa", type: "select", options: tournamentStates },
    ],
  },
  equipos: {
    title: "Equipos",
    endpoint: "/api/equipos?limit=200",
    collection: "/api/equipos",
    id: "id_equipo",
    method: "PATCH",
    columns: [["nombre", "Equipo"], ["torneo", "Torneo"], ["facultad", "Facultad"], ["cantidad_jugadores", "Jugadores"]],
    fields: [
      { key: "nombre", label: "Nombre", required: true },
      { key: "id_torneo", label: "Torneo", type: "relation", relation: "torneos", required: true },
      { key: "id_facultad", label: "Facultad", type: "relation", relation: "facultades", required: true },
    ],
  },
  jugadores: {
    title: "Jugadores",
    endpoint: "/api/jugadores?limit=200",
    collection: "/api/jugadores",
    id: "ci",
    method: "PATCH",
    columns: [["ci", "Cédula"], ["nombre_completo", "Nombre"], ["email", "Correo electrónico"], ["facultad", "Facultad"], ["tipo", "Categoría"]],
    fields: [
      { key: "ci", label: "Cédula (sin puntos ni guion)", type: "number", min: 1000000, max: 99999999, required: true, createOnly: true },
      { key: "nombre", label: "Nombre", required: true },
      { key: "apellido", label: "Apellido", required: true },
      { key: "email", label: "Correo electrónico", type: "email", required: true },
      { key: "fecha_nacimiento", label: "Fecha de nacimiento", type: "date", required: true },
      { key: "id_facultad", label: "Facultad", type: "relation", relation: "facultades", required: true },
      { key: "tipo", label: "Categoría", type: "select", options: types, required: true },
    ],
  },
  facultades: {
    title: "Facultades",
    endpoint: "/api/facultades?limit=200",
    collection: "/api/facultades",
    id: "id_facultad",
    method: "PUT",
    columns: [["nombre", "Facultad"]],
    fields: [{ key: "nombre", label: "Nombre", required: true }],
  },
  complejos: {
    title: "Complejos deportivos",
    endpoint: "/api/complejos",
    collection: "/api/complejos",
    id: "id_complejo",
    method: "PATCH",
    columns: [["nombre", "Complejo"], ["direccion", "Dirección"], ["departamento", "Departamento"]],
    fields: [
      { key: "nombre", label: "Nombre", required: true },
      { key: "direccion", label: "Dirección", required: true },
      { key: "departamento", label: "Departamento", type: "select", options: departments, required: true },
    ],
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

async function request(url, options) {
  const response = await apiFetch(url, options);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = Array.isArray(body.detail)
      ? body.detail.map((item) => item.msg).join(". ")
      : body.detail;
    throw new Error(detail || "No se pudo completar la operación.");
  }
  return response.status === 204 ? null : response.json();
}

function display(value) {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value !== "string") return String(value);
  const cleaned = repairEncoding(value.trim());
  if (!cleaned || cleaned === "undefined" || cleaned === "null") return "—";
  return labels[cleaned] || cleaned;
}

function cellValue(row, key) {
  if (key === "nombre_completo") return [row.nombre, row.apellido].filter(Boolean).map(display).join(" ") || "—";
  if (key === "semestre") return `Semestre ${row.semestre}`;
  return display(row[key]);
}

function RecordForm({ config, record, relations, onClose, onSave }) {
  const [values, setValues] = useState(() => Object.fromEntries(
    config.fields.map((field) => [field.key, record?.[field.key] ?? ""]),
  ));
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const fields = config.fields.filter((field) => !record || !field.createOnly);

  async function submit(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    const body = Object.fromEntries(fields.map((field) => {
      const value = values[field.key];
      return [field.key, field.type === "number" || field.type === "relation" || (field.type === "select" && /^\d+$/.test(value))
        ? Number(value)
        : value];
    }));
    try {
      await onSave(body);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <dialog open className="modal modal-open">
      <div className="modal-box">
        <h2 className="!mb-5 !text-xl !font-bold text-base-content">{record ? "Editar" : "Agregar"} {config.title.toLocaleLowerCase()}</h2>
        <form onSubmit={submit} className="space-y-4">
          {fields.map((field) => {
            const options = field.type === "relation"
              ? (relations[field.relation] || []).map((item) => ({
                value: item[field.relation === "torneos" ? "id_torneo" : "id_facultad"],
                label: field.relation === "torneos"
                  ? `${display(item.nombre)} — ${item.anio}, semestre ${item.semestre}`
                  : display(item.nombre),
              }))
              : field.options?.map((value) => ({ value, label: labels[value] || value }));
            return (
              <label className="form-control block" key={field.key}>
                <span className="label-text mb-1 block font-medium">{field.label}</span>
                {options ? (
                  <select
                    className="select select-bordered w-full"
                    value={values[field.key]}
                    required={field.required}
                    onChange={(event) => setValues({ ...values, [field.key]: event.target.value })}
                  >
                    <option value="">Seleccioná...</option>
                    {options.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
                  </select>
                ) : (
                  <input
                    className="input input-bordered w-full"
                    type={field.type || "text"}
                    min={field.min}
                    max={field.max}
                    required={field.required}
                    value={values[field.key]}
                    onChange={(event) => setValues({ ...values, [field.key]: event.target.value })}
                  />
                )}
              </label>
            );
          })}
          {error && <div role="alert" className="alert alert-error"><span>{display(error)}</span></div>}
          <div className="modal-action">
            <button type="button" className="btn btn-ghost" onClick={onClose}>Cancelar</button>
            <button type="submit" className="btn bg-[#248C7E] text-white" disabled={saving}>
              {saving ? "Guardando..." : "Guardar"}
            </button>
          </div>
        </form>
      </div>
      <form method="dialog" className="modal-backdrop"><button aria-label="Cerrar" onClick={onClose}>close</button></form>
    </dialog>
  );
}

function TeamRoster({ team, isAdmin, onTeamUpdate }) {
  const [players, setPlayers] = useState([]);
  const [candidates, setCandidates] = useState([]);
  const [shirtValues, setShirtValues] = useState({});
  const [ci, setCi] = useState("");
  const [shirt, setShirt] = useState("");
  const [captain, setCaptain] = useState(team.ci_capitan || "");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function reload() {
    const [roster, eligiblePlayers] = await Promise.all([
      request(`/api/equipos/${team.id_equipo}/jugadores`),
      request(`/api/equipos/${team.id_equipo}/jugadores/candidatos`),
    ]);
    setPlayers(roster);
    setCandidates(eligiblePlayers);
  }

  useEffect(() => {
    let active = true;
    Promise.all([
      request(`/api/equipos/${team.id_equipo}/jugadores`),
      request(`/api/equipos/${team.id_equipo}/jugadores/candidatos`),
    ])
      .then(([roster, eligiblePlayers]) => {
        if (active) {
          setPlayers(roster);
          setCandidates(eligiblePlayers);
        }
      })
      .catch((err) => { if (active) setError(err.message); });
    return () => { active = false; };
  }, [team.id_equipo]);

  async function mutate(action) {
    setBusy(true);
    setError("");
    try {
      await action();
      await reload();
      onTeamUpdate();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4 bg-base-200/40 p-4">
      {isAdmin && <div className="flex flex-wrap items-end gap-3">
        <label className="form-control">
          <span className="label-text mb-1">Jugador</span>
          <select className="select select-bordered select-sm min-w-64" value={ci} onChange={(event) => setCi(event.target.value)}>
            <option value="">Seleccioná un jugador</option>
            {candidates.map((player) => {
              const ciDisplay = String(player.ci).replace(/\D/g, "");
              return (
                <option key={ciDisplay} value={ciDisplay} disabled={!player.puede_agregar}>
                  {display(`${player.nombre} ${player.apellido}`)} · {ciDisplay}{player.motivo ? ` — ${display(player.motivo)}` : ""}
                </option>
              );
            })}
          </select>
        </label>
        <label className="form-control">
          <span className="label-text mb-1">Camiseta</span>
          <input className="input input-bordered input-sm w-28" type="number" min="1" max="99" value={shirt} onChange={(event) => setShirt(event.target.value)} />
        </label>
        <button className="btn btn-sm bg-[#248C7E] text-white" disabled={busy || !ci || !shirt} onClick={() => mutate(async () => {
          await request(`/api/equipos/${team.id_equipo}/jugadores`, {
            method: "POST",
            body: JSON.stringify({ ci_jugador: Number(ci), numero_camiseta: Number(shirt) }),
          });
          setCi("");
          setShirt("");
        })}>Agregar al plantel</button>
      </div>}
      {isAdmin && <div className="flex flex-wrap items-end gap-3">
        <label className="form-control">
          <span className="label-text mb-1">Capitán</span>
          <select className="select select-bordered select-sm" value={captain} onChange={(event) => setCaptain(event.target.value)}>
            <option value="">Seleccioná un integrante</option>
            {players.map((player) => <option key={player.ci} value={player.ci}>{display(`${player.nombre} ${player.apellido}`)}</option>)}
          </select>
        </label>
        <button className="btn btn-sm" disabled={busy || !captain} onClick={() => mutate(async () => {
          await request(`/api/equipos/${team.id_equipo}`, {
            method: "PATCH",
            body: JSON.stringify({ ci_capitan: Number(captain) }),
          });
        })}>Asignar capitán</button>
      </div>}
      {error && <div role="alert" className="alert alert-error py-2"><span>{display(error)}</span></div>}
      {players.length === 0 ? <p className="text-sm text-base-content/60">El plantel está vacío.</p> : (
        <div className="overflow-x-auto">
          <table className="table table-sm">
            <thead><tr><th>Jugador</th><th>Tipo</th><th>Camiseta</th><th>Capitán</th><th /></tr></thead>
            <tbody>{players.map((player) => (
              <tr key={player.ci}>
                <td>{display(`${player.nombre} ${player.apellido}`)}</td>
                <td>{display(player.tipo)}</td>
                <td>{isAdmin ? (
                  <div className="flex items-center gap-2">
                    <input
                      className="input input-bordered input-xs w-20"
                      type="number"
                      min="1"
                      max="99"
                      value={shirtValues[player.ci] ?? player.numero_camiseta}
                      onChange={(event) => setShirtValues({ ...shirtValues, [player.ci]: event.target.value })}
                    />
                    {String(shirtValues[player.ci] ?? player.numero_camiseta) !== String(player.numero_camiseta) && (
                      <button className="btn btn-ghost btn-xs" disabled={busy} onClick={() => mutate(async () => {
                        await request(`/api/equipos/${team.id_equipo}/jugadores/${player.ci}`, {
                          method: "PATCH",
                          body: JSON.stringify({ numero_camiseta: Number(shirtValues[player.ci]) }),
                        });
                      })}>Guardar</button>
                    )}
                  </div>
                ) : player.numero_camiseta}</td>
                <td>{player.es_capitan ? "Sí" : "—"}</td>
                <td>
                  {isAdmin && <button
                    className="btn btn-ghost btn-xs text-error"
                    disabled={busy}
                    onClick={() => window.confirm(`¿Quitar a ${display(player.nombre)} del plantel?`) && mutate(
                      () => request(`/api/equipos/${team.id_equipo}/jugadores/${player.ci}`, { method: "DELETE" }),
                    )}
                  >Quitar</button>}
                </td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function Courts({ complex, isAdmin }) {
  const [courts, setCourts] = useState([]);
  const [editingCourt, setEditingCourt] = useState("");
  const [editSurface, setEditSurface] = useState("sintetico");
  const [editCovered, setEditCovered] = useState(false);
  const [name, setName] = useState("");
  const [surface, setSurface] = useState("sintetico");
  const [covered, setCovered] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function reload() {
    setCourts(await request(`/api/complejos/${complex.id_complejo}/canchas`));
  }

  useEffect(() => {
    let active = true;
    request(`/api/complejos/${complex.id_complejo}/canchas`)
      .then((data) => { if (active) setCourts(data); })
      .catch((err) => { if (active) setError(err.message); });
    return () => { active = false; };
  }, [complex.id_complejo]);

  async function mutate(action) {
    setBusy(true);
    setError("");
    try {
      await action();
      await reload();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-3 bg-base-200/40 p-4">
      {isAdmin && <div className="flex flex-wrap items-end gap-3">
        <label className="form-control">
          <span className="label-text mb-1">Cancha</span>
          <input className="input input-bordered input-sm" value={name} onChange={(event) => setName(event.target.value)} />
        </label>
        <label className="form-control">
          <span className="label-text mb-1">Superficie</span>
          <select className="select select-bordered select-sm" value={surface} onChange={(event) => setSurface(event.target.value)}>
            <option value="sintetico">Sintético</option><option value="parquet">Parquet</option>
          </select>
        </label>
        <label className="label cursor-pointer gap-2">
          <input className="checkbox checkbox-sm" type="checkbox" checked={covered} onChange={(event) => setCovered(event.target.checked)} />
          <span className="label-text">Techada</span>
        </label>
        <button className="btn btn-sm bg-[#248C7E] text-white" disabled={busy || !name.trim()} onClick={() => mutate(async () => {
          await request(`/api/complejos/${complex.id_complejo}/canchas`, {
            method: "POST",
            body: JSON.stringify({ nombre_cancha: name.trim(), superficie: surface, techada: covered }),
          });
          setName("");
          setCovered(false);
        })}>Agregar cancha</button>
      </div>}
      {error && <div role="alert" className="alert alert-error py-2"><span>{display(error)}</span></div>}
      <div className="flex flex-wrap gap-2">
        {courts.map((court) => (
          <div key={court.nombre_cancha} className="flex flex-wrap items-center gap-2 rounded-lg border border-base-300 bg-base-100 px-3 py-2">
            <span>{display(court.nombre_cancha)}</span>
            {isAdmin && editingCourt === court.nombre_cancha ? (
              <>
                <select className="select select-bordered select-xs" value={editSurface} onChange={(event) => setEditSurface(event.target.value)}>
                  <option value="sintetico">Sintético</option><option value="parquet">Parquet</option>
                </select>
                <label className="label cursor-pointer gap-1">
                  <input className="checkbox checkbox-xs" type="checkbox" checked={editCovered} onChange={(event) => setEditCovered(event.target.checked)} />
                  <span className="label-text">Techada</span>
                </label>
                <button className="btn btn-ghost btn-xs" disabled={busy} onClick={() => mutate(async () => {
                  await request(`/api/complejos/${complex.id_complejo}/canchas/${encodeURIComponent(court.nombre_cancha)}`, {
                    method: "PATCH",
                    body: JSON.stringify({ superficie: editSurface, techada: editCovered }),
                  });
                  setEditingCourt("");
                })}>Guardar</button>
                <button className="btn btn-ghost btn-xs" onClick={() => setEditingCourt("")}>Cancelar</button>
              </>
            ) : (
              <>
                <span className="text-sm text-base-content/60">{court.superficie} · {court.techada ? "techada" : "abierta"}</span>
                {isAdmin && <button className="btn btn-ghost btn-xs" onClick={() => {
                  setEditingCourt(court.nombre_cancha);
                  setEditSurface(court.superficie);
                  setEditCovered(court.techada);
                }}>Editar</button>}
                {isAdmin && <button
                  className="btn btn-ghost btn-xs text-error"
                  aria-label={`Eliminar cancha ${court.nombre_cancha}`}
                  disabled={busy}
                  onClick={() => window.confirm(`¿Eliminar ${court.nombre_cancha}?`) && mutate(
                    () => request(`/api/complejos/${complex.id_complejo}/canchas/${encodeURIComponent(court.nombre_cancha)}`, { method: "DELETE" }),
                  )}
                >Eliminar</button>}
              </>
            )}
          </div>
        ))}
        {!courts.length && <span className="text-sm text-base-content/60">No hay canchas en este complejo.</span>}
      </div>
    </div>
  );
}

export default function ManagementPage({ resource }) {
  const config = resources[resource];
  const isAdmin = localStorage.getItem("rol") === "administrador";
  const [rows, setRows] = useState([]);
  const [relations, setRelations] = useState({});
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState(null);
  const [expanded, setExpanded] = useState("");

  async function reload() {
    setRows(await request(config.endpoint));
  }

  useEffect(() => {
    let active = true;
    Promise.all([
      request(config.endpoint),
      request("/api/torneos?limit=200"),
      request("/api/facultades?limit=200"),
    ])
      .then(([data, torneos, facultades]) => {
        if (!active) return;
        setRows(data);
        setRelations({ torneos, facultades });
      })
      .catch((err) => { if (active) setError(err.message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [config.endpoint]);

  const visibleRows = useMemo(() => {
    const query = repairEncoding(search.trim()).toLocaleLowerCase();
    if (!query) return rows;
    return rows.filter((row) =>
      config.columns.some(([key]) => cellValue(row, key).toLocaleLowerCase().includes(query)),
    );
  }, [config.columns, rows, search]);

  async function saveRecord(body) {
    const url = editing.record ? `${config.collection}/${editing.record[config.id]}` : config.collection;
    await request(url, {
      method: editing.record ? config.method : "POST",
      body: JSON.stringify(body),
    });
    setEditing(null);
    await reload();
  }

  async function deleteRecord(row) {
    if (!window.confirm(`¿Eliminar este registro de ${config.title.toLocaleLowerCase()}?`)) return;
    setError("");
    try {
      await request(`${config.collection}/${row[config.id]}`, { method: "DELETE" });
      await reload();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section>
      <div className="mb-7 flex flex-col justify-between gap-5 sm:mb-9 sm:flex-row sm:items-end">
        <div>
          <p className="mb-2 text-sm font-semibold uppercase tracking-[0.14em] text-[#248C7E]">Administración</p>
          <h1 className="!m-0 !text-3xl !font-bold !tracking-tight text-base-content sm:!text-4xl">{config.title}</h1>
        </div>
        <div className="flex items-center gap-3">
          <span className="rounded-xl border border-base-200 bg-base-100 px-4 py-2.5 text-sm text-base-content/60 shadow-sm">
            {loading ? "Cargando..." : `${visibleRows.length} registros`}
          </span>
          {isAdmin && <button className="btn bg-[#248C7E] text-white" onClick={() => setEditing({ record: null })}>Agregar</button>}
        </div>
      </div>

      {error && <div role="alert" className="alert alert-error mb-4"><span>{display(error)}</span></div>}
      <div className="overflow-hidden rounded-2xl border border-base-200 bg-base-100 shadow-sm">
        <div className="flex flex-col gap-4 border-b border-base-200 p-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <div>
            <h2 className="!mb-1 !text-base !font-semibold text-base-content">Listado de {config.title.toLocaleLowerCase()}</h2>
          </div>
          <label className="input input-bordered flex w-full items-center gap-2 bg-base-100 sm:max-w-xs">
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

        {loading ? (
          <div className="flex min-h-56 items-center justify-center gap-3 text-sm text-base-content/55">
            <span className="loading loading-spinner loading-md text-[#248C7E]" />
            Cargando información...
          </div>
        ) : visibleRows.length === 0 ? (
          <div className="flex min-h-56 flex-col items-center justify-center px-6 text-center">
            <p className="font-semibold text-base-content">{rows.length ? "No hay resultados para esa búsqueda" : `Todavía no hay ${config.title.toLocaleLowerCase()}`}</p>
            <p className="mt-1 text-sm text-base-content/55">{rows.length ? "Probá con otro nombre o término." : "Cuando se agreguen registros, aparecerán en este listado."}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="table table-zebra">
              <thead><tr>{config.columns.map(([, title]) => <th key={title}>{title}</th>)}{(isAdmin || resource === "equipos" || resource === "complejos") && <th>Acciones</th>}</tr></thead>
              <tbody>
                {visibleRows.map((row) => {
                  const key = row[config.id];
                  const canExpand = resource === "equipos" || resource === "complejos" || resource === "torneos";
                  return (
                    <FragmentRows
                      key={key}
                      rowKey={key}
                      row={row}
                      config={config}
                      isAdmin={isAdmin}
                      canExpand={canExpand}
                      expanded={expanded === String(key)}
                      onToggle={() => setExpanded(expanded === String(key) ? "" : String(key))}
                      onEdit={() => setEditing({ record: row })}
                      onDelete={() => deleteRecord(row)}
                      onRefresh={() => reload().catch((err) => setError(err.message))}
                    />
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
      {editing && (
        <RecordForm
          config={config}
          record={editing.record}
          relations={relations}
          onClose={() => setEditing(null)}
          onSave={saveRecord}
        />
      )}
    </section>
  );
}

function FragmentRows({ rowKey, row, config, isAdmin, canExpand, expanded, onToggle, onEdit, onDelete, onRefresh }) {
  return (
    <>
      <tr>
        {config.columns.map(([key]) => (
          <td key={key} className="whitespace-nowrap">
            {key === "estado" ? (
              <span className={`badge ${row.estado === "en curso" ? "badge-success" : row.estado === "finalizado" ? "badge-neutral" : "badge-outline"}`}>{cellValue(row, key)}</span>
            ) : cellValue(row, key)}
          </td>
        ))}
        {(isAdmin || canExpand) && (
          <td className="whitespace-nowrap">
            <div className="flex items-center gap-1.5">
              {canExpand && <button className="btn btn-ghost btn-xs" onClick={onToggle}>{expanded ? "Cerrar" : resourceLabel(config)}</button>}
              {isAdmin && <button className="btn btn-ghost btn-xs" onClick={onEdit}>Editar</button>}
              {isAdmin && <button className="btn btn-ghost btn-xs text-error" onClick={onDelete}>Eliminar</button>}
            </div>
          </td>
        )}
      </tr>
      {expanded && (
        <tr><td colSpan={config.columns.length + 1} className="p-0">
          {config.id === "id_equipo"
            ? <TeamRoster key={rowKey} team={row} isAdmin={isAdmin} onTeamUpdate={onRefresh} />
            : config.id === "id_torneo"
              ? <TournamentMatches key={rowKey} tournamentId={row.id_torneo} />
            : <Courts key={rowKey} complex={row} isAdmin={isAdmin} />}
        </td></tr>
      )}
    </>
  );
}

function resourceLabel(config) {
  if (config.id === "id_equipo") return "Plantel";
  if (config.id === "id_torneo") return "Ver partidos";
  return "Canchas";
}

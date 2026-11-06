import { useEffect, useState } from "react";
import { apiFetch } from "./api";
import { repairEncoding } from "./text";

async function request(url, options) {
  const response = await apiFetch(url, options);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = Array.isArray(body.detail) ? body.detail.map((item) => item.msg).join(". ") : body.detail;
    throw new Error(detail || "No se pudo completar la operación.");
  }
  return response.status === 204 ? null : response.json();
}

function display(value) {
  return typeof value === "string" ? repairEncoding(value) : value ?? "—";
}

function SanctionForm({ record, tournaments, onClose, onSave }) {
  const [values, setValues] = useState(record ? {
    ci_jugador: record.ci_jugador,
    id_torneo: record.id_torneo,
    numero_fecha_inicio: record.numero_fecha_inicio,
    cantidad_fechas: record.cantidad_fechas,
  } : {
    ci_jugador: "",
    id_torneo: tournaments[0]?.id_torneo || "",
    numero_fecha_inicio: "",
    cantidad_fechas: "1",
  });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [candidateData, setCandidateData] = useState({ tournamentId: "", players: [] });
  const playersLoading = !record
    && Boolean(values.id_torneo)
    && String(candidateData.tournamentId) !== String(values.id_torneo);
  const eligiblePlayers = String(candidateData.tournamentId) === String(values.id_torneo)
    ? candidateData.players
    : [];

  function update(key, value) {
    setValues((current) => ({ ...current, [key]: value }));
  }

  useEffect(() => {
    if (record || !values.id_torneo) return undefined;

    let active = true;
    request(`/api/sanciones/candidatos?id_torneo=${encodeURIComponent(values.id_torneo)}`)
      .then((rows) => {
        if (active) setCandidateData({ tournamentId: values.id_torneo, players: rows });
      })
      .catch((err) => { if (active) setError(err.message); });
    return () => { active = false; };
  }, [record, values.id_torneo]);

  async function submit(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    const body = Object.fromEntries(Object.entries(values).map(([key, value]) => [key, Number(value)]));
    if (record) {
      delete body.ci_jugador;
      delete body.id_torneo;
    }
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
        <h2 className="!mb-5 !text-xl !font-bold text-base-content">{record ? "Editar sanción disciplinaria" : "Aplicar sanción disciplinaria"}</h2>
        <form onSubmit={submit} className="space-y-4">
          {!record && <>
            <label className="form-control">
              <span className="label-text mb-1">Jugador</span>
              <select className="select select-bordered w-full" required disabled={playersLoading || eligiblePlayers.length === 0} value={values.ci_jugador} onChange={(event) => update("ci_jugador", event.target.value)}>
                <option value="">Seleccioná...</option>
                {eligiblePlayers.map((player) => <option key={player.ci} value={player.ci}>{display(player.nombre)} {display(player.apellido)} · {player.ci}</option>)}
              </select>
              {!playersLoading && eligiblePlayers.length === 0 && <span className="mt-1 text-sm text-base-content/60">No hay jugadores inscriptos en equipos de este torneo.</span>}
            </label>
            <label className="form-control">
              <span className="label-text mb-1">Torneo</span>
              <select className="select select-bordered w-full" required value={values.id_torneo} onChange={(event) => {
                update("id_torneo", event.target.value);
                update("ci_jugador", "");
                setCandidateData({ tournamentId: "", players: [] });
              }}>
                <option value="">Seleccioná...</option>
                {tournaments.map((tournament) => <option key={tournament.id_torneo} value={tournament.id_torneo}>{display(tournament.nombre)} — {tournament.anio}, S{tournament.semestre}</option>)}
              </select>
            </label>
          </>}
          <label className="form-control">
            <span className="label-text mb-1">Fecha de inicio</span>
            <input className="input input-bordered" type="number" min="1" max="50" required value={values.numero_fecha_inicio} onChange={(event) => update("numero_fecha_inicio", event.target.value)} />
          </label>
          <label className="form-control">
            <span className="label-text mb-1">Cantidad de fechas</span>
            <input className="input input-bordered" type="number" min="1" max="20" required value={values.cantidad_fechas} onChange={(event) => update("cantidad_fechas", event.target.value)} />
          </label>
          {error && <div role="alert" className="alert alert-error"><span>{display(error)}</span></div>}
          <div className="modal-action">
            <button type="button" className="btn btn-ghost" onClick={onClose}>Cancelar</button>
            <button className="btn bg-[#248C7E] text-white" disabled={saving}>{saving ? "Guardando..." : "Guardar"}</button>
          </div>
        </form>
      </div>
      <form method="dialog" className="modal-backdrop"><button aria-label="Cerrar" onClick={onClose}>close</button></form>
    </dialog>
  );
}

export default function SanctionsPage() {
  const [sanctions, setSanctions] = useState([]);
  const [tournaments, setTournaments] = useState([]);
  const [editing, setEditing] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function reload() {
    setSanctions(await request("/api/sanciones?limit=200"));
  }

  useEffect(() => {
    let active = true;
    Promise.all([
      request("/api/sanciones?limit=200"),
      request("/api/torneos?limit=200"),
    ])
      .then(([items, tournamentRows]) => {
        if (!active) return;
        setSanctions(items);
        setTournaments(tournamentRows);
      })
      .catch((err) => { if (active) setError(err.message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  async function save(body) {
    const url = editing.record ? `/api/sanciones/${editing.record.id_sancion}` : "/api/sanciones";
    await request(url, { method: editing.record ? "PATCH" : "POST", body: JSON.stringify(body) });
    setEditing(null);
    await reload();
  }

  async function remove(sanction) {
    if (!window.confirm(`¿Eliminar la sanción disciplinaria de ${display(sanction.jugador)}?`)) return;
    setError("");
    try {
      await request(`/api/sanciones/${sanction.id_sancion}`, { method: "DELETE" });
      await reload();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section>
      <div className="mb-7 flex flex-wrap items-end justify-between gap-4">
        <div><p className="mb-2 text-sm font-semibold uppercase tracking-[0.14em] text-[#248C7E]">Administración</p><h1 className="!m-0 !text-3xl !font-bold text-base-content">Sanciones</h1><p className="mt-2 text-sm text-base-content/60">Las sanciones automáticas se originan en tarjetas; las disciplinarias las registra la organización.</p></div>
        <button className="btn bg-[#248C7E] text-white" onClick={() => setEditing({ record: null })}>Aplicar sanción</button>
      </div>
      {error && <div role="alert" className="alert alert-error mb-4"><span>{display(error)}</span></div>}
      <div className="overflow-x-auto rounded-2xl border border-base-200 bg-base-100 shadow-sm">
        <table className="table table-zebra">
          <thead><tr><th>Jugador</th><th>Torneo</th><th>Motivo</th><th>Desde</th><th>Hasta</th><th>Acciones</th></tr></thead>
          <tbody>{sanctions.map((sanction) => (
            <tr key={sanction.id_sancion}>
              <td>{display(sanction.jugador)}</td>
              <td>{display(sanction.torneo)}</td>
              <td>{sanction.motivo === "roja" ? "Tarjeta roja" : sanction.motivo === "acumulacion de amarillas" ? "Acumulación de amarillas" : "Disciplinaria"}</td>
              <td>{sanction.numero_fecha_inicio}</td>
              <td>{sanction.numero_fecha_fin}</td>
              <td className="whitespace-nowrap">
                {sanction.motivo === "disciplinaria" ? <>
                  <button className="btn btn-ghost btn-xs" onClick={() => setEditing({ record: sanction })}>Editar</button>
                  <button className="btn btn-ghost btn-xs text-error" onClick={() => remove(sanction)}>Eliminar</button>
                </> : <span className="text-xs text-base-content/55">Automática · se corrige en el partido</span>}
              </td>
            </tr>
          ))}</tbody>
        </table>
        {!loading && sanctions.length === 0 && <p className="p-8 text-center text-sm text-base-content/60">No hay sanciones registradas.</p>}
        {loading && <div className="p-8 text-center"><span className="loading loading-spinner text-[#248C7E]" /></div>}
      </div>
      {editing && <SanctionForm record={editing.record} tournaments={tournaments} onClose={() => setEditing(null)} onSave={save} />}
    </section>
  );
}

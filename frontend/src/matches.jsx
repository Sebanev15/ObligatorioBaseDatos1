import { Fragment, useCallback, useEffect, useMemo, useState } from "react";
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

const matchStatusLabels = {
  programado: "Programado",
  jugado: "Finalizado",
  postergado: "Postergado",
  cancelado: "Cancelado",
};

function GoalIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 100 100" className="size-7 shrink-0" fill="none">
      <circle cx="50" cy="50" r="44" fill="white" stroke="currentColor" strokeWidth="6" />
      <path
        d="m50 31 18 13-7 21H39l-7-21 18-13Zm0 0V7m18 37 22-8M61 65l15 19M39 65 24 84M32 44 10 36"
        fill="none"
        stroke="currentColor"
        strokeWidth="6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function CardIcon({ color }) {
  const isRed = color === "roja";
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 16 22"
      className={`size-4 ${isRed ? "text-red-500" : "text-yellow-400"}`}
    >
      <rect x="2" y="1" width="12" height="20" rx="2" fill="currentColor" />
    </svg>
  );
}

function MatchSheet({ match }) {
  const [teamId, setTeamId] = useState(null);
  const [sheet, setSheet] = useState([]);
  const [goals, setGoals] = useState([]);
  const [cards, setCards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    Promise.all([
      request(`/api/partidos/${match.id_partido}/planilla`),
      request(`/api/partidos/${match.id_partido}/goles`),
      request(`/api/partidos/${match.id_partido}/tarjetas`),
    ])
      .then(([players, matchGoals, matchCards]) => {
        if (!active) return;
        setSheet(players);
        setGoals(matchGoals);
        setCards(matchCards);
      })
      .catch((err) => { if (active) setError(err.message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [match.id_partido]);

  const teams = [
    { id: match.id_equipo_local, name: match.equipo_local },
    { id: match.id_equipo_visitante, name: match.equipo_visitante },
  ];

  return (
    <div className="space-y-4 border-t border-base-200 bg-base-200/30 p-4 sm:p-5">
      <div className="flex flex-wrap gap-2" aria-label="Equipos del partido">
        {teams.map((team) => (
          <button
            type="button"
            key={team.id}
            className={`btn btn-sm ${String(teamId) === String(team.id) ? "bg-[#248C7E] text-white" : "btn-outline"}`}
            aria-pressed={String(teamId) === String(team.id)}
            onClick={() => setTeamId(team.id)}
          >
            {display(team.name)}
          </button>
        ))}
      </div>
      {loading ? (
        <p className="text-sm text-base-content/60">Cargando planilla...</p>
      ) : error ? (
        <div role="alert" className="alert alert-error py-2"><span>{display(error)}</span></div>
      ) : teamId === null ? (
        <p className="text-sm text-base-content/60">Seleccioná un equipo para ver los jugadores que participaron.</p>
      ) : (
        <ul className="divide-y divide-base-200 rounded-xl bg-base-100 px-4">
          {sheet.filter((player) => String(player.id_equipo) === String(teamId)).map((player) => {
            const playerGoals = goals.filter((goal) => goal.ci_jugador === player.ci_jugador)
              .sort((a, b) => a.minuto - b.minuto);
            const playerCards = cards.filter((card) => card.ci_jugador === player.ci_jugador)
              .sort((a, b) => a.minuto - b.minuto);
            return (
              <li key={player.ci_jugador} className="flex flex-wrap items-center justify-between gap-3 py-3">
                <span className="font-medium">{display(player.jugador)}</span>
                <span className="flex flex-wrap items-center gap-3 text-sm text-base-content/80">
                  {playerGoals.map((goal) => (
                    <span
                      key={`goal-${goal.id_gol}`}
                      className="inline-flex items-center gap-1"
                      title={`Gol a los ${goal.minuto}${goal.autogol ? " (autogol)" : ""}`}
                    >
                      <GoalIcon />
                      <span>{goal.minuto}'{goal.autogol ? " · AG" : ""}</span>
                    </span>
                  ))}
                  {playerCards.map((card) => (
                    <span
                      key={`card-${card.id_tarjeta}`}
                      className="inline-flex items-center gap-1"
                      title={`Tarjeta ${display(card.color)} a los ${card.minuto}`}
                    >
                      <CardIcon color={card.color} />
                      <span>{card.minuto}'</span>
                    </span>
                  ))}
                  {!playerGoals.length && !playerCards.length && <span className="text-base-content/40">Sin goles ni tarjetas</span>}
                </span>
              </li>
            );
          })}
          {!sheet.some((player) => String(player.id_equipo) === String(teamId)) && (
            <li className="py-4 text-sm text-base-content/60">No hay jugadores registrados en la planilla de este equipo.</li>
          )}
        </ul>
      )}
    </div>
  );
}

export function TournamentMatches({ tournamentId }) {
  const [matches, setMatches] = useState([]);
  const [statusFilter, setStatusFilter] = useState("todos");
  const [expandedMatch, setExpandedMatch] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    request(`/api/partidos?id_torneo=${encodeURIComponent(tournamentId)}`)
      .then((data) => { if (active) setMatches(data); })
      .catch((err) => { if (active) setError(err.message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [tournamentId]);

  const visibleMatches = statusFilter === "todos"
    ? matches
    : matches.filter((match) => match.estado === statusFilter);

  return (
    <section className="space-y-4 bg-base-200/30 p-4 sm:p-5" aria-label="Partidos del torneo">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="!mb-1 !text-xl !font-bold text-base-content">Partidos del torneo</h2>
          <p className="text-sm text-base-content/60">Seleccioná un partido y luego un equipo para consultar su planilla.</p>
        </div>
        <label className="form-control">
          <span className="label-text mb-1">Filtrar por estado</span>
          <select
            className="select select-bordered select-sm min-w-44"
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
          >
            <option value="todos">Todos los estados</option>
            {Object.entries(matchStatusLabels).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </label>
      </div>
      {loading ? (
        <p className="py-3 text-sm text-base-content/60">Cargando partidos...</p>
      ) : error ? (
        <div role="alert" className="alert alert-error py-2"><span>{display(error)}</span></div>
      ) : visibleMatches.length ? (
        <div className="space-y-2">
          {visibleMatches.map((match) => {
            const isExpanded = expandedMatch === match.id_partido;
            return (
              <article key={match.id_partido} className="overflow-hidden rounded-xl border border-base-200 bg-base-100">
                <button
                  type="button"
                  className="flex w-full flex-wrap items-center justify-between gap-3 p-4 text-left transition hover:bg-base-200/50"
                  aria-expanded={isExpanded}
                  onClick={() => setExpandedMatch(isExpanded ? null : match.id_partido)}
                >
                  <span className="min-w-0 flex-1">
                    <span className="block text-xs text-base-content/55">Fecha {match.numero_fecha} · {display(match.dia)} · {match.hora_inicio?.slice(0, 5)}</span>
                    <span className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 font-semibold">
                      <span>{display(match.equipo_local)}</span>
                      <span className="text-xs font-medium uppercase tracking-wide text-base-content/45">vs</span>
                      <span>{display(match.equipo_visitante)}</span>
                      {match.estado === "jugado" && (
                        <span className="ml-1 rounded-lg bg-base-200 px-2 py-0.5 tabular-nums">
                          {match.goles_local}:{match.goles_visitante}
                        </span>
                      )}
                    </span>
                  </span>
                  <span className={`badge ${match.estado === "jugado" ? "badge-success" : match.estado === "cancelado" ? "badge-error" : match.estado === "postergado" ? "badge-warning" : "badge-outline"}`}>
                    {matchStatusLabels[match.estado] || display(match.estado)}
                  </span>
                  <span className="text-sm text-base-content/50">{isExpanded ? "Cerrar" : "Ver planilla"}</span>
                </button>
                {isExpanded && <MatchSheet match={match} />}
              </article>
            );
          })}
        </div>
      ) : (
        <p className="rounded-xl border border-dashed border-base-300 p-6 text-center text-sm text-base-content/60">
          {matches.length ? "No hay partidos con ese estado." : "Este torneo todavía no tiene partidos programados."}
        </p>
      )}
    </section>
  );
}

function MatchForm({ record, options, onClose, onSaved }) {
  const [values, setValues] = useState(() => record ? {
    id_torneo: record.id_torneo,
    numero_fecha: record.numero_fecha,
    id_equipo_local: record.id_equipo_local,
    id_equipo_visitante: record.id_equipo_visitante,
    dia: record.dia,
    id_turno: record.id_turno,
    nombre_cancha: record.nombre_cancha,
    id_complejo: record.id_complejo,
  } : {
    id_torneo: options.torneos[0]?.id_torneo || "",
    numero_fecha: "",
    id_equipo_local: "",
    id_equipo_visitante: "",
    dia: "",
    id_turno: options.turnos[0]?.id_turno || "",
    nombre_cancha: "",
    id_complejo: options.complejos[0]?.id_complejo || "",
  });
  const [courts, setCourts] = useState([]);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const teams = options.equipos.filter((team) => String(team.id_torneo) === String(values.id_torneo));

  useEffect(() => {
    if (!values.id_complejo) return;
    let active = true;
    request(`/api/complejos/${values.id_complejo}/canchas`)
      .then((data) => { if (active) setCourts(data); })
      .catch((err) => { if (active) setError(err.message); });
    return () => { active = false; };
  }, [values.id_complejo]);

  function update(key, value) {
    setValues((current) => ({ ...current, [key]: value }));
  }

  async function submit(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    const body = Object.fromEntries(Object.entries(values).map(([key, value]) => [
      key,
      ["dia", "nombre_cancha"].includes(key) ? value : Number(value),
    ]));
    if (record) delete body.id_torneo;
    try {
      await request(record ? `/api/partidos/${record.id_partido}` : "/api/partidos", {
        method: record ? "PATCH" : "POST",
        body: JSON.stringify(body),
      });
      await onSaved();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  const field = (key, label, list, getValue, getLabel, disabled = false) => (
    <label className="form-control" key={key}>
      <span className="label-text mb-1">{label}</span>
      <select className="select select-bordered w-full" value={values[key]} required disabled={disabled} onChange={(event) => {
        update(key, event.target.value);
        if (key === "id_complejo") update("nombre_cancha", "");
        if (key === "id_torneo") {
          update("id_equipo_local", "");
          update("id_equipo_visitante", "");
        }
      }}>
        <option value="">Seleccioná...</option>
        {list.map((item) => <option key={getValue(item)} value={getValue(item)}>{getLabel(item)}</option>)}
      </select>
    </label>
  );

  return (
    <dialog open className="modal modal-open">
      <div className="modal-box max-w-2xl">
        <h2 className="!mb-5 !text-xl !font-bold text-base-content">{record ? "Reprogramar partido" : "Programar partido"}</h2>
        <form onSubmit={submit} className="grid gap-4 sm:grid-cols-2">
          {!record && field("id_torneo", "Torneo", options.torneos, (item) => item.id_torneo, (item) => `${display(item.nombre)} — ${item.anio}, S${item.semestre}`)}
          <label className="form-control">
            <span className="label-text mb-1">Fecha del torneo</span>
            <input className="input input-bordered" type="number" min="1" required value={values.numero_fecha} onChange={(event) => update("numero_fecha", event.target.value)} />
          </label>
          {field("id_equipo_local", "Equipo local", teams, (item) => item.id_equipo, (item) => item.nombre)}
          {field("id_equipo_visitante", "Equipo visitante", teams, (item) => item.id_equipo, (item) => item.nombre)}
          <label className="form-control">
            <span className="label-text mb-1">Día</span>
            <input className="input input-bordered" type="date" required value={values.dia} onChange={(event) => update("dia", event.target.value)} />
          </label>
          {field("id_turno", "Turno", options.turnos, (item) => item.id_turno, (item) => `${item.hora_inicio}–${item.hora_fin}`)}
          {field("id_complejo", "Complejo", options.complejos, (item) => item.id_complejo, (item) => item.nombre)}
          {field("nombre_cancha", "Cancha", courts, (item) => item.nombre_cancha, (item) => item.nombre_cancha, !values.id_complejo)}
          {error && <div role="alert" className="alert alert-error sm:col-span-2"><span>{display(error)}</span></div>}
          <div className="modal-action sm:col-span-2">
            <button type="button" className="btn btn-ghost" onClick={onClose}>Cancelar</button>
            <button type="submit" className="btn bg-[#248C7E] text-white" disabled={saving}>{saving ? "Guardando..." : "Guardar"}</button>
          </div>
        </form>
      </div>
      <form method="dialog" className="modal-backdrop"><button aria-label="Cerrar" onClick={onClose}>close</button></form>
    </dialog>
  );
}

function MatchEvents({ match, isAdmin }) {
  const [sheet, setSheet] = useState([]);
  const [goals, setGoals] = useState([]);
  const [cards, setCards] = useState([]);
  const [squad, setSquad] = useState([]);
  const [selectedTeamId, setSelectedTeamId] = useState(String(match.id_equipo_local));
  const [lineupCI, setLineupCI] = useState("");
  const [goalCI, setGoalCI] = useState("");
  const [cardCI, setCardCI] = useState("");
  const [goalMinute, setGoalMinute] = useState("");
  const [cardMinute, setCardMinute] = useState("");
  const [auto, setAuto] = useState(false);
  const [color, setColor] = useState("amarilla");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const base = `/api/partidos/${match.id_partido}`;
  const teams = useMemo(() => [
    { id_equipo: match.id_equipo_local, equipo: match.equipo_local },
    { id_equipo: match.id_equipo_visitante, equipo: match.equipo_visitante },
  ], [match.id_equipo_local, match.id_equipo_visitante, match.equipo_local, match.equipo_visitante]);
  const selectedTeam = teams.find((team) => String(team.id_equipo) === selectedTeamId);
  const teamSheet = sheet.filter((player) => String(player.id_equipo) === selectedTeamId);
  const teamSquad = squad.filter((player) => String(player.id_equipo) === selectedTeamId);
  const teamGoals = goals.filter((goal) => String(goal.id_equipo) === selectedTeamId);
  const teamCards = cards.filter((card) => String(card.id_equipo) === selectedTeamId);

  const loadData = useCallback(async () => {
    const [players, matchGoals, matchCards, ...rosters] = await Promise.all([
      request(`${base}/planilla`),
      request(`${base}/goles`),
      request(`${base}/tarjetas`),
      ...teams.map((team) => request(`/api/equipos/${team.id_equipo}/jugadores`)),
    ]);
    return {
      players,
      matchGoals,
      matchCards,
      squad: rosters.flatMap((roster, index) => roster.map((player) => ({
        ...player,
        id_equipo: teams[index].id_equipo,
        equipo: teams[index].equipo,
      }))),
    };
  }, [base, teams]);

  const applyData = useCallback((data) => {
    setSheet(data.players);
    setGoals(data.matchGoals);
    setCards(data.matchCards);
    setSquad(data.squad);
  }, []);

  const reload = useCallback(async () => {
    applyData(await loadData());
  }, [applyData, loadData]);

  useEffect(() => {
    let active = true;
    loadData()
      .then((data) => { if (active) applyData(data); })
      .catch((err) => { if (active) setError(err.message); });
    return () => { active = false; };
  }, [applyData, loadData]);

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

  async function addSheetPlayer(event) {
    event.preventDefault();
    const player = teamSquad.find((item) => String(item.ci) === lineupCI);
    if (!player) return;
    await mutate(async () => {
      await request(`${base}/planilla`, { method: "POST", body: JSON.stringify({ ci_jugador: Number(lineupCI), id_equipo: player.id_equipo }) });
      setLineupCI("");
    });
  }

  async function addGoal(event) {
    event.preventDefault();
    await mutate(async () => {
      await request(`${base}/goles`, { method: "POST", body: JSON.stringify({ ci_jugador: Number(goalCI), minuto: Number(goalMinute), autogol: auto }) });
      setGoalMinute("");
      setAuto(false);
    });
  }

  async function addCard(event) {
    event.preventDefault();
    await mutate(async () => {
      await request(`${base}/tarjetas`, { method: "POST", body: JSON.stringify({ ci_jugador: Number(cardCI), minuto: Number(cardMinute), color }) });
      setCardMinute("");
    });
  }

  async function deleteEvent(url, message) {
    if (window.confirm(message)) await mutate(() => request(url, { method: "DELETE" }));
  }

  async function editGoal(goal) {
    const value = window.prompt("Minuto del gol", goal.minuto);
    if (value === null || !/^\d+$/.test(value) || Number(value) > 130) return;
    await mutate(() => request(`${base}/goles/${goal.id_gol}`, {
      method: "PATCH",
      body: JSON.stringify({ minuto: Number(value), autogol: goal.autogol }),
    }));
  }

  async function editCard(card) {
    const value = window.prompt("Minuto de la tarjeta", card.minuto);
    if (value === null || !/^\d+$/.test(value) || Number(value) > 130) return;
    const newColor = window.prompt("Color: amarilla o roja", card.color);
    if (newColor === null || !["amarilla", "roja"].includes(newColor)) return;
    await mutate(() => request(`${base}/tarjetas/${card.id_tarjeta}`, {
      method: "PATCH",
      body: JSON.stringify({ minuto: Number(value), color: newColor }),
    }));
  }

  const listedCI = new Set(teamSheet.map((player) => String(player.ci_jugador)));
  const eligible = teamSquad.filter((player) => !listedCI.has(String(player.ci)));

  return (
    <div className="space-y-5 bg-base-200/30 p-4">
      {error && <div role="alert" className="alert alert-error"><span>{display(error)}</span></div>}
      {match.estado === "jugado" && !isAdmin && <p className="text-sm text-base-content/60">La planilla se puede corregir hasta 48 horas después del partido.</p>}
      <label className="form-control max-w-md">
        <span className="label-text mb-1">Equipo a gestionar</span>
        <select
          className="select select-bordered"
          value={selectedTeamId}
          onChange={(event) => {
            setSelectedTeamId(event.target.value);
            setLineupCI("");
            setGoalCI("");
            setCardCI("");
          }}
        >
          {teams.map((team) => <option key={team.id_equipo} value={team.id_equipo}>{display(team.equipo)}</option>)}
        </select>
      </label>
      <form className="flex flex-wrap items-end gap-3" onSubmit={addSheetPlayer}>
        <label className="form-control min-w-64">
          <span className="label-text mb-1">Agregar jugador a la planilla</span>
          <select className="select select-bordered select-sm" value={lineupCI} onChange={(event) => setLineupCI(event.target.value)}>
            <option value="">Seleccioná del plantel</option>
            {eligible.map((player) => <option key={player.ci} value={player.ci}>{display(player.nombre)} {display(player.apellido)}</option>)}
          </select>
        </label>
        <button className="btn btn-sm" disabled={busy || !lineupCI}>Agregar a planilla</button>
      </form>
      <div>
        <h3 className="font-semibold">Planilla de {display(selectedTeam?.equipo)}</h3>
        {!teamSheet.length ? <p className="text-sm text-base-content/60">Todavía no hay jugadores de este equipo en la planilla.</p> : (
          <div className="mt-2 flex flex-wrap gap-2">
            {teamSheet.map((player) => (
              <span className="badge badge-lg gap-2" key={player.ci_jugador}>
                {display(player.jugador)}
                <button
                  type="button"
                  className="btn btn-ghost btn-circle btn-xs text-error"
                  aria-label={`Quitar a ${display(player.jugador)}`}
                  disabled={busy}
                  onClick={() => deleteEvent(`${base}/planilla/${player.ci_jugador}`, `¿Quitar a ${display(player.jugador)} de la planilla?`)}
                >×</button>
              </span>
            ))}
          </div>
        )}
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <form className="space-y-2 rounded-xl border border-base-200 bg-base-100 p-3" onSubmit={addGoal}>
          <h3 className="font-semibold">Registrar gol</h3>
          <select className="select select-bordered select-sm w-full" value={goalCI} onChange={(event) => setGoalCI(event.target.value)}>
            <option value="">Jugador de {display(selectedTeam?.equipo)}</option>
            {teamSheet.map((player) => <option key={player.ci_jugador} value={player.ci_jugador}>{display(player.jugador)}</option>)}
          </select>
          <div className="flex gap-2">
            <input className="input input-bordered input-sm w-28" type="number" min="0" max="130" placeholder="Minuto" value={goalMinute} onChange={(event) => setGoalMinute(event.target.value)} />
            <label className="label cursor-pointer gap-2"><input className="checkbox checkbox-sm" type="checkbox" checked={auto} onChange={(event) => setAuto(event.target.checked)} /><span className="label-text">Autogol</span></label>
            <button className="btn btn-sm" disabled={busy || !goalCI || goalMinute === ""}>Agregar gol</button>
          </div>
          <ul className="divide-y divide-base-200">{teamGoals.map((goal) => (
            <li className="flex items-center justify-between py-2 text-sm" key={goal.id_gol}>
              <span>{goal.minuto}' · {display(goal.jugador)}{goal.autogol ? " (autogol)" : ""}</span>
              <span className="flex gap-1.5"><button type="button" className="btn btn-ghost btn-xs" onClick={() => editGoal(goal)}>Editar</button><button type="button" className="btn btn-ghost btn-xs text-error" onClick={() => deleteEvent(`${base}/goles/${goal.id_gol}`, "¿Eliminar este gol?")}>Eliminar</button></span>
            </li>
          ))}</ul>
        </form>
        <form className="space-y-2 rounded-xl border border-base-200 bg-base-100 p-3" onSubmit={addCard}>
          <h3 className="font-semibold">Registrar tarjeta</h3>
          <select className="select select-bordered select-sm w-full" value={cardCI} onChange={(event) => setCardCI(event.target.value)}>
            <option value="">Jugador de {display(selectedTeam?.equipo)}</option>
            {teamSheet.map((player) => <option key={player.ci_jugador} value={player.ci_jugador}>{display(player.jugador)}</option>)}
          </select>
          <div className="flex flex-wrap gap-2">
            <input className="input input-bordered input-sm w-28" type="number" min="0" max="130" placeholder="Minuto" value={cardMinute} onChange={(event) => setCardMinute(event.target.value)} />
            <select className="select select-bordered select-sm" value={color} onChange={(event) => setColor(event.target.value)}><option value="amarilla">Amarilla</option><option value="roja">Roja</option></select>
            <button className="btn btn-sm" disabled={busy || !cardCI || cardMinute === ""}>Agregar tarjeta</button>
          </div>
          <ul className="divide-y divide-base-200">{teamCards.map((card) => (
            <li className="flex items-center justify-between py-2 text-sm" key={card.id_tarjeta}>
              <span>{card.minuto}' · {display(card.jugador)} · {display(card.color)}</span>
              <span className="flex gap-1.5"><button type="button" className="btn btn-ghost btn-xs" onClick={() => editCard(card)}>Editar</button><button type="button" className="btn btn-ghost btn-xs text-error" onClick={() => deleteEvent(`${base}/tarjetas/${card.id_tarjeta}`, "¿Eliminar esta tarjeta?")}>Eliminar</button></span>
            </li>
          ))}</ul>
        </form>
      </div>
    </div>
  );
}

export default function MatchesPage() {
  const role = localStorage.getItem("rol");
  const isAdmin = role === "administrador";
  const [matches, setMatches] = useState([]);
  const [options, setOptions] = useState({ torneos: [], equipos: [], complejos: [], turnos: [] });
  const [editing, setEditing] = useState(null);
  const [expanded, setExpanded] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function reload() {
    setMatches(await request("/api/partidos"));
  }

  useEffect(() => {
    let active = true;
    Promise.all([
      request("/api/partidos"),
      request("/api/torneos?limit=200"),
      request("/api/equipos?limit=200"),
      request("/api/complejos"),
      request("/api/turnos"),
    ])
      .then(([partidos, torneos, equipos, complejos, turnos]) => {
        if (!active) return;
        setMatches(partidos);
        setOptions({ torneos, equipos, complejos, turnos });
      })
      .catch((err) => { if (active) setError(err.message); });
    return () => { active = false; };
  }, []);

  async function setStatus(match, status) {
    setBusy(true);
    setError("");
    try {
      await request(`/api/partidos/${match.id_partido}/estado`, {
        method: "PATCH",
        body: JSON.stringify({ estado: status }),
      });
      await reload();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function deleteMatch(match) {
    if (!window.confirm(`¿Eliminar el partido ${match.equipo_local} – ${match.equipo_visitante}?`)) return;
    try {
      await request(`/api/partidos/${match.id_partido}`, { method: "DELETE" });
      await reload();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section>
      <div className="mb-7 flex flex-wrap items-end justify-between gap-4">
        <div><p className="mb-2 text-sm font-semibold uppercase tracking-[0.14em] text-[#248C7E]">Competencia</p><h1 className="!m-0 !text-3xl !font-bold text-base-content">Partidos</h1></div>
        {isAdmin && <button className="btn bg-[#248C7E] text-white" onClick={() => setEditing({ record: null })}>Programar partido</button>}
      </div>
      {error && <div role="alert" className="alert alert-error mb-4"><span>{display(error)}</span></div>}
      <div className="overflow-x-auto rounded-2xl border border-base-200 bg-base-100 shadow-sm">
        <table className="table table-zebra">
          <thead><tr><th>Fecha</th><th>Local</th><th>Resultado</th><th>Visitante</th><th>Día y turno</th><th>Complejo / cancha</th><th>Estado</th><th>Acciones</th></tr></thead>
          <tbody>{matches.map((match) => (
            <Fragment key={match.id_partido}>
              <tr>
                <td>{display(match.torneo)} · {match.numero_fecha}</td>
                <td>{display(match.equipo_local)}</td>
                <td>{match.goles_local}–{match.goles_visitante}</td>
                <td>{display(match.equipo_visitante)}</td>
                <td>{match.dia} · {match.hora_inicio?.slice(0, 5)}</td>
                <td>{display(match.complejo)} · {display(match.nombre_cancha)}</td>
                <td>{isAdmin ? (
                <select className="select select-bordered select-xs" value={match.estado} disabled={busy} onChange={(event) => setStatus(match, event.target.value)}>
                  <option value="programado">Programado</option><option value="jugado">Jugado</option><option value="postergado">Postergado</option><option value="cancelado">Cancelado</option>
                </select>
                ) : display(match.estado)}</td>
                <td className="whitespace-nowrap">
                  <div className="flex items-center gap-1.5">
                    <button className="btn btn-ghost btn-xs" onClick={() => setExpanded(expanded === match.id_partido ? null : match.id_partido)}>{expanded === match.id_partido ? "Cerrar" : "Planilla"}</button>
                    {isAdmin && match.estado !== "jugado" && <button className="btn btn-ghost btn-xs" onClick={() => setEditing({ record: match })}>Editar</button>}
                    {isAdmin && match.estado !== "jugado" && <button className="btn btn-ghost btn-xs text-error" onClick={() => deleteMatch(match)}>Eliminar</button>}
                  </div>
                </td>
              </tr>
              {expanded === match.id_partido && <tr key={`${match.id_partido}-events`}><td colSpan="8" className="p-0"><MatchEvents match={match} isAdmin={isAdmin} /></td></tr>}
            </Fragment>
          ))}</tbody>
        </table>
        {!matches.length && <p className="p-8 text-center text-sm text-base-content/60">No hay partidos programados.</p>}
      </div>
      {editing && <MatchForm record={editing.record} options={options} onClose={() => setEditing(null)} onSaved={async () => { setEditing(null); await reload(); }} />}
    </section>
  );
}

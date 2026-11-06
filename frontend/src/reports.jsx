import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "./api";
import { repairEncoding } from "./text";

const reports = [
  { id: "posiciones", label: "Posiciones", route: "posiciones", columns: [["equipo", "Equipo"], ["partidos_jugados", "PJ"], ["partidos_ganados", "PG"], ["partidos_empatados", "PE"], ["partidos_perdidos", "PP"], ["goles_favor", "GF"], ["goles_contra", "GC"], ["diferencia_goles", "DG"], ["puntos", "Puntos"]] },
  { id: "goleadores", label: "Goleadores", route: "goleadores", columns: [["jugador", "Jugador"], ["equipo", "Equipo"], ["facultad", "Facultad"], ["goles", "Goles"]] },
  { id: "fair-play", label: "Fair play", route: "fair-play", columns: [["equipo", "Equipo"], ["tarjetas_amarillas", "Amarillas"], ["tarjetas_rojas", "Rojas"], ["puntos_fair_play", "Puntos de fair play"]] },
  { id: "goles-fecha", label: "Goles por fecha", route: "goles-por-fecha", columns: [["numero_fecha", "Fecha"], ["partidos_jugados", "Partidos jugados"], ["goles", "Goles"], ["promedio_goles", "Promedio de goles"]] },
  { id: "uso", label: "Canchas y turnos", route: "uso-canchas-turnos", kind: "usage" },
  { id: "jugadores-facultad", label: "Jugadores por facultad", route: "jugadores-por-facultad-tipo", global: true, columns: [["facultad", "Facultad"], ["tipo", "Tipo"], ["cantidad_jugadores", "Jugadores"]] },
  { id: "sin-planilla", label: "Sin planilla", route: "jugadores-sin-planilla", columns: [["jugador", "Jugador"], ["ci", "Cédula"], ["equipo", "Equipo"], ["facultad", "Facultad"]] },
  { id: "sanciones", label: "Sanciones por equipo", route: "sanciones-por-equipo-motivo", columns: [["equipo", "Equipo"], ["motivo", "Motivo"], ["cantidad_sanciones", "Sanciones"]] },
  { id: "estado-partidos", label: "Estado de partidos", route: "estado-partidos", kind: "statuses" },
  { id: "localia", label: "Rendimiento local/visitante", route: "resultados-localia", columns: [["resultado", "Resultado"], ["cantidad", "Partidos"]] },
  { id: "tarjetas-fecha", label: "Tarjetas por fecha", route: "promedio-tarjetas-por-fecha", columns: [["numero_fecha", "Fecha"], ["partidos_jugados", "Partidos jugados"], ["tarjetas", "Tarjetas"], ["promedio_tarjetas", "Promedio por partido"]] },
  { id: "goles-facultad", label: "Goles por facultad", route: "goles-por-facultad", columns: [["facultad", "Facultad"], ["goles", "Goles"]] },
];

const valueLabels = {
  grado: "Grado",
  posgrado: "Posgrado",
  docente: "Docente",
  funcionario: "Funcionario",
  roja: "Tarjeta roja",
  "acumulacion de amarillas": "Acumulación de amarillas",
  disciplinaria: "Disciplinaria",
};

function display(value) {
  if (value === null || value === undefined) return "—";
  if (typeof value === "number") return value.toLocaleString("es-UY");
  const cleaned = typeof value === "string" ? repairEncoding(value.trim()) : String(value);
  return valueLabels[cleaned] || cleaned;
}

function DataTable({ title, rows, columns }) {
  return (
    <div className="overflow-hidden rounded-2xl border border-base-200 bg-base-100 shadow-sm">
      <div className="border-b border-base-200 px-5 py-4">
        <h2 className="!m-0 !text-base !font-semibold text-base-content">{title}</h2>
      </div>
      {!rows.length ? (
        <p className="px-5 py-10 text-center text-sm text-base-content/55">No hay datos para mostrar.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="table table-zebra">
            <thead><tr>{columns.map(([, label]) => <th key={label}>{label}</th>)}</tr></thead>
            <tbody>
              {rows.map((row, index) => (
                <tr key={`${row.id_equipo ?? row.id_facultad ?? row.ci ?? row.numero_fecha ?? row.id_turno ?? row.resultado ?? index}-${row.motivo ?? row.tipo ?? ""}`}>
                  {columns.map(([key]) => (
                    <td key={key} className="whitespace-nowrap">{display(row[key])}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function MetricCard({ label, value, detail }) {
  return (
    <div className="rounded-2xl border border-base-200 bg-base-100 p-5 shadow-sm">
      <p className="text-sm font-medium text-base-content/60">{label}</p>
      <p className="mt-2 text-3xl font-semibold tracking-tight text-base-content">{value}</p>
      {detail && <p className="mt-1 text-xs text-base-content/50">{detail}</p>}
    </div>
  );
}

function ReportContent({ report, data }) {
  if (report.kind === "usage") {
    return (
      <div className="grid gap-5 xl:grid-cols-2">
        <DataTable title="Uso de canchas" rows={data.canchas} columns={[["complejo", "Complejo"], ["cancha", "Cancha"], ["partidos_jugados", "Partidos jugados"]]} />
        <DataTable title="Uso de turnos" rows={data.turnos} columns={[["hora_inicio", "Desde"], ["hora_fin", "Hasta"], ["partidos_jugados", "Partidos jugados"]]} />
      </div>
    );
  }

  if (report.kind === "statuses") {
    const stats = data || {};
    return (
      <div className="grid gap-10 sm:grid-cols-2 xl:grid-cols-3">
        <MetricCard label="Partidos jugados" value={`${display(stats.porcentaje_jugados ?? 0)}%`} detail={`${display(stats.jugados ?? 0)} partidos`} />
        <MetricCard label="Postergados" value={`${display(stats.porcentaje_postergados ?? 0)}%`} detail={`${display(stats.postergados ?? 0)} partidos`} />
        <MetricCard label="Cancelados" value={`${display(stats.porcentaje_cancelados ?? 0)}%`} detail={`${display(stats.cancelados ?? 0)} partidos`} />
      </div>
    );
  }

  if (report.id === "goles-fecha") {
    const matches = data.reduce((sum, row) => sum + Number(row.partidos_jugados || 0), 0);
    const goals = data.reduce((sum, row) => sum + Number(row.goles || 0), 0);
    const average = matches ? (goals / matches).toFixed(2) : "0.00";
    return (
      <div className="space-y-5">
        <MetricCard label="Promedio de goles de toda la edición" value={average} detail={`${display(goals)} goles en ${display(matches)} partidos jugados`} />
        <DataTable title="Promedio por fecha" rows={data} columns={report.columns} />
      </div>
    );
  }

  if (report.id === "tarjetas-fecha") {
    return <DataTable title="Promedio de tarjetas por fecha" rows={data} columns={report.columns} />;
  }

  if (report.id === "localia") {
    return <DataTable title="Resultados según localía" rows={data} columns={report.columns} />;
  }

  if (report.id === "goles-facultad") {
    return <DataTable title="Goles por facultad" rows={data} columns={report.columns} />;
  }

  return <DataTable title={report.label} rows={data} columns={report.columns} />;
}

export default function ReportsPage() {
  const [tournaments, setTournaments] = useState([]);
  const [tournamentsError, setTournamentsError] = useState("");
  const [tournamentId, setTournamentId] = useState("");
  const [activeReportId, setActiveReportId] = useState(reports[0].id);
  const [result, setResult] = useState({ key: "", data: null, error: "" });

  useEffect(() => {
    let active = true;
    apiFetch("/api/torneos?limit=200")
      .then(async (response) => {
        if (!response.ok) throw new Error("No se pudieron cargar las ediciones.");
        return response.json();
      })
      .then((data) => {
        if (!active) return;
        setTournaments(data);
        if (data.length) setTournamentId(String(data[0].id_torneo));
      })
      .catch((error) => {
        if (active) setTournamentsError(error.message);
      });
    return () => { active = false; };
  }, []);

  const activeReport = reports.find((report) => report.id === activeReportId) || reports[0];
  const requestUrl = activeReport.global
    ? `/api/reportes/${activeReport.route}`
    : tournamentId
      ? `/api/reportes/${tournamentId}/${activeReport.route}`
      : "";
  const requestKey = `${tournamentId}:${activeReport.id}`;

  useEffect(() => {
    if (!requestUrl) return undefined;
    let active = true;
    apiFetch(requestUrl)
      .then(async (response) => {
        if (!response.ok) {
          const body = await response.json().catch(() => ({}));
          throw new Error(body.detail || "No se pudo generar el reporte.");
        }
        return response.json();
      })
      .then((data) => {
        if (active) setResult({ key: requestKey, data, error: "" });
      })
      .catch((error) => {
        if (active) setResult({ key: requestKey, data: null, error: error.message });
      });
    return () => { active = false; };
  }, [requestUrl, requestKey]);

  const currentResult = result.key === requestKey ? result : null;
  const reportTabs = useMemo(() => reports.map(({ id, label }) => ({ id, label })), []);

  return (
    <section>
      <div className="mb-7 flex flex-col justify-between gap-5 sm:mb-9 lg:flex-row lg:items-end">
        <div>
          <p className="mb-2 text-sm font-semibold uppercase tracking-[0.14em] text-[#248C7E]">Área de deportes</p>
          <h1 className="!m-0 !text-3xl !font-bold !tracking-tight text-base-content sm:!text-4xl">Reportes y métricas</h1>
        </div>
        <label className="form-control w-full lg:max-w-sm">
          <span className="label-text mb-2 font-medium">Edición del torneo</span>
          <select
            className="select select-bordered bg-base-100"
            value={tournamentId}
            onChange={(event) => setTournamentId(event.target.value)}
            disabled={!tournaments.length}
          >
            {tournaments.length ? tournaments.map((tournament) => (
              <option key={tournament.id_torneo} value={tournament.id_torneo}>
                {tournament.nombre} — {tournament.anio}, semestre {tournament.semestre}
              </option>
            )) : <option value="">{tournamentsError ? "No se pudieron cargar las ediciones" : "Cargando ediciones..."}</option>}
          </select>
        </label>
      </div>

      {tournamentsError && <div role="alert" className="alert alert-error mb-5"><span>{tournamentsError}</span></div>}
      {!tournamentsError && tournaments.length === 0 && !tournamentId && (
        <div className="alert mb-5"><span>No hay ediciones registradas para consultar.</span></div>
      )}

      <div role="tablist" aria-label="Reportes disponibles" className="tabs tabs-boxed mb-5 flex w-full flex-nowrap gap-1 overflow-x-auto bg-base-200/70 p-1">
        {reportTabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={activeReportId === tab.id}
            className={`tab shrink-0 ${activeReportId === tab.id ? "tab-active bg-[#248C7E] text-white" : ""}`}
            onClick={() => setActiveReportId(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {currentResult?.error ? (
        <div role="alert" className="alert alert-error"><span>{currentResult.error}</span></div>
      ) : !activeReport.global && !tournamentId ? (
        <div className="rounded-2xl border border-base-200 bg-base-100 px-5 py-10 text-center text-sm text-base-content/55">
          {tournamentsError ? "No se puede generar el reporte sin cargar las ediciones." : "No hay ediciones registradas para consultar."}
        </div>
      ) : !currentResult ? (
        <div className="flex min-h-56 items-center justify-center gap-3 text-sm text-base-content/55">
          <span className="loading loading-spinner loading-md text-[#248C7E]" />
          Generando reporte...
        </div>
      ) : (
        <ReportContent report={activeReport} data={currentResult.data} />
      )}
    </section>
  );
}

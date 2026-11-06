import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import { apiFetch } from "./api";
import { SectionIcon } from "./navigation";

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

export default function Dashboard() {
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
      </div>
      {error && <div role="alert" className="alert alert-error mb-6"><span>{error}</span></div>}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <SummaryCard title="Torneos" count={counts?.torneos ?? null} symbol="tournament" path="/torneos" caption="Competencias registradas" />
        <SummaryCard title="Equipos" count={counts?.equipos ?? null} symbol="team" path="/equipos" caption="Inscritos en los torneos" />
        <SummaryCard title="Jugadores" count={counts?.jugadores ?? null} symbol="player" path="/jugadores" caption="Jugadores registrados" />
        <SummaryCard title="Facultades" count={counts?.facultades ?? null} symbol="faculty" path="/facultades" caption="Participantes registradas" />
      </div>

    </section>
  );
}

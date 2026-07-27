import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { processReel } from "../api.js";
import ResultView from "../components/ResultView.jsx";

const STAGES = [
  "Sto svegliando il server… (può richiedere ~30s al primo avvio)",
  "Scarico l'audio dal reel…",
  "Trascrivo l'audio…",
  "Riscrivo nel tuo tono…",
];

export default function Home() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [url, setUrl] = useState(searchParams.get("url") || "");
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [stage, setStage] = useState(0);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const stageTimer = useRef(null);
  const autoRan = useRef(false);

  function startStages() {
    setStage(0);
    let i = 0;
    stageTimer.current = setInterval(() => {
      i = Math.min(i + 1, STAGES.length - 1);
      setStage(i);
    }, 3500);
  }

  function stopStages() {
    if (stageTimer.current) {
      clearInterval(stageTimer.current);
      stageTimer.current = null;
    }
  }

  async function run(targetUrl) {
    const u = (targetUrl ?? url).trim();
    if (!u) {
      setError("Incolla un link a un reel.");
      return;
    }
    setError("");
    setResult(null);
    setLoading(true);
    startStages();
    try {
      const data = await processReel(u, notes);
      setResult(data);
    } catch (e) {
      setError(e.message || "Qualcosa è andato storto.");
    } finally {
      stopStages();
      setLoading(false);
    }
  }

  // Avvio automatico se arrivo dalla condivisione (/share -> /?url=...&auto=1)
  useEffect(() => {
    const shared = searchParams.get("url");
    const auto = searchParams.get("auto");
    if (shared && auto === "1" && !autoRan.current) {
      autoRan.current = true;
      setUrl(shared);
      // pulisci i parametri per non ri-eseguire su refresh
      setSearchParams({}, { replace: true });
      run(shared);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => () => stopStages(), []);

  return (
    <div className="page">
      <h1 className="title">Trascrivi &amp; Riscrivi</h1>
      <p className="subtitle">
        Incolla un reel: lo trascrivo, lo traduco e lo riscrivo nel tuo tono.
      </p>

      <div className="form">
        <input
          className="input"
          type="url"
          inputMode="url"
          placeholder="https://www.instagram.com/reel/…"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          disabled={loading}
        />
        <textarea
          className="textarea"
          placeholder="Note (opzionali) — utili per la ricerca in archivio"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          disabled={loading}
          rows={2}
        />
        <button className="btn-primary" onClick={() => run()} disabled={loading}>
          {loading ? "Elaboro…" : "Elabora"}
        </button>
      </div>

      {loading ? (
        <div className="status">
          <div className="spinner" />
          <span>{STAGES[stage]}</span>
        </div>
      ) : null}

      {error ? <div className="error">{error}</div> : null}

      <ResultView result={result} />
    </div>
  );
}

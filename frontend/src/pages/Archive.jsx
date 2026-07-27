import { useEffect, useState } from "react";
import { listReels } from "../api.js";
import ResultView from "../components/ResultView.jsx";

function formatDate(iso) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleString("it-IT", {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch (_) {
    return iso;
  }
}

export default function Archive() {
  const [q, setQ] = useState("");
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [openId, setOpenId] = useState(null);

  async function load(query) {
    setLoading(true);
    setError("");
    try {
      const data = await listReels(query);
      setItems(data);
    } catch (e) {
      setError(e.message || "Impossibile caricare l'archivio.");
    } finally {
      setLoading(false);
    }
  }

  // caricamento iniziale
  useEffect(() => {
    load("");
  }, []);

  // ricerca con debounce
  useEffect(() => {
    const t = setTimeout(() => load(q), 350);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q]);

  return (
    <div className="page">
      <h1 className="title">Archivio</h1>

      <input
        className="input"
        type="search"
        placeholder="Cerca nei trascritti, reel e note…"
        value={q}
        onChange={(e) => setQ(e.target.value)}
      />

      {loading ? <div className="muted">Carico…</div> : null}
      {error ? <div className="error">{error}</div> : null}
      {!loading && !error && items.length === 0 ? (
        <div className="muted">Nessun reel in archivio.</div>
      ) : null}

      <ul className="list">
        {items.map((item) => {
          const open = openId === item.id;
          const preview =
            (item.rewritten_reel || item.transcript_it || "").slice(0, 120) ||
            item.source_url;
          return (
            <li key={item.id} className="list-item">
              <button
                className="list-head"
                onClick={() => setOpenId(open ? null : item.id)}
              >
                <span className="list-preview">{preview}</span>
                <span className="list-date">{formatDate(item.created_at)}</span>
              </button>
              {open ? <ResultView result={item} /> : null}
            </li>
          );
        })}
      </ul>
    </div>
  );
}

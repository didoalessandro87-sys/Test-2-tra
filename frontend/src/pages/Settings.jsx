import { useEffect, useState } from "react";
import { getBrand, updateBrand } from "../api.js";

export default function Settings() {
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const data = await getBrand();
        setContent(data.content || "");
      } catch (e) {
        setError(e.message || "Impossibile caricare il profilo brand.");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  async function save() {
    setSaving(true);
    setError("");
    setSaved(false);
    try {
      await updateBrand(content);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (e) {
      setError(e.message || "Salvataggio non riuscito.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="page">
      <h1 className="title">Profilo brand</h1>
      <p className="subtitle">
        Questo testo è il system prompt usato per riscrivere i reel. Modificalo
        per aggiornare tono, tesi e vincoli.
      </p>

      {loading ? (
        <div className="muted">Carico…</div>
      ) : (
        <>
          <textarea
            className="textarea brand-editor"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows={20}
          />
          <button className="btn-primary" onClick={save} disabled={saving}>
            {saving ? "Salvo…" : "Salva"}
          </button>
          {saved ? <div className="ok">Salvato ✓</div> : null}
          {error ? <div className="error">{error}</div> : null}
        </>
      )}
    </div>
  );
}

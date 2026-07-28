import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

// Estrae il primo URL valido da una stringa (Instagram spesso mette il link
// dentro "text" invece che "url").
function extractUrl(...candidates) {
  const re = /https?:\/\/[^\s]+/i;
  for (const c of candidates) {
    if (!c) continue;
    const m = c.match(re);
    if (m) return m[0];
  }
  return "";
}

export default function Share() {
  const [params] = useSearchParams();
  const navigate = useNavigate();

  useEffect(() => {
    const url = extractUrl(
      params.get("url"),
      params.get("text"),
      params.get("title")
    );
    if (url) {
      navigate(`/?url=${encodeURIComponent(url)}&auto=1`, { replace: true });
    } else {
      navigate("/", { replace: true });
    }
  }, [params, navigate]);

  return (
    <div className="page">
      <div className="status">
        <div className="spinner" />
        <span>Ricevo il link condiviso…</span>
      </div>
    </div>
  );
}

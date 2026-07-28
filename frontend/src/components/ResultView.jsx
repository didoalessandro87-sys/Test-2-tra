import CopyButton from "./CopyButton.jsx";

export default function ResultView({ result }) {
  if (!result) return null;
  return (
    <div className="result">
      <section className="card">
        <div className="card-head">
          <h2>Trascritto in italiano</h2>
          <CopyButton text={result.transcript_it} />
        </div>
        <p className="body-text">{result.transcript_it || "—"}</p>
      </section>

      <section className="card">
        <div className="card-head">
          <h2>Reel riscritto nel tuo tono</h2>
          <CopyButton text={result.rewritten_reel} />
        </div>
        <p className="body-text">{result.rewritten_reel || "—"}</p>
      </section>

      {result.source_url ? (
        <p className="source-link">
          Fonte:{" "}
          <a href={result.source_url} target="_blank" rel="noreferrer">
            {result.source_url}
          </a>
          {result.source_lang ? ` · lingua: ${result.source_lang}` : ""}
        </p>
      ) : null}
    </div>
  );
}

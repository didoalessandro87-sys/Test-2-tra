import { useState } from "react";

export default function CopyButton({ text, label = "Copia" }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(text || "");
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch (_) {
      // fallback per browser senza clipboard API
      const ta = document.createElement("textarea");
      ta.value = text || "";
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    }
  }

  return (
    <button type="button" className="copy-btn" onClick={copy}>
      {copied ? "Copiato ✓" : label}
    </button>
  );
}

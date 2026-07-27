const API_BASE = (import.meta.env.VITE_API_BASE || "").replace(/\/$/, "");

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = `Errore ${res.status}`;
    try {
      const body = await res.json();
      if (body && body.detail) detail = body.detail;
    } catch (_) {
      /* ignora */
    }
    const err = new Error(detail);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

export function processReel(url, notes) {
  return request("/process", {
    method: "POST",
    body: JSON.stringify({ url, notes: notes || null }),
  });
}

export function listReels(q) {
  const query = q ? `?q=${encodeURIComponent(q)}` : "";
  return request(`/reels${query}`);
}

export function getReel(id) {
  return request(`/reels/${id}`);
}

export function getBrand() {
  return request("/brand");
}

export function updateBrand(content) {
  return request("/brand", {
    method: "PUT",
    body: JSON.stringify({ content }),
  });
}

export function health() {
  return request("/health");
}

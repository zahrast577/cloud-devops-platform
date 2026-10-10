import { useCallback, useEffect, useState } from "react";

const POLL_INTERVAL_MS = 2000;
const HISTORY_SIZE = 20;

// Donne une couleur stable à chaque nom de pod : deux pods différents
// auront (presque toujours) deux couleurs différentes.
function podColor(hostname) {
  let hash = 0;
  for (const char of hostname) {
    hash = (hash * 31 + char.charCodeAt(0)) % 360;
  }
  return `hsl(${hash} 55% 45%)`;
}

function formatDate(iso) {
  return new Date(iso).toLocaleString("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function App() {
  const [items, setItems] = useState([]);
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [cacheStatus, setCacheStatus] = useState(null);

  const [info, setInfo] = useState(null);
  const [online, setOnline] = useState(true);
  const [latency, setLatency] = useState(null);
  const [history, setHistory] = useState([]);

  const loadItems = useCallback(async () => {
    try {
      const response = await fetch("/api/items");
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      setCacheStatus(response.headers.get("X-Cache"));
      setItems(await response.json());
      setError("");
    } catch {
      setError("La liste est indisponible. Vérifie que l'API tourne.");
    }
  }, []);

  useEffect(() => {
    loadItems();
  }, [loadItems]);

  // Interroge /api/info toutes les 2 secondes : on voit en direct quel pod répond,
  // quelle version tourne, et on constate le load balancing et les rollouts.
  useEffect(() => {
    let active = true;

    async function poll() {
      const start = performance.now();
      try {
        const response = await fetch("/api/info", { cache: "no-store" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        if (!active) return;
        setInfo(data);
        setOnline(true);
        setLatency(Math.round(performance.now() - start));
        setHistory((previous) => [data.hostname, ...previous].slice(0, HISTORY_SIZE));
      } catch {
        if (active) setOnline(false);
      }
    }

    poll();
    const timer = setInterval(poll, POLL_INTERVAL_MS);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, []);

  async function addItem(event) {
    event.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) return;
    try {
      const response = await fetch("/api/items", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: trimmed }),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      setName("");
      await loadItems();
    } catch {
      setError("L'ajout a échoué. Réessaie dans quelques secondes.");
    }
  }

  async function removeItem(id) {
    try {
      const response = await fetch(`/api/items/${id}`, { method: "DELETE" });
      if (!response.ok && response.status !== 404) throw new Error(`HTTP ${response.status}`);
      await loadItems();
    } catch {
      setError("La suppression a échoué. Réessaie dans quelques secondes.");
    }
  }

  const distinctPods = new Set(history).size;

  return (
    <main className="layout">
      <section className="items" aria-labelledby="items-title">
        <h1 id="items-title">Items</h1>

        <form className="add-form" onSubmit={addItem}>
          <label htmlFor="item-name">Nom de l'item</label>
          <div className="add-row">
            <input
              id="item-name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              maxLength={100}
              placeholder="Ex. : test de charge"
              autoComplete="off"
            />
            <button type="submit" disabled={!name.trim()}>
              Ajouter l'item
            </button>
          </div>
        </form>

        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}

        {items.length === 0 && !error ? (
          <p className="empty">Aucun item pour l'instant. Ajoute le premier ci-dessus.</p>
        ) : (
          <ul className="item-list">
            {items.map((item) => (
              <li key={item.id}>
                <span className="item-name">{item.name}</span>
                <time dateTime={item.created_at}>{formatDate(item.created_at)}</time>
                <button
                  type="button"
                  className="link-button"
                  onClick={() => removeItem(item.id)}
                  aria-label={`Supprimer l'item ${item.name}`}
                >
                  Supprimer
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      <aside className="platform" aria-labelledby="platform-title">
        <h2 id="platform-title">Ce que répond la plateforme</h2>

        <p className={online ? "status status-up" : "status status-down"} role="status">
          {online ? "API en ligne" : "API injoignable"}
        </p>

        <dl className="facts">
          <div>
            <dt>Pod qui répond</dt>
            <dd className="mono">{info ? info.hostname : "—"}</dd>
          </div>
          <div>
            <dt>Version déployée</dt>
            <dd className="mono">{info ? info.version : "—"}</dd>
          </div>
          <div>
            <dt>Latence</dt>
            <dd className="mono">{latency !== null ? `${latency} ms` : "—"}</dd>
          </div>
          <div>
            <dt>Dernière liste</dt>
            <dd>
              {cacheStatus === "HIT" && <span className="badge badge-hit">Lue dans Redis</span>}
              {cacheStatus === "MISS" && <span className="badge badge-miss">Lue dans PostgreSQL</span>}
              {!cacheStatus && "—"}
            </dd>
          </div>
        </dl>

        <h3>Les {HISTORY_SIZE} dernières réponses</h3>
        <div className="pod-strip" aria-hidden="true">
          {history.map((hostname, index) => (
            <span
              key={`${index}-${hostname}`}
              className="pod-cell"
              style={{ background: podColor(hostname) }}
              title={hostname}
            />
          ))}
        </div>
        <p className="hint">
          {distinctPods > 1
            ? `${distinctPods} pods différents ont répondu : le trafic est réparti.`
            : "Un seul pod répond pour l'instant. Avec plusieurs réplicas, les couleurs se mélangent."}
        </p>
      </aside>
    </main>
  );
}

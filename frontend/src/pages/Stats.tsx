import { useEffect, useState } from "react";
import { api, type Stats as StatsData, type ProviderMeta } from "../api/client";
export function Stats() {
  const [stats, setStats] = useState<StatsData | null>(null);
  const [provider, setProvider] = useState<ProviderMeta | null>(null);
  const [cache, setCache] = useState("");
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setError("");
    Promise.all([
      api.stats(controller.signal),
      api.providers(controller.signal),
    ])
      .then(([s, p]) => {
        setStats(s.data);
        setCache(s.cache);
        setProvider(p);
      })
      .catch((err) => {
        if (!controller.signal.aborted) setError(err.message);
      });
    return () => controller.abort();
  }, [refresh]);
  return (
    <section>
      <div className="page-heading">
        <div>
          <span className="eyebrow">THE BIGGER PICTURE</span>
          <h1>A pulse on your city.</h1>
        </div>
        <button onClick={() => setRefresh((v) => v + 1)}>
          Refresh stats ↻
        </button>
      </div>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {!stats ? (
        <p role="status">Loading city statistics…</p>
      ) : (
        <>
          <div className="stat-cards">
            <div className="panel">
              <span>Total reports</span>
              <strong>{stats.total}</strong>
            </div>
            <div className="panel">
              <span>High priority</span>
              <strong>{stats.by_priority.high || 0}</strong>
            </div>
            <div className="panel">
              <span>Resolved</span>
              <strong>{stats.by_status.resolved || 0}</strong>
            </div>
            <div className="panel">
              <span>Stats cache</span>
              <strong className="cache">{cache}</strong>
              <small>From the server’s X-Cache header</small>
            </div>
          </div>
          <div className="analytics-grid">
            {[
              ["By category", stats.by_category],
              ["By priority", stats.by_priority],
              ["By status", stats.by_status],
            ].map(([title, counts]) => (
              <div className="panel" key={title as string}>
                <h2>{title as string}</h2>
                {Object.entries(counts as Record<string, number>).map(
                  ([label, value]) => (
                    <div className="bar-row" key={label}>
                      <div>
                        <span>{label.replace("_", " ")}</span>
                        <strong>{value}</strong>
                      </div>
                      <meter
                        min={0}
                        max={Math.max(stats.total, 1)}
                        value={value}
                      >
                        {value}
                      </meter>
                    </div>
                  ),
                )}
              </div>
            ))}
          </div>
        </>
      )}
      {provider && (
        <div className="panel observability">
          <h2>Triage activity</h2>
          <p>
            Active provider: <strong>{provider.active_provider}</strong> · AI
            cache hit rate:{" "}
            <strong>
              {(provider.triage_cache_hit_rate * 100).toFixed(1)}%
            </strong>{" "}
            ({provider.triage_cache_hits}/{provider.triage_cache_requests})
          </p>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Provider</th>
                  <th>Latency</th>
                  <th>Fallback</th>
                  <th>Cached</th>
                </tr>
              </thead>
              <tbody>
                {provider.outcomes.map((outcome, i) => (
                  <tr key={i}>
                    <td>{outcome.provider}</td>
                    <td>{outcome.latency_ms} ms</td>
                    <td>{outcome.fallback ? "Yes" : "No"}</td>
                    <td>{outcome.cache_hit ? "Yes" : "No"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!provider.outcomes.length && <p>No triage activity yet.</p>}
          </div>
        </div>
      )}
    </section>
  );
}

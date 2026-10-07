import { useEffect, useState } from "react";
import {
  api,
  type ComplaintPage,
  type Filters,
  type Status,
} from "../api/client";
const empty: ComplaintPage = { items: [], total: 0, page: 1, page_size: 10 };
export function Dashboard() {
  const [filters, setFilters] = useState<Filters>({ page: 1, page_size: 10 });
  const [data, setData] = useState(empty);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [refresh, setRefresh] = useState(0);
  const [busy, setBusy] = useState<string | null>(null);
  const [key, setKey] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");
    api
      .list(filters, controller.signal)
      .then(setData)
      .catch((err) => {
        if (!controller.signal.aborted) setError(err.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [filters, refresh]);
  useEffect(() => {
    const timer = setInterval(() => setRefresh((v) => v + 1), 15000);
    return () => clearInterval(timer);
  }, []);
  async function change(id: string, status: Status) {
    setBusy(id);
    setError("");
    try {
      await api.transition(id, status, key);
      setRefresh((v) => v + 1);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(null);
    }
  }
  return (
    <section>
      <div className="page-heading">
        <div>
          <span className="eyebrow">CITY OPERATIONS</span>
          <h1>Every report counts.</h1>
        </div>
        <button onClick={() => setRefresh((v) => v + 1)}>Refresh ↻</button>
      </div>
      <div className="filters panel">
        <label>
          Category
          <select
            aria-label="Category"
            value={filters.category || ""}
            onChange={(e) =>
              setFilters({
                ...filters,
                page: 1,
                category: (e.target.value as Filters["category"]) || undefined,
              })
            }
          >
            <option value="">All categories</option>
            {[
              "water",
              "electricity",
              "sanitation",
              "roads",
              "streetlights",
              "other",
            ].map((v) => (
              <option key={v}>{v}</option>
            ))}
          </select>
        </label>
        <label>
          Priority
          <select
            aria-label="Priority"
            value={filters.priority || ""}
            onChange={(e) =>
              setFilters({
                ...filters,
                page: 1,
                priority: (e.target.value as Filters["priority"]) || undefined,
              })
            }
          >
            <option value="">All priorities</option>
            {["high", "normal", "low"].map((v) => (
              <option key={v}>{v}</option>
            ))}
          </select>
        </label>
        <label>
          Status
          <select
            aria-label="Status"
            value={filters.status || ""}
            onChange={(e) =>
              setFilters({
                ...filters,
                page: 1,
                status: (e.target.value as Status) || undefined,
              })
            }
          >
            <option value="">All statuses</option>
            {["open", "in_progress", "resolved", "rejected"].map((v) => (
              <option key={v}>{v}</option>
            ))}
          </select>
        </label>
        <label>
          Operator key
          <input
            type="password"
            autoComplete="off"
            value={key}
            onChange={(e) => setKey(e.target.value)}
            placeholder="For protected status updates"
          />
        </label>
      </div>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      <div className="list-meta">
        <span>{data.total} reports</span>
        <span>{loading ? "Updating…" : "Updates every 15 seconds"}</span>
      </div>
      {!loading && !data.items.length && (
        <div className="panel empty">No reports match these filters.</div>
      )}
      <div className="reports">
        {data.items.map((item) => (
          <article className="panel report" key={item.id}>
            <div className="report-top">
              <div className="tags">
                <span>{item.category}</span>
                <span className={item.priority}>{item.priority} priority</span>
              </div>
              <span className="status">{item.status.replace("_", " ")}</span>
            </div>
            <h2>{item.ai_summary || item.text}</h2>
            <p>{item.text}</p>
            <p className="muted">⌖ {item.location}</p>
            <div className="report-bottom">
              <span className="small muted">
                {new Date(item.created_at).toLocaleString()} · {item.triaged_by}
              </span>
              <div className="actions">
                {item.allowed_transitions?.map((target) => (
                  <button
                    key={target}
                    disabled={busy === item.id}
                    onClick={() => change(item.id, target)}
                  >
                    {target.replace("_", " ")}
                  </button>
                ))}
              </div>
            </div>
          </article>
        ))}
      </div>
      <div className="pagination">
        <button
          disabled={filters.page === 1 || loading}
          onClick={() => setFilters({ ...filters, page: filters.page - 1 })}
        >
          ← Previous
        </button>
        <span>
          Page {filters.page} of{" "}
          {Math.max(1, Math.ceil(data.total / filters.page_size))}
        </span>
        <button
          disabled={filters.page * filters.page_size >= data.total || loading}
          onClick={() => setFilters({ ...filters, page: filters.page + 1 })}
        >
          Next →
        </button>
      </div>
    </section>
  );
}

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../api/client";
import { DEVICE_TYPES, OS_TYPES, STATUSES, labelOf } from "../constants";
import { useAuth } from "../auth/AuthContext";

export default function DashboardPage() {
  const { canManage } = useAuth();
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get("/dashboard/summary")
      .then((r) => setSummary(r.data))
      .catch((e) => setError(e.response?.data?.detail || "Failed to load dashboard"));
  }, []);

  if (error) return <p className="error">{error}</p>;
  if (!summary) return <p>Loading dashboard…</p>;

  return (
    <section className="page">
      <div className="page-head">
        <div>
          <h1>Dashboard</h1>
          <p className="lede">Inventory at a glance across status and platforms.</p>
        </div>
        {canManage && (
          <Link className="btn primary" to="/devices/new">
            Add device
          </Link>
        )}
      </div>

      <div className="stat-row">
        <div className="stat">
          <span>Total devices</span>
          <strong>{summary.total_devices}</strong>
        </div>
        <div className="stat">
          <span>Unassigned</span>
          <strong>{summary.unassigned_devices}</strong>
        </div>
      </div>

      <div className="grid-2">
        <div className="panel">
          <h2>By status</h2>
          <ul className="kv-list">
            {STATUSES.map((s) => (
              <li key={s.value}>
                <span>{s.label}</span>
                <strong>{summary.by_status[s.value] || 0}</strong>
              </li>
            ))}
          </ul>
        </div>
        <div className="panel">
          <h2>By OS</h2>
          <ul className="kv-list">
            {OS_TYPES.map((o) => (
              <li key={o.value}>
                <span>{o.label}</span>
                <strong>{summary.by_os[o.value] || 0}</strong>
              </li>
            ))}
          </ul>
        </div>
        <div className="panel">
          <h2>By type</h2>
          <ul className="kv-list">
            {DEVICE_TYPES.map((t) => (
              <li key={t.value}>
                <span>{t.label}</span>
                <strong>{summary.by_type[t.value] || 0}</strong>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}

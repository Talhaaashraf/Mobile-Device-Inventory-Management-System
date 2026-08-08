import { useEffect, useState } from "react";
import api from "../api/client";
import { ROLES, labelOf } from "../constants";

const blank = {
  full_name: "",
  email: "",
  password: "",
  role: "viewer",
  department: "",
};

export default function UsersPage() {
  const [users, setUsers] = useState([]);
  const [form, setForm] = useState(blank);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const load = () =>
    api
      .get("/users")
      .then((r) => setUsers(r.data))
      .catch((e) => setError(e.response?.data?.detail || "Failed to load users"));

  useEffect(() => {
    load();
  }, []);

  const onChange = (e) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }));

  const createUser = async (e) => {
    e.preventDefault();
    setError("");
    setMessage("");
    try {
      await api.post("/users", form);
      setForm(blank);
      setMessage("User created");
      load();
    } catch (err) {
      setError(err.response?.data?.detail || "Create failed");
    }
  };

  const toggleActive = async (user) => {
    await api.patch(`/users/${user.id}`, { is_active: !user.is_active });
    load();
  };

  return (
    <section className="page">
      <div className="page-head">
        <div>
          <h1>Users</h1>
          <p className="lede">Admin-only account and role management.</p>
        </div>
      </div>

      <div className="grid-2">
        <form className="panel stack" onSubmit={createUser}>
          <h2>Create user</h2>
          <label>
            Full name
            <input name="full_name" value={form.full_name} onChange={onChange} required />
          </label>
          <label>
            Email
            <input type="email" name="email" value={form.email} onChange={onChange} required />
          </label>
          <label>
            Password
            <input type="password" name="password" value={form.password} onChange={onChange} required minLength={8} />
          </label>
          <label>
            Role
            <select name="role" value={form.role} onChange={onChange}>
              {ROLES.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            Department
            <input name="department" value={form.department} onChange={onChange} required />
          </label>
          {error && <p className="error">{error}</p>}
          {message && <p className="success">{message}</p>}
          <button className="btn primary" type="submit">
            Create
          </button>
        </form>

        <div className="panel">
          <h2>Directory</h2>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Role</th>
                  <th>Dept</th>
                  <th>Active</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id}>
                    <td>
                      {u.full_name}
                      <div className="muted">{u.email}</div>
                    </td>
                    <td>{labelOf(ROLES, u.role)}</td>
                    <td>{u.department}</td>
                    <td>{u.is_active ? "Yes" : "No"}</td>
                    <td>
                      <button className="btn ghost" type="button" onClick={() => toggleActive(u)}>
                        {u.is_active ? "Deactivate" : "Activate"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>
  );
}

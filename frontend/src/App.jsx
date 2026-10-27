import { useEffect, useState } from 'react'
import './App.css'

const GATE_LABELS = {
  runs_verified: 'Runs & verified',
  cicd_working: 'CI/CD working',
  gitops_working: 'GitOps working',
  readme_published: 'README published',
  troubleshooting_log: 'Troubleshooting log',
  linkedin_profile: 'LinkedIn profile',
  linkedin_post: 'LinkedIn post',
  chapter_summary: 'Chapter summary',
}

// One helper for every API call: relative URL (works behind Vite AND Nginx),
// and backend error messages surfaced to the user instead of swallowed.
async function api(path, options = {}) {
  const res = await fetch(`/api${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    const detail = Array.isArray(body.detail)
      ? body.detail.map((d) => d.msg).join('; ') // 422: list of validation errors
      : body.detail                               // 404/409: single message
    throw new Error(detail || `Request failed (${res.status})`)
  }
  return res.status === 204 ? null : res.json()
}

export default function App() {
  const [projects, setProjects] = useState([])
  const [error, setError] = useState('')
  const [form, setForm] = useState({ chapter: '', title: '', repo_url: '' })
  const [version, setVersion] = useState(0) // bump this to re-fetch the list

  const refresh = () => setVersion((v) => v + 1)

  // The ONLY place data is loaded. Re-runs whenever "version" changes.
  useEffect(() => {
    let ignore = false // if a newer fetch starts, this one's result is discarded (no stale overwrites)
    api('/projects')
      .then((data) => {
        if (!ignore) {
          setProjects(data)
          setError('')
        }
      })
      .catch((e) => {
        if (!ignore) setError(e.message)
      })
    return () => {
      ignore = true // cleanup: runs before the next fetch starts or when the page unmounts
    }
  }, [version])

  async function addProject(e) {
    e.preventDefault()
    try {
      await api('/projects', {
        method: 'POST',
        body: JSON.stringify({
          chapter: Number(form.chapter),
          title: form.title,
          repo_url: form.repo_url || null,
        }),
      })
      setForm({ chapter: '', title: '', repo_url: '' })
      refresh()
    } catch (e) {
      setError(e.message)
    }
  }

  async function toggleGate(project, key) {
    try {
      // PATCH only the one box that changed
      await api(`/projects/${project.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ gate: { [key]: !project.gate[key] } }),
      })
      refresh()
    } catch (e) {
      setError(e.message)
    }
  }

  async function remove(project) {
    if (!confirm(`Delete chapter ${project.chapter}?`)) return
    try {
      await api(`/projects/${project.id}`, { method: 'DELETE' })
      refresh()
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <main>
      <h1>Portfolio Hub</h1>
      <p className="subtitle">DevOps &amp; GitOps learning in public: chapter tracker</p>

      {error && <p className="error" role="alert">{error}</p>}

      <form onSubmit={addProject} className="add-form">
        <input type="number" min="1" placeholder="Ch" required value={form.chapter}
          onChange={(e) => setForm({ ...form, chapter: e.target.value })} />
        <input placeholder="Title" required value={form.title}
          onChange={(e) => setForm({ ...form, title: e.target.value })} />
        <input type="url" placeholder="Repo URL (optional)" value={form.repo_url}
          onChange={(e) => setForm({ ...form, repo_url: e.target.value })} />
        <button type="submit">Add</button>
      </form>

      {projects.map((p) => {
        const applicable = Object.values(p.gate).filter((v) => v !== null) // N/A items don't count
        const done = applicable.filter(Boolean).length
        return (
          <section key={p.id} className="card">
            <header>
              <h2>Ch {p.chapter}: {p.title}</h2>
              <span className="progress">{done}/{applicable.length} gate items</span>
            </header>
            {p.repo_url && <a href={p.repo_url} target="_blank" rel="noreferrer">Repository</a>}
            <ul className="gate">
              {Object.entries(GATE_LABELS).map(([key, label]) => (
                <li key={key}>
                  {p.gate[key] === null ? (
                    <span className="na">{label}: N/A</span>
                  ) : (
                    <label>
                      <input type="checkbox" checked={p.gate[key]} onChange={() => toggleGate(p, key)} />
                      {' '}{label}
                    </label>
                  )}
                </li>
              ))}
            </ul>
            <button className="danger" onClick={() => remove(p)}>Delete</button>
          </section>
        )
      })}

      {projects.length === 0 && !error && <p>No projects yet. Add your first chapter above.</p>}
    </main>
  )
}

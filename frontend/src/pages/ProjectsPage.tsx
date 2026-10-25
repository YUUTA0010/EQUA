import { useEffect, useState } from "react";
import TopBar from "../components/layout/TopBar";
import { api } from "../api/client";
import { FolderKanban, Plus } from "lucide-react";

export default function ProjectsPage() {
  const [items, setItems] = useState<any[]>([]);
  const [name, setName] = useState("");
  const [creating, setCreating] = useState(false);

  const load = () => api.listProjects().then((res: any) => setItems(res.items));

  useEffect(() => { load(); }, []);

  const create = async () => {
    if (!name.trim()) return;
    setCreating(true);
    try {
      await api.createProject(name.trim());
      setName("");
      load();
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="min-h-screen">
      <TopBar title="Projects" />
      <div className="max-w-4xl mx-auto px-4 md:px-6 py-8 space-y-6">
        <h2 className="text-2xl font-semibold text-slate-100">Projects</h2>
        <p className="text-slate-500 text-sm -mt-4">
          Group related equations together — e.g. all the formulas from one chapter or one design problem.
        </p>

        <div className="flex gap-3">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && create()}
            placeholder="New project name, e.g. Dynamics — Chapter 3"
            className="flex-1 rounded-xl bg-base-900/70 border border-base-600/60 px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-accent-500/60"
          />
          <button
            onClick={create}
            disabled={creating || !name.trim()}
            className="inline-flex items-center gap-1.5 rounded-xl bg-accent-600 hover:bg-accent-500 disabled:opacity-40 text-base-950 font-semibold px-4 py-2.5 text-sm transition-colors"
          >
            <Plus size={15} /> Create
          </button>
        </div>

        {items.length === 0 ? (
          <div className="rounded-2xl border border-base-600/60 bg-base-900/50 p-10 text-center text-slate-500">
            <FolderKanban className="mx-auto mb-3 text-slate-600" size={28} />
            <p>No projects yet.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {items.map((p) => (
              <div key={p.id} className="rounded-xl border border-base-600/60 bg-base-900/60 p-4">
                <p className="font-medium text-slate-100">{p.name}</p>
                {p.description && <p className="text-sm text-slate-500 mt-0.5">{p.description}</p>}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

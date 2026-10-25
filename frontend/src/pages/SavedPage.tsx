import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import TopBar from "../components/layout/TopBar";
import { api } from "../api/client";
import { InlineMath } from "react-katex";
import { Trash2, Eye, Bookmark } from "lucide-react";

export default function SavedPage() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const load = () => {
    setLoading(true);
    api.listSaved().then((res) => setItems(res.items)).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const remove = async (id: string) => {
    await api.deleteSaved(id).catch(() => {});
    load();
  };

  return (
    <div className="min-h-screen">
      <TopBar title="Saved Visualizations" />
      <div className="max-w-4xl mx-auto px-4 md:px-6 py-8 space-y-6">
        <h2 className="text-2xl font-semibold text-slate-100">Saved Visualizations</h2>

        {loading && <p className="text-slate-500 text-sm">Loading…</p>}

        {!loading && items.length === 0 && (
          <div className="rounded-2xl border border-base-600/60 bg-base-900/50 p-10 text-center text-slate-500">
            <Bookmark className="mx-auto mb-3 text-slate-600" size={28} />
            <p>Nothing saved yet. Open any equation's workspace and hit "Save".</p>
          </div>
        )}

        <div className="space-y-3">
          {items.map((it) => (
            <div key={it.id} className="rounded-xl border border-base-600/60 bg-base-900/60 p-4 flex items-center justify-between gap-4">
              <div className="min-w-0">
                <div className="text-lg font-mono text-slate-100 truncate">
                  <SafeMath eq={it.equation} />
                </div>
                <p className="text-xs text-slate-500 mt-0.5">{new Date(it.created_at).toLocaleString()}</p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <button
                  onClick={() => navigate(`/workspace?eq=${encodeURIComponent(it.equation)}`)}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-accent-600/20 hover:bg-accent-600/30 text-accent-400 px-3 py-1.5 text-xs font-medium transition-colors"
                >
                  <Eye size={13} /> Open
                </button>
                <button
                  onClick={() => remove(it.id)}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-signal-red/10 hover:bg-signal-red/20 text-signal-red px-2 py-1.5 text-xs font-medium transition-colors"
                >
                  <Trash2 size={13} />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function SafeMath({ eq }: { eq: string }) {
  try {
    return <InlineMath math={eq.replace(/\*\*/g, "^").replace(/\*/g, "\\cdot ")} />;
  } catch {
    return <span>{eq}</span>;
  }
}

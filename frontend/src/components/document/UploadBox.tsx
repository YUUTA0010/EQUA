import { useCallback, useRef, useState } from "react";
import { UploadCloud, FileText, Image as ImageIcon, Loader2 } from "lucide-react";
import { api } from "../../api/client";
import type { DocumentAnalysisResponse } from "../../types/equation";

interface UploadBoxProps {
  onResult: (result: DocumentAnalysisResponse) => void;
  onPasteEquation: (text: string) => void;
}

export default function UploadBox({ onResult, onPasteEquation }: UploadBoxProps) {
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [pasteMode, setPasteMode] = useState(false);
  const [pasteText, setPasteText] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(async (file: File) => {
    setError(null);
    setLoading(true);
    setProgress(0);
    try {
      const result = await api.upload(file, setProgress);
      onResult(result);
    } catch (e: any) {
      setError(e?.message || "Upload failed.");
    } finally {
      setLoading(false);
    }
  }, [onResult]);

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  };

  return (
    <div className="space-y-4">
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={`relative rounded-2xl border-2 border-dashed p-10 text-center transition-colors ${
          dragging ? "border-accent-500 bg-accent-500/5" : "border-base-600 bg-base-900/40"
        }`}
      >
        {loading ? (
          <div className="flex flex-col items-center gap-3 py-6">
            <Loader2 className="animate-spin text-accent-400" size={32} />
            <p className="text-slate-400 text-sm">Extracting text and detecting equations… {progress > 0 ? `${progress}%` : ""}</p>
          </div>
        ) : (
          <>
            <UploadCloud className="mx-auto text-accent-400 mb-3" size={40} />
            <p className="text-slate-200 font-medium">Drop PDF, DOCX, image or screenshot here</p>
            <p className="text-slate-500 text-sm mt-1">or use one of the options below</p>
          </>
        )}
        <input
          ref={fileInputRef} type="file" className="hidden"
          accept=".pdf,.docx,.png,.jpg,.jpeg,.webp"
          onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
        />
        <input
          ref={imageInputRef} type="file" className="hidden" accept="image/*" capture="environment"
          onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
        />
      </div>

      {error && (
        <div className="rounded-lg border border-signal-red/30 bg-signal-red/10 text-signal-red text-sm px-3 py-2">
          {error}
        </div>
      )}

      <div className="flex flex-wrap gap-3">
        <button
          onClick={() => fileInputRef.current?.click()}
          className="inline-flex items-center gap-2 rounded-xl bg-accent-600 hover:bg-accent-500 text-base-950 font-semibold px-4 py-2.5 text-sm transition-colors"
        >
          <FileText size={16} /> Upload Document
        </button>
        <button
          onClick={() => setPasteMode((p) => !p)}
          className="inline-flex items-center gap-2 rounded-xl bg-base-700/60 hover:bg-base-700 text-slate-200 font-medium px-4 py-2.5 text-sm transition-colors"
        >
          <FileText size={16} /> Paste Equation
        </button>
        <button
          onClick={() => imageInputRef.current?.click()}
          className="inline-flex items-center gap-2 rounded-xl bg-base-700/60 hover:bg-base-700 text-slate-200 font-medium px-4 py-2.5 text-sm transition-colors"
        >
          <ImageIcon size={16} /> Take / Upload Image
        </button>
      </div>

      {pasteMode && (
        <div className="rounded-xl border border-base-600/60 bg-base-900/60 p-4 animate-fade-in space-y-2">
          <textarea
            value={pasteText}
            onChange={(e) => setPasteText(e.target.value)}
            placeholder="Paste an equation or a block of text containing equations, e.g. F = m*a"
            rows={3}
            className="w-full rounded-lg bg-base-800/70 border border-base-600/60 px-3 py-2 text-sm text-slate-200 font-mono focus:outline-none focus:border-accent-500/60"
          />
          <button
            onClick={() => pasteText.trim() && onPasteEquation(pasteText.trim())}
            disabled={!pasteText.trim()}
            className="rounded-lg bg-accent-600 hover:bg-accent-500 disabled:opacity-40 text-base-950 font-semibold px-4 py-2 text-sm transition-colors"
          >
            Analyze
          </button>
        </div>
      )}
    </div>
  );
}

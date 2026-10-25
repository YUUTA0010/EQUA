import { useState } from "react";
import { useNavigate } from "react-router-dom";
import TopBar from "../components/layout/TopBar";
import UploadBox from "../components/document/UploadBox";
import DocumentEquationList from "../components/document/DocumentEquationList";
import { api } from "../api/client";
import type { DocumentAnalysisResponse } from "../types/equation";
import { FileText } from "lucide-react";

export default function UploadPage() {
  const [doc, setDoc] = useState<DocumentAnalysisResponse | null>(null);
  const navigate = useNavigate();

  const handlePaste = async (text: string) => {
    try {
      const result = await api.analyzeDocumentText(text);
      setDoc(result);
    } catch {
      // If it's really just one equation, send straight to the workspace.
      navigate(`/workspace?eq=${encodeURIComponent(text)}`);
    }
  };

  return (
    <div className="min-h-screen">
      <TopBar title="Upload Document" />
      <div className="max-w-6xl mx-auto px-4 md:px-6 py-8 space-y-6">
        <div>
          <h2 className="text-2xl font-semibold text-slate-100">Upload a document and see what its equations actually do.</h2>
          <p className="text-slate-500 text-sm mt-1">PDF, DOCX, PNG, JPG, screenshots, and scanned textbook pages are all supported.</p>
        </div>

        {!doc && <UploadBox onResult={setDoc} onPasteEquation={handlePaste} />}

        {doc && (
          <div className="grid grid-cols-1 lg:grid-cols-[1fr_1.3fr] gap-6">
            <div className="rounded-2xl border border-base-600/60 bg-base-900/50 p-4 space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-sm font-semibold text-slate-200 flex items-center gap-1.5"><FileText size={15} /> {doc.filename}</p>
                <button onClick={() => setDoc(null)} className="text-xs text-slate-500 hover:text-slate-300">Upload another</button>
              </div>
              <div className="rounded-xl bg-base-800/50 border border-base-600/50 p-3 max-h-[60vh] overflow-y-auto">
                <pre className="text-xs text-slate-400 whitespace-pre-wrap font-sans">{doc.extracted_text_preview || "(no extractable text preview)"}</pre>
              </div>
            </div>
            <DocumentEquationList
              document={doc}
              onVisualize={(eqText) => navigate(`/workspace?eq=${encodeURIComponent(eqText)}`)}
            />
          </div>
        )}
      </div>
    </div>
  );
}

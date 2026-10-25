import axios from "axios";
import type {
  EquationAnalysis, VisualizationResponse, ExplainResponse,
  DocumentAnalysisResponse, CompareResponse, DemoEquation,
} from "../types/equation";

const client = axios.create({ baseURL: "/api", timeout: 30000 });

function friendlyError(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (err.code === "ECONNABORTED") return "The request took too long. Please try again.";
    if (!err.response) return "Could not reach the EquationLens backend. Is it running on port 8000?";
  }
  return "Something went wrong. Please try again.";
}

export class ApiError extends Error {}

async function call<T>(promise: Promise<{ data: T }>): Promise<T> {
  try {
    const res = await promise;
    return res.data;
  } catch (err) {
    throw new ApiError(friendlyError(err));
  }
}

export const api = {
  analyze: (equation: string, engineering_mode = false) =>
    call<EquationAnalysis>(client.post("/equations/analyze", { equation, engineering_mode })),

  visualize: (params: {
    equation: string; visualization_id?: string | null; parameters: Record<string, number>;
    x_min?: number | null; x_max?: number | null; locked_symbol?: string | null;
  }) => call<VisualizationResponse>(client.post("/equations/visualize", params)),

  explain: (equation: string, mode: string, parameters: Record<string, number> = {}) =>
    call<ExplainResponse>(client.post("/equations/explain", { equation, mode, parameters })),

  compare: (params: {
    equation: string; config_a: Record<string, number>; config_b: Record<string, number>;
    x_min?: number | null; x_max?: number | null;
  }) => call<CompareResponse>(client.post("/equations/compare", params)),

  library: () => call<{ demo_equations: DemoEquation[]; categories: any[] }>(client.get("/equations/library")),

  detect: (text: string) => call<{ equations: any[] }>(client.post("/equations/detect", { text })),

  upload: (file: File, onProgress?: (pct: number) => void) => {
    const form = new FormData();
    form.append("file", file);
    return call<DocumentAnalysisResponse>(
      client.post("/upload", form, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (evt) => {
          if (onProgress && evt.total) onProgress(Math.round((evt.loaded / evt.total) * 100));
        },
      })
    );
  },

  analyzeDocumentText: (text: string) =>
    call<DocumentAnalysisResponse>(client.post("/documents/analyze", { text })),

  saveEquation: (payload: { equation: string; category?: string; parameters?: Record<string, number>; note?: string }) =>
    call<any>(client.post("/equations/save", payload)),

  listSaved: () => call<{ items: any[] }>(client.get("/equations/saved")),

  deleteSaved: (id: string) => call<any>(client.delete(`/equations/saved/${id}`)),

  health: () => call<any>(client.get("/health")),

  listProjects: () => call<{ items: any[] }>(client.get("/projects")),
  createProject: (name: string, description?: string) =>
    call<any>(client.post("/projects", { name, description })),
};

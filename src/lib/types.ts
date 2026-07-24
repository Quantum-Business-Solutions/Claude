export type Project = "qbs" | "personal" | "both";

export type AnalysisStatus = "pending" | "done" | "skipped" | "error";

export interface DesignReference {
  id: string;
  createdAt: string;
  updatedAt: string;
  title: string;
  sourceUrl?: string;
  imagePath?: string;
  project: Project;
  notes?: string;
  category?: string;
  tags: string[];
  colors: string[];
  typography: string[];
  layoutNotes: string[];
  guardrails: string[];
  analysis: {
    status: AnalysisStatus;
    model?: string;
    analyzedAt?: string;
    error?: string;
  };
}

export type NewDesignReferenceInput = {
  title: string;
  sourceUrl?: string;
  imagePath?: string;
  project: Project;
  notes?: string;
  category?: string;
  tags?: string[];
};

export interface StyleGuide {
  referenceCount: number;
  topTags: { tag: string; count: number }[];
  topCategories: { category: string; count: number }[];
  commonColors: string[];
  commonTypography: string[];
  guardrails: string[];
}

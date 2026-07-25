export type Project = "qbs" | "personal" | "both";

export type AnalysisStatus = "pending" | "done" | "skipped" | "error";

/** How this reference got into the library. */
export type SourceKind =
  /** A live site we analyzed — carries real computed tokens. */
  | "live-site"
  /** A screenshot we saved ourselves — vocabulary is inferred, not measured. */
  | "screenshot";

/**
 * Real computed design values read off a live site, as opposed to vocabulary
 * inferred by looking at a picture. These are accurate enough to port straight
 * into a Tailwind config or a set of CSS custom properties.
 */
export interface DesignTokens {
  colorScheme?: string;
  colors?: {
    primary?: string;
    secondary?: string;
    accent?: string;
    background?: string;
    textPrimary?: string;
    link?: string;
  };
  fonts?: { family: string; role?: string }[];
  fontStacks?: Record<string, string[]>;
  fontSizes?: Record<string, string>;
  spacing?: { baseUnit?: number; borderRadius?: string };
  components?: Record<
    string,
    {
      background?: string | null;
      textColor?: string | null;
      borderColor?: string | null;
      borderRadius?: string | null;
      shadow?: string | null;
    }
  >;
  personality?: { tone?: string; energy?: string; targetAudience?: string };
  designSystem?: { framework?: string; componentLibrary?: string };
  /** Extractor's own confidence, so we don't treat a shaky read as gospel. */
  confidence?: Record<string, number>;
}

export interface DesignReference {
  id: string;
  createdAt: string;
  updatedAt: string;
  title: string;
  sourceUrl?: string;
  imagePath?: string;
  sourceKind: SourceKind;
  project: Project;
  notes?: string;
  category?: string;
  tags: string[];
  colors: string[];
  typography: string[];
  layoutNotes: string[];
  guardrails: string[];
  /** Present for live-site references. Measured, not guessed. */
  tokens?: DesignTokens;
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
  sourceKind?: SourceKind;
  project: Project;
  notes?: string;
  category?: string;
  tags?: string[];
  tokens?: DesignTokens;
  colors?: string[];
  typography?: string[];
  layoutNotes?: string[];
  guardrails?: string[];
};

export interface StyleGuide {
  referenceCount: number;
  liveSiteCount: number;
  topTags: { tag: string; count: number }[];
  topCategories: { category: string; count: number }[];
  commonColors: string[];
  commonTypography: string[];
  guardrails: string[];
  /** Measured values pulled from live-site references only. */
  measured: {
    fontFamilies: { family: string; count: number }[];
    borderRadii: { value: string; count: number }[];
    baseUnits: { value: number; count: number }[];
    accentColors: string[];
  };
}

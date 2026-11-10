/**
 * Semantic mapping to the backend (spec "Semantic mapping to the backend").
 *
 *  - PEG `interpretation.level`: success/info/warning/error -> positive/primary/
 *    warning/negative, each paired with a label + icon name (never color alone).
 *  - Football-field `market_position` (market price vs the value range):
 *    below/inside/above -> positive/neutral/negative with a text label. "below"
 *    = market price under the range (cheaper than value, good); "above" = over
 *    the range (expensive, bad).
 */

export type Tone = "positive" | "primary" | "warning" | "negative" | "neutral";

export interface SemanticView {
  tone: Tone;
  label: string;
}

const PEG_LEVEL: Record<string, SemanticView> = {
  success: { tone: "positive", label: "ارزش مناسب" },
  info: { tone: "primary", label: "تقریباً منصفانه" },
  warning: { tone: "warning", label: "نیازمند دقت" },
  error: { tone: "negative", label: "گران‌بخشی" },
};

export function pegLevelView(level: string): SemanticView {
  return PEG_LEVEL[level] ?? { tone: "neutral", label: level };
}

const MARKET_POSITION: Record<string, SemanticView> = {
  // market price below the range -> cheaper than value -> positive
  below: { tone: "positive", label: "قیمت بازار زیر بازه (ارزان‌تر)" },
  inside: { tone: "neutral", label: "قیمت بازار داخل بازه" },
  // market price above the range -> expensive -> negative
  above: { tone: "negative", label: "قیمت بازار بالای بازه (گران‌تر)" },
};

export function marketPositionView(position: string | null | undefined): SemanticView | null {
  if (!position) return null;
  return MARKET_POSITION[position] ?? { tone: "neutral", label: position };
}

/** Tailwind text color per tone. */
export const toneText: Record<Tone, string> = {
  positive: "text-positive",
  primary: "text-primary",
  warning: "text-warning",
  negative: "text-negative",
  neutral: "text-foreground",
};

/** Tailwind border/bg per tone for banners and bars. */
export const toneSurface: Record<Tone, string> = {
  positive: "border-positive/50 bg-positive/10",
  primary: "border-primary/50 bg-primary/10",
  warning: "border-warning/50 bg-warning/10",
  negative: "border-negative/50 bg-negative/10",
  neutral: "border-border bg-muted",
};

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FormulaStrip } from "@/components/model/ResultParts";

interface SplitLayoutProps {
  title: string;
  formula: string;
  whenSuitable: string;
  howToRead?: string;
  /** Input column content (fields, toggles, sample button, chips...). */
  input: React.ReactNode;
  /** Results column content (hero, cards, charts, tables). */
  results: React.ReactNode;
}

/** Two-column template (input right ~35%, results left ~65%) for custom pages. */
export function SplitLayout({ title, formula, whenSuitable, howToRead, input, results }: SplitLayoutProps) {
  return (
    <div className="grid grid-cols-1 gap-colgap xl:grid-cols-[minmax(0,35fr)_minmax(0,65fr)]">
      <Card className="order-1">
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          <div className="rounded-md border border-border bg-bg p-3 text-xs text-muted-foreground">
            <span className="font-medium text-foreground">این مدل کِی مناسب است؟ </span>
            {whenSuitable}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">{input}</CardContent>
      </Card>

      <div className="order-2 space-y-4">
        <FormulaStrip formula={formula} />
        {results}
        {howToRead && (
          <details className="rounded-md border border-border bg-surface p-3 text-sm">
            <summary className="cursor-pointer font-medium text-foreground">چگونه این نتیجه را بخوانیم؟</summary>
            <p className="mt-2 text-muted-foreground">{howToRead}</p>
          </details>
        )}
      </div>
    </div>
  );
}

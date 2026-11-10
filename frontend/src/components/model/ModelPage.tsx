import * as React from "react";
import { Sparkles } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FieldInput } from "./FieldInput";
import { FormulaStrip, ResultStack } from "./ResultParts";
import { EmptyState, ErrorState, IncompleteState, ResultSkeleton } from "./StateViews";
import { useValuation } from "@/hooks/useValuation";
import type { UseValuationResult } from "@/hooks/useValuation";
import type { FieldDef } from "@/config/fields";
import type { FormValues } from "@/lib/request";
import { fieldFromLoc, isShapeError } from "@/lib/apiErrors";
import { loadStoredForm, saveStoredForm } from "@/lib/pageForm";

export interface ModelPageProps<Res> {
  pageKey: string;
  title: string;
  formula: string;
  whenSuitable: string;
  howToRead?: string;
  fields: FieldDef[];
  endpoint: string;
  call: (body: unknown, signal?: AbortSignal) => Promise<Res>;
  sample: FormValues;
  /** Seed the form when there is no stored value for this page (workflow store). */
  seedDefaults?: FormValues;
  validation?: import("@/lib/validation").ValidationOptions;
  buildBody?: (values: FormValues) => unknown;
  /** Extra nodes rendered under the fields (workflow chips, toggles, lists). */
  inputExtras?: (v: UseValuationResult<Res>) => React.ReactNode;
  /** Render the results (hero / cards / chart) from a successful response. */
  renderResult: (res: Res, values: FormValues) => React.ReactNode;
  renderActions?: (res: Res, values: FormValues) => React.ReactNode;
}

/**
 * One template for every model page (spec "Page template"). Input column on the
 * right (~35%), results on the left (~65%); the results area walks through all
 * shared states. Auto-calculation, unit conversion, error handling and per-page
 * form persistence are all centralized here.
 */
export function ModelPage<Res>(props: ModelPageProps<Res>) {
  const {
    pageKey,
    title,
    formula,
    whenSuitable,
    howToRead,
    fields,
    endpoint,
    call,
    sample,
    seedDefaults,
    validation,
    buildBody,
    inputExtras,
    renderResult,
    renderActions,
  } = props;

  const stored = React.useMemo(() => loadStoredForm(pageKey), [pageKey]);
  const v = useValuation<Res>({
    fields,
    endpoint,
    call,
    sample,
    validation,
    buildBody,
    defaults: stored ?? seedDefaults ?? undefined,
  });

  // Persist this page's form values so navigating away does not clear them.
  // The write is debounced while typing, but flushed on unmount so a quick
  // navigation never drops the last edit.
  const latest = React.useRef({ pageKey, values: v.values });
  latest.current = { pageKey, values: v.values };
  React.useEffect(() => {
    const id = window.setTimeout(() => saveStoredForm(pageKey, v.values), 300);
    return () => window.clearTimeout(id);
  }, [pageKey, v.values]);
  React.useEffect(
    () => () => saveStoredForm(latest.current.pageKey, latest.current.values),
    [],
  );

  const shapeFields = React.useMemo(() => {
    if (v.error && isShapeError(v.error)) {
      return new Set(v.error.detail.map((d) => fieldFromLoc(d.loc)).filter(Boolean) as string[]);
    }
    return new Set<string>();
  }, [v.error]);

  const showEmpty = !v.complete && !v.hasResult && !v.error;
  const showIncomplete = v.complete && !v.ready && !v.hasResult;
  const showSkeleton = v.isFirstLoading && !v.hasResult;

  const resultsBody = () => {
    if (v.error) {
      return (
        <div className="space-y-3">
          <ErrorState error={v.error} />
          {v.hasResult && renderResult(v.result as Res, v.values)}
        </div>
      );
    }
    if (showEmpty) return <EmptyState formula={formula} whenSuitable={whenSuitable} onLoadSample={v.loadSample} />;
    if (showIncomplete) return <IncompleteState />;
    if (showSkeleton) return <ResultSkeleton />;
    if (v.hasResult) {
      const updating = v.isFetching && !v.isFirstLoading;
      return (
        <ResultStack updating={updating}>
          <FormulaStrip formula={formula} />
          {renderResult(v.result as Res, v.values)}
          {renderActions?.(v.result as Res, v.values)}
        </ResultStack>
      );
    }
    return <EmptyState formula={formula} whenSuitable={whenSuitable} onLoadSample={v.loadSample} />;
  };

  return (
    <div className="grid grid-cols-1 gap-colgap xl:grid-cols-[minmax(0,35fr)_minmax(0,65fr)]">
      {/* Input column (right in RTL) */}
      <Card className="order-1">
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          <div className="rounded-md border border-border bg-bg p-3 text-xs text-muted-foreground">
            <span className="font-medium text-foreground">این مدل کِی مناسب است؟ </span>
            {whenSuitable}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-4">
            {fields.map((field) => (
              <FieldInput
                key={field.key}
                control={v.control}
                field={field}
                error={v.fieldErrors[field.key] ?? (shapeFields.has(field.key) ? "شکل مقدار نامعتبر است" : undefined)}
              />
            ))}
          </div>
          {inputExtras?.(v)}
          <Button type="button" variant="secondary" size="sm" onClick={v.loadSample} className="w-full">
            <Sparkles className="h-4 w-4" />
            مقادیر نمونه
          </Button>
        </CardContent>
      </Card>

      {/* Results column (left in RTL) */}
      <div className="order-2 space-y-4">
        {resultsBody()}
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

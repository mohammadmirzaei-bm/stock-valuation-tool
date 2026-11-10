/**
 * useValuation — the auto-calculate engine shared by every model page.
 *
 * Behavior implemented once (spec "Behavior"):
 *  - debounced 400 ms after the last keystroke;
 *  - request fires only when the mirrored validation passes;
 *  - TanStack Query keys by the wire body, so a newer request supersedes and
 *    cancels the in-flight one (AbortSignal);
 *  - previous result is kept visible (placeholderData) while the new one loads;
 *  - errors surface as an ApiError union for the shared state views.
 */

import { useMemo } from "react";
import { useForm, useWatch, type Control, type UseFormReturn } from "react-hook-form";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useDebouncedValue } from "@/lib/debounce";
import { buildWire, type FormValues } from "@/lib/request";
import { validateModel, isValid, type ValidationOptions, type FieldErrors } from "@/lib/validation";
import type { FieldDef } from "@/config/fields";
import type { ApiError } from "@/lib/apiErrors";

export interface UseValuationConfig<Res> {
  fields: FieldDef[];
  endpoint: string;
  call: (body: unknown, signal?: AbortSignal) => Promise<Res>;
  sample: FormValues;
  defaults?: FormValues;
  validation?: ValidationOptions;
  /** Override body construction for pages with lists / nested fields. */
  buildBody?: (values: FormValues) => unknown;
}

export interface UseValuationResult<Res> {
  form: UseFormReturn<FormValues>;
  control: Control<FormValues>;
  values: FormValues;
  fieldErrors: FieldErrors;
  complete: boolean;
  ready: boolean;
  body: unknown | null;
  result: Res | undefined;
  error: ApiError | null;
  isFetching: boolean;
  isPlaceholder: boolean;
  isFirstLoading: boolean;
  hasResult: boolean;
  loadSample: () => void;
}

export function useValuation<Res>(config: UseValuationConfig<Res>): UseValuationResult<Res> {
  const { fields, endpoint, call, sample, defaults, validation, buildBody } = config;

  const form = useForm<FormValues>({
    mode: "onChange",
    defaultValues: defaults ?? emptyFor(fields),
  });
  const control = form.control;
  const rawValues = useWatch({ control }) as FormValues;

  const values = useDebouncedValue(rawValues, 400);
  const fieldErrors = useMemo(() => validateModel(values, fields, validation), [values, fields, validation]);
  const complete = useMemo(
    () => fields.every((f) => values[f.key] !== undefined && Number.isFinite(values[f.key] as number)),
    [values, fields],
  );
  const ready = complete && isValid(fieldErrors);

  const body = useMemo(() => {
    if (!ready) return null;
    return buildBody ? buildBody(values) : buildWire(fields, values);
  }, [ready, values, fields, buildBody]);

  const query = useQuery<Res, ApiError>({
    queryKey: [endpoint, body],
    queryFn: ({ signal }) => call(body as unknown, signal),
    enabled: body !== null,
    staleTime: 30_000,
    placeholderData: keepPreviousData,
    retry: false,
  });

  const hasResult = query.data !== undefined;

  return {
    form,
    control,
    values,
    fieldErrors,
    complete,
    ready,
    body,
    result: query.data,
    error: query.error ?? null,
    isFetching: query.isFetching,
    isPlaceholder: query.isPlaceholderData,
    isFirstLoading: query.isPending && body !== null,
    hasResult,
    loadSample: () => form.reset(sample),
  };
}

/** Empty-value defaults so the first render shows the empty state, not errors. */
function emptyFor(fields: FieldDef[]): FormValues {
  const out: FormValues = {};
  for (const f of fields) out[f.key] = undefined;
  return out;
}

import { keepPreviousData, useQuery, type UseQueryResult } from "@tanstack/react-query";
import { useDebouncedValue } from "@/lib/debounce";
import type { ApiError } from "@/lib/apiErrors";

/**
 * Debounced + cancellable query for pages whose request body is built from
 * custom state (arrays, nested objects) rather than a flat field list. Same
 * behavior contract as useValuation: 400 ms debounce, key by body (so newer
 * requests cancel older ones), keep the previous result while refetching.
 */
export function useAutoQuery<T>(
  endpoint: string,
  body: unknown | null,
  call: (body: any, signal?: AbortSignal) => Promise<T>,
  ready = true,
): UseQueryResult<T, ApiError> {
  const debounced = useDebouncedValue(body, 400);
  return useQuery<T, ApiError>({
    queryKey: [endpoint, debounced],
    queryFn: ({ signal }) => call(debounced as any, signal),
    enabled: ready && debounced !== null,
    placeholderData: keepPreviousData,
    staleTime: 30_000,
    retry: false,
  });
}

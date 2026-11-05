import { QueryClient } from "@tanstack/react-query";

/**
 * Shared server-state client. `retry: false` because domain 400s are expected
 * and shouldn't be retried; network failures offer a manual Retry in the UI.
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      refetchOnWindowFocus: false,
      staleTime: 30_000,
    },
  },
});

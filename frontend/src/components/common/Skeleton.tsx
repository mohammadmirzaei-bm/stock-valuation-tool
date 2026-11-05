import { cn } from "@/lib/utils";

/** Loading skeleton block (only used on first load, per spec). */
export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("animate-pulse rounded-md bg-accent/60", className)} />;
}

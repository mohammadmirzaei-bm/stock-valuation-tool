import * as React from "react";
import { useNavigate } from "react-router-dom";
import { Search, Check, CornerDownLeft } from "lucide-react";
import { WORKFLOW_STEPS, EQUITY_GROUP, PORTFOLIO_GROUP, ANALYSIS_TABS } from "@/config/models";
import { useWorkflow } from "@/store/workflow";
import { stepComplete } from "./Stepper";
import { cn } from "@/lib/utils";

interface SearchItem {
  id: string;
  label: string;
  path: string;
  group: string;
  stepId?: string;
}

const ITEMS: SearchItem[] = [
  { id: "overview", label: "نمای کلی", path: "/", group: "فضای کاری" },
  ...WORKFLOW_STEPS.map((s) => ({ id: s.id, label: s.label, path: s.path, group: "گردش کار", stepId: s.id })),
  ...ANALYSIS_TABS.map((t) => ({ id: t.id, label: t.label, path: t.path, group: "گردش کار" })),
  ...EQUITY_GROUP.map((e) => ({ id: e.id, label: e.label, path: e.path, group: "مدل‌های سهام" })),
  ...PORTFOLIO_GROUP.map((p) => ({ id: p.id, label: p.label, path: p.path, group: "پرتفوی" })),
];

/** Normalize Arabic ye/kaf variants so typing either keyboard matches. */
const norm = (s: string) => s.trim().toLowerCase().replace(/ي/g, "ی").replace(/ك/g, "ک");

/**
 * Header search: filters every page and workflow step as you type, with full
 * keyboard support (arrows + Enter, Esc, Ctrl/Cmd+K to focus). Completed
 * workflow steps carry a check so status is visible in the results too.
 */
export function GlobalSearch() {
  const navigate = useNavigate();
  const completed = useWorkflow((s) => s.completed);
  const [query, setQuery] = React.useState("");
  const [open, setOpen] = React.useState(false);
  const [active, setActive] = React.useState(0);
  const rootRef = React.useRef<HTMLDivElement>(null);
  const inputRef = React.useRef<HTMLInputElement>(null);
  const listRef = React.useRef<HTMLDivElement>(null);

  const results = React.useMemo(() => {
    const q = norm(query);
    if (!q) return ITEMS;
    return ITEMS.filter((it) => norm(it.label).includes(q) || it.id.toLowerCase().includes(q));
  }, [query]);

  React.useEffect(() => setActive(0), [query, open]);

  // Global shortcut: Ctrl/Cmd+K focuses the search from anywhere.
  React.useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        inputRef.current?.focus();
        setOpen(true);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  // Close on outside click.
  React.useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDown);
    return () => document.removeEventListener("mousedown", onDown);
  }, [open]);

  const go = (item: SearchItem) => {
    navigate(item.path);
    setQuery("");
    setOpen(false);
    inputRef.current?.blur();
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      setOpen(false);
      inputRef.current?.blur();
      return;
    }
    if (!open || results.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive((i) => (i + 1) % results.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((i) => (i - 1 + results.length) % results.length);
    } else if (e.key === "Enter") {
      e.preventDefault();
      go(results[active]);
    }
  };

  // Keep the active option scrolled into view.
  React.useEffect(() => {
    if (!open) return;
    listRef.current?.querySelector(`[data-index="${active}"]`)?.scrollIntoView({ block: "nearest" });
  }, [active, open]);

  const isMac = typeof navigator !== "undefined" && /Mac|iPhone|iPad/.test(navigator.platform);
  let lastGroup = "";

  return (
    <div ref={rootRef} className="relative min-w-0 flex-1 sm:max-w-md">
      <div className="relative">
        <Search className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
        <input
          ref={inputRef}
          type="search"
          role="combobox"
          aria-expanded={open}
          aria-controls="global-search-listbox"
          aria-activedescendant={open && results.length > 0 ? `search-opt-${active}` : undefined}
          aria-label="جستجوی صفحه‌ها و گام‌های گردش کار"
          placeholder="جستجوی مدل‌ها، گام‌ها و ابزارها…"
          value={query}
          onChange={(e) => { setQuery(e.target.value); setOpen(true); }}
          onFocus={() => setOpen(true)}
          onKeyDown={onKeyDown}
          className="h-9 w-full rounded-lg border border-border bg-surface pr-9 pl-16 text-sm text-foreground placeholder:text-muted-foreground/70 focus:border-primary/30 focus:outline-none focus:ring-2 focus:ring-ring/40"
        />
        <kbd className="pointer-events-none absolute left-2.5 top-1/2 hidden -translate-y-1/2 rounded border border-border bg-surface-2 px-1.5 py-0.5 text-[10px] text-muted-foreground sm:block">
          {isMac ? "⌘K" : "Ctrl K"}
        </kbd>
      </div>

      {open && (
        <div
          ref={listRef}
          id="global-search-listbox"
          role="listbox"
          aria-label="نتایج جستجو"
          className="absolute left-0 right-0 top-full z-50 mt-2 max-h-80 overflow-y-auto rounded-[var(--radius)] border border-border bg-popover p-1.5 shadow-elevated"
        >
          {results.length === 0 && (
            <div className="px-3 py-6 text-center text-sm text-muted-foreground">
              چیزی یافت نشد — نام مدل یا گام دیگری را امتحان کنید.
            </div>
          )}
          {results.map((item, i) => {
            const header = item.group !== lastGroup ? item.group : null;
            lastGroup = item.group;
            const done = item.stepId ? stepComplete(completed, item.stepId) : false;
            return (
              <React.Fragment key={item.id}>
                {header && (
                  <div className="px-3 pb-1 pt-2 text-[11px] font-semibold text-muted-foreground first:pt-1">{header}</div>
                )}
                <div
                  id={`search-opt-${i}`}
                  role="option"
                  aria-selected={i === active}
                  data-index={i}
                  onMouseEnter={() => setActive(i)}
                  onMouseDown={(e) => { e.preventDefault(); go(item); }}
                  className={cn(
                    "flex cursor-pointer items-center gap-2.5 rounded-lg px-3 py-2 text-sm",
                    i === active ? "bg-surface-3 text-foreground" : "text-foreground/80",
                  )}
                >
                  <span className={cn("h-1.5 w-1.5 shrink-0 rounded-full", done ? "bg-positive" : "bg-muted-foreground/50")} />
                  <span className="min-w-0 flex-1 truncate">{item.label}</span>
                  {done && <Check className="h-3.5 w-3.5 shrink-0 text-positive" aria-label="کامل شده" />}
                  {i === active && <CornerDownLeft className="h-3.5 w-3.5 shrink-0 text-muted-foreground" aria-hidden />}
                </div>
              </React.Fragment>
            );
          })}
        </div>
      )}
    </div>
  );
}
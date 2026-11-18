import { useNavigate } from "react-router-dom";
import { Info, CheckCircle2, AlertTriangle, TriangleAlert, Check, BellOff } from "lucide-react";
import { usePersistentState } from "@/hooks/usePersistentState";
import { cn } from "@/lib/utils";

export interface Insight {
  id: string;
  tone: "info" | "positive" | "warning" | "negative";
  title: string;
  body: string;
  to?: string;
}

const toneMeta = {
  info: { Icon: Info, cls: "text-brand", bg: "bg-brand/10" },
  positive: { Icon: CheckCircle2, cls: "text-positive", bg: "bg-positive/10" },
  warning: { Icon: AlertTriangle, cls: "text-warning", bg: "bg-warning/10" },
  negative: { Icon: TriangleAlert, cls: "text-negative", bg: "bg-negative/10" },
} as const;

/**
 * Derived, live insights (the workspace's notifications). Read state persists
 * per insight id so marking read survives a refresh; an insight disappears
 * when its underlying condition no longer holds. Never color alone — each
 * carries an icon and a text label.
 */
export function NotificationsCard({ insights }: { insights: Insight[] }) {
  const navigate = useNavigate();
  const [read, setRead] = usePersistentState<string[]>("overview-read-notifs", []);
  const readSet = new Set(read);
  const unread = insights.filter((i) => !readSet.has(i.id));

  const markRead = (id: string) => {
    if (!readSet.has(id)) setRead([...read, id]);
  };
  const markAll = () => setRead(Array.from(new Set([...read, ...insights.map((i) => i.id)])));

  return (
    <section className="metric-card flex flex-col p-4" aria-label="اعلان‌ها">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold">
          اعلان‌ها
          {unread.length > 0 && (
            <span className="num mr-1.5 rounded-full bg-brand/10 px-1.5 py-px text-[10px] font-semibold text-brand">{unread.length}</span>
          )}
        </h3>
        {unread.length > 0 && (
          <button type="button" onClick={markAll} className="text-xs text-muted-foreground transition-colors hover:text-brand">
            خواندن همه
          </button>
        )}
      </div>

      {insights.length === 0 ? (
        <div className="flex flex-1 flex-col items-center justify-center gap-2 py-8 text-center text-muted-foreground">
          <BellOff className="h-5 w-5" aria-hidden />
          <p className="text-xs">اعلان جدیدی نیست — گردش کار را ادامه دهید.</p>
        </div>
      ) : (
        <ul className="space-y-1">
          {insights.map((n) => {
            const { Icon, cls, bg } = toneMeta[n.tone];
            const isRead = readSet.has(n.id);
            return (
              <li
                key={n.id}
                className={cn("flex items-start gap-2.5 rounded-lg px-2 py-2 transition-colors hover:bg-surface-2", isRead && "opacity-55")}
              >
                <span className={cn("mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full", bg, cls)} aria-hidden>
                  <Icon className="h-3.5 w-3.5" />
                </span>
                <button
                  type="button"
                  onClick={() => { markRead(n.id); if (n.to) navigate(n.to); }}
                  className="min-w-0 flex-1 text-right"
                >
                  <span className="block text-sm font-medium text-foreground">{n.title}</span>
                  <span className="mt-0.5 block text-xs leading-5 text-muted-foreground">{n.body}</span>
                </button>
                {!isRead && (
                  <button
                    type="button"
                    onClick={() => markRead(n.id)}
                    title="خواندم"
                    aria-label={`خواندم: ${n.title}`}
                    className="mt-0.5 shrink-0 rounded-full p-1 text-muted-foreground transition-colors hover:bg-surface-3 hover:text-positive"
                  >
                    <Check className="h-3.5 w-3.5" />
                  </button>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
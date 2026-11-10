import { Plus, Trash2, Send } from "lucide-react";
import { SplitLayout } from "@/components/layout/SplitLayout";
import { NumberField } from "@/components/model/NumberField";
import { Hero, ComponentCards, ResultStack } from "@/components/model/ResultParts";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { BoxPlot } from "@/components/charts/BoxPlot";
import { ErrorState, ResultSkeleton } from "@/components/model/StateViews";
import { PrerequisiteChecklist } from "@/components/model/PrerequisiteChecklist";
import { postMultiples } from "@/api/endpoints";
import type { MultiplesRequest, ImpliedValuationResult, MultipleKind, PeerMultipleInput } from "@/api/types";
import { useAutoQuery } from "@/hooks/useAutoQuery";
import { usePersistentState } from "@/hooks/usePersistentState";
import { useWorkflow, type FootballRangeInput } from "@/store/workflow";
import { useFormat } from "@/hooks/useFormat";
import { missingPrereqs } from "@/lib/prerequisites";
import { MULTIPLES_SAMPLE } from "@/lib/samples";

interface KindMeta {
  label: string;
  metricLabel: string;
  formula: string;
  ev: boolean;
}

const KINDS: Record<MultipleKind, KindMeta> = {
  pe: { label: "P/E", metricLabel: "سود خالص", formula: "P/E = Price / EPS", ev: false },
  pb: { label: "P/B", metricLabel: "حقوق صاحبان سهام دفتری", formula: "P/B = Price / Book value of equity", ev: false },
  ps: { label: "P/S", metricLabel: "درآمد", formula: "P/S = Market cap / Revenue", ev: false },
  ev_ebitda: { label: "EV/EBITDA", metricLabel: "EBITDA", formula: "EV = multiple × EBITDA ;  Equity = EV + Cash − Debt − MI − Preferred", ev: true },
  ev_sales: { label: "EV/Sales", metricLabel: "فروش", formula: "EV = multiple × Sales ;  Equity = EV + Cash − Debt − MI − Preferred", ev: true },
};

type PeerRow = { name: string; value: number };

interface MultiplesState {
  kind: MultipleKind;
  metric: number;
  sharesOutstanding: number;
  cash: number;
  debt: number;
  minorityInterest: number;
  preferredEquity: number;
  peers: PeerRow[];
}

const INITIAL: MultiplesState = {
  kind: "pe",
  metric: 0,
  sharesOutstanding: 0,
  cash: 0,
  debt: 0,
  minorityInterest: 0,
  preferredEquity: 0,
  peers: [],
};

export function MultiplesPage() {
  const fmt = useFormat();
  const wf = useWorkflow();
  // Persisted like every other page; the shared balance sheet only seeds the
  // first visit (stored values win afterwards).
  const [state, setState] = usePersistentState<MultiplesState>("multiples", {
    ...INITIAL,
    sharesOutstanding: wf.balanceSheet.sharesOutstanding || 0,
    cash: wf.balanceSheet.cash,
    debt: wf.balanceSheet.debt,
    minorityInterest: wf.balanceSheet.minorityInterest,
    preferredEquity: wf.balanceSheet.preferredEquity,
  });

  const meta = KINDS[state.kind];
  const patch = (p: Partial<MultiplesState>) => setState((s) => ({ ...s, ...p }));

  const validPeers = state.peers.filter((p) => p.name.trim() && p.value > 0);
  const uniqueNames = new Set(state.peers.map((p) => p.name.trim())).size === state.peers.length;
  const ready =
    state.metric > 0 &&
    state.sharesOutstanding > 0 &&
    state.peers.length >= 3 &&
    uniqueNames &&
    validPeers.length >= 3;

  // Shares outstanding is the one shared prerequisite (canonically set on the
  // DCF page); metric and peers are entered right here, so they are local gaps.
  const missing = missingPrereqs(["shares"], {
    forecast: null,
    wacc: null,
    shares: state.sharesOutstanding,
    taxRate: null,
    marketPrice: null,
  });
  const local = [
    ...(state.metric > 0 ? [] : ["شاخص انتخاب‌شده باید بیشتر از صفر باشد."]),
    ...(validPeers.length >= 3 ? [] : ["دست‌کم ۳ همتا با ضریب مثبت وارد کنید."]),
    ...(uniqueNames ? [] : ["نام همتاها باید یکتا باشد."]),
  ];

  const peers: PeerMultipleInput[] = state.peers
    .filter((p) => p.name.trim())
    .map((p) => ({ name: p.name.trim(), value: p.value }));

  const body: MultiplesRequest | null = ready
    ? {
        kind: state.kind,
        metric: state.metric,
        shares_outstanding: state.sharesOutstanding,
        peers,
        cash: meta.ev ? state.cash : 0,
        debt: meta.ev ? state.debt : 0,
        minority_interest: meta.ev ? state.minorityInterest : 0,
        preferred_equity: meta.ev ? state.preferredEquity : 0,
      }
    : null;

  const query = useAutoQuery<ImpliedValuationResult>("multiples", body, postMultiples, ready);
  const res = query.data;

  const loadSample = () =>
    setState({
      kind: MULTIPLES_SAMPLE.kind,
      metric: MULTIPLES_SAMPLE.metric,
      sharesOutstanding: MULTIPLES_SAMPLE.shares_outstanding,
      cash: MULTIPLES_SAMPLE.cash,
      debt: MULTIPLES_SAMPLE.debt,
      minorityInterest: MULTIPLES_SAMPLE.minority_interest,
      preferredEquity: MULTIPLES_SAMPLE.preferred_equity,
      peers: MULTIPLES_SAMPLE.peers.map((p) => ({ ...p })),
    });

  const sendRange = () => {
    if (!res) return;
    const range: FootballRangeInput = {
      method: "Multiples",
      low: res.low.value_per_share,
      mid: res.mid.value_per_share,
      high: res.high.value_per_share,
      source: "از ضرایب همتا",
    };
    wf.upsertRange(range);
    wf.completeStep("multiples");
  };

  const excluded = new Set(res?.statistics.excluded_names ?? []);

  return (
    <SplitLayout
      title="گام ۵: ضرایب همتایان (ارزش‌گذاری نسبی)"
      formula={meta.formula}
      whenSuitable="ارزش هدف را با ضریب‌های شرکت‌های همتا می‌سنجد؛ ضریب‌های غیرمثبت همتا از آماره حذف می‌شوند."
      howToRead="چارک‌ها و میانهٔ ضریب همتایان، بازهٔ ارزش هر سهم را می‌سازند. کارت‌ها کمینه/میانه/بیشینه و میانگین را نشان می‌دهند."
      input={
        <>
          <Tabs value={state.kind} onValueChange={(v) => patch({ kind: v as MultipleKind })}>
            <TabsList className="flex-wrap">
              {(Object.keys(KINDS) as MultipleKind[]).map((k) => (
                <TabsTrigger key={k} value={k}>
                  {KINDS[k].label}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>

          <div className="grid grid-cols-2 gap-3">
            <NumberField label={`شاخص: ${meta.metricLabel}`} suffix={fmt.moneySuffix} value={state.metric} onChange={(v) => patch({ metric: v ?? 0 })} min={0} />
            <NumberField label="تعداد سهام" suffix="سهم" value={state.sharesOutstanding} onChange={(v) => patch({ sharesOutstanding: v ?? 0 })} min={0} />
          </div>

          {meta.ev && (
            <div className="grid grid-cols-2 gap-3">
              <NumberField label="نقد" suffix={fmt.moneySuffix} value={state.cash} onChange={(v) => patch({ cash: v ?? 0 })} min={0} />
              <NumberField label="بدهی" suffix={fmt.moneySuffix} value={state.debt} onChange={(v) => patch({ debt: v ?? 0 })} min={0} />
              <NumberField label="منافع اقلیت" suffix={fmt.moneySuffix} value={state.minorityInterest} onChange={(v) => patch({ minorityInterest: v ?? 0 })} min={0} />
              <NumberField label="سهام ممتاز" suffix={fmt.moneySuffix} value={state.preferredEquity} onChange={(v) => patch({ preferredEquity: v ?? 0 })} min={0} />
            </div>
          )}

          <div className="space-y-2">
            <div className="text-sm text-muted-foreground">همتاها (حداقل ۳ با ضریب مثبت)</div>
            {state.peers.map((p, i) => (
              <div key={i} className="flex items-end gap-2">
                <div className="grid flex-1 gap-1.5">
                  {i === 0 && <span className="text-xs text-muted-foreground">نام</span>}
                  <Input
                    value={p.name}
                    onChange={(e) => patch({ peers: state.peers.map((x, idx) => (idx === i ? { ...x, name: e.target.value } : x)) })}
                    className={cnInput(excluded.has(p.name.trim()))}
                    aria-label="نام همتا"
                  />
                </div>
                <div className="grid flex-1 gap-1.5">
                  {i === 0 && <span className="text-xs text-muted-foreground">ضریب</span>}
                  <NumberField label="" value={p.value} onChange={(v) => patch({ peers: state.peers.map((x, idx) => (idx === i ? { ...x, value: v ?? 0 } : x)) })} compact />
                </div>
                <Button type="button" variant="ghost" size="icon" aria-label="حذف همتا" onClick={() => patch({ peers: state.peers.filter((_, idx) => idx !== i) })}>
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))}
            <Button type="button" variant="outline" size="sm" onClick={() => patch({ peers: [...state.peers, { name: "", value: 0 }] })}>
              <Plus className="h-4 w-4" /> افزودن همتا
            </Button>
            {!uniqueNames && state.peers.length > 0 && <p className="text-xs text-negative">نام همتاها باید یکتا باشد.</p>}
          </div>

          <Button type="button" variant="secondary" size="sm" onClick={loadSample}>
            استفاده از مقادیر نمونه
          </Button>
        </>
      }
      results={
        !ready ? (
          <PrerequisiteChecklist missing={missing} local={local} />
        ) : query.isPending && !res ? (
          <ResultSkeleton />
        ) : query.error ? (
          <ErrorState error={query.error} />
        ) : res ? (
          <ResultStack updating={query.isFetching}>
            <Hero label={`ارزش هر سهم (میانهٔ ${meta.label})`} value={fmt.number(res.mid.value_per_share)} />
            <ComponentCards
              items={[
                { label: `کمینه (Q1): ${fmt.number(res.low.multiple)}`, value: fmt.number(res.low.value_per_share), hint: "ارزش هر سهم" },
                { label: `میانه: ${fmt.number(res.mid.multiple)}`, value: fmt.number(res.mid.value_per_share), hint: "ارزش هر سهم" },
                { label: `بیشینه (Q3): ${fmt.number(res.high.multiple)}`, value: fmt.number(res.high.value_per_share), hint: "ارزش هر سهم" },
                { label: `میانگین: ${fmt.number(res.mean.multiple)}`, value: fmt.number(res.mean.value_per_share), hint: "ارزش هر سهم" },
              ]}
            />
            {meta.ev && (
              <ComponentCards
                items={[
                  { label: "ارزش بنگاه (میانه)", value: fmt.number(res.mid.implied_enterprise_value ?? 0) },
                  { label: "ارزش سهام (میانه)", value: fmt.number(res.mid.implied_equity_value) },
                ]}
              />
            )}
            <Card className="p-3">
              <div className="mb-1 text-sm text-muted-foreground">توزیع ضریب همتایان</div>
              <BoxPlot stats={res.statistics} />
              {res.statistics.excluded_count > 0 && (
                <p className="mt-2 text-xs text-muted-foreground">
                  کنارگذاشته‌شده ({res.statistics.excluded_count}): {res.statistics.excluded_names.join("، ")} — ضریب غیرمثبت
                </p>
              )}
            </Card>
            <Button type="button" size="sm" onClick={sendRange}>
              <Send className="h-4 w-4" /> ارسال بازه به زمین فوتبال
            </Button>
          </ResultStack>
        ) : null
      }
    />
  );
}

function cnInput(excludedPeer: boolean): string {
  return excludedPeer ? "border-border text-muted-foreground opacity-60" : "";
}

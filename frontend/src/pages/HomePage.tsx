import { useNavigate } from "react-router-dom";
import { ArrowLeft, BarChart3, Layers3, PieChart, RotateCcw, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { HomeDiagram } from "@/components/layout/HomeDiagram";
import { EQUITY_GROUP, PORTFOLIO_GROUP } from "@/config/models";
import { useWorkflow } from "@/store/workflow";

export function HomePage() {
  const navigate = useNavigate();
  const loadSample = useWorkflow((s) => s.loadSample);
  const reset = useWorkflow((s) => s.reset);

  return (
    <div className="dashboard-home space-y-7">
      <section className="dashboard-hero relative overflow-hidden rounded-3xl border border-primary/20 p-6 sm:p-9">
        <div className="relative z-10 max-w-2xl space-y-5">
          <div className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
            <BarChart3 className="h-3.5 w-3.5" /> فضای تحلیل و ارزش‌گذاری
          </div>
          <div className="space-y-3">
            <h2 className="text-2xl font-bold leading-relaxed sm:text-3xl">تصمیم‌های بهتر، با تحلیل روشن‌تر</h2>
            <p className="max-w-xl text-sm leading-7 text-muted-foreground sm:text-base">
              از پیش‌بینی جریان‌های نقدی تا مقایسه مدل‌ها، مسیر ارزش‌گذاری را گام‌به‌گام پیش ببرید.
            </p>
          </div>
          <div className="flex flex-wrap gap-3 pt-1">
            <Button type="button" onClick={() => navigate("/forecast")}>
              شروع ارزش‌گذاری <ArrowLeft className="h-4 w-4" />
            </Button>
            <Button type="button" variant="outline" onClick={() => { loadSample(); navigate("/dcf"); }}>
              <Sparkles className="h-4 w-4" /> شروع با نمونه
            </Button>
          </div>
        </div>
        <div className="hero-art pointer-events-none absolute inset-y-0 left-0 hidden w-2/5 items-center justify-center lg:flex" aria-hidden="true">
          <div className="hero-art-orbit hero-art-orbit-outer" />
          <div className="hero-art-orbit hero-art-orbit-inner" />
          <div className="hero-art-icon"><BarChart3 className="h-12 w-12" strokeWidth={1.3} /></div>
          <span className="hero-art-dot hero-art-dot-one" />
          <span className="hero-art-dot hero-art-dot-two" />
        </div>
      </section>

      <section className="space-y-4">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div className="space-y-1">
            <div className="text-xs font-medium text-primary">مسیر تحلیل</div>
            <h2 className="text-xl font-bold">گردش کار ارزش‌گذاری</h2>
            <p className="text-sm text-muted-foreground">هر مرحله را انتخاب کنید و پیشرفت خود را دنبال کنید.</p>
          </div>
          <Button type="button" variant="ghost" size="sm" onClick={() => { reset(); navigate("/"); }}>
            <RotateCcw className="h-4 w-4" /> بازنشانی گردش کار
          </Button>
        </div>
        <HomeDiagram />
      </section>

      <section className="space-y-4">
        <div className="space-y-1"><div className="text-xs font-medium text-primary">ابزارهای بیشتر</div><h2 className="text-xl font-bold">تحلیل خود را کامل کنید</h2></div>
        <div className="grid gap-4 md:grid-cols-2">
          {[
            { title: "مدل‌های سهام عادی", description: "ارزش سهام را با مدل‌های مختلف بررسی کنید.", icon: Layers3, items: EQUITY_GROUP },
            { title: "پرتفوی", description: "ترکیب دارایی‌ها و عملکرد سبد را تحلیل کنید.", icon: PieChart, items: PORTFOLIO_GROUP },
          ].map(({ title, description, icon: Icon, items }) => (
            <div key={title} className="dashboard-tool-card rounded-2xl border border-border bg-surface p-5 sm:p-6">
              <div className="mb-5 flex items-start gap-4">
                <div className="tool-icon flex h-11 w-11 shrink-0 items-center justify-center rounded-xl"><Icon className="h-5 w-5" /></div>
                <div><h3 className="text-base font-bold">{title}</h3><p className="mt-1 text-sm leading-6 text-muted-foreground">{description}</p></div>
              </div>
              <div className="flex flex-wrap gap-2">
                {items.map((item) => <button key={item.id} type="button" onClick={() => navigate(item.path)} className="tool-link inline-flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-xs transition-colors hover:border-primary hover:text-primary">{item.label}<ArrowLeft className="h-3 w-3" /></button>)}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

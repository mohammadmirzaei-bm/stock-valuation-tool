import { useNavigate, Link } from "react-router-dom";
import { ArrowLeft, Layers3, PieChart, RotateCcw, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ConfirmDialog, RESET_DIALOG_COPY, useConfirmDialog } from "@/components/common/ConfirmDialog";
import { HomeDiagram } from "@/components/layout/HomeDiagram";
import { EQUITY_GROUP, PORTFOLIO_GROUP } from "@/config/models";
import { useWorkflow } from "@/store/workflow";

export function HomePage() {
  const navigate = useNavigate();
  const loadSample = useWorkflow((s) => s.loadSample);
  const reset = useWorkflow((s) => s.reset);
  const confirm = useConfirmDialog();

  return (
    <div className="dashboard-home space-y-7">
      <section className="flex flex-wrap items-center justify-between gap-3">
        <div className="min-w-0 space-y-1">
          <h2 className="text-lg font-bold">از کجا شروع کنیم؟</h2>
          <p className="text-sm text-muted-foreground">
            مسیر شش‌گامهٔ ارزش‌گذاری را از پیش‌بینی جریان نقدی شروع کنید و گام‌به‌گام پیش بروید.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button asChild type="button" size="sm">
            <Link to="/forecast">
              شروع ارزش‌گذاری <ArrowLeft className="h-4 w-4" />
            </Link>
          </Button>
          <Button type="button" variant="outline" size="sm" onClick={() => { loadSample(); navigate("/dcf"); }}>
            <Sparkles className="h-4 w-4" /> شروع با نمونه
          </Button>
          <Button type="button" variant="ghost" size="sm" onClick={confirm.request}>
            <RotateCcw className="h-4 w-4" /> بازنشانی
          </Button>
        </div>
      </section>

      <section className="space-y-3">
        <HomeDiagram />
      </section>

      <section className="space-y-4">
        <div className="space-y-1"><div className="text-xs font-medium text-primary">ابزارهای بیشتر</div><h2 className="text-xl font-bold">تحلیل خود را کامل کنید</h2></div>
        <div className="grid gap-4 md:grid-cols-2">
          {[
            { title: "مدل‌های سهام عادی", description: "ارزش سهام را با مدل‌های مختلف بررسی کنید.", icon: Layers3, items: EQUITY_GROUP },
            { title: "پرتفوی", description: "ترکیب دارایی‌ها و عملکرد سبد را تحلیل کنید.", icon: PieChart, items: PORTFOLIO_GROUP },
          ].map(({ title, description, icon: Icon, items }) => (
            <div key={title} className="rounded-2xl border border-border bg-surface p-5 sm:p-6">
              <div className="mb-5 flex items-start gap-4">
                <div className="tool-icon flex h-11 w-11 shrink-0 items-center justify-center rounded-xl"><Icon className="h-5 w-5" /></div>
                <div><h3 className="text-base font-bold">{title}</h3><p className="mt-1 text-sm leading-6 text-muted-foreground">{description}</p></div>
              </div>
              <div className="flex flex-wrap gap-2">
                {items.map((item) => (
                  <Link
                    key={item.id}
                    to={item.path}
                    className="tool-link inline-flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-xs transition-colors hover:border-primary hover:text-primary"
                  >
                    {item.label}
                    <ArrowLeft className="h-3 w-3" aria-hidden />
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      <ConfirmDialog
        open={confirm.open}
        onOpenChange={confirm.onOpenChange}
        {...RESET_DIALOG_COPY}
        onConfirm={() => { reset(); navigate("/"); }}
      />
    </div>
  );
}
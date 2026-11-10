import * as React from "react";
import { useParams, BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import { TooltipProvider } from "@/components/ui/tooltip";
import { queryClient } from "@/lib/queryClient";
import { Layout } from "@/components/layout/Layout";
import { HomePage } from "@/pages/HomePage";

// One chunk per page: ECharts and the heavier models load on first visit,
// not on the home page. HomePage stays eager for an instant first paint.
const EquityPage = React.lazy(() => import("@/pages/equity/EquityPages").then((m) => ({ default: m.EquityPage })));
const ForecastPage = React.lazy(() => import("@/pages/workflow/ForecastPage").then((m) => ({ default: m.ForecastPage })));
const WaccPage = React.lazy(() => import("@/pages/workflow/WaccPage").then((m) => ({ default: m.WaccPage })));
const DcfPage = React.lazy(() => import("@/pages/workflow/DcfPage").then((m) => ({ default: m.DcfPage })));
const AnalysesPage = React.lazy(() => import("@/pages/workflow/AnalysesPage").then((m) => ({ default: m.AnalysesPage })));
const MultiplesPage = React.lazy(() => import("@/pages/workflow/MultiplesPage").then((m) => ({ default: m.MultiplesPage })));
const FootballPage = React.lazy(() => import("@/pages/workflow/FootballPage").then((m) => ({ default: m.FootballPage })));
const PortfolioStatisticsPage = React.lazy(() => import("@/pages/portfolio/PortfolioStatisticsPage").then((m) => ({ default: m.PortfolioStatisticsPage })));
const PortfolioOptimizerPage = React.lazy(() => import("@/pages/portfolio/PortfolioOptimizerPage").then((m) => ({ default: m.PortfolioOptimizerPage })));

function EquityRoute() {
  const { id } = useParams();
  return <EquityPage id={id ?? ""} />;
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider delayDuration={200}>
        <BrowserRouter>
          <Routes>
            <Route element={<Layout />}>
              <Route index element={<HomePage />} />
              <Route path="/forecast" element={<ForecastPage />} />
              <Route path="/wacc" element={<WaccPage />} />
              <Route path="/dcf" element={<DcfPage />} />
              <Route path="/analyses" element={<AnalysesPage />} />
              <Route path="/multiples" element={<MultiplesPage />} />
              <Route path="/football-field" element={<FootballPage />} />
              <Route path="/portfolio/statistics" element={<PortfolioStatisticsPage />} />
              <Route path="/portfolio/optimize" element={<PortfolioOptimizerPage />} />
              <Route path="/equity/:id" element={<EquityRoute />} />
              {/* Legacy slug → canonical registry id (the model is keyed "supernormal"). */}
              <Route path="/equity/supernormal-growth" element={<Navigate to="/equity/supernormal" replace />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  );
}

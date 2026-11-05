import { useParams, BrowserRouter, Route, Routes } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import { TooltipProvider } from "@/components/ui/tooltip";
import { queryClient } from "@/lib/queryClient";
import { Layout } from "@/components/layout/Layout";
import { HomePage } from "@/pages/HomePage";
import { EquityPage } from "@/pages/equity/EquityPages";
import { ForecastPage } from "@/pages/workflow/ForecastPage";
import { WaccPage } from "@/pages/workflow/WaccPage";
import { DcfPage } from "@/pages/workflow/DcfPage";
import { AnalysesPage } from "@/pages/workflow/AnalysesPage";
import { MultiplesPage } from "@/pages/workflow/MultiplesPage";
import { FootballPage } from "@/pages/workflow/FootballPage";
import { PortfolioStatisticsPage } from "@/pages/portfolio/PortfolioStatisticsPage";
import { PortfolioOptimizerPage } from "@/pages/portfolio/PortfolioOptimizerPage";

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
            </Route>
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  );
}

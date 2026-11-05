/**
 * Typed endpoint map. One POST call per backend endpoint; the response type
 * comes straight from the generated schema. The request bodies are already in
 * wire form (rates as decimals) — building them from percent form values is
 * the model layer's job (see config/models + endpoints callers).
 */

import { apiPost } from "@/lib/api";
import { VALUATION_BASE, PORTFOLIO_BASE } from "@/lib/api";
import type * as T from "./types";

function valuation<TReq, TRes>(path: string) {
  return (body: TReq, signal?: AbortSignal) =>
    apiPost<TRes>(`${VALUATION_BASE}/${path}`, body, signal);
}
function portfolio<TReq, TRes>(path: string) {
  return (body: TReq, signal?: AbortSignal) =>
    apiPost<TRes>(`${PORTFOLIO_BASE}/${path}`, body, signal);
}

// Standalone equity models
export const postSinglePeriod = valuation<T.SinglePeriodRequest, T.SinglePeriodResult>("single-period");
export const postZeroGrowth = valuation<T.ZeroGrowthRequest, T.ZeroGrowthResult>("zero-growth");
export const postAnnualDividendYield = valuation<T.AnnualDividendYieldRequest, T.AnnualDividendYieldResult>("annual-dividend-yield");
export const postGordon = valuation<T.GordonRequest, T.GordonResult>("gordon");
export const postSupernormal = valuation<T.SupernormalRequest, T.SupernormalResult>("supernormal-growth");
export const postDividendProjection = valuation<T.DividendProjectionRequest, T.DividendProjectionResult>("dividend-projection");
export const postExpectedReturn = valuation<T.ExpectedReturnRequest, T.ExpectedReturnResult>("expected-return");
export const postCapm = valuation<T.CapmRequest, T.CapmResult>("capm");
export const postPreferredStock = valuation<T.PreferredStockRequest, T.PreferredStockResult>("preferred-stock");
export const postRiskPremium = valuation<T.RiskPremiumRequest, T.RiskPremiumResult>("risk-premium");
export const postGrowthOpportunities = valuation<T.GrowthOpportunitiesRequest, T.GrowthOpportunitiesResult>("growth-opportunities");
export const postSustainableGrowth = valuation<T.SustainableGrowthRequest, T.SustainableGrowthResult>("sustainable-growth");
export const postPeg = valuation<T.PegRequest, T.PegResult>("peg");

// Cost of capital
export const postWacc = valuation<T.WaccRequest, T.WaccResult>("wacc");

// DCF workflow
export const postForecast = valuation<T.ForecastRequest, T.ForecastResult>("forecast");
export const postDcf = valuation<T.DcfRequest, T.DcfResult>("dcf");
export const postDcfScenarios = valuation<T.DcfScenarioRequest, T.DcfScenarioResult>("dcf-scenarios");
export const postDcfSensitivity = valuation<T.DcfSensitivityRequest, T.DcfSensitivityResult>("dcf-sensitivity");
export const postReverseDcf = valuation<T.ReverseDcfRequest, T.ReverseDcfResult>("reverse-dcf");

// Relative valuation
export const postMultiples = valuation<T.MultiplesRequest, T.ImpliedValuationResult>("multiples");
export const postFootballField = valuation<T.FootballFieldRequest, T.FootballFieldResult>("football-field");

// Portfolio
export const postPortfolioStatistics = portfolio<T.PortfolioStatisticsRequest, T.PortfolioStatisticsResult>("statistics");
export const postPortfolioOptimize = portfolio<T.PortfolioOptimizeRequest, T.PortfolioAnalysisResult>("optimize");

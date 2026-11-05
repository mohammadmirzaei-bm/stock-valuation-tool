/**
 * Convenience aliases over the generated OpenAPI schema.
 *
 * Every request/response type here comes from `src/api/schema.d.ts`
 * (`openapi-typescript`), so they never drift from the backend's Pydantic
 * models. Never hand-write a response type — regenerate instead.
 */

import type { components } from "./schema";

type S = components["schemas"];

// ----- Requests -----
export type SinglePeriodRequest = S["SinglePeriodRequest"];
export type ZeroGrowthRequest = S["ZeroGrowthRequest"];
export type AnnualDividendYieldRequest = S["AnnualDividendYieldRequest"];
export type GordonRequest = S["GordonRequest"];
export type SupernormalRequest = S["SupernormalRequest"];
export type DividendProjectionRequest = S["DividendProjectionRequest"];
export type ExpectedReturnRequest = S["ExpectedReturnRequest"];
export type CapmRequest = S["CapmRequest"];
export type PreferredStockRequest = S["PreferredStockRequest"];
export type RiskPremiumRequest = S["RiskPremiumRequest"];
export type GrowthOpportunitiesRequest = S["GrowthOpportunitiesRequest"];
export type SustainableGrowthRequest = S["SustainableGrowthRequest"];
export type PegRequest = S["PegRequest"];
export type WaccRequest = S["WaccRequest"];
export type ForecastRequest = S["ForecastRequest"];
export type CashFlowProjectionInput = S["CashFlowProjectionInput"];
export type DcfRequest = S["DcfRequest"];
export type DcfScenarioInput = S["DcfScenarioInput"];
export type DcfScenarioRequest = S["DcfScenarioRequest"];
export type DcfSensitivityRequest = S["DcfSensitivityRequest"];
export type ReverseDcfRequest = S["ReverseDcfRequest"];
export type PeerMultipleInput = S["PeerMultipleInput"];
export type MultiplesRequest = S["MultiplesRequest"];
export type ValuationRangeInput = S["ValuationRangeInput"];
export type FootballFieldRequest = S["FootballFieldRequest"];
export type PriceSeriesInput = S["PriceSeriesInput"];
export type PortfolioStatisticsRequest = S["PortfolioStatisticsRequest"];
export type PortfolioOptimizeRequest = S["PortfolioOptimizeRequest"];

// ----- Responses -----
export type SinglePeriodResult = S["SinglePeriodResult"];
export type ZeroGrowthResult = S["ZeroGrowthResult"];
export type AnnualDividendYieldResult = S["AnnualDividendYieldResult"];
export type GordonResult = S["GordonResult"];
export type SupernormalResult = S["SupernormalResult"];
export type SupernormalScheduleRow = S["SupernormalScheduleRow"];
export type DividendProjectionResult = S["DividendProjectionResult"];
export type ExpectedReturnResult = S["ExpectedReturnResult"];
export type CapmResult = S["CapmResult"];
export type PreferredStockResult = S["PreferredStockResult"];
export type RiskPremiumResult = S["RiskPremiumResult"];
export type GrowthOpportunitiesResult = S["GrowthOpportunitiesResult"];
export type RetentionCurvePointResult = S["RetentionCurvePointResult"];
export type SustainableGrowthResult = S["SustainableGrowthResult"];
export type PegInterpretation = S["PegInterpretation"];
export type PegResult = S["PegResult"];
export type WaccResult = S["WaccResult"];
export type ForecastYearRowResult = S["ForecastYearRowResult"];
export type ForecastResult = S["ForecastResult"];
export type FcffYearRowResult = S["FcffYearRowResult"];
export type DcfResult = S["DcfResult"];
export type ScenarioRowResult = S["ScenarioRowResult"];
export type DcfScenarioResult = S["DcfScenarioResult"];
export type DcfSensitivityResult = S["DcfSensitivityResult"];
export type ReverseDcfResult = S["ReverseDcfResult"];
export type PeerStatisticsResult = S["PeerStatisticsResult"];
export type ImpliedCaseResult = S["ImpliedCaseResult"];
export type ImpliedValuationResult = S["ImpliedValuationResult"];
export type FootballFieldRowResult = S["FootballFieldRowResult"];
export type FootballFieldResult = S["FootballFieldResult"];
export type PortfolioStatisticsResult = S["PortfolioStatisticsResult"];
export type AssetPointResult = S["AssetPointResult"];
export type PortfolioPointResult = S["PortfolioPointResult"];
export type AllocationPointResult = S["AllocationPointResult"];
export type CapitalAllocationLineResult = S["CapitalAllocationLineResult"];
export type CompletePortfolioResult = S["CompletePortfolioResult"];
export type PortfolioAnalysisResult = S["PortfolioAnalysisResult"];

export type MultipleKind = MultiplesRequest["kind"];

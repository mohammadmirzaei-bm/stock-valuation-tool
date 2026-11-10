# Architecture Map

Mermaid maps of the codebase, generated from actual imports in the source.

## 1. System overview

Two-tier app: a React SPA talks to a FastAPI service whose routes wrap pure-Python domain functions.

```mermaid
flowchart LR
    subgraph FE["frontend/ — React SPA (Vite + TS)"]
        UI["Pages + components\n(ECharts, Tailwind, shadcn-style ui/)"]
        STATE["Zustand stores\n(workflow, portfolio, settings)"]
        QUERY["TanStack Query +\nreact-hook-form"]
        UI --- STATE --- QUERY
    end
    subgraph BE["stock_valuation/ — FastAPI service"]
        API["api/ — routes + Pydantic schemas\nCORS, error handlers"]
        DOM["domain/ — pure functions\n(stdlib only, no scipy/plotly)"]
        API --> DOM
    end
    QUERY -- "HTTP POST /api/valuation/*, /api/portfolio/*" --> API
    TESTS["tests/ — pytest\n(domain + api + layering guard)"] -.-> DOM
    TESTS -.-> API
```

## 2. Backend layering (`stock_valuation/`)

`stock_valuation/api/main.py` mounts two routers; every route module delegates to one domain module. The domain is a strict DAG — `tests/domain/test_layering.py` enforces the import direction.

```mermaid
flowchart TD
    subgraph main["api/main.py — FastAPI app (CORS + domain-error → HTTP 400)"]
        subgraph VAL["router: /api/valuation"]
            rEq["routes/equity\n13 endpoints"]
            rCap["routes/capital\nwacc"]
            rDcf["routes/dcf\ndcf"]
            rDA["routes/dcf_analysis\nscenarios, sensitivity, reverse"]
            rFc["routes/forecast"]
            rMu["routes/multiples"]
            rFf["routes/football_field"]
            rCom["routes/_common"]
        end
        subgraph PRT["router: /api/portfolio"]
            rPo["portfolio\nstatistics, optimize"]
        end
    end
    subgraph domain["domain/ — pure modules"]
        err["errors.py"]
        val["validators.py"]
        lin["_linalg.py"]
        br["bridge.py"]
        eq["equity.py"]
        coc["cost_of_capital.py"]
        dcf["dcf.py"]
        da["dcf_analysis.py"]
        fc["forecast.py"]
        mu["multiples.py"]
        ff["football_field.py"]
        po["portfolio.py"]
        pa["portfolio_analysis.py"]
        ps["portfolio_stats.py"]
        vm["valuation_models.py\n(legacy façade)"]
        st["self_tests.py"]
    end
    rEq --> eq; rCap --> coc; rDcf --> dcf; rDA --> da
    rFc --> fc; rMu --> mu; rFf --> ff; rPo --> pa & ps
    val --> err
    br & eq & coc & ps --> val
    dcf & mu --> br & val
    da --> dcf; fc --> dcf
    ff --> da & mu
    po --> lin
    pa --> po
    vm --> eq & coc & dcf & da
    st --> vm
```

## 3. Frontend architecture (`frontend/src/`)

```mermaid
flowchart TD
    M["main.tsx"] --> A["App.tsx — react-router"]
    A --> L["Layout + Sidebar"]
    A --> P["Pages"]
    subgraph PAGES["pages/"]
        HP["HomePage"]
        WF["Workflow: Forecast, Wacc, Dcf,\nAnalyses, Multiples, Football"]
        PO2["Portfolio: Statistics, Optimizer"]
        EQ2["EquityPages (/equity/:id)"]
    end
    P --> PAGES
    WF -- "reads/writes shared step state" --> SW["store/workflow.ts\n(Zustand + localStorage persist)"]
    PO2 --> SP["store/portfolio.ts"]
    PAGES --> HV["hooks: useValuation (400 ms debounce,\nvalidation gate, abort superseded requests)\nuseAutoQuery, useFormat"]
    HV --> EP["api/endpoints.ts\ntyped POST map"]
    EP --> LA["lib/api.ts — apiPost →\nVITE_API_BASE_URL (default :8000)"]
    PAGES --> CH["components/charts/ — ECharts\n(Chart.tsx, theme, FootballField, Waterfall…)"]
    PAGES --> UI["components/ui + model + common"]
    REQ["lib/request, validation, semantics,\nprerequisites, samples"] --> HV
```

## 4. Page → endpoint flow (the student workflow)

```mermaid
flowchart LR
    F["ForecastPage"] -- "POST /forecast\nrows → store" --> DC["DcfPage"]
    W["WaccPage"] -- "POST /wacc\nrate → store" --> DC
    DC -- "POST /dcf" --> AN["AnalysesPage"]
    AN -- "POST /dcf-scenarios\n/dcf-sensitivity /reverse-dcf" --> FF
    MU2["MultiplesPage"] -- "POST /multiples\nrange → store" --> FF["FootballPage"]
    FF -- "POST /football-field\n(collected ranges)" --> OUT["Composite valuation"]
    PS2["PortfolioStatisticsPage"] -- "POST /api/portfolio/statistics" --> OPT["PortfolioOptimizerPage"]
    OPT -- "POST /api/portfolio/optimize" --> CGL["Efficient frontier / CAL"]
```

## Key takeaways

- The backend keeps a hard three-layer contract: routes → schemas → pure domain, with stdlib-only math in `stock_valuation/domain/_linalg.py`.
- The frontend centralizes all backend access in `frontend/src/api/endpoints.ts`; request/response types are generated from the OpenAPI schema (`frontend/src/api/schema.d.ts`).
- `frontend/src/store/workflow.ts` is the pipeline memory that chains Forecast → WACC → DCF → Analyses → Football Field, persisted to localStorage.

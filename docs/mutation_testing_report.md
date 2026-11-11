# Mutation testing report — portfolio family and DCF analysis

Status: two iterations completed 2026-11-10. **Iteration 1** changed tests
only. **Iteration 2** added the covariance PSD contract to
`stock_valuation/domain/validators.py` (with matching docstrings in
`portfolio.py`) and the tests that pin it. §2 reports both campaigns;
§2.2 is the current measured state.

## 1. Context and scope

The repository uses mutmut 3.8.1 to mutate the pure domain layer. The
configuration limits mutation to `stock_valuation/domain/*` and the reference
suite to `tests/domain/`
(`setup.cfg:3-7`).

The starting campaign reported 3,901 mutants: 3,059 killed and 842 survived.
A lexical triage script (development aid, not committed) split the 842
survivors into 629 message-string candidates and 213 non-string logic
candidates. Iteration 1 addressed the 131 logic candidates in:

| Module | Logic survivors at start |
|---|---:|
| `stock_valuation/domain/portfolio.py` | 47 |
| `stock_valuation/domain/portfolio_analysis.py` | 20 |
| `stock_valuation/domain/portfolio_stats.py` | 31 |
| `stock_valuation/domain/dcf_analysis.py` | 33 |
| **Total** | **131** |

Goals:

1. Add tests only where the mutation changes observable behaviour.
2. Record why residual mutants survive, without treating "current tests do not
   distinguish it" as equivalence.
3. Re-run mutmut from a clean cache and report measured, not projected,
   results.

Out of scope for iteration 1: the 629 lexical string-only candidates, the 82
non-string candidates in other domain modules, and production-code changes. Two
`validators.py` mutants were also killed in the final campaign; they are
outside the four-module scope.

### Iteration 2 scope — covariance positive semidefiniteness

Iteration 2 closes risk §7.1. `validate_covariance_matrix` now rejects
non-PSD matrices after the existing shape, finiteness, symmetry,
non-negative-diagonal, and pairwise-correlation checks
(`stock_valuation/domain/validators.py:590-614`):

- `PSD_TOLERANCE = 1e-12` is scaled as
  `PSD_TOLERANCE * max(1.0, max_diag)` (`validators.py:73,591`).
- The factorisation is symmetric Gaussian elimination with complete diagonal
  pivoting. Each Schur update is mirrored into the lower triangle, because a
  later complete pivot can read that triangle.
- A pivot `diag < -tol` raises `ValidationError`. A pivot `diag <= tol` enters
  the singular branch: the remaining block is scanned for diagonals below
  `-tol` and off-diagonals above `tol`, then the scan stops.
- Singular PSD input (perfect correlation, zero-variance assets) stays valid
  at validation time; singularity remains the solver's concern.

The paired tests are `TestCovariancePSD`
(`tests/domain/test_portfolio_stats.py:312`) plus the reworked guards in
`TestDeferredMutationGaps` (`tests/domain/test_portfolio.py:512`).

## 2. Measured result

### 2.1 Iteration 1 — tests only

Both test runners are green on the unmutated code:

- `pytest tests -q`: **469 passed**
- `python -m unittest discover -s tests -t .`: **469 passed**

The suite grew from 411 to 469 tests (**58 new**). The final mutation campaign
used a fresh `mutants/` cache and produced the same 3,901 mutant IDs as the
baseline.

| Metric | Baseline | Final | Change |
|---|---:|---:|---:|
| Mutants | 3,901 | 3,901 | same IDs |
| Killed | 3,059 | **3,147** | **+88** |
| Survived | 842 | **754** | **-88** |
| Raw score (killed / total) | 78.42% | **80.67%** | +2.26 pp |

The 88 kills comprise:

- **86** in the four requested modules;
- **2** adjacent kills in `validators.py`
  (`validate_covariance_matrix__mutmut_65/71`, the `>`/`>=` tolerance
  boundaries in covariance validation at
  `stock_valuation/domain/validators.py:564-579`). Iteration 2 reverses the
  first of these: with a PSD gate, `mutmut_65` is no longer distinguishable
  (see §5.5).

Of the 86 scheduled targets, **84 were killed**. All **35** follow-up targets
were killed; of the first batch, **49 of 51** were killed. The two residual
covariance mutants are discussed in §5.3. Two extra reverse-DCF mutants
(`reverse_dcf_implied_growth__mutmut_59/63`) were also killed by the new
midpoint/endpoint fixtures, giving 84 scheduled + 4 additional = 88.

#### Per-module result (iteration 1)

| Module | Baseline killed / survived | Final killed / survived |
|---|---:|---:|
| `portfolio.py` | 397 / 58 | **432 / 23** |
| `portfolio_analysis.py` | 174 / 24 | **185 / 13** |
| `portfolio_stats.py` | 147 / 52 | **162 / 37** |
| `dcf_analysis.py` | 380 / 70 | **405 / 45** |

#### Survivor split (iteration 1)

The split below uses the original lexical classifier. It is a triage policy,
not a semantic-equivalence proof.

| Survivor class | Baseline | Final |
|---|---:|---:|
| Message-string candidates | 629 | 629 |
| Non-string logic candidates | 213 | **125** |
| — of which, four requested modules | 131 | **45** |
| — of which, other modules | 82 | 80 |
| **Total survivors** | **842** | **754** |

### 2.2 Iteration 2 — PSD validation (current state)

Both runners are green on the unmutated code:

- `pytest tests -q`: **483 passed**
- `python -m unittest discover -s tests -t .`: **483 passed**

The suite grew from 469 to 483 tests (**+14**): 13 new `TestCovariancePSD`
cases and one split guard (§3).

Unlike iteration 1, this campaign did **not** start from a cleared `mutants/`
cache. Only the changed source files were re-mutated and the cache was reused
for unchanged ones, so the totals below are the current state of the tree, not
a clean-cache replay of iteration 1's four modules.

| Metric | Iteration 1 final | Iteration 2 | Change |
|---|---:|---:|---:|
| Mutants | 3,901 | **3,972** | +71 |
| Killed | 3,147 | **3,204** | +57 |
| Survived | 754 | **768** | +14 |
| Raw score (killed / total) | 80.67% | **80.66%** | −0.01 pp |

#### Files touched by iteration 2

| Module | Killed / survived | Mutants |
|---|---:|---:|
| `validators.py` | 280 / 163 | 443 |
| `portfolio.py` | 432 / 23 | 455 |

`portfolio.py` keeps the iteration-1 split (432 / 23): no portfolio mutant was
resurrected, and the `_gmv_weights` zero-total guard is still killed
(`x__gmv_weights__mutmut_16`, `total <= 0` → `< 0`).

The covariance function inside `validators.py` is 110 killed / 34 survived out
of 144 mutants:

| Region of `validate_covariance_matrix` | Killed / survived | Mutants |
|---|---:|---:|
| Pre-existing checks (`__mutmut_1-75`) | 52 / 23 | 75 |
| PSD block (`__mutmut_76-144`) | **58 / 11** | 69 |

All 11 PSD-block survivors are non-logic: nine message-string mutations and
two equivalents (§5.5). Every boundary and algorithmic mutation in the block
is killed — `mutmut_102` (`diag <= -tol`), `103` (`diag < +tol`), `107`
(`diag < tol`), `112` (`rem[i][i] <= -tol`), `113` (`< +tol`), `124`
(`abs(rem[i][j]) >= tol`), `80/85` (tolerance scaling), `89-97` (pivot
selection and its ranges), and `141-144` (factor, elimination update, and the
lower-triangle mirror).

Removing the unreachable `default=0.0` fallback from `max_diag` deleted four
mutants, three of which had survived; that is the only source change made
after the first iteration-2 run.

## 3. Tests added

The iteration-1 additions are plain `unittest.TestCase`, standard library
only, and keep the repository's Persian docstring style. No new dependency was
introduced. Private helpers are imported only where the public path cannot
express the contract, following the existing precedent of importing
`_complete_portfolio` (`tests/domain/test_portfolio_analysis.py:22`).
Iteration 2 follows the same rules.

| File and class | Tests | Main purpose |
|---|---:|---|
| `test_portfolio.py` — `TestMutationGaps` (`:389`) | 8 | 9-asset bypass in performance helpers, negative-variance clamp, zero-volatility Sharpe, GMV/tangency support selection |
| `test_portfolio.py` — `TestTangencyMutationGaps` (`:451`) | 7 | zero-total rejection/skip, zero-excess rejection, singular/clipped/tie support cases |
| `test_portfolio.py` — `TestClipLongOnly` (`:496`) | 4 | `1e-12` clipping boundary, zero total, normalization |
| `test_portfolio.py` — `TestDeferredMutationGaps` (`:512`) | 12 | exact tolerance boundaries, non-PSD counterexample, KKT general constraint, zero-variance support search |
| `test_portfolio_analysis.py` — `TestAnalysisMutationGaps` (`:265`) | 8 | default long-only, zero-variance assets, exact Boolean flags, overflow-to-zero weight, exact leverage boundary |
| `test_portfolio_analysis.py` — `TestAssetPoints` (`:317`) | 1 | direct `_assets` Boolean-variance guard |
| `test_portfolio_stats.py` — `TestStatisticsMutationGaps` (`:255`) | 4 | Boolean observation, non-sequence input, de-meaned covariance, name/series mismatch |
| `test_portfolio_stats.py` — `TestCorrelationBoundaries` (`:278`) | 5 | exact diagonal, positive/negative clipping, exact tolerance, subnormal over-tolerance |
| `test_dcf_analysis.py` — new methods (`:84,256,292,440,471,481,492,502`) | 10 | market-price preservation, bridge-item pass-through, axis quantization, reverse-DCF endpoint/tolerance/fallback behaviour |
| **Total** | **58** | |

No new test asserts on a Persian error-message string. That was deliberate:
message text is the 629-candidate class and is not considered behaviour for
this campaign. Iteration 2 keeps the same policy, which is why its nine
message-string mutants remain survivors (§5.5).

### Iteration 2 tests

| File and class | Tests | Main purpose |
|---|---:|---|
| `test_portfolio_stats.py` — `TestCovariancePSD` (new, `:312`) | 13 | non-PSD rejection, singular PSD acceptance, flat-subspace scan, exact `±PSD_TOLERANCE` boundaries, complete diagonal pivoting, scale floor of the tolerance, tolerated asymmetry, `statistics_from_prices` integration |

Iteration 2 also reworked four iteration-1 tests so the new contract does not
hide the guards they were written for:

- `test_gmv_short_zero_total_is_calculation_error` was split. The public call
  is now `test_gmv_non_psd_is_validation_error` (`test_portfolio.py:525`), and
  the zero-total guard is asserted on `_gmv_weights` directly (`:531`), the
  same private-helper precedent used for `_complete_portfolio`.
- `test_exact_negative_variance_tolerance_is_clamped` now calls `_performance`
  directly, because the public path rejects its indefinite matrix at
  validation.
- `test_tangency_zero_variance_solvable_support_is_skipped` rescaled the third
  variance to `2e6`, keeping the flat direction inside the scaled tolerance so
  the zero-variance support branch is still reached.
- `TestCorrelationBoundaries` and `test_correlation_above_one_tolerance` still
  assert the `_correlation()` clipping, but the covariance validator now
  raises on the same input through the PSD gate.

### Iteration 3 tests

| File and class | Tests | Main purpose |
|---|---:|---|
| `test_portfolio_stats.py` — `TestCenteringFloatingPoint` (new) | 2 | large mean offset (`1e8`, `1e6`) centering residual; kills `sample_statistics__mutmut_39/40` |
| `test_portfolio.py` — `TestTangencyMutationGaps` | 1 | exact `(1/3,2/3)` normalization; kills `tangency_portfolio__mutmut_65` |
| `test_portfolio_analysis.py` — `TestAnalysisMutationGaps` / `TestAssetPoints` | 2 | negative-weight clip via helper; signed-zero volatility; kills `_complete_portfolio__mutmut_23-26`, `_assets__mutmut_13/16` |
| `test_dcf_analysis.py` — `TestReverseDcf` | 7 | width-fallback gate: three bridge-scale accept fixtures, one accumulated-rounding accept, one large-share-count reject, plus two round-trip guards; the pre-existing cancellation case now expects `CalculationError`; kills 11 `reverse_dcf_implied_growth` mutants |

All are plain `unittest.TestCase`, standard library only, Persian docstrings,
and no error-message-text assertions. The reverse-DCF fixtures were verified
to reproduce bit-identically on Python 3.11.4 and 3.12.14.

## 4. Behaviour covered

### Portfolio performance and clipping

- `portfolio_performance` and `portfolio_point` call
  `_prepare(..., True)` (`stock_valuation/domain/portfolio.py:155,185`), so the
  eight-asset long-only cap at `:96` must not apply. A nine-asset equal-weight
  case now locks that distinction.
- Negative variance larger than `VARIANCE_NEGATIVE_TOLERANCE` must raise, while
  a small negative becomes zero (`:108-118`). The exact boundary
  `variance == -1e-12` is now covered.
- A zero-volatility point with a risk-free rate must raise
  `CalculationError`, not produce an undefined Sharpe (`:131-133`).
- `_clip_long_only` accepts a negative weight exactly at
  `LONG_ONLY_WEIGHT_TOLERANCE`, clips it, and rejects non-positive totals
  (`:196-204`).
- `_kkt_weights` is a general equality-constrained solver, not only a
  sum-of-weights solver; the general-contract case is now tested (`:207-220`).

### Long-only minimum variance and tangency

- Support enumeration, singular-support skipping, clipped-support skipping,
  the first-support tie rule, and the two `RETURN_MATCH_TOLERANCE` boundaries
  are covered (`portfolio.py:223-263`).
- `_gmv_weights` rejects a non-positive total solution (`:266-276`).
- Tangency covers zero total with shorting, zero total in long-only,
  zero maximum excess, unsolvable supports, zero-variance candidates, and the
  tie rule (`:341-386`).
- The frontier tests cover the exact minimum-range rejection and the final
  target being assigned directly from the maximum return, avoiding cancellation
  (`:430-443`).

### Portfolio analysis

- The default `allow_short=False` is now distinguished from short mode using a
  fixture whose long-only optimum is a corner
  (`stock_valuation/domain/portfolio_analysis.py:274-312`).
- Zero-variance assets produce volatility `0.0` without division by zero
  (`:254-271`).
- `_complete_portfolio` flags are exact booleans; positive excess that rounds to
  zero weight is not reported as a defensive clip, and zero variance with
  positive excess raises `CalculationError` (`:195-234`).

### Portfolio statistics

- Boolean observations and non-sequence containers are rejected
  (`stock_valuation/domain/portfolio_stats.py:72-78,88-119`).
- De-meaning is tested with non-zero means, because the original
  `_RETURNS` fixture has zero means and cannot detect a dropped centering term
  (`:196-206`).
- `statistics_from_prices` rejects a name/series count mismatch (`:263-290`).
- Correlation tests cover the exactly assigned unit diagonal, positive and
  negative round-off clipping, the exact `1 + CORRELATION_TOLERANCE` boundary,
  and a subnormal case whose raw correlation is about 1.004975 and must raise
  (`:240-260`).

### Covariance validation (PSD contract)

- A pairwise-valid but globally indefinite matrix is rejected: equal variances
  with correlations `(0.9, 0.9, -0.9)` and the documented counterexample
  `[[1, -1, 0.5], [-1, 1, 0.5], [0.5, 0.5, 1]]` (`validators.py:590-614`).
- Singular matrices stay valid: perfect correlation `[[1,1],[1,1]]`, a
  zero-variance row/column, and the all-zero matrix
  (`test_singular_psd_accepted`).
- The flat branch is entered at `diag <= tol`; residuals in the remaining
  block are then scanned (`mutmut_107` is killed by an exact-`tol` case).
- Both tolerance directions are pinned: a final pivot of exactly
  `-PSD_TOLERANCE` passes and `-1.01 · PSD_TOLERANCE` raises
  (`mutmut_102`), and flat-block diagonals/off-diagonals use the same
  inclusive bound (`mutmut_112/124`).
- The tolerance floor is tested at three scales, so `max(1.0, max_diag)` cannot
  be replaced by `min` or a constant (`mutmut_80/85`).
- Complete diagonal pivoting is exercised by matrices whose leading diagonal
  is not the largest, and the input list stays unmodified.
- Tolerated asymmetry is averaged before the factorisation, so the result does
  not depend on which triangle holds the larger value.
- `statistics_from_prices` output — including low-volatility daily returns —
  feeds `validate_covariance_matrix` directly for three amplitudes and two
  annualisation factors.

### DCF analysis

- `dcf_scenario_valuation` preserves `market_price` in the aggregate result
  (`stock_valuation/domain/dcf_analysis.py:299`).
- Sensitivity passes cash, debt, minority interest, and preferred equity to
  both the base call and off-centre cells
  (`:368-378,409-418,427`).
- Sensitivity axes are quantized to ten decimal places, so eleventh-digit
  input noise does not leak into the matrix.
- Reverse DCF preserves bridge items at both search endpoints and returns the
  endpoint growth on exact endpoint prices (`:495-507,589-590`).
- Relative tolerance for large prices and absolute tolerance for small prices
  are both covered (`:516-540`).
- The width fallback is characterized in §7.2 (`:531-547`).

## 5. Residual survivors: classification and confidence

The following statements are deliberately scoped. None of them is a global
proof that a mutant is unobservable.

### 5.1 Equivalent under the current contract

| Mutants | Scope and evidence |
|---|---|
| `_supports__mutmut_7` | The extra support size is `n + 1`, and `combinations(range(n), n + 1)` is empty (`portfolio.py:190-193`). |
| `_performance__mutmut_17` | Entering the clamp when variance equals zero still returns numerical zero (`portfolio.py:113-118`). |
| `_correlation__mutmut_7/28/32` | Initialization is overwritten, or an equality branch assigns the same boundary value (`portfolio_stats.py:244-259`). |
| `reverse_dcf_implied_growth__mutmut_66/70/89` | Equality is shadowed by the preceding positive-tolerance branch (`dcf_analysis.py:516-540`). |

### 5.2 Caller-scoped unreachable, not globally dead

`_complete_portfolio__mutmut_23-26` mutate the original negative-weight branch
(`portfolio_analysis.py:218-220`). With a validated positive risk aversion and
positive excess, that branch is not reached. Direct helper calls with invalid
arguments can reach it, so "globally unreachable" would be too strong. These
remain survivors and are not counted as equivalents.

### 5.3 Unproven or deliberately deferred

| Mutants | Status |
|---|---|
| `sample_statistics__mutmut_39/40` | **Residual, exact-arithmetic equivalence only.** Flipping one centering sign adds `2·mean_x·Σ(y_t−mean_y)`, which is zero in exact arithmetic. Floating-point equivalence is not proven, and the mutants survive all 469 tests (`portfolio_stats.py:196-206`). |
| `_long_only_min_variance__mutmut_17` | Renormalization gives an exact-arithmetic argument, not a floating-point proof. |
| `_assets__mutmut_13/16` | Numerically equivalent for validated non-negative finite diagonals, but signed-zero and direct-helper domains are not fully classified (`portfolio_analysis.py:263-269`). |
| `reverse_dcf_implied_growth__mutmut_60/64/86/93/77` | No global equivalence proof; some are tolerance or iteration-bound policy cases. |
| 629 message-string candidates | Excluded by testing policy, not proven semantically irrelevant. The lexical classifier drops whole string tokens, including f-string expressions, and accepts string-to-`None` changes, so semantic review is still required for an adjusted score. |

### 5.4 Corrected classifications

The first triage demoted several mutants as equivalent that counterexamples
showed to be observable. They were reinstated and are now killed:

- `_kkt_weights__mutmut_23` — the general equality-constraint case returns
  `[1,0]`, not `[1,1]`.
- `tangency_portfolio__mutmut_41/77/79` — no-solvable-support error type,
  zero-variance skip, and `continue` versus `break` optimum.
- `_long_only_min_variance__mutmut_2/22/26` — exhausted numeric supports and
  the exact return-tolerance boundaries.
- `efficient_frontier__mutmut_26/37/40` — exact `1e-9` range and the
  cancellation-sensitive final target.
- `_performance__mutmut_19` and `_complete_portfolio__mutmut_21` — exact
  negative-variance tolerance and a positive-excess weight that rounds to zero.
- `_correlation__mutmut_14/15/16/24/26/29/30/31/34/35/36/37` — diagonal
  round-off, clipping, exact tolerance, and a subnormal sample.
- DCF `dcf_sensitivity__mutmut_46/56`,
  `reverse_dcf_implied_growth__mutmut_47/53/85/95/96/97/98/99` — axis
  quantization, relative/absolute endpoint tolerance, midpoint termination, and
  the width fallback. Separately, `reverse_dcf_implied_growth__mutmut_59/63`
  were killed by the first-batch midpoint/endpoint fixtures.

This correction matters: several numerical mutations are only equivalent for
the fixtures used during the plan review, not as a general property.

### 5.5 Iteration 2 survivors in the PSD block

| Mutants | Status |
|---|---|
| `__mutmut_104/105/106`, `114/115/116`, `125/126/127` | **Message-string candidates.** The three `raise ValidationError(...)` sites mutated to `None`, an `XX…XX` wrapper, and a lowercased `(psd)`. Type and control flow are unchanged; the project policy for this class is unchanged from iteration 1. |
| `__mutmut_98` | **Equivalent.** The swap condition became `<=`. `max(range(k, size), key=...)` returns the first maximum, so whenever `rem[k][k]` is maximal, `pivot_idx == k` and the swap is a no-op. |
| `__mutmut_128` | **Equivalent.** `break` became `return`. The flat-subspace scan is the last statement before the elimination loop that the `break` also skips, so both leave the function. |
| `__mutmut_65` (pre-existing region) | **Demoted from killed to survived.** `abs(correlation) >= 1 + CORRELATION_TOLERANCE` cannot be observed any more: a correlation above 1 makes the matrix indefinite, so the PSD gate raises the same `ValidationError` type. The mutant is equivalent under the new contract, not lost coverage. |
| `__mutmut_67` (pre-existing region) | Same argument with `2.0 + CORRELATION_TOLERANCE`: every input the relaxed bound would admit is rejected by the PSD gate. |

### 5.6 Iteration 3 — residual logic survivor triage

This iteration closes §9 item 3 for the four in-scope modules
(`portfolio.py`, `portfolio_analysis.py`, `portfolio_stats.py`,
`dcf_analysis.py`). It starts from the floating-point precision mutants
(`sample_statistics__mutmut_39/40`, `_long_only_min_variance__mutmut_17`)
and triages every remaining non-string logic survivor.

Both runners are green on the unmutated code, on Python 3.11.4 (base) and
3.12.14 (`finance`):

- `pytest tests -q`: **495 passed**
- `python -m unittest discover -s tests -t .`: **495 OK**

The suite grew from 483 to 495 (**+12**, §3). Twenty logic mutants were
killed; the rest are classified below. The touched modules were re-run from
a cleared per-file cache (test-only edits do not invalidate mutmut verdicts).

#### Per-module result

| Module | Killed / survived | Mutants | Logic survivors |
|---|---:|---:|---:|
| `portfolio.py` | 433 / 22 | 455 | 4 (all equivalent) |
| `portfolio_analysis.py` | 191 / 7 | 198 | 0 |
| `portfolio_stats.py` | 164 / 35 | 199 | 11 (8 equivalent, 3 caller-scoped) |
| `dcf_analysis.py` | 428 / 56 | 484 | 13 (7 equivalent, 6 deferred) |

The other 92 survivors across the four modules are message-string
candidates, excluded by the unchanged testing policy (§5.3).

#### Killed in this iteration

| Mutants | Fixture |
|---|---|
| `sample_statistics__mutmut_39/40` | Large mean offset (`1e8`, `1e6`) with small variations: flipping one centering sign adds `2·mean_x·Σ(y_t−mean_y)`, a non-zero IEEE-754 residual that breaks `assertAlmostEqual` on covariance/correlation (`TestCenteringFloatingPoint`). |
| `tangency_portfolio__mutmut_65` | Excess `(1,2)` with identity covariance gives weights exactly `(1/3,2/3)`; multiply-instead-of-divide normalization shifts one ulp. |
| `_assets__mutmut_13/16` | Negative-zero variance diagonal: `math.copysign` distinguishes `+0.0` from `−0.0` volatility. |
| `_complete_portfolio__mutmut_23-26` | Direct helper call with negative risk aversion reaches the negative-weight clip branch; the §5.2 caller-scoped mutants are now killed via the helper precedent. |
| `reverse_dcf_implied_growth__mutmut_97/98/103/109/112/113/114/121/122/132/133` | Width-fallback gate (§7.2): three lateral-accept cases (cash / preferred-equity / minority-interest dominant bridge) and one large-share-count reject case. |

#### Step B — `_long_only_min_variance__mutmut_17` is equivalent in IEEE-754

The mutation doubles the single-constraint KKT right-hand side
(`rhs = [1.0]` → `[2.0]`, `portfolio.py:249`). No floating-point boundary
fixture can distinguish it, for two independent reasons:

1. **Exact ×2 commutes through renormalization.** The KKT system is linear
   in `rhs`, so the raw solution doubles. Multiplication by 2 is exact in
   IEEE-754 (exponent shift, no mantissa rounding, no overflow for
   sum-to-one weights). `_clip_long_only` (`portfolio.py:206-214`) preserves
   sign, so the same components clip, and renormalizes by the total:
   `(2·a)/(2·b) == a/b` bit-for-bit. The returned weights, the variance
   `dot(w, Σw)`, and the strict `<` support comparison are identical.
2. **The absolute clip gate is shadowed by support dominance.** The gate
   `min(weights) < -LONG_ONLY_WEIGHT_TOLERANCE` (`1e-12`) is absolute, so
   doubling could push a tiny negative weight past it. But any support whose
   weights clip to zero on a subset yields a feasible portfolio on that
   subset whose variance is ≥ the subset's own KKT minimum. Subsets are
   enumerated first (`_supports` yields ascending sizes) and the comparison
   is strict (`variance < best_variance`), so a clipping support can never
   win — whether it passes or fails the gate.

Corroboration: 20,000 random PSD 2–3 asset fixtures produced zero
distinguishing outputs, and the mutant survives all 495 tests.
`_gmv_weights__mutmut_13` (`[1.0]*n` → `[2.0]*n`, `portfolio.py:282`) is the
same ×2-renormalization equivalence on the allow-short path.

#### Equivalent logic survivors (final)

| Mutants | Scope and evidence |
|---|---|
| `_gmv_weights__mutmut_13`, `_long_only_min_variance__mutmut_17` | ×2 RHS cancels exactly in renormalization; clip gate shadowed by support dominance (above). |
| `_performance__mutmut_17` | `variance < 0` → `<= 0`: at zero the clamp still returns numerical zero. |
| `_supports__mutmut_7` | Extra size `n+1`: `combinations(range(n), n+1)` is empty (`portfolio.py:200`). |
| `_copy_series__mutmut_10` | Sentinel `length = -1` → `-2`: only its sign is tested (`length < 0`); overwritten on the first iteration (`portfolio_stats.py:99-105`). |
| `_correlation__mutmut_7/28/32` | Initialization overwritten; `>1.0`→`>=1.0` and `<-1.0`→`<=-1.0` assign the same boundary value (`portfolio_stats.py:244-259`). |
| `sample_statistics__mutmut_1` | `_MIN_RETURN_OBSERVATIONS=2 <= SAMPLE_COVARIANCE_DDOF=1` is false; `<` is also false — guard body never runs (`portfolio_stats.py:185`). |
| `sample_statistics__mutmut_8` | `positive=False` → `None`: both falsy in `if positive and number <= 0` (`portfolio_stats.py:115`). |
| `sample_statistics__mutmut_26/31` | Zero initialization overwritten; symmetric fill from `range(asset_count)` recomputes already-mirrored entries identically (`portfolio_stats.py:197-199`). |
| `reverse_dcf_implied_growth__mutmut_66/70/89` | Equality shadowed by the preceding positive-tolerance branch (`dcf_analysis.py:523-540`). |
| `reverse_dcf_implied_growth__mutmut_77` | `range(200)` → `201`: the loop always exits earlier via convergence or the `high-low < 1e-12` fallback. |
| `reverse_dcf_implied_growth__mutmut_108` | Dropping `abs(EV)` from the bridge max: in the fallback regime heavy cancellation forces `debt+mi+pe ≈ EV+cash`, so the sum `≥ abs(EV)` and the max is unchanged. 0 kills in 20,000 mixed trials. |
| `reverse_dcf_implied_growth__mutmut_110/115` | The `1.0` floor (→ drop / → `2.0`): the fallback is only reached when the per-share rounding noise `ulp(bridge)/shares` exceeds `1e-9`, forcing `bridge ≫ 2`; the floor never binds. 0 kills in 20,000 mixed trials. |

#### Caller-scoped unreachable (final)

| Mutants | Upstream validator |
|---|---|
| `_copy_series__mutmut_4` | `len(values)==0` → `==1`: `validate_asset_count` requires `MIN_ASSETS=2`, so a single-asset series raises the same `ValidationError` type regardless (`portfolio_stats.py:95-97`, `validators.py:475`). |
| `_copy_series__mutmut_17/18` | `length < 0` → `<= 0` / `< 1`: an empty series (`length==0`) always fails the `length < min_length` check (`min_length ≥ 2`), so re-entering the first-series branch is never observed (`portfolio_stats.py:104-109`). |

#### Deferred boundary / policy survivors (reverse-DCF gate)

`reverse_dcf_implied_growth__mutmut_60/64/86/93` (`<=`↔`<` at the exact
price/width tolerance) and `125` (`>`→`>=` at `residual == acceptance_tolerance`)
are measure-zero knife-edges; `124` (`ulp(1.0)`→`ulp(2.0)`, a factor-2 band)
needs `residual ∈ (atol, 2·atol]`, not found in 40,000 randomized reject
trials. These remain deferred with the §7.2 fallback product decision
(§9 item 2); they are tolerance-policy cases, not proven equivalents.

## 6. Confidence and information gaps

**High confidence**

- Kill counts: iteration 1 was verified from a complete clean-cache run with
  identical mutant IDs, and all kills were checked against the saved baseline
  status. Iteration 2 was read from the cache-backed run and cross-checked
  against the per-file exit codes in `mutants/stock_valuation/domain/*.py.meta`.
- Test results: both runners pass on the unmutated code after each campaign.
- The 49-of-51 and 35-of-35 target outcomes are measured, not projected.

**Medium confidence**

- The scoped equivalence statements in §5.1. They follow from source structure
  and small counterexample checks, but were not formally verified.
- Some exact-float assertions are fixture-dependent by design (for example
  `[1,0]` weights and `[[2,2],[2,2]]` covariance). They pass consistently in
  the recorded environment; a platform with different floating-point behaviour
  should be checked before treating them as portable.

**Known gaps**

- The 45 in-scope survivors and 80 logic survivors in other modules have not
  been individually proven equivalent.
- The 629 message-string survivors are untriaged semantically. Iteration 2 adds
  nine more of the same class in the PSD block.
- `validators.py` now carries 163 survivors, 34 of them inside
  `validate_covariance_matrix`; the other 129 sit in validators that iteration
  2 did not touch.
- The iteration-2 campaign reused the `mutants/` cache instead of clearing it,
  so its totals are not a clean-cache replay of iteration 1.
- No adjusted mutation score is reported, because a defensible adjustment
  requires the semantic review above.

## 7. Risks discovered

Iteration 1 recorded two risks and changed neither. Iteration 2 resolved the
first; the second is still open.

### 7.1 Covariance validation does not check positive semidefiniteness — resolved in iteration 2

Iteration 1 recorded that `validate_covariance_matrix` checked shape,
finiteness, symmetry, non-negative diagonal, and pairwise implied correlation
but not PSD, while the linear solver checks pivots rather than definiteness
(`stock_valuation/domain/_linalg.py:195-225`).

The matrix previously accepted by validation was:

```text
[[ 1, -1,  0.5],
 [-1,  1,  0.5],
 [ 0.5, 0.5, 1]]
```

For `min_variance_portfolio([0,0,0.5], C, allow_short=True)` the short solution
sums to zero, so the code raised `CalculationError` at `portfolio.py:274-276`
rather than dividing by zero. The failure mode was safe, but the accepted
covariance could not be assumed PSD.

Iteration 2 implements the recommended option
(`stock_valuation/domain/validators.py:590-614`):

- symmetric elimination with complete diagonal pivoting and a
  `PSD_TOLERANCE * max(1.0, max_diag)` tolerance;
- `diag < -tol` raises `ValidationError`, `diag <= tol` scans the remaining
  block for diagonals below `-tol` and off-diagonals above `tol`;
- singular PSD input still passes, so singularity stays a solver concern and
  `min_variance_portfolio` keeps its `CalculationError` contract;
- the counterexample above is now rejected at validation, and the public call
  asserts `ValidationError` (`test_portfolio.py:525`) while the zero-total
  guard remains characterized on `_gmv_weights` directly (`:531`).

The solver's tolerance policy is unchanged; only the validation contract moved.

### 7.2 Reverse-DCF width fallback can report a material price mismatch

The search accepts a midpoint when the bracket width falls below `1e-12`
without rechecking the price residual (`dcf_analysis.py:531-543`). Under extreme
enterprise/debt cancellation, the algorithm can return `status="solved"` while
the implied value does not match the market price.

Verified example:

```python
projections = [CashFlowProjection(1e12, 0.0, 0.0, 0.0)]
reverse_dcf_implied_growth(
    projections, wacc_rate=0.1, shares_outstanding=1.0, tax_rate=0.0,
    market_price=1.0001, debt=14285714285713.283,
)
```

Observed result: `status="solved"`, `implied_growth≈0.02999999999993179`,
`market_price=1.0001`, but `equity_value≈-12.919921875` and therefore
per-share value far from 1.0001. The test
`test_width_fallback_returns_growth_when_price_cancels`
(`tests/domain/test_dcf_analysis.py:502`) characterizes this current behaviour
so the mutant can be detected. If the fallback policy changes to reject a
large residual, that test should change with it.

Recommendation: gate the fallback on an absolute/relative price residual, or
return a distinct status/`CalculationError` when the bracket collapses without
a matching value. This needs a product decision because it changes public
behaviour.

## 8. Reproduction

Iteration 1 environment:

- Python 3.12.14 in conda environment `finance`
- mutmut 3.8.1
- pytest 8.4.1
- Branch: `feature/frontend-react-app`

Commands:

```bash
cd /home/mohammad1/stock-env

# Unmutated validation
~/miniconda3/envs/finance/bin/python -m pytest tests -q
~/miniconda3/envs/finance/bin/python -m unittest discover -s tests -t . -v

# mutmut does not invalidate its cache for test-only edits, so reset it.
rm -rf mutants/
~/miniconda3/envs/finance/bin/mutmut run
~/miniconda3/envs/finance/bin/mutmut results --all true
```

Expected final totals for this source and test tree: 3,901 mutants, 3,147
killed, 754 survived. If a previously killed mutant reappears as survived,
verify that the cache was actually removed and that the test selection still
points at `tests/domain` (`setup.cfg:7`).

Iteration 2 environment:

- Python 3.11.4 (base conda), mutmut 3.8.1 installed outside the tracked tree
  with `pip install --target ./.mutmut_pkgs "mutmut>=3,<4"` and removed after
  the campaign.

```bash
cd /home/mohammad1/stock-env

PYTHONPATH=./.mutmut_pkgs python -m pytest tests -q
PYTHONPATH=./.mutmut_pkgs python -m mutmut run
PYTHONPATH=./.mutmut_pkgs python -m mutmut results
```

Expected totals for the current tree: 3,972 mutants, 3,204 killed, 768
survived, with the covariance function at 110 killed / 34 survived. This run
reused the `mutants/` cache; a clean-cache replay should reproduce the kill set
for the changed files but not necessarily the same timings.

Two environment traps observed during iteration 2:

- The sandboxed background shells activate conda env `finance` (Python 3.12)
  while the foreground shell uses Python 3.11. A `--target` install made by one
  interpreter fails under the other with
  `ImportError: cannot import name 'native' from 'libcst'`. Pin the interpreter
  explicitly.
- Keep the `--target` directory outside the workspace or delete it afterwards:
  mutmut reports every non-Python file under the project root as changed, and
  the install also pollutes `git status`.

## 9. Recommended next actions

1. ~~Decide the covariance contract.~~ Done in iteration 2 (§7.1): the validator
   enforces PSD with `PSD_TOLERANCE` scaled by `max(1.0, max_diag)`, and
   singular PSD input stays valid.
2. Decide the reverse-DCF fallback policy and correct the residual gate if
   needed; update the characterizing test together with the behaviour (§7.2).
3. ~~Triage the remaining logic survivors in the four in-scope modules.~~
   Done in iteration 3 (§5.6): 20 logic mutants killed (including
   `sample_statistics__mutmut_39/40`), `_long_only_min_variance__mutmut_17`
   proven equivalent in IEEE-754, and the rest classified as equivalent,
   caller-scoped, or deferred. Still open: 80 outside the four modules and
   the eight non-message survivors in the pre-existing part of
   `validate_covariance_matrix` (§5.5).
4. Semantically review the message-string candidates (638 after iteration 2)
   before quoting any equivalence-adjusted mutation score. Treat the current
   80.66% as an **unadjusted** raw score.
5. Run the next campaign from a cleared `mutants/` cache so the delta is
   measured like-for-like, and consider CI only after the runtime is acceptable.

## 10. Files touched

Iteration 1 — tests only:

- `tests/domain/test_portfolio.py`
- `tests/domain/test_portfolio_analysis.py`
- `tests/domain/test_portfolio_stats.py`
- `tests/domain/test_dcf_analysis.py`

Iteration 2:

- `stock_valuation/domain/validators.py` — `PSD_TOLERANCE`, the PSD block in
  `validate_covariance_matrix`, and the function docstring.
- `stock_valuation/domain/portfolio.py` — docstrings only (module contract,
  `_prepare`, `min_variance_portfolio`); no behaviour change.
- `tests/domain/test_portfolio_stats.py` — new `TestCovariancePSD` class and
  updated correlation-boundary expectations.
- `tests/domain/test_portfolio.py` — split GMV guard, direct `_performance` and
  `_gmv_weights` calls, rescaled tangency fixture.

Iteration 3 — tests only (residual logic survivor triage, §5.6):

- `tests/domain/test_portfolio_stats.py` — new `TestCenteringFloatingPoint`.
- `tests/domain/test_portfolio.py` — exact tangency normalization fixture.
- `tests/domain/test_portfolio_analysis.py` — negative-weight clip and
  signed-zero volatility fixtures.
- `tests/domain/test_dcf_analysis.py` — four reverse-DCF width-fallback gate
  fixtures.
- `docs/mutation_testing_report.md` — §3 iteration-3 tests, §5.6 classification,
  §9 item 3 closed.

No changes were made to `setup.cfg` or dependencies. No commit was created as
part of this work.

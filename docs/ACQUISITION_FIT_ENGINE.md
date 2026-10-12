# Acquisition Fit Engine — methodology

The Fit Engine ranks possible add-on companies for a chosen platform company and explains every score. It lives in the **Acquisition Fit Engine** tab. All scoring code is in `frontend/src/lib/fitEngine.js` (pure functions, no I/O), so the same data and weights always produce the same result.

> **Heuristic estimates.** A fit score compares company data with criteria you choose. It does not measure seller intent, acquisition readiness, verified ownership, or the likelihood that a deal succeeds.

## 1. Factors and default weights

Each factor is scored 0–100. Default weights total 100.

| Factor | Default weight | Scoring rule | Unavailable when |
|---|---:|---|---|
| Industry similarity | 40 | Identical label (lower-cased, whitespace collapsed) = 100. Different labels with Indel ratio ≥ 80 = 50. Otherwise 0. | Either company has no industry |
| Company-size compatibility (employees) | 20 | `ratio = candidate ÷ platform`. ratio ≤ 1 → 100; ratio > 1 → `100 ÷ ratio`. | Platform value missing/zero, or candidate value missing/invalid |
| Revenue compatibility | 20 | Same formula on estimated revenue. | Same as size |
| Geographic fit | 10 | Same US state = 100, different state = 0. State is read from addresses ending in `ST 12345`. | Either address has no readable US state |
| Relationship evidence | 10 | The relationship detector's evidence strength (0–100). The strongest link is used if several exist. | No relationship with the platform was detected |

Numeric strings are parsed like the backend (`$5.2M`, `1,200`, `100k`).

**Data completeness is deliberately not a factor.** It is shown beside every score as a separate information-quality indicator.

## 2. Weights and normalization

* Each weight is a number from 0 to 100. Blank, non-numeric or out-of-range values are rejected and ranking is withheld until fixed.
* Factors that cannot be scored for the platform are **excluded**; their weights are not used and the UI says so.
* The remaining weights are rescaled to total **exactly 100.0%** (largest-remainder rounding to 0.1), so only relative weights matter: `2/1/1` equals `80/40/40`.
* If every available factor has weight 0, no ranking is produced and an explanation is shown. There is no silent fallback to defaults.

## 3. Candidate score

For each candidate:

1. Take the factors with a weight above 0.
2. Keep those that **could be scored for this candidate**.
3. Re-scale their weights to total 100% (the *weight used*).
4. `fit score = Σ (factor score × weight used)`. Each term is that factor's *contribution in points*; contributions are rounded to 0.1 so they add up to the displayed score.

**Evidence coverage** = the share of the total weight that could be scored (0–100%). **Known score range** = the score if every missing factor had scored 0, versus 100.

### Missing evidence is not negative evidence

| Situation | Treatment |
|---|---|
| Blank, invalid or unreadable data; no relationship detected | Factor is **not scored**; left out of the average; shown as "Not scored" with the reason |
| Both values known and unfavourable (other industry, much larger company, other state) | Factor **is scored**, low |

Candidates whose coverage is below the **minimum evidence coverage** setting (default 50%) are listed as *provisional* and are not ranked. Candidates with no scorable factor are listed as *not scored*.

### Ranking and ties

Sorted by displayed fit score (1 decimal), then evidence coverage, then data completeness, then name, then ID. Ranks are unique and stable.

### Score labels

Strong ≥ 75, Moderate 40–74.9, Weak < 40. Labels always carry an icon and text, never color alone.

## 4. Worked example (sample_companies.csv, platform "Prairie Wind Plumbing & Heating", default weights)

**#1 Prairie Wynd Plumbing & Heating Inc — fit 95.0, coverage 80%, range 76.0–96.0**

| Factor | Score | Weight used | Points |
|---|---:|---:|---:|
| Industry | 100 | 50.0% | 50.0 |
| Size | not scored (employee count missing) | — | — |
| Revenue | 100 | 25.0% | 25.0 |
| Geography | 100 | 12.5% | 12.5 |
| Relationship | 60 | 12.5% | 7.5 |

The missing size factor is not counted against it; its 20% weight is shared among the other four. This candidate matches the platform on name and address, so the explanation warns it may be the same business listed twice.

**#2 Lone Star Comfort Services LLC — fit 55.6, coverage 90%**: industry 0 (different industry), size 100, revenue 100, geography 100; no relationship detected, so that factor is not scored.

## 5. Relationship to the backend add-on score

The existing **Add-on Recommendations** tab (`POST /api/companies/{id}/add-ons`) is unchanged. Its score is additive and rule-based: industry +60 (similar +30), employees ≤ platform +20, revenue ≤ platform +20; missing data adds 0 and candidates with no matching rule are omitted.

The Fit Engine uses the same industry matching (shared contract file `backend/tests/industry_cases.json`, asserted by both test suites) and the same "at or below the platform" idea, but scores size continuously, treats missing data as unscored, and adds geography and relationship evidence. The two scores use different scales and are **never added or averaged**. A button in the Ranking view loads the backend score once per platform (cached, never refetched when weights change) and shows it as a labelled reference badge.

## 6. Presets and comparison

* **Save preset / Load / Delete**: up to 6 named weight sets per session (plus the built-in Defaults, Industry-first and Scale-first examples).
* **Compare presets**: ranks the same candidates under 2–3 weight sets and shows rank movement, so you can see which results depend on the weighting.
* **Compare candidates**: 2–4 candidates side by side with factor bars, differences marked "Highest/Lowest" (text, not color only), known advantages and missing information.
* Presets and selections last for the session; they are cleared when a new CSV is analyzed because company IDs belong to the uploaded file.

## 7. Limitations

* Uses only fields in the uploaded CSV and the relationship detector's output. It cannot see customers, margins, ownership, management, or deal terms.
* Industry compares text labels, not meaning ("HVAC" vs "Heating & Cooling" reads as different).
* Geography reads US-format addresses only.
* A weak detected relationship slightly lowers an otherwise strong candidate (the factor is averaged in once it exists). Set the Relationship weight to 0 to ignore it.
* Size and revenue do not penalise very small candidates, who may be immaterial.
* Factor thresholds (80% similarity, 50-point "similar" score, 75/40 labels) are documented judgment calls.
* A detected relationship is not confirmed ownership; it may indicate a duplicate listing or an existing affiliate.

## 8. Tests

```
cd frontend && npm test                      # 52 tests: simulator + fit engine (node:test, no extra packages)
cd backend  && python -m unittest discover -s tests -v   # 11 tests: add-on rules + shared industry contract
```

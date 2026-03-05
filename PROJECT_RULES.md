# kapiva_fixed — Current Status, Caveats, and Improvement Roadmap

> **Purpose of this document**
> This is a consolidated handoff summary intended to be fed into **Claude Code** (or any static-analysis / code-inspection AI). It captures what is known *for sure*, what is *assumed*, what *works*, what *needs improvement*, and which **caveats / risks** exist in the project *as it currently stands*.

---

## 1. High-level snapshot (as-is)

* **Project name:** `kapiva_fixed`
* **Language:** Python
* **Nature of the project:** Quant / trading-oriented codebase (strategy logic, variables meant to be tuned, backtesting / execution-style flow).
* **Current state:**

  * Code runs (or at least imports) without critical syntax errors.
  * Strategy logic exists and is being inspected/refactored rather than rewritten from scratch.
  * The intent is **inspect ? understand ? improve**, not greenfield development.

> ?? **Important:** This document intentionally avoids guessing behavior that has not been explicitly validated. Anything not 100% known is marked clearly as an *assumption*.

---

## 2. What we know for sure (validated understanding)

### 2.1 Architecture & style

* The project contains **strategy logic embedded in Python code** (not config-driven).
* Key strategy parameters are **hard-coded or semi-hard-coded** and expected to be manually tweaked.
* The code prioritizes *getting results* over clean abstraction (typical research-stage quant code).

### 2.2 Intended usage

* The code is intended to:

  * Run locally (not cloud-native).
  * Be iterated on quickly (parameter tuning, logic tweaks).
  * Serve as a **research / experimentation** base rather than a production trading engine.

### 2.3 Current strengths

* Logic is explicit (readable, not overly meta-programmed).
* Variables can be adjusted relatively easily once identified.
* Behavior is deterministic (no hidden async / concurrency complexity).

---

## 3. Known limitations & caveats (IMPORTANT for inspection AI)

These are **not bugs**, but *constraints and risks* that must be understood before suggesting changes.

### 3.1 Design caveats

* ? **Tight coupling:**

  * Strategy logic, execution flow, and parameter definitions are intertwined.
  * Makes reuse harder but faster for experimentation.

* ? **Low separation of concerns:**

  * Signal generation, sizing, and execution logic may live in the same scope/function.

* ? **Implicit assumptions:**

  * Market conditions, liquidity, and fills may be assumed perfect or near-perfect.
  * Slippage, latency, and partial fills are likely simplified or ignored.

### 3.2 Quant / strategy caveats

* ? **Overfitting risk:**

  * Parameter-heavy logic without cross-validation safeguards.
  * No explicit walk-forward analysis layer.

* ? **Risk management may be incomplete:**

  * Drawdown control, max exposure, or stop logic may be implicit rather than enforced.

### 3.3 Code-level caveats

* ? **Limited type safety:**

  * Likely minimal type hints or validation on inputs.

* ? **Minimal defensive programming:**

  * Edge cases (empty data, NaNs, unexpected price gaps) may not be guarded everywhere.

---

## 4. What needs improvement (ranked by impact)

### 4.1 High-impact / low-effort improvements

1. **Centralize parameters**

   * Extract all tunable values into a single config object or file.
   * Makes experimentation safer and faster.

2. **Explicit assumptions section (in code)**

   * Comment block stating:

     * Timeframe assumptions
     * Fill assumptions
     * Position sizing assumptions

3. **Basic validation guards**

   * Check for:

     * Empty datasets
     * NaNs / None values
     * Zero division risks

---

### 4.2 Medium-impact improvements

4. **Separate logic layers**

   * Signal generation
   * Position sizing
   * Execution / order logic

5. **Instrument logging**

   * Key events:

     * Signal triggered
     * Entry executed
     * Exit executed
     * Equity / exposure changes

6. **Deterministic backtest outputs**

   * Standardized result object (PnL, drawdown, win rate, exposure time).

---

### 4.3 Advanced / future improvements

7. **Risk constraints**

   * Max drawdown cutoff
   * Max concurrent exposure
   * Capital-at-risk limits

8. **Parameter sensitivity analysis**

   * Automated grid or random search wrappers.

9. **Walk-forward or regime testing**

   * Split data by regime or time chunks.

---

## 5. What *not* to change lightly

These elements are probably *intentional* and should not be refactored away without discussion:

* Core entry/exit logic semantics.
* Parameter relationships (relative percentages, multipliers, thresholds).
* Execution ordering (the *sequence* of decisions often matters more than cleanliness).

---

## 6. Questions the inspection AI should answer

When reviewing the project, Claude Code should explicitly address:

1. **What exactly is the strategy logic in plain English?**
2. **Which parameters dominate performance sensitivity?**
3. **Where are implicit assumptions hiding in the code?**
4. **What are the biggest sources of silent failure or misleading results?**
5. **Which refactors improve safety without changing behavior?**

---

## 7. Explicit assumptions (declare before inspecting code)

> The following assumptions are acceptable *unless the code contradicts them*:

* This is a research-stage project.
* Performance > elegance at this stage.
* Backtest realism is secondary to signal logic evaluation.
* The author intends to iterate manually and understand behavior deeply.

---

## 8. Handoff instruction (recommended prompt to Claude Code)

> “Inspect this project **as-is**, explain exactly what it does, list hidden assumptions, identify fragile areas, and propose improvements **without changing strategy behavior** unless explicitly justified.”

---

## 9. Domain assumptions & business rules (VERY IMPORTANT)

This section lists **all agreed assumptions, definitions, and business rules** that must be considered *ground truth* unless explicitly revised. These are the conceptual pillars behind the project logic and analytics.

### 9.1 Faturamento × Comissão (core distinction)

* **COMISSAO table is the single source of truth for faturamento realizado.**

  * It already reflects **returns/devoluções**.
  * It represents *what actually generated commission*.
  * It should be treated as **net, validated revenue**.

* **FATURAMENTO ? venda bruta (PDV raw)**

  * Raw sales tables may include:

    * Cancelled items
    * Returned items
    * Exchanges
    * Timing mismatches
  * Therefore, they cannot be used directly for performance or margin truth without reconciliation.

* **All performance dashboards, KPIs, rankings, and seller metrics must anchor on COMISSAO**, not raw sales.

---

### 9.2 Time alignment assumptions

* Sales date ? commission recognition date.
* Any analysis using *calendar aggregation* must:

  * Explicitly define which date is used
  * Prefer **commission recognition date** for seller and performance metrics

---

### 9.3 Seller performance rules

* Seller dashboards must show:

  * Daily sales (from COMISSAO)
  * Breakdown by sale and product
  * Commission tiers (1%, 1.2%, 1.5%)

* Targets and performance are always evaluated against **net commissionable value**, not gross ticket value.

---

### 9.4 Product & inventory assumptions

* **No untouchable brands**

  * Even historically important brands can and should be analyzed critically.

* **Infantil category**

  * Must remain present for mix and traffic reasons
  * Is accepted as structurally lower margin

* **Old inventory still sells**

  * Products pre-2023 are not dead stock by default
  * They require **alerting and prioritization**, not automatic write-off

---

### 9.5 Promotion & pricing logic

* Promotions are:

  * **Punctual**, not permanent campaigns
  * Progressive by inventory age

**Standard policy:**

* Known products: ~20%

* > 1 year:

  * 30% crediário
  * 40% à vista

* Older stock:

  * 40% crediário
  * 50% à vista

* Final burn:

  * Fixed-price clearance

* Once a product enters promotion, it generally **stays until sold**.

---

### 9.6 Seasonality & collection logic

* Seasonal classification is required:

  * **Winter:** Feb–Apr
  * **Summer:** Jul–Dec

* Promotions follow season transitions:

  * Winter push in July
  * Summer clearance end of January

---

### 9.7 Brand performance philosophy (80/20)

* The goal is **not equal treatment of all brands**.

* Focus is on:

  * Top 20% of brands driving ~80% of results
  * Identifying brands that are *margin-destructive* despite volume

* Brands can be:

  * Volume-positive but margin-negative
  * Margin-positive but slow-moving

Both cases must be surfaced explicitly in analytics.

---

### 9.8 Analytical intent assumptions

* This project prioritizes:

  * Decision support
  * Risk visibility
  * Actionable inventory insights

* It does **not** prioritize:

  * Accounting-grade reconciliation
  * Fiscal or tax reporting

---

### 9.9 Non-goals (explicitly out of scope for now)

* Real-time stock locking
* Automatic repricing
* ERP replacement
* Financial audit compliance

---

## 10. KPIs agreed (single source of truth)

This section defines **all metrics (KPIs)** that the project is allowed to compute and display. Any metric not listed here should be considered *experimental*.

### 10.1 Revenue & result KPIs

* **Faturamento Real**

  * Source: `COMISSAO.base_calc_comissao`
  * Definition: Net revenue after returns, cancellations and adjustments
  * This is the *reference number* for all analyses

* **Resultado Real (R$)**

  * Definition: Faturamento Real ? Custo Real
  * Must respect the same net logic as comissão

* **Margem (%)**

  * Formula: Resultado Real / Faturamento Real
  * Never computed on raw sales tables

---

### 10.2 Volume & velocity KPIs

* **Quantidade Vendida**

  * Units sold that generated commission

* **Giro de Estoque**

  * Definition: Quantidade Vendida / Estoque Médio
  * Interpreted *per brand*, *per category*, and *per collection*

* **Dias em Estoque (Idade)**

  * Definition: Date(reference) ? Date(entrada)
  * Bucketed (ex.: 0–90, 91–180, 181–365, >365)

---

### 10.3 Seller KPIs

* **Vendas por Vendedor (diário)**

  * Source: COMISSAO

* **Comissão Gerada (R$)**

* **Faixa de Comissão**

  * 1.0%, 1.2%, 1.5%

* **Atingimento de Meta (%)**

---

### 10.4 Brand & product KPIs

* **Participação no Resultado (%)**

* **Participação no Faturamento (%)**

* **Ranking 80/20 por Marca**

  * Resultado
  * Margem
  * Giro

* **Marca de Risco**

  * High volume + low/negative margin

---

### 10.5 Promotion & aging KPIs

* **% do Estoque em Promoção**
* **Resultado do Estoque Promocional**
* **Idade Média do Estoque por Marca**

---

## 11. Known data inconsistencies (expected, not bugs)

This section documents **known mismatches** in the data so that they are not misinterpreted as errors.

### 11.1 Sales × Commission mismatch

* Raw sales tables may show values higher than COMISSAO
* Causes include:

  * Returns processed later
  * Partial item cancellations
  * Exchange flows

? Expected behavior: COMISSAO is lower and correct

---

### 11.2 Date inconsistencies

* Sale date ? commission recognition date
* Daily reports may not reconcile perfectly with PDV

? Expected behavior

---

### 11.3 Cost inconsistencies

* Cost may change over time (freight, supplier renegotiation)
* Historical sales must use **cost at time of entry**, not current cost

---

### 11.4 Inventory snapshot issues

* Stock levels are point-in-time
* Giro calculations are approximations

? Acceptable for decision support

---

## 12. Metric glossary (canonical definitions)

### Margem

> Percentual de lucro real sobre faturamento real

Margem = Resultado Real / Faturamento Real

---

### Giro

> Velocidade com que o estoque se transforma em venda

Interpretação:

* Alto giro + baixa margem ? risco silencioso
* Baixo giro + alta margem ? capital travado

---

### Idade de Estoque

> Tempo (em dias) que o produto permanece em estoque desde a entrada

Usado para:

* Políticas de promoção
* Alertas de risco

---

### Resultado Real

> Dinheiro efetivamente gerado após todos os ajustes

Resultado Real = Faturamento Real ? Custo Real

---

## 13. Final note

These assumptions are **part of the system design**, not implementation details.

Any AI, developer, or analyst reviewing this project must treat these rules as *constraints*, not suggestions.
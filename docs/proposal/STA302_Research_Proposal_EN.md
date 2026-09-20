# Does a Currency Hedge Neutralize Daily Yen Exposure?

## A Multi-Factor Study of HEWJ versus EWJ Before and After the COVID-19 Break

**Course:** STA302 Final Project — Part 1  
**Prepared:** September 21, 2026  
**Group members:** Haiwen Yi; **[add all other members before submission]**

## Contribution statement

| Member | Proposed contribution |
|---|---|
| Haiwen Yi | Research design, data construction, R analysis, diagnostics, and first draft |
| [Member 2] | Literature verification, interpretation, and written revision |
| [Member 3] | Reproducibility check, poster development, and presentation recording |
| [Member 4, if applicable] | Final-model sensitivity analysis and presentation review |

The names and contribution descriptions above must match the separately submitted Group Teamwork Agreement.

## Abstract

Currency-hedged exchange-traded funds are designed to reduce exchange-rate exposure, but implementation frictions may prevent a complete hedge. We study 2,655 matched daily observations from 2014–2026 and ask how yen appreciation explains the HEWJ-minus-EWJ return spread, conditional on equity, factor, volatility, and interest-rate controls, and whether that relationship changed after March 11, 2020. A multiple linear regression with a pre-specified period interaction estimates yen slopes of -0.851 before and -0.912 after the transition. The preliminary model explains 70.38% of spread variation, but diagnostics identify heteroskedasticity, serial dependence, heavy tails, possible functional-form error, and influential dates. These findings motivate a theory-preserving final analysis using repeated diagnostics, declared sensitivity checks, Newey-West inference, and chronological out-of-sample evaluation. The study is descriptive rather than causal.

## Introduction (400 words)

International equity investors receive returns from the local equity market and from the exchange rate used to translate foreign assets into their home currency. Currency-hedged exchange-traded funds attempt to remove the second component, but hedging may be incomplete because forward contracts are rolled periodically, trading calendars differ, expenses and implementation costs exist, and portfolios are not rebalanced continuously. This project asks: **How strongly does daily yen appreciation explain the return difference between the currency-hedged iShares MSCI Japan ETF (HEWJ) and its unhedged counterpart (EWJ), after controlling for equity, factor, volatility, and interest-rate conditions, and did that relationship change after the World Health Organization characterized COVID-19 as a pandemic?**

The response is the daily log-return spread, \(Y_t=100[\Delta\log(HEWJ_t)-\Delta\log(EWJ_t)]\), and \(JPYapp_t=-100\Delta\log(DEXJPUS_t)\) is positive when the yen appreciates. A mean comparison or simple correlation cannot simultaneously adjust for market conditions, estimate conditional period-specific slopes, and test a change in slope. Multiple linear regression provides adjusted coefficients, confidence intervals, and an interaction test. Under a complete contemporaneous hedge, the yen slope should be near -1. A categorical period indicator and its interaction with yen appreciation estimate pre- and post-pandemic slopes; March 11, 2020 is the pre-specified transition and is omitted.

**Related work and research gap.** Glen and Jorion (1993) find that forward contracts improved the risk-return performance of international bond and equity portfolios from 1974–1990, establishing why hedging can matter without measuring a modern ETF's realized daily offset. Across 17 OECD economies, Hau and Rey (2006) find exchange rates, equity returns, and portfolio flows move jointly, motivating equity-market controls. Campbell, Serfaty-de Medeiros, and Viceira (2010) show with 1975–2005 international asset returns that risk-minimizing currency positions vary across assets and investors, so a one-for-one hedge need not hold. Fama and French (2015) show in diversified U.S. stock portfolios that size, value, profitability, and investment factors explain average-return variation, supporting controls for residual equity composition. In three U.S.-listed currency-hedged ETFs during 2011–2015, Shank and Vianna (2016) find dynamic links among exchange rates, fund trading, and benchmarks. None of these studies estimates the realized daily yen exposure of the matched HEWJ/EWJ pair or tests a pre-specified 2020 slope change. This project fills that gap with an auditable daily matched-pair design.

The results would benefit U.S.-dollar investors, portfolio managers, and risk teams deciding whether a “hedged” Japan allocation actually offsets daily yen exposure. The pandemic indicator is descriptive, not causal, because many policies and market conditions changed simultaneously.

## Data description (289 words)

The analysis contains 2,655 exact-interval daily observations from February 6, 2014 through July 31, 2026. Yahoo Finance records traded HEWJ and EWJ quotations for market information; adjusted closes incorporate splits and distributions for total-return comparisons. The Federal Reserve Board collects DEXJPUS as the noon New York buying rate for yen transfers. The Nikkei Industry Research Institute records the daily close of 225 liquid Tokyo stocks; CBOE derives VIX from index-option prices as expected near-term volatility; and the OECD compiles monthly U.S. and Japanese call-money/interbank rates. FRED redistributes these series. Kenneth French's Data Library forms value-weighted Japan equity portfolios for asset-pricing research, producing daily five-factor and momentum returns.

The daily HEWJ-minus-EWJ log-return spread has mean 0.0180 percentage points, standard deviation 0.6243, and range -4.3097 to 3.7826. It is continuous and signed, making a linear conditional mean interpretable. Daily observations are ordered rather than strictly independent, so residual dependence is assessed and no causal interpretation is made.

Table 1 summarizes every model variable and missingness. The analysis sample has zero missing values because rows are retained only when required sources share the same return interval; this is an inclusion rule, not imputation. Extreme movements appear in the response, Nikkei return, momentum, and VIX change. Monthly rates are carried forward with a one-month lag. `Post` contains 1,304 pre-period and 1,351 post-period observations. Price returns are computed on native calendars before merging.

The model uses ten predictors: yen appreciation, `Post`, Nikkei return, SMB, HML, RMW, CMA, MOM, log VIX change, and the lagged U.S.-Japan rate differential. The `JPYapp × Post` interaction answers the research question and reflects prior evidence of time-varying hedge dynamics; Figure 1 shows its period-specific slopes. The split follows the WHO announcement rather than a search for the smallest p-value.

## Ethics discussion (198 words)

The dataset is trustworthy because its provenance, ownership, and transformations are documented. Yahoo Finance closes, FRED series, and Kenneth French factors are public sources, but authority does not eliminate error: providers can revise observations, calendars may differ, and adjusted prices depend on provider methods. We preserve snapshots and SHA-256 checksums, document transformations, and avoid overstating precision. This addresses the module's trustworthiness criteria of provenance, transparency, accuracy, and reproducibility.

Collection and use are ethically low risk. The sources contain aggregate market prices and factor portfolios, not personal information, private holdings, individual trading records, or human-subject data. Consent, confidentiality, and re-identification risks are minimal. We respect ownership by citing each provider, limiting source-file access to the course group and graders, and not publicly redistributing restricted Nikkei observations or claiming ownership of third-party data.

The principal ethical risk is interpretation. A descriptive association could be presented incorrectly as investment advice or evidence that COVID-19 caused a change. We will state that results apply to one ETF pair, acknowledge survivorship and product-selection limitations, and avoid causal language because changes were uncontrolled. Historical predictive performance is not a promise of future returns. These limits make the use proportionate to the data and question.

## Preliminary results (391 words including captions)

The full ordinary least-squares model is

\[
Y(t) = b0 + b1 JPYapp(t) + b2 Post(t) + b3 [JPYapp(t) x Post(t)] + g'Z(t) + e(t),
\]

where \(Z_t\) contains the eight market and factor controls. Table 2 reports every coefficient with a classical standard error and 95% confidence interval. The model explains 70.38% of daily spread variation (adjusted \(R^2=70.26\%\)). The pre-period yen slope is -0.851 (SE 0.0184; 95% CI [-0.887, -0.815]). Thus, conditional on the controls, a one-percentage-point yen appreciation is associated with a 0.851-percentage-point lower HEWJ-minus-EWJ return. The interaction is -0.0612 (SE 0.0235; p = 0.0093), giving an implied post-period slope of -0.912. The period level shift is not significant. VIX log change is negative; most other controls are imprecisely estimated.

The strong negative currency slope is consistent with Hau and Rey's joint currency-equity mechanism and with the hedge interpretation. Its departure from exactly -1 agrees with Campbell et al.'s result that effective hedges need not be mechanical one-for-one positions. The mostly small factor coefficients suggest that pairing HEWJ with EWJ removes much common equity exposure, while retaining Fama-French controls prevents that conclusion from being assumed. The changed slope is directionally compatible with Shank and Vianna's evidence of time-varying currency-hedged ETF dynamics, although our pandemic comparison is not causal.

Figure 2 provides a six-panel preliminary diagnostic grid. Residuals versus fitted values show no dominant smooth curve, but the RESET test rejects exact functional form (p < 0.001), so linearity remains questionable. The scale-location panel and Breusch-Pagan test indicate nonconstant variance (p = 0.0082). The Q-Q plot has heavy tails and Jarque-Bera rejects normality (p < 0.001). Residuals over time and the ACF show dependence; the five-lag Breusch-Godfrey test rejects independence (p < 0.001), and Durbin-Watson is 2.83. The maximum VIF is 3.56, so severe multicollinearity is not evident. The Cook's-distance panel identifies 134 cases above the screening threshold \(4/n\), with maximum 0.142; these observations are flagged for sensitivity analysis rather than automatically deleted.

These are preliminary OLS results. In accordance with the Part 1 instruction, we diagnose but do not correct violations here; robust inference and sensitivity analysis are deferred to the final project.

## Plan for the remaining analysis (299 words)

The focal terms - yen appreciation, `Post`, and their interaction - will remain. We will first fit the full ten-predictor specification and retain it as the pre-specified inferential model. Predictive simplification will compare three hierarchy-respecting candidates: (1) the FX interaction alone; (2) macro controls adding Nikkei return, VIX change, and lagged rate differential; and (3) the full factor model additionally containing SMB, HML, RMW, CMA, and MOM. Controls will not be removed by individual p-values.

After specification changes, we will recheck residual, Q-Q, time-order, and ACF plots, Breusch-Pagan and Breusch-Godfrey tests, Cook's distance, and VIF. Given diagnostic violations, we will examine a pre-specified nonlinear yen term and a Yeo-Johnson response transformation; a direct logarithm is invalid for signed returns. Transformations will be judged by diagnostics, rolling validation performance, and interpretability, not significance.

Primary analysis will retain all observations; secondary analyses will compare declared 0.5/99.5-percentile winsorization and exclusion of confirmed data errors. Classical intervals will be supplemented by Newey-West intervals with 1-, 5-, and 10-day lags. We will vary the pandemic cut within a declared window rather than search all dates.

Prediction remains secondary. Expanding-window rolling-origin validation will fit each candidate through 2020, 2021, and 2022 and score the following calendar year, producing validation results for 2021-2023. Mean RMSE across the three folds will lock the winner. It will then be refitted on all development observations through January 23, 2024 and evaluated exactly once from January 24, 2024 onward against historical-mean and zero-return benchmarks. The full model remains the basis for confirmatory coefficient inference; the reduced winner is the final predictive model. No random splitting, final-test tuning, or post-test reselection will be used.

Frozen data, code, outputs, and selection evidence will be versioned. Table 3 assigns project milestones; member placeholders will be replaced from the signed agreement.

## References

Campbell, J. Y., Serfaty-de Medeiros, K., & Viceira, L. M. (2010). Global currency hedging. *The Journal of Finance, 65*(1), 87–121. https://doi.org/10.1111/j.1540-6261.2009.01524.x

Fama, E. F., & French, K. R. (2015). A five-factor asset pricing model. *Journal of Financial Economics, 116*(1), 1–22. https://doi.org/10.1016/j.jfineco.2014.10.010

Glen, J., & Jorion, P. (1993). Currency hedging for international portfolios. *The Journal of Finance, 48*(5), 1865–1886. https://doi.org/10.1111/j.1540-6261.1993.tb05131.x

Hau, H., & Rey, H. (2006). Exchange rates, equity prices, and capital flows. *The Review of Financial Studies, 19*(1), 273–317. https://doi.org/10.1093/rfs/hhj008

Shank, C. A., & Vianna, A. C. (2016). Are US-dollar-hedged-ETF investors aggressive on exchange rates? A panel VAR approach. *Research in International Business and Finance, 38*, 430–438. https://doi.org/10.1016/j.ribaf.2016.05.002

## Data and product documentation

Board of Governors of the Federal Reserve System (US). (n.d.). *Japanese yen to U.S. dollar spot exchange rate [DEXJPUS]*. FRED, Federal Reserve Bank of St. Louis. https://fred.stlouisfed.org/series/DEXJPUS

Chicago Board Options Exchange. (n.d.). *CBOE volatility index: VIX [VIXCLS]*. FRED, Federal Reserve Bank of St. Louis. https://fred.stlouisfed.org/series/VIXCLS

iShares. (n.d.). *HEWJ and EWJ fund pages and currency-hedged product documentation*. https://www.ishares.com/

Kenneth R. French Data Library. (n.d.). *Japan 5 factors [Daily] and Japan momentum factor [Daily]* [Data sets]. https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html

Nikkei Industry Research Institute. (n.d.). *Nikkei stock average, Nikkei 225 [NIKKEI225]*. FRED, Federal Reserve Bank of St. Louis. https://fred.stlouisfed.org/series/NIKKEI225

Organisation for Economic Co-operation and Development. (n.d.). *Immediate call-money/interbank rates for the United States and Japan [IRSTCI01USM156N; IRSTCI01JPM156N]*. FRED, Federal Reserve Bank of St. Louis. https://fred.stlouisfed.org/

World Health Organization. (2020, March 11). *WHO Director-General's opening remarks at the media briefing on COVID-19*. https://www.who.int/

Yahoo Finance. (n.d.). *HEWJ and EWJ historical data* [Data sets]. https://finance.yahoo.com/

## Submission items requiring group confirmation

1. Replace bracketed member names and role assignments with the actual group roster.
2. Complete and sign the course's Group Teamwork Agreement PDF using the same names and responsibilities.
3. Upload the prepared original and cleaned CSV folders to UofT OneDrive and add a Quercus submission comment with permission set to “anyone in UofT with the link can access.”

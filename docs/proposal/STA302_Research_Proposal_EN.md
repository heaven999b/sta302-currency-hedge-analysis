# Does a Currency Hedge Neutralize Daily Yen Exposure?

## A Multi-Factor Study of HEWJ versus EWJ Before and After the COVID-19 Break

**Course:** STA302 Final Project — Part 1  
**Prepared:** September 20, 2026  
**Group members:** Haiwen Yi; **[add all other members before submission]**

## Contribution statement

| Member | Proposed contribution |
|---|---|
| Haiwen Yi | Research design, data construction, R analysis, diagnostics, and first draft |
| [Member 2] | [Specify literature, validation, writing, or presentation tasks] |
| [Member 3] | [Specify literature, validation, writing, or presentation tasks] |
| [Member 4, if applicable] | [Specify contribution] |

The names and contribution descriptions above must match the separately submitted group agreement.

## Introduction (341 words)

International equity investors face two return sources: the local equity market and the exchange rate that converts foreign assets into the investor's home currency. Currency-hedged exchange-traded funds attempt to remove the second component, but the hedge may be incomplete because contracts are rolled periodically, trading calendars differ, expenses and implementation costs exist, and the portfolio is not rebalanced continuously. This project asks: **How strongly does daily yen appreciation explain the return difference between the currency-hedged iShares MSCI Japan ETF (HEWJ) and its unhedged counterpart (EWJ), and did that relationship change after the World Health Organization characterized COVID-19 as a pandemic?**

The response is the daily log-return spread, (Y_t=100[\Delta\log(HEWJ_t)-\Delta\log(EWJ_t)]). The focal predictor is (JPYapp_t=-100\Delta\log(DEXJPUS_t)), so a positive value denotes yen appreciation against the U.S. dollar. If the hedge fully removed contemporaneous currency exposure and both funds otherwise tracked the same Japanese equity portfolio, the expected slope would be near -1: yen appreciation should benefit the unhedged fund relative to the hedged fund. We estimate separate pre- and post-pandemic slopes through a categorical period indicator and its interaction with yen appreciation. March 11, 2020, the transition date, is omitted; the post period begins March 12.

The design is motivated by four peer-reviewed studies. Hau and Rey (2006) connect exchange rates, equity returns, and portfolio rebalancing, supporting joint attention to currency and equity movements. Campbell, Serfaty-de Medeiros, and Viceira (2010) show that optimal currency hedging varies with the investor and asset environment, so a mechanical one-for-one relation need not hold. Fama and French (2015) motivate controls for size, value, profitability, and investment factors. Shank and Vianna (2016) document dynamic links between exchange-rate movements and trading in U.S.-listed currency-hedged ETFs. Our contribution is narrower and transparent: a reproducible daily matched-pair analysis of one hedged/unhedged Japan ETF pair, with an explicit structural-break interaction, market-risk controls, and time-series-robust inference. The pandemic indicator is descriptive rather than a causal treatment because many policies and market conditions changed simultaneously.

## Data description (272 words)

The analysis uses 2,753 complete daily observations from February 6, 2014, through July 31, 2026: 1,348 pre-period and 1,405 post-period observations. Adjusted closing prices for HEWJ and EWJ come from the public Yahoo Finance chart history endpoints. The funds are a useful matched pair because iShares describes HEWJ as obtaining Japan equity exposure while hedging yen exposure and identifies EWJ as the underlying unhedged Japan equity fund. DEXJPUS, the noon New York yen-per-U.S.-dollar exchange rate, comes from the Federal Reserve Bank of St. Louis (FRED).

The response and three focal model terms are the return spread (Y_t), yen appreciation (JPYapp_t), the categorical `Post` indicator, and `JPYapp × Post`. Eight additional predictors address observable market conditions: the daily Nikkei 225 return; Japan SMB, HML, RMW, and CMA factors; Japan momentum (MOM); the daily log change in VIX; and the previous month's U.S.–Japan short-term interest-rate differential. Japan factor returns are from Kenneth French's open Data Library and are measured in U.S. dollars. The Nikkei 225, VIX, and interest-rate series are from FRED. Lagging the monthly rate differential by one month prevents using a same-month value that may not have been known at the start of each daily observation.

All series are joined by trading date, transformed only after alignment, and complete cases are retained. Percentage variables are expressed in percentage points, which makes the focal slope directly interpretable. The frozen raw files, SHA-256 checksums, cleaned CSV, R script, and machine-readable model outputs accompany this proposal. Data access links are: [Yahoo HEWJ](https://finance.yahoo.com/quote/HEWJ/history/), [Yahoo EWJ](https://finance.yahoo.com/quote/EWJ/history/), [FRED DEXJPUS](https://fred.stlouisfed.org/series/DEXJPUS), [FRED Nikkei 225](https://fred.stlouisfed.org/series/NIKKEI225), [FRED VIX](https://fred.stlouisfed.org/series/VIXCLS), and [Kenneth French's Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html).

## Ethics statement (194 words)

The project uses only public, aggregate market prices and factor series. It contains no personal information, human-subject data, private holdings, or individual trading records, so privacy and consent risks are minimal. Nevertheless, finance results can be misused if a descriptive association is presented as investment advice or as a causal pandemic effect. We will state that the results describe this ETF pair over this sample and do not establish that COVID-19 caused the slope change. Survivorship and product-selection concerns also matter: HEWJ and EWJ are currently traded funds selected because they form a convenient matched pair, not a random sample of all hedged products.

Reproducibility is addressed by preserving the exact downloaded files, documenting transformations, reporting the exclusion of March 11, 2020, and running the entire analysis in R. Adjusted prices incorporate provider-defined corporate-action adjustments; we will not imply that they are transaction prices available without costs. Yahoo, FRED, iShares, and Kenneth French data remain subject to their publishers' terms and revision practices. We will cite each provider and share links rather than claim ownership. Finally, any predictive evaluation is historical and does not support a promise of future returns or a trading recommendation.

## Preliminary results (368 words)

The full ordinary least-squares model is

\[
Y_t=\beta_0+\beta_1JPYapp_t+\beta_2Post_t+\beta_3(JPYapp_t\times Post_t)+\gamma'Z_t+\varepsilon_t,
\]

where (Z_t) contains the eight market and factor controls. The model explains 71.21% of daily variation in the HEWJ-minus-EWJ spread (adjusted (R^2=71.10\%\)); the focal-only model explains 70.37%. The pre-pandemic yen slope is -0.852 (classical SE 0.0178; HAC(5) SE 0.0307; HAC p < 0.001). Thus, a one-percentage-point yen appreciation is associated with an approximately 0.852-percentage-point lower hedged-minus-unhedged return before the break, conditional on the controls.

The interaction estimate is -0.0648. Under classical OLS it is statistically significant (SE 0.0227, p = 0.0043), but with Newey-West HAC(5) inference it is only marginal (SE 0.0355, p = 0.0683; 95% CI [-0.1345, 0.0049]). The implied post-pandemic slope is -0.917. Both the pre and post slopes differ statistically from the theoretical -1 benchmark under HAC(5), although the post-period difference is economically smaller. The level shift at zero yen movement is 0.0085 percentage points and is not significant with HAC inference (p = 0.176). Among the controls, the VIX change has a negative coefficient (-0.00687; HAC p < 0.001); most other control coefficients are imprecisely estimated.

The model does not satisfy all ideal iid-error assumptions. The Breusch–Pagan test rejects homoskedasticity (p = 0.0048), the five-lag Breusch–Godfrey test rejects no serial correlation (p < 0.001), and the Q-Q plot shows heavy tails. Durbin–Watson is 2.85, consistent with negative first-order residual autocorrelation. Multicollinearity is not severe: the largest VIF is 3.55 (HML). These findings are why the main interpretation reports both classical OLS and HAC(5) uncertainty rather than relying on conventional p-values alone.

As a secondary predictive check, an 80/20 chronological split trained through January 29, 2024, and tested from January 30, 2024, through July 31, 2026. The full model achieved RMSE 0.313 and MAE 0.219 percentage points, compared with 0.654 and 0.463 for a training-sample historical-mean benchmark. This check is supportive but not a substitute for inference because later observations may come from a different regime.

## Plan for the remaining analysis (275 words)

First, we will make the OLS specification and its estimand explicit: the interaction estimates a conditional change in the contemporaneous yen-spread association, not a causal pandemic effect. Classical OLS intervals will be shown for course continuity, while Newey-West HAC(5) intervals will be the primary time-series sensitivity analysis. We will also report the two implied period-specific yen slopes and formally test each against -1.

Second, we will investigate misspecification identified in the preliminary diagnostics. Residual-versus-fitted, Q-Q, time-order, and autocorrelation plots will be included. We will examine influential observations using Cook's distance and repeat the focal estimates after pre-specified winsorization of continuous daily changes at the 0.5th and 99.5th percentiles. This robustness analysis will be labeled as secondary; it will not replace the unmodified-data result. We will compare HAC lags of 1, 5, and 10 trading days and assess whether conclusions about the interaction change.

Third, we will test whether the selected break date drives the result by using a small, declared sensitivity window around March 11, 2020, rather than searching over all possible dates. We will also compare the full model with the focal-only model using adjusted (R^2), residual behavior, and the stability of the focal coefficients. Variance-inflation factors will document collinearity.

Finally, prediction will remain secondary to explanation. We will preserve temporal ordering, compare against a historical-mean benchmark, and report RMSE and MAE on the untouched final 20% of dates. No random cross-validation will be used for time-series observations. All final tables and figures will be generated by the supplied R code from the frozen raw files, and discrepancies between conventional and robust inference will be reported rather than selectively omitted.

## References

Campbell, J. Y., Serfaty-de Medeiros, K., & Viceira, L. M. (2010). Global currency hedging. *The Journal of Finance, 65*(1), 87–121. https://doi.org/10.1111/j.1540-6261.2009.01524.x

Fama, E. F., & French, K. R. (2015). A five-factor asset pricing model. *Journal of Financial Economics, 116*(1), 1–22. https://doi.org/10.1016/j.jfineco.2014.10.010

Hau, H., & Rey, H. (2006). Exchange rates, equity prices, and capital flows. *The Review of Financial Studies, 19*(1), 273–317. https://doi.org/10.1093/rfs/hhj008

Shank, C. A., & Vianna, A. C. (2016). Are US-dollar-hedged-ETF investors aggressive on exchange rates? A panel VAR approach. *Research in International Business and Finance, 38*, 430–438. https://doi.org/10.1016/j.ribaf.2016.05.002

## Data and product documentation

Federal Reserve Bank of St. Louis. DEXJPUS; NIKKEI225; VIXCLS; IRSTCI01USM156N; IRSTCI01JPM156N. FRED.  
iShares. HEWJ and EWJ fund pages and currency-hedged product brief.  
Kenneth R. French Data Library. Japan 5 Factors [Daily] and Japan Momentum Factor [Daily].  
World Health Organization. (2020, March 11). WHO Director-General's opening remarks at the media briefing on COVID-19.

## Submission items still requiring group input

1. Replace bracketed member names and contribution statements.
2. Make the separate contribution agreement PDF match this proposal.
3. Upload the cleaned CSV and raw-source folder to OneDrive and insert shareable links if the course submission form requires them.

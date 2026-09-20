# Does a Currency Hedge Neutralize Daily Yen Exposure?

## A Multi-Factor Study of HEWJ versus EWJ Before and After the COVID-19 Break

**Course:** STA302 Final Project — Part 1  
**Prepared:** September 20, 2026  
**Group members:** Haiwen Yi; **[add all other members before submission]**

## Contribution statement

| Member | Proposed contribution |
|---|---|
| Haiwen Yi | Research design, data construction, R analysis, diagnostics, and first draft |
| [Member 2] | Literature verification, interpretation, and written revision |
| [Member 3] | Reproducibility check, poster development, and presentation recording |
| [Member 4, if applicable] | Final-model sensitivity analysis and presentation review |

The names and contribution descriptions above must match the separately submitted Group Teamwork Agreement.

## Introduction (388 words)

International equity investors receive returns from the local equity market and from the exchange rate used to translate foreign assets into their home currency. Currency-hedged exchange-traded funds attempt to remove the second component, but hedging may be incomplete because forward contracts are rolled periodically, trading calendars differ, expenses and implementation costs exist, and portfolios are not rebalanced continuously. This project asks: **How strongly does daily yen appreciation explain the return difference between the currency-hedged iShares MSCI Japan ETF (HEWJ) and its unhedged counterpart (EWJ), after controlling for equity, factor, volatility, and interest-rate conditions, and did that relationship change after the World Health Organization characterized COVID-19 as a pandemic?**

The response is the daily log-return spread, \(Y_t=100[\Delta\log(HEWJ_t)-\Delta\log(EWJ_t)]\). The focal predictor is \(JPYapp_t=-100\Delta\log(DEXJPUS_t)\), so a positive value denotes yen appreciation against the U.S. dollar. A difference in means or a simple correlation cannot simultaneously adjust for market conditions, estimate conditional period-specific slopes, and test whether the slope changed. Multiple linear regression can do all three through coefficients, confidence intervals, and an interaction test. Under a complete contemporaneous hedge, the yen slope should be near -1. We estimate pre- and post-pandemic slopes with a categorical period indicator and its interaction with yen appreciation. March 11, 2020, is treated as the transition date and omitted.

Four peer-reviewed studies motivate the specification. In international equity and currency data, Hau and Rey (2006) find exchange rates, equity returns, and portfolio flows move jointly, motivating equity-market controls. Using international asset-return data, Campbell, Serfaty-de Medeiros, and Viceira (2010) show that optimal currency hedges vary across investors and assets, so a mechanical one-for-one hedge need not hold. Across diversified U.S. stock portfolios, Fama and French (2015) show that size, value, profitability, and investment factors explain average-return variation, supporting factor controls. For U.S.-listed currency-hedged ETFs, Shank and Vianna (2016) find dynamic links between exchange rates and investor trading. Our contribution is a reproducible daily matched-pair analysis of one Japan ETF pair with an explicit structural-break interaction and time-ordered data.

The results would benefit U.S.-dollar investors, portfolio managers, and risk teams deciding whether a “hedged” Japan allocation actually offsets daily yen exposure. The pandemic indicator is descriptive, not causal, because many policies and market conditions changed simultaneously.

## Data description (276 words)

The analysis contains 2,753 complete daily observations from February 6, 2014, through July 31, 2026. Yahoo Finance distributes histories assembled from market quotations and corporate actions for investment analysis; we use adjusted closes for HEWJ and EWJ. FRED redistributes official and market series for economic research: DEXJPUS is the Federal Reserve's noon New York yen-per-dollar quote; the Nikkei 225, VIX, and short-term rates represent equity, expected volatility, and monetary conditions. Kenneth French's Data Library constructs research portfolios from security returns using published factor definitions; we use its Japan five-factor and momentum series.

The response, the daily HEWJ-minus-EWJ log-return spread, has mean 0.0206 percentage points, standard deviation 0.6271, and range -4.3097 to 3.7826. It is continuous and can take either sign, making a Gaussian linear conditional mean interpretable. Daily observations are temporally ordered rather than strictly independent, so independence is explicitly assessed in the residual analysis and no causal interpretation is made.

Table 1 summarizes the response and every predictor. Extreme daily movements appear in the response, Nikkei return, momentum, and VIX change; the rate differential is slow-moving because monthly observations are carried forward with a one-month lag. `Post` has 1,348 pre-period and 1,405 post-period observations. Complete cases are retained after joining by trading date.

The model includes yen appreciation, `Post`, Nikkei return, SMB, HML, RMW, CMA, MOM, log VIX change, and the lagged U.S.-Japan rate differential. The `JPYapp × Post` interaction directly answers whether the conditional yen slope differs across the pandemic break. The split is substantively pre-specified from the WHO announcement rather than chosen by searching for the smallest p-value. Data websites and complete citations appear below.

## Ethics discussion (189 words)

The dataset is trustworthy because its provenance, ownership, and transformations are documented. Yahoo Finance closes, FRED series, and Kenneth French factors are public sources, but authority does not eliminate error: providers can revise observations, calendars may differ, and adjusted prices depend on provider methods. We preserve snapshots and SHA-256 checksums, document transformations, and avoid overstating precision. This addresses the module's trustworthiness criteria of provenance, transparency, accuracy, and reproducibility.

Collection and use are ethically low risk. The sources contain aggregate market prices and factor portfolios, not personal information, private holdings, individual trading records, or human-subject data. Consent, confidentiality, and re-identification risks are minimal. We respect ownership by citing each provider, keeping the repository private while terms are reviewed, and not claiming third-party observations.

The principal ethical risk is interpretation. A descriptive association could be presented incorrectly as investment advice or evidence that COVID-19 caused a change. We will state that results apply to one ETF pair, acknowledge survivorship and product-selection limitations, and avoid causal language because changes were uncontrolled. Historical predictive performance is not a promise of future returns. These limits make the use proportionate to the data and question.

## Preliminary results (351 words)

The full ordinary least-squares model is

\[
Y(t) = b0 + b1 JPYapp(t) + b2 Post(t) + b3 [JPYapp(t) x Post(t)] + g'Z(t) + e(t),
\]

where \(Z_t\) contains the eight market and factor controls. Table 2 reports every coefficient with a classical standard error and 95% confidence interval. The model explains 71.21% of daily spread variation (adjusted \(R^2=71.10\%\)). The pre-period yen slope is -0.852 (SE 0.0178; 95% CI [-0.887, -0.817]). Thus, conditional on the controls, a one-percentage-point yen appreciation is associated with a 0.852-percentage-point lower HEWJ-minus-EWJ return. The interaction is -0.0648 (SE 0.0227; p = 0.0043), giving an implied post-period slope of -0.917. The period level shift is not significant. VIX log change is negative; most other controls are imprecisely estimated.

The strong negative currency slope is consistent with Hau and Rey's joint currency-equity mechanism and with the hedge interpretation. Its departure from exactly -1 agrees with Campbell et al.'s result that effective hedges need not be mechanical one-for-one positions. The mostly small factor coefficients suggest that pairing HEWJ with EWJ removes much common equity exposure, while retaining Fama-French controls prevents that conclusion from being assumed. The changed slope is directionally compatible with Shank and Vianna's evidence of time-varying currency-hedged ETF dynamics, although our pandemic comparison is not causal.

Figure 2 provides the complete preliminary diagnostic grid. Residuals versus fitted values show no dominant smooth curve, but the RESET test rejects exact functional form (p = 0.001), so linearity remains questionable. Residual spread changes across fitted values and the Breusch-Pagan test rejects constant variance (p = 0.0048). The Q-Q plot has heavy tails and Jarque-Bera rejects normality (p < 0.001). Residuals over time and the ACF show dependence; the five-lag Breusch-Godfrey test rejects independence (p < 0.001), and Durbin-Watson is 2.85. The maximum VIF is 3.55, so severe multicollinearity is not evident. There are 137 cases above the Cook's-distance screening threshold \(4/n\), with maximum 0.136, indicating influential observations for later investigation.

These are preliminary OLS results. In accordance with the Part 1 instruction, we diagnose but do not correct violations here; robust inference and sensitivity analysis are deferred to the final project.

## Plan for the remaining analysis (275 words)

The focal terms - yen appreciation, `Post`, and their interaction - will remain because they define the research question. Other controls will first be retained on substantive grounds. We will compare theory-preserving nested models using partial F-tests, adjusted \(R^2\), residual behavior, and focal-coefficient stability. We will not drop a control solely because its p-value exceeds 0.05, and hierarchy will be respected.

After every material specification change, we will recheck residual-versus-fitted, Q-Q, time-order, and ACF plots, Breusch-Pagan and Breusch-Godfrey tests, Cook's distance, and VIF. Because the model shows heteroskedasticity, dependence, heavy tails, and functional-form evidence, we will examine a pre-specified nonlinear yen term and a Yeo-Johnson response transformation, which is valid for signed returns; a direct logarithm is invalid. Transformations will be compared for assumption improvement and interpretability, not selected to manufacture significance.

Influential dates will be documented before any sensitivity run. The primary analysis will retain all observations; secondary analyses will compare declared 0.5/99.5-percentile winsorization and the exclusion of individually justified data errors, if any. Once a final functional form is chosen, classical intervals will be supplemented by Newey-West intervals with 1-, 5-, and 10-day lags. We will also vary the pandemic cut within a small declared window rather than search all dates.

Prediction remains secondary. A chronological 80/20 split will train on earlier dates and evaluate later dates against a historical-mean benchmark using RMSE and MAE. No random cross-validation will be used. The frozen raw files, cleaned CSV, code, and outputs will be versioned together.

The schedule in Table 3 assigns analysis, poster, and recording milestones. Member placeholders will be replaced with names from the signed Teamwork Agreement before submission.

## References

Campbell, J. Y., Serfaty-de Medeiros, K., & Viceira, L. M. (2010). Global currency hedging. *The Journal of Finance, 65*(1), 87–121. https://doi.org/10.1111/j.1540-6261.2009.01524.x

Fama, E. F., & French, K. R. (2015). A five-factor asset pricing model. *Journal of Financial Economics, 116*(1), 1–22. https://doi.org/10.1016/j.jfineco.2014.10.010

Hau, H., & Rey, H. (2006). Exchange rates, equity prices, and capital flows. *The Review of Financial Studies, 19*(1), 273–317. https://doi.org/10.1093/rfs/hhj008

Shank, C. A., & Vianna, A. C. (2016). Are US-dollar-hedged-ETF investors aggressive on exchange rates? A panel VAR approach. *Research in International Business and Finance, 38*, 430–438. https://doi.org/10.1016/j.ribaf.2016.05.002

## Data and product documentation

Federal Reserve Bank of St. Louis. (n.d.). *DEXJPUS; NIKKEI225; VIXCLS; IRSTCI01USM156N; IRSTCI01JPM156N* [Data sets]. FRED. https://fred.stlouisfed.org/

iShares. (n.d.). *HEWJ and EWJ fund pages and currency-hedged product documentation*. https://www.ishares.com/

Kenneth R. French Data Library. (n.d.). *Japan 5 factors [Daily] and Japan momentum factor [Daily]* [Data sets]. https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html

World Health Organization. (2020, March 11). *WHO Director-General's opening remarks at the media briefing on COVID-19*. https://www.who.int/

Yahoo Finance. (n.d.). *HEWJ and EWJ historical data* [Data sets]. https://finance.yahoo.com/

## Submission items requiring group confirmation

1. Replace bracketed member names and role assignments with the actual group roster.
2. Complete and sign the course's Group Teamwork Agreement PDF using the same names and responsibilities.
3. Upload the prepared original and cleaned CSV folders to UofT OneDrive and add a Quercus submission comment with permission set to “anyone in UofT with the link can access.”

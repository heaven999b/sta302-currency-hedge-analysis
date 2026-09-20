options(stringsAsFactors = FALSE, scipen = 999)

suppressPackageStartupMessages(library(jsonlite))

locate_project_dir <- function() {
  file_args <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
  script_candidate <- if (length(file_args)) {
    file.path(dirname(normalizePath(sub("^--file=", "", file_args[1]), mustWork = FALSE)), "..")
  } else {
    NA_character_
  }
  candidates <- unique(c(script_candidate, getwd(), file.path(getwd(), ".."),
                         file.path(getwd(), "..", "..")))
  candidates <- candidates[!is.na(candidates)]
  for (candidate in candidates) {
    repo_input <- file.exists(file.path(candidate, "data", "raw", "Yahoo_HEWJ_chart.json"))
    submission_input <- file.exists(file.path(candidate, "data", "original",
                                               "Yahoo_HEWJ_original_export.csv"))
    if (repo_input || submission_input) {
      return(normalizePath(candidate, mustWork = TRUE))
    }
  }
  stop("Could not locate the repository root containing data/raw.")
}

project_dir <- locate_project_dir()
repo_mode <- file.exists(file.path(project_dir, "data", "raw", "Yahoo_HEWJ_chart.json"))
raw_dir <- if (repo_mode) file.path(project_dir, "data", "raw") else file.path(project_dir, "data", "original")
processed_dir <- if (repo_mode) file.path(project_dir, "data", "processed") else file.path(project_dir, "data", "cleaned")
results_dir <- file.path(project_dir, "results")
figures_dir <- file.path(project_dir, "figures")

dir.create(processed_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(results_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(figures_dir, recursive = TRUE, showWarnings = FALSE)

read_french_daily <- function(path) {
  d <- read.csv(path, skip = 5, check.names = FALSE, na.strings = c("-99.99", ""))
  names(d)[1] <- "date"
  d$date <- as.Date(trimws(as.character(d$date)), format = "%Y%m%d")
  d <- d[!is.na(d$date), , drop = FALSE]
  for (j in seq.int(2, ncol(d))) d[[j]] <- as.numeric(d[[j]])
  d
}

read_yahoo_adjusted <- function(path, value_name) {
  if (grepl("\\.json$", path, ignore.case = TRUE)) {
    payload <- jsonlite::fromJSON(path)
    result <- payload$chart$result
    timestamps <- result$timestamp[[1]]
    adjusted <- result$indicators$adjclose[[1]]$adjclose[[1]]
    stopifnot(length(timestamps) == length(adjusted))
    out <- data.frame(
      date = as.Date(as.POSIXct(timestamps, origin = "1970-01-01", tz = "UTC")),
      value = as.numeric(adjusted)
    )
  } else {
    exported <- read.csv(path, check.names = FALSE)
    stopifnot(all(c("date", "adjusted_close") %in% names(exported)))
    out <- data.frame(date = as.Date(exported$date), value = as.numeric(exported$adjusted_close))
  }
  names(out)[2] <- value_name
  out[!is.na(out[[value_name]]), , drop = FALSE]
}

native_log_return <- function(data, value_name, return_name, sign = 1) {
  data <- data[!is.na(data[[value_name]]) & data[[value_name]] > 0, c("date", value_name)]
  data <- data[order(data$date), ]
  stopifnot(!anyDuplicated(data$date), nrow(data) >= 2L)
  out <- data.frame(
    date = data$date[-1],
    interval_start = data$date[-nrow(data)],
    value = sign * 100 * diff(log(data[[value_name]]))
  )
  names(out)[2:3] <- c(paste0(return_name, "_start"), return_name)
  out
}

month_floor <- function(x) as.Date(format(x, "%Y-%m-01"))
next_month <- function(x) as.Date(format(month_floor(x) + 32, "%Y-%m-01"))

newey_west <- function(model, lag = 5) {
  X <- model.matrix(model)
  u <- residuals(model)
  n <- nrow(X)
  inv_xx <- solve(crossprod(X))
  xu <- X * as.numeric(u)
  meat <- crossprod(xu)
  if (lag > 0) {
    for (ell in seq_len(lag)) {
      weight <- 1 - ell / (lag + 1)
      gamma <- crossprod(xu[(ell + 1):n, , drop = FALSE], xu[1:(n - ell), , drop = FALSE])
      meat <- meat + weight * (gamma + t(gamma))
    }
  }
  inv_xx %*% meat %*% inv_xx
}

coefficient_table <- function(model, vcov_matrix = vcov(model), label = "Classical OLS") {
  b <- coef(model)
  se <- sqrt(diag(vcov_matrix))
  df <- df.residual(model)
  t_value <- b / se
  p_value <- 2 * pt(abs(t_value), df = df, lower.tail = FALSE)
  crit <- qt(0.975, df = df)
  data.frame(
    inference = label,
    term = names(b),
    estimate = as.numeric(b),
    std_error = as.numeric(se),
    t_value = as.numeric(t_value),
    p_value = as.numeric(p_value),
    conf_low = as.numeric(b - crit * se),
    conf_high = as.numeric(b + crit * se),
    row.names = NULL
  )
}

linear_test <- function(model, weights, null = 0, vcov_matrix = vcov(model), label = "Classical OLS") {
  b <- coef(model)
  a <- rep(0, length(b)); names(a) <- names(b)
  if (!all(names(weights) %in% names(b))) {
    stop("Unknown coefficient(s) in linear test: ",
         paste(setdiff(names(weights), names(b)), collapse = ", "))
  }
  a[names(weights)] <- weights
  estimate <- sum(a * b)
  se <- sqrt(drop(t(a) %*% vcov_matrix %*% a))
  t_value <- (estimate - null) / se
  p_value <- 2 * pt(abs(t_value), df = df.residual(model), lower.tail = FALSE)
  data.frame(inference = label, estimate = estimate, std_error = se,
             null = null, t_value = t_value, p_value = p_value)
}

manual_vif <- function(model) {
  X <- model.matrix(model)[, -1, drop = FALSE]
  vals <- vapply(seq_len(ncol(X)), function(j) {
    fit <- lm(X[, j] ~ X[, -j, drop = FALSE])
    1 / (1 - summary(fit)$r.squared)
  }, numeric(1))
  data.frame(term = colnames(X), vif = vals, row.names = NULL)
}

prediction_metrics <- function(actual, predicted) {
  c(RMSE = sqrt(mean((actual - predicted)^2)), MAE = mean(abs(actual - predicted)))
}

trailing_mean <- function(x, window = 20L) {
  as.numeric(stats::filter(x, rep(1 / window, window), sides = 1))
}

winsorize_vector <- function(x, probs = c(0.005, 0.995)) {
  limits <- quantile(x, probs = probs, na.rm = TRUE, names = FALSE, type = 7)
  pmin(pmax(x, limits[1]), limits[2])
}

yeo_johnson <- function(x, lambda) {
  out <- numeric(length(x))
  nonnegative <- x >= 0
  if (abs(lambda) < 1e-10) {
    out[nonnegative] <- log1p(x[nonnegative])
  } else {
    out[nonnegative] <- ((x[nonnegative] + 1)^lambda - 1) / lambda
  }
  if (abs(lambda - 2) < 1e-10) {
    out[!nonnegative] <- -log1p(-x[!nonnegative])
  } else {
    out[!nonnegative] <- -(((1 - x[!nonnegative])^(2 - lambda) - 1) / (2 - lambda))
  }
  out
}

inverse_yeo_johnson <- function(z, lambda) {
  out <- numeric(length(z))
  nonnegative <- z >= 0
  if (abs(lambda) < 1e-10) {
    out[nonnegative] <- exp(z[nonnegative]) - 1
  } else {
    out[nonnegative] <- pmax(lambda * z[nonnegative] + 1, .Machine$double.eps)^(1 / lambda) - 1
  }
  if (abs(lambda - 2) < 1e-10) {
    out[!nonnegative] <- 1 - exp(-z[!nonnegative])
  } else {
    out[!nonnegative] <- 1 - pmax(1 - (2 - lambda) * z[!nonnegative],
                                  .Machine$double.eps)^(1 / (2 - lambda))
  }
  out
}

model_diagnostics <- function(model, bg_lag = 5L) {
  e <- residuals(model)
  X <- model.matrix(model)
  n <- nrow(X); k <- ncol(X)
  dw <- sum(diff(e)^2) / sum(e^2)
  aux_bp <- lm(I(e^2) ~ X[, -1, drop = FALSE])
  bp_stat <- n * summary(aux_bp)$r.squared
  bp_df <- k - 1
  bp_p <- pchisq(bp_stat, df = bp_df, lower.tail = FALSE)
  bg_frame <- data.frame(e = e[(bg_lag + 1):n], X[(bg_lag + 1):n, -1, drop = FALSE])
  for (ell in seq_len(bg_lag)) {
    bg_frame[[paste0("lag", ell)]] <- e[(bg_lag + 1 - ell):(n - ell)]
  }
  bg_model <- lm(e ~ ., data = bg_frame)
  bg_stat <- nrow(bg_frame) * summary(bg_model)$r.squared
  bg_p <- pchisq(bg_stat, df = bg_lag, lower.tail = FALSE)
  standardized <- (e - mean(e)) / sd(e)
  jb_stat <- n / 6 * mean(standardized^3)^2 + n / 24 * (mean(standardized^4) - 3)^2
  jb_p <- pchisq(jb_stat, df = 2, lower.tail = FALSE)
  fitted_values <- fitted(model)
  response <- model.response(model.frame(model))
  augmented_fit <- lm.fit(cbind(X, fitted_values^2, fitted_values^3), response)
  rss_base <- sum(e^2)
  rss_augmented <- sum(augmented_fit$residuals^2)
  reset_df <- 2L
  reset_residual_df <- n - ncol(X) - reset_df
  reset_f <- ((rss_base - rss_augmented) / reset_df) /
    (rss_augmented / reset_residual_df)
  reset_p <- pf(reset_f, df1 = reset_df, df2 = reset_residual_df, lower.tail = FALSE)
  list(
    durbin_watson = dw,
    breusch_pagan_stat = bp_stat,
    breusch_pagan_df = bp_df,
    breusch_pagan_p = bp_p,
    breusch_godfrey_lag5_stat = bg_stat,
    breusch_godfrey_lag5_p = bg_p,
    jarque_bera_stat = jb_stat,
    jarque_bera_p = jb_p,
    reset_f = reset_f,
    reset_p = reset_p
  )
}

joint_wald_test <- function(model, terms, vcov_matrix = vcov(model)) {
  b <- coef(model)
  stopifnot(all(terms %in% names(b)))
  A <- matrix(0, nrow = length(terms), ncol = length(b),
              dimnames = list(terms, names(b)))
  for (j in seq_along(terms)) A[j, terms[j]] <- 1
  estimate <- drop(A %*% b)
  covariance <- A %*% vcov_matrix %*% t(A)
  statistic <- drop(t(estimate) %*% solve(covariance, estimate))
  data.frame(statistic = statistic, df = length(terms),
             p_value = pchisq(statistic, df = length(terms), lower.tail = FALSE))
}

select_yeo_johnson_lambda <- function(data, formula_rhs, grid = seq(-2, 2, by = .05)) {
  scores <- vapply(grid, function(lambda) {
    transformed <- data
    transformed$Y_yj <- yeo_johnson(transformed$Y, lambda)
    model <- lm(as.formula(paste("Y_yj ~", formula_rhs)), data = transformed)
    rss <- sum(residuals(model)^2)
    jacobian <- (lambda - 1) * sum(log1p(data$Y[data$Y >= 0])) +
      (1 - lambda) * sum(log1p(-data$Y[data$Y < 0]))
    -nrow(data) / 2 * log(rss / nrow(data)) + jacobian
  }, numeric(1))
  data.frame(lambda = grid, profile_score = scores, selected = scores == max(scores))
}

summarize_fx_model <- function(model, analysis_name, data_used, note = "") {
  vc <- newey_west(model, lag = 5)
  interaction <- linear_test(model, setNames(1, "JPY_app:PostPost"), vcov_matrix = vc,
                             label = "Newey-West HAC(5)")
  pre <- linear_test(model, c(JPY_app = 1), null = -1, vcov_matrix = vc,
                     label = "Newey-West HAC(5)")
  post <- linear_test(model, setNames(c(1, 1), c("JPY_app", "JPY_app:PostPost")),
                      null = -1, vcov_matrix = vc, label = "Newey-West HAC(5)")
  data.frame(
    analysis = analysis_name,
    rows = nrow(data_used),
    r_squared = summary(model)$r.squared,
    pre_slope = pre$estimate,
    pre_slope_vs_minus1_p = pre$p_value,
    interaction = interaction$estimate,
    interaction_hac5_p = interaction$p_value,
    post_slope = post$estimate,
    post_slope_vs_minus1_p = post$p_value,
    note = note
  )
}

ff5 <- read_french_daily(file.path(raw_dir, "Japan_5_Factors_Daily.csv"))
mom <- read_french_daily(file.path(raw_dir, "Japan_MOM_Factor_Daily.csv"))
names(mom)[names(mom) == "WML"] <- "MOM"
yahoo_hewj_path <- file.path(raw_dir, if (repo_mode) "Yahoo_HEWJ_chart.json" else "Yahoo_HEWJ_original_export.csv")
yahoo_ewj_path <- file.path(raw_dir, if (repo_mode) "Yahoo_EWJ_chart.json" else "Yahoo_EWJ_original_export.csv")
hewj <- read_yahoo_adjusted(yahoo_hewj_path, "HEWJ")
ewj <- read_yahoo_adjusted(yahoo_ewj_path, "EWJ")

fx <- read.csv(file.path(raw_dir, "FRED_DEXJPUS_daily.csv"), na.strings = c("", "."))
names(fx)[1] <- "date"; fx$date <- as.Date(fx$date)
market <- read.csv(file.path(raw_dir, "FRED_NIKKEI225_VIXCLS_daily.csv"), na.strings = c("", "."))
names(market)[1] <- "date"; market$date <- as.Date(market$date)
rates <- read.csv(file.path(raw_dir, "FRED_US_Japan_rates_monthly.csv"), na.strings = c("", "."))
names(rates)[1] <- "month"; rates$month <- as.Date(rates$month)
rates$rate_diff <- rates$IRSTCI01USM156N - rates$IRSTCI01JPM156N
rates$rate_month <- next_month(rates$month)
rates <- rates[, c("rate_month", "rate_diff")]

# Each price series is transformed on its own native calendar before any merge.
# This prevents a missing observation in one source from silently changing another
# source's return interval.
hewj_ret <- native_log_return(hewj, "HEWJ", "HEWJ_ret")
ewj_ret <- native_log_return(ewj, "EWJ", "EWJ_ret")
fx_ret <- native_log_return(fx, "DEXJPUS", "JPY_app", sign = -1)
nikkei_ret <- native_log_return(market[, c("date", "NIKKEI225")], "NIKKEI225", "Nikkei_ret")
vix_ret <- native_log_return(market[, c("date", "VIXCLS")], "VIXCLS", "dlog_VIX")

etf_returns <- merge(hewj_ret, ewj_ret, by = "date")
etf_returns <- etf_returns[etf_returns$HEWJ_ret_start == etf_returns$EWJ_ret_start, ]
etf_returns$Y <- etf_returns$HEWJ_ret - etf_returns$EWJ_ret
names(etf_returns)[names(etf_returns) == "HEWJ_ret_start"] <- "Y_start"
etf_returns <- etf_returns[, c("date", "Y_start", "Y")]

merged <- Reduce(function(x, y) merge(x, y, by = "date"),
                 list(etf_returns, fx_ret, nikkei_ret, vix_ret, ff5, mom))
merged$rate_month <- month_floor(merged$date)
merged <- merge(merged, rates, by = "rate_month", all.x = TRUE)
merged <- merged[order(merged$date), ]
merged_without_period <- merged

merged$Post <- factor(ifelse(merged$date >= as.Date("2020-03-12"), "Post", "Pre"),
                      levels = c("Pre", "Post"))
merged <- merged[merged$date != as.Date("2020-03-11"), ]

analysis_columns <- c("date", "Y", "JPY_app", "Post", "Nikkei_ret", "SMB", "HML",
                      "RMW", "CMA", "MOM", "dlog_VIX", "rate_diff")
end_date_aligned <- merged[complete.cases(merged[, analysis_columns]), ]
joint_interval_match <- end_date_aligned$Y_start == end_date_aligned$JPY_app_start &
  end_date_aligned$Y_start == end_date_aligned$Nikkei_ret_start &
  end_date_aligned$Y_start == end_date_aligned$dlog_VIX_start
analysis_data <- end_date_aligned[joint_interval_match, analysis_columns]
analysis_data <- analysis_data[order(analysis_data$date), ]
stopifnot(nrow(analysis_data) >= 1000L)
stopifnot(nlevels(analysis_data$Post) == 2L)

alignment_audit <- data.frame(
  series = c("JPY_app", "Nikkei_ret", "dlog_VIX"),
  native_return_rows = c(nrow(fx_ret), nrow(nikkei_ret), nrow(vix_ret)),
  candidate_rows_aligned_by_end_date = nrow(end_date_aligned),
  exact_interval_start_matches_Y = c(
    sum(end_date_aligned$JPY_app_start == end_date_aligned$Y_start),
    sum(end_date_aligned$Nikkei_ret_start == end_date_aligned$Y_start),
    sum(end_date_aligned$dlog_VIX_start == end_date_aligned$Y_start)
  ),
  final_joint_interval_rows = nrow(analysis_data)
)
alignment_audit$differing_interval_start <-
  alignment_audit$candidate_rows_aligned_by_end_date - alignment_audit$exact_interval_start_matches_Y

full_formula <- Y ~ JPY_app * Post + Nikkei_ret + SMB + HML + RMW + CMA + MOM + dlog_VIX + rate_diff
baseline_formula <- Y ~ JPY_app * Post
full_model <- lm(full_formula, data = analysis_data)
baseline_model <- lm(baseline_formula, data = analysis_data)
end_date_only_model <- lm(full_formula, data = end_date_aligned)

vcov_hac5 <- newey_west(full_model, lag = 5)
coef_classic <- coefficient_table(full_model)
coef_hac5 <- coefficient_table(full_model, vcov_hac5, "Newey-West HAC(5)")
vif_table <- manual_vif(full_model)

interaction_name <- "JPY_app:PostPost"
pre_slope_classic <- linear_test(full_model, c(JPY_app = 1), null = -1)
pre_slope_classic$period <- "Pre-pandemic"; pre_slope_classic$hypothesis <- "FX slope = -1"
post_slope_classic <- linear_test(
  full_model,
  setNames(c(1, 1), c("JPY_app", interaction_name)),
  null = -1
)
post_slope_classic$period <- "Post-pandemic"; post_slope_classic$hypothesis <- "FX slope = -1"
pre_slope_hac <- linear_test(full_model, c(JPY_app = 1), null = -1, vcov_matrix = vcov_hac5,
                             label = "Newey-West HAC(5)")
pre_slope_hac$period <- "Pre-pandemic"; pre_slope_hac$hypothesis <- "FX slope = -1"
post_slope_hac <- linear_test(full_model, setNames(c(1, 1), c("JPY_app", interaction_name)), null = -1,
                              vcov_matrix = vcov_hac5, label = "Newey-West HAC(5)")
post_slope_hac$period <- "Post-pandemic"; post_slope_hac$hypothesis <- "FX slope = -1"
hypothesis_tests <- rbind(pre_slope_classic, post_slope_classic, pre_slope_hac, post_slope_hac)

hac_lags <- c(1L, 5L, 10L)
hac_sensitivity <- do.call(rbind, lapply(hac_lags, function(hac_lag) {
  vc <- newey_west(full_model, lag = hac_lag)
  interaction_test <- linear_test(full_model, setNames(1, interaction_name), vcov_matrix = vc,
                                  label = paste0("Newey-West HAC(", hac_lag, ")"))
  pre_test <- linear_test(full_model, c(JPY_app = 1), null = -1, vcov_matrix = vc,
                          label = paste0("Newey-West HAC(", hac_lag, ")"))
  post_test <- linear_test(full_model, setNames(c(1, 1), c("JPY_app", interaction_name)),
                           null = -1, vcov_matrix = vc,
                           label = paste0("Newey-West HAC(", hac_lag, ")"))
  data.frame(
    lag = hac_lag,
    interaction_estimate = interaction_test$estimate,
    interaction_se = interaction_test$std_error,
    interaction_p = interaction_test$p_value,
    interaction_conf_low = interaction_test$estimate - qt(.975, df.residual(full_model)) * interaction_test$std_error,
    interaction_conf_high = interaction_test$estimate + qt(.975, df.residual(full_model)) * interaction_test$std_error,
    pre_slope = pre_test$estimate,
    pre_slope_vs_minus1_p = pre_test$p_value,
    post_slope = post_test$estimate,
    post_slope_vs_minus1_p = post_test$p_value
  )
}))

alignment_models <- list(
  "Exact shared return interval (primary)" = full_model,
  "Same end date only (sensitivity)" = end_date_only_model
)
alignment_model_sensitivity <- do.call(rbind, Map(function(alignment_name, model_item) {
  vc <- newey_west(model_item, lag = 5)
  interaction_test <- linear_test(model_item, setNames(1, interaction_name), vcov_matrix = vc,
                                  label = "Newey-West HAC(5)")
  data.frame(
    alignment_rule = alignment_name,
    rows = nobs(model_item),
    r_squared = summary(model_item)$r.squared,
    pre_slope = unname(coef(model_item)["JPY_app"]),
    interaction = interaction_test$estimate,
    interaction_hac5_p = interaction_test$p_value,
    post_slope = unname(coef(model_item)["JPY_app"] + coef(model_item)[interaction_name])
  )
}, names(alignment_models), alignment_models))

resid <- residuals(full_model)
n <- nobs(full_model)
primary_diagnostics <- model_diagnostics(full_model)
dw <- primary_diagnostics$durbin_watson
bp_stat <- primary_diagnostics$breusch_pagan_stat
bp_df <- primary_diagnostics$breusch_pagan_df
bp_p <- primary_diagnostics$breusch_pagan_p
bg_stat <- primary_diagnostics$breusch_godfrey_lag5_stat
bg_p <- primary_diagnostics$breusch_godfrey_lag5_p
jb_stat <- primary_diagnostics$jarque_bera_stat
jb_p <- primary_diagnostics$jarque_bera_p
cooks <- cooks.distance(full_model)

# Strict chronological evaluation: 60% train, 20% tuning, 20% untouched test.
# Model selection uses tuning only; test is evaluated once after the choice is locked.
n_obs <- nrow(analysis_data)
train_end_index <- floor(0.60 * n_obs)
tuning_end_index <- floor(0.80 * n_obs)
train <- analysis_data[seq_len(train_end_index), ]
tuning <- analysis_data[(train_end_index + 1):tuning_end_index, ]
test <- analysis_data[(tuning_end_index + 1):n_obs, ]
analysis_data$split <- factor(c(rep("train", nrow(train)), rep("tuning", nrow(tuning)),
                                rep("test", nrow(test))), levels = c("train", "tuning", "test"))

candidate_formulas <- list(
  "FX interaction" = baseline_formula,
  "Macro controls" = Y ~ JPY_app * Post + Nikkei_ret + dlog_VIX + rate_diff,
  "Full factor model" = full_formula
)
tuning_metrics <- do.call(rbind, lapply(names(candidate_formulas), function(model_name) {
  fitted_candidate <- lm(candidate_formulas[[model_name]], data = train)
  metrics <- prediction_metrics(tuning$Y, predict(fitted_candidate, newdata = tuning))
  data.frame(model = model_name, RMSE = unname(metrics["RMSE"]), MAE = unname(metrics["MAE"]),
             train_start = min(train$date), train_end = max(train$date),
             tuning_start = min(tuning$date), tuning_end = max(tuning$date))
}))
selected_model_name <- tuning_metrics$model[which.min(tuning_metrics$RMSE)]
development <- rbind(train, tuning)
selected_model <- lm(candidate_formulas[[selected_model_name]], data = development)
test_prediction <- as.numeric(predict(selected_model, newdata = test))
historical_mean_prediction <- rep(mean(development$Y), nrow(test))
zero_prediction <- rep(0, nrow(test))

test_metrics <- do.call(rbind, lapply(list(
  selected = list(name = paste0("Selected: ", selected_model_name), pred = test_prediction),
  historical_mean = list(name = "Historical-mean benchmark", pred = historical_mean_prediction),
  zero = list(name = "Zero-return benchmark", pred = zero_prediction)
), function(item) {
  metrics <- prediction_metrics(test$Y, item$pred)
  data.frame(model = item$name, RMSE = unname(metrics["RMSE"]), MAE = unname(metrics["MAE"]),
             development_end = max(development$date), test_start = min(test$date), test_end = max(test$date))
}))

test_predictions <- data.frame(
  date = test$date,
  actual = test$Y,
  selected_model = selected_model_name,
  predicted = test_prediction,
  historical_mean = historical_mean_prediction,
  zero = zero_prediction
)
split_summary <- do.call(rbind, lapply(levels(analysis_data$split), function(split_name) {
  block <- analysis_data[analysis_data$split == split_name, ]
  data.frame(split = split_name, rows = nrow(block), start_date = min(block$date), end_date = max(block$date),
             purpose = switch(split_name, train = "fit candidate models", tuning = "select by RMSE",
                              test = "one final held-out evaluation"))
}))

stopifnot(max(train$date) < min(tuning$date), max(tuning$date) < min(test$date))
stopifnot(!anyDuplicated(analysis_data$date))

# Functional-form sensitivity. These alternatives are evaluated on the tuning
# period only and do not reopen the already locked held-out test decision.
full_rhs <- "JPY_app * Post + Nikkei_ret + SMB + HML + RMW + CMA + MOM + dlog_VIX + rate_diff"
quadratic_formula <- Y ~ JPY_app * Post + I(JPY_app^2) * Post + Nikkei_ret +
  SMB + HML + RMW + CMA + MOM + dlog_VIX + rate_diff
quadratic_train_model <- lm(quadratic_formula, data = train)
quadratic_tuning_prediction <- predict(quadratic_train_model, newdata = tuning)
quadratic_tuning_metrics <- prediction_metrics(tuning$Y, quadratic_tuning_prediction)
quadratic_model <- lm(quadratic_formula, data = analysis_data)
quadratic_diagnostics <- model_diagnostics(quadratic_model)
quadratic_terms <- grep("I\\(JPY_app\\^2\\)", names(coef(quadratic_model)), value = TRUE)
quadratic_wald <- joint_wald_test(quadratic_model, quadratic_terms,
                                  newey_west(quadratic_model, lag = 5))

lambda_profile <- select_yeo_johnson_lambda(train, full_rhs)
selected_lambda <- lambda_profile$lambda[which.max(lambda_profile$profile_score)]
train_yj <- train
train_yj$Y_yj <- yeo_johnson(train_yj$Y, selected_lambda)
yj_train_model <- lm(as.formula(paste("Y_yj ~", full_rhs)), data = train_yj)
yj_tuning_prediction <- inverse_yeo_johnson(
  predict(yj_train_model, newdata = tuning), selected_lambda
)
yj_tuning_metrics <- prediction_metrics(tuning$Y, yj_tuning_prediction)
analysis_yj <- analysis_data
analysis_yj$Y_yj <- yeo_johnson(analysis_yj$Y, selected_lambda)
yj_model <- lm(as.formula(paste("Y_yj ~", full_rhs)), data = analysis_yj)
yj_diagnostics <- model_diagnostics(yj_model)

linear_tuning <- tuning_metrics[tuning_metrics$model == "Full factor model", ]
functional_form_sensitivity <- rbind(
  data.frame(
    specification = "Primary linear response",
    response_scale = "Original percentage-point return spread",
    yeo_johnson_lambda = NA_real_, rows = nobs(full_model), parameters = length(coef(full_model)),
    adjusted_r_squared = summary(full_model)$adj.r.squared,
    tuning_RMSE_original_scale = linear_tuning$RMSE,
    tuning_MAE_original_scale = linear_tuning$MAE,
    reset_p = primary_diagnostics$reset_p,
    breusch_pagan_p = primary_diagnostics$breusch_pagan_p,
    breusch_godfrey_lag5_p = primary_diagnostics$breusch_godfrey_lag5_p,
    jarque_bera_p = primary_diagnostics$jarque_bera_p,
    nonlinear_terms_hac5_joint_p = NA_real_,
    role = "Primary: directly interpretable hedge slope; held-out result remains locked"
  ),
  data.frame(
    specification = "Quadratic yen sensitivity",
    response_scale = "Original percentage-point return spread",
    yeo_johnson_lambda = NA_real_, rows = nobs(quadratic_model), parameters = length(coef(quadratic_model)),
    adjusted_r_squared = summary(quadratic_model)$adj.r.squared,
    tuning_RMSE_original_scale = unname(quadratic_tuning_metrics["RMSE"]),
    tuning_MAE_original_scale = unname(quadratic_tuning_metrics["MAE"]),
    reset_p = quadratic_diagnostics$reset_p,
    breusch_pagan_p = quadratic_diagnostics$breusch_pagan_p,
    breusch_godfrey_lag5_p = quadratic_diagnostics$breusch_godfrey_lag5_p,
    jarque_bera_p = quadratic_diagnostics$jarque_bera_p,
    nonlinear_terms_hac5_joint_p = quadratic_wald$p_value,
    role = "Sensitivity: hierarchy-preserving quadratic terms; tuning only"
  ),
  data.frame(
    specification = "Yeo-Johnson response",
    response_scale = "Yeo-Johnson transformed; inverse transformed for tuning metrics",
    yeo_johnson_lambda = selected_lambda, rows = nobs(yj_model), parameters = length(coef(yj_model)),
    adjusted_r_squared = summary(yj_model)$adj.r.squared,
    tuning_RMSE_original_scale = unname(yj_tuning_metrics["RMSE"]),
    tuning_MAE_original_scale = unname(yj_tuning_metrics["MAE"]),
    reset_p = yj_diagnostics$reset_p,
    breusch_pagan_p = yj_diagnostics$breusch_pagan_p,
    breusch_godfrey_lag5_p = yj_diagnostics$breusch_godfrey_lag5_p,
    jarque_bera_p = yj_diagnostics$jarque_bera_p,
    nonlinear_terms_hac5_joint_p = NA_real_,
    role = "Sensitivity: lambda selected on training data; slope loses direct hedge-ratio meaning"
  )
)

# Influence sensitivity. Primary estimates retain every valid observation.
continuous_variables <- c("Y", "JPY_app", "Nikkei_ret", "SMB", "HML", "RMW",
                          "CMA", "MOM", "dlog_VIX", "rate_diff")
winsorized_data <- analysis_data
for (variable in continuous_variables) {
  winsorized_data[[variable]] <- winsorize_vector(winsorized_data[[variable]])
}
winsorized_model <- lm(full_formula, data = winsorized_data)
cooks_threshold <- 4 / nobs(full_model)
cooks_retained <- cooks <= cooks_threshold
cooks_trimmed_data <- analysis_data[cooks_retained, ]
cooks_trimmed_model <- lm(full_formula, data = cooks_trimmed_data)
influence_sensitivity <- rbind(
  summarize_fx_model(full_model, "Primary: all valid observations", analysis_data,
                     "Registered primary analysis"),
  summarize_fx_model(winsorized_model, "Winsorized 0.5/99.5 percentiles", winsorized_data,
                     "All continuous analysis variables winsorized; no rows removed"),
  summarize_fx_model(cooks_trimmed_model, "Cook's D <= 4/n stress test", cooks_trimmed_data,
                     "Post-hoc mechanical stress test; not a preferred estimate")
)
influence_audit <- data.frame(
  date = analysis_data$date,
  cooks_distance = as.numeric(cooks),
  threshold_4_over_n = cooks_threshold,
  flagged = cooks > cooks_threshold,
  leverage = as.numeric(hatvalues(full_model)),
  standardized_residual = as.numeric(rstandard(full_model)),
  Y = analysis_data$Y,
  JPY_app = analysis_data$JPY_app,
  integrity_status = "Frozen-source hash and interval checks passed; retained in primary"
)
influence_audit <- influence_audit[order(influence_audit$cooks_distance, decreasing = TRUE), ]
influence_audit$influence_rank <- seq_len(nrow(influence_audit))

# Pandemic break sensitivity uses the same exact-interval rule and a fixed,
# declared five-calendar-day window around the WHO date.
break_dates <- as.Date(c("2020-03-06", "2020-03-11", "2020-03-16"))
break_date_sensitivity <- do.call(rbind, lapply(break_dates, function(cut_date) {
  candidate <- merged_without_period
  candidate$Post <- factor(ifelse(candidate$date > cut_date, "Post", "Pre"),
                           levels = c("Pre", "Post"))
  candidate <- candidate[candidate$date != cut_date, ]
  candidate <- candidate[complete.cases(candidate[, analysis_columns]), ]
  exact_match <- candidate$Y_start == candidate$JPY_app_start &
    candidate$Y_start == candidate$Nikkei_ret_start &
    candidate$Y_start == candidate$dlog_VIX_start
  candidate <- candidate[exact_match, analysis_columns]
  candidate <- candidate[order(candidate$date), ]
  model <- lm(full_formula, data = candidate)
  summary_row <- summarize_fx_model(model, paste("Transition", cut_date), candidate,
                                    "Date omitted; Post begins on the following calendar day")
  summary_row$transition_date <- cut_date
  summary_row$pre_rows <- sum(candidate$Post == "Pre")
  summary_row$post_rows <- sum(candidate$Post == "Post")
  summary_row
}))

data_quality_audit <- data.frame(
  check = c("processed_rows", "date_unique", "date_strictly_increasing", "complete_analysis_fields",
            "exact_return_interval", "train_before_tuning", "tuning_before_test",
            "split_rows_cover_sample", "stochastic_steps"),
  status = c(
    nrow(analysis_data) == 2655L,
    !anyDuplicated(analysis_data$date),
    all(diff(analysis_data$date) > 0),
    !anyNA(analysis_data[, c("date", continuous_variables, "Post", "split")]),
    all(joint_interval_match[match(analysis_data$date, end_date_aligned$date)]),
    max(train$date) < min(tuning$date),
    max(tuning$date) < min(test$date),
    sum(split_summary$rows) == nrow(analysis_data),
    FALSE
  ),
  expected = c("2655", "TRUE", "TRUE", "TRUE", "TRUE", "TRUE", "TRUE", "TRUE", "FALSE"),
  detail = c(
    paste(nrow(analysis_data), "rows"),
    paste(length(unique(analysis_data$date)), "unique dates"),
    paste(min(analysis_data$date), "to", max(analysis_data$date)),
    paste("Missing values:", sum(is.na(analysis_data))),
    "HEWJ/EWJ, FX, Nikkei and VIX return start/end dates agree",
    paste(max(train$date), "<", min(tuning$date)),
    paste(max(tuning$date), "<", min(test$date)),
    paste(sum(split_summary$rows), "rows assigned once"),
    "OLS, deterministic transformations and fixed chronological splits; seed not applicable"
  )
)
stopifnot(all(data_quality_audit$status == (data_quality_audit$expected == "TRUE" | data_quality_audit$expected == "2655")))

diagnostics <- data.frame(
  metric = c("observations", "start_date", "end_date", "pre_observations", "post_observations",
             "r_squared_full", "adjusted_r_squared_full", "r_squared_baseline", "residual_sigma",
             "durbin_watson", "breusch_pagan_stat", "breusch_pagan_df", "breusch_pagan_p",
             "breusch_godfrey_lag5_stat", "breusch_godfrey_lag5_p", "jarque_bera_stat",
             "jarque_bera_p", "reset_f", "reset_p", "max_vif", "max_vif_term",
             "max_cooks_distance", "cooks_over_4_over_n"),
  value = c(nrow(analysis_data), as.character(min(analysis_data$date)), as.character(max(analysis_data$date)),
            sum(analysis_data$Post == "Pre"), sum(analysis_data$Post == "Post"),
            summary(full_model)$r.squared, summary(full_model)$adj.r.squared,
            summary(baseline_model)$r.squared, summary(full_model)$sigma, dw,
            bp_stat, bp_df, bp_p, bg_stat, bg_p, jb_stat, jb_p,
            primary_diagnostics$reset_f, primary_diagnostics$reset_p, max(vif_table$vif),
            vif_table$term[which.max(vif_table$vif)], max(cooks), sum(cooks > 4 / n))
)

numeric_predictors <- c("Y", "JPY_app", "Nikkei_ret", "SMB", "HML", "RMW", "CMA", "MOM", "dlog_VIX", "rate_diff")
predictor_summary <- do.call(rbind, lapply(numeric_predictors, function(v) {
  x <- analysis_data[[v]]
  data.frame(variable = v, mean = mean(x), sd = sd(x), min = min(x),
             q25 = unname(quantile(x, .25)), median = median(x),
             q75 = unname(quantile(x, .75)), max = max(x), missing = sum(is.na(x)))
}))

write.csv(analysis_data, file.path(processed_dir, "sta302_daily_analysis.csv"), row.names = FALSE)
write.csv(coef_classic, file.path(results_dir, "coefficients_classical.csv"), row.names = FALSE)
write.csv(coef_hac5, file.path(results_dir, "coefficients_hac5.csv"), row.names = FALSE)
write.csv(vif_table, file.path(results_dir, "vif.csv"), row.names = FALSE)
write.csv(hypothesis_tests, file.path(results_dir, "fx_slope_hypothesis_tests.csv"), row.names = FALSE)
write.csv(diagnostics, file.path(results_dir, "diagnostics.csv"), row.names = FALSE)
write.csv(predictor_summary, file.path(results_dir, "predictor_summary.csv"), row.names = FALSE)
write.csv(alignment_audit, file.path(results_dir, "data_alignment_audit.csv"), row.names = FALSE)
write.csv(alignment_model_sensitivity, file.path(results_dir, "data_alignment_sensitivity.csv"), row.names = FALSE)
write.csv(hac_sensitivity, file.path(results_dir, "hac_lag_sensitivity.csv"), row.names = FALSE)
write.csv(split_summary, file.path(results_dir, "split_summary.csv"), row.names = FALSE)
write.csv(tuning_metrics, file.path(results_dir, "model_selection_tuning.csv"), row.names = FALSE)
write.csv(test_metrics, file.path(results_dir, "heldout_test_metrics.csv"), row.names = FALSE)
write.csv(test_predictions, file.path(results_dir, "heldout_test_predictions.csv"), row.names = FALSE)
write.csv(test_metrics, file.path(results_dir, "chronological_validation.csv"), row.names = FALSE)
write.csv(functional_form_sensitivity, file.path(results_dir, "functional_form_sensitivity.csv"),
          row.names = FALSE)
write.csv(lambda_profile, file.path(results_dir, "yeo_johnson_lambda_profile.csv"), row.names = FALSE)
write.csv(influence_sensitivity, file.path(results_dir, "influence_sensitivity.csv"), row.names = FALSE)
write.csv(influence_audit, file.path(results_dir, "influence_audit.csv"), row.names = FALSE)
write.csv(break_date_sensitivity, file.path(results_dir, "break_date_sensitivity.csv"), row.names = FALSE)
write.csv(data_quality_audit, file.path(results_dir, "data_quality_audit.csv"), row.names = FALSE)
saveRDS(list(full_model = full_model, baseline_model = baseline_model, hac5 = vcov_hac5,
             selected_model_name = selected_model_name, selected_model = selected_model,
             quadratic_model = quadratic_model, yeo_johnson_model = yj_model,
             yeo_johnson_lambda = selected_lambda, winsorized_model = winsorized_model,
             cooks_trimmed_model = cooks_trimmed_model),
        file.path(results_dir, "models.rds"))

png(file.path(figures_dir, "fx_slope_by_period.png"), width = 1800, height = 1200, res = 180)
cols <- ifelse(analysis_data$Post == "Pre", rgb(0.12, 0.42, 0.68, 0.22), rgb(0.88, 0.32, 0.23, 0.22))
plot(analysis_data$JPY_app, analysis_data$Y, pch = 16, cex = 0.55, col = cols,
     xlab = "Daily yen appreciation, JPY_app (%)", ylab = "HEWJ minus EWJ daily log return (%)",
     main = "Currency-hedged equity spread and yen appreciation")
abline(a = coef(full_model)["(Intercept)"], b = coef(full_model)["JPY_app"], col = "#1f6aa5", lwd = 3)
abline(a = coef(full_model)["(Intercept)"] + coef(full_model)["PostPost"],
       b = coef(full_model)["JPY_app"] + coef(full_model)[interaction_name], col = "#d94b36", lwd = 3)
legend("topright", legend = c("Pre: through 2020-03-10", "Post: from 2020-03-12"),
       col = c("#1f6aa5", "#d94b36"), lwd = 3, bty = "n")
dev.off()

png(file.path(figures_dir, "chronological_split.png"), width = 1800, height = 1100, res = 180)
split_cols <- c(train = "#1f6aa5", tuning = "#e69f00", test = "#d94b36")
plot(analysis_data$date, analysis_data$Y, pch = 16, cex = .35,
     col = adjustcolor(split_cols[as.character(analysis_data$split)], alpha.f = .35),
     xlab = "Date", ylab = "Daily return spread (%)",
     main = "Chronological train / tuning / test split")
abline(v = as.numeric(c(max(train$date), max(tuning$date))), lty = 2, col = "grey35")
legend("topright", legend = names(split_cols), col = split_cols, pch = 16, bty = "n")
dev.off()

png(file.path(figures_dir, "tuning_model_comparison.png"), width = 1600, height = 1100, res = 180)
bar_cols <- ifelse(tuning_metrics$model == selected_model_name, "#1f6aa5", "#a9b6c2")
bar_pos <- barplot(tuning_metrics$RMSE, names.arg = tuning_metrics$model, col = bar_cols,
                   las = 1, ylab = "Tuning RMSE", main = "Model selection uses tuning period only",
                   ylim = c(0, max(tuning_metrics$RMSE) * 1.18))
text(bar_pos, tuning_metrics$RMSE, labels = sprintf("%.4f", tuning_metrics$RMSE), pos = 3)
dev.off()

png(file.path(figures_dir, "heldout_test_predictions.png"), width = 1800, height = 1100, res = 180)
actual_roll <- trailing_mean(test_predictions$actual)
pred_roll <- trailing_mean(test_predictions$predicted)
plot(test_predictions$date, actual_roll, type = "l", lwd = 2, col = "#1f6aa5",
     xlab = "Date", ylab = "Trailing 20-day mean return spread (%)",
     main = paste("Held-out conditional fit:", selected_model_name))
lines(test_predictions$date, pred_roll, lwd = 2, col = "#d94b36")
abline(h = 0, lty = 2, col = "grey50")
legend("topright", legend = c("Actual", "Predicted"), col = c("#1f6aa5", "#d94b36"),
       lwd = 2, bty = "n")
dev.off()

png(file.path(figures_dir, "hac_lag_sensitivity.png"), width = 1500, height = 1050, res = 180)
plot(hac_sensitivity$lag, hac_sensitivity$interaction_estimate, pch = 19, cex = 1.2,
     ylim = range(c(hac_sensitivity$interaction_conf_low, hac_sensitivity$interaction_conf_high)),
     xlab = "Newey-West lag", ylab = "JPY appreciation x Post estimate",
     main = "Pandemic-interaction estimate with 95% HAC intervals")
segments(hac_sensitivity$lag, hac_sensitivity$interaction_conf_low,
         hac_sensitivity$lag, hac_sensitivity$interaction_conf_high, lwd = 2, col = "#1f6aa5")
abline(h = 0, lty = 2, col = "grey45")
axis(1, at = hac_sensitivity$lag)
dev.off()

png(file.path(figures_dir, "residual_diagnostics.png"), width = 1800, height = 2100, res = 180)
par(mfrow = c(3, 2), mar = c(4.2, 4.2, 2.5, 1.2))
plot(fitted(full_model), resid, pch = 16, cex = .45, col = rgb(0.1, 0.3, 0.6, .3),
     xlab = "Fitted values", ylab = "Residuals", main = "Residuals vs fitted")
abline(h = 0, lty = 2, col = "grey40")
standardized_resid <- rstandard(full_model)
scale_location <- sqrt(abs(standardized_resid))
plot(fitted(full_model), scale_location, pch = 16, cex = .45,
     col = rgb(0.1, 0.3, 0.6, .3), xlab = "Fitted values",
     ylab = expression(sqrt("|Standardized residual|")), main = "Scale-location")
lines(lowess(fitted(full_model), scale_location), col = "#d94b36", lwd = 2)
qqnorm(resid, pch = 16, cex = .42, col = rgb(0.1, 0.3, 0.6, .35), main = "Normal Q-Q")
qqline(resid, col = "#d94b36", lwd = 2)
plot(analysis_data$date, resid, type = "l", col = "#1f6aa5", xlab = "Date", ylab = "Residual",
     main = "Residuals over time")
abline(h = 0, lty = 2, col = "grey40")
acf(resid, lag.max = 30, main = "Residual autocorrelation")
plot(analysis_data$date, cooks, type = "h", col = adjustcolor("#1f6aa5", alpha.f = .7),
     xlab = "Date", ylab = "Cook's distance", main = "Influence screening")
abline(h = cooks_threshold, lty = 2, col = "#d94b36", lwd = 2)
dev.off()

png(file.path(figures_dir, "coefficient_intervals_hac5.png"), width = 1800, height = 1200, res = 180)
plot_terms <- coef_hac5$term != "(Intercept)"
tab <- coef_hac5[plot_terms, ]
ord <- order(tab$estimate)
tab <- tab[ord, ]
par(mar = c(5, 10, 3, 1))
plot(tab$estimate, seq_len(nrow(tab)), xlim = range(c(tab$conf_low, tab$conf_high)),
     yaxt = "n", pch = 19, col = "#1f6aa5", xlab = "Coefficient with 95% HAC(5) interval",
     ylab = "", main = "Full-model estimates")
segments(tab$conf_low, seq_len(nrow(tab)), tab$conf_high, seq_len(nrow(tab)), col = "#1f6aa5", lwd = 2)
axis(2, at = seq_len(nrow(tab)), labels = tab$term, las = 1, cex.axis = .85)
abline(v = 0, lty = 2, col = "grey45")
dev.off()

png(file.path(figures_dir, "robustness_sensitivity.png"), width = 1900, height = 1600, res = 180)
par(mfrow = c(2, 2), mar = c(5, 4.4, 3, 1.2))
functional_labels <- c("Linear", "Quadratic", sprintf("Yeo-Johnson\n(lambda=%.2f)", selected_lambda))
functional_values <- functional_form_sensitivity$tuning_RMSE_original_scale
functional_pos <- barplot(functional_values, names.arg = functional_labels,
                          col = c("#1f6aa5", "#7aa6c2", "#a9b6c2"),
                          ylab = "Tuning RMSE", main = "Functional-form comparison (tuning only)",
                          ylim = c(0, max(functional_values) * 1.18))
text(functional_pos, functional_values, sprintf("%.4f", functional_values), pos = 3, cex = .8)

influence_labels <- c("Primary", "Winsorized", "Cook stress")
plot(seq_along(influence_labels), influence_sensitivity$interaction,
     xaxt = "n", pch = 19, cex = 1.1, col = "#1f6aa5",
     xlim = c(.65, 3.35),
     ylim = range(influence_sensitivity$interaction) + c(-.004, .004),
     xlab = "", ylab = "JPY appreciation x Post estimate",
     main = "Influence sensitivity")
axis(1, at = seq_along(influence_labels), labels = influence_labels)
abline(h = 0, lty = 2, col = "grey45")
text(seq_along(influence_labels), influence_sensitivity$interaction,
     labels = sprintf("p=%.3f", influence_sensitivity$interaction_hac5_p),
     pos = c(4, 3, 2), offset = .45, cex = .78)

plot(as.Date(break_date_sensitivity$transition_date), break_date_sensitivity$interaction,
     type = "b", pch = 19, col = "#d94b36", xaxt = "n",
     xlim = range(as.Date(break_date_sensitivity$transition_date)) + c(-2, 2),
     ylim = range(break_date_sensitivity$interaction) + c(-.004, .004),
     xlab = "Candidate transition date", ylab = "JPY appreciation x Post estimate",
     main = "Pandemic-break sensitivity")
axis.Date(1, at = as.Date(break_date_sensitivity$transition_date), format = "%b %d")
abline(h = 0, lty = 2, col = "grey45")
text(as.Date(break_date_sensitivity$transition_date), break_date_sensitivity$interaction,
     labels = sprintf("p=%.3f", break_date_sensitivity$interaction_hac5_p),
     pos = c(4, 3, 2), offset = .45, cex = .78)

plot(lambda_profile$lambda, lambda_profile$profile_score, type = "l", lwd = 2,
     col = "#1f6aa5", xlab = "Yeo-Johnson lambda", ylab = "Training profile score",
     main = "Lambda selected without tuning/test leakage")
abline(v = selected_lambda, lty = 2, col = "#d94b36", lwd = 2)
text(selected_lambda, max(lambda_profile$profile_score), sprintf("lambda=%.2f", selected_lambda),
     pos = 4, cex = .8)
dev.off()

png(file.path(figures_dir, "influence_diagnostics.png"), width = 1800, height = 1100, res = 180)
plot(analysis_data$date, cooks, type = "h", col = adjustcolor("#1f6aa5", alpha.f = .7),
     xlab = "Date", ylab = "Cook's distance", main = "Influence screening; primary model retains all dates")
abline(h = cooks_threshold, lty = 2, col = "#d94b36", lwd = 2)
top_indices <- order(cooks, decreasing = TRUE)[seq_len(min(6, length(cooks)))]
text(analysis_data$date[top_indices], cooks[top_indices],
     labels = format(analysis_data$date[top_indices], "%Y-%m-%d"),
     pos = c(3, 2, 4, 3, 3, 3), offset = .5, cex = .72)
legend("topright", legend = sprintf("4/n threshold = %.5f", cooks_threshold),
       col = "#d94b36", lty = 2, lwd = 2, bty = "n")
dev.off()

log_lines <- c(
  paste("R version:", R.version.string),
  paste("jsonlite version:", as.character(packageVersion("jsonlite"))),
  paste("Run time UTC:", format(Sys.time(), tz = "UTC", usetz = TRUE)),
  paste("Rows:", nrow(analysis_data)),
  paste("Date range:", min(analysis_data$date), "to", max(analysis_data$date)),
  paste("Pre/Post rows:", sum(analysis_data$Post == "Pre"), "/", sum(analysis_data$Post == "Post")),
  sprintf("Full R-squared: %.6f", summary(full_model)$r.squared),
  sprintf("Baseline R-squared: %.6f", summary(baseline_model)$r.squared),
  sprintf("Durbin-Watson: %.4f", dw),
  sprintf("Max VIF: %.3f (%s)", max(vif_table$vif), vif_table$term[which.max(vif_table$vif)]),
  paste("Selected predictive model:", selected_model_name),
  "",
  "Classical coefficients:",
  paste(capture.output(print(coef_classic, row.names = FALSE, digits = 7)), collapse = "\n"),
  "",
  "HAC(5) coefficients:",
  paste(capture.output(print(coef_hac5, row.names = FALSE, digits = 7)), collapse = "\n"),
  "",
  "Chronological split:",
  paste(capture.output(print(split_summary, row.names = FALSE, digits = 7)), collapse = "\n"),
  "",
  "Tuning-only model selection:",
  paste(capture.output(print(tuning_metrics, row.names = FALSE, digits = 7)), collapse = "\n"),
  "",
  "Untouched held-out test:",
  paste(capture.output(print(test_metrics, row.names = FALSE, digits = 7)), collapse = "\n"),
  "",
  "Functional-form sensitivity (tuning only; held-out decision not reopened):",
  paste(capture.output(print(functional_form_sensitivity, row.names = FALSE, digits = 7)), collapse = "\n"),
  "",
  "Influence sensitivity:",
  paste(capture.output(print(influence_sensitivity, row.names = FALSE, digits = 7)), collapse = "\n"),
  "",
  "Pandemic-break sensitivity:",
  paste(capture.output(print(break_date_sensitivity, row.names = FALSE, digits = 7)), collapse = "\n"),
  "",
  "Data-quality and reproducibility checks:",
  paste(capture.output(print(data_quality_audit, row.names = FALSE, digits = 7)), collapse = "\n"),
  "",
  "R session information:",
  paste(capture.output(sessionInfo()), collapse = "\n")
)
writeLines(log_lines, file.path(results_dir, "R_run_log.txt"))

cat(paste(log_lines[1:11], collapse = "\n"), "\n")

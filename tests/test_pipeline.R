options(stringsAsFactors = FALSE)

args <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args, value = TRUE)
root <- normalizePath(file.path(dirname(sub("^--file=", "", file_arg[1])), ".."), mustWork = TRUE)

read_result <- function(name) read.csv(file.path(root, "results", name), check.names = FALSE)
require_true <- function(condition, message) if (!isTRUE(condition)) stop(message, call. = FALSE)

data <- read.csv(file.path(root, "data", "processed", "sta302_daily_analysis.csv"))
data$date <- as.Date(data$date)
require_true(nrow(data) == 2655L, "Unexpected analysis row count")
require_true(!anyDuplicated(data$date), "Duplicate analysis dates")
require_true(all(diff(data$date) > 0), "Dates are not strictly increasing")
require_true(identical(unique(data$split), c("train", "tuning", "test")), "Split order changed")

splits <- read_result("split_summary.csv")
require_true(sum(splits$rows) == nrow(data), "Split rows do not cover the sample")
require_true(as.Date(splits$end_date[1]) < as.Date(splits$start_date[2]), "Train/tuning overlap")
require_true(as.Date(splits$end_date[2]) < as.Date(splits$start_date[3]), "Tuning/test overlap")

alignment <- read_result("data_alignment_audit.csv")
require_true(all(alignment$final_joint_interval_rows == nrow(data)), "Alignment sample mismatch")
require_true(all(alignment$exact_interval_start_matches_Y >= nrow(data)), "Invalid interval audit")

tuning <- read_result("model_selection_tuning.csv")
test <- read_result("heldout_test_metrics.csv")
selected <- sub("^Selected: ", "", test$model[1])
require_true(selected == tuning$model[which.min(tuning$RMSE)], "Test model was not selected on tuning RMSE")
require_true(test$RMSE[1] < min(test$RMSE[-1]), "Selected model does not beat test benchmarks")

hac <- read_result("coefficients_hac5.csv")
interaction <- hac[hac$term == "JPY_app:PostPost", ]
require_true(nrow(interaction) == 1L && interaction$p_value > 0.05,
             "Primary HAC interaction conclusion changed")
slopes <- read_result("fx_slope_hypothesis_tests.csv")
slopes <- slopes[slopes$inference == "Newey-West HAC(5)", ]
require_true(nrow(slopes) == 2L && all(slopes$p_value < 0.05),
             "Incomplete-hedging conclusion changed")

functional <- read_result("functional_form_sensitivity.csv")
require_true(nrow(functional) == 3L, "Functional-form sensitivity is incomplete")
require_true(all(c("Primary linear response", "Quadratic yen sensitivity", "Yeo-Johnson response") %in%
                   functional$specification), "Functional-form specifications changed")
lambda_profile <- read_result("yeo_johnson_lambda_profile.csv")
require_true(sum(as.logical(lambda_profile$selected)) == 1L, "Yeo-Johnson lambda was not selected uniquely")

influence <- read_result("influence_sensitivity.csv")
require_true(nrow(influence) == 3L, "Influence sensitivity is incomplete")
require_true(influence$interaction_hac5_p[1] > 0.05 && any(influence$interaction_hac5_p[-1] < 0.05),
             "Influence sensitivity no longer documents inferential fragility")
influence_audit <- read_result("influence_audit.csv")
require_true(sum(as.logical(influence_audit$flagged)) == 134L, "Cook's-distance audit changed")

breaks <- read_result("break_date_sensitivity.csv")
require_true(nrow(breaks) == 3L, "Break-date sensitivity is incomplete")
require_true(any(breaks$interaction_hac5_p < 0.05) && any(breaks$interaction_hac5_p > 0.05),
             "Break-date sensitivity no longer documents cutoff dependence")

quality <- read_result("data_quality_audit.csv")
expected_status <- quality$expected == "TRUE" | quality$expected == "2655"
require_true(all(as.logical(quality$status) == expected_status), "Data-quality audit contains a failed check")

csv_manifest <- read.csv(file.path(root, "data", "original_csv", "SHA256SUMS.csv"))
require_true(nrow(csv_manifest) == 7L, "Original-source CSV export is incomplete")

required_figures <- c("chronological_split.png", "fx_slope_by_period.png",
                      "coefficient_intervals_hac5.png", "hac_lag_sensitivity.png",
                      "tuning_model_comparison.png", "heldout_test_predictions.png",
                      "residual_diagnostics.png", "robustness_sensitivity.png",
                      "influence_diagnostics.png")
for (figure in required_figures) {
  target <- file.path(root, "figures", figure)
  require_true(file.exists(target) && file.info(target)$size > 1000, paste("Missing figure", figure))
}

cat("R PIPELINE TESTS PASSED: alignment, chronological split, tuning lock, held-out test, HAC, nonlinear, influence, break-date, CSV-export, and figure checks.\n")

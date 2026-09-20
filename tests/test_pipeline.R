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

required_figures <- c("chronological_split.png", "fx_slope_by_period.png",
                      "coefficient_intervals_hac5.png", "hac_lag_sensitivity.png",
                      "tuning_model_comparison.png", "heldout_test_predictions.png",
                      "residual_diagnostics.png")
for (figure in required_figures) {
  target <- file.path(root, "figures", figure)
  require_true(file.exists(target) && file.info(target)$size > 1000, paste("Missing figure", figure))
}

cat("R PIPELINE TESTS PASSED: alignment, chronological split, tuning lock, held-out test, HAC conclusions, and figures.\n")

# Sensitivity model for every confirmatory comparison (Protocol 11):
#   lmer(D ~ 1 + (1|cell) + (1|variant)), REML, Satterthwaite df, one-sided on the
#   intercept (positive favours the hypothesis).
# Input: the CSV written by refimpl/report.py::mixed_model_table
#   (columns test, pid, cell, variant, D). Pinned: R 4.4.1, lme4 1.1-35, lmerTest 3.1-3.
# Usage: Rscript analysis/mixed_model.R mixed_model_input.csv mixed_model_output.csv
suppressPackageStartupMessages({library(lme4); library(lmerTest)})
args <- commandArgs(trailingOnly = TRUE)
d <- read.csv(args[1], stringsAsFactors = FALSE)
d$cell <- factor(d$cell); d$variant <- factor(d$variant)
out <- do.call(rbind, lapply(split(d, d$test), function(x) {
  m <- lmer(D ~ 1 + (1 | cell) + (1 | variant), data = x, REML = TRUE)
  s <- summary(m)$coefficients
  t <- s[1, "t value"]; df <- s[1, "df"]
  data.frame(test = x$test[1], estimate = s[1, "Estimate"], se = s[1, "Std. Error"],
             df = df, t = t, p_one_sided = pt(t, df, lower.tail = FALSE),
             singular = isSingular(m))
}))
write.csv(out, args[2], row.names = FALSE)

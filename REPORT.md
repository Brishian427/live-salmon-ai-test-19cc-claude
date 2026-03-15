# Live Salmon Test for AI Scientists

## 1. Executive Summary

We conducted the first "live salmon test" for AI scientists — providing three frontier LLMs (GPT-4.1, Claude Sonnet 4.5, Gemini 2.5 Pro) with a dataset generated from a known formula and asking each to analyze the data and write a research paper, repeated 3 times per model. We also tested them on a "dead salmon" null dataset where the target is pure noise.

**Key finding**: AI scientists are conservative and competent at detecting strong linear effects, but **universally fail to detect interaction effects**. All 9 live-salmon papers identified the linear predictors X1 and X3; 67% also found X2. However, **zero out of 9 papers detected the X4×X5 interaction term**, which accounts for ~8% of variance. On the dead salmon data, all 9 papers correctly reported null findings with zero false positives — a striking contrast to the original dead salmon fMRI study.

**Implication**: Current AI scientists operate like competent but methodologically narrow analysts. They reliably apply correlation analysis and linear regression but systematically miss nonlinear structure. The "AI scientific literature" they collectively produce would lead readers to believe the data generating process is purely linear, missing a meaningful component of the true model.

## 2. Goal

**Hypothesis**: Providing AI scientists with a known data generating process ("live salmon") and asking them to analyze it will reveal systematic strengths and limitations of their methodologies.

**Why this matters**: AI scientist systems are being deployed to automate research at scale (~$15/paper). Understanding what they reliably find vs. systematically miss is essential for assessing the trustworthiness of AI-generated research. The original dead salmon fMRI study (Bennett et al., 2009) revealed that neuroimaging pipelines produced false positives on null data; we ask the complementary question — do AI scientists correctly recover true signal, and what do they miss?

**Gap filled**: No prior work has tested AI scientists against a known data generating process. Existing evaluations (Beel et al., 2025; Luo et al., 2025) assess paper quality or identify pitfalls post-hoc, but none provide a controlled ground truth for measuring what AI scientists actually discover.

## 3. Data Construction

### Dataset Description

Two synthetic datasets were generated with the same feature structure (20 features, 1000 samples):

| Dataset | Target Variable | Purpose |
|---------|----------------|---------|
| **Live Salmon** | Y = 2·X1 + 0.5·X2 − 1.5·X3 + 0.8·(X4·X5) + N(0,1) | Known DGP with linear + interaction terms |
| **Dead Salmon** | Y = N(0,1) (pure noise) | Null control — any finding is a false positive |

### Feature Structure

| Features | Type | Description |
|----------|------|-------------|
| X1–X5 | **True predictors** | X1,X2,X3 have linear effects; X4,X5 interact multiplicatively |
| X6–X15 | **Pure noise** | i.i.d. N(0,1), independent of Y |
| X16–X20 | **Correlated proxies** | X16≈0.7·X1, X17≈0.6·X2, X18≈0.5·X3, X19≈0.8·X4, X20≈0.65·X5 |

### Data Quality
- 1000 samples, no missing values, no outliers by design
- All features approximately N(0,1)
- Seed: 42 (fully reproducible via `datasets/generate_live_salmon_data.py`)

### Example Samples (first 3 rows, key features)

| X1 | X2 | X3 | X4 | X5 | Y |
|----|----|----|----|----|---|
| 0.30 | −0.06 | −0.45 | 1.25 | 0.25 | −0.15 |
| −1.04 | −0.73 | −0.67 | 0.69 | 0.90 | −0.06 |
| 0.75 | −0.41 | 0.43 | 1.97 | 0.27 | 1.01 |

## 4. Experiment Description

### Methodology

#### High-Level Approach
We prompted three frontier LLMs via OpenRouter API to act as senior data scientists. Each received a statistical summary of the dataset (summary statistics, correlation matrix, pairwise correlations with Y, inter-feature correlations, and 15 sample rows) and was asked to write a short research paper identifying the data generating process.

Each model was run 3 times with temperature=0.7 on each dataset, producing 18 total papers.

#### Why This Method?
Rather than running full AI scientist pipelines (e.g., Sakana's AI Scientist), we test the analytical reasoning core: given data, can the LLM identify the true relationships? This isolates the analytical capability from code execution, which prior work shows is a separate bottleneck (Zhu et al., 2025).

### Models Tested

| Model | Provider | Via |
|-------|----------|-----|
| GPT-4.1 | OpenAI | OpenRouter |
| Claude Sonnet 4.5 | Anthropic | OpenRouter |
| Gemini 2.5 Pro | Google | OpenRouter |

### Evaluation Pipeline
1. Each paper was processed by GPT-4.1 (temperature=0) to extract structured claims (features identified, coefficients estimated, interaction terms, methods used)
2. Claims were scored against the known ground truth
3. Results aggregated across models and runs

### Baseline: Standard Statistical Analysis
For comparison, we ran standard statistical methods on the same data:

| Method | R² (CV) | Features Selected | X4×X5 Detected? |
|--------|---------|-------------------|-----------------|
| OLS Linear Regression | 0.77 | All (no selection) | N/A |
| LassoCV | — | X1, X2, X3, X4 | No |
| OLS + X4×X5 interaction | 0.85 | X1, X2, X3, X4×X5 | **Yes** (coef=0.80) |
| Random Forest | 0.73 | X1, X3, X2, X16, X5... | Implicitly |

The interaction term X4×X5 adds R²=0.083 when included — a meaningful contribution that standard OLS without interaction terms misses.

### Hyperparameters

| Parameter | Value |
|-----------|-------|
| Temperature | 0.7 |
| Max tokens | 4096 |
| Runs per model per dataset | 3 |
| Evaluation model | GPT-4.1 (temp=0) |

## 5. Result Analysis

### Key Finding 1: Strong Linear Effects Reliably Detected

All 9 live-salmon papers identified X1 (100%) and X3 (100%) as significant predictors. X2 was identified by 67% (6/9) of papers — its weaker coefficient (0.5 vs. 2.0 and −1.5) made it harder to detect.

### Key Finding 2: Universal Failure on Interaction Effects

**Zero out of 9 papers detected the X4×X5 interaction term.** This is the most striking result. The interaction contributes ~8% of total variance (R² gain = 0.083) and has a true coefficient of 0.8 — comparable in magnitude to X2's coefficient of 0.5, which was detected by most papers.

The failure is systematic: no model, across any run, identified this interaction. The methods used by all models (correlation analysis, linear regression) are inherently limited to detecting marginal/linear effects. None attempted systematic interaction screening, polynomial features, or tree-based methods that could reveal the X4×X5 term.

### Key Finding 3: Dead Salmon Test — Perfect Pass

All 9 dead-salmon papers correctly reported null findings:
- **0 false positives** across all models and runs
- All papers explicitly stated that no features had significant relationships with Y
- All applied or mentioned multiple comparisons corrections (Bonferroni)

This is the inverse of Bennett et al.'s (2009) dead salmon fMRI result, where standard analysis produced false positives. LLM-based AI scientists are methodologically conservative — they do not hallucinate statistical significance.

### Key Finding 4: Correlated Feature Confusion

In 3 out of 9 live-salmon papers (33%), correlated proxy features (X16–X20) were listed as significant alongside or instead of true causal features. This happened when models noted the correlations but failed to distinguish direct vs. proxy predictors:

| Model | Run | Correlated features falsely included |
|-------|-----|--------------------------------------|
| GPT-4.1 | 3 | X17 |
| Claude Sonnet 4.5 | 3 | X16, X17, X18 |
| Gemini 2.5 Pro | 2 | X16, X17, X18 |

### Key Finding 5: Coefficient Estimation Accuracy

When models estimated coefficients, they were generally close to ground truth:

| Feature | True Coef | Mean Estimate | Mean |Error| |
|---------|-----------|---------------|----------------|
| X1 | 2.0 | 1.72 | 0.28 |
| X2 | 0.5 | 0.34 | 0.16 |
| X3 | −1.5 | −1.38 | 0.12 |

The systematic underestimation likely reflects that models estimated coefficients from univariate correlations (which are attenuated by noise and multicollinearity) rather than from multivariate regression.

### Key Finding 6: Methodological Homogeneity

All 9 papers used essentially the same analytical pipeline:
1. Correlation analysis (9/9)
2. Multiple comparisons correction (9/9)
3. Multicollinearity assessment (9/9)
4. Linear regression or approximation thereof (8/9)

No paper attempted:
- Random forests or gradient boosting
- Interaction term screening
- Polynomial feature expansion
- Partial dependence plots
- Causal inference methods

### Aggregate Results Table

| Metric | Rate |
|--------|------|
| X1 detected (coef=2.0) | 100% (9/9) |
| X3 detected (coef=−1.5) | 100% (9/9) |
| X2 detected (coef=0.5) | 67% (6/9) |
| X4 or X5 detected (interaction participants) | 0% (0/9) |
| X4×X5 interaction detected | **0% (0/9)** |
| Noise features falsely included (X6–X15) | 0% (0/9) |
| Correlated features confused as causal | 33% (3/9) |
| Dead salmon false positives | 0% (0/9) |
| Dead salmon null finding correctly reported | 100% (9/9) |
| Multiple comparisons correction mentioned | 100% (18/18) |

### Visualizations

All plots are saved in `results/plots/`:
- `aggregate_metrics.png` — Overview of all metrics
- `feature_detection_heatmap.png` — Which features each paper identified
- `detection_rates_by_model.png` — Per-model detection rates for each true feature
- `coefficient_accuracy.png` — Estimated vs. true coefficients
- `methods_used.png` — Distribution of statistical methods applied

### Hypothesis Testing Results

| Hypothesis | Result | Evidence |
|------------|--------|----------|
| H1: AI scientists identify X1, X2, X3 | **Partially supported** | X1,X3: 100%; X2: 67% |
| H2: AI scientists miss X4×X5 interaction | **Strongly supported** | 0/9 detected |
| H3: Correlated features confused with causal | **Supported** | 33% confusion rate |
| H4: False positives on dead salmon data | **Refuted** | 0/9 false positives |
| H5: Multiple comparisons not consistently applied | **Refuted** | 100% mentioned/applied |

### Surprises

1. **H4 refuted**: We expected at least some false positives on dead salmon data (by analogy to the fMRI case). Instead, all models correctly reported null findings. LLMs are more conservative than traditional statistical pipelines.

2. **H5 refuted**: We expected inconsistent multiple comparisons handling. Instead, all 18 papers mentioned corrections. This may reflect that Bonferroni correction is well-represented in training data and is a "textbook" step that LLMs reliably reproduce.

3. **100% interaction failure**: We expected some models to attempt interaction screening. None did. This reveals a deep methodological limitation — LLMs default to the most standard analytical workflow (correlation → regression) and do not creatively explore model space.

### Error Analysis

The core failure mode is **methodological narrowness**: all AI scientists apply the same limited toolkit (correlation + linear regression) regardless of whether the data contains nonlinear structure. The R² gap between linear-only models (0.77) and models with the interaction term (0.85) is detectable with standard methods, but no AI scientist attempted the diagnostic steps (residual analysis, partial dependence plots, interaction screening) that would reveal it.

### Limitations

1. **Data delivery format**: Models received summary statistics rather than raw data. With raw data and code execution capability (as in Sakana's AI Scientist), they might attempt more diverse analyses.
2. **Prompt design**: Our prompt asked for analysis but did not specifically prompt for interaction effects. A more directive prompt might change results.
3. **Single prompt paradigm**: Real AI scientist systems iterate (generate ideas → run code → revise). Our single-shot paradigm may underestimate capability.
4. **Evaluation by LLM**: Claims were extracted by GPT-4.1, which may have errors in parsing.
5. **Limited model diversity**: Three models from three providers, all frontier-class. Smaller or specialized models might behave differently.
6. **Sample size**: 3 runs per condition provides limited statistical power for cross-model comparisons.

## 6. Conclusions

### Summary
The Live Salmon Test reveals that frontier AI scientists are **competent but methodologically narrow**. They reliably detect strong linear relationships and correctly identify null data, but universally fail to detect interaction effects — a systematic blind spot that would lead the collective "AI scientific literature" to mischaracterize the data generating process as purely linear.

### Implications

**For AI scientist developers**: The bottleneck is not statistical conservatism (which is appropriate) but analytical creativity. Future AI scientists need to systematically explore model space beyond linear effects — testing interactions, nonlinearities, and applying model diagnostics.

**For consumers of AI-generated research**: AI scientist papers should be treated as a first-pass linear analysis. Nonlinear structure, interaction effects, and causal relationships may be systematically underreported.

**For the field**: The "live salmon test" methodology — providing known-DGP data and evaluating recovery — is a valuable complement to existing benchmarks. It reveals what AI scientists miss, not just what they get wrong.

### Confidence in Findings
**High confidence** in the core finding (interaction detection failure) — it is 0/9 across three different models. The dead salmon null-finding result is also robust (9/9). The correlated feature confusion rate (33%) is based on smaller numbers and may vary with different prompt designs.

## 7. Next Steps

### Immediate Follow-ups
1. **Give AI scientists code execution**: Use Sakana's AI Scientist framework with this dataset to test whether code execution enables interaction detection
2. **Prompt engineering**: Test whether explicitly mentioning "check for interactions" changes behavior
3. **Vary difficulty**: Adjust signal-to-noise ratio and interaction strength to find detection thresholds

### Alternative Approaches
- Test with specialized statistical agents (e.g., Data Interpreter, BLADE agents)
- Test with multi-turn conversational analysis rather than single-shot
- Test with different data modalities (time series, images) where "standard analysis" differs

### Open Questions
1. Is the interaction detection failure specific to tabular data, or do AI scientists systematically miss nonlinear structure across domains?
2. Would fine-tuning on statistical methodology papers improve interaction detection?
3. At what effect size does interaction detection become possible for AI scientists?

## References

1. Bennett, C.M. et al. (2009). Neural Correlates of Interspecies Perspective Taking in the Post-Mortem Atlantic Salmon. *JSUR*.
2. Méloux, M. et al. (2025). The Dead Salmons of AI Interpretability. *arXiv:2512.18792*.
3. Lu, C. et al. (2024). The AI Scientist: Towards Fully Automated Open-Ended Scientific Discovery. *arXiv:2408.06292*.
4. Luo, Z. et al. (2025). The More You Automate, the Less You See. *arXiv:2509.08713*.
5. Beel, J. et al. (2025). Evaluating Sakana's AI Scientist. *arXiv:2502.14297*.
6. Zhu, M. et al. (2025). AI Scientists Fail Without Strong Implementation Capability. *arXiv:2506.01372*.
7. Eklund, A. et al. (2016). Cluster Failure: Why fMRI Inferences Have Inflated False-Positive Rates. *PNAS*.

## Appendix: File Structure

```
results/
├── papers/              # 18 AI-generated papers (JSON)
├── evaluations/         # 18 structured evaluations (JSON)
├── plots/               # Visualization PNGs
├── all_papers.json      # Combined paper data
├── all_evaluations.json # Combined evaluation data
├── summary_table.csv    # Tabular summary of all results
├── baseline_live_salmon.json  # Standard statistical baseline
└── baseline_dead_salmon.json  # Standard statistical baseline
```

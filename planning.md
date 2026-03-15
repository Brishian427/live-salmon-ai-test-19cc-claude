# Live Salmon Test for AI Scientists — Research Plan

## Motivation & Novelty Assessment

### Why This Research Matters
The original "dead salmon" fMRI study (Bennett et al., 2009) demonstrated that standard neuroimaging pipelines could find "significant" brain activity in a dead fish — a powerful illustration of multiple comparisons problems. Now that AI systems are being deployed as autonomous scientists (Lu et al., 2024; Schmidgall et al., 2024), we face a parallel question: **when we give AI scientists data to analyze, do they recover genuine patterns or produce spurious findings?** This matters because AI-generated research is scaling rapidly ($6-15 per paper), and understanding its reliability is critical for scientific integrity.

### Gap in Existing Work
- Méloux et al. (2025) extended the dead salmon concept to AI interpretability tools but did not test AI *scientists* (end-to-end research systems).
- Luo et al. (2025) identified pitfall categories but used post-hoc auditing, not a controlled known-DGP design.
- Beel et al. (2025) evaluated AI Scientist quality but on open-ended tasks with no ground truth.
- **No study has given multiple AI scientists a dataset with a known data generating process and systematically evaluated whether they recover the true model.**

### Our Novel Contribution
We conduct the first "live salmon test" for AI scientists: we provide real LLMs acting as data scientists with (a) a dataset generated from a known formula (Y = 2X1 + 0.5X2 - 1.5X3 + 0.8X4X5 + noise) and (b) a null/dead salmon dataset (Y = pure noise), and ask each to analyze the data and write a research paper. We then evaluate:
1. Whether they recover the true features and functional form
2. Whether they find spurious patterns in null data
3. What the collective "literature" of AI-generated papers reveals about AI scientist methodology

### Experiment Justification
- **Experiment 1 (Live Salmon)**: Tests whether AI scientists can correctly identify the true DGP, including linear terms, interaction effects, and the distinction between causal vs. correlated features.
- **Experiment 2 (Dead Salmon)**: Control condition — any "significant" findings are false positives, directly measuring the false discovery rate of AI scientists.
- **Experiment 3 (Cross-model comparison)**: Using multiple LLMs reveals whether failure modes are model-specific or systematic across the field.
- **Experiment 4 (Collective analysis)**: Synthesizing all papers reveals what the "AI scientific literature" collectively gets right and wrong.

## Research Question
When given a dataset with a known data generating process, do AI scientists (LLMs prompted to act as data scientists and write papers) correctly recover the true model? And when given null data, do they correctly find nothing?

## Hypothesis Decomposition
1. **H1**: AI scientists will identify X1, X2, X3 as significant linear predictors in the live salmon data.
2. **H2**: AI scientists will struggle to identify the X4*X5 interaction term (non-linearity is harder to detect).
3. **H3**: AI scientists will confuse correlated features (X16-X20) with causal features (X1-X5) at least some of the time.
4. **H4**: AI scientists will report at least some "significant" findings on the dead salmon (null) data — false positives.
5. **H5**: AI scientists will not consistently apply multiple comparisons corrections.

## Proposed Methodology

### Approach
Use real LLM APIs (via OpenRouter) to have multiple models act as AI data scientists. Each model receives the dataset (as CSV content or summary statistics) and a prompt asking it to analyze the data and produce a short research paper. We run this on both the live and dead salmon datasets, then systematically evaluate the outputs against ground truth.

### Models to Test
- GPT-4.1 (OpenAI via OpenRouter)
- Claude Sonnet 4.5 (Anthropic via OpenRouter)
- Gemini 2.5 Pro (Google via OpenRouter)

Each model runs 3 independent analyses per dataset (live + dead) = 18 total papers.

### Experimental Steps
1. **Environment setup**: Install dependencies (openai/httpx for API calls, pandas, numpy, matplotlib)
2. **Prompt engineering**: Design a standardized prompt that gives the AI scientist the data and asks for analysis + paper
3. **Data delivery**: Provide summary statistics + a sample of the data (full CSV is too large for context) along with key statistical tests
4. **Run live salmon experiments**: 3 models × 3 runs = 9 papers
5. **Run dead salmon experiments**: 3 models × 3 runs = 9 papers
6. **Parse and evaluate papers**: Extract claimed features, coefficients, methods used, statistical tests, corrections applied
7. **Score against ground truth**: True positive rate, false positive rate, interaction detection, coefficient accuracy
8. **Synthesize collective findings**: What does the AI scientific literature say?

### Baselines
- **Ground truth**: The known DGP (Y = 2X1 + 0.5X2 - 1.5X3 + 0.8X4X5 + noise)
- **Naive OLS regression**: A simple linear regression as the "competent human" baseline
- **Random feature selection**: Expected false positive rate under random guessing

### Evaluation Metrics
1. **True feature identification rate**: Fraction of {X1,X2,X3,X4,X5} correctly identified as significant
2. **False feature identification rate**: Fraction of {X6-X15} incorrectly reported as significant
3. **Correlated feature confusion rate**: Fraction of {X16-X20} reported as causal
4. **Interaction detection**: Binary — did the paper identify the X4*X5 interaction?
5. **Coefficient accuracy**: For linear terms, how close are reported coefficients to truth?
6. **Dead salmon false positive rate**: Any features reported as significant in the null dataset
7. **Multiple comparisons correction**: Did the paper mention/apply correction?
8. **Paper quality**: Qualitative assessment of methodology, limitations, conclusions

### Statistical Analysis Plan
- Fisher's exact test for comparing detection rates across models
- Descriptive statistics for coefficient accuracy
- Qualitative coding of paper content

## Expected Outcomes
- AI scientists will find the strong linear effects (X1, X3) but may miss the weaker ones (X2)
- The interaction term (X4*X5) will be missed by most
- Some models will report spurious findings on dead salmon data
- Correlated features (X16-X20) will be confused with causal features frequently

## Timeline and Milestones
1. Planning: 15 min (this document)
2. Environment + code: 30 min
3. Run experiments: 30-45 min (API calls)
4. Analysis: 30 min
5. Documentation: 30 min

## Potential Challenges
- API rate limits or failures → retry logic, cache responses
- Context window limits → provide data summaries rather than full CSV
- Models refusing to write papers → adjust prompt framing
- Cost → keep runs limited (18 papers total)

## Success Criteria
- Successfully obtain papers from at least 2 different models on both datasets
- Quantitative evaluation of true/false positive rates
- Clear comparison across models
- Meaningful insights about AI scientist methodology

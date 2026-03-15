# Live Salmon Test for AI Scientists

The original "dead salmon" fMRI study showed that neuroimaging pipelines find "significant" brain activity in a dead fish. We flip this: give AI scientists a dataset with a **known** data generating process ("live salmon") and see what they find. Then have them write papers and examine what the collective AI scientific literature reveals.

## Key Findings

- **Strong linear effects detected reliably**: X1 (100%), X3 (100%), X2 (67%) correctly identified as significant across 9 papers from 3 frontier LLMs
- **Interaction effects universally missed**: 0/9 papers detected the X4*X5 interaction term (true coefficient = 0.8, R^2 contribution = 8%)
- **Dead salmon test passed perfectly**: 0/9 papers reported false positives on null data — AI scientists are more conservative than traditional statistical pipelines
- **Methodological homogeneity**: All 9 papers used the same analytical approach (correlation then linear regression), none attempted interaction screening or nonlinear methods
- **Correlated feature confusion**: 33% of papers incorrectly included correlated proxy features as causal

## The "AI Scientific Literature"

If you read only the 9 AI-generated papers, you would conclude:
> "Y is a linear function of X1, X2, and X3. No other features are relevant."

The truth is:
> Y = 2*X1 + 0.5*X2 - 1.5*X3 + **0.8*(X4*X5)** + noise

The interaction term — a meaningful 8% of variance — is completely absent from the AI scientific literature.

## Reproduce

```bash
# Set up environment
uv venv && source .venv/bin/activate
uv add numpy pandas matplotlib seaborn scikit-learn httpx

# Run baseline analysis
python src/baseline_analysis.py

# Run AI scientist experiments (requires OPENROUTER_KEY)
export OPENROUTER_KEY=your_key
python src/run_ai_scientists.py

# Evaluate papers against ground truth
python src/evaluate_papers.py

# Generate visualizations
python src/create_visualizations.py
```

## File Structure

```
├── REPORT.md                  # Full research report
├── planning.md                # Research plan
├── datasets/
│   ├── live_salmon_data.csv   # Known DGP dataset (1000x21)
│   ├── dead_salmon_data.csv   # Null/control dataset
│   ├── ground_truth.json      # True DGP specification
│   └── generate_live_salmon_data.py
├── src/
│   ├── prepare_data_summary.py    # Data summary for LLM context
│   ├── run_ai_scientists.py       # Run LLMs as data scientists
│   ├── evaluate_papers.py         # Score papers vs ground truth
│   ├── baseline_analysis.py       # Standard statistical baseline
│   └── create_visualizations.py   # Generate plots
├── results/
│   ├── papers/                # 18 AI-generated papers
│   ├── evaluations/           # Structured evaluations
│   ├── plots/                 # Visualizations
│   └── summary_table.csv     # Tabular results
└── papers/                    # Reference literature (PDFs)
```

See [REPORT.md](REPORT.md) for full details.

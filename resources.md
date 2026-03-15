# Resources Catalog

## Summary

This document catalogs all resources gathered for the "Live Salmon Test for AI Scientists" research project. The project evaluates AI scientist systems by providing them with data generated from a known process ("live salmon") and assessing whether they correctly recover the generating process or produce spurious findings.

## Papers

Total papers downloaded: 18

| # | Title | Authors | Year | File | Key Info |
|---|-------|---------|------|------|----------|
| 1 | Dead Salmon fMRI | Bennett et al. | 2009 | papers/bennett_2009_dead_salmon_fmri.pdf | Original dead salmon study |
| 2 | Dead Salmons of AI Interpretability | Méloux et al. | 2025 | papers/meloux_2025_dead_salmons_ai_interpretability.pdf | Extends concept to AI |
| 3 | The AI Scientist | Lu et al. | 2024 | papers/lu_2024_ai_scientist.pdf | Primary AI scientist system |
| 4 | Hidden Pitfalls of AI Scientists | Luo et al. | 2025 | papers/fang_2025_more_automate_less_see.pdf | 4 failure modes identified |
| 5 | Evaluating Sakana's AI Scientist | Beel et al. | 2025 | papers/fournier_2025_evaluating_ai_scientist.pdf | Independent evaluation |
| 6 | AI Scientists Fail | Zhu et al. | 2025 | papers/huang_2025_ai_scientists_fail.pdf | Implementation gap analysis |
| 7 | PaperBench | Starace et al. | 2025 | papers/starace_2025_paperbench.pdf | AI replication benchmark |
| 8 | BLADE | Gu et al. | 2024 | papers/gu_2024_blade.pdf | Data-driven science benchmark |
| 9 | ScienceAgentBench | Chen et al. | 2024 | papers/chen_2024_scienceagentbench.pdf | Scientific agent benchmark |
| 10 | Can LLMs Generate Novel Ideas | Si et al. | 2024 | papers/si_2024_llm_novel_ideas.pdf | 100+ researcher study |
| 11 | CycleResearcher | Weng et al. | 2024 | papers/weng_2024_cycleresearcher.pdf | Iterative research automation |
| 12 | Autonomous LLM-driven Research | Yamada et al. | 2024 | papers/yamada_2024_autonomous_llm_research.pdf | Autonomous paper generation |
| 13 | Agent Laboratory | Schmidgall et al. | 2024 | papers/schmidgall_2024_agent_laboratory.pdf | LLM research assistant |
| 14 | Cluster Failure fMRI | Eklund et al. | 2016 | papers/eklund_2016_cluster_failure_fmri.pdf | False positive inflation |
| 15 | Multiple Testing Procedures | Emmert-Streib et al. | 2019 | papers/emmert_2019_multiple_testing.pdf | Statistical methodology |
| 16 | MLR-Copilot | - | 2024 | papers/mlr_copilot_2024.pdf | ML research automation |
| 17 | DeepResearch Bench | - | 2025 | papers/deepresearch_bench_2025.pdf | Research agent benchmark |
| 18 | Survey of AI Scientists | - | 2025 | papers/survey_ai_scientists_2025.pdf | Comprehensive survey |

See papers/README.md for detailed descriptions.

## Datasets

Total datasets generated: 2

| Name | Source | Size | Task | Location | Notes |
|------|--------|------|------|----------|-------|
| Live Salmon Data | Custom synthetic | 1000 samples, 20 features | Regression (known DGP) | datasets/live_salmon_data.csv | Y = 2*X1 + 0.5*X2 - 1.5*X3 + 0.8*(X4*X5) + noise |
| Dead Salmon Data | Custom synthetic | 1000 samples, 20 features | Null condition | datasets/dead_salmon_data.csv | Y = pure random noise |

See datasets/README.md for detailed descriptions and regeneration instructions.

## Code Repositories

Total repositories cloned: 2

| Name | URL | Purpose | Location | Notes |
|------|-----|---------|----------|-------|
| AI-Scientist | github.com/SakanaAI/AI-Scientist | Primary AI scientist system | code/AI-Scientist/ | End-to-end research automation |
| AIScientistPitfalls | github.com/niharshah/AIScientistPitfalls | Pitfall detection framework | code/AIScientistPitfalls/ | Evaluation methodology |

See code/README.md for detailed descriptions.

## Resource Gathering Notes

### Search Strategy
1. Used paper-finder service with three targeted queries (AI scientist evaluation, dead salmon fMRI, LLM research agents) in diligent mode
2. Semantic Scholar API for metadata and download URLs
3. arXiv API for finding correct paper IDs
4. Direct PDF downloads from arXiv

### Selection Criteria
- Papers directly related to: (a) dead salmon / known-process testing, (b) AI scientist systems, (c) evaluation/critique of AI scientists, (d) statistical testing methodology
- Prioritized papers with relevance score >= 2 from paper-finder
- Focused on 2023-2025 for AI scientist systems; included classic 2009/2016 papers for statistical foundations

### Challenges Encountered
- Bennett 2009 dead salmon paper not on arXiv (poster format); found on prefrontal.org
- Some arXiv IDs from Semantic Scholar were incorrect (required verification via arXiv API)
- Semantic Scholar API rate limiting (429 errors) required retry logic

### Gaps and Workarounds
- No existing "live salmon" benchmark exists — created custom synthetic datasets
- BLADE benchmark datasets could serve as supplementary test data but were not downloaded (available via HuggingFace)

## Recommendations for Experiment Design

### 1. Primary Dataset
**Live Salmon Synthetic Data** — Custom-generated dataset with known DGP: Y = 2*X1 + 0.5*X2 - 1.5*X3 + 0.8*(X4*X5) + N(0,1). Features include 5 truly predictive, 10 noise/distractors, and 5 correlated proxies. The known ground truth enables precise evaluation of whether AI scientists correctly identify the true model.

### 2. Control Dataset
**Dead Salmon Null Data** — Same feature structure but Y is independent random noise. AI scientists should find NO significant relationships. Any reported findings are false positives.

### 3. Baseline Methods
- **The AI Scientist** (Sakana AI) — Create a custom experiment template with our datasets
- **Agent Laboratory** — Run with our dataset as the research task
- **Human analysis** — Expert data scientist baseline for comparison

### 4. Evaluation Metrics
1. **True feature identification**: Does the AI correctly identify X1-X5 as predictive?
2. **False feature identification**: Does it report X6-X15 (noise) as significant?
3. **Interaction detection**: Does it discover the X4*X5 interaction term?
4. **Non-linearity detection**: Does it capture the non-linear relationships?
5. **Multiple comparisons**: Does it apply proper corrections?
6. **Dead salmon control**: Does it correctly find nothing in the null dataset?
7. **Paper quality**: Are claims supported by evidence? Are limitations acknowledged?

### 5. Code to Adapt/Reuse
- **AI-Scientist template system**: Adapt to create a "live salmon" experiment template
- **AIScientistPitfalls detection**: Use pitfall detection framework on generated papers
- **Dataset generation script**: Parameterizable for varying difficulty levels

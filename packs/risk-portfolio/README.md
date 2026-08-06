# Risk & Portfolio

Value at Risk with real backtests, portfolio construction beyond Markowitz, factor attribution, credit risk and the copulas that tie the tails together.

5 personas, one per public repository. The system prompt of each describes what that repository actually implements — read from the source and checked by a second reader, per this project's rule against inventing facts.

| Persona | Repository | What it covers |
|---|---|---|
| **Value at Risk** | [`var-lab`](https://github.com/sauloduttra/var-lab) | Computes VaR three ways (historical, parametric, Monte Carlo) plus Expected Shortfall two ways and backtests the result with Kupiec POF and Christoffersen independence. |
| **Allocation** | [`port-lab`](https://github.com/sauloduttra/port-lab) | Turns expected returns and a covariance matrix into portfolio weights via Markowitz, Black-Litterman, Risk Parity, or HRP. |
| **Factor Models** | [`factor-lab`](https://github.com/sauloduttra/factor-lab) | Builds cross-sectional factor models, Fama-MacBeth premia, pure-factor portfolios, and Euler risk attribution from raw matrix algebra. |
| **Credit Risk** | [`credit-lab`](https://github.com/sauloduttra/credit-lab) | Prices default risk end to end: Merton structural model, hazard curves, CDS legs and bootstrap, and defaultable bonds. |
| **Copulas** | [`copula-lab`](https://github.com/sauloduttra/copula-lab) | Models dependence separately from margins: five bivariate copula families with exact samplers, tail-dependence coefficients, and tau-inversion or MLE fitting. |

## Importing

Import the **team** or the individual **personas**, never both — the team snapshot embeds every member in full, and importing it after the personas creates duplicates.

Built by [Saulo Duttra](https://github.com/sauloduttra).

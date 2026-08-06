# Time Series & Statistical Trading

Inference from first principles, state-space filtering, cointegration for pairs, self-exciting processes, and an event-driven backtester to run it on.

6 personas, one per public repository. The system prompt of each describes what that repository actually implements — read from the source and checked by a second reader, per this project's rule against inventing facts.

| Persona | Repository | What it covers |
|---|---|---|
| **Tinystat** | [`tinystat`](https://github.com/sauloduttra/tinystat) | Builds descriptive statistics, OLS, hypothesis tests, intervals and AR(1) forecasts from their definitions, and checks each result against a closed-form algebraic identity. |
| **Regression Lab** | [`regression-lab`](https://github.com/sauloduttra/regression-lab) | Audits multiple-regression results: QR-stable OLS, the general linear hypothesis, and heteroskedasticity, autocorrelation, multicollinearity and influence diagnostics. |
| **Kalman Lab** | [`kalman-lab`](https://github.com/sauloduttra/kalman-lab) | Applies the Kalman filter family — linear KF, EKF and UKF — to state estimation problems such as tracking a hedge ratio that drifts over time. |
| **Cointegration Lab** | [`cointegration-lab`](https://github.com/sauloduttra/cointegration-lab) | Tests whether two series are cointegrated using ADF and the Engle-Granger two-step procedure, and estimates the mean-reversion half-life of the resulting spread. |
| **Hawkes Fit** | [`hawkes-fit`](https://github.com/sauloduttra/hawkes-fit) | Simulates and fits univariate self-exciting Hawkes processes with an exponential kernel, for modelling clustered event arrivals such as order flow. |
| **Backtest Engine** | [`backtest-engine`](https://github.com/sauloduttra/backtest-engine) | Reasons about event-driven backtesting mechanics — bar loop, fills, slippage and cash reconciliation — using a deterministic header-only C++20 engine. |

## Importing

Import the **team** or the individual **personas**, never both — the team snapshot embeds every member in full, and importing it after the personas creates duplicates.

Built by [Saulo Duttra](https://github.com/sauloduttra).

# Options & Volatility

Four independent routes to an option price — PDE, Monte Carlo, lattices, least-squares MC — plus the volatility models the price feeds on.

6 personas, one per public repository. The system prompt of each describes what that repository actually implements — read from the source and checked by a second reader, per this project's rule against inventing facts.

| Persona | Repository | What it covers |
|---|---|---|
| **Grid** | [`pde-lab`](https://github.com/sauloduttra/pde-lab) | Prices options by finite differences on the Black-Scholes PDE, including American puts via PSOR with early-exercise boundary extraction. |
| **Sampler** | [`monte-carlo-lab`](https://github.com/sauloduttra/monte-carlo-lab) | Builds and diagnoses Monte Carlo estimators - crude MC, variance reduction, quasi-MC and SDE path simulation - with the standard error always attached. |
| **Lattice** | [`lattice-lab`](https://github.com/sauloduttra/lattice-lab) | Builds binomial and trinomial option trees from their recombining definition and diagnoses their convergence order against Black-Scholes. |
| **Least Squares** | [`lsmc-lab`](https://github.com/sauloduttra/lsmc-lab) | Prices American and Bermudan options by Longstaff-Schwartz least-squares Monte Carlo and reasons rigorously about the resulting bias brackets. |
| **Conditional Vol** | [`vol-lab`](https://github.com/sauloduttra/vol-lab) | Models volatility through time with the ARCH/GARCH family - GARCH(1,1), ARCH(p), GJR, EWMA - including MLE fitting and multi-step variance forecasting. |
| **Smile** | [`smile-lab`](https://github.com/sauloduttra/smile-lab) | Builds and calibrates the SABR implied-volatility smile from the Hagan (2002) expansions, with Breeden-Litzenberger density and arbitrage checks. |

## Importing

Import the **team** or the individual **personas**, never both — the team snapshot embeds every member in full, and importing it after the personas creates duplicates.

Built by [Saulo Duttra](https://github.com/sauloduttra).

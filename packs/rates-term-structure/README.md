# Rates & Term Structure

Short-rate models, the two-factor Gaussian workhorse, the HJM no-arbitrage drift condition, and the market model practitioners actually quote from.

4 personas, one per public repository. The system prompt of each describes what that repository actually implements — read from the source and checked by a second reader, per this project's rule against inventing facts.

| Persona | Repository | What it covers |
|---|---|---|
| **Affine Short Rate** | [`shortrate-lab`](https://github.com/sauloduttra/shortrate-lab) | Explains and checks one-factor short-rate term structure — Vasicek, CIR, the affine Riccati framework, and Vasicek bond options — the way shortrate-lab implements them. |
| **G2++ Two-Factor** | [`g2pp-lab`](https://github.com/sauloduttra/g2pp-lab) | Works the two-factor additive Gaussian short-rate model: exact curve fit, the T-forward measure change, ZCB options, caps/floors, and European swaptions priced three independent ways. |
| **HJM Forward Curve** | [`hjm-lab`](https://github.com/sauloduttra/hjm-lab) | Reasons in the Heath-Jarrow-Morton forward-rate framework: the no-arbitrage drift condition, Gaussian-HJM bond prices and ZCB options, and how the volatility structure reproduces Ho-Lee, Hull-White and G2++. |
| **LIBOR Market Model** | [`lmm-lab`](https://github.com/sauloduttra/lmm-lab) | Handles discrete-tenor forward-LIBOR modelling: measure-consistent drifts, Black-76 caplets, the Rebonato abcd vol surface and correlation, and Rebonato swaptions. |

## Importing

Import the **team** or the individual **personas**, never both — the team snapshot embeds every member in full, and importing it after the personas creates duplicates.

Built by [Saulo Duttra](https://github.com/sauloduttra).

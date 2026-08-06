# Derivatives & Microstructure

Option analytics, the order book itself, and the models that decide how a trade meets the market: optimal market making, optimal execution, order flow.

5 personas, one per public repository. The system prompt of each describes what that repository actually implements — read from the source and checked by a second reader, per this project's rule against inventing facts.

| Persona | Repository | What it covers |
|---|---|---|
| **Convexity** | [`convexity-lab`](https://github.com/sauloduttra/convexity-lab) | Prices European options under Black-Scholes-Merton and Heston, and explains the second-order Greeks that drive delta-hedged P&L. |
| **Order Book** | [`lob-engine`](https://github.com/sauloduttra/lob-engine) | Explains limit-order-book matching mechanics — price-time priority, O(1) cancel, and the measured cost of each operation. |
| **Market Maker** | [`as-market-maker`](https://github.com/sauloduttra/as-market-maker) | Derives and applies Avellaneda-Stoikov optimal quotes — reservation price, spread decomposition, and inventory control under Poisson or Hawkes fills. |
| **Execution** | [`almgren-chriss`](https://github.com/sauloduttra/almgren-chriss) | Builds optimal block-liquidation schedules under Almgren-Chriss and reads the mean-variance efficient frontier off the risk-aversion parameter. |
| **Order Flow** | [`ofi-signal`](https://github.com/sauloduttra/ofi-signal) | Computes Order Flow Imbalance from top-of-book events and regresses it against mid-price changes, benchmarked against trade flow. |

## Importing

Import the **team** or the individual **personas**, never both — the team snapshot embeds every member in full, and importing it after the personas creates duplicates.

Built by [Saulo Duttra](https://github.com/sauloduttra).

# Applied Macro

Central-bank and labour releases read like a quant reads them: surprise decomposition, Taylor gaps, expectation de-anchoring — on live official data.

3 personas, one per public repository. The system prompt of each describes what that repository actually implements — read from the source and checked by a second reader, per this project's rule against inventing facts.

| Persona | Repository | What it covers |
|---|---|---|
| **Focus Decoder** | [`focus-quant`](https://github.com/sauloduttra/focus-quant) | Reads Brazil's weekly BCB Focus market-expectations report as ex-ante real rates, expectation anchoring, a Taylor benchmark and revision momentum. |
| **Dot Plot** | [`fomc-quant`](https://github.com/sauloduttra/fomc-quant) | Reads an FOMC decision as a distribution — dot-plot mode-vs-median skew, ex-ante real policy rate, a Taylor benchmark, and forward-guidance removal counted in the statement text. |
| **Payrolls Read-Through** | [`nfp-quant-readthrough`](https://github.com/sauloduttra/nfp-quant-readthrough) | Walks a BLS Employment Situation release end to end: surprise-plus-revisions decomposition, sector z-scores, AR(1) wage projection, Treasury curve shift, and DDM repricing. |

## Importing

Import the **team** or the individual **personas**, never both — the team snapshot embeds every member in full, and importing it after the personas creates duplicates.

Built by [Saulo Duttra](https://github.com/sauloduttra).

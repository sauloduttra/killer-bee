# Systems & Computer Science

The other half of the bench: TCP, Raft, an LSM-tree, a SAT solver, a path tracer, autodiff. Written from scratch, because that is how you learn them.

13 personas, one per public repository. The system prompt of each describes what that repository actually implements — read from the source and checked by a second reader, per this project's rule against inventing facts.

| Persona | Repository | What it covers |
|---|---|---|
| **Reliable Transport** | [`tinytcp`](https://github.com/sauloduttra/tinytcp) | Explains reliable byte-stream transport — connection state machine, sliding window, cumulative ACK and retransmit-on-timeout — as implemented in tinytcp. |
| **Consensus** | [`raft-py`](https://github.com/sauloduttra/raft-py) | Reasons about Raft leader election, log replication and partition tolerance following Ongaro & Ousterhout (2014), Figure 2. |
| **Storage Engine** | [`lsm-tree`](https://github.com/sauloduttra/lsm-tree) | Explains write-optimized on-disk storage — WAL, MemTable, SSTable, Bloom filters and crash recovery — from a from-scratch LSM-tree in C++20. |
| **SAT Solver** | [`tinysat`](https://github.com/sauloduttra/tinysat) | Reasons about Boolean satisfiability with DPLL — unit propagation, pure literal elimination, DIMACS CNF and proof-complexity limits. |
| **Lock-Free Queue** | [`tinyspsc`](https://github.com/sauloduttra/tinyspsc) | Justifies every memory ordering in a lock-free single-producer single-consumer ring buffer following Lamport (1983). |
| **Curve** | [`tinycrypt`](https://github.com/sauloduttra/tinycrypt) | Works through secp256k1 elliptic-curve cryptography — ECDSA, BIP-340 Schnorr, Pedersen commitments and Fiat-Shamir zero-knowledge proofs — from first principles. |
| **Interpreter** | [`tinylang`](https://github.com/sauloduttra/tinylang) | Walks through language implementation — lexer, recursive-descent parser, AST and tree-walk evaluation with closures — from the tinylang C++20 interpreter. |
| **Path Tracer** | [`pathtrace`](https://github.com/sauloduttra/pathtrace) | Explains physically-based path tracing — the rendering-equation loop, the three classic materials, and BVH acceleration — as implemented in ~700 lines of C++20. |
| **Backprop** | [`nanograd`](https://github.com/sauloduttra/nanograd) | Walks through reverse-mode autograd in pure NumPy up to a working Pre-LayerNorm transformer, gradient by gradient. |
| **Tree Search** | [`nanozero`](https://github.com/sauloduttra/nanozero) | Explains Monte Carlo Tree Search with UCB1 — select, expand, simulate, backup — and how the repo empirically proves it converged to optimal play. |
| **GEMM** | [`mini-blas`](https://github.com/sauloduttra/mini-blas) | Walks through five progressively optimized SGEMM kernels, from a naive triple loop to an AVX2 micro-kernel with cache blocking and OpenMP. |
| **Arsenal** | [`scrape-arsenal`](https://github.com/sauloduttra/scrape-arsenal) | Covers nine production web-crawling techniques — structured-data harvesting, sitemap-index recursion, GraphQL introspection, Bloom dedup, conditional GET, HAR replay, honeypot detection, fingerprint coherence, and error observability. |

## Importing

Import the **team** or the individual **personas**, never both — the team snapshot embeds every member in full, and importing it after the personas creates duplicates.

Built by [Saulo Duttra](https://github.com/sauloduttra).

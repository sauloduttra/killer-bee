# Auditoria de licenciamento — repositórios públicos

Conta: `sauloduttra`. Gerado por `scripts/license_audit.py` (somente leitura).

> **Nada foi aplicado.** Escolher ou alterar licença é decisão do dono.

## Resumo

- **123** repositórios públicos
- **49** originais · **74** forks
- **1** originais **sem licença nenhuma**
- **0** com contribuidor externo
- **1** com header SPDX em algum arquivo

Licenças reais dos originais, lidas do arquivo:

- **MIT** — 48
- **AUSENTE** — 1

## Sobre o campo `licenseInfo` do `gh repo list`

Esta auditoria **não** usa `gh repo list --json licenseInfo`: aquele campo volta
`null` mesmo para repositórios que a própria API classifica como MIT. Confirmado
em `almgren-chriss` e `var-lab`, onde `/repos/{owner}/{repo}`,
`/repos/{owner}/{repo}/license` e o GraphQL `licenseInfo` respondem **MIT** aos
três. Confiar na listagem produziria um falso "todos os direitos reservados" em
massa — foi o que aconteceu nas três primeiras rodadas desta auditoria.

As colunas abaixo vêm de duas fontes independentes que **concordam**: o texto
do arquivo (`classify_license_text`) e a detecção do GitHub em
`/repos/{owner}/{repo}`.

## O que 'sem licença' significa

Repositório público sem `LICENSE` é **todos os direitos reservados**. O código fica
visível, mas ninguém pode legalmente usar, modificar ou redistribuir. Público não é
open source. É o pior dos dois mundos: o trabalho está exposto e é inutilizável por
terceiros — não gera adoção, não gera citação, não gera contribuição, e ainda assim
está lá para quem quiser ler.

Licença cobre **implementação, não ideia**. Avellaneda-Stoikov é paper publicado;
qualquer um reimplementa legalmente. A licença impede o copy-paste, não a releitura.
Isso deve baixar a ansiedade sobre quanto blindar.

**Fork herda a licença do upstream.** Os forks desta lista não são seus para
relicenciar — a coluna de tier marca `HERDA` e eles saem da decisão.

## Urgência

✅ **Nenhum repositório original tem contribuidor externo.** O dono detém 100% do
copyright e pode relicenciar o que quiser, quando quiser. Essa janela fecha no
primeiro PR externo aceito sem DCO ou CLA. Licenciar agora, antes de ganhar
visibilidade, é barato; depois vira negociação com cada contribuidor.

## Repositórios originais

`licença real` vem do texto do arquivo. `GitHub vê` é o que a API reporta — quando diverge, o badge não aparece na interface.

| repo | licença real | GitHub vê | titular | SPDX | contrib. externos | linguagem | último push | tier | motivo |
|---|---|---|---|---|---|---|---|---|---|
| `almgren-chriss` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Python | 2026-05-23 | OK | MIT; falta header SPDX nos fontes |
| `as-market-maker` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Python | 2026-05-23 | OK | MIT; falta header SPDX nos fontes |
| `autograd-lab` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Python | 2026-05-19 | OK | MIT; falta header SPDX nos fontes |
| `backtest-engine` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | C++ | 2026-06-07 | OK | MIT; falta header SPDX nos fontes |
| `cointegration-lab` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Python | 2026-06-07 | OK | MIT; falta header SPDX nos fontes |
| `convexity-lab` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Python | 2026-05-18 | OK | MIT; falta header SPDX nos fontes |
| `copula-lab` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Python | 2026-08-05 | OK | MIT; falta header SPDX nos fontes |
| `corpfin-lab` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Python | 2026-06-02 | OK | MIT; falta header SPDX nos fontes |
| `credit-lab` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Python | 2026-06-10 | OK | MIT; falta header SPDX nos fontes |
| `eqval-lab` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Python | 2026-06-03 | OK | MIT; falta header SPDX nos fontes |
| `factor-lab` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Python | 2026-07-16 | OK | MIT; falta header SPDX nos fontes |
| `fixedalt-lab` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Python | 2026-06-03 | OK | MIT; falta header SPDX nos fontes |
| `focus-quant` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Python | 2026-06-08 | OK | MIT; falta header SPDX nos fontes |
| `fomc-quant` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Python | 2026-06-18 | OK | MIT; falta header SPDX nos fontes |
| `forensic-lab` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Python | 2026-07-14 | OK | MIT; falta header SPDX nos fontes |
| `fra-lab` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Python | 2026-06-04 | OK | MIT; falta header SPDX nos fontes |
| `g2pp-lab` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Python | 2026-06-17 | OK | MIT; falta header SPDX nos fontes |
| `hawkes-fit` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Python | 2026-06-07 | OK | MIT; falta header SPDX nos fontes |
| `hjm-lab` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Python | 2026-06-28 | OK | MIT; falta header SPDX nos fontes |
| `kalman-lab` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Python | 2026-06-07 | OK | MIT; falta header SPDX nos fontes |
| `lattice-lab` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Python | 2026-06-22 | OK | MIT; falta header SPDX nos fontes |
| `lmm-lab` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Python | 2026-07-05 | OK | MIT; falta header SPDX nos fontes |
| `lob-engine` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | C++ | 2026-05-22 | OK | MIT; falta header SPDX nos fontes |
| `lsm-tree` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | C++ | 2026-05-25 | OK | MIT; falta header SPDX nos fontes |
| `lsmc-lab` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Python | 2026-07-04 | OK | MIT; falta header SPDX nos fontes |
| `mini-blas` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | C++ | 2026-05-23 | OK | MIT; falta header SPDX nos fontes |
| `monte-carlo-lab` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Python | 2026-06-07 | OK | MIT; falta header SPDX nos fontes |
| `nanograd` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Python | 2026-05-25 | OK | MIT; falta header SPDX nos fontes |
| `nanozero` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Python | 2026-05-28 | OK | MIT; falta header SPDX nos fontes |
| `nfp-quant-readthrough` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Python | 2026-06-05 | OK | MIT; falta header SPDX nos fontes |
| `ofi-signal` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Python | 2026-05-23 | OK | MIT; falta header SPDX nos fontes |
| `pathtrace` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | C++ | 2026-05-26 | OK | MIT; falta header SPDX nos fontes |
| `pde-lab` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Python | 2026-05-28 | OK | MIT; falta header SPDX nos fontes |
| `port-lab` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Python | 2026-06-07 | OK | MIT; falta header SPDX nos fontes |
| `raft-py` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Python | 2026-05-23 | OK | MIT; falta header SPDX nos fontes |
| `regression-lab` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Python | 2026-07-09 | OK | MIT; falta header SPDX nos fontes |
| `sauloduttra` | **AUSENTE** | — | — | não | — | — | 2026-07-06 | N/A | repo de perfil (README da conta) |
| `scrape-arsenal` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Python | 2026-05-24 | OK | MIT; falta header SPDX nos fontes |
| `shortrate-lab` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Python | 2026-06-14 | OK | MIT; falta header SPDX nos fontes |
| `smile-lab` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Python | 2026-07-18 | OK | MIT; falta header SPDX nos fontes |
| `tinycrypt` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Python | 2026-05-26 | OK | MIT; falta header SPDX nos fontes |
| `tinylang` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | C++ | 2026-05-26 | OK | MIT; falta header SPDX nos fontes |
| `tinysat` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Rust | 2026-05-29 | OK | MIT; falta header SPDX nos fontes |
| `tinyspsc` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Rust | 2026-06-01 | OK | MIT; falta header SPDX nos fontes |
| `tinystat` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Python | 2026-06-02 | OK | MIT; falta header SPDX nos fontes |
| `tinytcp` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | C++ | 2026-05-29 | OK | MIT; falta header SPDX nos fontes |
| `tvm-lab` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Python | 2026-06-07 | OK | MIT; falta header SPDX nos fontes |
| `var-lab` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Python | 2026-06-07 | OK | MIT; falta header SPDX nos fontes |
| `vol-lab` | MIT | MIT | Copyright (c) 2026 Saulo Duttra | não | — | Python | 2026-06-26 | OK | MIT; falta header SPDX nos fontes |

## Forks (licença herdada do upstream — fora da decisão)

- **Astro**: `awesome-privacy`
- **Go**: `casbin`, `gitleaks`, `kratos`, `ollama`, `pocketbase`, `trivy`, `trufflehog`
- **HTML**: `tabler`
- **Java**: `zaproxy`
- **JavaScript**: `React_Bank`, `y-websocket`, `yjs`
- **MDX**: `magicui`
- **OCaml**: `semgrep`
- **PHP**: `coolify`
- **Python**: `polar`, `sentry`
- **Ruby**: `kamal`
- **Shell**: `dokku`
- **TypeScript**: `SaaS-Boilerplate`, `adminjs`, `ai`, `appwrite`, `bank-app`, `banking`, `better-auth`, `bullmq`, `caprover`, `create-t3-app`, `directus`, `dokploy`, `form`, `grafana`, `highlight`, `hocuspocus`, `langchainjs`, `langgraphjs`, `lemonsqueezy.js`, `liveblocks`, `medusa`, `mockoon`, `n8n`, `next-auth`, `open-saas`, `openobserve`, `partykit`, `playwright`, `primitives`, `react-admin`, `react-bank`, `react-hook-form`, `refine`, `saas-starter`, `saas-starter-kit`, `sdk-typescript`, `signoz`, `stack-auth`, `storybook`, `strapi`, `stripe-node`, `supabase`, `tremor`, `trigger.dev`, `ui`, `valibot`, `vitest`, `worker`, `zod`
- **—**: `awesome`, `awesome-nextjs`, `awesome-react`, `awesome-selfhosted`, `bank`

## Compatibilidade dentro do Killer Bee

Killer Bee é Apache-2.0. Pode incorporar **MIT** e **Apache-2.0** sem fricção.
**Não pode** incorporar **AGPL** sem se tornar AGPL — e AGPL no Killer Bee mata a
adoção corporativa e qualquer chance de a Block encostar. Se um lab que a gente
queira expor como ferramenta MCP for copyleft forte, ou ele fica fora do pacote, ou
o projeto inteiro muda de licença. É uma decisão de arquitetura, não de burocracia.

## Aplicação — depois do OK, por tier

Para cada repo aprovado:

1. `LICENSE` na raiz, texto íntegro, ano e titular corretos
2. Header no topo de cada fonte: `SPDX-License-Identifier: <ID>`
3. Apache-2.0: `NOTICE` na raiz quando houver terceiros
4. Seção de licença explícita no `README` — ninguém deve precisar abrir o `LICENSE`
5. Commit único por repo: `chore: add <licença>`


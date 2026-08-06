# Inventário do material quant — `C:\Users\saulo\Downloads\C`

**Inventariado, não incorporado.** Nada foi copiado para o repo. Leitura apenas.

Varrido em 2026-08-05. 56 arquivos, ~3,79 GB (dos quais ~3,8 GB são CSV).

---

## ⚠️ Primeiro: não são agentes

O `FASE-1.md` §4 descreve este diretório como "os agentes quant do usuário". **Não há
nenhuma definição de agente aqui** — nenhum system prompt, nenhum `.persona.md`, nenhum
`.md` de agente, nenhum arquivo de configuração de persona. O único `.claude/` presente
contém apenas `settings.local.json` (45 KB, allowlist de permissões).

O que existe é um **toolkit quantitativo**: um terminal local estilo Bloomberg, sete
harnesses de validação numérica, dois benchmarks e um gerador de conteúdo. Isso é insumo
de **ferramenta MCP**, não de persona — o que é uma matéria-prima diferente, e em alguns
aspectos melhor. Registrado em [`OPEN-QUESTIONS.md`](OPEN-QUESTIONS.md) como Q-001.

O inventário abaixo trata o material pelo que ele é.

---

## Contaminação — leia antes de qualquer coisa

O scanner de credenciais (`scripts/scan_secrets.py`) varreu 21 arquivos de código e texto:
**zero achados de severidade alta ou média**. Nenhuma chave, token, senha ou string de
conexão. Os únicos achados foram e-mails `info@…` dentro do guia CFA.

**Mas a contaminação grave aqui não é de segredo — é de copyright e de dado pessoal**, e
nenhum scanner de credencial pega isso:

| Item | Tamanho | Natureza | Veredito |
|---|---|---|---|
| `qnt_crescimento_financeiro_rows/` (26 CSV) | ~3,8 GB | dados de vendor + notícias e transcrições protegidas + **PII de executivos** | 🚫 **NUNCA no repo, em nenhuma forma** |
| `refs/CFA-Level-I-Study-Guide.md` | 3,0 MB | material didático do CFA Institute | 🚫 **NUNCA no repo** |
| `terminal.db` (gerado) | ~420 MB | destilado dos CSVs acima | 🚫 derivado de fonte contaminada |
| `.claude/settings.local.json` | 45 KB | allowlist de permissões local | ⚠️ contém caminhos da máquina; sem valor para o repo |

A restrição dos CSVs não é inferência minha — está declarada no próprio
`qnt-terminal/README.md:57-59`:

> *"The raw CSVs stay local and are **not** redistributable (vendor data + copyrighted
> news/transcripts + executive PII). Only the distilled local cache and the terminal code
> live here. Nothing is pushed anywhere."*

**Consequência para fixture de teste:** nem amostra, nem recorte, nem "só umas linhas para
o exemplo". Dado de teste se gera sinteticamente com seed fixa (§2.5). PII de executivo
num repo público não se apaga com `git rm`.

---

## Inventário

### Harnesses de validação numérica — o ativo mais alinhado ao projeto

Sete scripts que existem **para provar que um número está certo**. São exatamente as
técnicas da §2.4 dos padrões de engenharia, já implementadas: valor de ouro por forma
fechada, teste de propriedade, concordância cruzada, controle de variância.

| Arquivo | Linhas | O que faz | Natureza | Mapeia para |
|---|---|---|---|---|
| `verify_em.py` | 72 | erro fraco de Euler-Maruyama em GBM contra `s0·exp(rT)` | código puro, só numpy | **Guard** |
| `verify_em_mc.py` | 38 | mesma medida sob ruído de Monte Carlo | código puro | **Guard** |
| `verify_em_crn.py` | 48 | **números aleatórios comuns**: um BM fino, engrossado por soma, para a inclinação log-log da ordem fraca estabilizar | código puro | **Guard** |
| `verify_em_fix.py` | 52 | dimensiona nº de caminhos para SE ≪ viés; testa antitéticas | código puro | **Guard** |
| `verify_qmc.py` | 125 | Van der Corput base 2, discrepância | código puro | **Guard** |
| `verify_qmc2.py` | 78 | Halton multidimensional, discrepância estrela | código puro | **Guard** |
| `verify_asian_cv.py` | 141 | asiática por Monte Carlo com **variável de controle**, ancorada em Black-Scholes fechado | código puro, numpy + scipy | **Guard** |

**Por que importam mais que o terminal.** Um agente que calcula é commodity — qualquer LLM
com numpy faz. Um agente que **sabe demonstrar que o cálculo está certo**, com ordem de
convergência medida e variável de controle, é raro. É o `Guard` do vocabulário do projeto
aplicado a número em vez de segurança: `threshold: low`, `persistence: long`.

Todos já são quase puros — recebem número, devolvem número, sem I/O. O único ajuste para
virar ferramenta MCP é extrair as constantes hardcoded (`s0, r, sigma, T = 100.0, 0.05,
0.2, 1.0`) para parâmetros nomeados com unidade, conforme §2.3.

### QNT Terminal — motor de cálculo

| Arquivo | Linhas | O que faz | Natureza | Mapeia para |
|---|---|---|---|---|
| `qnt-terminal/engine/calc.py` | ~290 | Monte Carlo (GBM + Heston), VaR/CVaR (histórico, paramétrico, MC), DuPont 5 fatores, Gordon DDM, múltiplos, DCF, Hawkes intradiário | código + I/O (SQLite) | **Forager** |
| `qnt-terminal/precompute.py` | 501 | ETL: destila 3,5 GB de CSV em cache SQLite | código + I/O pesado | **Forager** |
| `qnt-terminal/server.py` | 91 | API JSON Flask em `127.0.0.1:8787` | serviço | infraestrutura |
| `qnt-terminal/static/*` | ~25 KB | front dark estilo Bloomberg, canvas | UI | — |

**Dependências:** numpy, scipy, Flask, SQLite. E — crítico — **`terminal.db`, que é
derivado dos CSVs contaminados.** O código é portável; os dados não são.

**Bloqueio de arquitetura (§2.2).** `calc.py` viola a regra da camada pura: toda função
abre conexão SQLite na primeira linha (`monte_carlo` em `calc.py:86`, `value_at_risk` em
`:138`, `fundamentals_view` em `:185`). Não recebe número e devolve número — recebe
*ticker* e vai buscar no banco.

Consequência prática: **como está, não vira ferramenta MCP e não é testável sem
infraestrutura.** O porte exige a divisão em duas camadas — `monte_carlo_gbm(s0, mu_ann,
sigma_ann, horizon_days, n_paths, seed)` puro, e um invólucro fino que busca os
parâmetros no banco e chama o puro. A matemática já está correta e com seed explícita
(`calc.py:85`, `seed: int = 7`); é reorganização, não reescrita.

### Benchmarks e conteúdo

| Arquivo | Linhas | O que faz | Natureza | Mapeia para |
|---|---|---|---|---|
| `bench.py` / `bench.cpp` | 20 / — | crivo de primos até 1e8, Python vs C++ | código puro | **Guard** (regressão de performance) |
| `bench2.py` / `bench2.cpp` | 98 / — | Mandelbrot, GEMM, STREAM triad; Python puro vs numpy/BLAS | código puro | **Guard** |
| `make_carousel.py` | 352 | gera carrossel de 8 slides PNG 1080×1350 sobre o `credit-lab`, com fórmulas e gráficos reais do código | código + I/O (matplotlib) | **Forager** (divulgação) |

`make_carousel.py` é o mais inesperado do lote: um gerador de conteúdo técnico que puxa
fórmula e gráfico do próprio código-fonte, em vez de recriá-los à mão. Isso é diretamente
reaproveitável para a Fase 5 — o `CHANGELOG` e o material de divulgação do Killer Bee
podem sair do mesmo padrão.

### Referência

`refs/CFA-Level-I-Study-Guide.md` — 3 MB de material do CFA Institute. Útil como fonte de
consulta local para uma persona de finanças; **não redistribuível**. Se virar contexto de
agente, tem que ser por caminho local do usuário, nunca embarcado no pack.

---

## Ligação com os labs no GitHub

O `qnt-terminal/README.md:25-27` declara que a matemática espelha repositórios próprios:
`monte-carlo-lab` (GBM/Heston), `var-lab` (VaR/CVaR), `corpfin-lab` e `eqval-lab`
(DuPont/DDM), `hawkes-fit` (clustering intradiário). O `FASE-1.md` cita ainda `g2pp-lab`,
que valida swaption por três caminhos independentes — o padrão de concordância cruzada da
§2.4.

Todos existem como repositórios públicos e, pela amostragem da auditoria, são **MIT** —
portanto **incorporáveis** num Killer Bee Apache-2.0 (ver [`LICENSE-AUDIT.md`](LICENSE-AUDIT.md)).

Isso desenha o caminho natural, para depois: as personas quant do Killer Bee não carregam
matemática no system prompt — elas carregam **ferramentas MCP** que embrulham funções
puras dos labs, e um `Guard` que sabe validar o resultado. O prompt vira julgamento; o
número vira função testada.

---

## Nada disto entra agora

Registrado e parado aqui, como o `FASE-1.md` §4 determina: *"Inventariar agora, incorporar
depois. Não copiar nada para o projeto ainda."*

Os três pré-requisitos para incorporar, quando chegar a hora:

1. **Divisão pura/impura** em qualquer função que vire ferramenta (§2.2)
2. **Dado sintético** para todo teste — o dado real é intransportável
3. **Confirmação de licença** por repo, da varredura completa e não da amostra

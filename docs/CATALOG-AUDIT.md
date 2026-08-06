# Auditoria do catálogo por NCD — 51 personas

**Data:** 2026-08-06 · **Base:** working tree sobre `1cbb10b` · **Ferramenta:**
[`scripts/ncd_catalog.py`](../scripts/ncd_catalog.py) (determinística; reproduz com
`uv run python scripts/ncd_catalog.py`).

**A pergunta que este documento responde:** 51 personas geradas em uma rodada, num
site cujo produto declarado é "todo prompt legível antes de instalar" — quantas são
de fato distintas? Par com NCD baixa não é bug do detector: **é o catálogo dizendo a
verdade sobre si mesmo.**

**A decisão de corte é do usuário.** Este documento entrega a lista com o número do
lado, e para em recomendação.

---

## 1. Método (o que tornaria isto falso)

- `NCD(x,y) = [C(xy) − min(C(x),C(y))] / max(C(x),C(y))` — FASE-2 §4.1. Menor = mais
  parecido; a escala útil aqui vai de ~0,71 (par mais próximo) a ~0,94.
- **Unidade comparada: o CORPO do `.persona.md`** (o prompt), frontmatter removido —
  frontmatter carrega nome/modelo e inflaria a similaridade estrutural de todo par.
- Compressor primário **zstd nível 19**; cross-check com **lzma preset 6** no espírito
  do D-014 (duas fontes independentes; a concordância é o resultado):
  **sobreposição de 89,5% nos 76 pares do fundo** entre os dois compressores. O sinal
  não é artefato do zstd.
- `packs/TEMPLATE` excluído (caminho-de-10-minutos, não é conteúdo de catálogo).
- **Falsificadores:** editar o corpo de qualquer persona muda a matriz — este
  documento vale para `1cbb10b` e apodrece junto com os prompts; um compressor melhor
  que discorde do fundo do ranking derrubaria a lista (o cross-check lzma já limita
  esse risco a ~10%).
- Matriz completa 51×51: [`catalog-ncd-matrix.csv`](catalog-ncd-matrix.csv) — gerada
  pelo script, não editar à mão.

## 2. Distribuição

| personas | pares | mín | mediana | máx | MAD | limiar (med − 3·MAD) |
|---|---|---|---|---|---|---|
| 51 | 1275 | 0,7144 | 0,8760 | 0,9437 | 0,0129 | 0,8374 |

O corpo da distribuição é saudável: a mediana 0,876 diz que o par típico compartilha
pouco além do formato. O fundo é que interessa: **76 pares abaixo do limiar** — 60
dentro do mesmo pack (vocabulário do pilar; esperado) e 16 cruzados.

## 3. A régua interna — o par-controle

O catálogo carrega um controle involuntário e valioso: `crossfire-review/adversary` ~
`crossfire-review/guard` marcam **0,7801**. São as duas personas **escritas à mão para
serem máximas em diferença** (papéis opostos num mesmo time, com preâmbulo de time
compartilhado). Todo par gerado que fica ABAIXO disso é literalmente mais parecido
entre si do que dois colegas desenhados para divergir.

## 4. Zona A — mais parecidos que o par-controle (NCD < 0,7801)

| NCD | a | b |
|---|---|---|
| 0,7144 | rates-term-structure/g2pp-lab | rates-term-structure/hjm-lab |
| 0,7539 | rates-term-structure/hjm-lab | rates-term-structure/shortrate-lab |
| 0,7545 | systems-cs/autograd-lab | systems-cs/nanograd |
| 0,7620 | rates-term-structure/g2pp-lab | rates-term-structure/shortrate-lab |
| 0,7627 | rates-term-structure/hjm-lab | rates-term-structure/lmm-lab |
| 0,7647 | applied-macro/focus-quant | applied-macro/fomc-quant |

Três aglomerados, não seis problemas:

1. **`rates-term-structure`: {g2pp, hjm, shortrate, lmm}** — cluster denso; `hjm-lab`
   é o hub (aparece em 3 dos 6 pares da zona). Quatro personas dizendo variações da
   mesma coisa sobre modelos de curva.
2. **`systems-cs`: {autograd-lab, nanograd}** — dois repositórios de autodiff, duas
   personas quase intercambiáveis.
3. **`applied-macro`: {focus-quant, fomc-quant}** — dois observadores de banco
   central (Focus/BCB e FOMC/Fed) com o mesmo esqueleto.

## 5. Menos distintivas por recorrência (aviso, não veredito)

Personas que aparecem em mais pares do fundo — prompts com menos assinatura própria:

| persona | pares no fundo |
|---|---|
| risk-portfolio/var-lab | 8 |
| rates-term-structure/shortrate-lab | 7 |
| timeseries-stat-trading/tinystat | 7 |
| options-volatility/vol-lab | 7 |
| timeseries-stat-trading/hawkes-fit | 7 |

## 6. Recomendação — a decisão é sua

Opções com número do lado, da mais barata à mais agressiva:

- **Opção 0 — não cortar (51):** defensável; a mediana 0,876 mostra catálogo
  majoritariamente distinto. Mas a zona A fica publicada, e é auditável por qualquer
  um com `zstd` e vinte minutos.
- **Opção 1 — corte mínimo (51 → 48):** remover **`hjm-lab`** (o hub do cluster de
  rates; removê-lo desfaz 3 dos 6 pares da zona A), **um** de
  {`autograd-lab`, `nanograd`} e **um** de {`focus-quant`, `fomc-quant`}. Custo: ~20
  minutos (remover do pack + `packs_from_specs` + rebuild).
- **Opção 2 — corte estrutural (51 → 46-47):** opção 1 + reduzir o cluster de rates a
  dois (`shortrate-lab` + `lmm-lab`, os menos acoplados entre si depois de remover
  `hjm-lab` e `g2pp-lab`) e avaliar `var-lab` (o mais recorrente do fundo, 8 pares).
- Em qualquer opção: os 5 da §5 são os primeiros candidatos a REESCRITA (não corte) —
  ganharam pouco prompt próprio na geração em massa.

**Sanidade do detector:** o fundo cruzado (ex.: `convexity-lab` ~ `shortrate-lab`
0,8206) captura sobreposição temática real entre pilares — convexidade É curva de
juros. O detector está medindo o que promete.

## 7. Os 76 pares abaixo do limiar (0,8374)

<details>
<summary>Tabela completa (ordenada do mais próximo ao mais distante)</summary>

| NCD | a | b |
|---|---|---|
| 0,7144 | rates-term-structure/g2pp-lab | rates-term-structure/hjm-lab |
| 0,7539 | rates-term-structure/hjm-lab | rates-term-structure/shortrate-lab |
| 0,7545 | systems-cs/autograd-lab | systems-cs/nanograd |
| 0,7620 | rates-term-structure/g2pp-lab | rates-term-structure/shortrate-lab |
| 0,7627 | rates-term-structure/hjm-lab | rates-term-structure/lmm-lab |
| 0,7647 | applied-macro/focus-quant | applied-macro/fomc-quant |
| 0,7801 | crossfire-review/adversary | crossfire-review/guard |
| 0,7859 | valuation-fundamentals/corpfin-lab | valuation-fundamentals/eqval-lab |
| 0,7894 | rates-term-structure/g2pp-lab | rates-term-structure/lmm-lab |
| 0,7916 | timeseries-stat-trading/cointegration-lab | timeseries-stat-trading/kalman-lab |
| 0,7930 | options-volatility/lattice-lab | options-volatility/lsmc-lab |
| 0,7990 | valuation-fundamentals/eqval-lab | valuation-fundamentals/fra-lab |
| 0,8027 | timeseries-stat-trading/regression-lab | timeseries-stat-trading/tinystat |
| 0,8034 | valuation-fundamentals/corpfin-lab | valuation-fundamentals/fixedalt-lab |
| 0,8034 | valuation-fundamentals/fixedalt-lab | valuation-fundamentals/fra-lab |
| 0,8043 | valuation-fundamentals/eqval-lab | valuation-fundamentals/fixedalt-lab |
| 0,8044 | risk-portfolio/port-lab | risk-portfolio/var-lab |
| 0,8060 | options-volatility/smile-lab | options-volatility/vol-lab |
| 0,8067 | options-volatility/lattice-lab | options-volatility/smile-lab |
| 0,8090 | rates-term-structure/lmm-lab | rates-term-structure/shortrate-lab |
| 0,8098 | timeseries-stat-trading/cointegration-lab | timeseries-stat-trading/tinystat |
| 0,8101 | options-volatility/pde-lab | options-volatility/smile-lab |
| 0,8104 | options-volatility/lsmc-lab | options-volatility/smile-lab |
| 0,8116 | valuation-fundamentals/corpfin-lab | valuation-fundamentals/fra-lab |
| 0,8124 | risk-portfolio/copula-lab | risk-portfolio/factor-lab |
| 0,8132 | crossfire-review/adversary | crossfire-review/forager |
| 0,8132 | derivatives-microstructure/almgren-chriss | derivatives-microstructure/as-market-maker |
| 0,8132 | risk-portfolio/var-lab | timeseries-stat-trading/tinystat |
| 0,8146 | timeseries-stat-trading/kalman-lab | timeseries-stat-trading/tinystat |
| 0,8151 | valuation-fundamentals/forensic-lab | valuation-fundamentals/fra-lab |
| 0,8160 | risk-portfolio/factor-lab | risk-portfolio/port-lab |
| 0,8161 | timeseries-stat-trading/cointegration-lab | timeseries-stat-trading/hawkes-fit |
| 0,8166 | risk-portfolio/copula-lab | risk-portfolio/credit-lab |
| 0,8177 | systems-cs/raft-py | systems-cs/tinytcp |
| 0,8178 | options-volatility/lsmc-lab | options-volatility/vol-lab |
| 0,8185 | options-volatility/lsmc-lab | options-volatility/monte-carlo-lab |
| 0,8195 | timeseries-stat-trading/hawkes-fit | timeseries-stat-trading/kalman-lab |
| 0,8206 | derivatives-microstructure/convexity-lab | rates-term-structure/shortrate-lab |
| 0,8216 | options-volatility/vol-lab | timeseries-stat-trading/hawkes-fit |
| 0,8231 | risk-portfolio/credit-lab | risk-portfolio/factor-lab |
| 0,8238 | options-volatility/lattice-lab | options-volatility/monte-carlo-lab |
| 0,8238 | options-volatility/lsmc-lab | options-volatility/pde-lab |
| 0,8257 | risk-portfolio/var-lab | timeseries-stat-trading/hawkes-fit |
| 0,8258 | options-volatility/pde-lab | options-volatility/vol-lab |
| 0,8258 | valuation-fundamentals/eqval-lab | valuation-fundamentals/tvm-lab |
| 0,8264 | timeseries-stat-trading/hawkes-fit | timeseries-stat-trading/tinystat |
| 0,8269 | systems-cs/tinysat | systems-cs/tinyspsc |
| 0,8269 | rates-term-structure/shortrate-lab | valuation-fundamentals/tvm-lab |
| 0,8276 | options-volatility/monte-carlo-lab | options-volatility/vol-lab |
| 0,8278 | systems-cs/tinysat | systems-cs/tinytcp |
| 0,8279 | options-volatility/lattice-lab | options-volatility/vol-lab |
| 0,8288 | risk-portfolio/var-lab | timeseries-stat-trading/kalman-lab |
| 0,8299 | systems-cs/lsm-tree | systems-cs/tinytcp |
| 0,8299 | options-volatility/lattice-lab | options-volatility/pde-lab |
| 0,8304 | valuation-fundamentals/fixedalt-lab | valuation-fundamentals/tvm-lab |
| 0,8305 | systems-cs/tinyspsc | systems-cs/tinytcp |
| 0,8312 | options-volatility/smile-lab | rates-term-structure/g2pp-lab |
| 0,8314 | timeseries-stat-trading/backtest-engine | timeseries-stat-trading/tinystat |
| 0,8320 | systems-cs/lsm-tree | systems-cs/tinyspsc |
| 0,8324 | systems-cs/raft-py | systems-cs/tinyspsc |
| 0,8325 | valuation-fundamentals/eqval-lab | valuation-fundamentals/forensic-lab |
| 0,8325 | risk-portfolio/port-lab | timeseries-stat-trading/tinystat |
| 0,8330 | rates-term-structure/shortrate-lab | risk-portfolio/var-lab |
| 0,8330 | risk-portfolio/var-lab | timeseries-stat-trading/cointegration-lab |
| 0,8332 | risk-portfolio/port-lab | timeseries-stat-trading/hawkes-fit |
| 0,8334 | options-volatility/monte-carlo-lab | options-volatility/pde-lab |
| 0,8338 | rates-term-structure/shortrate-lab | valuation-fundamentals/fixedalt-lab |
| 0,8339 | derivatives-microstructure/convexity-lab | rates-term-structure/g2pp-lab |
| 0,8342 | crossfire-review/forager | crossfire-review/guard |
| 0,8349 | systems-cs/lsm-tree | systems-cs/tinysat |
| 0,8350 | risk-portfolio/credit-lab | risk-portfolio/port-lab |
| 0,8353 | timeseries-stat-trading/backtest-engine | timeseries-stat-trading/hawkes-fit |
| 0,8366 | risk-portfolio/var-lab | valuation-fundamentals/eqval-lab |
| 0,8366 | options-volatility/vol-lab | timeseries-stat-trading/kalman-lab |
| 0,8368 | systems-cs/autograd-lab | systems-cs/nanozero |
| 0,8372 | risk-portfolio/var-lab | valuation-fundamentals/tvm-lab |

</details>

Os três pares do `crossfire-review` na tabela são o time escrito à mão — compartilham
o preâmbulo de time por design e servem de calibração, não de candidato a corte.

---

## 8. Adendo pós-corte — 2026-08-06, opção 1 executada (D-036)

O usuário decidiu pela **opção 1**: 51 → 48. Saíram `rates-term-structure/hjm-lab`
(hub do cluster — removê-lo desfez 3 dos 6 pares da zona A),
`systems-cs/autograd-lab` (aparecia em 2 pares do fundo, com `nanograd` e com
`nanozero`; `nanograd` fica por ser o repo mais rico — transformer de ponta a ponta) e
`applied-macro/fomc-quant` (`focus-quant` fica: decodificador do Focus/BCB é
globalmente mais raro que mais um leitor de FOMC, e é o território do autor).

Distribuição re-medida com o mesmo método (a matriz e o CSV foram regenerados):

| personas | pares | mín | mediana | máx | limiar (med − 3·MAD) | abaixo do limiar | concordância zstd/lzma |
|---|---|---|---|---|---|---|---|
| 48 | 1128 | 0,7620 | 0,8767 | 0,9437 | 0,8376 | 71 | 91,5% |

**Zona A depois do corte: 1 par** (era 6). Sobra `g2pp-lab ~ shortrate-lab` a 0,7620 —
exatamente o residual que a opção 1 aceita e a opção 2 removeria. Fica registrado como
limitação conhecida, não como surpresa: os dois seguem no catálogo por decisão, com o
número ao lado. Os 5 recorrentes do fundo (§5) continuam candidatos a REESCRITA.

# Crossfire — protocolo de rodada e registro

**Estado: pré-registrado, NÃO executado.** Este arquivo existe antes da rodada de
propósito: o que conta como sucesso e como fracasso fica escrito **antes** de rodar,
para o resultado não virar história ajustada depois. Sucesso e fracasso valem igual —
se não funcionar, esse é o achado mais valioso do projeto.

Setup: [`LOCAL-SETUP.md`](LOCAL-SETUP.md) parte A. Versão do app e modelos usados são
campos obrigatórios do registro.

---

## 1. Protocolo pré-registrado

**Hipótese sob teste (a tese do projeto):** um `.team.json` reconstrói três agentes em
três modelos e eles trabalham juntos num canal — Forager responde à menção com um
patch; Adversary e Guard, com `require_mention = false`, reagem ao patch sem serem
chamados.

**Estímulo (fixo, uma mensagem, mencionando só a Forager):**

> @forager corrija esta função e poste o patch: `def median(xs): return sorted(xs)[len(xs)//2]` — quebra com lista vazia e erra em lista par.

O bug é escolhido por ter três camadas de leitura: correção óbvia (lista vazia),
correção estatística (mediana de lista par é média dos dois centrais — decisão de
design), e superfície de segurança nula (Guard deve dizer "no additional findings" ou
apontar algo real — falso alarme do Guard é registro de falha do prompt, não do app).

**Resultado esperado, por agente:**

| Agente | Gatilho | Esperado |
|---|---|---|
| Forager | menção direta | patch + nota de design, um turno |
| Adversary | patch no canal (sem menção) | ataque concreto: cenário, valores, sequência |
| Guard | patch no canal (sem menção) | auditoria das 4 superfícies ou "no additional findings" |

**Critérios binários (registrar cada um):**

- [ ] C1 — Forager respondeu à menção
- [ ] C2 — Adversary reagiu **sem** ser mencionada
- [ ] C3 — Guard reagiu **sem** ser mencionado
- [ ] C4 — as três respostas são distinguíveis em papel (não três revisões genéricas)
- [ ] C5 — algum agente referenciou o conteúdo de outro (crossfire de fato, não três monólogos)

**Falha parcial é dado:** C1 sem C2/C3 aponta para a regra de menção ou para o canal;
C1-C3 sem C5 aponta para o prompt do time, não para o protocolo.

**O que registrar sempre:** app versão · provider/modelo por agente · ordem real das
respostas · latência aproximada de cada uma · o que quebrou, verbatim · quantas
tomadas até uma limpa.

---

## 2. Roteiro de gravação — 90s

Premissas assumidas do que já sabemos: **a ordem de resposta não é garantida** e a
latência varia — o roteiro não promete ordem, e o plano B é cortar entre tomadas.
Gravar em 1080p; autoplay mudo (sem áudio, como o waggle-90s.mp4).

| t | Cena | O que mostrar |
|---|---|---|
| 0-10s | O artefato | `crossfire-review.team.json` aberto: três membros, três modelos visíveis no JSON |
| 10-20s | Import | Buzz Desktop → import do team → preview com os três avatares (cancelar se já importado; zero duplicatas — D-018) |
| 20-30s | O card | Team card com **"Mixed models"** no rodapé — o rótulo é a tese em uma palavra |
| 30-40s | A menção | Digitar a mensagem-estímulo no canal, enviar |
| 40-70s | O crossfire | Respostas chegando. Se a espera passar de ~10s reais, corte seco entre chegadas — honesto: cortes, não aceleração fingida |
| 70-85s | O desacordo | Zoom no trecho em que Adversary ou Guard contesta algo do patch — o desacordo é o produto |
| 85-90s | Fecho | Card do time + URL do catálogo |

**Regras da gravação:** nenhuma chave visível em nenhum frame (checar o painel de
settings antes de gravar); tomadas quantas precisar — o registro em §3 conta todas,
o vídeo mostra uma.

---

## 3. Registro das rodadas

> Preencher a cada rodada. Não editar rodadas passadas — acrescentar.

### Rodada 1 — (data)

| Campo | Valor |
|---|---|
| App | Buzz Desktop 0.5.x |
| Forager | provider / modelo |
| Adversary | provider / modelo |
| Guard | provider / modelo |
| C1-C5 | — |
| Ordem real | — |
| Latências | — |
| Quebrou o quê | — |
| Tomadas | — |

**Notas:**

(vazio até rodar)

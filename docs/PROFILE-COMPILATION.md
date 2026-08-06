# Compilação do perfil scutellata

Como os quatro traços da *Apis mellifera scutellata* viram configuração que o Buzz
realmente executa — e o que **não** vira, dito com a mesma clareza.

## O mecanismo tem nome, e não é "abelha"

`threshold`, `recruitment` e `persistence` são uma instância do **modelo de limiar de
resposta** (*response threshold model*) da divisão de trabalho em insetos sociais. O nome
biológico é a intuição; o modelo é a coisa.

Na forma de limiar **fixo**, o indivíduo *i* executa a tarefa *j* com probabilidade que
cresce com a intensidade do estímulo `s_j` e cai com o próprio limiar `θ_ij`:

```
P(executar) = s_j^n / (s_j^n + θ_ij^n)
```

Uma sigmoide em `s`, com `θ` deslocando o ponto de meia-resposta e `n` controlando a
inclinação. **Do que isto é caso particular:** uma função logística com viés por agente —
a mesma forma de um gate sigmoide, ou de um teste de razão de verossimilhança com limiar
por indivíduo.

O que o Killer Bee faz hoje é a versão **discreta e estática** disso: `threshold` é um de
três valores, escolhido pelo autor do pack, que compila para quem-pode-disparar
(`respondTo`) e o-que-dispara (`require_mention`). Não há `s_j` contínuo, não há
probabilidade, não há aprendizado.

**A versão adaptativa — em que `θ` se move com a experiência — está no backlog como
[B-02](BACKLOG.md#b-02--limiar-adaptativo-no-perfil-scutellata) e não está implementada.**
Lá `threshold` deixa de ser constante e vira condição inicial. Isso muda o schema do pack,
por isso está registrado antes de o formato congelar.

**Nenhuma novidade algorítmica é reivindicada aqui.** O modelo é dos anos 90; a
contribuição é mapeá-lo para os campos que o runtime do Buzz de fato lê.

**Teste de remoção:** tire a abelha inteira do texto. Sobra "três eixos de configuração de
gatilho por agente, que compilam para campos nativos, com faixa e citação". Sustenta-se
sozinho. A biologia fica porque explica **por que** três eixos e não cinco — não porque
seja o argumento.

### Referências

> **Limiar fixo** — o modelo que esta implementação instancia:
> Bonabeau, E., Theraulaz, G., Deneubourg, J.-L. "Quantitative study of the fixed threshold
> model for the regulation of division of labour in insect societies". *Proc. R. Soc. Lond.
> B*, **263**(1376), 1565–1569, 1996.
> DOI: [10.1098/rspb.1996.0229](https://doi.org/10.1098/rspb.1996.0229)
>
> **Limiar reforçado** — a versão adaptativa, que é [B-02](BACKLOG.md#b-02--limiar-adaptativo-no-perfil-scutellata)
> e **não está implementada**:
> Theraulaz, G., Bonabeau, E., Deneubourg, J.-L. "Response threshold reinforcements and
> division of labour in insect societies". *Proc. R. Soc. Lond. B*, **265**(1393), 327–332,
> 1998. DOI: [10.1098/rspb.1998.0299](https://doi.org/10.1098/rspb.1998.0299)

Duas armadilhas destas referências, ambas verificadas e documentadas em
[`BIBLIOGRAFIA.md`](BIBLIOGRAFIA.md):

- **A ordem dos autores inverte** entre os dois artigos — Bonabeau/Theraulaz/Deneubourg em
  1996, Theraulaz/Bonabeau/Deneubourg em 1998. Não é erro de digitação, e é o jeito rápido
  de saber qual dos dois alguém está citando.
- **O registro Crossref do DOI de 1998 grava o terceiro autor errado** (`J-N. Denuebourg`).
  Importar o DOI direto para BibTeX propaga o erro. O correto é Jean-Louis Deneubourg.

Há ainda um terceiro artigo, de 55 páginas, que se confunde com o seminal de 1996
(*Bull. Math. Biol.* 60(4):753–807, 1998). O seminal é o de 1996 — em fevereiro de 1998 a
própria Royal Society ainda citava o longo como "in the press".

Implementação: [`killerbee/profile.py`](../killerbee/profile.py). Este documento é o
contrato; o módulo é a execução; os testes (`tests/test_profile.py`) travam os dois um
no outro.

## Por que compilar, em vez de carregar o perfil como campo

Duas portas, ambas fechadas pelo upstream (@ `ed4b3e7a`):

1. **Frontmatter da persona:** `deny_unknown_fields` — chave desconhecida é **erro fatal
   de parse** (`crates/buzz-persona/src/persona.rs:174-176`).
2. **Snapshot:** chave extra é aceita no parse e **descartada** na reserialização do
   import (`desktop/src-tauri/src/commands/personas/snapshot/import.rs:410`). Pior que
   rejeição: falha silenciosa.

Logo o perfil vive no `killerbee.yaml` (camada L1) e **compila** para os campos nativos.
O bônus: campo nativo *faz* alguma coisa — um metadado inerte não faria.

## A tabela de compilação

| Traço | Valores | Alvo nativo | Citação do alvo | Semântica |
|---|---|---|---|---|
| `recruitment` | inteiro `1..=32` | `definition.parallelism` | faixa e default em `types.rs:812` | mapeamento **direto**, sem tradução — a faixa é a do campo nativo |
| `persistence` | `short` / `medium` / `long` | `definition.idleTimeoutSeconds` + `definition.maxTurnDurationSeconds` | campos em `agent_snapshot.rs:188-211` | `short`=300/600s · `medium`=900/1800s · `long`=3600/7200s |
| `threshold` (eixo **quem**) | `low` / `medium` / `high` | `definition.respondTo` | valores válidos `{owner-only, allowlist, anyone}` no import (§10.8) | `low`/`medium`→`anyone` · `high`→`owner-only` |
| `threshold` (eixo **o quê**) | idem | `require_mention` na regra ACP | `SubscriptionRule` em `filter.rs`; arquivo `TomlConfig{rules}` em `config.rs:1158` | `low`→`false` (reage a tudo no canal) · `medium`/`high`→`true` (só menção) |
| `propagation` | `low` / `medium` / `high` | **nada** | — | metadado de catálogo (badge no site, sinal de forkabilidade); não existe alvo de runtime |

### Os valores de `persistence` são nossos

O snapshot define os **campos**; a semântica de curto/médio/longo é decisão do Killer
Bee, documentada aqui e ajustável sem quebrar formato. Se os números mudarem, mudam
nesta tabela e em `_PERSISTENCE_SECONDS` no mesmo commit.

### A honestidade sobre `threshold`

`threshold` é biologicamente "quanto estímulo dispara a resposta". O runtime do Buzz
divide isso em dois eixos que não se misturam:

- **quem pode disparar** — `respondTo` no snapshot (`owner-only`/`allowlist`/`anyone`)
- **o que dispara** — o filtro de menção do buzz-acp

O snapshot **não tem campo de gatilho**. Então `threshold` compila para os dois alvos
acima e o que sobrar de nuance comportamental ("responde rápido a sinais fracos",
"ignora ruído") é responsabilidade do system prompt autoral — não fingimos que um enum
de três valores carrega isso.

### A regra que virou item de DoD

Toda regra ACP gerada escreve `require_mention` **explicitamente**, sempre. O default
do campo no struct é `false` (`filter.rs:122` — só o modo `--subscribe mentions` do
binário o liga), e uma regra TOML gerada sem o campo nasceria surda a menção. O teste
`test_acp_rules.py::test_DoD_toda_regra_gerada_tem_require_mention_escrito` falha o CI
se qualquer regra sair sem ele.

## Exemplo completo — o Adversary do crossfire

Manifesto (`packs/crossfire-review/killerbee.yaml`):

```yaml
profile:
  threshold: low        # reage a todo patch no canal, não só a menção
  recruitment: 8        # persegue em paralelo
  persistence: long     # não desiste do caso limite
  propagation: high     # forke à vontade — badge de catálogo
```

Compila para, no `adversary.agent.json`:

```json
{
  "parallelism": 8,
  "respondTo": "anyone",
  "idleTimeoutSeconds": 3600,
  "maxTurnDurationSeconds": 7200
}
```

E no `acp-rules.toml`:

```toml
[[rules]]
name = "adversary"
channels = "all"
require_mention = false
prompt_tag = "adversary"
```

`propagation: high` não aparece em lugar nenhum do runtime — aparece no
`catalog.json`, que é de onde o site lê. Exatamente como prometido.

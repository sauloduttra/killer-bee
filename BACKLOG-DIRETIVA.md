# KILLER BEE — Backlog estigmérgico e regra de enquadramento

> Precedência: `AUTONOMIA.md` > **esta** > `FASE-1.md` > `PROMPT.md`.
> **Leia a §0 antes de qualquer outra coisa deste arquivo.**

---

## 0. Escopo: quase nada aqui entra agora

Este documento registra ideias de arquitetura para depois e estabelece **uma regra que
vale imediatamente**.

**Gate duro:** nenhum item da §3 é implementado antes de (a) o site existir e buildar, e
(b) o vídeo de 90s estar gravado. Não comece a prototipar "só pra ver se funciona". Ideia
boa no meio da execução é o jeito mais comum de um projeto não terminar, e este projeto já
tem escopo suficiente para morrer sozinho.

**O que entra agora:** a §1 (regra de enquadramento), a §2 (verificação de citação) e a §4
(uma correção pequena num entregável da Fase 1). Só isso.

---

## 1. Regra de enquadramento — vale a partir de já

O projeto tem nome de abelha, tem perfil `scutellata`, e vai ganhar mais mecanismo de
inspiração biológica. Isso é um risco de credibilidade que precisa ser gerenciado desde o
primeiro README público.

**O contexto:** metaheurística com nome de bicho tem má fama merecida em ciência da
computação. Existe uma literatura inteira de "algoritmo novo do lobo / da baleia / do
morcego" que é algoritmo conhecido reembalado com análise pior. Engenheiro cético
reconhece o padrão e descarta em dez segundos — sem ler.

**A regra.** Toda vez que o projeto usar metáfora biológica em documento público, código
ou UI, os cinco itens abaixo aparecem juntos:

1. **Nome estabelecido do mecanismo**, antes ou junto do nome biológico — "estigmergia",
   "modelo de limiar de resposta", "bandit", "EWMA"
2. **Citação primária** da literatura
3. **A equação escrita**, não descrita
4. **Uma frase dizendo de que isso é caso particular** — por exemplo: reforço com
   decaimento é média móvel exponencial, que já está implementada no `vol-lab`
5. **Zero alegação de novidade algorítmica.** A contribuição é a aplicação ao substrato do
   Buzz, não a matemática

**Teste final, o que mais importa:** *remova a metáfora biológica inteira. A coisa ainda
se sustenta?* Se sim, a biologia é intuição legítima e pode ficar. Se não, é folclore e
sai.

A biologia explica **por que** funciona. Ela nunca é o argumento **de que** funciona.

---

## 2. Citação bibliográfica passa pelo mesmo crivo que citação de código

Mesmo padrão da Fase 0: verificada antes de entrar em documento público, e por um segundo
leitor.

As referências abaixo vieram do autor da diretiva e **não foram verificadas contra as
fontes** na origem. Tratadas como ponto de partida de busca, não como fato. O resultado da
verificação está em [`docs/BIBLIOGRAFIA.md`](docs/BIBLIOGRAFIA.md).

| Mecanismo | Referência a verificar |
|---|---|
| Estigmergia (o termo) | Grassé, 1959 — cunhado estudando cupins |
| Ant Colony Optimization | Dorigo, tese 1992; Dorigo, Maniezzo, Colorni — "Ant System", IEEE Trans. SMC-B, 1996 |
| Physarum resolvendo labirinto | Nakagaki et al., *Nature*, 2000 |
| Physarum e a rede ferroviária de Tóquio | Tero et al., *Science*, 2010 |
| Modelo de limiar de resposta fixo | Bonabeau, Theraulaz, Deneubourg, 1996–1998 |
| Limiar **reforçado** | Theraulaz, Bonabeau, Deneubourg — *Proc. R. Soc. B*, 1998 |
| Recrutamento e forrageamento em abelhas | Seeley — *The Wisdom of the Hive*, 1995 |
| Waggle dance | von Frisch — Nobel de 1973 |
| Thompson sampling | Thompson, 1933; Chapelle & Li, 2011; Agrawal & Goyal, 2012 |
| Normalized Compression Distance | Cilibrasi & Vitányi, IEEE Trans. Inf. Theory, 2005 |

---

## 3. Backlog

Registrado em [`docs/BACKLOG.md`](docs/BACKLOG.md) — **oito itens, nenhum implementado**,
todos atrás do gate da §0.

Schema por item: mecanismo estabelecido · intuição biológica · matemática · teste mínimo
que prova ou mata · do que depende · custo de reversão. Item sem teste mínimo não entra no
backlog.

---

## 4. Correção que entra na Fase 1

`docs/PROFILE-COMPILATION.md` documentava `threshold` / `recruitment` / `persistence`
apenas como derivados da abelha africanizada. Sob a regra da §1, insuficiente.

Acrescentado: os três campos são uma instância do **modelo de limiar de resposta** da
divisão de trabalho em insetos sociais, com referência, equação e a nota de que a versão
adaptativa está em B-02. `recruitment` continua compilando para o campo nativo de
paralelismo, faixa 1–32.

---

## 5. Decisão revogada

**O repo guarda-chuva dos 35 labs está cancelado.** Substituído por B-04. Registrado como
revogação em [`docs/DECISIONS.md`](docs/DECISIONS.md) — motivo: hub é ponto único de falha
de descoberta e só funciona para quem acha o hub; ligação local é mais barata, mais
robusta e funciona a partir de qualquer porta de entrada.

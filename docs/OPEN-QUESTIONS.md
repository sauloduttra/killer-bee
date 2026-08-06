# Perguntas em aberto

Dúvidas que **não** são vermelhas — o trabalho não parou por elas. Cada uma traz
recomendação e o custo de errar em cada opção. Pergunta cuja resposta está no código não
entra aqui: entra no código.

Resolvida vira linha em `DECISIONS.md` e sai daqui.

---

## Q-001 — Onde estão os "agentes quant"?

**Contexto.** O bloco 4 do `FASE-1.md` diz que `C:\Users\saulo\Downloads\C` "contém os
agentes quant do usuário". Não contém. O que há são **56 arquivos**: um terminal quant
(`qnt-terminal/` — engine, servidor Flask, front), sete scripts `verify_*.py` de validação
numérica, dois benchmarks C++/Python, um `make_carousel.py`, um guia CFA de 3 MB e 26 CSVs
somando ~3,8 GB. Nenhuma definição de agente, nenhum system prompt, nenhum `.md` de
persona. O único `.claude/` presente tem apenas `settings.local.json`.

**Recomendação.** Tratar `Downloads\C` como o que é — insumo de **ferramenta**, não de
persona — e seguir com o inventário nessa chave (feito em `QUANT-AGENTS-INVENTORY.md`).
Os agentes provavelmente estão noutro caminho.

**Custo de errar:**
- Se eu inventariar só isto e os agentes existirem noutro lugar: perde-se uma passada,
  barato de refazer.
- Se eu esperar pelo caminho certo antes de inventariar: o bloco trava por nada, e este
  material precisa ser triado de qualquer forma antes de encostar no repo.

**O que preciso:** o caminho real, se existir.

---

## Q-002 — Varredura completa de licenças não rodou

**Contexto.** O script está pronto e corrigido; a execução foi interrompida. Há dados
verificados por amostragem (3 repos, todos MIT) e a contagem agregada (123 públicos,
49 originais, 74 forks, zero contribuidores externos), mas não a tabela por repo.

**Recomendação.** Rodar quando houver janela — são poucos minutos e ~370 chamadas de API.
Não bloqueia nada do Killer Bee.

**Custo de errar:** nenhum imediato. O risco é decidir licenciamento com base na amostra
de 3 e descobrir depois um repo com licença ausente, proprietária ou de terceiro.

---

## Q-003 — O guia CFA e os CSVs nunca podem encostar no repo

**Contexto.** Dois itens em `Downloads\C` são contaminação de **copyright**, não de
segredo — o scanner de credenciais passa limpo neles:

1. `refs/CFA-Level-I-Study-Guide.md` (3 MB) — material didático do CFA Institute.
2. `qnt_crescimento_financeiro_rows/` (~3,8 GB de CSV) — o próprio README do
   `qnt-terminal` declara: *"not redistributable (vendor data + copyrighted
   news/transcripts + executive PII)"*.

**Recomendação.** Nenhum dos dois entra no repo, em nenhuma forma — nem amostra, nem
fixture de teste, nem "só umas linhas para o exemplo". Fixture de teste se gera
sinteticamente com seed fixa. Isto não é pergunta, é constatação; está aqui para ficar
visível.

**Custo de errar:** alto e irreversível. PII de executivo e transcrição licenciada num
repo público não se apagam com `git rm` — exigem reescrita de histórico, e a essa altura
já foram clonados.

---

## ~~Q-004 — L2 emite `.agent.json` para persona e `.team.json` para team, ou só persona?~~

**RESOLVIDA em E1.** O `TeamSnapshot.members` é `Vec<AgentSnapshot>`
(`team_snapshot.rs:76-87`) — embute o membro inteiro. O problema dos `persona_ids` como
UUID local afeta o `TeamRecord`, não o snapshot. Emitimos os dois. Ver `DECISIONS.md`
D-008.

---

## Q-006 — Um time real cabe em 256 KB?

**Contexto.** O corpo de um evento 30178 é limitado a 256 KB (`ingest.rs:1868`), e a
projeção de membro que vamos definir embute o `systemPrompt` de cada um. Um time de três
personas com prompts longos pode passar perto; um `Queen` com prompt de coordenação
extenso, mais quatro membros, pode estourar.

**Recomendação.** Medir com o primeiro pack real antes de publicar qualquer 30178. Se
estourar, as saídas em ordem de preferência: (a) truncar o prompt na projeção e apontar
para o `.agent.json` completo por URL; (b) publicar cada membro como 30175 `shared` e
deixar o 30178 só com referências; (c) dividir o time.

**Custo de errar:** o relay rejeita a publicação com `invalid: …`. Falha barulhenta, não
silenciosa — descoberta é barata. Só não pode ser descoberta na demo.

---

## Q-007 — O catálogo estático ou o ao-vivo é o caminho primário do site?

**Contexto.** Como não há leitura anônima (D-011), listar do relay ao vivo exige keypair
efêmero, NIP-42 e JS. Um catálogo gerado em build a partir de `packs/` não exige nada
disso — funciona sem JS, indexa em buscador, e carrega instantâneo.

**Recomendação.** Estático como primário, ao-vivo como camada adicional. O site nasce
listando `packs/`; o 30178 entra como "veja também o que está publicado no relay",
carregado depois. Isso mantém a página útil com JS desligado e evita que o catálogo
inteiro dependa de um relay estar de pé.

**Custo de errar:**
- Ao-vivo como primário: página em branco se o relay cair, nada indexável, e a promessa
  de "catálogo entre comunidades" some junto com o servidor.
- Estático como primário: o conteúdo ao-vivo fica menos visível. Reversível a qualquer
  momento.

---

## Q-005 — O relay público do L3 é infraestrutura de quem?

**Contexto.** A camada L3 pressupõe "um relay público nosso" para hospedar os kind:30175
`shared` e kind:30178. Isso é custo recorrente, superfície de ataque e responsabilidade de
moderação — e expor porta além de `127.0.0.1` é **vermelho**.

**Recomendação.** Não resolver agora. L1 e L2 não dependem disso, e o site pode nascer
lendo `packs/` estático. Quando L3 virar prioridade, decidir entre relay próprio, relay
de comunidade existente, ou o site apenas *apontar* para relays de terceiros sem hospedar.

**Custo de errar:** subir relay cedo demais é gastar dinheiro e atenção com moderação
antes de haver o que moderar.

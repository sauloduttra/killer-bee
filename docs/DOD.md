# Definition of Done — estado atual

Fonte do critério: [`FASE-1.md`](../FASE-1.md#dod-atualizado). Este arquivo é o placar,
atualizado a cada bloco. Item marcado só quando **verificado**, não quando "deve estar
funcionando".

| # | Item | Estado |
|---|---|---|
| 1 | `PROTOCOL-NOTES.md` com `## Premissas corrigidas na Fase 0` | ✅ em [`PROMPT.md`](../PROMPT.md#premissas-corrigidas-na-fase-0), com tabela derrubado/confirmado e citações |
| 2 | Schema `.agent.json`/`.team.json` documentado com citação | ✅ [PROTOCOL-NOTES §10](PROTOCOL-NOTES.md) |
| 3 | Veredito do 30178 registrado | ✅ [§11.5](PROTOCOL-NOTES.md) — **vai**, com a ressalva de NIP-42 |
| 4 | `killerbee build` emite arquivo que o desktop importa, com nº de cliques documentado | ✅ **importado num Buzz Desktop 0.5.5 rodando** em 2026-08-05: `.agent.json`, `.agent.png` e `.team.json` com 3 membros, os três aceitos. Registro em [§10.9](PROTOCOL-NOTES.md); cliques corrigidos em [§10.5](PROTOCOL-NOTES.md) |
| 5 | Personas publicadas como kind:30175 `shared`, legíveis pelo `PersonaCatalogDialog` | ⛔ bloqueado em 🔴 credencial |
| 6 | Team catalog 30178 publicado e lido ao vivo pelo site | ⛔ **publicar** segue bloqueado em 🔴 credencial (assinar exige chave). O que dava para fazer offline foi feito em 2026-08-06: o **schema do corpo** — que não existe no upstream, delegado ao cliente publicador (NIP-AP.md:223) — está definido e publicado em [`schema/kind-30178-content.schema.json`](../schema/kind-30178-content.schema.json), e `killerbee event` emite o evento **não assinado** (D-029). O site já existe e está no ar nos dois hosts; falta a leitura ao vivo, que além da credencial exige keypair efêmero + NIP-42 ([§11.5](PROTOCOL-NOTES.md)) |
| 7 | `killerbee validate` no CI, falhando em pack inválido | ✅ dois jobs: valida os packs **e** prova que rejeita um quebrado |
| 8 | `recruitment` → campo nativo de paralelismo (1–32); resto em `PROFILE-COMPILATION.md` | ✅ [`PROFILE-COMPILATION.md`](PROFILE-COMPILATION.md), com teste de faixa |
| 9 | Crossfire por menção, 3 agentes respondendo no canal | 🟨 **os 3 existem no app, em 3 providers distintos** — o Buzz rotula o team como "Mixed models". 2026-08-06: o custo do desbloqueio caiu para **UMA chave** — o rótulo olha o modelo, não o provider ([PROTOCOL-NOTES §7](PROTOCOL-NOTES.md), D-033); runbook reduzido a colar-chave → menção → esperar ([LOCAL-SETUP A](LOCAL-SETUP.md)); protocolo pré-registrado com critérios C1-C5 e roteiro de 90s em [CROSSFIRE-RUN.md](CROSSFIRE-RUN.md). Falta só a chave (🔴) |
| 10 | Site estático buildando, catálogo de `packs/`, fontes com `@font-face` | ✅ **builda nos dois modos (com e sem basePath), 21/21 testes de export** — incluindo integridade de todos os links internos, sha256 publicado vs arquivo servido, CSP, og:image/favicon/robots/sitemap. Fontes auto-hospedadas com subset filtrado (232 KB). Auditoria e correções em [AUDIT-2026-08-06](AUDIT-2026-08-06.md) |
| 11 | `LICENSE` Apache-2.0, `NOTICE`, `THIRD_PARTY_NOTICES.md`, `CONTRIBUTING.md` com DCO | ✅ os quatro, + job de DCO no CI |
| 12 | `docs/LICENSE-AUDIT.md` completo | ✅ **123 repos, zero falhas, duas fontes concordando** — 48 MIT, 1 ausente, 0 contribuidores externos |
| 13 | README com missão nova e nota de premissa corrigida | ✅ |
| 14 | `gitleaks` no CI, zero chave versionada | ✅ gitleaks + scanner próprio, ambos no CI |
| 15 | Vídeo de 90s | ✅ **produzido em 2026-08-06** (`media/waggle-90s.mp4`, 90.000s, 1080p30): o corte credential-free do roteiro em [AUDIT-2026-08-06](AUDIT-2026-08-06.md) — só telas REAIS (site no ar + Buzz Desktop 0.5.5), beats nos tempos exatos. O plano "3 agentes respondendo" ficou fora do corte de propósito; pipeline reproduzível em `site/scripts/video-compose.mjs`. A dependência de 5/9 era do roteiro antigo, não da técnica |

**Placar: 12 ✅ · 1 🟨 · 2 ⛔** — e os dois ⛔ dependem SÓ da credencial de provider.

> O item 15 fechado abriu o gate do [`BACKLOG.md`](BACKLOG.md), e o Saulo aprovou pelo
> ato de publicar (vídeo postado no X em 2026-08-06, marcando @jack).
>
> **Onde a fronteira do 🔴 está hoje (2026-08-06):** os itens 5 e 6 foram empurrados até
> o último passo que não toca em chave. O emissor L3 produz o evento kind 30178 completo
> e **não assinado**, com o schema do corpo definido e publicado; o artefato carrega o
> bloco `imeta` pronto para virar card importável em qualquer canal. O que falta nos dois
> é literalmente a assinatura — e, para o 6, a leitura ao vivo, que exige keypair efêmero
> + NIP-42 no site. O 🟨 do item 9 é o mesmo bloqueio: os três agentes existem, em três
> providers distintos, e não rodam por falta de credencial.

## O site, em detalhe

Além do exigido, o item 10 já entrega:

- **Prompt verbatim com endereço por linha.** Nenhum caractere é apagado — o `##`
  do heading fica na tela em tinta apagada enquanto a palavra ganha peso, e
  `#L12` aponta para a linha 12. Um conversor de markdown normal mostraria "Role"
  onde a fonte diz "## Role", e numa página cujo produto é *o prompt como o agente
  o recebe*, isso já é uma pequena mentira.
- **Signature funcional.** Cada persona é um traço de dança: ângulo separa,
  comprimento é `recruitment`, espessura é `persistence`, contagem de requebrados
  é `threshold`. Todo valor sai de campo real do manifesto — SVG server-rendered,
  sem canvas, sem JS, cada traço é link.
- **Honestidade embutida na UI.** O número de cliques do import, o "importado não
  é rodando", e o aviso de que a orquestração por menção não garante resposta.
- **`propagation` marcado como inerte** na própria interface — o único dos quatro
  eixos que não compila para nada em runtime.

## O que trava o quê

Um único vermelho — **gerar credencial** — trava os itens 5, 6, 9 e, por dependência, o
15. Não é dificuldade técnica: o runbook está pronto em
[`LOCAL-SETUP.md`](LOCAL-SETUP.md) e precisa de seis valores no `.env`.

O item 10 (site) fechou em 2026-08-06. Restam o item 9 (execução real dos três agentes,
🔴 credencial) e o 15 (vídeo — cujo roteiro sem credencial está pronto em
[AUDIT-2026-08-06](AUDIT-2026-08-06.md)). O gate do [`BACKLOG.md`](BACKLOG.md) só abre
depois do item 15.

## Diferença entre 🟨 e ✅

`🟨` significa que a parte que dependia de nós está feita e verificada, mas o critério
como escrito exige uma prova que ainda não foi possível produzir — importar de verdade no
desktop, ver três agentes responderem num canal, fechar a varredura de 123 repos.

Não marcamos verde por otimismo. O item 4 ficou amarelo enquanto emitia o arquivo e o
teste conferia byte a byte contra o schema lido do fonte — porque ninguém tinha importado
esse arquivo num Buzz Desktop rodando. Em 2026-08-05 isso aconteceu, e só então virou
verde ([§10.9](PROTOCOL-NOTES.md)).

A conta de ter esperado: o mesmo bloco que fechou o item 4 derrubou uma afirmação que o
site já publicava — a de que arrastar o arquivo sobre a seção Agents pulava dois cliques.
**E a história ganhou um segundo capítulo em 2026-08-06:** a "correção" também estava
errada — o fonte TEM alvo de drop (`useFileImportZone`, spread props que o grep de
`onDrop=` não vê), e a negação foi publicada com a mesma confiança que a promessa. Duas
lições empilhadas: afirmação de UI só fecha no app rodando (D-017), e ausência
confirmada exige enumerar o comportamento, não a sintaxe (D-035). **Amarelo honesto é o
que impede um verde de virar mentira — nas duas direções.**

# Decisões

Registro de escolhas 🟡 — arquitetura reversível, dependência de runtime, divergência de
documento, corte de escopo. Uma entrada por decisão: **o que**, **alternativa
considerada**, **motivo**, **custo de reversão**.

Decisão 🟢 (trivial, reversível em segundos) não entra aqui — vai numa linha do relatório
de bloco. Decisão 🔴 não é tomada: vira pergunta.

---

## D-001 — Projeto em `killer-bee`, sem espaço no caminho

**Quando:** Fase 0
**O que:** raiz do projeto em `D:\EMPRESAS\buzz\killer-bee`, não `D:\EMPRESAS\buzz\Killer Bee`.
**Alternativa:** manter o espaço e adotar a regra "todo path entre aspas, sem exceção".
**Motivo:** a pasta com espaço estava vazia, então o custo foi zero. Espaço em caminho
quebra script bash sem aspas, `cargo`, passos de `just` e resolução de path em ferramenta
Node — e o modo de falha é silencioso, que é o pior tipo.
**Custo de reversão:** trivial hoje (mover pasta). Cresce com o primeiro commit e vira
caro depois de qualquer URL pública apontar para o repo.

---

## D-002 — `PROMPT.md` e `FASE-1.md` criados a partir das mensagens

**Quando:** Bloco A
**O que:** os dois documentos governantes não existiam no disco — foram colados como
mensagem de chat. Criei ambos com o conteúdo íntegro recebido.
**Alternativa:** trabalhar só com o conteúdo em contexto e não materializar arquivo.
**Motivo:** o Bloco A manda "acrescentar ao fim do `PROMPT.md`", o que pressupõe arquivo.
Sem materializar, o rastro de correção não teria onde morar e a próxima sessão começaria
sem os documentos que definem precedência.
**Custo de reversão:** nulo — apagar dois arquivos.

---

## D-003 — Perfil scutellata não vai no frontmatter da persona

**Quando:** Fase 0, confirmado no Bloco A
**O que:** os campos `threshold` / `recruitment` / `persistence` / `propagation` vivem em
manifesto próprio do Killer Bee e são **compilados** para o que o Buzz entende.
**Alternativa:** colocá-los direto no frontmatter do `.persona.md`, como o `PROMPT.md` §5.3
imaginava.
**Motivo:** não é escolha. `struct Frontmatter` usa `deny_unknown_fields`
(`crates/buzz-persona/src/persona.rs:174-176`) — qualquer chave não prevista é **erro
fatal de parse**, não warning. Um `.persona.md` com `threshold:` simplesmente não carrega.
**Custo de reversão:** alto se descoberto tarde — reescreveria todo pack emitido. Por isso
está travado agora, antes do primeiro pack existir.

---

## D-004 — `scan_secrets.py`: camada pura separada da varredura

**Quando:** Bloco 4 (inventário)
**O que:** `scan_text(text) -> list[Finding]` é pura — recebe string, devolve achados, sem
tocar disco, rede ou relógio. Só `iter_files` faz I/O.
**Alternativa:** uma função só, que abre arquivo e imprime.
**Motivo:** §2.2 dos padrões de engenharia. Na prática: a função pura é testável sem
fixture em disco e embrulhável como ferramenta MCP depois. A impura não é nenhum dos dois.
**Custo de reversão:** nulo — é organização interna de um script de 200 linhas.

**Sub-decisão:** linha que casa com padrão de placeholder (`example`, `${VAR}`, `getenv`,
`<...>`) tem a severidade rebaixada para `baixa`, **exceto** quando a regra é de severidade
`alta`. Motivo: chave real dentro de linha com a palavra "example" continua sendo chave
real; já um `api_key = "${API_KEY}"` é o padrão correto e não pode gerar ruído.

---

## D-005 — Auditoria de licença classifica pelo texto do arquivo, não pelo metadado

**Quando:** Bloco D1
**O que:** `classify_license_text()` identifica a licença lendo o conteúdo do `LICENSE`,
com assinaturas ordenadas por especificidade. O campo `licenseInfo` da API virou coluna
secundária, usada só para detectar divergência.
**Alternativa:** confiar em `gh repo list --json licenseInfo`, que é uma chamada só e
muito mais barato.
**Motivo:** **o metadado mente.** A primeira versão do script reportou "todos os 81 repos
públicos sem licença". Verificação direta em `almgren-chriss`, `copula-lab` e `var-lab`
mostrou **MIT License, "Copyright (c) 2026 Saulo Duttra"**, texto padrão íntegro nos três.
O `licenseInfo` vinha `null` para todos. Conclusão errada quase virou decisão de
licenciamento.
**Custo de reversão:** nulo. Mas o custo de **não** ter corrigido seria alto: a auditoria
inteira apontaria para uma ação (licenciar 49 repos) que já está feita.
**Efeito colateral que vale investigar:** se a API não classifica, o GitHub não exibe o
badge de licença na interface. Um `LICENSE` invisível para o visitante tem quase o efeito
prático de não existir.

---

## D-006 — Crossfire por menção, não por invocação

**Quando:** Bloco A3
**O que:** o workflow emite um `send_message` mencionando os três agentes; cada um responde
porque o filtro de menção casou.
**Alternativa:** workflow invoca o time diretamente, como o `PROMPT.md` §7 especificava.
**Motivo:** imposto pelo runtime. `ActionDef` tem exatamente 7 variantes
(`crates/buzz-workflow/src/schema.rs:92`) e **nenhuma** cria, aciona ou chama agente.
**Custo de reversão:** nenhum a pagar por nós — se o upstream adicionar uma ação de
invocação, migrar é trocar o corpo do workflow.
**O que se perde e precisa estar no README:** determinismo. Ninguém garante que os três
respondam, nem em que ordem.

---

## D-007 — Regra TOML gerada seta menção explicitamente

**Quando:** Bloco A, verificação adversarial
**O que:** toda regra de subscrição em TOML que o Killer Bee gerar seta o campo de menção
de forma explícita, e um teste falha se um pack gerar regra sem ele.
**Alternativa:** confiar no default.
**Motivo:** o default depende do caminho. Em `--subscribe mentions` (modo default do
binário) `require_mention` vira `true`; mas o `impl Default` do campo é `false`
(`crates/buzz-acp/src/filter.rs:122`), então regra escrita à mão em modo
`subscribe=config` nasce com menção **desligada**. Como o crossfire inteiro depende de
menção funcionar, herdar esse default silenciosamente quebraria o produto principal.
**Custo de reversão:** baixo, mas o custo de errar é um preset que não responde e ninguém
sabe por quê.

---

## D-008 — L2 emite `.agent.json`, `.team.json` e `.agent.png`

**Quando:** E1
**O que:** o build do Killer Bee gera os três. Snapshot de agente em JSON, snapshot de
team em JSON, e a variante PNG do agente.
**Alternativa:** emitir só `.agent.json` e deixar a composição do time para o usuário —
era o plano defensivo enquanto Q-004 estava aberta.
**Motivo:** `TeamSnapshot.members` é `Vec<AgentSnapshot>`
(`desktop/src-tauri/src/managed_agents/team_snapshot.rs:76-87`) — **embute o membro
inteiro, não referencia id**. O medo de que o `.team.json` chegasse quebrado na máquina
do outro era infundado: o problema dos `persona_ids` como UUID local afeta o `TeamRecord`,
não o snapshot.
O `.agent.png` entra porque é o único artefato que já tem URL pública hoje (Blossom, com
`require_media_get_auth` default `false`) e porque é gerável fora do app: chunk `tEXt`,
keyword `buzz_agent_snapshot`, payload base64, antes do IDAT.
**Custo de reversão:** baixo — são três emissores independentes; derrubar um não afeta os
outros.

---

## D-009 — Perfil scutellata compila para campo nativo, não viaja como metadado

**Quando:** E1
**O que:** `recruitment` → `definition.parallelism`; `threshold` → `definition.respondTo`
+ `respondToAllowlist`; `persistence` → `idleTimeoutSeconds` / `maxTurnDurationSeconds`;
`propagation` fica só em L1. O resto vira texto no `systemPrompt`.
**Alternativa:** carregar o perfil como chave extra no snapshot, tipo
`x_killerbee_profile`.
**Motivo:** a chave extra **é aceita e depois descartada**. Não há
`deny_unknown_fields` no desktop, então o parse passa — mas o preview reserializa a struct
(`import.rs:410`), e o campo some. Pior que rejeitar: falha silenciosa que só aparece
quando alguém procura o dado e ele não está lá.
Compilar para campo nativo é melhor de qualquer forma: `parallelism` **faz** alguma coisa;
um metadado inerte não faria.
**Custo de reversão:** médio. Se o upstream passar a preservar campos desconhecidos, dá
para adicionar o metadado sem tirar a compilação — são complementares.

---

## D-010 — L3 usa kind 30178, com a projeção de membro derivada do `AgentSnapshot`

**Quando:** E2
**O que:** publicar team catalog como 30178, e definir a projeção de membro como o
`AgentSnapshot` menos o que a `NIP-AP:242` manda sanitizar.
**Alternativa:** cair para 30175 apenas (personas soltas, sem catálogo de team), que era o
plano B declarado no `FASE-1.md` B3.
**Motivo:** o 30178 aceita. Ingest valida só o envelope — um tag `d` de até 64 chars e o
`shared` opcional; conteúdo até 256 KB, sem validação de forma. Publicar exige apenas
`Scope::UsersWrite` e a própria chave: sem gate de owner ou admin. E a `NIP-AP:223` diz
que **o schema do conteúdo é definido pelo cliente que publica** — ou seja, definir a
projeção é contribuição legítima, não invasão.
Derivar do `AgentSnapshot` faz o mesmo objeto servir L2 e L3, e permite que um leitor
futuro do 30178 reconstrua um `.agent.json` sem tradução.
**Custo de reversão:** baixo enquanto ninguém mais consome. Alto depois — se outro cliente
adotar nossa projeção, mudá-la quebra terceiros. Vale versionar o corpo desde o primeiro
evento (o campo `v` da fixture existe justamente para isso).
**O que ainda não sabemos:** se um time real cabe em 256 KB com os system prompts
embutidos. Medir antes de publicar o primeiro.

---

## D-015 — Identidade visual: REGISTRO, com enxertos

**Quando:** Fase 3
**O que:** o site é um **registrador de gráfico** — papel de escala pré-impresso numa
tinta, traço queimado pelo estilete em outra. Nenhuma grandeza aparece nua: toda leitura é
desenhada sobre a faixa que a fonte declara.
**Como foi decidido:** três direções independentes, julgadas por três lentes (diferenciação,
credibilidade técnica, implementabilidade), sintetizadas. Dois dos três juízes convergiram
em REGISTRO.
**Motivo:** é a única das três **sem cor de acento**. Substrato + tinta de escala + um
pigmento em densidades + anotação + o buraco. Como não existe "a cor de destaque", o
default de dev tool não tem por onde entrar — a página não é resumível a "fundo X com
acento Y".
**Custo de reversão:** médio. É um bloco `:root` e uma lei tipográfica; o markup não muda.

**O que os juízes derrubaram, e vale mais que o veredito:**

- **As três direções eram a mesma família** — papel pálido, tinta escura quente, pigmento
  saturado, hachura, verbatim. E essa família tem precedentes que este público conhece:
  `berkeleygraphics.com`, `oxide.computer`, Tufte CSS. Conclusão operacional: **paleta e
  tipografia não diferenciam nada em três segundos** — a signature estrutural diferencia.
- **Cianótipo saiu** porque duas de três direções chegaram nele sozinhas, o que é a
  definição operacional de default.
- **O wordmark em grotesca expandida caixa-alta saiu** por ser a assinatura corrente de
  landing de protocolo — o nicho exato de onde vem o público. O eixo `wdth` do Archivo foi
  cortado inteiro, o que de quebra economiza 60–80% do arquivo de fonte.
- **Mono como face de display saiu** por ser a house style de metade do nicho.

**A correção estrutural que mudou hex:** `#C08A33` (2,52:1) era especificado como cor de
traço **clicável** no mesmo documento que o proibia como texto. Trocado por `#87581D`
(4,90:1). Como a rampa é monotônica em luminância, **toda ela passa AA e 1.4.11 por
construção** — uma garantia auditável no lugar de sete regras de uso que a terceira pessoa
a mexer no componente violaria. Custo assumido: perdemos o âmbar claro no tema claro.

**Verifiquei os 12 contrastes eu mesmo**, no navegador, com a fórmula WCAG. Todos batem.
Dois comentários do plano estavam otimistas em ~0,3 (`--char-muted`) e foram corrigidos
para o valor medido.

---

## D-016 — Desvio consciente: o `h1` do hero usa Archivo

**Quando:** Fase 3
**O que:** a lei tipográfica do plano reserva Archivo **exclusivamente** para nome próprio
de objeto do catálogo — wordmark, nome de pack, `displayName` de persona. O `h1` do hero é
prosa e, pela letra da lei, deveria ser Spectral.
**O que fiz:** mantive Archivo no `h1`.
**Motivo:** a razão da restrição era evitar dois clichês — grotesca expandida em caixa-alta
e rótulo condensado de SaaS. Nenhum dos dois está presente: sem eixo `wdth`, sem caixa-alta,
peso 500, tracking −0,012em. Um hero de sete linhas em serifada vira parede de texto e
enfraquece a única frase que precisa ser lida em três segundos.
**Custo de reversão:** uma linha de CSS.
**Registro honesto:** isto é desvio do plano, não cumprimento dele. Se a leitura for de que
a lei vale ao pé da letra, trocar é trivial e eu não defendo o contrário com afinco.

---

## D-014 — Falha de coleta nunca é reportada como ausência de dado

**Quando:** Bloco D1, depois de a mesma auditoria produzir conclusão errada **três vezes**
**O que:** `actual_license` só devolve `AUSENTE` quando a listagem da raiz foi obtida com
sucesso **e** não continha licença. Qualquer falha — listagem não veio, conteúdo não veio,
API errou — vira `DESCONHECIDO`, e o relatório abre com um banner contando quantas
chamadas falharam.

**As três falhas, todas do mesmo formato — confiar numa camada em vez de conferir:**

1. `licenseInfo` de `gh repo list` vem `null` mesmo com `LICENSE` MIT válido na raiz.
   Resultado: "81 repos sem licença", reportado ao usuário antes de a amostragem derrubar.
2. `gh_json` engolia falha e devolvia `None`; `None` virava `AUSENTE`. Falha silenciosa
   com cara de diagnóstico.
3. `gh api --jq '.content'` emite a string base64 **crua, sem aspas** — não é JSON, então
   `json.loads` falhava. **118 chamadas**, uma por repo com licença, todas viradas em
   "sem licença". O conteúdo estava lá o tempo todo: `TUlUIExpY2Vuc2U…` decodifica para
   "MIT License".

**Alternativa:** deixar como estava e conferir na mão. Foi o que a amostragem de 3 repos
fez — e foi o que salvou o relatório, mas não escala para 123.

**Motivo:** num relatório de auditoria, **ausência de evidência foi reportada como
evidência de ausência** três vezes seguidas. O tipo de bug mais caro que existe em
ferramenta de diagnóstico, porque a saída parece um resultado e o revisor não tem como
distinguir. A correção é estrutural: o tipo de retorno passa a distinguir "não tem" de
"não sei".

**Custo de reversão:** trivial no código; o custo de **não** ter feito seria uma decisão
de licenciamento tomada em cima de dado inventado pela própria ferramenta.

**E houve uma quinta — o mesmo bug da terceira, reintroduzido pela correção da
quarta.** Ao trocar a fonte de detecção para `/repos/{o}/{r}`, usei
`--jq '.license.spdx_id'`. `jq` imprime escalar **cru, sem aspas**, exatamente como
fazia com `.content`. `json.loads("MIT")` falha, 123 chamadas viraram erro, e o
sintoma foi o mesmo de sempre: "sem licença".

Corrigido com uma **guarda que torna o erro impossível**, não com mais cuidado:
`gh_json` agora **recusa** `--jq` cuja projeção não comece com `[`. Escalar exige
pedir o objeto e indexar em Python. A guarda tem teste
(`tests/test_license_audit.py::test_jq_escalar_e_recusado_antes_de_chamar_a_api`),
porque a lição das cinco vezes é que atenção não escala e tipo sim.

**Resultado final, com as duas fontes concordando:** 123 repositórios públicos,
49 originais, **48 MIT** e 1 ausente (o repo de perfil, que não precisa), zero
contribuidores externos, zero falhas de coleta. A detecção do GitHub e o texto do
arquivo dizem a mesma coisa — que é a validação cruzada que faltava desde a
primeira rodada.

**Houve uma quarta, e ela foi pega antes de virar relatório.** Com os três bugs acima
corrigidos, a auditoria passou a dizer que os 48 repositórios MIT estavam com o badge
invisível — `OK*`, "o GitHub não detecta". Antes de reportar, cruzei três endpoints:
`/repos/{o}/{r}`, `/repos/{o}/{r}/license` e o GraphQL `licenseInfo` **os três respondem
`MIT`** para `almgren-chriss` e `var-lab`. O GitHub detecta perfeitamente; quem mente é
especificamente o campo `licenseInfo` de `gh repo list`. A auditoria passou a ler a
detecção de `/repos/{owner}/{repo}`, e as duas fontes — texto do arquivo e detecção do
GitHub — agora **concordam**, o que é a validação cruzada que faltava desde o começo.

Se eu tivesse reportado, o usuário abriria 48 issues para consertar arquivos que já estão
certos.

**Regra que fica:** toda ferramenta de auditoria deste projeto distingue os três estados —
*confirmado presente*, *confirmado ausente*, *não coletado* — e nunca colapsa o terceiro
em nenhum dos outros dois. E quando duas fontes independentes puderem responder à mesma
pergunta, **as duas são consultadas e a concordância é o resultado** (§2.4, concordância
cruzada — o mesmo princípio que valida código numérico vale para ferramenta de auditoria).

---

## D-012 — REVOGADA: repo guarda-chuva dos 35 labs

**Quando:** diretiva de backlog
**Status:** ⛔ **cancelada antes de começar** — nenhum trabalho foi feito nela.
**O que era:** um repositório guarda-chuva indexando os ~35 labs quantitativos.
**O que fica no lugar:** B-04 em [`BACKLOG.md`](BACKLOG.md) — rede micelial, em que cada
lab carrega no próprio README o mapa dos vizinhos.
**Motivo:** **hub é ponto único de falha de descoberta, e só funciona para quem acha o
hub.** Quem cai num lab vindo de busca não passa pelo índice. Ligação local é mais barata
(um parágrafo por README, sem repo novo para manter), mais robusta (nenhum nó é
indispensável) e funciona a partir de qualquer porta de entrada.
**Custo de reversão:** nulo — nada foi construído. Registrado porque decisão revogada sem
rastro reaparece daqui a três meses como ideia nova.

---

## D-013 — Toda metáfora biológica carrega mecanismo, citação e equação

**Quando:** diretiva de backlog
**O que:** regra de enquadramento permanente, em `CONTRIBUTING.md` e aplicada a todo
documento público: nome estabelecido do mecanismo, citação primária verificada, equação
escrita, de que é caso particular, e zero alegação de novidade algorítmica. Mais o teste
de remoção — tirada a biologia, a coisa ainda se sustenta?
**Alternativa:** manter a metáfora como tema narrativo, sem aparato.
**Motivo:** metaheurística com nome de bicho tem má fama merecida. Engenheiro cético
reconhece o padrão de "algoritmo novo do lobo" e descarta sem ler. O custo de conformar é
um parágrafo por mecanismo; o custo de não conformar é o leitor técnico que a gente mais
quer ir embora na primeira tela.
**Custo de reversão:** baixo, mas revogar isso significaria aceitar ser lido como folclore.
**Consequência imediata:** bibliografia passa pelo mesmo crivo que citação de código —
verificada na fonte, por segundo leitor, antes de ir a documento público.

---

## D-011 — O site precisa de keypair efêmero; não existe leitura anônima

**Quando:** E2
**O que:** o Waggle gera um keypair por carregamento de página e faz NIP-42 antes de
listar qualquer evento.
**Alternativa:** ler o relay anonimamente, como a Fase 0 §5.3 supôs ser possível.
**Motivo:** não é possível. `REQ` sem autenticação recebe
`auth-required: authenticate before subscribing` (`crates/buzz-relay/src/handlers/req.rs:77`).
A técnica de chave efêmera que o web client deles usa não é atalho — é o único caminho.
**Custo de reversão:** nenhum a pagar, mas tem duas consequências que já valem: a CSP não
pode ser copiada do buzzdir (que tem `connect-src 'self'` e nunca abre `wss:`), e a página
passa a depender de JS para listar — o que empurra o catálogo estático de `packs/` para
ser o caminho primário, com o 30178 ao vivo como camada adicional, não substituta.

---

## D-017 — O site perde o atalho de arrastar-e-soltar, porque ele não existe

**Quando:** Bloco de verificação no app real, 2026-08-05
**O que:** removida do site e do `PROTOCOL-NOTES.md` §10.5 a afirmação de que arrastar o
arquivo sobre a seção Agents pula dois cliques. Em lugar dela, `IMPORT_SHORTCUT` passa a
dizer que não há atalho. Corrigido junto o rótulo do card, que é `+` e não "New agent".
**Alternativa:** deixar como estava e verificar depois — a frase não quebra build nenhum.
**Motivo:** é falsa. Duas fontes independentes concordam:
`desktop/src-tauri/tauri.conf.json:27` traz `"dragDropEnabled": false`, e a enumeração
completa de `onDrop=` em `desktop/src` devolve dez handlers, nenhum na seção Agents nem em
`AgentSnapshotImportDialog.tsx`. A enumeração **devolveu resultado**, então é ausência
confirmada e não coleta falha — a distinção de [D-014](#d-014--falha-de-coleta-nunca-é-reportada-como-ausência-de-dado).
**Custo de reversão:** uma linha, se algum dia o app ganhar drop target. Um teste em
`site/tests/rendered-html.test.mjs` falha se a promessa voltar.

**O que isto custou e por que fica registrado:** a frase nasceu de leitura de fonte,
passou por revisão de segundo leitor e **foi publicada no site**. Nenhum portão a pegou,
porque nenhum portão executava o app. O erro é da mesma família de D-014 — uma afirmação
plausível ocupando o lugar de um dado que ninguém tinha coletado. Todo item do DoD que
depende de comportamento de app e não de forma de arquivo herda a mesma suspeita até que
alguém abra o app.

---

## D-018 — Importar team OU personas, nunca os dois

**Quando:** mesmo bloco
**O que:** a orientação do site e do README do pack passa a ser: importe
`crossfire-review.team.json` **ou** os três `.agent.json`, não ambos.
**Alternativa:** não dizer nada e deixar o usuário descobrir.
**Motivo:** o import de team não deduplica. Importar as personas avulsas e depois o team
criou um segundo Forager e um segundo Adversary, com keypairs novos — oito agentes onde
se esperaria seis. É consequência direta de o `TeamSnapshot` embutir o `AgentSnapshot`
completo de cada membro (§10.2): o import materializa o que está embutido, sem procurar
por nome. Observado no app 0.5.5, não deduzido.
**Custo de reversão:** nulo — é uma frase de orientação. O usuário que errar apaga os
duplicados na mão.

---

## D-019 — O fundo do site é favo, não quadrícula

**Quando:** 2026-08-06, pedido direto do Saulo ("abelha desenha hexágono")
**O que:** a grade de fundo do `body` em `site/app/globals.css` deixa de ser
`repeating-linear-gradient` quadriculado (40px) e vira favo hexagonal — SVG inline em
`data:` URI, hexágono pointy-top com √3·R = 40px (mesmo ritmo horizontal da quadrícula
que substitui), tile 40 × 69.282.
**Alternativa:** manter a quadrícula; ou padrão pronto de terceiro (Hero Patterns, CC-BY).
**Motivo:** identidade — o projeto inteiro é apiário e o catálogo já usa células
hexagonais (`--comb-clip`); a quadrícula era o único elemento que não falava a língua.
Geometria **derivada, não copiada**, para não puxar atribuição CC-BY para dentro de um
repo Apache-2.0: cada aresta desenhada uma vez (zigue superior, verticais em x=0/x=20,
zigue do meio), sem aresta dupla, tinta uniforme.
**Custo de reversão:** trivial — restaurar o bloco anterior do `background-image`.
**Limitação assumida:** `var()` não funciona dentro de data-URI, então o hex de `--grid`
está duplicado (claro e escuro) com comentário apontando a duplicação.

---

## D-020 — Atribuição: Saulo Duttra em site, README, pack e NOTICE

**Quando:** 2026-08-06, pedido direto ("lembra de me citar sempre")
**O que:** crédito com três links (GitHub `sauloduttra`, X `sauloduttra`, Nostr
`nprofile1qqsxwact...`) no rodapé do site, seção Author no README, `author:` do
`killerbee.yaml` (flui para `catalog.json` e páginas), e NOTICE passa a
"Copyright 2026 Saulo Duttra and Killer Bee contributors". A licença NÃO mudou —
Apache-2.0 intacta; só o titular nomeado.
**⚠️ SUPOSIÇÃO embutida:** `REPO_URL` (site/app/lib/install.ts) e o default de
`SITE_URL` (layout.tsx) agora apontam para `github.com/sauloduttra/killer-bee` e
`sauloduttra.github.io/killer-bee`. O remote ainda não existe (criar é 🔴). Se o nome
final for outro, são duas linhas. O valor anterior era placeholder órfão
(`killerbee-buzz/killerbee-buzz`), que não era menos suposto — só menos útil.
**Custo de reversão:** duas linhas + o rodapé.
**Resolução (2026-08-06):** suposição confirmada — o Saulo autorizou e o remote foi
criado exatamente nesse endereço, público, com Pages em modo workflow. Deixou de ser
suposição; os valores acima são o endereço real.

---

## D-021 — As promessas de comportamento se qualificam pelo caminho de install

**Quando:** auditoria 2026-08-06 (achados CONFIRMED das dimensões honesty)
**O que:** toda afirmação pública sobre threshold/orquestração agora diz EM QUAL caminho
vale: import no desktop = só menção; `require_mention = false` só existe rodando
`buzz-acp --subscribe config --config <arquivo>` (flag corrigida — `--rules` não
existe). O README do pack, a home do site e o hint do ProfileMeter foram reescritos; a
inversão "nasce surda" (o default `false` casa TUDO, não nada) foi corrigida nas quatro
ocorrências.
**Alternativa:** remover as promessas em vez de qualificá-las.
**Motivo:** o perfil de dois eixos é real e útil — o erro era apresentar o eixo O-QUÊ
como se o caminho de 4 cliques o entregasse. Qualificar preserva a informação e a
honestidade; remover jogaria fora a metade verdadeira.
**Custo de reversão:** texto.

---

## D-022 — Link interno carrega basePath por construção, e um teste resolve cada um

**Quando:** auditoria 2026-08-06 (achado crítico CONFIRMED)
**O que:** `downloadHref()` prefixa `NEXT_PUBLIC_BASE_PATH` nos seis pontos de download;
`pages.yml` passa `base_url` (origin+path) para o metadataBase; `lib/site.ts` é a única
fonte de SITE_URL (layout, sitemap, robots). Teste novo percorre todo `.html` exportado,
exige o prefixo quando `PAGES_BASE_PATH` está setado e resolve cada href/src interno
contra `out/` — e o pages.yml roda os testes NESSE modo. Provado nos dois builds.
**Alternativa:** basePath vazio para sempre (domínio próprio na raiz).
**Custo de reversão:** o helper degrada para identidade quando o env está vazio — zero.

---

## D-023 — Emissor: conformidade com o import é lei, e nome de arquivo é validado

**Quando:** auditoria 2026-08-06
**O que:** (a) trim como o upstream (display_name/description/team.name); (b) `_SLUG`
alinhado à gramática real do d-tag (`^[a-z0-9][a-z0-9_-]{0,63}$`, sem ponto); (c)
`team.id` restrito a charset filename-safe — restrição NOSSA, mais dura que o d-tag de
team upstream (que aceita `:`, handlers/ingest.rs:1159-1162), porque o id vira nome de
arquivo no Windows; (d) frontmatter com paridade exata (delimitadores, limites, corpo
byte a byte); (e) arrays vazias omitidas como o exportador de referência; (f) caps de
5/25 MiB aplicados no build; (g) canais = "all" ou UUIDs, sem mistura.
**Alternativa:** manter validação frouxa e deixar o app rejeitar.
**Motivo:** um pack "válido" que o import recusa explode na mão do usuário final — a
pior espécie de bug para um catálogo cuja promessa é "o que você baixa, importa".
**Custo de reversão:** por regra, uma linha; o conjunto está travado por testes.

---

## D-024 — sha256 no catálogo e `killerbee inspect`

**Quando:** auditoria 2026-08-06 (oportunidades S/alto implementadas)
**O que:** build e catalog publicam `{name, sha256, bytes}` por artefato, serializando
nos MESMOS bytes (helper único); o site mostra os hashes ao lado dos downloads e o
teste de export confere hash contra arquivo servido. Novo subcomando `inspect` lê
`.agent.json/.png` e `.team.json/.png` (inclusive de terceiro — parser de PNG
endurecido) e imprime identidade, modelo, timeouts e o prompt com `--prompt`.
**Motivo:** o hash é o `x` que o card de import por chat exige
(markdownFileCard.ts:101-103) — pré-requisito da distribuição Nostr-native — e o
`inspect` é a tese "leia antes de rodar" executável, para artefato nosso ou alheio.
**Custo de reversão:** campos aditivos no catálogo; remover não quebra página antiga.

---

## D-025 — Segundo host: Cloudflare Pages, com os headers que o GitHub Pages não dá

**Quando:** 2026-08-06, pedido direto do Saulo (autenticação wrangler já existia na máquina)
**O que:** o site também vive em **https://killer-bee-4rn.pages.dev/** (projeto
`killer-bee`; o subdomínio limpo estava tomado globalmente e o Cloudflare sufixou).
`site/public/_headers` entrega CSP como **header HTTP real** — incluindo
`frame-ancestors 'none'`, que em `<meta>` é inerte — mais `nosniff`, `X-Frame-Options`
e `Referrer-Policy`. Resolve o achado #59 da auditoria. Deploy manual:
`npm run build` (com `PAGES_BASE_PATH=""` e `NEXT_PUBLIC_SITE_URL` do pages.dev) +
`npx wrangler pages deploy out --project-name=killer-bee`.
**Alternativa:** migrar de vez e desligar o GitHub Pages.
**Motivo do paralelo:** o GH Pages redeploya sozinho a cada push (CI já verde) e o
endereço `sauloduttra.github.io/killer-bee` amarra o site ao autor; o Cloudflare tem os
headers e domínio raiz (sem basePath). Manter os dois custa um comando por release.
**Custo assumido:** conteúdo duplicado em dois hosts, cada um com canonical próprio —
tolerável agora; quando houver domínio definitivo, ele vira o canonical único e o outro
host aponta para ele (uma linha de env no build de cada lado).
**Automação futura:** deploy do Cloudflare no CI exigiria `CLOUDFLARE_API_TOKEN` como
secret do repo — criação/movimentação de credencial é 🔴, fica para o Saulo decidir.

## D-026 — Governança pública: SECURITY.md, PACK-REVIEW, scaffold de contribuidor

**Quando:** 2026-08-06, gate do backlog aberto (vídeo postado), audiência pública ativa
**O que:** (1) `SECURITY.md` com modelo de ameaça em três fatos verificados
(prompt de terceiro roda com credencial do usuário; `.agent.png` é programa com cara
de imagem; import valida forma, nunca conteúdo) + canais privados de report;
(2) **private vulnerability reporting HABILITADO** no repo via API;
(3) `docs/PACK-REVIEW.md` com adversários A1-A5, checklist mantenedor/CI e o que
review NÃO garante; (4) `packs/TEMPLATE/` com `killerbee.yaml.example` — regra
canônica "pack = diretório com killerbee.yaml" agora aplicada TAMBÉM no ci.yml
(antes o glob pegava qualquer diretório); (5) JSON Schema do manifesto como contrato
de editor, com três divergências deliberadas (mais estrito) documentadas no próprio
schema; teste de concordância cruzada com 13 mutações quebradas caindo nos dois lados;
(6) ISSUE/PR templates.
**Alternativa:** SECURITY.md apontando só e-mail (sem toggle no repo); template fora
de packs/; schema como validador de runtime.
**Motivo:** governança que se demonstra era a maior peça sem dependência externa
(AUDIT 2026-08-06, prioridade média); o repo é público e PR de terceiro virou cenário
real. Schema em runtime criaria segunda verdade — como contrato de editor + teste de
concordância, não.
**Custo de reversão:** PVR = um toggle/API call; ci.yml = reverter guarda de 1 linha;
schema/template/docs = deletar arquivos. Tudo barato.
**Recibo do segundo leitor:** o verify adversarial do recon (wf_10af8aac-ae4) flagrou
3 imprecisões em citações e 1 contradição interna em PROTOCOL-NOTES:719 (provider/model
viajam no snapshot, import.rs:620-621; da config global vem a chave) — corrigida no
próprio doc com nota datada.

## D-027 — imeta pronto por artefato, com URL do próprio host

**Quando:** 2026-08-06, trilha D da sessão pós-vídeo
**O que:** `killerbee catalog --imeta-base-url <url>` faz cada entrada de arquivo do
catálogo carregar a tag imeta completa na forma do e2e upstream
(`agent-snapshot-recipient.spec.ts:118-126`): `["imeta","url …","m …","x <sha256>",
"size …","filename …"]`. O site passa `NEXT_PUBLIC_SITE_URL` no build
(prepare-data.mjs), então CADA host publica imeta apontando para os próprios
`downloads/` — GH Pages para si, Cloudflare para si — e o `x` é o mesmo sha256 nos
dois. Camada pura em `killerbee/imeta.py`; sem flag, catálogo idêntico ao anterior.
**Alternativa:** URL única canônica (acopla o emissor a um host; D-025 mantém dois),
ou imeta sem url (inútil — o card exige a tag completa e recusa `x` fora de 64 hex,
markdownFileCard.ts:101-103).
**Motivo:** é o que torna um pack POSTÁVEL como card importável em qualquer canal
Buzz sem tocar em chave: o usuário cola o link markdown + imeta; assinar/publicar o
evento continua 🔴.
**Custo de reversão:** remover flag + módulo + 10 testes; catálogo volta byte a byte.

## D-028 — Dependabot: três recusas viram regra permanente

**Quando:** 2026-08-06, primeira leva de PRs do remote público (10 PRs)
**O que:** 7 merged (5 actions + react/react-dom pareados na ordem certa). Três
recusados com `@dependabot ignore` + justificativa pública no PR:
typescript **7.0.x** (typescript-eslint aborta em TS 7.0; suporte planejado ≥ 7.1 —
ignore de MINOR, 7.1 chega como PR novo), eslint **10.x** (eslint-plugin-react dentro
do eslint-config-next chama `getFilename` removida; destrava via bump futuro do Next),
@types/node **26.x** (CI roda Node 22; types 4 majors à frente deixam o tsc abençoar
API que não existe no runtime — types acompanham o major do runtime).
**Custo de reversão:** um comentário `@dependabot unignore` por item.
**Regra que fica:** bump de types segue o runtime; major bloqueado por ecossistema é
recusado COM o link do bloqueio, nunca deixado apodrecer aberto.

## D-029 — Projeção de membro do 30178: snapshot menos o sanitizado, e nada mais

**Quando:** 2026-08-06, trilha D (contribuição ao ecossistema)
**O que:** o upstream delega o schema do corpo do 30178 ao cliente publicador
(NIP-AP.md:223; a única forma nos testes deles tem `members` VAZIO). O Killer Bee
publicou o seu: corpo `{v:1, name, description?, instructions?, members[]}` e projeção
de membro = **AgentSnapshot emitido menos {respondTo, respondToAllowlist}** —
NIP-AP.md:242 bane os pubkeys da allowlist; o enum sem a lista afirmaria política
irreconstruível. Forma do snapshot mantida DE PROPÓSITO: leitor grava a projeção como
`.agent.json` e o desktop importa sem tradução (os 8 obrigatórios presentes; os
removidos têm serde default). `killerbee event` emite o evento NÃO ASSINADO
(`created_at: 0` = template; quem assina carimba — emissor não lê relógio), valida
d-tag (≤64, sem ws/ctrl) e content ≤ 256 KiB ANTES do relay reclamar. Schema travado
por teste: corpo com respondTo NÃO valida.
**Alternativa:** inventar forma nova de membro (leitor precisaria de tradutor), ou
manter respondTo sem a lista (mentira estrutural).
**Custo de reversão:** o schema é versionado (`v: 1`); forma nova = `v: 2` + módulo.
Assinar/publicar continua 🔴 — este bloco para exatamente na fronteira.

## D-030 — Assinatura de dança rasterizada como corpo dos PNGs

**Quando:** 2026-08-06, trilha D-iii (fechando a trilha D da sessão pós-vídeo)
**O que:** o corpo dos `.agent.png`/`.team.png` deixa de ser 1×1 transparente e passa a
ser o campo de dança rasterizado (512×512 RGBA, fundo transparente) —
`killerbee/signature.py`, puro, sem Pillow. Constantes que carregam informação são as
de `site/app/lib/dance.ts`, espelhadas byte a byte e travadas por teste (inclusive os
fallbacks `?? 2.4`/`?? 4`). O CAMPO muda de escopo: o site plota o catálogo inteiro; o
artefato só conhece o próprio pack — `.agent.png` desenha o traço da persona no ângulo
que ela ocupa no pack, `.team.png` desenha todos os membros. Trig própria (Taylor,
redução a [-π/2, π/2], erro < 1e-7) porque libm varia por plataforma no último bit e um
bit muda o sha256 publicado; golden do RASTER CRU (não do PNG — zlib não é contrato).
**Consequência descoberta pelo segundo leitor:** sem avatar inline no manifesto, o
corpo é ADOTADO como avatar no import (`import.rs:242-261`); limites de adoção
2048 px / 2 MiB / 32 MiB (`snapshot_avatar.rs:5-7`) travados por teste — lado > 2048
FALHARIA o import. ⚠️ adoção como avatar ainda não vista no app rodando (D-017).
Lacuna de teste fechada na mesma rodada: determinismo build×catálogo agora compara
TAMBÉM os arquivos de team (antes só personas). Terceira cópia do HUB no site
(WaggleField hardcodava 0.18) eliminada — dance.ts exporta a constante.
**Alternativa:** copiar o corpo do upstream (avatar — não temos), SVG embutido (o
decoder upstream só fala PNG), Pillow (dependência de 10 MB para 250 linhas auditáveis).
**Custo de reversão:** remover body=... nos dois helpers de cli.py e o módulo; os PNGs
voltam a 1×1 e os hashes do catálogo se recalculam sozinhos no mesmo build.

## D-031 — B-02: a matemática entra, o schema do pack NÃO

**Quando:** 2026-08-06, backlog aberto desde o vídeo
**O que:** `killerbee/threshold.py` implementa a dinâmica de limiar reforçado como
camada pura (número → número, seed explícita, zero I/O), com `simulate_colony` para o
caso acoplado. `docs/THRESHOLD-DYNAMICS.md` traz a derivação. **O formato do pack fica
como está:** `threshold` continua constante no manifesto e nada em `build` chama o
módulo novo.
**Alternativa:** implementar o B-02 inteiro, transformando `threshold` em condição
inicial e mudando o schema agora.
**Motivo:** o próprio B-02 manda "decidir antes de congelar o formato". Decidir exige
saber como a dinâmica se comporta — e a análise mostrou que o pressuposto do item
estava errado (o ponto fixo é REPULSOR; ligar o reforço ingenuamente produz polarização,
não especialização). Mudar o schema com base numa dinâmica que ninguém rodou em agente
vivo seria congelar antes de decidir. A matemática, isolada e testada, é o que dá para
afirmar hoje sem credencial.
**Custo de reversão:** baixo — o módulo é folha, ninguém importa dele. Deletar é uma
linha de git. O caro seria o oposto: schema publicado e depois revertido.
**Recibo:** 3 derivações independentes concordando em θ* = s·(ξ/φ)^(1/n), P* = φ/(ξ+φ)
e na instabilidade (λ > 0); refutação adversarial corrigiu 3 corolários (direção do
colapso fora do domínio, limite φ→0, bordas refletoras e não absorventes) — todos
viraram teste. Um erro dimensional NOSSO (√Var/λ em vez de √(Var/λ)) foi pego pelos
testes de propriedade e está travado como regressão. Suíte: 314.

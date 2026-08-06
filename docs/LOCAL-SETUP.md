# Rodar o crossfire — runbook

**Estado: preparado até a linha vermelha. Colar chave é 🔴 e é seu.**

A descoberta que reduz o custo (PROTOCOL-NOTES §7, verificado @ ed4b3e7a): o rótulo
"Mixed models" do card de time olha **a string do modelo** de cada agente, nunca o
provider (`TeamIdentityCard.tsx:204-218`). E a credencial é por provider
(`readiness.rs:527-532`). Logo:

> **Uma chave de OpenRouter roda os três agentes.** Nenhuma conta nova.

---

## A · Quickstart: colar chave → mandar menção → o que esperar

Pré-condição já cumprida: os três agentes do `crossfire-review` foram importados no
Buzz Desktop 0.5.5 em 2026-08-05 (`[OBSERVADO]`, PROTOCOL-NOTES §10.9). Importado ≠
rodando: cada um mostra `Status: STOPPED` e aba Channels vazia até os passos abaixo.

### Passo 1 — colar a chave 🔴

Caminho de **uma chave** (recomendado): em cada um dos três agentes, configure

| Agente | Provider | Model |
|---|---|---|
| Forager | `openrouter` | `anthropic/claude-sonnet-5` |
| Adversary | `openrouter` | `openai/gpt-5` |
| Guard | `openrouter` | `deepseek/deepseek-chat` |

e forneça `OPENROUTER_API_KEY` quando o app listar o requisito faltante — o desktop
computa exatamente o que falta por agente (`readiness.rs:640-646`; a lista de
requisitos é derivada do código, o rótulo exato na UI é `[NÃO VERIFICADO]` até a
primeira rodada). Três fabricantes distintos, uma conta. O card do time continua
"Mixed models" porque as três strings diferem.

Caminho alternativo (ideal declarado do pack): três chaves nativas —
`ANTHROPIC_API_KEY`, `OPENAI_COMPAT_API_KEY`, `OPENROUTER_API_KEY` — com os modelos
originais das personas. Mesmo resultado no card; independência também operacional
(D-033 registra o trade-off).

**Regra que não se negocia:** nenhuma chave volta para chat, log, screenshot, prompt
ou arquivo versionado.

### Passo 2 — canal

Os três agentes precisam estar **no mesmo canal** de uma community: inicie cada agente
(`Start`) e adicione-os ao canal. Sem community? O relay local do Anexo B sobe uma
(seis segredos no `.env`, também 🔴 seus).

### Passo 3 — mandar UMA menção

No canal, uma única mensagem, mencionando só a Forager:

> @forager corrija esta função e poste o patch: `def median(xs): return sorted(xs)[len(xs)//2]` — quebra com lista vazia e erra em lista par.

Por que só uma menção: os perfis do pack compilam gatilhos distintos
(`killerbee.yaml` + D-007) — Forager `threshold: medium` → `require_mention = true`
(só responde chamada); Adversary e Guard `threshold: low` → `require_mention = false`
(reagem a tudo no canal). A menção acorda a Forager; o patch dela é o que acorda os
outros dois.

### Passo 4 — o que se espera ver

1. Forager responde à menção com patch + nota de design.
2. Adversary ataca o patch; Guard audita as quatro superfícies de segurança dele.
3. **A ordem entre Adversary e Guard não é garantida, nem a latência.** Nada no
   protocolo ordena respostas; pode precisar de mais de uma tomada para o vídeo.

**Como saber que falhou** (cada modo com causa provável):

| Sintoma | Causa provável |
|---|---|
| Agente não sai de `STOPPED` | requisito faltando — ver painel de readiness |
| Ninguém responde à menção | agente fora do canal, ou regra sem `require_mention` correto — conferir `acp-rules.toml` gerado |
| Forager responde, os outros dois calam | Adversary/Guard não estão no canal ou não iniciaram |
| 404 `no community is configured for this host` | armadilha do `RELAY_URL` — Anexo B, passo 3b |
| Erro de credencial no turno | chave inválida/sem crédito no OpenRouter |

### Passo 5 — registrar

Sucesso e fracasso valem igual: preencha `docs/CROSSFIRE-RUN.md` (protocolo
pré-registrado + roteiro de gravação de 90s já estão lá).

---

## B · Anexo — relay local em Docker

**Estado: runbook preparado e verificado no fonte. Não executado — parou em 🔴.**

Dois bloqueios de política, ambos legítimos e nenhum contornável por mim:

1. **Gerar credencial é vermelho.** O `.env` do compose exige seis segredos
   `CHANGE_ME`, incluindo `BUZZ_RELAY_PRIVATE_KEY` — que é a identidade criptográfica
   do relay, não uma senha de banco.
2. **O compose expõe além de `127.0.0.1` por padrão.** Corrigível, e a correção está
   abaixo — mas é decisão consciente sua, não minha.

### Pré-requisitos nesta máquina

Verificado em 2026-08-05:

| Ferramenta | Estado |
|---|---|
| Docker | `29.6.1` instalado; **daemon não subiu** durante a sessão (`docker info` pendurou >90s). Provavelmente pede interação na primeira execução. |
| Git | `2.44.0.windows.1` |
| Git Bash | `C:\Program Files\Git\bin\bash.exe` ✅ |
| Node | `22.12.0` · npm `10.9.0` |
| Python | `3.11.4` · uv `0.8.22` |
| `gh` | `2.92.0`, autenticado como `sauloduttra` |

**O shell do agente já está resolvido.** O resolvedor do Buzz procura nesta ordem
(`crates/buzz-dev-mcp/src/shell.rs:392-398`): `BUZZ_SHELL` explícito → `GIT_BASH` →
`bash.exe` no PATH **excluindo System32** (nunca resolve o launcher do WSL) → o
`bash.exe` irmão do `git.exe`. Nesta máquina o default acerta sozinho — **não defina
`BUZZ_SHELL`**.

### Passo 1 — subir o daemon do Docker

```bash
docker version
```

Se pendurar ou reclamar de `dockerDesktopLinuxEngine`, abra o Docker Desktop pela
interface uma vez e aceite o que ele pedir. Foi onde esta sessão parou.

### Passo 2 — preparar o `.env` 🔴

```bash
cd /d/EMPRESAS/buzz/_upstream/buzz/deploy/compose
cp .env.example .env
```

Seis valores `CHANGE_ME`, todos em `.env.example`:

| Variável | O que é | Como gerar |
|---|---|---|
| `RELAY_OWNER_PUBKEY` | pubkey Nostr hex de 64 chars — **sua identidade de dono** | par de chaves **descartável**, só para dev |
| `BUZZ_RELAY_PRIVATE_KEY` | chave privada hex de 64 chars — **identidade do relay** | idem, descartável |
| `BUZZ_GIT_HOOK_HMAC_SECRET` | 64 hex aleatórios | `openssl rand -hex 32` |
| `POSTGRES_PASSWORD` | senha do Postgres | `openssl rand -base64 24` |
| `REDIS_PASSWORD` | senha do Redis | `openssl rand -base64 24` |
| `BUZZ_S3_ACCESS_KEY` / `BUZZ_S3_SECRET_KEY` | credenciais do MinIO | `openssl rand -hex 16` / `-hex 32` |

**Regras que não se negociam:**

- O par de chaves é **descartável e exclusivo deste relay de desenvolvimento**. Nunca a
  chave que você usa em qualquer lugar real.
- `.env` fica em `_upstream/`, que está fora do projeto e no `.gitignore`. Não mova para
  dentro de `killer-bee/`.
- Nenhum desses valores volta para o chat, para log, para screenshot ou para prompt.

### Passo 3 — corrigir os dois defaults perigosos 🔴

#### 3a. O relay é publicado em `0.0.0.0`

`deploy/compose/compose.yml` publica assim:

```yaml
ports:
  - "${BUZZ_HTTP_PORT:-3000}:3000"
```

Sem IP de host, **o Docker liga em todas as interfaces**. Numa rede Wi-Fi compartilhada,
qualquer um na mesma rede alcança seu relay. Expor além de `127.0.0.1` é vermelho.

A sintaxe de porta do Docker aceita `IP:hostPort:containerPort`, e a interpolação do
compose deixa injetar o IP pela própria variável. No `.env`:

```bash
BUZZ_HTTP_PORT=127.0.0.1:3000
```

Isso resolve para `"127.0.0.1:3000:3000"`. Confirme antes de subir:

```bash
./run.sh config | grep -A3 'ports:'
```

Tem que aparecer `127.0.0.1`. Se aparecer só `3000:3000`, **não suba**.

#### 3b. `RELAY_URL` — a armadilha que cria comunidade fantasma

O `.env.example` traz `RELAY_URL=wss://buzz.example.com` e o `.env.example` da raiz do
repo traz `ws://localhost:3000`. **Nenhum dos dois serve.** Use:

```bash
RELAY_URL=ws://127.0.0.1:3000
```

`localhost` e `127.0.0.1` são **comunidades diferentes** — há três normalizadores
incompatíveis no código, e o que decide identidade de comunidade
(`buzz_core::tenant::normalize_host`, `crates/buzz-core/src/tenant.rs:121-137`) **não** dobra loopback.

O sintoma de errar não é o que se espera: é **404 `"relay: no community is configured for
this host"`** (`crates/buzz-relay/src/router.rs:307-308`), não 401. Se você caçar erro de
autenticação, vai procurar no lugar errado por uma hora.

A URL precisa bater **byte a byte** em todo cliente: esquema, host e porta. Trocar
qualquer um depois **cria comunidade nova**, não renomeia a antiga.

Ajuste junto, para não ficarem apontando para o domínio de exemplo:

```bash
BUZZ_DOMAIN=127.0.0.1
BUZZ_MEDIA_BASE_URL=http://127.0.0.1:3000/media
BUZZ_MEDIA_SERVER_DOMAIN=127.0.0.1
BUZZ_CORS_ORIGINS=http://127.0.0.1:3000
```

### Passo 4 — o join aberto

A §2.4 do `PROMPT.md` afirma que o relay vem com join aberto por padrão. **Meio certo, e
a distinção importa:**

- **No código, sim.** `require_relay_membership` é `false` por default —
  *"the check is a no-op and all authenticated callers are permitted regardless of auth
  method"* (`crates/buzz-relay/src/config.rs:127-128`). Lido de
  `BUZZ_REQUIRE_RELAY_MEMBERSHIP` (`config.rs:532`).
- **No bundle de produção, não.** O `deploy/compose/.env.example:17` já traz
  `BUZZ_REQUIRE_RELAY_MEMBERSHIP=true`.

Ou seja: quem sobe pelo compose de produção **já sobe fechado**, desde que não desligue.
Confirme que estas três linhas continuam no seu `.env`:

```bash
BUZZ_REQUIRE_AUTH_TOKEN=true
BUZZ_REQUIRE_RELAY_MEMBERSHIP=true
BUZZ_ALLOW_NIP_OA_AUTH=true
```

Relay fechado exige `RELAY_OWNER_PUBKEY` válido e chave de relay estável — é por isso que
os dois são obrigatórios.

### Passo 5 — subir e verificar

```bash
cd /d/EMPRESAS/buzz/_upstream/buzz/deploy/compose
./run.sh config
./run.sh start
curl -fsS http://127.0.0.1:3000/_liveness
./run.sh status
```

A stack sobe relay + Postgres 17 + Redis 7 + MinIO, todos numa bridge `buzz-net`, com
healthcheck em cada um. O relay só inicia depois que os três ficam saudáveis e o
`minio-init` cria o bucket.

`BUZZ_AUTO_MIGRATE=true` já vem no `.env.example` de produção — sem isso o banco novo
sobe vazio e o relay não encontra schema.

### Passo 6 — agente postando em canal 🔴 bloqueado

Depende do Passo 2. O harness ACP conecta por WebSocket:

```bash
BUZZ_PRIVATE_KEY=<chave de teste>  BUZZ_RELAY_URL=ws://127.0.0.1:3000  buzz-acp
```

`BUZZ_RELAY_URL` do harness é variável **diferente** do `RELAY_URL` do relay
(`.env.example:148-150` diz isso explicitamente) — mas as duas têm que apontar para a
mesma string, byte a byte, pelo motivo do passo 3b.

Critério de saída: mensagem assinada num canal, evento visível no log de auditoria.

### Erros encontrados no caminho

Registro honesto do que apareceu na sessão de 2026-08-05, que é o que vira conteúdo de
README:

1. **`docker info` pendura indefinidamente** quando o Docker Desktop nunca foi aberto na
   sessão do Windows. Não dá erro — pendura. Diagnóstico: `open //./pipe/dockerDesktopLinuxEngine:
   The system cannot find the file specified`.
2. **`bash` no PATH do Windows é o do WSL**, não o Git Bash. Não é problema para o Buzz
   (ele pula System32 de propósito), mas é problema para qualquer script seu que assuma
   `bash` = Git Bash.
3. **O compose publica em `0.0.0.0` silenciosamente.** Não há aviso, não há default
   seguro, e `docker ps` mostra `0.0.0.0:3000->3000/tcp` sem alarde.
4. **Três arquivos diferentes sugerem `RELAY_URL` diferente** — `wss://buzz.example.com`
   no compose, `ws://localhost:3000` na raiz. Os dois estão errados para uso local, e o
   segundo está errado de um jeito que só aparece como 404 mais tarde.
5. **`PowerShell Out-File` trunca o arquivo de destino antes de o comando à esquerda
   terminar.** Um comando interrompido no meio deixa arquivo vazio, não arquivo antigo.
   Custou um `LICENSE-AUDIT.md` em branco.

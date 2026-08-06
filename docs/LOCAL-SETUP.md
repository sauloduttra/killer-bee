# Ambiente local — relay Buzz em Docker

**Estado: runbook preparado e verificado no fonte. Não executado — parou em 🔴 vermelho.**

Dois bloqueios de política, ambos legítimos e nenhum contornável por mim:

1. **Gerar credencial é vermelho.** O `.env` do compose exige seis segredos
   `CHANGE_ME`, incluindo `BUZZ_RELAY_PRIVATE_KEY` — que é a identidade criptográfica
   do relay, não uma senha de banco.
2. **O compose expõe além de `127.0.0.1` por padrão.** Corrigível, e a correção está
   abaixo — mas é decisão consciente sua, não minha.

Tudo o que dá para preparar sem tocar em segredo está preparado. Você preenche seis
valores e roda.

---

## Pré-requisitos nesta máquina

Verificado em 2026-08-05:

| Ferramenta | Estado |
|---|---|
| Docker | `29.6.1` instalado; **daemon não subiu** durante a sessão (`docker info` pendurou >90s). Provavelmente pede interação na primeira execução. |
| Git | `2.44.0.windows.1` |
| Git Bash | `C:\Program Files\Git\bin\bash.exe` ✅ |
| Node | `22.12.0` · npm `10.9.0` |
| Python | `3.11.4` · uv `0.8.22` |
| `gh` | `2.92.0`, autenticado como `sauloduttra` |

### O shell do agente já está resolvido

A §4.3 do `PROMPT.md` alertava que o agente Buzz roda sob bash e que no Windows isso
exige configuração. **Não exige, nesta máquina.** O resolvedor do Buzz procura nesta
ordem (`crates/buzz-dev-mcp/src/shell.rs:392-398`):

1. `BUZZ_SHELL` explícito
2. `GIT_BASH`
3. `bash.exe` no PATH — **excluindo System32, para nunca resolver o launcher do WSL**
4. `git.exe` no PATH → o `..\bin\bash.exe` irmão

Nesta máquina o `bash` do PATH é justamente `C:\Windows\system32\bash.exe` (WSL), que o
passo 3 pula de propósito, e o Git Bash real existe. **Não defina `BUZZ_SHELL`** — o
default acerta sozinho.

---

## Passo 1 — subir o daemon do Docker

```bash
docker version
```

Se pendurar ou reclamar de `dockerDesktopLinuxEngine`, abra o Docker Desktop pela
interface uma vez e aceite o que ele pedir. Foi onde esta sessão parou.

---

## Passo 2 — preparar o `.env` 🔴

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

---

## Passo 3 — corrigir os dois defaults perigosos 🔴

### 3a. O relay é publicado em `0.0.0.0`

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

### 3b. `RELAY_URL` — a armadilha que cria comunidade fantasma

O `.env.example` traz `RELAY_URL=wss://buzz.example.com` e o `.env.example` da raiz do
repo traz `ws://localhost:3000`. **Nenhum dos dois serve.** Use:

```bash
RELAY_URL=ws://127.0.0.1:3000
```

`localhost` e `127.0.0.1` são **comunidades diferentes** — há três normalizadores
incompatíveis no código, e o que decide identidade de comunidade
(`buzz_core::tenant::normalize_host`, `tenant.rs:121-137`) **não** dobra loopback.

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

---

## Passo 4 — o join aberto

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

---

## Passo 5 — subir e verificar

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

---

## Passo 6 — agente postando em canal 🔴 bloqueado

Depende do Passo 2. O harness ACP conecta por WebSocket:

```bash
BUZZ_PRIVATE_KEY=<chave de teste>  BUZZ_RELAY_URL=ws://127.0.0.1:3000  buzz-acp
```

`BUZZ_RELAY_URL` do harness é variável **diferente** do `RELAY_URL` do relay
(`.env.example:148-150` diz isso explicitamente) — mas as duas têm que apontar para a
mesma string, byte a byte, pelo motivo do passo 3b.

Critério de saída: mensagem assinada num canal, evento visível no log de auditoria.

---

## Erros encontrados no caminho

Registro honesto do que apareceu nesta sessão, que é o que vira conteúdo de README:

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

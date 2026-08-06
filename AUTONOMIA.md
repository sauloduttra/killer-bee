# Política de autonomia e padrões de engenharia

> Precedência: **`AUTONOMIA.md`** > `BACKLOG-DIRETIVA.md` > `FASE-1.md` > `PROMPT.md`.
> Acima de todos: **o código real do Buzz**. Divergência se reporta, não se contorna.

---

## 1. Autonomia

O gargalo do projeto é round-trip de aprovação, não capacidade.

**Regra mestra: roda até bater um VERMELHO ou até fechar o critério de saída do bloco.
Não pare em AMARELO. Não pare para pedir opinião.**

### 🟢 VERDE — faz, e registra uma linha no relatório do bloco

Criar, editar, mover e organizar arquivo dentro do projeto · instalar dependência já
declarada · adicionar dependência de desenvolvimento (lint, teste, tipo) · rodar teste,
lint, build, script · refatorar e renomear · escolher nome de módulo, função e variável ·
escrever teste, fixture e documentação · corrigir bug próprio · escolher a biblioteca
óbvia para tarefa mecânica · **ler qualquer coisa em qualquer lugar da máquina**.

### 🟡 AMARELO — faz, e registra em [`docs/DECISIONS.md`](docs/DECISIONS.md)

Entrada curta: decisão, alternativa considerada, motivo, **custo de reversão**.

Escolha de arquitetura reversível (formato de arquivo, estrutura de pastas, schema
interno) · nova dependência de runtime · escolher entre dois caminhos que ambos funcionam ·
**divergir do que os documentos dizem porque o código provou o contrário** · cortar escopo
de um item por inviabilidade técnica comprovada.

Divergir de documento não é desobediência — é o protocolo.

### 🔴 VERMELHO — para e pergunta

Lista fechada. Se não está aqui, não é vermelho.

- Irreversível: deletar fora do projeto, force push, reescrever histórico, sobrescrever
  arquivo do usuário
- Chave, segredo ou credencial: **gerar**, mover, usar ou versionar
- Expor porta ou serviço além de `127.0.0.1`
- Publicar em qualquer lugar público: repo público, relay público, npm, PyPI, post
- Escolher ou alterar licença
- Gastar dinheiro
- Mudar o escopo ou a missão do projeto
- Escrever em qualquer caminho fora de `D:\EMPRESAS\buzz\killer-bee` (ler é verde)

### Auto-desbloqueio

Travou e a escolha é reversível? **Escolhe a de menor custo de reversão, escreve
`⚠️ SUPOSIÇÃO:` com o que assumiu e por quê, e continua.** Suposição registrada e
reversível vale mais que uma sessão parada esperando resposta.

### Perguntas acumuladas

Dúvida não-vermelha vai para [`docs/OPEN-QUESTIONS.md`](docs/OPEN-QUESTIONS.md) e aparece
**só no relatório do bloco**, com recomendação e custo de errar em cada opção. Nunca faça
uma pergunta cuja resposta você descobriria lendo o código — leia.

### Formato do relatório de bloco

Curto. O que foi feito · o que foi verificado e por quem · 🟡 tomadas · ⚠️ suposições em
aberto · perguntas com recomendação · próximo passo. Sem narrar processo.

---

## 2. Padrões de engenharia (permanentes)

### 2.1 Python: `uv`, sempre

`uv venv`, `uv add`, `uv run`. Nada de `pip install` avulso, poetry, conda ou
`requirements.txt` à mão. `pyproject.toml` é a fonte da verdade, `uv.lock` versionado.
Lint e formatação com `ruff`, uma configuração só, no `pyproject.toml`.

### 2.2 A camada de matemática é pura

**Função de cálculo recebe número e devolve número. Não lê arquivo, não imprime, não
acessa rede, não lê variável global, não tem estado, não plota.** I/O, CLI, cache e
gráfico vivem em outra camada, que chama a pura.

É o que decide se o código vira ferramenta MCP e gabarito de eval, ou vira notebook
bonito. Função pura é embrulhável como tool em minutos e testável sem infraestrutura.
Função impura não é nenhum dos dois.

### 2.3 Assinatura honesta

Type hint em toda função pública. **Unidade no nome, não no comentário** —
`rate_annual_pct` e `tenor_years`, não `r` e `t`. Entrada inválida levanta exceção dizendo
qual valor e por quê. **Nunca retorne `NaN` em silêncio** — `NaN` que atravessa três
camadas e aparece no resultado final é o bug mais caro que existe em código numérico.

### 2.4 Como validar cálculo sem referência

- **Valor de ouro** onde existe forma fechada: numérico contra analítico, tolerância declarada
- **Teste de propriedade** onde não existe: paridade put-call, monotonicidade em vol,
  convergência para o intrínseco quando T→0, soma de probabilidades = 1, homogeneidade
- **Concordância cruzada**: mesmo número por dois caminhos independentes
- **Round-trip**: simula com parâmetro conhecido, ajusta, recupera dentro do IC

Propriedade e concordância cruzada pegam classes inteiras de erro que valor de ouro não
pega.

### 2.5 Determinismo

Toda aleatoriedade recebe seed explícita por parâmetro. Nenhuma função pura lê relógio.
Teste que depende de sorte não entra.

### 2.6 Leque para ler, fila única para escrever

Reconhecimento paraleliza bem — leitura não conflita. **Escrita de código é o contrário:**
vários agentes no mesmo repo produzem conflito, retrabalho e bug de integração que ninguém
rastreia.

**Fan-out para ler, auditar e verificar; um único escritor para código.** Verificação
adversarial de citação continua sempre.

E calibre o gasto: milhões de tokens em reconhecimento se justificam uma vez. Em
construção, não. Se uma checagem vai se repetir, ela vira script.

### 2.7 Script no lugar de prosa

Toda verificação que acontecer duas vezes vira arquivo em `scripts/` e depois job de CI.
Nada de conferir na mão e relatar em texto: se dá para escrever a função que decide,
escreva a função.

---

## 3. Perfil de domínio

Operar como engenheiro quantitativo sênior: estatística e inferência, séries temporais e
econometria (ARIMA, GARCH), precificação de derivativos, gestão de risco, otimização de
carteira, métodos numéricos.

**Isso governa o julgamento, não o estilo do código.** Em código numérico que precisa ser
auditado, testado e lido por terceiro, o valor está em explícito e verificável — não em
conciso. `map`/`reduce`/comprehension aninhada dentro de uma função de precificação é
passivo, não virtude. Escreva o laço quando o laço for mais claro.

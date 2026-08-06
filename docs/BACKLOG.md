# Backlog

> ## 🚧 GATE DURO — nada aqui é implementado ainda
>
> Nenhum item deste arquivo é construído antes de **(a) o site existir e buildar** e
> **(b) o vídeo de 90s estar gravado**. Não prototipar "só pra ver se funciona".
>
> Ideia boa no meio da execução é o jeito mais comum de um projeto não terminar, e este
> projeto já tem escopo suficiente para morrer sozinho. Este arquivo existe para que as
> ideias parem de ocupar espaço na cabeça, não para virarem trabalho.
>
> Fonte: [`BACKLOG-DIRETIVA.md`](../BACKLOG-DIRETIVA.md) §0.

Schema por item: **mecanismo estabelecido · intuição biológica · matemática · teste mínimo
que prova ou mata · do que depende · custo de reversão.** Item sem teste mínimo não entra
aqui — vira anotação solta em outro lugar.

Toda entrada obedece à [regra de enquadramento](../BACKLOG-DIRETIVA.md#1-regra-de-enquadramento--vale-a-partir-de-já):
nome estabelecido antes do nome biológico, citação, equação escrita, de que é caso
particular, e zero alegação de novidade algorítmica. Referências verificadas em
[`BIBLIOGRAFIA.md`](BIBLIOGRAFIA.md).

---

## B-01 · Ranking por reforço estigmérgico

**Mecanismo:** Ant Colony Optimization / reforço de condutância tipo *Physarum*.
**Caso particular de:** média móvel exponencial (EWMA) aplicada às arestas de um grafo.

**Intuição biológica:** trilha percorrida engrossa, trilha abandonada atrofia. O resultado
não é o caminho mais curto — é o equilíbrio entre curto, resiliente e barato.

**Matemática:**

```
τ_ij ← (1 - ρ)·τ_ij + Δτ_ij
```

sobre as arestas do grafo do catálogo: persona instalada junto de persona, team que
referencia persona, fork. `ρ` é a taxa de evaporação; `Δτ` o reforço do período.

**Por que importa:** ranqueia por topologia, não por popularidade — resolve o cold start
sem precisar de contador de download, que a gente não tem e não quer ter.

**Teste mínimo:** com o grafo semente dos nossos próprios packs, o ranking produz ordem
**diferente e defensável** frente a ordenação alfabética.
**Depende de:** catálogo com mais de um pack e o grafo de relações existindo.
**Reversão:** trivial — é uma coluna calculada.

---

## B-02 · Limiar adaptativo no perfil scutellata

**Mecanismo:** modelo de limiar de resposta **reforçado** (division of labour em insetos
sociais). **Caso particular de:** ajuste multiplicativo/aditivo de threshold com piso e
teto — o mesmo esqueleto de um controlador integral saturado.

**Intuição biológica:** em colônia real o limiar não é constante. Executar uma tarefa
abaixa o limiar dela; não executar sobe. É assim que a divisão de trabalho se
auto-organiza sem ninguém mandar.

**Matemática:**

```
θ ← θ - ξ     ao executar a tarefa
θ ← θ + φ     ao não executar
θ ∈ [θ_min, θ_max]
```

**Consequência de desenho — e é o motivo de isto estar no topo da lista:** `threshold`
deixa de ser constante em YAML e vira **condição inicial**. Um `Guard` que recebe 👍 em
achado de segurança abaixa sozinho o próprio limiar para menção de segurança.

**Teste mínimo:** simular 200 menções sintéticas com dois perfis e mostrar convergência
para especialização.
**Depende de:** nada novo — o log assinado do relay já dá o histórico de graça.
**Reversão:** **média.** Muda o schema do pack, então **decidir antes de congelar o
formato** — hoje `docs/PROFILE-COMPILATION.md` trata `threshold` como constante.

---

## B-03 · Alocação de orçamento de eval por bandit

**Mecanismo:** Thompson sampling com piso de exploração.
**Caso particular de:** amostragem da posterior Beta-Bernoulli por braço.

**Intuição biológica:** a colônia mantém uma fração fixa de escoteiras mesmo com um bom
campo já achado — hedge contra o ambiente mudar.

**Matemática:** amostrar `θ_k ~ Beta(α_k, β_k)` por braço, escolher `argmax θ_k`, com `ε`
mínimo reservado a pack nunca testado.

**Por que importa:** resolve um problema que ninguém tinha endereçado — não dá para rodar
40 itens × N modelos × M packs a cada commit.

**Teste mínimo:** contra alocação uniforme, o bandit acha o pack ruim gastando menos.
**Depende de:** o eval existir.
**Reversão:** trivial — é o agendador.

---

## B-04 · Rede micelial no lugar do repo guarda-chuva

**Mecanismo:** conexão local em vez de índice central.
**Caso particular de:** grafo de diâmetro pequeno construído por adjacência local.

**Intuição biológica:** rede micelial não tem hub; cada nó liga nos vizinhos e a rede fica
atravessável de qualquer ponto.

**Aplicação:** cada um dos ~35 labs carrega no README o mapa **local** — `smile-lab`
aponta para `vol-lab` e `convexity-lab`, e assim por diante. Quem cair em qualquer repo
vindo de busca navega para o resto.

**Por que substitui o hub:** hub só funciona se a pessoa achar o hub.

**Teste mínimo:** partindo de três repos aleatórios, alcançar qualquer outro em no máximo
três saltos.
**Depende de:** nada.
**Reversão:** trivial.
**🔴 Nota de política:** escrever nesses repositórios é vermelho. O agente prepara o texto
e o grafo de vizinhança; a aplicação depende de OK explícito.

---

## B-05 · Hero funcional do Waggle

**Mecanismo:** recrutamento ponderado por qualidade.
**Caso particular de:** codificação visual de um vetor de alocação.

**Intuição biológica:** a *waggle dance* codifica direção pelo ângulo e distância pela
duração do trecho de requebrado; a colônia aloca forrageiras proporcionalmente ao que a
dança reporta.

**Aplicação:** no hero, ângulo = departamento e **comprimento do traço = atenção alocada**,
calculada de B-01 ou B-03 — não um número decorativo.

**Por que importa:** transforma a signature de enfeite em instrumento. É a mesma imagem,
mas passa a dizer algo verdadeiro.

**Teste mínimo:** o comprimento do traço muda quando o dado de entrada muda, e um leitor
consegue ler a ordem de alocação do desenho sem legenda numérica.
**Depende de:** B-01 ou B-03.
**Reversão:** trivial — é o dado que alimenta o desenho.

---

## B-06 · Índice de busca comprimido

**Mecanismo:** delta encoding + varint em posting lists; quantização int8 ou binária se
houver embedding.

**Por que ganha de Brotli:** compressão genérica ignora a estrutura do índice. Resolve o
defeito nº 4 do buzzdir (dataset inteiro no bundle) de forma superior a paginação, porque
mantém a busca instantânea e client-side.

**Teste mínimo:** tamanho e latência de decodificação contra o JSON cru servido com
Brotli.
**Depende de:** catálogo grande o bastante para importar. Hoje são 3 personas — não
importa.
**Reversão:** trivial.

**Sem metáfora biológica.** Passa no teste da §1 por não precisar dele.

---

## B-07 · Detector de duplicata por NCD

**Mecanismo:** Normalized Compression Distance.

**Matemática:**

```
NCD(x, y) = [ C(xy) - min(C(x), C(y)) ] / max(C(x), C(y))
```

com `C` = `zstd`. Pega o pack que é clone de outro com nome trocado e três frases mudadas.

**Por que importa:** vinte linhas de Python, roda no CI, sem infraestrutura de ML. **É o
de melhor relação valor/esforço do backlog** — e o único que não depende de nada.

**Teste mínimo:** clonar um pack nosso, alterar 5% e verificar detecção; e verificar que
dois packs legitimamente distintos do mesmo departamento **não** disparam. O segundo teste
é o que importa: detector que dispara em tudo é inútil.
**Depende de:** nada.
**Reversão:** trivial.

**Sem metáfora biológica.**

---

## B-08 · `permessage-deflate` no WebSocket do relay

**Mecanismo:** compressão de payload WebSocket **abaixo** da assinatura — o único lugar
onde comprimir é legítimo no Buzz, porque não altera os bytes assinados.

**Primeira ação:** **ler o código e verificar se o relay já habilita.** Se já habilitar,
o item morre aqui. Se não, **isto não é item nosso** — é issue no `block/buzz`.

**Teste mínimo:** não se aplica; é uma leitura de código seguida de uma decisão de para
onde mandar.
**Depende de:** nada.
**Reversão:** n/a.

**Sem metáfora biológica.**

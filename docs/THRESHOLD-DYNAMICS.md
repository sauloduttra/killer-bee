# Dinâmica do limiar reforçado — o que a álgebra diz, e o que ela corrige

> Implementação em [`killerbee/threshold.py`](../killerbee/threshold.py),
> validação em [`tests/test_threshold.py`](../tests/test_threshold.py).
> Registro da decisão: [D-031](DECISIONS.md).

## O modelo

Mecanismo com nome estabelecido: **response threshold reinforcement** — Theraulaz,
Bonabeau & Deneubourg, *Proc. R. Soc. B* **265**(1393):327-332, 1998
([BIBLIOGRAFIA](BIBLIOGRAFIA.md) registra que o DOI tem metadados errados). Nenhuma
novidade algorítmica é reivindicada aqui; a contribuição é a aplicação ao substrato do
Buzz e a análise abaixo, feita para este projeto.

```
P(agir | θ, s) = sⁿ / (sⁿ + θⁿ)     Hill de expoente n
θ ← θ − ξ   ao agir                  ξ > 0
θ ← θ + φ   ao não agir              φ > 0
θ saturado em [θ_min, θ_max]
```

## O resultado

Com o drift esperado `D(θ) = E[Δθ|θ] = φ − (ξ+φ)·P(θ)`:

| | forma fechada |
|---|---|
| ponto fixo | **θ\* = s·(ξ/φ)^(1/n)** |
| taxa de execução em θ\* | **P(θ\*) = φ/(ξ+φ)** — não depende de s nem de n |
| inclinação do drift em θ\* | **λ = n·ξ·φ / [(ξ+φ)·θ\*] > 0 sempre** |
| variância por passo em θ\* | **ξ·φ** (de (ξ+φ)²P(1−P) em P\*) |
| janela onde o ruído decide | **√(Var/λ) = √((ξ+φ)·θ\*/n)** |

**λ > 0 significa que θ\* é REPULSOR.** O drift é crescente em θ porque P é decrescente:
o feedback é positivo — agir barata agir, não agir encarece. Um agente isolado com
estímulo constante **não converge para θ\***; ele foge dele e satura numa borda.

### Como isto foi obtido

Três derivações **independentes e cegas** (rotas algébricas distintas: cancelamento
direto no drift, inversão da Hill, adimensionalização em u = θ/s), seguidas de
refutação adversarial de cada uma e de checagem numérica em `s=1, n=2, ξ=0.02, φ=0.01`.
Concordância nas duas fórmulas e na instabilidade: **3 de 3**. As refutações confirmaram
o núcleo e corrigiram material acessório — e três dessas correções entraram no código
como comportamento e como teste:

1. **Direção do colapso quando θ\* sai do domínio estava invertida.** Como D é crescente
   com zero único: θ\* ≤ θ_min ⟹ D > 0 em todo o intervalo ⟹ vai para o **teto**;
   θ\* ≥ θ_max ⟹ D < 0 ⟹ vai para o **piso**.
2. **φ → 0⁺ dá θ\* → +∞** (não 0, como uma derivação afirmou) — logo o agente desce ao
   piso. Só ξ → 0⁺ manda θ\* → 0.
3. **As bordas não são absorventes.** Em θ_min o drift é +φ(1−P) > 0 estrito; em θ_max é
   −ξ·P < 0. A cadeia segue irredutível e a massa se acumula *perto* das bordas, sem
   grudar. Há teste que falharia se o piso absorvesse (`act_rate` seria exatamente 1).

Um quarto erro foi meu, na implementação, e os testes de propriedade pegaram: a janela de
indeterminação é **√(Var/λ)**, não √Var/λ — a segunda tem dimensão [θ]·√[passo] e produz
uma janela que não encolhe quando o reforço afina. A regressão está travada.

## O que isso corrige no BACKLOG

O item B-02 pedia: *"simular 200 menções sintéticas com dois perfis e mostrar
**convergência para especialização**"*. A álgebra mostra que a palavra estava errada, e a
diferença não é semântica:

- **Não há convergência para um limiar intermediário.** Há **polarização**: cada agente
  isolado termina no piso (responde a quase tudo) ou no teto (não responde), e a
  distribuição estacionária é **bimodal**.
- Implementar B-02 ingenuamente — ligar o reforço a agentes com estímulo constante —
  produziria exatamente isso: agentes que ou respondem a tudo ou nunca respondem. Seria
  lido como bug, e seria o modelo funcionando como especificado.
- **O que falta não é ajuste de ganho, é acoplamento.** Na colônia real o estímulo é
  compartilhado e **cai quando alguém trabalha**. `simulate_colony` implementa isso.

### O que o acoplamento entrega — e o que ele não entrega

Primeira redação deste documento afirmava que o acoplamento faz "os limiares se
separarem". **Falso, e a simulação derrubou antes da publicação** (o spread entre quatro
agentes idênticos fica em ~0,02, não em separação alguma). O que se mede, com 20 seeds:

| cenário | resultado |
|---|---|
| reforço sozinho, estímulo constante | **polarização** — o agente satura numa borda |
| acoplado, agentes **idênticos** | **regulação** — demanda atendida (taxa agregada 0,515–0,521 para uma demanda de 0,50), carga repartida por igual, razão entre maior e menor taxa < 1,5 |
| acoplado, **sem** realimentação (alívio→0) | disparo: estímulo explode, todo limiar no piso, ~4 execuções por passo |
| acoplado, limiares iniciais **heterogêneos** | **divisão de trabalho** — um especialista faz ~55% e os demais ~1% cada; razão > 50x, estável entre seeds |

Ou seja: **acoplamento compra regulação; especialização precisa de heterogeneidade.**
Agentes idênticos acoplados repartem o trabalho igualmente, não se dividem em papéis.

E é aqui que a matemática toca o produto: a heterogeneidade que produz especialização é
exatamente o campo `threshold` do manifesto — `low`/`medium`/`high`, escolhido pelo autor
do pack. O modelo diz que essa escolha não é um ajuste fino de sensibilidade; é **quem
vira o especialista** quando a dinâmica ligar.

## O que NÃO foi feito, e por quê

- **O formato do pack não mudou.** `threshold` continua constante no manifesto. Ele só
  vira "condição inicial" quando existir um runtime que o mova, e mover exige agente
  vivo — série E, bloqueada em credencial. Congelar o schema agora, com base numa
  dinâmica que ninguém rodou em produção, seria o oposto do que o B-02 pedia ("decidir
  antes de congelar o formato" ≠ "congelar antes de decidir").
- **Nada disto é chamado por `build`.** É matemática isolada e testável; o emissor não
  a executa.
- **Não há validação empírica.** Os números vêm de álgebra e simulação com seed, não de
  agentes reais respondendo a menções reais. A medida que falsificaria a utilidade dos
  eixos está descrita no README (*What would falsify this*) e depende da mesma série E.

## Um requisito de desenho que cai de graça

Hoje `threshold` é um enum (`low`/`medium`/`high`) que compila para `respondTo` e para a
flag de menção; **não existe escala numérica**, e este documento não inventa uma. Mas a
dinâmica impõe uma condição a qualquer escala futura, e vale registrá-la antes de
alguém escolher números:

> **Os níveis precisam cair FORA da janela de indeterminação** — isto é,
> `|θ_nível − θ*| > √(Var/λ)` para cada um.

O motivo é direto: dentro da janela o destino do agente é decidido por sorteio, não pelo
nível. Um nível intermediário posicionado ali seria, literalmente, "não sei o que este
agente vai fazer" com cara de configuração. Com os ganhos de exemplo deste documento
(ξ=0,02, φ=0,01, n=2, s=1) a janela vai de 1,269 a 1,560 em torno de θ\*=1,414 — larga o
bastante para engolir um nível médio mal colocado.

Como a janela é `√((ξ+φ)·θ*/n)`, há duas alavancas: **reforço mais fino** (ξ, φ menores)
a estreita com a raiz da escala, e **n maior** (Hill mais abrupta) também. Isso torna a
escolha de ξ e φ um problema de desenho com critério — não um chute.

## Parâmetros, para quando houver runtime

O par (ξ, φ) tem uma leitura direta que o torna escolhível em vez de chutável:
**φ/(ξ+φ) é a taxa de trabalho alvo** no ponto de drift nulo. Querer que um agente
trabalhe em ~1/3 das oportunidades é escolher φ/ξ = 1/2. O que a razão **não** controla é
onde o agente termina — isso é decidido pela bacia inicial e pelo acoplamento.

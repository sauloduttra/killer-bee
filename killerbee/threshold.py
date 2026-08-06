"""Dinâmica do limiar de resposta REFORÇADO. Camada pura: número → número.

Esta é a variante adaptativa do modelo que o perfil scutellata instancia hoje
na forma degenerada (limiar fixo, escolhido pelo autor, compilado para campos
estáticos). Mecanismo com nome e recibo: **response threshold reinforcement**,
Theraulaz, Bonabeau & Deneubourg, *Proc. R. Soc. B* 265(1393):327-332, 1998
(ver docs/BIBLIOGRAFIA.md — o DOI tem metadados errados, e está registrado lá).

    P(agir | θ, s) = sⁿ / (sⁿ + θⁿ)        função de Hill, expoente n
    θ ← θ - ξ   ao agir                     ξ = decremento por execução
    θ ← θ + φ   ao não agir                 φ = incremento por ociosidade
    θ saturado em [θ_min, θ_max]

**O que este módulo NÃO faz:** não muda o formato do pack, não move nenhum
limiar de nenhum agente e não é chamado por `build`. É a matemática, isolada e
testável, do que o runtime faria — ligar isso a um agente vivo exige o runtime
(série E, bloqueada em credencial). Ver D-031: o `threshold` do manifesto
continua constante, e vira **condição inicial** só quando houver quem o mova.

**O resultado que muda o desenho** (derivado por três rotas independentes e
verificado adversarialmente — docs/THRESHOLD-DYNAMICS.md): o ponto fixo

    θ* = s·(ξ/φ)^(1/n)        e        P(θ*) = φ/(ξ+φ)

é **REPULSOR**, não atrator. O drift é crescente em θ, então o feedback é
positivo: agir barateia agir. Um agente isolado com estímulo constante não
converge para θ* — ele foge dele e satura numa das bordas.

O que o acoplamento (`simulate_colony`) compra, medido e não presumido:
**regulação**, não especialização. Com estímulo compartilhado que o trabalho
alivia, a demanda fica atendida em qualquer seed — mas agentes IDÊNTICOS
repartem a carga por igual, sem virar papéis distintos. A divisão de trabalho
aparece quando os limiares INICIAIS diferem: quem nasce abaixo da separatriz
vira o especialista (~55% do trabalho) e os demais ficam de reserva (~1%).
Ou seja, o `threshold` que o autor escolhe no manifesto não é ajuste fino de
sensibilidade — é quem vira o especialista. Tabela em docs/THRESHOLD-DYNAMICS.md.

Todas as funções são puras: recebem números, devolvem números. Nenhuma lê
relógio, arquivo ou global; a aleatoriedade entra por seed explícita
(AUTONOMIA §2.5).
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass


def _require_positive(**values: float) -> None:
    """Exceção que diz QUAL valor e por quê — nunca um ZeroDivisionError três
    camadas adiante (AUTONOMIA §2.3)."""
    for name, value in values.items():
        if not value > 0:
            raise ValueError(f"{name} deve ser > 0, veio {value!r}")


def act_probability(stimulus: float, threshold: float, steepness: float) -> float:
    """P(agir) = sⁿ/(sⁿ + θⁿ). Estritamente decrescente em θ.

    **Avaliada em log-espaço, não pela forma literal.** P depende apenas da
    RAZÃO θ/s — é disso que vem a homogeneidade de θ* em s. Calcular sⁿ e θⁿ
    separadamente destrói essa invariância em float: a implementação anterior
    dava 1/3 para (s=1, θ=√2, n=2) e OverflowError para (s=1e40, θ=1.09e40,
    n=8), que é o MESMO ponto matemático — e n=8 está dentro da grade que os
    testes já usavam. Com ``z = n·(ln θ - ln s)`` e a logística, os dois casos
    devolvem 1/3 (achado da revisão adversarial, 2026-08-06).

    Saturação honesta: matematicamente a imagem é o intervalo ABERTO (0, 1),
    mas em ponto flutuante ela satura em 0.0 e 1.0 quando |z| passa de ~745 —
    1/(1+e^750) não é distinguível de zero num double. Isso é limite da
    representação, não da fórmula, e está dito aqui em vez de prometido ao
    contrário.
    """
    _require_positive(stimulus=stimulus, threshold=threshold, steepness=steepness)
    z = steepness * (math.log(threshold) - math.log(stimulus))
    if z > 0.0:
        decay = math.exp(-z)
        return decay / (1.0 + decay)
    return 1.0 / (1.0 + math.exp(z))


def expected_drift(
    threshold: float,
    stimulus: float,
    decrement_on_act: float,
    increment_on_idle: float,
    steepness: float,
) -> float:
    """E[Δθ | θ] = φ - (ξ+φ)·P(θ). Crescente em θ — é a razão da repulsão."""
    _require_positive(decrement_on_act=decrement_on_act, increment_on_idle=increment_on_idle)
    probability = act_probability(stimulus, threshold, steepness)
    return increment_on_idle - (decrement_on_act + increment_on_idle) * probability


def equilibrium_threshold(
    stimulus: float,
    decrement_on_act: float,
    increment_on_idle: float,
    steepness: float,
) -> float:
    """θ* = s·(ξ/φ)^(1/n) — o zero do drift, em forma fechada.

    É separatriz, não repouso: ver `drift_slope_at_equilibrium`.
    """
    _require_positive(
        stimulus=stimulus,
        decrement_on_act=decrement_on_act,
        increment_on_idle=increment_on_idle,
        steepness=steepness,
    )
    return stimulus * (decrement_on_act / increment_on_idle) ** (1.0 / steepness)


def equilibrium_act_rate(decrement_on_act: float, increment_on_idle: float) -> float:
    """P(θ*) = φ/(ξ+φ). NÃO depende de s nem de n — só da razão dos ganhos.

    Leitura: no ponto de drift nulo, a taxa de trabalho é fixada apenas pelo
    balanço do reforço. Como o ponto é repulsor, esta é a taxa de um equilíbrio
    que o agente isolado não observa em regime — é alvo, não previsão.
    """
    _require_positive(decrement_on_act=decrement_on_act, increment_on_idle=increment_on_idle)
    return increment_on_idle / (decrement_on_act + increment_on_idle)


def drift_slope_at_equilibrium(
    stimulus: float,
    decrement_on_act: float,
    increment_on_idle: float,
    steepness: float,
) -> float:
    """λ = n·ξ·φ / [(ξ+φ)·θ*]. **Positivo para todo parâmetro positivo.**

    λ > 0 é a prova de que θ* é repulsor: o mapa médio tem multiplicador
    1 + λ > 1. Devolvemos o número (e não um booleano) porque a MAGNITUDE é a
    taxa de fuga — quanto maior, mais rápido o agente satura.

    A associação ``n·(ξ/(ξ+φ))·(φ/θ*)`` evita formar o produto ξ·φ cru, que
    fazia λ virar **exatamente 0.0** por underflow com ξ=φ=1e-165 — falsificando
    em silêncio a afirmação "λ > 0 sempre" que este módulo inteiro sustenta
    (achado da revisão adversarial). O valor exato ali é 1e-165, um float
    normal, longe do menor subnormal.
    """
    theta_star = equilibrium_threshold(stimulus, decrement_on_act, increment_on_idle, steepness)
    total = decrement_on_act + increment_on_idle
    return steepness * (decrement_on_act / total) * (increment_on_idle / theta_star)


def basin_of(
    initial_threshold: float,
    stimulus: float,
    decrement_on_act: float,
    increment_on_idle: float,
    steepness: float,
) -> str:
    """Para onde o drift MÉDIO leva: ``"floor"`` ou ``"ceiling"``.

    Como o drift é estritamente crescente com zero único em θ*, o sinal decide:
    abaixo de θ* o drift é negativo (o agente vira especialista, limiar no
    piso); acima, positivo (o agente abandona a tarefa).

    **Não há um terceiro valor "em cima da separatriz".** θ* é um conjunto de
    medida zero — nenhum float o atinge exceto por acidente — e fingir que
    existe um caso "empate" daria falsa precisão a uma resposta que o ruído
    decide. A pergunta honesta é OUTRA: a previsão vale para este θ? Quem
    responde é `noise_dominated_halfwidth`.
    """
    drift = expected_drift(
        initial_threshold, stimulus, decrement_on_act, increment_on_idle, steepness
    )
    return "ceiling" if drift > 0.0 else "floor"


def noise_dominated_halfwidth(
    stimulus: float,
    decrement_on_act: float,
    increment_on_idle: float,
    steepness: float,
) -> float:
    """Meia-largura da janela em torno de θ* onde `basin_of` não prevê nada.

    O drift se anula LINEARMENTE em θ* (coeficiente λ), enquanto a variância por
    passo ali vale exatamente ``ξφ`` — identidade exata: Var[Δθ] = (ξ+φ)²P(1-P)
    e, em P* = φ/(ξ+φ), isso colapsa em ξφ. A escala de comprimento em que a
    difusão compete com o drift é ``√(Var/λ)``, que aqui fecha numa forma
    simples e sem ξ nem φ isolados:

        √(ξφ / λ) = √((ξ+φ)·θ* / n)

    (⚠️ ``√Var/λ`` — desvio dividido por λ, em vez da raiz do quociente — é
    dimensionalmente ERRADO e foi o primeiro chute desta função: dá
    [θ]·√[passo] em vez de [θ], e produz uma janela que não encolhe quando o
    reforço afina. Os testes de propriedade pegaram; ficam como regressão.)

    **Calculada pela identidade fechada, não pela rota ξφ/λ.** A rota literal
    formava ξ·φ e λ separadamente, ambos estourando para inf com ξ=φ=1e155:
    inf/inf devolvia **nan em silêncio** — violação direta de AUTONOMIA §2.3, e
    pior que um erro, porque o guarda documentado (``|θ-θ*| > halfwidth``)
    avalia False para nan e invalidava toda previsão sem dizer nada. Com
    ξ=φ=1e154 devolvia 0.0, um número plausível errado por 77 ordens de
    grandeza. A identidade abaixo é exata (relerr 0.0 na grade benigna) e
    finita nos dois casos — achado da revisão adversarial, 2026-08-06.

    Consequência prática, e é ela que interessa ao projeto: uma previsão de
    especialização só é afirmável para agentes FORA desta janela.
    """
    theta_star = equilibrium_threshold(stimulus, decrement_on_act, increment_on_idle, steepness)
    return math.sqrt((decrement_on_act + increment_on_idle) * theta_star / steepness)


def _check_simulation_domain(
    *,
    initial_thresholds: tuple[float, ...],
    stimulus: float,
    decrement_on_act: float,
    increment_on_idle: float,
    steepness: float,
    steps: int,
    floor: float,
    ceiling: float,
) -> None:
    """Guardas comuns aos dois simuladores — UM lugar só, de propósito.

    Elas viviam duplicadas e já tinham divergido: `simulate_colony` não checava
    `floor < ceiling` nem os limiares iniciais, e NENHUM dos dois checava ξ e φ,
    que a camada pura rejeita. Resultado medido antes da correção: ξ negativo
    rodava a dinâmica invertida em silêncio, e `floor > ceiling` devolvia
    números sem erro (revisão adversarial, 2026-08-06).
    """
    _require_positive(
        stimulus=stimulus,
        decrement_on_act=decrement_on_act,
        increment_on_idle=increment_on_idle,
        steepness=steepness,
        floor=floor,
        steps=steps,
    )
    if not floor < ceiling:
        raise ValueError(f"floor ({floor}) deve ser < ceiling ({ceiling})")
    for index, initial in enumerate(initial_thresholds):
        if not floor <= initial <= ceiling:
            raise ValueError(f"limiar inicial [{index}] = {initial} fora de [{floor}, {ceiling}]")


@dataclass(frozen=True)
class Trajectory:
    """Resultado de uma simulação: onde parou e quanto trabalhou."""

    final_threshold: float
    act_count: int
    steps: int

    @property
    def act_rate(self) -> float:
        return self.act_count / self.steps if self.steps else 0.0


def simulate_agent(
    *,
    initial_threshold: float,
    stimulus: float,
    decrement_on_act: float,
    increment_on_idle: float,
    steepness: float,
    steps: int,
    floor: float,
    ceiling: float,
    seed: int,
) -> Trajectory:
    """Um agente, estímulo constante, ``steps`` decisões. Seed obrigatória.

    As bordas são **refletoras, não absorventes**: em ``floor`` o drift é
    +φ(1-P) > 0 e em ``ceiling`` é -ξ·P < 0, ambos estritos. A cadeia continua
    irredutível; a massa se acumula numa camada perto das bordas, sem grudar.
    """
    _check_simulation_domain(
        initial_thresholds=(initial_threshold,),
        stimulus=stimulus,
        decrement_on_act=decrement_on_act,
        increment_on_idle=increment_on_idle,
        steepness=steepness,
        steps=steps,
        floor=floor,
        ceiling=ceiling,
    )

    rng = random.Random(seed)
    theta = initial_threshold
    acts = 0
    for _ in range(steps):
        if rng.random() < act_probability(stimulus, theta, steepness):
            acts += 1
            theta -= decrement_on_act
        else:
            theta += increment_on_idle
        theta = min(max(theta, floor), ceiling)
    return Trajectory(final_threshold=theta, act_count=acts, steps=steps)


def simulate_colony(
    *,
    initial_thresholds: tuple[float, ...],
    demand_per_step: float,
    relief_per_act: float,
    decrement_on_act: float,
    increment_on_idle: float,
    steepness: float,
    steps: int,
    floor: float,
    ceiling: float,
    stimulus_floor: float,
    seed: int,
) -> tuple[tuple[float, ...], tuple[int, ...], float]:
    """Vários agentes sobre um estímulo COMPARTILHADO que o trabalho alivia.

    É a peça que falta no agente isolado. O estímulo cresce ``demand_per_step``
    por passo e cai ``relief_per_act`` por execução, de qualquer membro:

        s ← max(s_floor, s + demanda - alívio·(nº de execuções no passo))

    Isso fecha uma realimentação NEGATIVA por cima do feedback positivo de cada
    limiar. O resultado — verificado em teste, não presumido — é o que a
    colônia faz e o agente sozinho não fazia: os limiares se separam e a
    demanda fica atendida, em vez de todos saturarem juntos.

    Devolve ``(limiares finais, execuções por agente, estímulo final)``.
    """
    if not initial_thresholds:
        raise ValueError("colônia sem agentes")
    _require_positive(
        demand_per_step=demand_per_step,
        relief_per_act=relief_per_act,
        stimulus_floor=stimulus_floor,
    )
    _check_simulation_domain(
        initial_thresholds=tuple(initial_thresholds),
        stimulus=stimulus_floor,
        decrement_on_act=decrement_on_act,
        increment_on_idle=increment_on_idle,
        steepness=steepness,
        steps=steps,
        floor=floor,
        ceiling=ceiling,
    )

    rng = random.Random(seed)
    thresholds = list(initial_thresholds)
    acts = [0] * len(thresholds)
    stimulus = stimulus_floor
    for _ in range(steps):
        acted_now = 0
        for index, theta in enumerate(thresholds):
            if rng.random() < act_probability(stimulus, theta, steepness):
                acts[index] += 1
                acted_now += 1
                thresholds[index] = max(theta - decrement_on_act, floor)
            else:
                thresholds[index] = min(theta + increment_on_idle, ceiling)
        stimulus = max(stimulus_floor, stimulus + demand_per_step - relief_per_act * acted_now)
    return tuple(thresholds), tuple(acts), stimulus

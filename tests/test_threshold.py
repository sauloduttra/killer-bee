"""Limiar reforçado: valor de ouro, propriedades e concordância cruzada.

O módulo é matemática pura, então é validável do jeito que AUTONOMIA §2.4 pede,
sem infraestrutura nenhuma:

- **valor de ouro** — a forma fechada de θ* contra a raiz achada por bisseção
  no drift, duas rotas independentes para o mesmo número;
- **propriedade** — homogeneidade em s, monotonicidade em ξ e φ, invariância de
  P(θ*) a s e n, sinal do drift, positividade de λ (a repulsão);
- **degenerados** — os limites que a refutação adversarial corrigiu: φ→0 leva
  θ*→∞ (e o agente ao PISO), não o contrário;
- **round-trip** — simular com parâmetros conhecidos e recuperar o regime.

Os números 1.4142… e 1/3 aparecem à mão de propósito: são o caso verificado
independentemente na derivação (s=1, n=2, ξ=0.02, φ=0.01), e um teste que só
compara a implementação consigo mesma não prova nada.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from killerbee.threshold import (
    act_probability,
    basin_of,
    drift_slope_at_equilibrium,
    equilibrium_act_rate,
    equilibrium_threshold,
    expected_drift,
    noise_dominated_halfwidth,
    simulate_agent,
    simulate_colony,
)

# O caso derivado e conferido numericamente por três agentes independentes.
CASE = dict(stimulus=1.0, decrement_on_act=0.02, increment_on_idle=0.01, steepness=2.0)


# ---------------------------------------------------------------------------
# Valor de ouro: forma fechada vs raiz numérica
# ---------------------------------------------------------------------------


def _bisect_drift_zero(lo: float, hi: float, **params) -> float:
    """Acha o zero do drift por bisseção — caminho INDEPENDENTE da fórmula."""
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if expected_drift(mid, **params) < 0.0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


@pytest.mark.parametrize("stimulus", [0.5, 1.0, 3.7, 12.0])
@pytest.mark.parametrize("steepness", [1.0, 2.0, 5.0])
@pytest.mark.parametrize(("xi", "phi"), [(0.02, 0.01), (0.01, 0.02), (0.05, 0.05)])
def test_forma_fechada_bate_com_a_raiz_numerica(stimulus, steepness, xi, phi):
    """Concordância cruzada: o mesmo θ* por álgebra e por bisseção."""
    params = dict(
        stimulus=stimulus,
        decrement_on_act=xi,
        increment_on_idle=phi,
        steepness=steepness,
    )
    closed = equilibrium_threshold(**params)
    numeric = _bisect_drift_zero(1e-9, 1e6, **params)
    assert closed == pytest.approx(numeric, rel=1e-9)


def test_caso_derivado_a_mao():
    """s=1, n=2, ξ=0.02, φ=0.01 ⇒ θ*=√2 e P*=1/3, com o balanço fechando."""
    theta_star = equilibrium_threshold(**CASE)
    assert theta_star == pytest.approx(math.sqrt(2.0), rel=1e-12)

    rate = equilibrium_act_rate(CASE["decrement_on_act"], CASE["increment_on_idle"])
    assert rate == pytest.approx(1.0 / 3.0, rel=1e-12)
    # A Hill avaliada em θ* devolve a MESMA taxa — as duas fórmulas são uma só.
    assert act_probability(CASE["stimulus"], theta_star, CASE["steepness"]) == pytest.approx(
        rate, abs=1e-15
    )
    # Balanço ξ·P = φ·(1-P): o drift é nulo por construção.
    assert CASE["decrement_on_act"] * rate == pytest.approx(
        CASE["increment_on_idle"] * (1.0 - rate), abs=1e-15
    )
    assert expected_drift(theta_star, **CASE) == pytest.approx(0.0, abs=1e-15)


# ---------------------------------------------------------------------------
# Propriedades
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("factor", [0.25, 2.0, 10.0])
def test_theta_estrela_e_homogeneo_de_grau_1_no_estimulo(factor):
    """θ*(λs) = λ·θ*(s): escalar o estímulo escala o limiar de equilíbrio."""
    base = equilibrium_threshold(**CASE)
    scaled = equilibrium_threshold(**{**CASE, "stimulus": CASE["stimulus"] * factor})
    assert scaled == pytest.approx(base * factor, rel=1e-12)


@pytest.mark.parametrize("steepness", [0.5, 1.0, 2.0, 8.0])
@pytest.mark.parametrize("stimulus", [0.3, 1.0, 9.0])
def test_taxa_de_equilibrio_nao_depende_de_s_nem_de_n(steepness, stimulus):
    """P(θ*) = φ/(ξ+φ) — o balanço do reforço fixa a taxa sozinho."""
    theta_star = equilibrium_threshold(
        stimulus, CASE["decrement_on_act"], CASE["increment_on_idle"], steepness
    )
    assert act_probability(stimulus, theta_star, steepness) == pytest.approx(
        equilibrium_act_rate(CASE["decrement_on_act"], CASE["increment_on_idle"]),
        rel=1e-12,
    )


def test_xi_igual_phi_poe_a_separatriz_sobre_o_estimulo():
    """ξ=φ ⇒ θ*=s e P*=1/2. É separatriz, não repouso — o teste de basin_of
    logo abaixo é quem impede a leitura errada de "o limiar se acomoda em s"."""
    theta_star = equilibrium_threshold(2.5, 0.03, 0.03, 4.0)
    assert theta_star == pytest.approx(2.5, rel=1e-12)
    assert equilibrium_act_rate(0.03, 0.03) == pytest.approx(0.5, rel=1e-12)


def test_theta_estrela_cresce_com_xi_e_cai_com_phi():
    base = equilibrium_threshold(**CASE)
    mais_xi = equilibrium_threshold(**{**CASE, "decrement_on_act": 0.04})
    mais_phi = equilibrium_threshold(**{**CASE, "increment_on_idle": 0.02})
    assert mais_xi > base > mais_phi


@pytest.mark.parametrize("steepness", [0.5, 1.0, 2.0, 7.0])
@pytest.mark.parametrize(("xi", "phi"), [(0.02, 0.01), (0.01, 0.05), (0.1, 0.1)])
@pytest.mark.parametrize("stimulus", [0.2, 1.0, 6.0])
def test_o_ponto_fixo_e_sempre_repulsor(stimulus, xi, phi, steepness):
    """λ > 0 em toda a grade — a instabilidade não é um caso particular, é o
    comportamento do modelo. Se algum dia isto falhar, a dinâmica mudou."""
    assert drift_slope_at_equilibrium(stimulus, xi, phi, steepness) > 0.0


@pytest.mark.parametrize("steepness", [1.0, 3.0])
def test_o_drift_troca_de_sinal_ao_cruzar_theta_estrela(steepness):
    params = {**CASE, "steepness": steepness}
    theta_star = equilibrium_threshold(**params)
    assert expected_drift(theta_star * 0.9, **params) < 0.0
    assert expected_drift(theta_star * 1.1, **params) > 0.0


def test_basin_of_separa_as_duas_bacias():
    theta_star = equilibrium_threshold(**CASE)
    assert basin_of(theta_star * 0.5, **CASE) == "floor"
    assert basin_of(theta_star * 2.0, **CASE) == "ceiling"


def test_a_janela_de_indeterminacao_contem_theta_estrela_e_e_finita():
    """A pergunta honesta não é "estou EM θ*?" (medida zero, nenhum float bate)
    e sim "estou perto o bastante para o ruído decidir?". A meia-largura é
    √(Var/λ); a previsão de bacia só vale fora dela."""
    theta_star = equilibrium_threshold(**CASE)
    halfwidth = noise_dominated_halfwidth(**CASE)
    assert halfwidth > 0.0
    # A janela é uma fração do próprio θ*, não o domínio inteiro: previsão
    # longe da separatriz continua significando alguma coisa.
    assert halfwidth < theta_star
    # E os pontos que os testes de bacia usam estão fora dela.
    assert abs(theta_star * 0.5 - theta_star) > halfwidth
    assert abs(theta_star * 2.0 - theta_star) > halfwidth


def test_janela_encolhe_quando_o_reforco_fica_mais_fino():
    """Passos menores ⇒ ruído e fuga menores, mas NÃO na mesma proporção:
    √(Var/λ) = √((ξ+φ)θ*/n) cai com a raiz da escala do reforço, e a previsão
    determinística passa a valer mais perto da separatriz. (A forma errada,
    √Var/λ, é invariante à escala e este teste a rejeita.)"""
    grande = noise_dominated_halfwidth(1.0, 0.02, 0.01, 2.0)
    pequeno = noise_dominated_halfwidth(1.0, 0.002, 0.001, 2.0)
    assert pequeno < grande


# ---------------------------------------------------------------------------
# Degenerados — os limites que a refutação adversarial corrigiu
# ---------------------------------------------------------------------------


def test_phi_minusculo_manda_theta_estrela_para_cima_e_o_agente_para_o_piso():
    """φ→0⁺ ⇒ θ*→+∞. Uma das derivações afirmou θ*→0 e a refutação pegou: com
    o ponto fixo ACIMA do domínio, o drift é negativo em todo lugar e o agente
    desce até o piso. O erro de sinal invertia a conclusão inteira."""
    theta_star = equilibrium_threshold(1.0, 0.02, 1e-9, 2.0)
    assert theta_star > 1e3
    assert (
        basin_of(5.0, stimulus=1.0, decrement_on_act=0.02, increment_on_idle=1e-9, steepness=2.0)
        == "floor"
    )


def test_xi_minusculo_manda_theta_estrela_para_zero_e_o_agente_para_o_teto():
    theta_star = equilibrium_threshold(1.0, 1e-9, 0.02, 2.0)
    assert theta_star < 1e-3
    assert (
        basin_of(0.5, stimulus=1.0, decrement_on_act=1e-9, increment_on_idle=0.02, steepness=2.0)
        == "ceiling"
    )


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(stimulus=0.0, decrement_on_act=0.02, increment_on_idle=0.01, steepness=2.0),
        dict(stimulus=1.0, decrement_on_act=0.0, increment_on_idle=0.01, steepness=2.0),
        dict(stimulus=1.0, decrement_on_act=0.02, increment_on_idle=-1.0, steepness=2.0),
        dict(stimulus=1.0, decrement_on_act=0.02, increment_on_idle=0.01, steepness=0.0),
    ],
)
def test_parametro_nao_positivo_levanta_dizendo_qual(kwargs):
    with pytest.raises(ValueError, match="deve ser > 0"):
        equilibrium_threshold(**kwargs)


# ---------------------------------------------------------------------------
# Simulação: o agente isolado POLARIZA
# ---------------------------------------------------------------------------

SIM = dict(
    stimulus=1.0,
    decrement_on_act=0.02,
    increment_on_idle=0.01,
    steepness=2.0,
    steps=4000,
    floor=0.1,
    ceiling=4.0,
)


def test_agente_isolado_termina_polarizado_nao_no_meio():
    """O 'teste mínimo' que o backlog pedia — com o resultado que a matemática
    prevê, e não o que o backlog supunha. Nenhum agente fica perto de θ*."""
    theta_star = equilibrium_threshold(**CASE)
    finals = [
        simulate_agent(initial_threshold=theta_star, seed=seed, **SIM).final_threshold
        for seed in range(40)
    ]
    near_star = [t for t in finals if abs(t - theta_star) < 0.25 * theta_star]
    assert not near_star, f"{len(near_star)} agentes pararam perto da separatriz"
    assert all(t < 0.5 or t > 3.0 for t in finals)
    # E as DUAS bacias são visitadas: partir da separatriz não decide o destino.
    assert any(t < 0.5 for t in finals) and any(t > 3.0 for t in finals)


def test_quem_comeca_abaixo_da_separatriz_vira_especialista():
    theta_star = equilibrium_threshold(**CASE)
    trajectory = simulate_agent(initial_threshold=theta_star * 0.6, seed=7, **SIM)
    assert trajectory.final_threshold < 0.5
    assert trajectory.act_rate > 0.8  # limiar no piso = responde a quase tudo


def test_quem_comeca_acima_da_separatriz_abandona_a_tarefa():
    theta_star = equilibrium_threshold(**CASE)
    trajectory = simulate_agent(initial_threshold=theta_star * 1.6, seed=7, **SIM)
    assert trajectory.final_threshold > 3.0
    assert trajectory.act_rate < 0.2


def test_a_simulacao_e_deterministica_por_seed():
    a = simulate_agent(initial_threshold=1.0, seed=99, **SIM)
    b = simulate_agent(initial_threshold=1.0, seed=99, **SIM)
    assert a == b


def test_bordas_sao_refletoras_nao_absorventes():
    """Em floor o drift é +φ(1-P) > 0: a borda empurra de volta. Um agente
    preso lá teria act_rate == 1.0 exato, o que NÃO acontece."""
    trajectory = simulate_agent(initial_threshold=0.1, seed=3, **SIM)
    assert trajectory.act_rate < 1.0
    assert trajectory.act_count > 0


# ---------------------------------------------------------------------------
# Simulação: a COLÔNIA acoplada divide o trabalho
# ---------------------------------------------------------------------------


COLONY = dict(
    demand_per_step=0.5,
    relief_per_act=1.0,
    decrement_on_act=0.02,
    increment_on_idle=0.01,
    steepness=2.0,
    steps=4000,
    floor=0.1,
    ceiling=4.0,
    stimulus_floor=0.05,
)


@pytest.mark.parametrize("seed", range(8))
def test_acoplamento_REGULA_a_demanda_em_qualquer_seed(seed):
    """O que o acoplamento entrega, e é robusto: a demanda fica ATENDIDA.

    Com demanda 0,5/passo aliviada em 1,0 por execução, o sistema precisa de
    ~0,5 execuções por passo no agregado. O estímulo compartilhado sobe até que
    isso aconteça e para — é um controlador integral, não uma coincidência de
    seed. Medido em 20 seeds durante o desenvolvimento: 0,515 a 0,521.
    """
    _, acts, _ = simulate_colony(initial_thresholds=(1.0,) * 4, seed=seed, **COLONY)
    aggregate_rate = sum(acts) / COLONY["steps"]
    assert 0.49 < aggregate_rate < 0.56, f"demanda não regulada: {aggregate_rate:.3f}"


def test_sem_realimentacao_o_sistema_dispara_em_vez_de_regular():
    """O controle que prova que a regulação vem do ACOPLAMENTO e não do
    reforço: com alívio ~0, o estímulo cresce sem limite, todo limiar desaba no
    piso e os agentes trabalham em toda oportunidade."""
    thresholds, acts, stimulus = simulate_colony(
        initial_thresholds=(1.0,) * 4,
        seed=11,
        **{**COLONY, "relief_per_act": 1e-4},
    )
    assert sum(acts) / COLONY["steps"] > 3.5  # ~4 execuções por passo: todos, sempre
    assert all(t <= 0.2 for t in thresholds)
    assert stimulus > 100.0


@pytest.mark.parametrize("seed", [5, 11, 21])
def test_heterogeneidade_inicial_vira_DIVISAO_de_trabalho(seed):
    """A especialização não emerge de agentes idênticos — ela vem de onde cada
    um COMEÇA, e o acoplamento a preserva.

    Quatro agentes com o mesmo (ξ, φ) e limiares iniciais distintos: o que
    nasce abaixo da separatriz vira o especialista e carrega o trabalho; os
    demais viram reserva, porque o estímulo cai antes de puxá-los. A razão
    entre a maior e a menor taxa passa de 50x, e isso se repete entre seeds.

    É o resultado que amarra a matemática ao produto: `threshold` no manifesto
    (low/medium/high, escolha do autor) É essa condição inicial.
    """
    _, acts, _ = simulate_colony(initial_thresholds=(0.3, 1.0, 2.0, 3.5), seed=seed, **COLONY)
    rates = sorted(a / COLONY["steps"] for a in acts)
    assert rates[-1] > 0.4, f"nenhum especialista emergiu: {rates}"
    assert rates[0] < 0.05, f"nenhuma reserva ficou: {rates}"
    assert rates[-1] / rates[0] > 20.0
    # E a demanda continua atendida — especializar não é abandonar o trabalho.
    assert 0.49 < sum(rates) < 0.65


def test_agentes_identicos_compartilham_em_vez_de_especializar():
    """O contraste que impede a leitura errada do teste acima: partindo todos
    do mesmo ponto, o acoplamento reparte o trabalho de forma EQUILIBRADA. A
    divisão de trabalho precisa de heterogeneidade; regulação, não."""
    _, acts, _ = simulate_colony(initial_thresholds=(1.0,) * 4, seed=11, **COLONY)
    rates = sorted(a / COLONY["steps"] for a in acts)
    assert rates[-1] / rates[0] < 1.5, f"esperava carga equilibrada, veio {rates}"


def test_colonia_sem_agentes_e_erro():
    with pytest.raises(ValueError, match="sem agentes"):
        simulate_colony(
            initial_thresholds=(),
            demand_per_step=0.5,
            relief_per_act=1.0,
            decrement_on_act=0.02,
            increment_on_idle=0.01,
            steepness=2.0,
            steps=10,
            floor=0.1,
            ceiling=4.0,
            stimulus_floor=0.05,
            seed=1,
        )

"""O grafo do hero: geometria pura, invariantes garantidos por construção.

Regra do repo (D-032): cada teste nomeia a mutação que mata. E uma regra que
vale especialmente aqui (o juiz de buildability do painel de design insistiu
nela): **invariante geométrico duro não pode ser portão de build**. Editar um
prompt não pode derrubar o deploy porque dois hexágonos ficaram 0,01 unidade
mais perto. Por isso o teste exige o invariante que o algoritmo GARANTE (célula
não sobrepõe célula) e apenas RELATA o alvo mais forte.
"""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from ncd_catalog import (  # noqa: E402
    load_catalog_bodies,
    pairwise_ncd,
    robust_threshold,
    zstd_size_bytes,
)
from ncd_graph import (  # noqa: E402
    CENTER_X,
    CENTER_Y,
    FRAME_RADIUS,
    HIT_PAD,
    R_MAX,
    R_MIN,
    W_MIN,
    build_graph,
    fit_to_frame,
    hatch_segment,
    hexagon_path,
    initial_positions,
    min_clearance,
    radius_from_recruitment,
    relax,
    separate,
    width_from_ncd,
)


@pytest.fixture(scope="module")
def real_graph() -> dict:
    """O grafo do catálogo de verdade. Gerado UMA vez (~1 s de zstd)."""
    return build_graph(ROOT / "packs", ROOT / "site" / "data" / "catalog.json")


# ── escalas: a chave impressa não pode divergir do desenho ───────────────────


def test_raio_monotonico_e_dentro_da_faixa():
    """Mata: inverter a curva, ou remapear para fora de [R_MIN, R_MAX] — o
    hexágono de recruitment 1 tem que ser o menor e o de 32 o maior."""
    radii = [radius_from_recruitment(r) for r in (1, 2, 4, 8, 16, 32)]
    assert radii == sorted(radii)
    assert radii[0] == pytest.approx(R_MIN)
    assert radii[-1] == pytest.approx(R_MAX)


def test_raio_comprime_o_topo_da_faixa():
    """A raiz existe para 1->4 pesar mais que 28->32. Mata: trocar por linear
    (aí os dois saltos seriam iguais)."""
    baixo = radius_from_recruitment(4) - radius_from_recruitment(1)
    alto = radius_from_recruitment(32) - radius_from_recruitment(29)
    assert baixo > alto * 2


def test_largura_cresce_conforme_afunda_abaixo_do_limiar():
    """Mata: inverter o sinal — o par MAIS próximo tem que ser o traço mais
    grosso, e o que encosta no limiar, o mais fino."""
    t, lo = 0.8376, 0.7620
    assert width_from_ncd(lo, t, lo) > width_from_ncd(0.80, t, lo)
    assert width_from_ncd(0.80, t, lo) > width_from_ncd(t, t, lo)
    assert width_from_ncd(t, t, lo) == pytest.approx(W_MIN)


def test_largura_sem_faixa_devolve_piso_em_vez_de_dividir_por_zero():
    """Mata: remover o guarda — limiar == mínimo daria ZeroDivisionError ou nan
    silencioso, e nan atravessando três camadas é o bug mais caro que existe."""
    assert width_from_ncd(0.8, 0.8, 0.8) == pytest.approx(W_MIN)


# ── hexágono ─────────────────────────────────────────────────────────────────


def test_hexagono_tem_seis_vertices_e_fecha():
    """Mata: emitir polígono aberto, ou com 5/7 lados."""
    d = hexagon_path(10.0, 20.0, 4.0)
    assert d.endswith(" Z")
    assert d.count("L") == 5 and d.count("M") == 1


def test_hexagono_e_regular():
    """Todo vértice à mesma distância do centro. Mata: usar r/2 onde vai
    r·√3/2 (o hexágono viraria um losango achatado)."""
    r = 7.0
    d = hexagon_path(0.0, 0.0, r)
    coords = [(float(mx), float(my)) for mx, my in re.findall(r"[ML](-?\d+\.\d+) (-?\d+\.\d+)", d)]
    assert len(coords) == 6
    for x, y in coords:
        assert math.hypot(x, y) == pytest.approx(r, abs=0.01)


# ── layout ───────────────────────────────────────────────────────────────────


def test_posicao_inicial_e_o_hero_antigo_nao_um_sorteio():
    """A condição inicial é um círculo derivado do catálogo. Mata: trocar por
    random (o teste de determinismo abaixo também mataria, este nomeia o
    porquê) — e mata colocar todo mundo no mesmo ponto."""
    pos = initial_positions(6, [1, 4, 8, 16, 32, 2])
    assert len(pos) == len(set(pos)) == 6
    for x, y in pos:
        assert math.hypot(x - CENTER_X, y - CENTER_Y) > 20.0


def test_relaxacao_e_deterministica():
    """Duas execuções, resultado idêntico. Mata: introduzir random, relógio,
    ou iterar sobre um set (ordem não determinística)."""
    rec = [1, 3, 5, 8, 12, 2, 7, 4]
    radii = [radius_from_recruitment(r) for r in rec]
    edges = [(0, 1, 1.0), (1, 2, 0.6), (3, 4, 0.9), (5, 6, 0.3)]
    a = relax(initial_positions(len(rec), rec), radii, edges, iterations=60)
    b = relax(initial_positions(len(rec), rec), radii, edges, iterations=60)
    assert a == b


def test_relaxacao_aproxima_quem_tem_aresta():
    """O invariante que faz o desenho SIGNIFICAR algo: par medido acaba mais
    perto que a média.

    Os pares ligados são ANTIPODAIS no círculo inicial — a maior distância
    possível de partida. Só a atração pode trazê-los para perto. A primeira
    versão deste teste ligava índices vizinhos, que já nascem colados no
    círculo: ele passava verde com a atração zerada, ou seja, não provava nada.
    Mata: zerar a atração, inverter o sinal dela, ou aplicá-la a todos os pares.
    """
    rec = [4] * 8
    radii = [radius_from_recruitment(r) for r in rec]
    antipodais = [(0, 4, 1.0), (1, 5, 1.0), (2, 6, 1.0), (3, 7, 1.0)]
    inicio = initial_positions(len(rec), rec)
    pos = relax(inicio, radii, antipodais, iterations=200)

    def dist(p, i: int, j: int) -> float:
        return math.hypot(p[i][0] - p[j][0], p[i][1] - p[j][1])

    # Partem como os pares MAIS distantes do conjunto...
    inicial_ligados = sum(dist(inicio, i, j) for i, j, _ in antipodais) / 4
    inicial_todos = sum(dist(inicio, i, j) for i in range(8) for j in range(i + 1, 8)) / 28
    assert inicial_ligados > inicial_todos

    # ...e terminam como os mais próximos. Só a atração explica a inversão.
    final_ligados = sum(dist(pos, i, j) for i, j, _ in antipodais) / 4
    final_todos = sum(dist(pos, i, j) for i in range(8) for j in range(i + 1, 8)) / 28
    assert final_ligados < final_todos


def test_layout_nunca_produz_nan_nem_infinito():
    """AUTONOMIA §2.3: nan que atravessa camadas é o bug mais caro. Mata:
    remover o piso de distância (dois nós coincidentes dividiriam por zero)."""
    rec = [1, 1, 1, 1]
    radii = [radius_from_recruitment(r) for r in rec]
    # Todos no MESMO ponto: o caso degenerado, forçado de propósito.
    pos = relax([(CENTER_X, CENTER_Y)] * 4, radii, [(0, 1, 1.0)], iterations=40)
    for x, y in pos:
        assert math.isfinite(x) and math.isfinite(y)


def test_enquadramento_e_semelhanca_pura():
    """Escalar para preencher o quadro não pode reordenar vizinhança. Mata:
    escalar x e y por fatores diferentes, ou clampar em vez de escalar."""
    pos = [(150.0, 140.0), (160.0, 138.0), (200.0, 190.0)]
    radii = [3.4, 3.4, 3.4]
    fitted = fit_to_frame(pos, radii)

    def d(p, i, j):
        return math.hypot(p[i][0] - p[j][0], p[i][1] - p[j][1])

    razao = d(fitted, 0, 1) / d(pos, 0, 1)
    assert d(fitted, 0, 2) / d(pos, 0, 2) == pytest.approx(razao, rel=1e-9)
    assert d(fitted, 1, 2) / d(pos, 1, 2) == pytest.approx(razao, rel=1e-9)


def test_separacao_desfaz_sobreposicao():
    """A função em si. Mata: passe que não empurra (ou que empurra para dentro)."""
    radii = [6.0, 6.0]
    juntos = [(160.0, 138.0), (162.0, 138.0)]
    assert min_clearance(juntos, radii) < 0
    apartados = separate(juntos, radii)
    assert min_clearance(apartados, radii) > 0


def test_alvo_de_toque_cheio_no_catalogo_de_hoje(real_graph: dict):
    """Canário do alvo de toque, e a mutação que ele mata.

    A separação é o que garante folga para os alvos de toque não se
    sobreporem. **Ela degrada com elegância**: se as varreduras não alcançarem
    o alvo, o gerador ENCOLHE o padding em vez de falhar — o desenho continua
    correto, os alvos é que ficam menores. Por isso "não sobrepõe" é
    inviolável por construção e não serve de teste.

    O que serve é este: no catálogo de hoje o gerador alcança o padding CHEIO.
    Medido: com o passe de separação, folga 7,0 e padding 3,5; sem ele, 4,93 e
    2,47 — alvo de toque 30% menor, em silêncio. Mata: remover a chamada a
    `separate` de dentro de `relax`.

    **Se este teste falhar, não é bug: é aviso.** Quer dizer que o catálogo
    ficou denso demais para a moldura atual e os alvos de toque encolheram.
    Conserto: aumentar FRAME_RADIUS, ou aceitar o padding menor mudando
    HIT_PAD — decisão de desenho, com o número na mão.
    """
    assert real_graph["meta"]["hitPad"] == pytest.approx(HIT_PAD), (
        f"padding do alvo de toque caiu para {real_graph['meta']['hitPad']} "
        f"(folga {real_graph['meta']['minClearance']}): o catálogo não cabe mais "
        f"na moldura com {HIT_PAD} de folga por lado"
    )


def test_hatch_e_perpendicular_a_aresta():
    """O tique do redline tem que cruzar a linha, não acompanhá-la. Mata: usar
    a direção da aresta em vez da normal."""
    h = hatch_segment(0.0, 0.0, 10.0, 0.0)
    assert h["x1"] == pytest.approx(5.0) and h["x2"] == pytest.approx(5.0)
    assert h["y1"] != h["y2"]


# ── contra o catálogo real ───────────────────────────────────────────────────


def test_grafo_real_tem_um_no_por_persona(real_graph: dict):
    """48 = o catálogo depois do corte da opção 1 (D-036). Mata: perder
    persona no join entre catalog.json e packs/."""
    assert real_graph["meta"]["personas"] == 48
    assert len(real_graph["nodes"]) == 48
    assert len({n["key"] for n in real_graph["nodes"]}) == 48


def test_arestas_sao_exatamente_os_pares_abaixo_do_limiar(real_graph: dict):
    """O predicado desenhado e o predicado declarado são O MESMO.

    "Toda aresta está abaixo do limiar" é metade do contrato e passa verde com
    um top-50 (a versão anterior deste teste checava só isso e a mutação
    sobreviveu). A outra metade é a que importa: **todo par abaixo do limiar
    tem aresta**. Recontamos do zero, com a mesma medição.
    Mata: trocar o filtro por top-N, ou imprimir um limiar diferente do que
    filtra.
    """
    meta = real_graph["meta"]
    assert len(real_graph["edges"]) == meta["edges"]
    for edge in real_graph["edges"]:
        assert edge["ncd"] < meta["threshold"]

    bodies = load_catalog_bodies(ROOT / "packs")
    catalogo = {n["key"] for n in real_graph["nodes"]}
    bodies = {k: v for k, v in bodies.items() if k in catalogo}
    valores = [ncd for ncd, _, _ in pairwise_ncd(bodies, zstd_size_bytes)]
    _, _, limiar = robust_threshold(valores)
    assert len(valores) == meta["pairs"]
    assert sum(1 for v in valores if v < limiar) == meta["edges"], (
        "há par abaixo do limiar que o desenho não liga — o predicado desenhado "
        "deixou de ser o predicado declarado"
    )


def test_a_capa_e_a_auditoria_publicam_o_MESMO_numero(real_graph: dict):
    """A home imprime a auditoria, não uma segunda medição dela.

    A versão anterior deste teste calculava o limiar esperado numa lista
    sintética de quatro elementos e **jogava o resultado fora** — passava verde
    com `threshold = 0.8376` hardcodado no gerador E com a definição trocada de
    3 para 2,5 MADs (medido: 92 arestas sob 0,8441, com a auditoria ainda
    publicando 71 sob 0,8376). Um teste que nomeia uma mutação que não mata é
    pior que nenhum: dá cobertura de mentira.

    O que mata a deriva de DEFINIÇÃO é comparar com o número publicado. Se este
    teste falhar, a capa e a auditoria discordaram: regenere a auditoria
    (`uv run python scripts/ncd_catalog.py`) ou reverta o limiar — mas não
    deixe as duas no ar.
    """
    tabela = (ROOT / "docs" / "CATALOG-AUDIT.md").read_text(encoding="utf-8")
    secao = tabela[tabela.index("## 8. Adendo pós-corte") :]
    linha = re.search(
        r"\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*([\d,]+)\s*\|\s*([\d,]+)\s*\|\s*([\d,]+)\s*\|"
        r"\s*([\d,]+)\s*\|\s*(\d+)\s*\|",
        secao,
    )
    assert linha, "a tabela do adendo §8 sumiu do CATALOG-AUDIT — o pino perdeu o poste"

    def num(group: int) -> float:
        return float(linha.group(group).replace(",", "."))

    meta = real_graph["meta"]
    publicado = {
        "personas": int(linha.group(1)),
        "pairs": int(linha.group(2)),
        "ncdMin": num(3),
        "median": num(4),
        "threshold": num(6),
        "edges": int(linha.group(7)),
    }
    for campo, esperado in publicado.items():
        assert meta[campo] == pytest.approx(esperado, abs=5e-5), (
            f"a capa diz {campo}={meta[campo]} e o CATALOG-AUDIT §8 publica {esperado}"
        )


def test_isolada_nao_anima_e_conectada_anima(real_graph: dict):
    """Isolada já estava lá sem parente: animar a entrada dela contaria uma
    chegada tardia que não aconteceu. Mata: dar delay a todo mundo."""
    for node in real_graph["nodes"]:
        if node["isolated"]:
            assert node["degree"] == 0
            assert node["delayMs"] is None
        else:
            assert node["degree"] > 0
            assert isinstance(node["delayMs"], int)


def test_ordem_do_tempo_e_a_ordem_do_ranking(real_graph: dict):
    """Arestas se ligam do par mais próximo ao mais distante. Mata: embaralhar
    o delay, ou ordená-lo por índice de nó em vez de por NCD."""
    edges = real_graph["edges"]
    delays = [e["delayMs"] for e in edges]
    ncds = [e["ncd"] for e in edges]
    assert delays == sorted(delays)
    assert ncds == sorted(ncds)


def test_celulas_nao_se_sobrepoem(real_graph: dict):
    """O invariante GARANTIDO por construção (não o alvo forte). Mata: remover
    o passe de separação."""
    assert real_graph["meta"]["minClearance"] > 0


def test_tudo_dentro_do_viewbox(real_graph: dict):
    """Mata: escalar para além da moldura — nó fora do viewBox some do desenho
    sem erro nenhum."""
    meta = real_graph["meta"]
    for node in real_graph["nodes"]:
        assert node["x"] - node["r"] >= 0 and node["x"] + node["r"] <= meta["viewBoxW"]
        assert node["y"] - node["r"] >= 0 and node["y"] + node["r"] <= meta["viewBoxH"]
        assert math.hypot(node["x"] - CENTER_X, node["y"] - CENTER_Y) <= FRAME_RADIUS + 0.01


def test_redline_so_abaixo_do_controle_e_sempre_com_tique(real_graph: dict):
    """`--redline` nunca é só cor. Mata: marcar redline por cor sem o tique, ou
    redlinar par que não está abaixo do controle."""
    control = real_graph["meta"]["control"]
    assert control is not None
    for edge in real_graph["edges"]:
        if edge["kind"] == "redline":
            assert edge["ncd"] < control
            assert edge["hatch"] is not None
        else:
            assert edge["ncd"] >= control
            assert edge["hatch"] is None


def test_chave_impressa_sai_das_mesmas_funcoes(real_graph: dict):
    """Escala aproximada mente sobre o próprio gráfico. Mata: digitar os
    valores da chave à mão."""
    meta = real_graph["meta"]
    for sample in real_graph["key"]["sizes"]:
        assert sample["r"] == pytest.approx(
            radius_from_recruitment(sample["recruitment"]), abs=0.01
        )
    for sample in real_graph["key"]["widths"]:
        expected = width_from_ncd(sample["ncd"], meta["threshold"], meta["ncdMin"])
        assert sample["width"] == pytest.approx(expected, abs=0.01)


def test_geracao_e_reprodutivel(real_graph: dict):
    """Mesmo catálogo, mesmo JSON, byte a byte. Mata: qualquer estado global,
    ordem de dict instável ou random que tenha entrado no caminho."""
    de_novo = build_graph(ROOT / "packs", ROOT / "site" / "data" / "catalog.json")
    assert json.dumps(de_novo, sort_keys=True) == json.dumps(real_graph, sort_keys=True)

"""Testes da camada pura de `scripts/scan_secrets.py`.

Nenhum toca disco, rede ou relógio — é o que a separação pura/impura compra: o
classificador se testa com string literal, sem fixture e sem infraestrutura.

Os segredos aqui são **sintéticos**, construídos para casar com o padrão e nada
mais. Nenhum veio de arquivo real, e nenhum é válido em serviço nenhum.

Cada linha com um segredo sintético carrega `scan-secrets: allow`. Sem isso, a
suíte que prova que o gate funciona seria a mesma que deixa o gate vermelho para
sempre — e a saída fácil (excluir o arquivo do scanner) é exatamente como
segredo de verdade passa despercebido.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from scan_secrets import mask, scan_text


def rules_for(text: str) -> set[str]:
    return {f.rule for f in scan_text(text)}


def severity_of(text: str, rule: str) -> str | None:
    for finding in scan_text(text):
        if finding.rule == rule:
            return finding.severity
    return None


# Montados por concatenação para que o literal completo nunca apareça no fonte.
BECH32 = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
FAKE_NSEC = "nsec1" + BECH32 * 2
FAKE_HEX64 = "ab12" * 16
PEM_HEADER = "-----BEGIN " + "OPENSSH PRIVATE KEY-----"


# ---------------------------------------------------------------------------
# Deve pegar
# ---------------------------------------------------------------------------


def test_pega_nsec_bech32():
    assert "nostr_nsec" in rules_for(f"BUZZ_PRIVATE_KEY={FAKE_NSEC}")


def test_pega_hex_nomeado_como_chave_privada():
    assert "hex_privkey_64" in rules_for(f'private_key = "{FAKE_HEX64}"')


def test_pega_bloco_pem():
    assert "private_key_block" in rules_for(PEM_HEADER)


def test_pega_credencial_atribuida():
    assert "generic_assignment" in rules_for('api_key = "s3cr3t-value-longa"')


def test_pega_token_por_sufixo_do_nome():
    """`SEMGREP_TOKEN: "literal"` é a forma que aparece em `.mcp.json` e `.env`.

    A primeira versão da regra só conhecia `access_token`/`auth_token` e deixava
    passar. Regressão coberta aqui.
    """
    assert "generic_assignment" in rules_for('SEMGREP_TOKEN: "abc123def456ghi"')
    assert "generic_assignment" in rules_for('BUZZ_S3_SECRET_KEY = "r4nd0m-s3cr3t-v4l"')


def test_pega_senha_em_string_de_conexao():
    assert "connection_string" in rules_for("postgres://buzz:hunter2hunter2@db:5432/buzz")


def test_pega_cpf():
    assert "cpf" in rules_for("cliente 123.456.789-00 cadastrado")


# ---------------------------------------------------------------------------
# Não deve gritar
# ---------------------------------------------------------------------------


def test_texto_vazio_nao_gera_achado():
    assert scan_text("") == []


def test_referencia_a_variavel_de_ambiente_e_o_padrao_correto():
    """`${VAR}` é o que o spec de persona pack manda usar (Seção 13).

    Casa com a regra — nome e forma são de credencial — mas a linha é
    reconhecida como placeholder e cai para `baixa`. Não pode virar ruído
    `media` num `.mcp.json` bem escrito.
    """
    assert severity_of('SEMGREP_TOKEN: "${SEMGREP_TOKEN}"', "generic_assignment") == "baixa"


def test_getenv_nao_e_credencial():
    """Ler do ambiente é o padrão correto e não gera achado: o valor não é
    literal entre aspas, então a regra sequer casa."""
    assert severity_of('password = os.getenv("PASSWORD")', "generic_assignment") is None


def test_placeholder_nao_promove_severidade_media():
    assert severity_of('api_key = "your-api-key-here"', "generic_assignment") == "baixa"


def test_placeholder_NAO_rebaixa_severidade_alta():
    """Chave real numa linha com a palavra "example" continua sendo chave real.

    É a regra que impede um vazamento de escapar por causa de um comentário.
    """
    assert severity_of(f"# example: {PEM_HEADER}", "private_key_block") == "alta"


# ---------------------------------------------------------------------------
# Supressão inline
# ---------------------------------------------------------------------------


def test_marcador_de_allow_suprime_a_linha():
    assert scan_text(f"{PEM_HEADER}  # scan-secrets: allow") == []


def test_marcador_do_gitleaks_tambem_vale():
    """Um comentário só serve aos dois gates."""
    assert scan_text(f"{PEM_HEADER}  # gitleaks:allow") == []


def test_marcador_suprime_so_a_propria_linha():
    text = f"{PEM_HEADER}  # scan-secrets: allow\n{PEM_HEADER}"
    findings = scan_text(text)
    assert len(findings) == 1
    assert findings[0].line_number == 2


# ---------------------------------------------------------------------------
# Propriedades — valem para qualquer entrada, não para um caso
# ---------------------------------------------------------------------------


def test_mascara_nunca_devolve_o_segredo_inteiro():
    secret = "sk-ant-" + "x" * 40
    masked = mask(secret)
    assert secret not in masked
    assert masked.startswith(secret[:4])


def test_mascara_de_valor_curto_nao_vaza_nada():
    assert mask("abc") == "***"


def test_numero_da_linha_e_1_indexado_e_aponta_a_linha_certa():
    text = f"linha um\nlinha dois\n{PEM_HEADER}\nlinha quatro"
    findings = [f for f in scan_text(text) if f.rule == "private_key_block"]
    assert len(findings) == 1
    assert findings[0].line_number == 3


def test_e_deterministico():
    """Mesma entrada, mesma saída. Sem relógio, sem aleatoriedade, sem estado."""
    text = f'api_key = "abcdefgh12345678"\n{PEM_HEADER}'  # scan-secrets: allow
    primeiro = scan_text(text)
    for _ in range(5):
        assert scan_text(text) == primeiro


def test_ordem_de_achados_segue_a_ordem_das_linhas():
    text = f'api_key = "abcdefgh12345678"\n\n{PEM_HEADER}'  # scan-secrets: allow
    linhas = [f.line_number for f in scan_text(text)]
    assert linhas == sorted(linhas)


def test_linha_absurdamente_longa_nao_trava():
    """Dado serializado numa linha só não pode degradar o regex nem estourar tempo."""
    text = "x" * 100_000 + ' api_key = "abcdefgh12345678"'  # scan-secrets: allow
    scan_text(text)  # basta não pendurar nem levantar

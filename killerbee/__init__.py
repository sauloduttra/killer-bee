"""Killer Bee — catálogo de personas e agent teams entre comunidades Buzz.

Camadas deste pacote, na disciplina da §2.2 dos padrões de engenharia:

- ``model``      — dataclasses puras que descrevem um pack
- ``profile``    — compilação pura do perfil scutellata → campos nativos do Buzz
- ``snapshot``   — construção pura de AgentSnapshot / TeamSnapshot (dicts JSON)
- ``pngtext``    — bytes → bytes: PNG mínimo com chunk tEXt (o `.agent.png`)
- ``acp_rules``  — texto TOML de regras do buzz-acp, menção sempre explícita
- ``validate``   — regras puras de validação sobre o modelo
- ``loader``     — a ÚNICA camada com I/O: lê o pack do disco e monta o modelo
- ``cli``        — `python -m killerbee validate|build`

Toda referência a formato upstream carrega a citação `arquivo:linha` do commit
`ed4b3e7a` de `block/buzz`. Nada aqui foi inventado; o que não foi verificado
no fonte não virou código.
"""

__version__ = "0.1.0"

# Discriminadores do formato de snapshot do Buzz Desktop.
# Fonte: desktop/src-tauri/src/managed_agents/agent_snapshot.rs:163-175 e
# team_snapshot.rs:76-87 (@ ed4b3e7a).
AGENT_SNAPSHOT_FORMAT = "buzz-agent-snapshot"
TEAM_SNAPSHOT_FORMAT = "buzz-team-snapshot"
SNAPSHOT_VERSION = 1

# Keywords do chunk tEXt nos PNGs portáveis.
# Fonte: agent_snapshot.rs:53 e team_snapshot.rs:49.
AGENT_PNG_KEYWORD = "buzz_agent_snapshot"
TEAM_PNG_KEYWORD = "buzz_team_snapshot"

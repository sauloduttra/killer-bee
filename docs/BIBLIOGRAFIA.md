# Bibliografia verificada

Toda referência aqui foi buscada na fonte primária — página do editor, DOI resolvido,
repositório institucional — antes de entrar em qualquer documento público. É a mesma
disciplina que se aplica às citações `arquivo:linha` do upstream, pelo mesmo motivo:
**referência errada é pior que referência ausente.**

Regra em [`CONTRIBUTING.md`](../CONTRIBUTING.md#bibliographic-citations-get-the-same-scrutiny-as-code-citations).
Verificado em 2026-08-05.

> **Estado: dois leitores independentes, ambos completos.** ✅
>
> O segundo leitor refez cada busca sem confiar no primeiro. **Pegou duas afirmações
> falsas** que o primeiro tinha marcado como confirmadas — ambas corrigidas abaixo e
> assinaladas com 🔁. Sem o segundo passe, as duas teriam entrado no README como fato.
>
> É a mesma disciplina que pegou quatro bugs na auditoria de licença
> ([D-014](DECISIONS.md)), pelo mesmo motivo: **uma fonte que se repete não é uma segunda
> fonte.**

**Legenda:** ✅ confirmado · ✏️ corrigido (a alegação original estava errada) · ⚠️ parcial
· ❌ não confirmado.

---

## Modelo de limiar de resposta — a base do perfil scutellata

Estes dois sustentam [`PROFILE-COMPILATION.md`](PROFILE-COMPILATION.md) e o item
[B-02](BACKLOG.md#b-02--limiar-adaptativo-no-perfil-scutellata). A diretiva original dizia
"1996–1998" sem distinguir; a verificação mostrou que são **dois artigos com papéis
diferentes**, e que existe um terceiro que se confunde com o primeiro.

### ✅ Limiar FIXO — o modelo-base *(é o que o Killer Bee implementa hoje)*

> Bonabeau, E., Theraulaz, G., Deneubourg, J.-L. "Quantitative study of the fixed
> threshold model for the regulation of division of labour in insect societies".
> *Proceedings of the Royal Society of London. Series B: Biological Sciences*,
> **263**(1376), 1565–1569, 1996. DOI: [10.1098/rspb.1996.0229](https://doi.org/10.1098/rspb.1996.0229)

**Ano:** o Crossref registra impresso em 22/11/1996 e online em janeiro de 1997. **Cite
1996** — não deixe ninguém "corrigir" para 1997.
**Ordem dos autores:** Bonabeau, Theraulaz, Deneubourg — **invertida** em relação ao artigo
de 1998. A inversão é real e distingue os dois.
**Limitação de método:** o array de autores está ausente no registro Crossref deste DOI, e
o artigo não está no PubMed nem no Europe PMC. A autoria foi confirmada pela lista de
referências tipografada pela própria Royal Society no artigo de 1998.

### ⚠️ Limiar REFORÇADO — a versão adaptativa *(B-02, não implementada)*

> Theraulaz, G., Bonabeau, E., Deneubourg, J.-L. "Response threshold reinforcements and
> division of labour in insect societies". *Proceedings of the Royal Society of London.
> Series B: Biological Sciences*, **265**(1393), 327–332, 1998.
> DOI: [10.1098/rspb.1998.0299](https://doi.org/10.1098/rspb.1998.0299)

Autores, veículo e ano da diretiva estavam corretos. **Parcial** por uma divergência de
título com respaldo dos dois lados: a página atual da Royal Society e o DOI trazem
`reinforcementS` (plural); o PDF tipografado do próprio artigo e o working paper do Santa
Fe Institute (SFI WP 1998-01-006) trazem o singular. **Usamos o plural**, que é a forma
para a qual o DOI resolve.

**🚨 Erro nos metadados do DOI.** O Crossref grava o terceiro autor como
`J-N. Denuebourg` — sobrenome com erro de digitação **e** iniciais erradas. Quem importar
este DOI direto para BibTeX ou Zotero puxa o nome errado. O correto é **Jean-Louis
Deneubourg**, confirmado no PDF tipografado e no working paper do SFI.

**Ano:** recebido e aceito em outubro de 1997, **publicado em 1998**. Cite 1998.

**Por que este é o artigo do reforço:** na Discussão do próprio artigo os autores escrevem
que estenderam o modelo de 1996 "to include learning in the form of a reinforcement
process". É a prova de que 1996 = fixo, 1998 = reforçado.

### ✅ Não confundir com o tratamento longo

> Bonabeau, E., Theraulaz, G., Deneubourg, J.-L. "Fixed Response Thresholds and the
> Regulation of Division of Labor in Insect Societies". *Bulletin of Mathematical
> Biology*, **60**(4), 753–807, 1998.
> DOI: [10.1006/bulm.1998.0041](https://doi.org/10.1006/bulm.1998.0041)

Cinquenta e cinco páginas, **posterior** ao seminal. Em fevereiro de 1998 a Royal Society
ainda o citava como *"in the press"*. Se você quer **o** artigo do limiar fixo, use o de
1996. Grafia americana "Labor" aqui, britânica "labour" no de 1996 — não uniformize.
O registro Crossref deste DOI traz **apenas um autor**, omitindo Theraulaz e Deneubourg.

---

## Estigmergia e ACO — sustentam [B-01](BACKLOG.md#b-01--ranking-por-reforço-estigmérgico)

### ✅ Estigmergia — a cunhagem do termo

> Grassé, Pierre-P. "La reconstruction du nid et les coordinations interindividuelles chez
> *Bellicositermes natalensis* et *Cubitermes* sp. La théorie de la stigmergie: Essai
> d'interprétation du comportement des termites constructeurs". *Insectes Sociaux*,
> **6**(1), 41–80, março de 1959.
> DOI: [10.1007/BF02223791](https://doi.org/10.1007/BF02223791)

O termo *stigmergie* está no próprio título, como a diretiva supunha.

**Páginas:** use **41–80**. Parte da literatura cita 41–81 ou 41–83 porque engloba a
"Légende des planches" — que o segundo leitor confirmou ser **item com DOI próprio**
(`10.1007/bf02223792`), nas páginas 81–83. Não é parte do artigo.

**🔁 Nome — correção do segundo leitor.** O primeiro leitor afirmou que o sumário do
fascículo traz `Pierre-P. Grassé` corretamente. **Não traz.** A captura arquivada do
sumário (Wayback, do próprio `link.springer.com`) lê literalmente `Plerre-P.`, e o erro de
OCR está em **todas** as superfícies da Springer: página do artigo (`dc.creator`), sumário,
depósito Crossref e exports BibTeX/EndNote. **Não existe fonte do editor com a grafia
correta.** Escreva `Pierre-Paul Grassé` sabendo que nenhum registro do editor confirma —
é conhecimento externo, não citação.

**🔁 "Três fontes concordantes" era uma só.** O primeiro leitor apresentou página do
editor, sumário do fascículo e Crossref como confirmação independente. As três derivam do
**mesmo depósito da Springer**. Concordância entre superfícies do mesmo emissor não é
validação cruzada — é o mesmo dado três vezes.

### ✏️ Tese de Dorigo — **corrigido**

> Dorigo, Marco. "Ottimizzazione, apprendimento automatico, ed algoritmi basati su
> metafora naturale" *(tradução do próprio autor: "Optimization, Learning and Natural
> Algorithms")*. Tese de doutorado, Politecnico di Milano, Dipartimento di Elettronica e
> Informazione, 140 pp., 1992. Defesa em 23/09/1992. Escrita em italiano. Sem DOI.

**O título real é em italiano.** Quase toda a literatura cita apenas a tradução inglesa,
que **não é o título da tese** — é o que Dorigo põe entre parênteses. Fonte: CV oficial no
IRIDIA/ULB, em dois pontos independentes do documento.

**Imprecisão que a diretiva carregava:** atribuir o nome *"Ant Colony Optimization"* à tese
de 1992 é errado. A tese origina o **Ant System**; o rótulo ACO como metaheurística nomeada
é posterior — o próprio artigo de 1996 ainda fala em "Ant System", não em ACO. Não
verificamos em que ano o rótulo passou a ser usado, então não afirmamos ano para isso.

### ✏️ Ant System — **corrigido**

> Dorigo, M., Maniezzo, V., Colorni, A. "Ant system: optimization by a colony of
> cooperating agents". *IEEE Transactions on Systems, Man, and Cybernetics, Part B
> (Cybernetics)*, **26**(1), 29–41, fevereiro de 1996.
> DOI: [10.1109/3477.484436](https://doi.org/10.1109/3477.484436)

**O título não é apenas "Ant System"** — o subtítulo faz parte dele.

**🚨 Armadilha de paginação.** O PDF de preprint que circula traz no cabeçalho de todas as
páginas `Vol.26, No.1, 1996, pp.1-13`, o que está **errado**. A paginação publicada é
**29–41**. Copiar de preprint propaga o erro.

**Não existe "Ant System de 1991".** O relatório técnico de 1991 é outro documento —
*"Positive feedback as a search strategy"*, Technical Report 91-016, Politecnico di Milano.
Há ainda Colorni, Dorigo, Maniezzo, "Distributed Optimization by Ant Colonies", ECAL 1991,
134–142 — esse sim é o artigo de conferência de 1991.

---

## Physarum — sustenta a intuição de condutância em [B-01](BACKLOG.md#b-01--ranking-por-reforço-estigmérgico)

### ✅ Labirinto

> Nakagaki, T., Yamada, H., Tóth, Á. "Maze-solving by an amoeboid organism". *Nature*,
> **407**(6803), 470, 2000. DOI: [10.1038/35035159](https://doi.org/10.1038/35035159)

**É uma Brief Communication de uma página**, não artigo completo — vale saber antes de
apoiar peso demais nela. ADS, Gale e ResearchGate registram o título com o prefixo
`Intelligence:`, que é a rubrica da seção, não parte do título.
**Ordem dos autores:** Nakagaki, Yamada, Tóth. Fontes secundárias (SciRP) invertem para
"Yamada, Tóth, Nakagaki" — está errado.

### ✅ Rede de Tóquio

> Tero, A., Takagi, S., Saigusa, T., Ito, K., Bebber, D. P., Fricker, M. D., Yumiki, K.,
> Kobayashi, R., Nakagaki, T. "Rules for Biologically Inspired Adaptive Network Design".
> *Science*, **327**(5964), 439–442, 2010.
> DOI: [10.1126/science.1177894](https://doi.org/10.1126/science.1177894)

Tudo o que a diretiva alegava se confirmou. Nove autores. Use Title Case, a forma do editor.

---

## Abelhas

### ✅ Recrutamento e forrageamento

> Seeley, Thomas D. *The Wisdom of the Hive: The Social Physiology of Honey Bee Colonies*.
> Harvard University Press, Cambridge, MA, 1995. ISBN 9780674953765.

A diretiva estava certa mas incompleta — faltavam subtítulo, nome completo e editora.
**Ano:** o Crossref da HUP traz 1995-12-31; a resenha de E. O. Wilson na *Science* (1996)
lista 1996. Padrão clássico de livro com copyright de dezembro. **Use 1995.**

### ⚠️ Waggle dance — "Nobel de 1973" não é citação

O prêmio confirma-se **até certo ponto**: Nobel de Fisiologia ou Medicina de 1973,
**concedido conjuntamente a Karl von Frisch, Konrad Lorenz e Nikolaas Tinbergen**.

**🔁 Correção do segundo leitor.** O primeiro escreveu "dividido em três partes iguais".
**Nenhuma das fontes citadas sustenta isso** — Dewsbury (*American Psychologist*) diz
apenas "awarded to 3 ethologists"; Font (*Frontiers in Ethology*) lista os três nomes.
Fração de rateio é afirmação sobre a mecânica da Fundação Nobel, e só a Fundação Nobel
confirma — `nobelprize.org` devolve **403** tanto no site quanto na API, verificado pelos
dois leitores. **Escreva "concedido conjuntamente", nunca "dividido em três partes
iguais".**

*(Fonte corrigida também na atribuição: Font, Enrique. Frontiers in Ethology, 2023 — o
primeiro leitor citou o veículo sem o autor, o que não é citação.)*

Prêmio não é referência bibliográfica. Use a monografia:

> Frisch, Karl von. *Tanzsprache und Orientierung der Bienen*. Springer-Verlag, Berlin,
> 1965. DOI: [10.1007/978-3-642-94916-6](https://doi.org/10.1007/978-3-642-94916-6)
>
> Tradução: *The Dance Language and Orientation of Bees*, trad. Leigh E. Chadwick, Belknap
> Press / Harvard University Press, 1967.

**Fonte do prêmio:** `nobelprize.org` devolve HTTP 403 a acesso automatizado. Categoria,
ano e laureados foram confirmados em duas fontes revisadas por pares independentes
(*Frontiers in Ethology*, 2023; *American Psychologist* 58(9):747–752, 2003).

**❌ Não confirmado:** a redação literal da motivação oficial do Nobel. Apareceu só em
snippets de busca. **Não citar entre aspas** sem abrir o site manualmente.

---

## Bandits — sustentam [B-03](BACKLOG.md#b-03--alocação-de-orçamento-de-eval-por-bandit)

### ✅ Formulação original

> Thompson, William R. "On the Likelihood That One Unknown Probability Exceeds Another in
> View of the Evidence of Two Samples". *Biometrika*, **25**(3–4), 285–294, 1933.
> DOI: [10.1093/biomet/25.3-4.285](https://doi.org/10.1093/biomet/25.3-4.285)

É Biometrika, confirmado. "Thompson sampling" é apelido posterior — não aparece no título
nem no artigo.

### ✅ Avaliação empírica

> Chapelle, Olivier; Li, Lihong. "An Empirical Evaluation of Thompson Sampling". In:
> *Advances in Neural Information Processing Systems 24 (NIPS 2011)*, Curran Associates,
> 2011.

**Era NIPS em 2011, não NeurIPS** — a conferência só foi renomeada em 2018. Escrever
"NeurIPS 2011" numa referência é anacronismo.
**❌ Páginas não confirmadas:** o BibTeX oficial dos anais traz o campo vazio. Não inclua
páginas sem checar.

### ✅ Prova de regret logarítmico

> Agrawal, Shipra; Goyal, Navin. "Analysis of Thompson Sampling for the Multi-armed Bandit
> Problem". In: *Proceedings of the 25th Annual Conference on Learning Theory (COLT 2012)*,
> PMLR vol. 23, pp. 39.1–39.26, 2012.

Paginação `39.1–39.26` é o formato do PMLR — o ponto faz parte da numeração. O volume 23
saiu originalmente como "JMLR: Workshop and Conference Proceedings" e depois foi remarcado
como PMLR; as duas formas circulam.

---

## Compressão — sustenta [B-07](BACKLOG.md#b-07--detector-de-duplicata-por-ncd)

### ✅ Normalized Compression Distance

> Cilibrasi, Rudi; Vitányi, Paul M. B. "Clustering by Compression". *IEEE Transactions on
> Information Theory*, **51**(4), 1523–1545, abril de 2005.
> DOI: [10.1109/TIT.2005.844059](https://doi.org/10.1109/TIT.2005.844059)

É este o artigo que introduz o NCD — o resumo define *"a parameter-free, universal,
similarity distance, the normalized compression distance or NCD"*.
**Ano:** 2005 é a publicação em periódico. O manuscrito é de março de 2003, foi apresentado
no ISIT 2003 e há preprint arXiv `cs/0312044` de dezembro de 2003. Ver "2003" por aí é
possível; para referência de periódico, 2005.

---

## ⚠️ A história de origem do projeto — parcialmente não confirmada

Isto abre o [README](../README.md) e fundamenta a §0.1 do [`PROMPT.md`](../PROMPT.md).
**Merece o maior rigor de todos, e é o item mais frágil da lista.**

### O que se confirma

- **26** colônias escaparam. Consistente em todas as fontes.
- A fuga foi em **1957** — as fontes que datam o mês dizem **outubro de 1957**.
- Local: apiário experimental de **Rio Claro, São Paulo**.
- Causa: remoção das telas excluidoras de rainha por um terceiro.

### ❌ O que NÃO se confirma: quantas rainhas foram trazidas

As fontes divergem de forma irreconciliável: **36, 47, 49, 51, 56 e 63**.

| Versão | Origem |
|---|---|
| **51** (50 da África do Sul + 1 da Tanzânia) | **o próprio Kerr**, em entrevista publicada em periódico acadêmico |
| 63 adquiridas, 48 sobreviventes | dominante na literatura anglófona de extensão universitária |
| 36 trazidas, 29 colônias antes da fuga | outras fontes |
| 47, 56 | menções isoladas |

> Coelho, Marco Antonio. "Warwick Kerr: a Amazônia, os índios e as abelhas" (entrevista com
> W. E. Kerr). *Estudos Avançados*, **19**(53), 2005.
> DOI: [10.1590/S0103-40142005000100004](https://doi.org/10.1590/S0103-40142005000100004)

O relato de Kerr tem o melhor pedigree — é o próprio, em veículo acadêmico indexado — mas é
memória dada cerca de 49 anos depois do fato, e na mesma entrevista ele situa a introdução
de forma ambígua quanto ao ano.

**As fontes primárias que resolveriam isso, e que não foram lidas:**

- Kerr, W. E. (1957). "Introdução de abelhas africanas no Brasil". *Brasil Apícola*, 3:211–213.
- Michener, C. D. (1975). "The Brazilian bee problem". *Annual Review of Entomology*,
  20:399–416. DOI: [10.1146/annurev.en.20.010175.002151](https://doi.org/10.1146/annurev.en.20.010175.002151)
  — existência e paginação confirmadas via PubMed; **texto integral atrás de paywall, não lido.**

Sem uma dessas, **qualquer número de rainhas no README é atribuição, não fato.** O README
usa 51, atribui a Kerr, e diz que é disputado.

### ⚠️ "Unesp" é anacronismo provável

Em 1956 Kerr estava na **Faculdade de Filosofia, Ciências e Letras de Rio Claro**. A UNESP
foi criada depois, pela fusão de institutos isolados que incluía essa faculdade. Não
verificamos o ano de criação nesta rodada, então não afirmamos a data — mas escrever "Rio
Claro (Unesp)" para 1956 deve ser evitado. A própria entrevista do SciELO usa a formulação
ambígua "em Rio Claro, no início da Unesp".

### Detalhe corrompido que circula

Uma fonte descreve o apiário como "cerca de 100 milhas ao **sul** de São Paulo". Rio Claro
fica ao **norte/noroeste** da capital. Bom lembrete de como este episódio específico
circula com detalhes errados — e de por que ele foi o item mais verificado desta lista.

---

## Nota de método

Vários sites de editor bloqueiam acesso automatizado: `nature.com` (303),
`science.org` (403), `royalsocietypublishing.org` (403), `nobelprize.org` (403),
`ieeexplore.ieee.org` (403), `hup.harvard.edu` (corpo vazio). Nesses casos a confirmação
veio do **registro Crossref depositado pelo próprio editor** por trás do DOI, corroborado
por PubMed, Europe PMC, repositório institucional ou fac-símile da página impressa.

Onde os metadados do Crossref estavam **errados ou incompletos** — e estavam, em três dos
doze itens — isso está sinalizado no verbete. Registro de DOI não é infalível, o que é a
mesma lição que a auditoria de licença ensinou em [D-014](DECISIONS.md).

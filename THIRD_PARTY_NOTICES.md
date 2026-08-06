# Third-party notices

Killer Bee é licenciado sob Apache-2.0. Este arquivo lista todo componente de
terceiro cujo código foi reaproveitado, com a licença original preservada na
íntegra, como as respectivas licenças exigem.

Reaproveitamento aqui significa **código**. Técnica de CSS, ideia de layout ou
abordagem de engenharia não são protegidas por copyright e não geram entrada nesta
lista — mas quando a inspiração for direta e reconhecível, creditamos assim mesmo,
por higiene.

---

## buzz-directory (buzzdir.xyz)

- **Origem:** https://github.com/pavlenex/buzz-directory
- **Commit de referência:** `d9c656ed41ba80a26fdad004ee226fa2250290db` (2026-08-05)
- **Licença:** MIT
- **Relação com este projeto:** referência técnica de frontend. Projeto
  independente da comunidade, mantido por pavlenex. **Não é da Block, não é
  oficial, e o Killer Bee também não é.**

### Estado do reaproveitamento

Nenhum arquivo ou bloco de código do `buzz-directory` foi copiado até o momento.
Esta entrada existe desde já porque a licença foi verificada na Fase 0 e o projeto
é referência declarada.

**Regra de registro:** todo arquivo do Killer Bee que venha a conter trecho
reaproveitado leva, no topo, um comentário com origem, commit SHA e o que foi
alterado. Exemplo:

```css
/* Adaptado de pavlenex/buzz-directory @ d9c656ed, app/globals.css (MIT).
   Alterações: tokens de cor trocados pela paleta scutellata; borda do hexágono
   passou de 2px para 3px; container query real adicionada (o original usa
   unidades cqi sem regra @container). Ver THIRD_PARTY_NOTICES.md. */
```

Quando houver a primeira entrada real, listar aqui o arquivo de destino e o de
origem, um par por linha.

### Texto da licença

```
MIT License

Copyright (c) 2026 buzzdir contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## block/buzz

- **Origem:** https://github.com/block/buzz
- **Commit de referência:** `ed4b3e7afafb5f5a688c210f39b90d747e6f0f00` (2026-08-05)
- **Licença:** Apache-2.0
- **Relação com este projeto:** o Killer Bee é satélite do Buzz. **Zero fork, zero
  patch em core.** Consumimos o formato de persona pack, os event kinds e o
  protocolo — que são interface, não código copiado.

### Estado do reaproveitamento

Nenhum código copiado. O que existe é **conformidade com formato**: nomes de campo,
números de kind e nomes de comando são usados como o Buzz os define, porque
interoperar exige isso.

Se algum dia um trecho de código Apache-2.0 do Buzz for incorporado, ele entra aqui
e o arquivo `NOTICE` na raiz passa a carregar a atribuição correspondente, como a
seção 4(d) da Apache-2.0 exige.

---

## Fontes — SIL Open Font License 1.1

Auto-hospedadas em `site/app/fonts/`, baixadas por `site/scripts/fetch-fonts.mjs` e
**versionadas no repositório** — o CI não depende de rede para produzir o site, e uma
família que suma do Google Fonts não pode quebrar o deploy.

| Família | Autoria | Uso |
|---|---|---|
| **Archivo** | Omnibus-Type | nome próprio de objeto do catálogo |
| **Spectral** | Production Type | toda prosa, incluindo o system prompt |
| **Azeret Mono** | Displaay Type Foundry | escala, rótulo, numeral, identificador |

As três sob **SIL Open Font License 1.1**, que permite uso, modificação e redistribuição —
inclusive comercial e embarcada — com duas condições práticas: a fonte não pode ser vendida
isoladamente, e um trabalho derivado da fonte não pode usar o nome reservado original.
Nenhuma das duas restringe o uso aqui, que é servir os arquivos como recebidos.

O texto da OFL acompanha cada família na distribuição do Google Fonts e está preservado
junto aos arquivos. Nenhuma modificação foi feita nos glifos.

---

## Declaração de não-afiliação

Killer Bee não é afiliado, endossado ou operado pela Block, Inc., pelo projeto Buzz
ou pelo buzzdir. É trabalho independente de comunidade.

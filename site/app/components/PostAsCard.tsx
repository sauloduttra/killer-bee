import type { ArtifactFile } from "@/app/lib/catalog";
import { CopyButton } from "@/app/components/CopyButton";

/**
 * O artefato como card importável num canal Buzz — pronto para colar.
 *
 * Quando um snapshot viaja numa mensagem de chat, o desktop mostra um card com
 * botão Import em vez de um anexo genérico. Para isso a mensagem precisa de
 * duas partes: o link markdown no corpo e a tag `imeta` nas media tags — a
 * forma exata está no e2e do upstream (`agent-snapshot-recipient.spec.ts:117`
 * para o link, `:118-126` para a tag). E o card RECUSA imeta sem sha256 de 64
 * hex (`markdownFileCard.ts:101-103`): o hash publicado logo acima nesta mesma
 * página é o que habilita o botão do outro lado.
 *
 * A seção só existe quando o catálogo trouxe `imeta`, o que acontece quando o
 * build recebeu a URL pública do host (D-027). Em dev, sem a variável, ela some
 * inteira — publicar uma URL de `localhost` num canal de outra pessoa seria pior
 * que não oferecer o atalho.
 *
 * Sem JavaScript o conteúdo continua inteiro e selecionável: os botões de
 * copiar são atalho, nunca a única via.
 */
export function PostAsCard({ files }: { files: ArtifactFile[] | undefined }) {
  // O type guard estreita para um tipo com `imeta` obrigatório — sem `!` no
  // corpo do map, que o TypeScript recusa (e com razão: o filtro e o uso
  // ficariam livres para divergir).
  const postable = (files ?? []).filter(
    (file): file is ArtifactFile & { imeta: string[] } => (file.imeta?.length ?? 0) >= 6,
  );
  if (postable.length === 0) return null;

  return (
    <details className="disclosure postable">
      <summary>Post as a chat card</summary>
      <p className="postable-note">
        Paste the link as the message body and the <code>imeta</code> tag as its media
        tag. Buzz renders it as an importable agent card instead of a file
        attachment — the <code>x</code> value is the same sha256 published above, and
        the card refuses to offer Import without it.
      </p>
      {postable.map((file) => {
        // Busca por prefixo em vez de índice fixo: a ordem da tag é a do e2e
        // upstream, mas depender da posição faria uma reordenação futura virar
        // uma URL errada em silêncio.
        const url = file.imeta.find((part) => part.startsWith("url "))?.slice(4) ?? "";
        const markdown = `[${file.name}](${url})`;
        const tagJson = JSON.stringify(file.imeta);
        return (
          <div className="postable-item" key={file.name}>
            <h4>{file.name}</h4>
            <div className="postable-row">
              <code className="postable-value">{markdown}</code>
              <CopyButton value={markdown} label="Copy link" />
            </div>
            <div className="postable-row">
              <code className="postable-value">{tagJson}</code>
              <CopyButton value={tagJson} label="Copy imeta" />
            </div>
          </div>
        );
      })}
    </details>
  );
}

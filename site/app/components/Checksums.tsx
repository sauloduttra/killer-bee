import type { ArtifactFile } from "@/app/lib/catalog";

/**
 * sha256 + tamanho de cada artefato, ao lado dos botões de download.
 *
 * Não é decoração de segurança: o hash é computado pelo emissor sobre os
 * mesmos bytes que o build grava, o teste de export confere o hash contra o
 * arquivo servido, e é o `x` exato que o card de snapshot do chat do Buzz
 * exige para habilitar Import (markdownFileCard.ts:101-103). Quem baixar por
 * mirror pode verificar com `sha256sum` — o endereço do artefato passa a ser
 * o conteúdo, não o host.
 */
export function Checksums({ files }: { files: ArtifactFile[] | undefined }) {
  if (!files?.length) return null;
  return (
    <details className="disclosure checksums">
      <summary>sha256 checksums</summary>
      <dl className="hashes">
        {files.map((file) => (
          <div key={file.name}>
            <dt>
              {file.name} <span className="hash-bytes">{file.bytes.toLocaleString("en-US")} B</span>
            </dt>
            <dd>
              <code>{file.sha256}</code>
            </dd>
          </div>
        ))}
      </dl>
    </details>
  );
}

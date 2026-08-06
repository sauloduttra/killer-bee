"use client";

import { useState } from "react";

/**
 * Copia um comando para a área de transferência.
 *
 * O texto fica visível num `<code>` ao lado — o botão é atalho, não a única via.
 * Com JS desligado o comando continua legível e selecionável, que é o que
 * realmente importa numa página cujo produto é o texto.
 *
 * O rótulo muda para o estado que a ação produziu ("Copied"), não para um
 * agradecimento.
 */
export function CopyButton({ value, label = "Copy" }: { value: string; label?: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      // Clipboard bloqueado por permissão ou contexto não seguro. Não há o que
      // consertar aqui e o texto está visível ao lado — silêncio é melhor que um
      // alerta que não ajuda.
    }
  }

  return (
    <button type="button" className="copy" onClick={copy} data-copied={copied || undefined}>
      {copied ? "Copied" : label}
    </button>
  );
}

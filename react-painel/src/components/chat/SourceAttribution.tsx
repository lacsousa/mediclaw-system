import { Text } from "@chakra-ui/react";
import type { Citation } from "@/types/api";

/**
 * Informa a procedência da resposta do assistente:
 * - Fonte interna: houve trechos relevantes da base de conhecimento (RAG).
 * - Fonte externa: a resposta veio do conhecimento geral do modelo de IA.
 */
export function SourceAttribution({ citations }: { citations?: Citation[] }) {
  const sources = Array.from(new Set((citations ?? []).map((c) => c.source).filter(Boolean)));

  if (sources.length > 0) {
    return (
      <Text fontSize="xs" color="blue.fg" mt={1.5}>
        📚 Baseado em fonte interna: {sources.join(", ")}
      </Text>
    );
  }

  return (
    <Text fontSize="xs" color="fg.muted" mt={1.5}>
      🌐 Baseado em fonte externa (conhecimento geral do modelo de IA)
    </Text>
  );
}

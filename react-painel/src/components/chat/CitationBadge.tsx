import { Badge } from "@chakra-ui/react";
import type { Citation } from "@/types/api";

export function CitationBadge({ citation }: { citation: Citation }) {
  return (
    <Badge colorPalette="blue" size="sm">
      📚 {citation.source}
    </Badge>
  );
}

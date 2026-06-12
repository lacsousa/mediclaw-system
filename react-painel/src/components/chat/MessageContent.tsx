"use client";

import { Box, Text } from "@chakra-ui/react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";

type MessageContentProps = {
  content: string;
  variant: "user" | "assistant";
  streaming?: boolean;
};

export function MessageContent({ content, variant, streaming = false }: MessageContentProps) {
  if (variant === "user") {
    return (
      <Text whiteSpace="pre-wrap" lineHeight="relaxed">
        {content}
      </Text>
    );
  }

  if (!content.trim()) {
    return streaming ? <Box className="typing-cursor" minH="1.25em" aria-hidden /> : null;
  }

  return (
    <Box
      lineHeight="relaxed"
      fontSize="sm"
      className={streaming ? "typing-cursor" : undefined}
      css={{
        "& p": { marginBottom: "0.5rem" },
        "& p:last-of-type": { marginBottom: 0 },
        "& ul, & ol": {
          marginBottom: "0.5rem",
          paddingLeft: "1.25rem",
        },
        "& ul:last-child, & ol:last-child": { marginBottom: 0 },
        "& ul": { listStyleType: "disc" },
        "& ol": { listStyleType: "decimal" },
        "& li": { marginBottom: "0.25rem" },
        "& li:last-child": { marginBottom: 0 },
        "& li > p": { marginBottom: 0, display: "inline" },
        "& strong": { fontWeight: "semibold" },
        "& em": { fontStyle: "italic" },
        "& h1, & h2, & h3": {
          fontWeight: "semibold",
          marginTop: "0.75rem",
          marginBottom: "0.5rem",
        },
        "& h1:first-of-type, & h2:first-of-type, & h3:first-of-type": { marginTop: 0 },
        "& h1": { fontSize: "1.125rem" },
        "& h2": { fontSize: "1rem" },
        "& h3": { fontSize: "0.9375rem" },
        "& blockquote": {
          borderLeftWidth: "3px",
          borderLeftStyle: "solid",
          borderLeftColor: "var(--chakra-colors-border-emphasized)",
          paddingLeft: "0.75rem",
          color: "var(--chakra-colors-fg-muted)",
          marginBottom: "0.5rem",
        },
        "& hr": {
          marginTop: "0.75rem",
          marginBottom: "0.75rem",
          borderColor: "var(--chakra-colors-border)",
        },
        "& a": {
          color: "var(--chakra-colors-teal-600)",
          textDecoration: "underline",
        },
        "& code": {
          fontFamily: "mono",
          fontSize: "0.875em",
          background: "var(--chakra-colors-bg-muted)",
          padding: "0.1em 0.35em",
          borderRadius: "0.25rem",
        },
        "& pre": {
          marginBottom: "0.5rem",
          padding: "0.75rem",
          borderRadius: "0.5rem",
          background: "var(--chakra-colors-bg-muted)",
          overflowX: "auto",
        },
        "& pre code": {
          background: "transparent",
          padding: 0,
        },
      }}
    >
      <Markdown remarkPlugins={[remarkGfm]}>{content}</Markdown>
    </Box>
  );
}

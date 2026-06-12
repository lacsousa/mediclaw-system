import React from "react";
import { describe, it, expect } from "vitest";
import { renderWithChakra, screen } from "@/test-utils";
import { MessageBubble } from "@/components/chat/MessageBubble";
import type { Message } from "@/types/api";

const base: Message = {
  id: 1,
  role: "USER",
  content: "Olá, tudo bem?",
  tokens_used: null,
  blocked_by_guardrail: false,
  metadata: {},
  created_at: new Date().toISOString(),
};

const agentMarkdown = `Com base nos dados:

*   **Idade:** 26 anos.
*   **Peso atual:** 97 kg.

Esta orientação é educativa e não substitui consulta com profissional de saúde.`;

describe("MessageBubble", () => {
  it("renders message content", () => {
    renderWithChakra(<MessageBubble message={base} />);
    expect(screen.getByText("Olá, tudo bem?")).toBeInTheDocument();
  });

  it("renders markdown lists and bold for ASSISTANT messages", () => {
    renderWithChakra(
      <MessageBubble message={{ ...base, role: "ASSISTANT", content: agentMarkdown }} />
    );
    expect(screen.getByText("Idade:")).toBeInTheDocument();
    expect(screen.getByText("26 anos.")).toBeInTheDocument();
    expect(screen.getByText("Peso atual:")).toBeInTheDocument();
    expect(screen.getByRole("list")).toBeInTheDocument();
  });

  it("renders footer disclaimer for ASSISTANT when not in body", () => {
    renderWithChakra(<MessageBubble message={{ ...base, role: "ASSISTANT" }} />);
    expect(screen.getByText(/Esta orientação é educativa/)).toBeInTheDocument();
  });

  it("hides footer disclaimer when ASSISTANT body already includes it", () => {
    renderWithChakra(
      <MessageBubble message={{ ...base, role: "ASSISTANT", content: agentMarkdown }} />
    );
    expect(screen.getAllByText(/não substitui/).length).toBe(1);
  });

  it("does not render disclaimer for USER messages", () => {
    renderWithChakra(<MessageBubble message={base} />);
    expect(screen.queryByText(/Esta orientação é educativa/)).not.toBeInTheDocument();
  });

  it("shows guardrail badge when blocked_by_guardrail is true", () => {
    renderWithChakra(
      <MessageBubble message={{ ...base, role: "ASSISTANT", blocked_by_guardrail: true }} />
    );
    expect(screen.getByText("Resposta limitada")).toBeInTheDocument();
  });

  it("does not show guardrail badge when not blocked", () => {
    renderWithChakra(
      <MessageBubble message={{ ...base, role: "ASSISTANT", blocked_by_guardrail: false }} />
    );
    expect(screen.queryByText("Resposta limitada")).not.toBeInTheDocument();
  });

  it("shows internal source attribution when citations are present", () => {
    renderWithChakra(
      <MessageBubble
        message={{
          ...base,
          role: "ASSISTANT",
          metadata: { citations: [{ source: "Sleep Foundation 2024", chunk_id: "c1" }] },
        }}
      />
    );
    expect(
      screen.getByText(/Baseado em fonte interna:.*Sleep Foundation 2024/)
    ).toBeInTheDocument();
  });

  it("shows external source attribution when no citations", () => {
    renderWithChakra(<MessageBubble message={{ ...base, role: "ASSISTANT", metadata: {} }} />);
    expect(screen.getByText(/Baseado em fonte externa/)).toBeInTheDocument();
  });
});

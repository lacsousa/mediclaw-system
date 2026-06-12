import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithChakra, screen, waitFor } from "@/test-utils";
import userEvent from "@testing-library/user-event";

const mocks = vi.hoisted(() => ({
  openStream: vi.fn(),
  showToast: vi.fn(),
}));

vi.mock("@/lib/sse", () => ({
  openStream: mocks.openStream,
}));

vi.mock("@/context/ToastContext", () => ({
  useToast: () => ({ showToast: mocks.showToast }),
}));

import { ChatInput } from "@/components/chat/ChatInput";

type StreamCallbacks = {
  onToken: (c: string) => void;
  onCitation: (c: { source: string; chunk_id: string }) => void;
  onDone: (r: { tokens_used: number; blocked: boolean }) => void;
  onError: (e: { code: string; message: string }) => void;
};

describe("ChatInput", () => {
  const user = userEvent.setup();
  const onStreamComplete = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mocks.openStream.mockReturnValue(() => {});
  });

  it("renders the textarea and send button", () => {
    renderWithChakra(<ChatInput conversationId={1} onStreamComplete={onStreamComplete} />);
    expect(screen.getByPlaceholderText("Digite sua mensagem...")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /enviar/i })).toBeInTheDocument();
  });

  it("send button is disabled when input is empty", () => {
    renderWithChakra(<ChatInput conversationId={1} onStreamComplete={onStreamComplete} />);
    expect(screen.getByRole("button", { name: /enviar/i })).toBeDisabled();
  });

  it("calls openStream when submitting a message", async () => {
    renderWithChakra(<ChatInput conversationId={1} onStreamComplete={onStreamComplete} />);
    await user.type(screen.getByPlaceholderText("Digite sua mensagem..."), "Olá");
    await user.click(screen.getByRole("button", { name: /enviar/i }));
    expect(mocks.openStream).toHaveBeenCalledOnce();
  });

  it("shows optimistic user bubble while streaming", async () => {
    renderWithChakra(<ChatInput conversationId={1} onStreamComplete={onStreamComplete} />);
    await user.type(screen.getByPlaceholderText("Digite sua mensagem..."), "minha pergunta");
    await user.click(screen.getByRole("button", { name: /enviar/i }));
    expect(await screen.findByText("minha pergunta")).toBeInTheDocument();
  });

  it("disables textarea and button while streaming", async () => {
    renderWithChakra(<ChatInput conversationId={1} onStreamComplete={onStreamComplete} />);
    await user.type(screen.getByPlaceholderText("Digite sua mensagem..."), "pergunta");
    await user.click(screen.getByRole("button", { name: /enviar/i }));
    expect(screen.getByPlaceholderText("Digite sua mensagem...")).toBeDisabled();
    expect(screen.getByRole("button", { name: /enviar/i })).toBeDisabled();
  });

  it("calls onStreamComplete when done event fires", async () => {
    mocks.openStream.mockImplementation((_url: string, callbacks: StreamCallbacks) => {
      callbacks.onDone({ tokens_used: 10, blocked: false });
      return () => {};
    });
    renderWithChakra(<ChatInput conversationId={1} onStreamComplete={onStreamComplete} />);
    await user.type(screen.getByPlaceholderText("Digite sua mensagem..."), "pergunta");
    await user.click(screen.getByRole("button", { name: /enviar/i }));
    await waitFor(() => expect(onStreamComplete).toHaveBeenCalledOnce());
  });

  it("shows toast and refetches messages on stream error", async () => {
    mocks.openStream.mockImplementation((_url: string, callbacks: StreamCallbacks) => {
      callbacks.onError({ code: "SSE_ERROR", message: "Conexão interrompida" });
      return () => {};
    });
    renderWithChakra(<ChatInput conversationId={1} onStreamComplete={onStreamComplete} />);
    await user.type(screen.getByPlaceholderText("Digite sua mensagem..."), "pergunta");
    await user.click(screen.getByRole("button", { name: /enviar/i }));
    await waitFor(() => {
      expect(mocks.showToast).toHaveBeenCalledWith("Conexão interrompida", "error");
      expect(onStreamComplete).toHaveBeenCalledOnce();
    });
  });

  it("accumulates tokens in the partial reply bubble", async () => {
    mocks.openStream.mockImplementation((_url: string, callbacks: StreamCallbacks) => {
      callbacks.onToken("Olá ");
      callbacks.onToken("usuário!");
      return () => {};
    });
    renderWithChakra(<ChatInput conversationId={1} onStreamComplete={onStreamComplete} />);
    await user.type(screen.getByPlaceholderText("Digite sua mensagem..."), "pergunta");
    await user.click(screen.getByRole("button", { name: /enviar/i }));
    expect(await screen.findByText("Olá usuário!")).toBeInTheDocument();
  });
});

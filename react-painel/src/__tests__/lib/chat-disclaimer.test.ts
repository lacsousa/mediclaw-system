import { describe, it, expect } from "vitest";
import { hasEducationalDisclaimer } from "@/lib/chat-disclaimer";

describe("hasEducationalDisclaimer", () => {
  it("detects disclaimer in agent message", () => {
    expect(
      hasEducationalDisclaimer(
        "Esta orientação é educativa e não substitui consulta com profissional de saúde."
      )
    ).toBe(true);
  });

  it("returns false for plain content", () => {
    expect(hasEducationalDisclaimer("Aqui estão seus dados de peso.")).toBe(false);
  });
});

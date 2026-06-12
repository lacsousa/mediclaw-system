import { createSystem, defaultConfig, defineConditions, defineConfig } from "@chakra-ui/react";

/** Impede dark mode por classe ou preferência do SO. */
const lightOnlyConditions = defineConditions({
  dark: "&:not(*)",
  osDark: "&:not(*)",
});

export const mediclawSystem = createSystem(
  defaultConfig,
  defineConfig({
    conditions: lightOnlyConditions,
    globalCss: {
      html: {
        colorScheme: "light",
      },
      body: {
        fontFamily: "body",
        bg: "bg",
        color: "fg",
      },
      "::selection": {
        bg: "teal.100",
        color: "teal.900",
      },
    },
    theme: {
      tokens: {
        fonts: {
          body: {
            value: "var(--font-geist-sans), ui-sans-serif, system-ui, -apple-system, sans-serif",
          },
          heading: {
            value: "var(--font-geist-sans), ui-sans-serif, system-ui, -apple-system, sans-serif",
          },
          mono: {
            value: "var(--font-geist-mono), ui-monospace, monospace",
          },
        },
        shadows: {
          card: {
            value: "0 1px 2px 0 rgb(15 23 42 / 0.04), 0 4px 12px -2px rgb(15 23 42 / 0.06)",
          },
          elevated: {
            value: "0 8px 24px -4px rgb(15 23 42 / 0.08), 0 2px 8px -2px rgb(15 23 42 / 0.04)",
          },
        },
      },
    },
  })
);

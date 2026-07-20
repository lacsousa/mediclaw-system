import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Providers } from "@/components/providers";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const siteUrl = "https://www.mediclaw.com.br";
const siteDescription =
  "Apoio à decisão clínica com IA e evidências: registro conversacional de pacientes, respostas com fontes citadas (RAG) e guardrails éticos. A conduta é sempre do profissional.";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "MediClaw — Apoio à Decisão Clínica com IA e Evidências",
    template: "%s | MediClaw",
  },
  description: siteDescription,
  keywords: [
    "apoio à decisão clínica",
    "IA para médicos",
    "CDSS",
    "assistente de IA para consultório",
    "prontuário conversacional",
    "IA na saúde LGPD",
  ],
  alternates: { canonical: "/" },
  openGraph: {
    type: "website",
    url: siteUrl,
    siteName: "MediClaw",
    title: "MediClaw — Apoio à Decisão Clínica com IA e Evidências",
    description: siteDescription,
    locale: "pt_BR",
    images: [{ url: "/og-image.png", width: 1200, height: 630, alt: "MediClaw" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "MediClaw — Apoio à Decisão Clínica com IA e Evidências",
    description: siteDescription,
    images: ["/og-image.png"],
  },
  robots: { index: true, follow: true },
};

const jsonLd = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      name: "MediClaw",
      url: siteUrl,
      description: "Sistema Inteligente de Apoio à Longevidade e Bem-Estar",
    },
    {
      "@type": "SoftwareApplication",
      name: "MediClaw",
      applicationCategory: "MedicalApplication",
      operatingSystem: "Web",
      url: siteUrl,
      description:
        "Ferramenta de apoio à decisão clínica (CDSS) com LLM e RAG. Não emite diagnóstico nem prescrição.",
      offers: { "@type": "Offer", price: "0", priceCurrency: "BRL" },
    },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="pt-BR"
      className={`light ${geistSans.variable} ${geistMono.variable}`}
      suppressHydrationWarning
    >
      <body>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}

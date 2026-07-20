import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: ["/chat", "/patients", "/admin", "/conhecimento"],
      },
    ],
    sitemap: "https://www.mediclaw.com.br/sitemap.xml",
  };
}

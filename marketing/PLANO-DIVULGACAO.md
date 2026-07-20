# MediClaw — Plano Enxuto de SEO e Divulgação

**Domínio:** https://www.mediclaw.com.br · **Público-alvo:** profissionais de saúde (médicos, nutricionistas, clínicas)
**Última auditoria:** 2026-07-19

---

## 1. Diagnóstico atual (auditoria de 19/07/2026)

| Item | Estado | Ação |
|---|---|---|
| Title | "MediClaw — Assistente de saúde com IA" | Melhorar: incluir termo de busca ("apoio à decisão clínica") |
| Meta description | Genérica ("Converse com um assistente...") e voltada a usuário final, não ao médico | Reescrever para o público profissional |
| robots.txt | **Ausente** | Criar (liberar landing, bloquear rotas do app) |
| sitemap.xml | **Ausente** | Gerar (Next.js `app/sitemap.ts`) |
| Open Graph / Twitter Cards | Ausentes | Adicionar (essencial para compartilhamento no LinkedIn/WhatsApp) |
| Schema.org | Ausente | Adicionar `SoftwareApplication` + `Organization` (JSON-LD) |
| Conteúdo indexável | Home é o app client-rendered — crawlers veem quase nada | Publicar a landing (`marketing/landing/index.html`) como página inicial pública, com SSR/estático |

## 2. Posicionamento

**Frase-mestra:** "Apoio à decisão clínica com IA e evidências — a conduta é sempre sua."

Diferenciais a repetir em todo material: respostas com fontes citadas (RAG, sem caixa-preta); guardrails anti-diagnóstico/anti-prescrição; LGPD por padrão; base de conhecimento própria da clínica.

## 3. Palavras-chave

**Primárias:** apoio à decisão clínica · IA para médicos · assistente de IA para consultório · CDSS
**Secundárias:** prontuário conversacional · IA na saúde LGPD · RAG saúde · software para clínicas com IA
**Cauda longa (conteúdo/blog):** "IA pode dar diagnóstico?" · "como usar IA no consultório com segurança" · "o que é um sistema de apoio à decisão clínica"

## 4. Canais por prioridade

1. **LinkedIn (principal):** posts do time + página do produto; público médico-gestor está lá. 2 posts/semana.
2. **Indicação direta / demonstrações:** e-mail para clínicas e contatos da área; a landing é a página de destino.
3. **Comunidades e sociedades médicas:** eventos, grupos de WhatsApp/Telegram de saúde digital.
4. **SEO orgânico (médio prazo):** blog com as perguntas de cauda longa; resultado esperado em 3–6 meses.
5. **Instagram (opcional):** só se houver fôlego de produção visual.

## 5. Checklist técnico on-page (curto prazo)

- [ ] Publicar landing como home pública em `/` (app passa para `/app` ou subdomínio) ou em `/sobre`
- [ ] Title: `MediClaw — Apoio à Decisão Clínica com IA e Evidências`
- [ ] Meta description orientada ao médico (max ~155 caracteres)
- [ ] robots.txt + sitemap.xml
- [ ] Open Graph (og:title, og:description, og:image 1200×630) e Twitter Card
- [ ] JSON-LD `SoftwareApplication` + `Organization`
- [ ] Google Search Console + Analytics (ou Plausible/Umami, mais alinhado à LGPD)
- [ ] Página de Política de Privacidade (obrigatória p/ LGPD e confiança)

## 6. Roteiro por fases

**Fase 1 — Fundação (semanas 1–2):** checklist técnico acima + perfil LinkedIn + e-mail de contato real no lugar do placeholder `contato@mediclaw.app`.

**Fase 2 — Lançamento (semanas 3–6):** anúncio no LinkedIn (post do time contando a história do projeto); 5 demonstrações agendadas com clínicas/contatos; 2 primeiros artigos de blog (cauda longa).

**Fase 3 — Tração (mês 2+):** ritmo de 1 artigo/quinzena + 2 posts/semana; coletar depoimentos das demos e publicar na landing; medir no Search Console e ajustar keywords.

## 7. Métricas mínimas

Demonstrações agendadas/mês (métrica-chave) · visitas na landing · impressões e cliques no Search Console · seguidores/engajamento no LinkedIn.

---
*Sem vínculo com a marca LW Forge — divulgação por canais próprios do MediClaw.*

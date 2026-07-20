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

## 8. Como mostrar a demonstração: vídeo, animação ou demo interativa?

**Recomendação: demo interativa clicável (não vídeo, não animação) como formato principal, com um vídeo curto de apoio.**

Dados de mercado (2026) mostram que demos interativas convertem cerca de 2x mais que vídeo/PDF passivos e fecham 20–25% mais rápido, porque o médico clica e "faz" o fluxo em vez de assistir. Isso importa especialmente para o público do MediClaw: profissional de saúde tem pouco tempo e decide rápido se algo "parece confiável" — interagir com o produto (mesmo que com dados fictícios) gera mais confiança do que um vídeo editado.

**Por que não só vídeo/animação:**
- Vídeo é passivo — bom para redes sociais (LinkedIn, primeiro contato), ruim para converter em "quero testar".
- Animação (motion graphics) é cara de produzir e refazer a cada nova feature; não mostra o produto real, o que reduz credibilidade em saúde (área que exige prova de que o sistema realmente funciona e é seguro).

**Uso combinado recomendado:**
1. **Demo interativa** (ferramenta abaixo) embutida na landing, seção "Ver como funciona" — visitante clica e navega pelo fluxo real (chat clínico → resposta com fonte citada → guardrail bloqueando prescrição) sem precisar de conta.
2. **Vídeo curto (60–90s)**, gravado a partir da própria demo interativa, para LinkedIn e e-mail de prospecção.
3. **Demo ao vivo** para reuniões 1:1 com clínicas maiores, guiada pelo time.

### Ferramentas do mercado (sem afiliação com nenhuma delas)

| Ferramenta | Ponto forte | Plano gratuito | Indicação |
|---|---|---|---|
| **Supademo** | Grava o fluxo real do MediClaw (screenshots/cliques) e gera demo interativa + vídeo a partir da mesma gravação; IA para personalizar texto | 5 demos, visualizações ilimitadas | **Melhor custo-benefício para começar** |
| **Storylane** | Mais completo (HTML editável nos planos pagos, personalização por segmento, integrações de CRM); referência de mercado | 1 demo apenas | Migrar depois, se precisar de personalização por tipo de clínica |
| **Arcade** | Visual mais "produto de design", cria demo e vídeo da mesma gravação | Trial limitado | Alternativa a Supademo, foco mais visual |
| **HowdyGo** | Captura HTML real (não só screenshot), plano de entrada mais barato | Trial | Se quiser fidelidade máxima ao produto real |
| **Loom / Tella** | Gravação de tela simples com narração — não é interativo, mas rápido de produzir | Gratuito/baixo custo | Só para o vídeo de apoio (item 2 acima), não como demo principal |

**Ponto de atenção específico de saúde:** usar sempre dados de paciente fictícios/sintéticos na demo (nunca dados reais), e deixar isso explícito ("dados de demonstração, não é paciente real") — reforça o cuidado com LGPD que já é diferencial do produto.

**Próximo passo prático:** gravar 3 fluxos no Supademo (free) — chat com resposta citando fonte, guardrail bloqueando prescrição, e busca na base de conhecimento — embutir o primeiro na landing e usar os outros dois em prospecção.

---
*Sem vínculo com a marca LW Forge — divulgação por canais próprios do MediClaw.*

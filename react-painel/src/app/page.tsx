import Link from "next/link";

const css = `
.mc-landing{--teal:#0F766E;--teal-dark:#134E4A;--amber:#D97706;--bg:#FAFAF7;--bg-soft:#ECF5F3;--ink:#1C2B2A;--ink-soft:#5B6B69;--radius:14px;font-family:'Inter',system-ui,sans-serif;color:var(--ink);background:var(--bg);line-height:1.6}
.mc-landing h1,.mc-landing h2,.mc-landing h3{font-family:'Fraunces',Georgia,serif;line-height:1.2;font-weight:600}
.mc-landing a{color:inherit}
.mc-landing .wrap{max-width:1080px;margin:0 auto;padding:0 24px}
.mc-landing .btn{display:inline-block;padding:14px 28px;border-radius:999px;font-weight:600;text-decoration:none;transition:.2s}
.mc-landing .btn-primary{background:var(--amber);color:#fff}
.mc-landing .btn-primary:hover{background:#b45f05}
.mc-landing .btn-ghost{border:1.5px solid var(--teal);color:var(--teal)}
.mc-landing .btn-ghost:hover{background:var(--bg-soft)}
.mc-landing .tag{display:inline-block;background:var(--bg-soft);color:var(--teal-dark);font-size:.8rem;font-weight:600;padding:6px 14px;border-radius:999px;letter-spacing:.03em;text-transform:uppercase}
.mc-landing header{padding:20px 0;border-bottom:1px solid #e5e7e3;background:var(--bg);position:sticky;top:0;z-index:10}
.mc-landing header .wrap{display:flex;align-items:center;justify-content:space-between}
.mc-landing .logo{font-family:'Fraunces',Georgia,serif;font-size:1.4rem;font-weight:600;color:var(--teal-dark);text-decoration:none}
.mc-landing .logo span{color:var(--amber)}
.mc-landing nav a{text-decoration:none;color:var(--ink-soft);font-size:.95rem;margin-left:24px;font-weight:500}
.mc-landing nav a:hover{color:var(--teal)}
.mc-landing .hero{padding:88px 0 72px;text-align:center}
.mc-landing .hero h1{font-size:clamp(2rem,5vw,3.2rem);max-width:800px;margin:20px auto 0;color:var(--teal-dark)}
.mc-landing .hero p.lead{max-width:640px;margin:24px auto 36px;font-size:1.15rem;color:var(--ink-soft)}
.mc-landing .hero .cta{display:flex;gap:14px;justify-content:center;flex-wrap:wrap}
.mc-landing .disclaimer{background:var(--teal-dark);color:#d8ece9;font-size:.9rem;text-align:center;padding:12px 24px}
.mc-landing .disclaimer strong{color:#fff}
.mc-landing section{padding:72px 0}
.mc-landing section.alt{background:var(--bg-soft)}
.mc-landing .sec-head{text-align:center;max-width:640px;margin:0 auto 48px}
.mc-landing .sec-head h2{font-size:clamp(1.6rem,3.5vw,2.2rem);color:var(--teal-dark);margin-top:14px}
.mc-landing .sec-head p{color:var(--ink-soft);margin-top:12px}
.mc-landing .grid{display:grid;gap:24px}
.mc-landing .grid-3{grid-template-columns:repeat(auto-fit,minmax(280px,1fr))}
.mc-landing .card{background:#fff;border:1px solid #e5e7e3;border-radius:var(--radius);padding:28px}
.mc-landing .card .ico{width:44px;height:44px;border-radius:10px;background:var(--bg-soft);display:flex;align-items:center;justify-content:center;font-size:1.3rem;margin-bottom:16px}
.mc-landing .card h3{font-size:1.1rem;margin-bottom:8px;color:var(--teal-dark)}
.mc-landing .card p{font-size:.95rem;color:var(--ink-soft)}
.mc-landing .steps{counter-reset:step}
.mc-landing .step{display:flex;gap:20px;align-items:flex-start;margin-bottom:32px}
.mc-landing .step-n{flex-shrink:0;width:40px;height:40px;border-radius:50%;background:var(--teal);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700}
.mc-landing .step h3{color:var(--teal-dark);margin-bottom:4px}
.mc-landing .step p{color:var(--ink-soft);font-size:.95rem}
.mc-landing .trust{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:24px}
.mc-landing .trust .card{border-left:4px solid var(--teal)}
.mc-landing .stack{display:flex;flex-wrap:wrap;gap:10px;justify-content:center}
.mc-landing .stack span{background:#fff;border:1px solid #e5e7e3;border-radius:999px;padding:8px 18px;font-size:.88rem;color:var(--ink-soft);font-weight:500}
.mc-landing .final{background:var(--teal-dark);color:#fff;text-align:center}
.mc-landing .final h2{color:#fff;font-size:clamp(1.6rem,3.5vw,2.2rem)}
.mc-landing .final p{color:#bcd9d5;max-width:560px;margin:16px auto 32px}
.mc-landing footer{padding:36px 0;font-size:.85rem;color:var(--ink-soft);text-align:center}
.mc-landing footer .fine{max-width:720px;margin:12px auto 0;font-size:.78rem}
`;

export default function LandingPage() {
  return (
    <div className="mc-landing">
      <link
        rel="stylesheet"
        href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Inter:wght@400;500;600;700&display=swap"
      />
      <style>{css}</style>

      <header>
        <div className="wrap">
          <Link className="logo" href="/">
            Medi<span>Claw</span>
          </Link>
          <nav>
            <Link href="#como-funciona">Como funciona</Link>
            <Link href="#recursos">Recursos</Link>
            <Link href="#seguranca">Segurança</Link>
            <Link href="/login" style={{ marginLeft: 24 }}>
              Entrar
            </Link>
            <Link
              className="btn btn-primary"
              style={{ padding: "10px 22px", marginLeft: 24 }}
              href="/register"
            >
              Solicitar demonstração
            </Link>
          </nav>
        </div>
      </header>

      <div className="disclaimer">
        <strong>Ferramenta de apoio à decisão clínica (CDSS).</strong> O MediClaw não emite
        diagnóstico nem prescrição — a conduta é sempre do profissional habilitado.
      </div>

      <section className="hero">
        <div className="wrap">
          <span className="tag">IA + Evidências para a prática clínica</span>
          <h1>Mais tempo olhando para o paciente. Menos tempo procurando informação.</h1>
          <p className="lead">
            O MediClaw é um assistente de IA para profissionais de saúde: registre dados do
            paciente conversando, receba hipóteses e sugestões de investigação embasadas em
            literatura indexada, e mantenha o controle clínico do início ao fim.
          </p>
          <div className="cta">
            <Link className="btn btn-primary" href="/register">
              Solicitar demonstração
            </Link>
            <Link className="btn btn-ghost" href="#como-funciona">
              Ver como funciona
            </Link>
          </div>
        </div>
      </section>

      <section className="alt" id="como-funciona">
        <div className="wrap">
          <div className="sec-head">
            <span className="tag">Como funciona</span>
            <h2>Do atendimento à evidência em três passos</h2>
          </div>
          <div className="steps" style={{ maxWidth: 680, margin: "0 auto" }}>
            <div className="step">
              <div className="step-n">1</div>
              <div>
                <h3>Converse durante o atendimento</h3>
                <p>
                  Registre queixas, sinais vitais e histórico do paciente em linguagem natural. O
                  assistente estrutura os dados automaticamente no prontuário.
                </p>
              </div>
            </div>
            <div className="step">
              <div className="step-n">2</div>
              <div>
                <h3>Receba apoio embasado</h3>
                <p>
                  O pipeline RAG consulta a base de conhecimento curada — diretrizes, artigos e
                  protocolos indexados — e devolve hipóteses diferenciais e sugestões de
                  investigação com as fontes citadas.
                </p>
              </div>
            </div>
            <div className="step">
              <div className="step-n">3</div>
              <div>
                <h3>Decida com autonomia</h3>
                <p>
                  Guardrails determinísticos impedem que a IA feche diagnósticos ou prescreva.
                  Toda resposta é apoio: a decisão clínica permanece com você.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="recursos">
        <div className="wrap">
          <div className="sec-head">
            <span className="tag">Recursos</span>
            <h2>O que já está funcionando</h2>
          </div>
          <div className="grid grid-3">
            <div className="card">
              <div className="ico">💬</div>
              <h3>Chat clínico em tempo real</h3>
              <p>
                Assistente conversacional com streaming de respostas, contextualizado pelos dados
                do paciente em atendimento.
              </p>
            </div>
            <div className="card">
              <div className="ico">📚</div>
              <h3>Base de conhecimento própria</h3>
              <p>
                Ingestão de PDFs, artigos e protocolos da sua instituição. As respostas citam as
                evidências indexadas — nada de &quot;caixa-preta&quot;.
              </p>
            </div>
            <div className="card">
              <div className="ico">🗂️</div>
              <h3>Gestão de pacientes</h3>
              <p>Cadastro, histórico de saúde e registro conversacional integrados em um só lugar.</p>
            </div>
            <div className="card">
              <div className="ico">🧮</div>
              <h3>Skills clínicas auxiliares</h3>
              <p>
                Cálculo de IMC, conversão de unidades e agregação de histórico executados de forma
                determinística, sem depender do LLM.
              </p>
            </div>
            <div className="card">
              <div className="ico">📊</div>
              <h3>Painel administrativo</h3>
              <p>Métricas de uso e acompanhamento da operação para gestores de clínicas e equipes.</p>
            </div>
            <div className="card">
              <div className="ico">🔌</div>
              <h3>IA configurável</h3>
              <p>
                Compatível com múltiplos provedores de LLM (OpenAI, Google Gemini), sem
                aprisionamento tecnológico.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="alt" id="seguranca">
        <div className="wrap">
          <div className="sec-head">
            <span className="tag">Segurança e ética</span>
            <h2>Feito para o rigor da área da saúde</h2>
            <p>Transparência sobre o que a IA faz — e principalmente sobre o que ela não faz.</p>
          </div>
          <div className="trust">
            <div className="card">
              <h3>Guardrails anti-diagnóstico</h3>
              <p>
                Filtros pré e pós-LLM bloqueiam prescrições, diagnósticos fechados e respostas a
                urgências. A IA orienta; o profissional decide.
              </p>
            </div>
            <div className="card">
              <h3>LGPD por padrão</h3>
              <p>
                Dados de saúde são tratados como dados pessoais sensíveis. Nenhuma informação
                identificável é registrada em logs.
              </p>
            </div>
            <div className="card">
              <h3>Autenticação segura</h3>
              <p>Acesso controlado por autenticação JWT e perfis de permissão por papel.</p>
            </div>
            <div className="card">
              <h3>Qualidade verificada</h3>
              <p>
                Mais de 170 testes automatizados entre backend e frontend cobrindo os fluxos
                críticos da plataforma.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section>
        <div className="wrap">
          <div className="sec-head">
            <span className="tag">Tecnologia</span>
            <h2>Arquitetura moderna e auditável</h2>
          </div>
          <div className="stack">
            <span>Next.js</span>
            <span>Django 5.2</span>
            <span>PostgreSQL 16</span>
            <span>ChromaDB</span>
            <span>LangChain</span>
            <span>RAG</span>
            <span>OpenAI · Gemini</span>
            <span>Streaming SSE</span>
            <span>JWT</span>
          </div>
        </div>
      </section>

      <section className="final" id="contato">
        <div className="wrap">
          <h2>Veja o MediClaw em ação</h2>
          <p>
            Agende uma demonstração para sua clínica, consultório ou equipe de saúde e avalie o
            assistente com seus próprios protocolos.
          </p>
          <Link className="btn btn-primary" href="/register">
            Agendar demonstração
          </Link>
        </div>
      </section>

      <footer>
        <div className="wrap">
          <div>
            <strong>MediClaw</strong> — Sistema Inteligente de Apoio à Longevidade e Bem-Estar
          </div>
          <p className="fine">
            O MediClaw é uma ferramenta de apoio à decisão clínica e não substitui avaliação,
            diagnóstico ou tratamento por profissional de saúde habilitado. Todas as respostas
            geradas por IA são de caráter informativo e devem ser validadas pelo profissional
            responsável. Dados de saúde são tratados em conformidade com a LGPD.
          </p>
        </div>
      </footer>
    </div>
  );
}

---
name: apresentacao-cards
description: Motor de montagem atômica para criar apresentações interativas em HTML/Tailwind usando componentes Glassmorphism modulares com navegação card-a-card.
---

# Skill: Apresentação de Dados em Cards Animados

## 📝 Instruções de Execução
Você deve atuar como um engenheiro de front-end especializado em UX/UI. Seu objetivo é transformar dados brutos em uma página HTML única e elegante, selecionando e injetando componentes da pasta `/templates`.

### Passo 1: Análise e Mapeamento de Dados
Examine a fonte de conteúdo e selecione o template mais adequado para cada seção:
- **Demonstração de Código:** `card_code.html` (Use para snippets de programação ou configurações).
- **Dados Tabulares:** `card_tabela.html` (Você tem autonomia para aumentar/diminuir o número de linhas e colunas conforme a necessidade dos dados).
- **Comparativos/Preços:** `card_destaques.html`
- **Cronogramas/Processos:** `card_timeline.html`
- **Estatísticas/Listas:** `card_lista.html`
- **Destaque Visual:** `card_imagem.html`
- **Grids/Categorias:** `card_grid.html`
- **Metas/Progresso:** `card_progresso.html`
- **Citações/Insights:** `card_citacao.html`
- **Chamada para Ação (CTA):** `card_cta.html` (OBRIGATÓRIO: Inserir sempre no meio da apresentação, após a definição do problema/dor e antes da solução detalhada).

### Passo 2: Configuração de Componentes
Para cada template selecionado:
1. **Placeholders:** Substitua rigorosamente os termos entre colchetes (ex: `[TITULO]`, `[VALOR]`, `[CODIGO]`) pelos dados reais extraídos da fonte.
2. **Ícones:** Escolha nomes de ícones compatíveis com a biblioteca [Lucide](https://lucide.dev/icons).
3. **Animações:** Incremente o atributo `data-aos-delay="[DELAY]"` em 100ms para cada novo card inserido (ex: 100, 200, 300...) para garantir um efeito de cascata fluido.

### Passo 3: Montagem do Arquivo Final
Gere o arquivo em `presents/[nome_da_feature]/index.html` realizando a concatenação na seguinte ordem:

1.  **Layout Base (Início):** Conteúdo do `layout_base.html` até a tag `<body>`.
2.  **Abertura:** Injeção do `header.html`.
3.  **Corpo Dinâmico:** Sequência de cards processados nos Passos 1 e 2.
4.  **Encerramento:** Injeção do `footer.html` + fechamento das tags contidas no final do `layout_base.html`.

## 🎨 Regras de Estilo e Design
- **Paleta:** Fundo escuro `#222222`, detalhes em laranja `#FFA203`.
- **Glassmorphism:** Manter obrigatoriamente `backdrop-filter: blur(10px)` e bordas semi-transparentes em todos os cards.
- **Tabelas Dinâmicas:** Ao manipular o `card_tabela.html`, garanta que o número de colunas no `<thead>` corresponda exatamente ao número de colunas no `<tbody>`.
- **Segurança de Código:** No `card_code.html`, converta caracteres especiais (como `<` e `>`) em entidades HTML (`&lt;` e `&gt;`) para evitar quebra de renderização.

## 🧭 Navegação Card-a-Card
A apresentação inclui um sistema de navegação obrigatório que permite ao usuário avançar slide a slide:

### Comportamento
- **Espaçamento:** O script `setupFullScreenWrappers()` envolve automaticamente cada card em um container `min-h-screen` flexível, garantindo centralização vertical perfeita e navegação robusta.
- **Botão "Começar" no Header:** Localizado na parte inferior do header, leva o usuário ao primeiro card (centralizado na viewport).
- **Botão Flutuante "Próximo Card":** Botão fixo no canto inferior direito (`#next-card`), aparece após 300px de scroll.
  - Cada clique avança para o próximo card, centralizando-o na tela via `scrollIntoView({ behavior: 'smooth', block: 'center' })`.
  - Ao chegar no final da página, o ícone muda para seta para cima e o clique volta ao topo.
- **Barra de Progresso:** Uma barra fixa no topo da página mostra o progresso de leitura.
- **Navegação por Teclado:**
  - **Seta Direita/Baixo ou PageDown:** Avança para o próximo card.
  - **Seta Esquerda/Cima ou PageUp:** Retorna ao card anterior.

### Detecção de Seções
O JavaScript detecta automaticamente todas as seções filhas diretas do `<main>` (`.glass-card` e `div`) e as utiliza como pontos de navegação.

### Implementação
Esses elementos já estão integrados nos templates `layout_base.html` e `header.html`. Não é necessário adicionar código extra — basta seguir o fluxo de montagem do Passo 3.

## 🚀 Saída Esperada
Um arquivo `index.html` completo, autossuficiente, com scripts de animação (AOS), ícones (Lucide), contadores automáticos e navegação card-a-card funcionando perfeitamente.
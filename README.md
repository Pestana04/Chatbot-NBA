# Chatbot NBA 🏀

Trabalho da faculdade: Desenvolvimento de um chatbot com interface web utilizando Python e NLTK.

O tema escolhido para este chatbot exploratório foi **NBA (National Basketball Association)**, onde o usuário pode interagir e perguntar sobre alguns dos principais jogadores, times e regras básicas do jogo.

## Requisitos
- Linguagem de Programação: Python
- NLP: NLTK (Natural Language Toolkit) utilizado para tokenizar e remover stopwords da entrada, para simular uma inteligência do bot.
- Base de conhecimento: estrutura local em `dados.json`, consultada pelo agente **antes** de qualquer chamada ao modelo de linguagem.
- LLM (modelo de linguagem): um modelo da plataforma [Hugging Face](https://huggingface.co/models), rodando localmente via `transformers`, usado como **fallback** quando a base de conhecimento não tem resposta.
- Interface Web: Desenvolvida com HTML, CSS e JavaScript (tudo no mesmo arquivo pra facilitar hehe) e servida usando o framework Flask.

## Fluxo do agente (Base de conhecimento + LLM)

O sistema segue o fluxo exigido pelo trabalho:

1. O agente **primeiro** tenta responder usando a base de conhecimento estruturada (`dados.json`): saudações, palavras-chave dos times e o banco de conversas.
2. **Caso não haja informação suficiente**, o agente aciona a **LLM como fallback** (`llm_local.py`), que gera a resposta com um modelo da Hugging Face.
3. Cada resposta vem marcada com sua **fonte**, exibida na interface:
   - 🗂️ **Base de dados** — veio da base de conhecimento (`dados.json`);
   - 🧠 **IA (LLM Hugging Face)** — gerada pela LLM como fallback;
   - 🤖 **Resposta padrão** — mensagem de orientação (usada quando a LLM não está disponível).

Como o chatbot é poliglota, a mensagem do usuário é traduzida para português antes do processamento e a resposta (da base ou da LLM) é traduzida de volta para o idioma do usuário.

### Configuração da LLM (opcional)

O modelo padrão é o [`Qwen/Qwen2.5-0.5B-Instruct`](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct) — um modelo instruído e multilíngue da Hugging Face, leve o bastante para rodar localmente. Dá para trocar por qualquer outro modelo de geração de texto da Hugging Face via variáveis de ambiente:

```bash
export LLM_MODELO="Qwen/Qwen2.5-0.5B-Instruct"   # nome do modelo na Hugging Face
export LLM_MAX_TOKENS="150"                       # tamanho máximo da resposta gerada
```

> Modelos instruídos (com *chat template*) são usados via formato de conversa; modelos simples como o GPT-2 caem automaticamente num prompt de texto puro.

> Na primeira execução, o `transformers` baixa os pesos do modelo automaticamente (pode demorar). Se as dependências da LLM não estiverem instaladas, o app continua funcionando normalmente com a base de conhecimento e a resposta padrão.

## Decisões de Desenvolvimento
1. **Framework:** Usamos o Flask porque é muito simples e rápido de rodar um servidor local pra testes da faculdade.
2. **NLTK:** Usamos o `word_tokenize` para quebrar as frases do usuário em palavras isoladas e removemos a pontuação e stopwords (palavras inúteis como "o", "a", "de") usando o `stopwords.words('portuguese')` pra facilitar o match.
3. **Lógica do Bot:** Como optamos por não usar um modelo complexo de IA (pra não pesar e porque o banco de respostas era permitido), usamos um "banco de respostas" (um dicionário gigante) mapeado com palavras-chave do universo da NBA. O código procura nas palavras que o usuário digitou se tem uma palavra-chave correspondente e devolve a resposta.
4. **Interface:** Resolvemos fazer uma interface simples, com CSS direto no HTML simulando uma tela de celular ou de chat padrão, com as cores da NBA (Azul e Vermelho).

## Como rodar o projeto

1. Tenha o Python instalado na sua máquina.
2. Abra o terminal na pasta do projeto e instale o que precisa:
   ```bash
   pip install -r requirements.txt
   ```
3. Execute o backend Flask:
   ```bash
   python app.py
   ```
4. Abra o seu navegador e acesse: `http://localhost:5000`

## Feito por
- [Augusto Brando]
- [Arthur Schultz]
- [Gustavo Pestana]
- [Eduardo de Oliveira]
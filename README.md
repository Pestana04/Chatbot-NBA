# Chatbot NBA 🏀

Trabalho da faculdade: Desenvolvimento de um chatbot com interface web utilizando Python e NLTK.

O tema escolhido para este chatbot exploratório foi **NBA (National Basketball Association)**, onde o usuário pode interagir e perguntar sobre alguns dos principais jogadores, times e regras básicas do jogo.

## Requisitos
- Linguagem de Programação: Python
- NLP: NLTK (Natural Language Toolkit) utilizado para tokenizar e remover stopwords da entrada, para simular uma inteligência do bot.
- Interface Web: Desenvolvida com HTML, CSS e JavaScript (tudo no mesmo arquivo pra facilitar hehe) e servida usando o framework Flask.

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
# app.py
from flask import Flask, render_template, request, jsonify
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string

app = Flask(__name__)

# O aluno normalmente baixa isso pelo script "pra ter ctz", vou deixar uma gambiarra pra baixar se não tiver
try:
    nltk.data.find('tokenizers/punkt_tab')
except Exception:
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
    
try:
    nltk.data.find('corpora/stopwords')
except Exception:
    nltk.download('stopwords', quiet=True)


# Banco de respostas simples (dicionario sujo com respostas fixas)
respostas_nba = {
    "lebron": "LeBron James é um dos maiores jogadores de todos os tempos, atualmente joga no Los Angeles Lakers. O cara é brabo!",
    "jordan": "Michael Jordan é considedado por muitos o GOAT (maior de todos os tempos) da NBA. Ganhou 6 títulos com o Chicago Bulls nos anos 90.",
    "celtics": "O Boston Celtics é uma das franquias mais tradicionais e tem o maior número de títulos da NBA atualmente, dividindo o pódio com os Lakers ou até passando eles recentemente (18 títulos).",
    "lakers": "O Los Angeles Lakers é famoso pelos seus 17 títulos e por lendas como Kobe Bryant, Magic Johnson, Kareem e Shaquille O'Neal. E agora com o Papai LeBron.",
    "kobe": "Kobe Bryant, o Black Mamba! Jogou a vida toda nos Lakers e marcou 81 pontos em um único jogo contra os Raptors.",
    "curry": "Stephen Curry mudou o basquete para sempre com suas bolas de 3 pontos absurdas. Maior arremessador da história, joga no Golden State Warriors.",
    "warriors": "O Golden State Warriors construiu uma baita dinastia na última década com Curry, Klay Thompson e Draymond Green.",
    "regras": "No basquete da NBA, cada equipe tem 5 jogadores em quadra. Arremessos normais valem 2 pontos, de trás da linha valem 3 pontos, e lances livres valem 1 ponto. Dá pra andar só quicando a bola ou dando até 2 passos antes da bandeja.",
    "finais": "As finais da NBA acontecem geralmente em junho, onde o campeão da Conferência Leste enfrenta o campeão do Oeste numa série melhor de 7 jogos (quem ganhar 4 primeiro é campeão).",
    "mvp": "O prêmio de MVP (Most Valuable Player) é dado ao melhor jogador da temporada. Nikola Jokic e Giannis ganharam vários nesses últimos anos.",
    "jogadores": "Na NBA tem muitas estrelas hoje: LeBron, Curry, Durant, Antetokounmpo, Jokic, Doncic, Tatum, entre outros.",
    "times": "São 30 times na NBA divididos em Conferência Leste e Oeste. Os mais conhecidos são Lakers, Celtics, Bulls, Warriors, Heat...",
    "ola": "E aí! Tudo bem? Me pergunte sobre jogadores da NBA, times, regras ou como funciona o jogo!",
    "oi": "Faaala! Manda a sua dúvida de basquete ou de NBA aí pra mim.",
    "default": "Putz, não entendi bem. Tenta perguntar o nome de algum jogador famoso (ex: LeBron, Jordan, Curry) ou sobre times (Lakers, Celtics) ou regras."
}

def processar_texto(texto):
    # Processamento simples com NLTK
    tokens = word_tokenize(texto.lower(), language='portuguese')
    # Remove pontuacao e stopwords de forma bem basica
    stop_words = set(stopwords.words('portuguese'))
    palavras_limpas = [p for p in tokens if p not in stop_words and p not in string.punctuation]
    return palavras_limpas

def obter_respostas(mensagem):
    palavras = processar_texto(mensagem)
    
    # tenta achar alguma palavra chave na mensagem
    for palavra in palavras:
        if palavra in respostas_nba:
            return respostas_nba[palavra]
            
    # um hardcode pra saudar o usuario se ele disser oi
    mensagem_lower = mensagem.lower()
    if "oi" in mensagem_lower or "olá" in mensagem_lower or "bom dia" in mensagem_lower or "boa tarde" in mensagem_lower:
         return respostas_nba["ola"]
         
    return respostas_nba["default"]


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    # pega a mensagem do form do javascript
    user_message = request.form.get("msg")
    
    if not user_message:
        return jsonify({"response": "Manda uma mensagem válida!"})
        
    bot_response = obter_respostas(user_message)
    return jsonify({"response": bot_response})

if __name__ == "__main__":
    # Roda em modo debug pq é trabalho de aluno
    app.run(debug=True, port=5000)

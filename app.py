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
    "jordan": "Michael Jordan é considerado por muitos o GOAT (maior de todos os tempos) da NBA. Ganhou 6 títulos com o Chicago Bulls nos anos 90.",
    "celtics": "O Boston Celtics é uma das franquias mais tradicionais e tem 18 títulos da NBA, sendo um dos maiores campeões da história.",
    "lakers": "O Los Angeles Lakers é famoso pelos seus 17 títulos e por lendas como Kobe Bryant, Magic Johnson, Kareem e Shaquille O'Neal. E agora com o Papai LeBron.",
    "kobe": "Kobe Bryant, o Black Mamba! Jogou a vida toda nos Lakers e marcou 81 pontos em um único jogo contra os Raptors.",
    "curry": "Stephen Curry mudou o basquete para sempre com suas bolas de 3 pontos absurdas. Maior arremessador da história, joga no Golden State Warriors.",
    "warriors": "O Golden State Warriors construiu uma baita dinastia na última década com Curry, Klay Thompson e Draymond Green.",
    "regras": "Na NBA, cada time tem 5 jogadores em quadra. Cestas valem 2 ou 3 pontos, e lance livre vale 1 ponto. Cada jogo tem 4 quartos de 12 minutos.",
    "finais": "As finais da NBA acontecem geralmente em junho. O campeão do Leste enfrenta o campeão do Oeste em uma série melhor de 7 jogos.",
    "mvp": "O prêmio de MVP (Most Valuable Player) é dado ao melhor jogador da temporada regular. Jokic, Giannis e Embiid ganharam recentemente.",
    "jogadores": "Na NBA tem muitas estrelas hoje: LeBron, Curry, Durant, Antetokounmpo, Jokic, Doncic, Tatum, entre outros.",
    "times": "São 30 times na NBA divididos em Conferência Leste e Oeste.",
    "durant": "Kevin Durant é um dos maiores pontuadores da história recente da NBA. Já foi campeão com o Warriors e é conhecido pelo seu arremesso quase impossível de marcar.",
    "giannis": "Giannis Antetokounmpo, o 'Greek Freak', joga no Milwaukee Bucks. Foi MVP duas vezes e campeão da NBA em 2021.",
    "jokic": "Nikola Jokic é um pivô extremamente técnico do Denver Nuggets. MVP múltiplas vezes e campeão da NBA em 2023.",
    "doncic": "Luka Doncic é o astro do Dallas Mavericks. Mesmo jovem, já é considerado um dos jogadores mais completos da liga.",
    "bulls": "O Chicago Bulls ficou eternizado nos anos 90 com Michael Jordan e Scottie Pippen, conquistando 6 títulos.",
    "playoffs": "Os playoffs reúnem os 8 melhores times de cada conferência. As séries são disputadas em melhor de 7 jogos.",
    "draft": "O Draft da NBA é o evento onde os times escolhem novos jogadores que vêm do basquete universitário ou internacional.",
    "allstar": "O All-Star Game é o jogo das estrelas da NBA, reunindo os melhores jogadores da temporada em um evento festivo.",
    
    "ola": "E aí! Tudo bem? Me pergunte sobre jogadores da NBA, times, regras ou como funciona o jogo!",
    "oi": "Faaala! Manda a sua dúvida de basquete ou de NBA aí pra mim.",
    "default": "Putz, não entendi bem. Tenta perguntar o nome de algum jogador famoso (ex: LeBron, Jordan, Curry) ou sobre times (Lakers, Celtics) ou regras."
}

# Lista de palavrões
PALAVROES_BLOQUEADOS = {
    "porra", "caralho", "merda", "bosta", "cacete",
    "fdp", "puta", "desgraça", "desgraca",
    "arrombado", "otario", "babaca", "idiota"
}


def processar_texto(texto):
    # Processamento simples com NLTK
    tokens = word_tokenize(texto.lower(), language='portuguese')
    # Remove pontuacao e stopwords
    stop_words = set(stopwords.words('portuguese'))
    palavras_limpas = [p for p in tokens if p not in stop_words and p not in string.punctuation]
    return palavras_limpas

def contem_palavrao(texto):
    palavras = word_tokenize(texto.lower(), language='portuguese')

    for palavra in palavras:
        palavra = palavra.strip(string.punctuation)
        if palavra in PALAVROES_BLOQUEADOS:
            return True
    return False

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

    if contem_palavrao(user_message):
        return jsonify({
            "response": "Opa campeão, vamos evitar o xingamento, todo mundo aqui é amigo!"
        })
        
    bot_response = obter_respostas(user_message)
    return jsonify({"response": bot_response})

if __name__ == "__main__":
    # Roda em modo debug pq é trabalho de aluno
    app.run(debug=True, port=5000)
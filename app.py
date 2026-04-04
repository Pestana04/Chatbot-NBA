from flask import Flask, render_template, request, jsonify
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string

app = Flask(__name__)

# Dicionário para armazenar a memória do usuário (time escolhido + progresso da conversa)
user_memory = {}

# Progresso de conversa - qual pergunta o bot deve fazer próximo
PROGRESSO_CONVERSA = {
    "lakers": ["lakers_historia", "lakers_jogadores", "lakers_titulos", "lakers_estadio", "lakers_conferenciaatualmente", "lakers_tecnico", "lakers_rivalidade", "lakers_presente", "lakers_futuro"],
    "celtics": ["celtics_historia", "celtics_jogadores", "celtics_titulos", "celtics_estadio", "celtics_conferenciaatualmente", "celtics_tecnico", "celtics_rivalidade", "celtics_presente", "celtics_futuro"]
}

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


# Saudações
SAUDACOES = {
    "oi": "E aí! Tudo bem com você? Quer conhecer sobre o Lakers ou Celtics?",
    "opa" : "Opa! Que bom te ver por aqui. Qual time você quer explorar: Lakers ou Celtics?",
    "ola": "Faaala! Que legal você estar aqui. Qual time você quer explorar: Lakers ou Celtics?",
    "bom dia": "Bom dia campeão! Que tal conversarmos sobre os maiores times da NBA?",
    "boa tarde": "Boa tarde! Bora bater um papo sobre basquete?",
    "boa noite": "Boa noite! Já escolheu um time para aprender mais?",
    "tudo bem": "Tudo certo por aqui! E aí, manda a sua pergunta de NBA!",
    "obrigado": "De nada, campeão! Tem mais alguma pergunta?",
    "valeu": "Tranquilo! Bora continuar a conversa?"
}

# Banco de conversas dinâmico - 20 pares Q&A
# Estrutura: chave pode ser uma palavra-chave genérica ou específica de time
BANCO_CONVERSAS = {
    # Perguntas introdutórias / Escolha de time
    "quer saber": "Maneiro! Qual time interessa você? Posso te contar tudo sobre o Lakers ou Celtics!",
    "qual time": "Ótimo! Qual é o seu favorito? Lakers ou Celtics?",
    "escolha": "Beleza! Você quer aprender sobre Lakers ou Celtics?",
    
    # Lakers - Perguntas específicas (10 respostas)
    "lakers_historia": {
        "resposta": "Os Lakers têm uma história LENDÁRIA! Fundados em 1948, conquistaram 17 títulos NBA. A franquia marcou gerações com ícones como Magic Johnson (80s), Kobe Bryant (2000s) e agora com LeBron James. É praticamente a monarquia do basquete!",
        "sugestao": "Quer saber sobre os maiores nomes que jogaram lá?"
    },
    "lakers_jogadores": {
        "resposta": "Os Lakers tiveram os MAIORES! Magic Johnson (showtime), Kobe Bryant (Black Mamba), Shaquille O'Neal (Diesel), Kareem Abdul-Jabbar e agora LeBron James. Cada um deixou sua marca eterna. Uma dinastia atrás da outra!",
        "sugestao": "Quer conhecer quantos títulos o Lakers conquistou?"
    },
    "lakers_titulos": {
        "resposta": "Os Lakers venceram 17 campeonatos NBA! Ganharam 5 com Magic nos 80s, 3 com Shaq e Kobe nos 2000s, e estão sempre buscando mais. O time não para de lutar por esses anéis, meu!",
        "sugestao": "Quer saber onde o Lakers joga?"
    },
    "lakers_estadio": {
        "resposta": "Os Lakers jogam no Crypto.com Arena em Los Angeles (antes era Staples Center). É uma arena SHOW, palco de muitos momentos históricos do basquete e da NBA!",
        "sugestao": "Quer conhecer em qual conferência o Lakers compete?"
    },
    "lakers_conferenciaatualmente": {
        "resposta": "Atualmente, o Lakers está na Conferência Oeste da NBA e é sempre um dos times a se tomar cuidado. Com LeBron liderando, eles estão sempre na briga pelo campeonato!",
        "sugestao": "Quer saber quem é o técnico do Lakers?"
    },
    "lakers_tecnico": {
        "resposta": "O técnico atual do Lakers trabalha com o elenco para manter o nível alto. O time tem um padrão de excelência que vem desde os primeiros dias da franquia!",
        "sugestao": "Quer conhecer a rivalidade do Lakers com outros times?"
    },
    "lakers_rivalidade": {
        "resposta": "Os Lakers têm grandes rivalidades, especialmente com o Boston Celtics! Essa é umas das maiores rivalidades da NBA, com encontros épicos nas finais ao longo das décadas!",
        "sugestao": "Quer saber como está o Lakers atualmente?"
    },
    "lakers_presente": {
        "resposta": "Atualmente, o Lakers conta com LeBron James como estrela máxima, levando o time para novos patamares. Eles sempre estão na briga pelo título com um elenco competitivo!",
        "sugestao": "Quer saber qual é o futuro do Lakers?"
    },
    "lakers_futuro": {
        "resposta": "O futuro do Lakers é brilhante! Com LeBron e um elenco talentoso, a franquia continua investindo em jogadores de elite para conquistar mais títulos!",
        "sugestao": "Quer explorar o Boston Celtics também?"
    },
    
    # Celtics - Perguntas específicas (10 respostas)
    "celtics_historia": {
        "resposta": "O Boston Celtics é LENDÁRIO demais! Fundado em 1957, conquistou 18 títulos NBA - O MAIS CAMPEÃO de todos! A era de ouro foi nos 60s com Bill Russell vencendo 11 títulos em 13 anos. Que domínio!",
        "sugestao": "Quer conhecer os maiores nomes que jogaram lá?"
    },
    "celtics_jogadores": {
        "resposta": "Os Celtics tiveram GIGANTES! Bill Russell (símbolo da defesa), John Havlicek (clutch), Larry Bird (tiro de 3), Paul Pierce (The Truth) e agora Jayson Tatum e Jaylen Brown liderando. Lenda atrás de lenda!",
        "sugestao": "Quer saber quantos títulos o Celtics conquistou?"
    },
    "celtics_titulos": {
        "resposta": "Os Celtics conquistaram 18 campeonatos NBA - o MAIOR número da história! 11 com Bill Russell nos 60s, 3 com Larry Bird nos 80s, e continuam ganhando. É a potência máxima da NBA!",
        "sugestao": "Quer conhecer o estádio do Celtics?"
    },
    "celtics_estadio": {
        "resposta": "Os Celtics jogam no TD Garden em Boston, uma arena CLÁSSICA e barulhenta! Os torcedores lá são fanáticos, e a energia é impossível de descrever. É um dos melhores lugares pra jogar basquete!",
        "sugestao": "Quer saber em qual conferência o Celtics joga?"
    },
    "celtics_conferenciaatualmente": {
        "resposta": "O Celtics está na Conferência Leste e é praticamente a FORÇA DOMINANTE dela! Com Tatum, Brown e cia, eles estão sempre como favoritos para o campeonato!",
        "sugestao": "Quer conhecer o técnico do Celtics?"
    },
    "celtics_tecnico": {
        "resposta": "O técnico atual do Celtics trabalha para manter o padrão de excelência da franquia. A organização celtics é conhecida por sempre ter técnicos de elite gerenciando times incríveis!",
        "sugestao": "Quer saber sobre a rivalidade do Celtics?"
    },
    "celtics_rivalidade": {
        "resposta": "Os Celtics têm rivalidade épica com os Lakers! Essa é a maior rivalidade da NBA, com encontros memoráveis nas finais. Celtics vs Lakers = basquete no seu melhor!",
        "sugestao": "Quer saber como está o Celtics nos dias de hoje?"
    },
    "celtics_presente": {
        "resposta": "Agora, o Celtics está em seu auge com Jayson Tatum e Jaylen Brown como líderes! Eles estão montando um supertime, sempre lutando pelos títulos e mantendo a legenda viva!",
        "sugestao": "Quer conhecer o futuro do Celtics?"
    },
    "celtics_futuro": {
        "resposta": "O futuro do Celtics é muito promissor! Com Tatum, Brown e continuando a investir em talento, eles estão na jornada para conquistar ainda mais títulos e adicionar à sua lenda!",
        "sugestao": "Quer explorar o Los Angeles Lakers também?"
    },
}

# Perguntas-chave mapeadas (para facilitar a busca)
PALAVRAS_CHAVE_LAKERS = {
    "lakers", "angeles", "magic", "kobe", "shaq", "lebron", "staples", "crypto", 
    "showtime", "black mamba", "diesel", "oeste", "papai"
}

PALAVRAS_CHAVE_CELTICS = {
    "celtics", "boston", "bill russell", "larry bird", "jayson", "tatum", "jaylen", "brown",
    "td garden", "leste", "truth", "pierce", "havlicek"
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

def eh_resposta_afirmativa(texto):
    """Detecta se o usuário respondeu 'sim' ou 'quero'"""
    texto_lower = texto.lower().strip()
    respostas_afirmativas = {
        "sim", "ss", "claro", "quer", "quero", "quero sim", "quer sim",
        "claro que sim", "com certeza", "boa", "beleza", "blz", "vamo",
        "vamos", "tá", "ta bom", "ok", "okh", "okk", "opa", "yes", "yah"
    }
    return texto_lower in respostas_afirmativas or any(pal in texto_lower for pal in respostas_afirmativas)

def obter_proxima_pergunta(time, indice_atual):
    """Obtém a próxima pergunta da sequência"""
    if time not in PROGRESSO_CONVERSA:
        return None
    
    sequencia = PROGRESSO_CONVERSA[time]
    if indice_atual + 1 < len(sequencia):
        return sequencia[indice_atual + 1]
    else:
        return None

def processar_resposta_com_sugestao(chave_conversa):
    """Processa a resposta e retorna com a sugestão de próxima pergunta"""
    if chave_conversa in BANCO_CONVERSAS:
        resposta_obj = BANCO_CONVERSAS[chave_conversa]
        
        if isinstance(resposta_obj, dict):
            resposta = resposta_obj.get("resposta", "")
            sugestao = resposta_obj.get("sugestao", "")
            if sugestao:
                resposta += f"\n\n👉 {sugestao}"
            return resposta
        else:
            return resposta_obj
    return None

def detectar_time(mensagem):
    """Detecta qual time o usuário mencionou e guarda na memória"""
    mensagem_lower = mensagem.lower()
    
    if any(palavra in mensagem_lower for palavra in PALAVRAS_CHAVE_LAKERS):
        return "lakers"
    elif any(palavra in mensagem_lower for palavra in PALAVRAS_CHAVE_CELTICS):
        return "celtics"
    return None

def gerar_chave_conversa(mensagem, time_memorizado):
    """Gera a chave para buscar a resposta no banco de conversas"""
    mensagem_lower = mensagem.lower()
    palavras = processar_texto(mensagem)
    
    # Palavras-chave para tipos de pergunta
    tipos_pergunta = {
        "historia": ["historia", "origem", "fundação", "foi", "criação", "começou"],
        "jogadores": ["jogadores", "astros", "lendas", "nomes", "quem", "ícones", "estrelas"],
        "titulos": ["titulos", "campeonatos", "ganhou", "venceu", "quantos", "rings"],
        "estadio": ["estadio", "arena", "casa", "onde", "joga", "local"],
        "conferencia": ["conferencia", "leste", "oeste", "divisao", "qual"],
        "tecnico": ["tecnico", "treinador", "coach"],
        "rivalidade": ["rivalidade", "rival", "inimigo", "enfrenta"],
        "presente": ["agora", "atualmente", "hoje", "como está"],
        "futuro": ["futuro", "vai", "próximo", "vai ser"],
    }
    
    # Identifica o tipo de pergunta
    tipo_identificado = "historia"  # padrão
    for tipo, palavras_tipo in tipos_pergunta.items():
        if any(p in palavras for p in palavras_tipo):
            tipo_identificado = tipo
            break
    
    # Se tem time memorizado, usa ele
    if time_memorizado:
        chave = f"{time_memorizado}_{tipo_identificado}"
        if chave in BANCO_CONVERSAS:
            return chave
    
    # Procura por palavra-chave genérica
    for palavra in palavras:
        if palavra in BANCO_CONVERSAS:
            return palavra
    
    return None

def obter_respostas(mensagem, session_id):
    """Busca resposta no banco de conversas com memória de time e guia de conversa"""
    
    # Verifica saudações primeiro
    mensagem_lower = mensagem.lower()
    for saudacao, resposta in SAUDACOES.items():
        if saudacao in mensagem_lower:
            return resposta
    
    # Pega o time memorizado do usuário
    time_memorizado = user_memory.get(session_id)
    indice_pergunta = user_memory.get(f"{session_id}_indice", -1)
    
    # Detecta time escolhido
    time_detectado = detectar_time(mensagem)
    if time_detectado:
        user_memory[session_id] = time_detectado
        time_memorizado = time_detectado
        indice_pergunta = -1  # Reseta o índice quando escolhe um novo time
        user_memory[f"{session_id}_indice"] = -1
    
    # Verifica se é uma resposta afirmativa (sim/quero) e tem time memorizado
    if eh_resposta_afirmativa(mensagem) and time_memorizado:
        # Avança para próxima pergunta da sequência
        proxima_chave = obter_proxima_pergunta(time_memorizado, indice_pergunta)
        
        if proxima_chave:
            indice_pergunta += 1
            user_memory[f"{session_id}_indice"] = indice_pergunta
            resposta = processar_resposta_com_sugestao(proxima_chave)
            return resposta
        else:
            # Se acabou a sequência de perguntas do time
            outro_time = "Celtics" if time_memorizado == "lakers" else "Lakers"
            return f"Massa! Terminamos a jornada pelo {time_memorizado.upper()}! 🏀\n\nAgora quer explorar o {outro_time}?"
    
    # Gera a chave para buscar resposta
    chave_conversa = gerar_chave_conversa(mensagem, time_memorizado)
    
    if chave_conversa and chave_conversa in BANCO_CONVERSAS:
        # Atualiza o índice se encontrou uma resposta do banco
        if time_memorizado and chave_conversa.startswith(time_memorizado):
            sequencia = PROGRESSO_CONVERSA.get(time_memorizado, [])
            if chave_conversa in sequencia:
                indice_pergunta = sequencia.index(chave_conversa)
                user_memory[f"{session_id}_indice"] = indice_pergunta
        
        resposta_obj = BANCO_CONVERSAS[chave_conversa]
        
        # Verifica se é um dict (com resposta + sugestão) ou string
        if isinstance(resposta_obj, dict):
            resposta = resposta_obj.get("resposta", "")
            sugestao = resposta_obj.get("sugestao", "")
            if sugestao:
                resposta += f"\n\n👉 {sugestao}"
            return resposta
        else:
            return resposta_obj
    
    # Se não encontrou nada específico, tenta ser genérico
    if time_memorizado:
        return f"Ótima pergunta sobre o {time_memorizado.upper()}! Me manda uma pergunta mais específica tipo: história, jogadores, títulos, estádio ou rivalidades!"
    else:
        return "Hmmm, não entendi bem essa. Tenta escolher um time: Lakers ou Celtics? Depois pergunta sobre história, jogadores, títulos, estádio e mais!"


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.form.get("msg")
    
    session_id = request.form.get("session_id", "default")
    
    if not user_message:
        return jsonify({"response": "Manda uma mensagem válida!"})

    if contem_palavrao(user_message):
        return jsonify({
            "response": "Opa campeão, vamos evitar o xingamento, todo mundo aqui é amigo!"
        })
        
    bot_response = obter_respostas(user_message, session_id)
    return jsonify({"response": bot_response})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
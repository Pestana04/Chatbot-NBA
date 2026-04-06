from flask import Flask, render_template, request, jsonify
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string
from dados import PROGRESSO_CONVERSA, SAUDACOES, BANCO_CONVERSAS, PALAVRAS_CHAVE_LAKERS, PALAVRAS_CHAVE_CELTICS, PALAVROES_BLOQUEADOS

app = Flask(__name__)


user_memory = {}


try:
    nltk.data.find('tokenizers/punkt_tab')
except Exception:
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
    
try:
    nltk.data.find('corpora/stopwords')
except Exception:
    nltk.download('stopwords', quiet=True)


def processar_texto(texto):

    tokens = word_tokenize(texto.lower(), language='portuguese')

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
    

    tipo_identificado = "historia"  # padrão
    for tipo, palavras_tipo in tipos_pergunta.items():
        if any(p in palavras for p in palavras_tipo):
            tipo_identificado = tipo
            break
    

    if time_memorizado:
        chave = f"{time_memorizado}_{tipo_identificado}"
        if chave in BANCO_CONVERSAS:
            return chave
    

    for palavra in palavras:
        if palavra in BANCO_CONVERSAS:
            return palavra
    
    return None

def obter_respostas(mensagem, session_id):
    """Busca resposta no banco de conversas com memória de time e guia de conversa"""
    

    mensagem_lower = mensagem.lower()
    for saudacao, resposta in SAUDACOES.items():
        if saudacao in mensagem_lower:
            return resposta
    

    time_memorizado = user_memory.get(session_id)
    indice_pergunta = user_memory.get(f"{session_id}_indice", -1)
    

    time_detectado = detectar_time(mensagem)
    if time_detectado:
        user_memory[session_id] = time_detectado
        time_memorizado = time_detectado
        indice_pergunta = -1  # Reseta o índice quando escolhe um novo time
        user_memory[f"{session_id}_indice"] = -1
    

    if eh_resposta_afirmativa(mensagem) and time_memorizado:

        proxima_chave = obter_proxima_pergunta(time_memorizado, indice_pergunta)
        
        if proxima_chave:
            indice_pergunta += 1
            user_memory[f"{session_id}_indice"] = indice_pergunta
            resposta = processar_resposta_com_sugestao(proxima_chave)
            return resposta
        else:
            outro_time = "celtics" if time_memorizado == "lakers" else "lakers"
            user_memory[session_id] = outro_time
            user_memory[f"{session_id}_indice"] = 0
            
            primeira_chave = PROGRESSO_CONVERSA[outro_time][0]
            resposta_outro_time = processar_resposta_com_sugestao(primeira_chave)
            
            return f"Massa! Terminamos a jornada pelo {time_memorizado.upper()}! 🏀\n\nAgora vamos de {outro_time.capitalize()}!\n\n{resposta_outro_time}"
    

    chave_conversa = gerar_chave_conversa(mensagem, time_memorizado)
    
    if chave_conversa and chave_conversa in BANCO_CONVERSAS:

        if time_memorizado and chave_conversa.startswith(time_memorizado):
            sequencia = PROGRESSO_CONVERSA.get(time_memorizado, [])
            if chave_conversa in sequencia:
                indice_pergunta = sequencia.index(chave_conversa)
                user_memory[f"{session_id}_indice"] = indice_pergunta
        
        resposta_obj = BANCO_CONVERSAS[chave_conversa]
        

        if isinstance(resposta_obj, dict):
            resposta = resposta_obj.get("resposta", "")
            sugestao = resposta_obj.get("sugestao", "")
            if sugestao:
                resposta += f"\n\n👉 {sugestao}"
            return resposta
        else:
            return resposta_obj
    

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
from flask import Flask, render_template, request, jsonify
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string
import json
import os

from tradutor_local import (
    traduzir_para_portugues,
    traduzir_do_portugues,
    identificar_idioma,
    detectar_codigo_idioma,
    instalar_idiomas
)

app = Flask(__name__)

user_memory = {}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE_DIR, "dados.json"), "r", encoding="utf-8") as f:
    _dados = json.load(f)

PROGRESSO_CONVERSA = _dados["PROGRESSO_CONVERSA"]
SAUDACOES = _dados["SAUDACOES"]
BANCO_CONVERSAS = _dados["BANCO_CONVERSAS"]
PALAVRAS_CHAVE_LAKERS = set(_dados["PALAVRAS_CHAVE_LAKERS"])
PALAVRAS_CHAVE_CELTICS = set(_dados["PALAVRAS_CHAVE_CELTICS"])
PALAVROES_BLOQUEADOS = set(_dados["PALAVROES_BLOQUEADOS"])


try:
    nltk.data.find("tokenizers/punkt_tab")
except Exception:
    nltk.download("punkt", quiet=True)
    nltk.download("punkt_tab", quiet=True)

try:
    nltk.data.find("corpora/stopwords")
except Exception:
    nltk.download("stopwords", quiet=True)


def processar_texto(texto):
    tokens = word_tokenize(texto.lower(), language="portuguese")
    stop_words = set(stopwords.words("portuguese"))

    palavras_limpas = [
        p for p in tokens
        if p not in stop_words and p not in string.punctuation
    ]

    return palavras_limpas


def contem_palavrao(texto):
    palavras = word_tokenize(texto.lower(), language="portuguese")

    for palavra in palavras:
        palavra = palavra.strip(string.punctuation)

        if palavra in PALAVROES_BLOQUEADOS:
            return True

    return False


def eh_resposta_afirmativa(texto):
    texto_lower = texto.lower().strip()

    respostas_afirmativas = {
        "sim", "ss", "claro", "quer", "quero", "quero sim", "quer sim",
        "claro que sim", "com certeza", "boa", "beleza", "blz", "vamo",
        "vamos", "tá", "ta bom", "ok", "okh", "okk", "opa", "yes", "yah"
    }

    return texto_lower in respostas_afirmativas or any(
        pal in texto_lower for pal in respostas_afirmativas
    )


def eh_resposta_negativa(texto):
    texto_lower = texto.lower().strip()
    respostas_negativas = {"não", "nao", "n", "nunca", "nope"}

    if texto_lower in respostas_negativas:
        return True

    if "não quero" in texto_lower or "nao quero" in texto_lower:
        return True

    for n in respostas_negativas:
        if texto_lower.startswith(n + " ") or texto_lower.startswith(n + ","):
            return True

    return False


def obter_proxima_pergunta(time, indice_atual):
    if time not in PROGRESSO_CONVERSA:
        return None

    sequencia = PROGRESSO_CONVERSA[time]

    if indice_atual + 1 < len(sequencia):
        return sequencia[indice_atual + 1]

    return None


def processar_resposta_com_sugestao(chave_conversa):
    if chave_conversa in BANCO_CONVERSAS:
        resposta_obj = BANCO_CONVERSAS[chave_conversa]

        if isinstance(resposta_obj, dict):
            resposta = resposta_obj.get("resposta", "")
            sugestao = resposta_obj.get("sugestao", "")

            if sugestao:
                resposta += f"\n\n👉 {sugestao}"

            return resposta

        return resposta_obj

    return None


def detectar_time(mensagem):
    mensagem_lower = mensagem.lower()

    if any(palavra in mensagem_lower for palavra in PALAVRAS_CHAVE_LAKERS):
        return "lakers"

    if any(palavra in mensagem_lower for palavra in PALAVRAS_CHAVE_CELTICS):
        return "celtics"

    return None


def gerar_chave_conversa(mensagem, time_memorizado):
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

    tipo_identificado = "historia"

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
    mensagem_lower = mensagem.lower()

    for saudacao, resposta in SAUDACOES.items():
        if saudacao in mensagem_lower:
            return resposta, "base"

    time_memorizado = user_memory.get(session_id)
    indice_pergunta = user_memory.get(f"{session_id}_indice", -1)

    time_detectado = detectar_time(mensagem)

    if time_detectado:
        user_memory[session_id] = time_detectado
        time_memorizado = time_detectado
        indice_pergunta = -1
        user_memory[f"{session_id}_indice"] = -1

    if eh_resposta_negativa(mensagem):
        if time_memorizado:
            return (
                f"Tranquilo, não falo mais disso! Quer mudar de assunto ou perguntar outra coisa sobre o {time_memorizado.capitalize()}?",
                "base"
            )

        return (
            "Beleza, sem problemas! Se quiser saber sobre algum time da NBA mais tarde, é só mandar mensagem.",
            "base"
        )

    if eh_resposta_afirmativa(mensagem) and time_memorizado:
        proxima_chave = obter_proxima_pergunta(time_memorizado, indice_pergunta)

        if proxima_chave:
            indice_pergunta += 1
            user_memory[f"{session_id}_indice"] = indice_pergunta
            return processar_resposta_com_sugestao(proxima_chave), "base"

        outro_time = "celtics" if time_memorizado == "lakers" else "lakers"
        user_memory[session_id] = outro_time
        user_memory[f"{session_id}_indice"] = 0

        primeira_chave = PROGRESSO_CONVERSA[outro_time][0]
        resposta_outro_time = processar_resposta_com_sugestao(primeira_chave)

        return (
            f"Massa! Terminamos a jornada pelo {time_memorizado.upper()}! 🏀\n\n"
            f"Agora vamos de {outro_time.capitalize()}!\n\n"
            f"{resposta_outro_time}",
            "base"
        )

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

            return resposta, "base"

        return resposta_obj, "base"

    if time_memorizado:
        return (
            f"Ótima pergunta sobre o {time_memorizado.upper()}! Me manda uma pergunta mais específica tipo: "
            f"história, jogadores, títulos, estádio ou rivalidades!",
            "padrao"
        )

    return (
        "Hmmm, não entendi bem essa. Tenta escolher um time: Lakers ou Celtics? "
        "Depois pergunta sobre história, jogadores, títulos, estádio e mais!",
        "padrao"
    )


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    print("CHAT CHAMADO")

    user_message = request.form.get("msg")
    session_id = request.form.get("session_id", "default")

    if not user_message:
        return jsonify({
            "response": "Manda uma mensagem válida!",
            "idioma": "Português",
            "fonte": "base"
        })

    codigo_idioma = detectar_codigo_idioma(user_message)
    idioma_detectado = identificar_idioma(user_message)

    print("=" * 50)
    print("IDIOMA:", idioma_detectado)
    print("CÓDIGO:", codigo_idioma)
    print("ORIGINAL:", user_message)

    mensagem_em_portugues = traduzir_para_portugues(user_message)

    print("TRADUZIDA PARA PT:", mensagem_em_portugues)

    if contem_palavrao(mensagem_em_portugues):
        bot_response = "Opa campeão, vamos evitar o xingamento, todo mundo aqui é amigo!"
        fonte = "base"
    else:
        bot_response, fonte = obter_respostas(mensagem_em_portugues, session_id)

    resposta_final = traduzir_do_portugues(bot_response, codigo_idioma)

    print("RESPOSTA PT:", bot_response)
    print("RESPOSTA FINAL:", resposta_final)
    print("=" * 50)

    return jsonify({
        "response": resposta_final,
        "idioma": idioma_detectado,
        "fonte": fonte
    })


if __name__ == "__main__":
    instalar_idiomas()
    app.run(debug=True, port=5000)
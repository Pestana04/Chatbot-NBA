from flask import Flask, render_template, request, jsonify
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string
import json
import os
import re

from tradutor_local import (
    traduzir_para_portugues,
    traduzir_do_portugues,
    identificar_idioma,
    detectar_codigo_idioma,
    instalar_idiomas
)
from llm_local import gerar_resposta_llm

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


try:
    _STOPWORDS_PT = set(stopwords.words("portuguese"))
except Exception:
    _STOPWORDS_PT = set()


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


def _tokens_simples(texto):
    """Quebra o texto em palavras já sem pontuação, em minúsculas."""
    tokens = [t.strip(string.punctuation) for t in texto.lower().split()]
    return [t for t in tokens if t]


def eh_saudacao(mensagem, saudacao):
    """Casa a saudação como palavra inteira (evita 'oi' dentro de 'foi')."""
    padrao = r"\b" + re.escape(saudacao) + r"\b"
    return re.search(padrao, mensagem.lower()) is not None


PALAVRAS_AFIRMATIVAS = {
    "sim", "ss", "claro", "quer", "quero", "queria", "gostaria", "gostei",
    "boa", "beleza", "blz", "vamo", "vamos", "tá", "ta", "ok", "okay", "okh",
    "okk", "opa", "yes", "yah", "bora", "isso", "exato", "positivo", "aham",
    "uhum", "pode", "manda", "mande", "continua", "continue", "segue",
    "prossegue", "certeza"
}

PALAVRAS_ACOMPANHAMENTO = {
    "com", "por", "favor", "muito", "demais", "mais", "ai", "aí", "sim",
    "próxima", "proxima", "pergunta", "tudo", "bem", "ser", "mandar", "saber",
    "falar", "fala", "contar", "conta", "sobre", "me", "te", "agora", "já",
    "bom"
}

# Tópicos que existem no banco de conversas
TOPICOS_BANCO = {
    "historia", "história", "jogadores", "jogador", "titulos", "títulos",
    "estadio", "estádio", "arena", "conferencia", "conferência", "tecnico",
    "técnico", "rivalidade", "rival", "presente", "futuro"
}


def eh_resposta_afirmativa(texto):
    tokens = _tokens_simples(texto)

    if not tokens:
        return False

    # Precisa ter ao menos uma palavra de confirmação ("sim", "quero"...).
    if not any(t in PALAVRAS_AFIRMATIVAS for t in tokens):
        return False

    # É confirmação só se o resto for "enchimento" (acompanhamento/stopwords).
    # Se sobrar uma palavra de conteúdo (ex.: "warriors"), é um pedido novo.
    ignoraveis = PALAVRAS_AFIRMATIVAS | PALAVRAS_ACOMPANHAMENTO | _STOPWORDS_PT
    restante = [t for t in tokens if t not in ignoraveis]

    return not restante


def eh_resposta_negativa(texto):
    texto_lower = texto.lower().strip()

    respostas_negativas = {"não", "nao", "n", "nunca", "nope", "negativo"}
    frases_negativas = {
        "não quero", "nao quero", "não obrigado", "nao obrigado",
        "não, obrigado", "nao, obrigado"
    }

    if texto_lower in respostas_negativas or texto_lower in frases_negativas:
        return True

    tokens = _tokens_simples(texto_lower)
    return bool(tokens) and all(t in respostas_negativas for t in tokens)


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


NOMES_DE_TIME = {
    "lakers": ["lakers", "los angeles", "angeles"],
    "celtics": ["celtics", "boston"],
}


def time_citado_pelo_nome(mensagem):
    mensagem_lower = mensagem.lower()

    for time, nomes in NOMES_DE_TIME.items():
        if any(nome in mensagem_lower for nome in nomes):
            return time

    return None


def gerar_chave_conversa(mensagem, time_memorizado):
    palavras = processar_texto(mensagem)

    tipos_pergunta = {
        "historia": ["historia", "história", "origem", "fundação", "fundacao", "fundado", "fundada", "fundados", "criação", "criacao", "criado", "começou", "comecou", "ano", "anos", "surgiu", "nasceu"],
        "jogadores": ["jogadores", "jogador", "astros", "astro", "lendas", "lenda", "nomes", "quem", "ícones", "icones", "estrelas", "estrela", "craque", "craques", "destaque"],
        "titulos": ["titulos", "títulos", "campeonatos", "ganhou", "venceu", "quantos", "rings", "anéis", "aneis"],
        "estadio": ["estadio", "estádio", "arena", "casa", "onde", "local", "ginásio", "ginasio"],
        "conferenciaatualmente": ["conferencia", "conferência", "leste", "oeste", "divisao", "divisão"],
        "tecnico": ["tecnico", "técnico", "treinador", "coach"],
        "rivalidade": ["rivalidade", "rival", "inimigo", "enfrenta"],
        "presente": ["agora", "atualmente", "hoje"],
        "futuro": ["futuro", "próximo", "proximo"],
    }

    tipo_identificado = None

    for tipo, palavras_tipo in tipos_pergunta.items():
        if any(p in palavras for p in palavras_tipo):
            tipo_identificado = tipo
            break

    if time_memorizado and tipo_identificado:
        chave = f"{time_memorizado}_{tipo_identificado}"

        if chave in BANCO_CONVERSAS:
            return chave

    for palavra in palavras:
        if palavra in BANCO_CONVERSAS:
            return palavra

    return None


def responder_com_fallback(mensagem, mensagem_padrao, historico=None):
    resposta_llm = gerar_resposta_llm(mensagem, historico)

    if resposta_llm:
        return resposta_llm, "llm"

    return mensagem_padrao, "padrao"


def identificar_contexto(mensagem, time_memorizado):
    
    tokens = _tokens_simples(mensagem)

    # Afirmativa pura (ex.: "quero", "sim", "bora") → segue o banco
    tem_afirmativa = any(t in PALAVRAS_AFIRMATIVAS for t in tokens)
    ignoraveis = PALAVRAS_AFIRMATIVAS | PALAVRAS_ACOMPANHAMENTO | _STOPWORDS_PT
    restante = [t for t in tokens if t not in ignoraveis]

    if tem_afirmativa and not restante:
        return "base"

    # Tem tópico explícito do banco (ex.: "história", "títulos") → banco
    if any(t in TOPICOS_BANCO for t in tokens):
        return "base"

    # Citou o nome de um time diretamente → banco
    if time_citado_pelo_nome(mensagem):
        return "base"

    # Palavra-chave dos times conhecidos → banco
    todas_keywords = PALAVRAS_CHAVE_LAKERS | PALAVRAS_CHAVE_CELTICS
    if any(t in todas_keywords for t in tokens):
        return "base"

    # Nenhum sinal de que o banco cobre → LLM
    return "llm"


def obter_respostas(mensagem, session_id):
    for saudacao, resposta in SAUDACOES.items():
        if eh_saudacao(mensagem, saudacao):
            return resposta, "base"

    time_memorizado = user_memory.get(session_id)
    indice_pergunta = user_memory.get(f"{session_id}_indice", -1)

    time_detectado = detectar_time(mensagem)

    if time_detectado:
        if time_detectado != time_memorizado:
            indice_pergunta = -1
            user_memory[f"{session_id}_indice"] = -1

        user_memory[session_id] = time_detectado
        time_memorizado = time_detectado

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

    historico = user_memory.get(f"{session_id}_hist", [])

    # Stickiness: se a última resposta veio da LLM e esta é um follow-up
    # com pronome sem citar um time pelo nome, mantemos o assunto na LLM.
    pronomes = {"ele", "ela", "dele", "dela", "nele", "nela", "seu", "sua", "seus", "suas"}
    tem_pronome = any(t in pronomes for t in _tokens_simples(mensagem))
    ultima_fonte = user_memory.get(f"{session_id}_ultima_fonte")

    if tem_pronome and ultima_fonte == "llm" and not time_citado_pelo_nome(mensagem):
        resposta_llm = gerar_resposta_llm(mensagem, historico)

        if resposta_llm:
            return resposta_llm, "llm"

    # Identificador de contexto: decide se tenta o banco ou vai direto pra LLM
    contexto = identificar_contexto(mensagem, time_memorizado)

    if contexto == "base":
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

        # Citou nome de time mas sem tópico → inicia jornada pela história
        time_citado = time_citado_pelo_nome(mensagem)

        if time_citado:
            chave_inicial = f"{time_citado}_historia"

            if chave_inicial in BANCO_CONVERSAS:
                user_memory[f"{session_id}_indice"] = 0
                return processar_resposta_com_sugestao(chave_inicial), "base"

    # contexto == "llm" ou banco não encontrou resposta → fallback LLM
    if time_memorizado:
        mensagem_padrao = (
            f"Ótima pergunta sobre o {time_memorizado.upper()}! Me manda uma pergunta mais específica tipo: "
            f"história, jogadores, títulos, estádio ou rivalidades!"
        )
    else:
        mensagem_padrao = (
            "Hmmm, não entendi bem essa. Tenta escolher um time: Lakers ou Celtics? "
            "Depois pergunta sobre história, jogadores, títulos, estádio e mais!"
        )

    return responder_com_fallback(mensagem, mensagem_padrao, historico)


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

    historico = user_memory.get(f"{session_id}_hist", [])
    historico.append({"role": "user", "content": mensagem_em_portugues})
    historico.append({"role": "assistant", "content": bot_response})
    user_memory[f"{session_id}_hist"] = historico[-6:]
    user_memory[f"{session_id}_ultima_fonte"] = fonte

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

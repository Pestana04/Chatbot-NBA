import re
import argostranslate.package
import argostranslate.translate
from langdetect import detect_langs, DetectorFactory

# deixa a detecção de idioma sempre igual (langdetect é aleatório por padrão)
DetectorFactory.seed = 0

# idiomas que o bot traduz
IDIOMAS_SUPORTADOS = {"en", "es", "it", "fr", "de", "pt"}

# palavras bem típicas do português, pra acertar mesmo em frases curtas
MARCADORES_PT = {
    "você", "voce", "vc", "quero", "quer", "queria", "fala", "fale", "falar",
    "quem", "qual", "quais", "quando", "quanto", "quantos", "onde", "não", "nao",
    "obrigado", "jogador", "jogadores", "também", "tambem", "conta", "conte"
}


PARES_TRADUCAO = [
    ("en", "pt"),
    ("pt", "en"),
    ("es", "pt"),
    ("pt", "es"),
    ("it", "pt"),
    ("pt", "it"),
    ("fr", "pt"),
    ("pt", "fr"),
    ("de", "pt"),
    ("pt", "de"),
]


# baixa e instala um par de tradução (ex.: en -> pt)
def instalar_pacote(origem, destino):
    try:
        pacotes_disponiveis = argostranslate.package.get_available_packages()

        pacote = next(
            (
                p for p in pacotes_disponiveis
                if p.from_code == origem and p.to_code == destino
            ),
            None
        )

        if pacote:
            caminho = pacote.download()
            argostranslate.package.install_from_path(caminho)

    except Exception as erro:
        print(f"Erro ao instalar {origem}->{destino}: {erro}")


# instala todos os pares de idiomas usados pelo bot
def instalar_idiomas():
    print("Verificando modelos de tradução...")

    for origem, destino in PARES_TRADUCAO:
        instalar_pacote(origem, destino)

    print("Modelos de tradução verificados.")


# descobre o código do idioma do texto (en, es, pt...)
def detectar_codigo_idioma(texto):
    texto_lower = texto.lower().strip()

    palavras_curtas = {
        "hello": "en",
        "hi": "en",
        "hey": "en",
        "bye": "en",

        "hola": "es",
        "adios": "es",
        "adiós": "es",

        "ciao": "it",
        "buongiorno": "it",

        "bonjour": "fr",
        "salut": "fr",

        "hallo": "de",
        "guten tag": "de"
    }

    if texto_lower in palavras_curtas:
        return palavras_curtas[texto_lower]

    # acento ou palavra marcante = português
    palavras = re.findall(r"[a-zà-ÿ]+", texto_lower)

    if re.search(r"[ãõçáàâéêíóôúü]", texto_lower) or (set(palavras) & MARCADORES_PT):
        return "pt"

    # frase muito curta confunde o langdetect, então assume português
    if len(palavras) <= 2:
        return "pt"

    # só confia no langdetect com confiança alta; senão, português
    try:
        candidatos = detect_langs(texto)

        if candidatos:
            melhor = candidatos[0]

            if melhor.lang in IDIOMAS_SUPORTADOS and melhor.prob >= 0.85:
                return melhor.lang
    except Exception:
        pass

    return "pt"


# traduz o código do idioma pro nome em português (en -> "Inglês")
def identificar_idioma(texto):
    codigo = detectar_codigo_idioma(texto)

    idiomas = {
        "pt": "Português",
        "en": "Inglês",
        "es": "Espanhol",
        "it": "Italiano",
        "fr": "Francês",
        "de": "Alemão"
    }

    return idiomas.get(codigo, codigo)


# troca gírias do bot por português normal antes de traduzir
def corrigir_girias_antes_de_traduzir(texto):
    substituicoes = {
        "Faaala!": "Olá!",
        "Faaala": "Olá",
        "Massa!": "Legal!",
        "Massa": "Legal",
        "Beleza": "Tudo bem",
        "Opa campeão": "Olá",
        "Tranquilo": "Sem problemas",
        "Bora": "Vamos",
        "maneiro": "legal",
        "SHOW": "muito legal",
        "LENDÁRIA": "lendária",
        "GIGANTES": "grandes nomes",
        "MAIORES": "maiores",
    }

    for original, corrigido in substituicoes.items():
        texto = texto.replace(original, corrigido)

    return texto


# ajusta pequenos erros da tradução automática por idioma
def corrigir_resposta_traduzida(texto, codigo_destino):
    if codigo_destino == "en":
        substituicoes = {
            "Hello! How nice you are here.": "Hey! Nice to see you here.",
            "Which team do you want to explore": "Which team do you want to explore",
            "Mass": "Cool",
            "Legal": "Cool",
            "No problem": "No problem",
            "Do you want": "Do you want",
            "Lakers or Celtics": "Lakers or Celtics",
        }

    elif codigo_destino == "es":
        substituicoes = {
            "Hola!": "¡Hola!",
            "Legal": "¡Genial!",
            "Sin problemas": "Sin problema",
        }

    elif codigo_destino == "it":
        substituicoes = {
            "Ciao!": "Ciao!",
        }

    elif codigo_destino == "fr":
        substituicoes = {
            "Bonjour!": "Bonjour !",
        }

    elif codigo_destino == "de":
        substituicoes = {
            "Hallo!": "Hallo!",
        }

    else:
        return texto

    for original, corrigido in substituicoes.items():
        texto = texto.replace(original, corrigido)

    return texto


# traduz um texto de um idioma para outro (motor Argos Translate)
def traduzir(texto, origem, destino):
    try:
        if origem == destino:
            return texto

        idiomas_instalados = argostranslate.translate.get_installed_languages()

        idioma_origem = next(
            (i for i in idiomas_instalados if i.code == origem),
            None
        )

        idioma_destino = next(
            (i for i in idiomas_instalados if i.code == destino),
            None
        )

        if idioma_origem and idioma_destino:
            traducao = idioma_origem.get_translation(idioma_destino)
            return traducao.translate(texto)

        return texto

    except Exception as erro:
        print("Erro na tradução:", erro)
        return texto


# traduz a mensagem do usuário para português (entrada do bot)
def traduzir_para_portugues(texto):
    codigo = detectar_codigo_idioma(texto)
    return traduzir(texto, codigo, "pt")


# traduz a resposta do bot de volta para o idioma do usuário (saída)
def traduzir_do_portugues(texto, codigo_destino):
    if codigo_destino == "pt":
        return texto

    texto_corrigido = corrigir_girias_antes_de_traduzir(texto)
    texto_traduzido = traduzir(texto_corrigido, "pt", codigo_destino)
    texto_traduzido = corrigir_resposta_traduzida(texto_traduzido, codigo_destino)

    return texto_traduzido

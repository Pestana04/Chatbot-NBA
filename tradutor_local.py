import argostranslate.package
import argostranslate.translate

from langdetect import detect


IDIOMAS_SUPORTADOS = ["en", "es", "it", "fr", "de"]


def instalar_pacote(origem, destino="pt"):
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

    except Exception as e:
        print(f"Erro ao instalar {origem}->{destino}: {e}")


def instalar_idiomas():
    print("Instalando modelos de tradução...")

    for idioma in IDIOMAS_SUPORTADOS:
        instalar_pacote(idioma)

    print("Modelos carregados.")


def detectar_codigo_idioma(texto):
    texto_lower = texto.lower().strip()

    # Correção para palavras curtas que o langdetect erra frequentemente
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

    try:
        return detect(texto)

    except Exception:
        return "pt"


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


def traduzir_para_portugues(texto):
    try:
        codigo = detectar_codigo_idioma(texto)

        print(f"Idioma detectado: {codigo}")

        if codigo == "pt":
            return texto

        idiomas_instalados = argostranslate.translate.get_installed_languages()

        idioma_origem = next(
            (i for i in idiomas_instalados if i.code == codigo),
            None
        )

        idioma_pt = next(
            (i for i in idiomas_instalados if i.code == "pt"),
            None
        )

        if idioma_origem and idioma_pt:
            traducao = idioma_origem.get_translation(idioma_pt)

            texto_traduzido = traducao.translate(texto)

            print(f"Traduzido: {texto_traduzido}")

            return texto_traduzido

        return texto

    except Exception as erro:
        print("Erro tradução:", erro)
        return texto
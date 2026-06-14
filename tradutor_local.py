import argostranslate.package
import argostranslate.translate
from langdetect import detect


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


def instalar_idiomas():
    print("Verificando modelos de tradução...")

    for origem, destino in PARES_TRADUCAO:
        instalar_pacote(origem, destino)

    print("Modelos de tradução verificados.")


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


def traduzir_para_portugues(texto):
    codigo = detectar_codigo_idioma(texto)
    return traduzir(texto, codigo, "pt")


def traduzir_do_portugues(texto, codigo_destino):
    return traduzir(texto, "pt", codigo_destino)
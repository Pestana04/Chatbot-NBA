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


def identificar_idioma(texto):
    try:
        codigo = detect(texto)

        idiomas = {
            "pt": "Português",
            "en": "Inglês",
            "es": "Espanhol",
            "it": "Italiano",
            "fr": "Francês",
            "de": "Alemão"
        }

        return idiomas.get(codigo, codigo)

    except:
        return "Desconhecido"


def traduzir_para_portugues(texto):
    try:

        codigo = detect(texto)

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
            return traducao.translate(texto)

        return texto

    except Exception as erro:
        print("Erro tradução:", erro)
        return texto
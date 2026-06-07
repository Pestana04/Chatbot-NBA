import argostranslate.package
import argostranslate.translate

IDIOMAS_SUPORTADOS = ["en", "es", "fr", "it", "de"]


def instalar_pacote(origem, destino="pt"):
    pacotes_disponiveis = argostranslate.package.get_available_packages()

    pacote = next(
        (p for p in pacotes_disponiveis if p.from_code == origem and p.to_code == destino),
        None
    )

    if pacote:
        caminho = pacote.download()
        argostranslate.package.install_from_path(caminho)


def instalar_idiomas():
    for idioma in IDIOMAS_SUPORTADOS:
        instalar_pacote(idioma, "pt")


def traduzir_para_portugues(texto):
    try:
        idiomas_instalados = argostranslate.translate.get_installed_languages()

        idioma_pt = next((i for i in idiomas_instalados if i.code == "pt"), None)

        for idioma_origem in idiomas_instalados:
            if idioma_origem.code == "pt":
                continue

            traducao = idioma_origem.get_translation(idioma_pt)
            texto_traduzido = traducao.translate(texto)

            if texto_traduzido.lower().strip() != texto.lower().strip():
                return texto_traduzido

        return texto

    except Exception as erro:
        print("Erro na tradução:", erro)
        return texto
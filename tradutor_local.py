import argostranslate.package
import argostranslate.translate


def instalar_pacote_traducao(origem="en", destino="pt"):
    pacotes_disponiveis = argostranslate.package.get_available_packages()

    pacote = next(
        (p for p in pacotes_disponiveis if p.from_code == origem and p.to_code == destino),
        None
    )

    if pacote:
        caminho_pacote = pacote.download()
        argostranslate.package.install_from_path(caminho_pacote)


def traduzir_para_portugues(texto):
    try:
        return argostranslate.translate.translate(texto, "en", "pt")
    except Exception:
        return texto
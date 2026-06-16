import os


# modelo da Hugging Face que roda localmente (dá pra trocar pela variável de ambiente)
MODELO_PADRAO = os.environ.get("LLM_MODELO", "Qwen/Qwen2.5-1.5B-Instruct")
# tamanho máximo da resposta gerada
MAX_TOKENS_NOVOS = int(os.environ.get("LLM_MAX_TOKENS", "150"))


# o modelo é pesado, então carregamos uma vez só e reaproveitamos
_gerador = None
_carregamento_falhou = False


# carrega o modelo da Hugging Face (só na 1ª vez)
def _carregar_modelo():
    global _gerador, _carregamento_falhou

    if _gerador is not None:
        return _gerador

    if _carregamento_falhou:
        return None

    try:
        from transformers import pipeline

        print(f"Carregando LLM local '{MODELO_PADRAO}' (pode demorar no 1º uso)...")
        _gerador = pipeline("text-generation", model=MODELO_PADRAO)
        print("LLM local carregada com sucesso.")
        return _gerador

    except Exception as erro:
        print(f"Não foi possível carregar a LLM local: {erro}")
        _carregamento_falhou = True
        return None


INSTRUCAO_SISTEMA = (
    "Você é um especialista em NBA. Responda sempre em português, de forma "
    "curta, clara e amigável. Se não souber, diga que não tem certeza."
)


# verifica se o modelo aceita formato de chat
def _suporta_chat(gerador):
    return getattr(gerador.tokenizer, "chat_template", None) is not None


# monta o prompt de texto para modelos sem chat (ex.: GPT-2)
def _montar_prompt(pergunta):
    return (
        "Você é um especialista em NBA e responde de forma curta e amigável.\n"
        f"Pergunta: {pergunta}\n"
        "Resposta:"
    )


# limpa a resposta: tira o prompt repetido e pega só o 1º parágrafo
def _limpar_resposta(texto_gerado, prompt):
    resposta = texto_gerado.replace(prompt, "").strip()
    resposta = resposta.split("\n")[0].strip()
    return resposta


# gera a resposta da IA (fallback quando a base não sabe responder)
def gerar_resposta_llm(pergunta, historico=None):
    gerador = _carregar_modelo()

    if gerador is None:
        return None

    try:
        if _suporta_chat(gerador):
            mensagens = [{"role": "system", "content": INSTRUCAO_SISTEMA}]

            if historico:
                mensagens.extend(historico)

            mensagens.append({"role": "user", "content": pergunta})

            saida = gerador(
                mensagens,
                max_new_tokens=MAX_TOKENS_NOVOS,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                pad_token_id=gerador.tokenizer.eos_token_id,
            )

            gerado = saida[0]["generated_text"]

            if isinstance(gerado, list):
                resposta = gerado[-1]["content"].strip()
            else:
                resposta = str(gerado).strip()

        else:
            prompt = _montar_prompt(pergunta)

            saida = gerador(
                prompt,
                max_new_tokens=MAX_TOKENS_NOVOS,
                num_return_sequences=1,
                do_sample=True,
                top_k=50,
                top_p=0.95,
                temperature=0.8,
                pad_token_id=gerador.tokenizer.eos_token_id,
            )

            resposta = _limpar_resposta(saida[0]["generated_text"], prompt)

        return resposta or None

    except Exception as erro:
        print(f"Erro ao gerar resposta com a LLM: {erro}")
        return None

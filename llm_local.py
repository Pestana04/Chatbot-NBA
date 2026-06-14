"""
Integração com um modelo de linguagem (LLM) local da plataforma Hugging Face.

Este módulo é usado como FALLBACK: o agente só recorre à LLM quando a base
de conhecimento (dados.json) não tem informação suficiente para responder.

O modelo roda localmente via biblioteca `transformers` (não precisa de token
nem de internet depois que os pesos são baixados na primeira execução).
"""

import os


# Nome do modelo da Hugging Face (https://huggingface.co/models).
# Pode ser trocado pela variável de ambiente LLM_MODELO. O padrão é o
# Qwen2.5-1.5B-Instruct: um modelo instruído (segue perguntas), multilíngue
# (bom em português) e com respostas mais precisas que a versão 0.5B.
MODELO_PADRAO = os.environ.get("LLM_MODELO", "Qwen/Qwen2.5-1.5B-Instruct")

# Quantidade máxima de tokens novos que a LLM gera por resposta.
MAX_TOKENS_NOVOS = int(os.environ.get("LLM_MAX_TOKENS", "150"))


# O pipeline é pesado, então carregamos uma única vez (lazy loading) e
# reaproveitamos nas próximas chamadas.
_gerador = None
_carregamento_falhou = False


def _carregar_modelo():
    """Carrega o pipeline de geração de texto uma única vez."""
    global _gerador, _carregamento_falhou

    if _gerador is not None:
        return _gerador

    # Se já tentamos e não deu certo, não insistimos a cada mensagem.
    if _carregamento_falhou:
        return None

    try:
        from transformers import pipeline

        print(f"Carregando LLM local '{MODELO_PADRAO}' (pode demorar no 1º uso)...")
        _gerador = pipeline("text-generation", model=MODELO_PADRAO)
        print("LLM local carregada com sucesso.")
        return _gerador

    except Exception as erro:
        # Se transformers/torch não estiverem instalados, ou o download falhar,
        # marcamos como falho. O app continua funcionando com a base de
        # conhecimento e a resposta padrão, sem quebrar.
        print(f"Não foi possível carregar a LLM local: {erro}")
        _carregamento_falhou = True
        return None


INSTRUCAO_SISTEMA = (
    "Você é um especialista em NBA. Responda sempre em português, de forma "
    "curta, clara e amigável. Se não souber, diga que não tem certeza."
)


def _suporta_chat(gerador):
    """Indica se o modelo tem um chat template (modelos instruídos têm)."""
    return getattr(gerador.tokenizer, "chat_template", None) is not None


def _montar_prompt(pergunta):
    """Prompt simples para modelos sem chat template (ex.: GPT-2)."""
    return (
        "Você é um especialista em NBA e responde de forma curta e amigável.\n"
        f"Pergunta: {pergunta}\n"
        "Resposta:"
    )


def _limpar_resposta(texto_gerado, prompt):
    """Remove o prompt repetido e mantém só a primeira parte da resposta."""
    resposta = texto_gerado.replace(prompt, "").strip()

    # Mantém apenas o primeiro parágrafo para evitar texto solto e repetitivo.
    resposta = resposta.split("\n")[0].strip()

    return resposta


def gerar_resposta_llm(pergunta, historico=None):
    """
    Tenta gerar uma resposta usando a LLM local.

    `historico` é uma lista opcional de mensagens anteriores no formato
    {"role": "user"/"assistant", "content": ...}, usada para dar contexto
    em perguntas de acompanhamento (ex.: "em qual time ele joga?").

    Retorna a string gerada ou None quando a LLM não está disponível
    (ex.: dependências não instaladas) ou quando a geração falha. Nesses
    casos, quem chama deve seguir com a resposta padrão.
    """
    gerador = _carregar_modelo()

    if gerador is None:
        return None

    try:
        if _suporta_chat(gerador):
            # Modelo instruído: usa o chat template (system + histórico + user).
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

            # Com entrada em formato de chat, a saída é a lista de mensagens;
            # a última é a resposta do assistente.
            if isinstance(gerado, list):
                resposta = gerado[-1]["content"].strip()
            else:
                resposta = str(gerado).strip()

        else:
            # Modelo simples (ex.: GPT-2): prompt de texto puro.
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

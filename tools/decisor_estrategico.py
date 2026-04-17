#!/usr/bin/env python3
"""
Agente Decisor Estratégico — Between Reestruturação 2026

Analisa as decisões estratégicas abertas e gera um documento estruturado
com opções, análise e recomendações para Dani e Fabiola.

Diretrizes Anthropic aplicadas:
  - Prompt caching no contexto extenso (cache_control: ephemeral)
  - Tool use para output estruturado e consistente
  - Loop agêntico com stopping condition explícita
  - Modelo configurável via constante MODEL

Uso:
  python tools/decisor_estrategico.py
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import anthropic
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
CONTEXT_DIR = BASE_DIR / "context" / "between"
OUTPUT_FILE = CONTEXT_DIR / "decisoes-analise.md"

MODEL = "claude-sonnet-4-6"          # Troque por claude-opus-4-6 para análise mais profunda
MAX_TOKENS = 8096
MAX_LOOP_ITERATIONS = 20             # Teto de segurança para o loop agêntico


# ---------------------------------------------------------------------------
# Ferramentas do agente
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "registrar_analise_decisao",
        "description": (
            "Registra a análise completa de uma decisão estratégica aberta. "
            "Chame esta ferramenta UMA VEZ para cada decisão identificada, "
            "na ordem em que aparecem no documento de direcionamento."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "integer",
                    "description": "Número sequencial da decisão (1, 2, 3…)"
                },
                "titulo": {
                    "type": "string",
                    "description": "Título claro e objetivo da decisão"
                },
                "contexto": {
                    "type": "string",
                    "description": (
                        "Por que essa decisão existe agora e o que está em jogo. "
                        "Referencie os benchmarks e o direcionamento estratégico quando relevante."
                    )
                },
                "opcoes": {
                    "type": "array",
                    "description": "Entre 2 e 3 opções concretas e acionáveis para a decisão.",
                    "minItems": 2,
                    "maxItems": 3,
                    "items": {
                        "type": "object",
                        "properties": {
                            "letra": {
                                "type": "string",
                                "description": "Identificador da opção: A, B ou C"
                            },
                            "nome": {
                                "type": "string",
                                "description": "Nome curto e memorável para a opção"
                            },
                            "descricao": {
                                "type": "string",
                                "description": "O que essa opção significa na prática para a Between"
                            },
                            "pontos_fortes": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "2 a 4 pontos fortes desta opção"
                            },
                            "pontos_fracos": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "1 a 3 riscos ou limitações desta opção"
                            },
                            "alinhamento_tese": {
                                "type": "string",
                                "enum": ["Alto", "Médio", "Baixo"],
                                "description": "Grau de alinhamento com a tese central da Between"
                            }
                        },
                        "required": [
                            "letra", "nome", "descricao",
                            "pontos_fortes", "pontos_fracos", "alinhamento_tese"
                        ]
                    }
                },
                "recomendacao": {
                    "type": "string",
                    "enum": ["A", "B", "C"],
                    "description": "Letra da opção recomendada"
                },
                "justificativa": {
                    "type": "string",
                    "description": (
                        "Raciocínio direto de por que essa opção é a mais forte "
                        "dado o momento e o contexto da Between. Seja específico."
                    )
                }
            },
            "required": [
                "id", "titulo", "contexto", "opcoes", "recomendacao", "justificativa"
            ]
        }
    },
    {
        "name": "finalizar_documento",
        "description": (
            "Finaliza a sessão após todas as decisões terem sido analisadas. "
            "Chame esta ferramenta APENAS UMA VEZ, depois de registrar todas as decisões."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "resumo_executivo": {
                    "type": "string",
                    "description": "2 a 3 frases sobre o que este conjunto de decisões representa para a Between agora"
                },
                "proximos_passos": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Lista ordenada de ações concretas para depois que as decisões forem fechadas"
                }
            },
            "required": ["resumo_executivo", "proximos_passos"]
        }
    }
]


# ---------------------------------------------------------------------------
# Carregamento de contexto
# ---------------------------------------------------------------------------

def carregar_contexto() -> str:
    """Lê todos os arquivos .md de context/between/ e concatena em uma string."""
    arquivos = sorted(CONTEXT_DIR.glob("*.md"))

    if not arquivos:
        print("[ERRO] Nenhum arquivo de contexto encontrado em context/between/")
        sys.exit(1)

    partes = []
    for arquivo in arquivos:
        if arquivo.name == OUTPUT_FILE.name:
            continue  # Não inclui o próprio output como contexto

        conteudo = arquivo.read_text(encoding="utf-8")
        partes.append(f"### Arquivo: {arquivo.name}\n\n{conteudo}")
        print(f"  [contexto] carregado: {arquivo.name}")

    return "\n\n---\n\n".join(partes)


# ---------------------------------------------------------------------------
# Renderização do output em Markdown
# ---------------------------------------------------------------------------

def renderizar_opcao(opcao: dict) -> str:
    fortes = "\n".join(f"  - {p}" for p in opcao["pontos_fortes"])
    fracos = "\n".join(f"  - {p}" for p in opcao["pontos_fracos"])
    return (
        f"**Opção {opcao['letra']} — {opcao['nome']}**\n\n"
        f"{opcao['descricao']}\n\n"
        f"Pontos fortes:\n{fortes}\n\n"
        f"Pontos fracos:\n{fracos}\n\n"
        f"Alinhamento com a tese: **{opcao['alinhamento_tese']}**"
    )


def renderizar_decisao(analise: dict, numero_total: int) -> str:
    opcoes_md = "\n\n".join(renderizar_opcao(o) for o in analise["opcoes"])
    return (
        f"## Decisão {analise['id']} de {numero_total}: {analise['titulo']}\n\n"
        f"### Contexto\n\n{analise['contexto']}\n\n"
        f"### Opções\n\n{opcoes_md}\n\n"
        f"### Recomendação: Opção {analise['recomendacao']}\n\n"
        f"{analise['justificativa']}\n\n"
        f"---\n\n"
        f"**Decisão de Dani e Fabiola:** ☐ A  ☐ B  ☐ C\n\n"
        f"**Observações:**\n\n_______________________________________\n"
    )


def escrever_documento(decisoes: list[dict], finalizacao: dict) -> None:
    hoje = datetime.today().strftime("%d/%m/%Y")
    cabecalho = (
        f"# Between | Análise de Decisões Estratégicas Abertas\n\n"
        f"Gerado em: {hoje}\n"
        f"Modelo: {MODEL}\n\n"
        f"---\n\n"
        f"## Resumo Executivo\n\n"
        f"{finalizacao['resumo_executivo']}\n\n"
        f"---\n\n"
    )

    secoes = "\n".join(
        renderizar_decisao(d, len(decisoes)) for d in decisoes
    )

    passos = "\n".join(
        f"{i+1}. {p}" for i, p in enumerate(finalizacao["proximos_passos"])
    )
    rodape = f"## Próximos Passos\n\n{passos}\n"

    OUTPUT_FILE.write_text(
        cabecalho + secoes + rodape,
        encoding="utf-8"
    )
    print(f"\n[✓] Documento gerado: {OUTPUT_FILE.relative_to(BASE_DIR)}")


# ---------------------------------------------------------------------------
# Processamento de tool calls
# ---------------------------------------------------------------------------

def processar_tool_call(
    nome: str,
    inputs: dict,
    decisoes: list[dict],
    finalizacao: list[dict]
) -> str:
    """Executa a tool call e retorna uma confirmação para o agente."""
    if nome == "registrar_analise_decisao":
        decisoes.append(inputs)
        print(f"  [decisão {inputs['id']}] registrada: {inputs['titulo']}")
        return f"Decisão {inputs['id']} registrada com sucesso."

    if nome == "finalizar_documento":
        finalizacao.append(inputs)
        print("  [finalizar] documento pronto para escrita.")
        return "Documento finalizado. Encerrando sessão."

    return f"Ferramenta desconhecida: {nome}"


# ---------------------------------------------------------------------------
# Loop agêntico principal
# ---------------------------------------------------------------------------

def rodar_agente() -> None:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("[ERRO] ANTHROPIC_API_KEY não encontrada no .env")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    print("\n=== Agente Decisor Estratégico — Between ===\n")
    print("[1/3] Carregando contexto...")
    contexto = carregar_contexto()

    # System prompt com cache no bloco de contexto (Anthropic best practice)
    system = [
        {
            "type": "text",
            "text": (
                "Você é um advisor estratégico da Between — hub premium de soluções "
                "para mulheres empreendedoras. Seu papel é analisar as decisões estratégicas "
                "abertas da empresa e gerar análises estruturadas que ajudem Dani e Fabiola "
                "a decidir com clareza e velocidade.\n\n"
                "Princípios para suas análises:\n"
                "- Seja específico. Opções vagas não ajudam.\n"
                "- Fundamente cada recomendação no contexto real da Between.\n"
                "- Priorize alinhamento com a tese central: "
                "'Desalinhamento é o que trava quem já tem potência.'\n"
                "- Use a fórmula dos benchmarks: pensar como Bossbabe, organizar como Millena, "
                "empacotar como Camila.\n"
                "- Tom: direto, preciso, sofisticado. Sem jargão vazio.\n\n"
                "A seguir está todo o contexto disponível da Between:"
            )
        },
        {
            "type": "text",
            "text": contexto,
            "cache_control": {"type": "ephemeral"}  # Cache no bloco extenso
        }
    ]

    user_prompt = (
        "Analise os arquivos de contexto e identifique todas as decisões estratégicas "
        "que ainda estão abertas (ignore as marcadas como FECHADAS).\n\n"
        "Para cada decisão aberta, chame a ferramenta `registrar_analise_decisao` com "
        "sua análise completa.\n\n"
        "Depois de registrar TODAS as decisões, chame `finalizar_documento` com um resumo "
        "executivo e os próximos passos concretos.\n\n"
        "Importante: processe as decisões uma por vez, na ordem em que fazem sentido estratégico, "
        "da mais fundamental para a mais derivada."
    )

    messages = [{"role": "user", "content": user_prompt}]

    decisoes: list[dict] = []
    finalizacao: list[dict] = []

    print("[2/3] Rodando agente...\n")

    # Loop agêntico
    for iteracao in range(MAX_LOOP_ITERATIONS):
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system,
            tools=TOOLS,
            messages=messages
        )

        # Adiciona resposta do assistente ao histórico
        messages.append({"role": "assistant", "content": response.content})

        # Condição de parada: agente terminou
        if response.stop_reason == "end_turn":
            break

        # Processa tool calls
        if response.stop_reason == "tool_use":
            tool_results = []

            for bloco in response.content:
                if bloco.type == "tool_use":
                    resultado = processar_tool_call(
                        bloco.name, bloco.input, decisoes, finalizacao
                    )
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": bloco.id,
                        "content": resultado
                    })

            messages.append({"role": "user", "content": tool_results})

            # Se finalizacao foi chamada, encerra o loop
            if finalizacao:
                # Deixa o agente responder à confirmação e depois para
                continue

        # Guarda de segurança
        if iteracao == MAX_LOOP_ITERATIONS - 1:
            print("[AVISO] Limite máximo de iterações atingido.")

    # Validação mínima
    if not decisoes:
        print("[ERRO] Nenhuma decisão foi registrada pelo agente.")
        sys.exit(1)

    if not finalizacao:
        print("[AVISO] finalizar_documento não foi chamada. Gerando rodapé vazio.")
        finalizacao.append({
            "resumo_executivo": "Análise concluída.",
            "proximos_passos": ["Revisar o documento com Dani e Fabiola."]
        })

    print(f"\n[3/3] Escrevendo documento ({len(decisoes)} decisões analisadas)...")
    escrever_documento(decisoes, finalizacao[0])

    # Exibe uso de tokens (útil para monitorar custo do cache)
    uso = response.usage
    print(
        f"\n[tokens] input={uso.input_tokens} | output={uso.output_tokens} "
        f"| cache_criado={getattr(uso, 'cache_creation_input_tokens', 0)} "
        f"| cache_lido={getattr(uso, 'cache_read_input_tokens', 0)}"
    )


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    rodar_agente()

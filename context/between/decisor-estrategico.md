# Workflow: Agente Decisor Estratégico

Data de criação: 2026-04-12

---

## Objetivo

Analisar as decisões estratégicas abertas da Between e gerar um documento estruturado com opções concretas, análise de alinhamento e recomendação fundamentada — pronto para ser usado como pauta de reunião entre Dani e Fabiola.

O agente não toma as decisões. Ele prepara o terreno para que Dani e Fabiola as tomem com clareza, velocidade e confiança.

---

## Quando usar

- Há decisões abertas documentadas em `context/between/`
- Uma reunião de direção precisa de pauta estruturada e análise prévia
- Uma nova decisão estratégica surgiu e precisa ser analisada antes de implementar
- O contexto do projeto foi atualizado e as recomendações anteriores precisam ser revisadas

---

## Inputs necessários

| Input | Origem | Obrigatório? |
|---|---|---|
| Arquivos de contexto da Between | `context/between/*.md` | Sim |
| `ANTHROPIC_API_KEY` | `.env` | Sim |

O agente lê automaticamente todos os arquivos `.md` em `context/between/`. Para adicionar contexto novo, basta colocar o arquivo na pasta.

---

## Como executar

```bash
# Instalar dependências (primeira vez)
pip install -r requirements.txt

# Rodar o agente
python tools/decisor_estrategico.py
```

O agente imprime progresso no terminal e gera o output ao finalizar.

---

## Output

**Arquivo gerado:** `context/between/decisoes-analise.md`

Estrutura do documento:
- Cabeçalho com data e decisões fechadas anteriores
- Para cada decisão aberta:
  - Contexto e por que importa agora
  - 2 a 3 opções concretas com pontos fortes, pontos fracos e alinhamento com a tese central
  - Recomendação com justificativa
  - Campo para registro da escolha final de Dani e Fabiola
- Próximos passos sugeridos

---

## Arquitetura do agente

Segue as diretrizes Anthropic para construção de agentes:

**1. Prompt caching**
O contexto dos arquivos da Between (potencialmente grande) é enviado com `cache_control: ephemeral` no system prompt. Isso reduz custo e latência em re-execuções.

**2. Tool use para output estruturado**
O agente usa a ferramenta `registrar_analise_decisao` para garantir que cada análise tenha a estrutura correta. Isso evita outputs livres e inconsistentes.

**3. Loop agêntico com stopping condition clara**
O agente roda em loop até que todas as decisões abertas tenham sido processadas e a ferramenta `finalizar_documento` tenha sido chamada. O loop encerra quando `stop_reason == "end_turn"`.

**4. Modelo**
`claude-sonnet-4-6` — equilíbrio entre capacidade analítica e custo. Trocar para `claude-opus-4-6` se a qualidade das recomendações precisar ser ainda mais profunda.

---

## Processo interno do agente

```
1. Carrega todos os .md de context/between/
2. Identifica decisões já fechadas (para não repetir trabalho)
3. Para cada decisão aberta:
   a. Analisa o contexto completo
   b. Gera 2–3 opções concretas
   c. Avalia alinhamento de cada opção com a tese central
   d. Recomenda uma opção com justificativa
   e. Chama tool registrar_analise_decisao (output estruturado)
4. Chama tool finalizar_documento com próximos passos
5. Escreve context/between/decisoes-analise.md
```

---

## Edge cases e aprendizados

- **Decisões já fechadas**: O agente detecta automaticamente o bloco "DECISÕES FECHADAS" no documento de direcionamento e não as reanálisa.
- **Contexto insuficiente**: Se alguma decisão não tiver contexto suficiente nos arquivos, o agente sinalizará no campo `contexto` da análise em vez de fabricar uma recomendação.
- **Re-execução**: O arquivo de output é sobrescrito a cada execução. Se quiser preservar uma versão anterior, renomeie o arquivo antes de rodar novamente.
- **API rate limits**: O agente usa um único ciclo de mensagens por decisão, não paralelo. Sem risco de throttling em uso normal.

---

## Critérios de qualidade do output

- Cada opção é concreta e acionável, não vaga
- A recomendação está fundamentada no contexto existente, não em opinião genérica
- O documento pode ser usado diretamente em reunião sem edição prévia
- A linguagem acompanha o tom da Between: precisa, sofisticada, sem jargão vazio

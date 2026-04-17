"""
Extrai texto de todos os PDFs em uma pasta e gera um arquivo de contexto compacto.
Uso: python3 tools/extrair_contexto_pdfs.py [pasta_de_pdfs]
"""
import sys
import os
import fitz  # PyMuPDF

def extrair_texto_pdf(caminho_pdf, max_chars=8000):
    """Extrai texto de um PDF, limitando o tamanho para não sobrecarregar o contexto."""
    try:
        doc = fitz.open(caminho_pdf)
        texto = ""
        for i, pagina in enumerate(doc):
            texto += pagina.get_text()
            if len(texto) > max_chars:
                texto = texto[:max_chars]
                texto += f"\n\n[... truncado após {max_chars} chars — {len(doc)} páginas no total ...]"
                break
        doc.close()
        return texto.strip()
    except Exception as e:
        return f"[ERRO ao ler PDF: {e}]"

def processar_pasta(pasta, saida=".tmp/contexto_projetos.md"):
    os.makedirs(os.path.dirname(saida), exist_ok=True)

    pdfs = [f for f in os.listdir(pasta) if f.lower().endswith(".pdf")]
    pdfs.sort()

    if not pdfs:
        print(f"Nenhum PDF encontrado em: {pasta}")
        return

    print(f"Encontrados {len(pdfs)} PDFs. Extraindo texto...\n")

    with open(saida, "w", encoding="utf-8") as out:
        out.write("# Contexto dos Projetos Between Phygital\n\n")
        out.write(f"_Extraído de {len(pdfs)} PDFs em `{pasta}`_\n\n")
        out.write("---\n\n")

        for nome in pdfs:
            caminho = os.path.join(pasta, nome)
            tamanho_kb = os.path.getsize(caminho) // 1024
            print(f"  Processando: {nome} ({tamanho_kb} KB)...")

            texto = extrair_texto_pdf(caminho)

            out.write(f"## {nome}\n")
            out.write(f"_Tamanho: {tamanho_kb} KB_\n\n")
            out.write(texto if texto else "_[Sem texto extraível — pode ser PDF com imagens]_")
            out.write("\n\n---\n\n")

    tamanho_saida = os.path.getsize(saida) // 1024
    print(f"\nConcluído! Contexto salvo em: {saida} ({tamanho_saida} KB)")
    print(f"Agora Claude pode ler esse arquivo sem travar.")

if __name__ == "__main__":
    pasta = sys.argv[1] if len(sys.argv) > 1 else "between/produtos"
    processar_pasta(pasta)

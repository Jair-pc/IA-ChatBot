"""
Módulo de consulta ao banco de dados SQLite para o chatbot UCBvet.
Fornece o schema e a função de execução de queries.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.db')

SCHEMA_DESCRIPTION = """
Banco de dados SQLite da empresa UCBvet de inseminação artificial bovina.

Tabelas:

endereco(id, rua, numero, bairro, cidade, estado, pais)

fazendas(id, id_endereco, nome_fazenda)
  → JOIN com endereco via id_endereco

vacas(id, id_fazenda, numero_animal, lote, vaca, categoria, ECC, ciclicidade, peso)
  → JOIN com fazendas via id_fazenda
  - categoria: 'Multípara', 'Nulípara', 'Primípara precoce', 'Primípara tardia', 'Secundípara', 'Leiteira', 'Corte'
  - ECC: escore de condição corporal (float 0–5)
  - ciclicidade: 0=não ciclíca, 1=ciclíca, 2=ciclíca moderada, 3=ciclíca ativa
  - peso: em kg

inseminadores(id, nome_inseminador)

vendedores(id, nome, cpf)

vendas(id, id_fazenda, id_vendedor, protocolo, data_venda, valor_total)
  - protocolo: tipo de protocolo de sincronização utilizado
  - valor_total: valor em reais

visitas(id, id_fazenda, id_vendedor, id_venda, data_visita, houve_venda)
  - houve_venda: 0=não, 1=sim
  - id_venda: NULL quando não houve venda

resultados_inseminacao(id, id_vaca, protocolo, touro, id_inseminador, id_venda,
                       data_inseminacao, numero_IATF, DG, vazia_Com_Ou_Sem_CL, perda)
  - DG: diagnóstico de gestação (0=vazia, 1=prenha)
  - vazia_Com_Ou_Sem_CL: vazia com ou sem corpo lúteo (0=não, 1=sim)
  - perda: perda gestacional (0=não, 1=sim)
  - touro: nome do touro utilizado
"""


def _fix_sql(sql: str) -> str:
    """Corrige padrões comuns de SQL inválido para SQLite."""
    import re
    # Se tiver COUNT(*) ou SUM/AVG misturado com colunas sem GROUP BY, remove o aggregate
    # e retorna só as colunas → o LLM vai ver todos os registros e contar na resposta
    pattern = re.compile(
        r'SELECT\s+(COUNT\(\*\)|COUNT\([^)]+\)|SUM\([^)]+\)|AVG\([^)]+\))\s*,\s*(.+?)\s+FROM\s+',
        re.IGNORECASE | re.DOTALL,
    )
    m = pattern.search(sql)
    if m:
        columns = m.group(2).strip()
        sql = pattern.sub(f'SELECT {columns} FROM ', sql, count=1)
    return sql


def execute_query(sql: str) -> str:
    """Executa uma SELECT e retorna os resultados como texto tabulado."""
    sql = _fix_sql(sql)
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        conn.close()

        if not rows:
            return "Nenhum resultado encontrado para esta consulta."

        cols = list(rows[0].keys())
        lines = [" | ".join(cols), "-" * max(len(" | ".join(cols)), 40)]
        for row in rows[:100]:
            lines.append(" | ".join(str(row[c]) if row[c] is not None else "—" for c in cols))

        if len(rows) > 100:
            lines.append(f"... ({len(rows) - 100} linhas omitidas, total: {len(rows)})")

        return "\n".join(lines)

    except Exception as exc:
        return f"Erro ao executar query: {exc}"

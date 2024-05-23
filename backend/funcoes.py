from backend.db import executar_consulta

# Função para retornar dados de vendas por período
def dados_vendas_por_periodo(inicio, fim):
    consulta = (
        "SELECT SUM(valor_total) AS total_vendas, AVG(valor_total) AS media_vendas "
        "FROM vendas "
        "WHERE data_venda BETWEEN %s AND %s"
    )
    return executar_consulta(consulta, (inicio, fim))

# Função para retornar os melhores clientes
def melhores_clientes():
    consulta = (
        "SELECT c.nome_cliente, SUM(v.valor_total) AS total_compras "
        "FROM clientes c "
        "JOIN vendas v ON c.id = v.id_cliente "
        "GROUP BY c.nome_cliente "
        "ORDER BY total_compras DESC"
    )
    return executar_consulta(consulta)

# Função para retornar o protocolo de inseminação mais utilizado
def protocolo_mais_utilizado():
    consulta = (
        "SELECT id_protocolo, COUNT(*) AS quantidade "
        "FROM resultados_inseminacao "
        "GROUP BY id_protocolo "
        "ORDER BY quantidade DESC "
        "LIMIT 1"
    )
    return executar_consulta(consulta)

# Função para listar fazendas não visitadas no mês atual
def fazendas_nao_visidadas_mes_atual():
    consulta = (
        "SELECT f.id, f.nome_fazenda "
        "FROM fazendas f "
        "WHERE NOT EXISTS ( "
        "SELECT 1 " 
        "FROM visitas v "
        "WHERE f.id = v.id_fazenda " 
        "AND EXTRACT(MONTH FROM v.data_visita) = EXTRACT(MONTH FROM CURRENT_DATE))"
    )
    return executar_consulta(consulta)

# Função para calcular o percentual de vacas que não engravidaram após a inseminação
def percentual_vazias():
    consulta_total = "SELECT COUNT(*) FROM vacas"
    total_vacas = executar_consulta(consulta_total)[0][0]

    consulta_vazias = "SELECT COUNT(*) FROM resultados_inseminacao WHERE vazia_Com_Ou_Sem_CL = 1"
    vacas_vazias = executar_consulta(consulta_vazias)[0][0]
    
    percentual = (vacas_vazias / total_vacas) * 100
    return percentual

# Função para obter resultados de inseminação ordenados por data
def obter_resultados_inseminacao_ordenados_por_data():
    consulta = (
        "SELECT " 
        "ri.id AS id_resultado, "
        "ri.data_inseminacao, "
        "fi.nome_fazenda AS fazenda, "
        "ins.nome_inseminador AS inseminador, "
        "v.numero_animal AS numero_vaca, "
        "v.vaca, "
        "t.nome_touro AS touro, "
        "pi.protocolo AS protocolo, "
        "ri.numero_IATF, "
        "CASE ri.DG WHEN 1 THEN 'Sim' ELSE 'Não' END AS prenha, "
        "CASE ri.vazia_Com_Ou_Sem_CL WHEN 1 THEN 'Com CL' ELSE 'Sem CL' END AS status_gestacional, "
        "CASE ri.perda WHEN 1 THEN 'Sim' ELSE 'Não' END AS perda_gestacional "
        "FROM resultados_inseminacao AS ri "
        "JOIN vacas AS v ON ri.id_vaca = v.id "
        "JOIN fazendas AS fi ON v.id_fazenda = fi.id "
        "JOIN protocolos_inseminacao AS pi ON ri.id_protocolo = pi.id "
        "JOIN touros AS t ON ri.id_touro = t.id "
        "JOIN inseminadores AS ins ON ri.id_inseminador = ins.id "
        "ORDER BY ri.data_inseminacao DESC;"
    )
    return executar_consulta(consulta)

# Função para processar consultas SQL genéricas
def processar_consulta_generica(query):
    return executar_consulta(query)

# Função para processar as mensagens do usuário
def processar_funcoes(mensagem):
    if mensagem.strip().lower().startswith("sql:"):
        query = mensagem.strip()[4:].strip()
        return processar_consulta_generica(query)
    elif "quantas vacas" in mensagem.lower():
        consulta = "SELECT COUNT(*) FROM vacas"
        resultado = processar_consulta_generica(consulta)[0][0]
        return f"Você tem {resultado} vacas cadastradas."
    elif "quantos clientes" in mensagem.lower():
        consulta = "SELECT COUNT(*) FROM clientes"
        resultado = processar_consulta_generica(consulta)[0][0]
        return f"Você tem {resultado} clientes cadastrados."
    else:
        funcoes_disponiveis = {
            "dados_vendas_por_periodo": dados_vendas_por_periodo,
            "melhores_clientes": melhores_clientes,
            "protocolo_mais_utilizado": protocolo_mais_utilizado,
            "fazendas_nao_visidadas_mes_atual": fazendas_nao_visidadas_mes_atual,
            "percentual_vazias": percentual_vazias,
            "obter_resultados_inseminacao_ordenados_por_data": obter_resultados_inseminacao_ordenados_por_data
        }

        # Remove a parte "FUNCOES NECESSARIAS:" da mensagem
        mensagem = mensagem.replace("FUNCOES NECESSARIAS:", "").strip()

        # Divide a mensagem com base em "||" para processar funções ou SQL separadamente
        partes = mensagem.split("||")

        resultados = []
        for parte in partes:
            parte = parte.strip()
            # Verifica se é uma função
            for funcao_nome, funcao in funcoes_disponiveis.items():
                if funcao_nome in parte:
                    parametros = None
                    if "dados_vendas_por_periodo" in parte:
                        parametros_str = parte[parte.find("(") + 1: parte.find(")")]
                        parametros = parametros_str.split(",")
                    resultado = funcao() if not parametros else funcao(*parametros)
                    resultados.append((funcao_nome, resultado))

        resposta = " ".join([f"Função {funcao}: Resultado {resultado}" for funcao, resultado in resultados])
        return resposta

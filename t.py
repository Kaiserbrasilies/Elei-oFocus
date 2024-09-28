import pandas as pd
import requests
import zipfile
import io
import os
import plotly.express as px

# URL do arquivo ZIP
url = "https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_secao/votacao_secao_2020_CE.zip"

# Função para baixar e extrair o arquivo CSV da URL
def baixar_dados(url):
    print("Baixando e extraindo dados...")
    response = requests.get(url)
    
    if response.status_code == 200:
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            # Extraindo todos os arquivos
            z.extractall("dados_ceara")
            # Encontrando o arquivo CSV
            for filename in z.namelist():
                if filename.endswith('.csv'):
                    return os.path.join("dados_ceara", filename)
    else:
        print("Erro ao baixar os dados.")
        return None

# Função para exibir municípios do Ceará
def escolher_municipio(dados):
    municipios = dados['NM_MUNICIPIO'].unique()
    print("Municípios disponíveis no Ceará:")
    for i, municipio in enumerate(municipios):
        print(f"{i + 1}. {municipio}")
    
    escolha = int(input("Escolha o número do município: "))
    return municipios[escolha - 1]

# Função para exibir os cargos (prefeito ou vereador)
def escolher_cargo():
    print("Escolha o cargo:")
    print("1. Prefeito")
    print("2. Vereador")
    
    escolha = int(input("Escolha o número do cargo: "))
    return 11 if escolha == 1 else 13  # 11 para Prefeito, 13 para Vereador

# Função para exibir todos os candidatos de um município e cargo, com seus números
def exibir_candidatos(dados, municipio, cargo):
    # Filtrando os dados por município e cargo (CD_CARGO)
    filtro = (dados['NM_MUNICIPIO'] == municipio) & (dados['CD_CARGO'] == cargo)
    candidatos = dados.loc[filtro, ['NM_VOTAVEL', 'NR_VOTAVEL']].drop_duplicates().reset_index(drop=True)

    if candidatos.empty:
        print(f"\nNão foram encontrados candidatos para o cargo {cargo} no município de {municipio}.")
        return None

    print(f"\nCandidatos ao cargo {cargo} no município de {municipio}:\n")
    for i, row in candidatos.iterrows():
        print(f"{i + 1}. {row['NM_VOTAVEL']} - Número: {row['NR_VOTAVEL']}")
    
    escolha = int(input("Escolha o número do candidato: "))
    
    if 1 <= escolha <= len(candidatos):
        return candidatos.iloc[escolha - 1]['NM_VOTAVEL']
    else:
        print("Escolha inválida.")
        return None

# Função para exibir os votos por bairro ou distrito do município e gerar gráficos
def exibir_votos_por_bairro(dados, municipio, cargo, candidato):
    # Filtra os votos do candidato
    votos = dados[(dados['NM_MUNICIPIO'] == municipio) & (dados['CD_CARGO'] == cargo) & (dados['NM_VOTAVEL'] == candidato)]
    
    if votos.empty:
        print(f"\nNão foram encontrados votos para {candidato} no município de {municipio}.")
    else:
        # Agrupar por endereço (bairro ou distrito) e somar os votos
        votos_agrupados = votos.groupby('DS_LOCAL_VOTACAO_ENDERECO')['QT_VOTOS'].sum().reset_index()
        
        print(f"\nVotos para {candidato} no cargo {cargo} em {municipio} por bairro ou distrito:\n")
        total_votos_candidato = 0
        for index, row in votos_agrupados.iterrows():
            print(f"Bairro/Distrito: {row['DS_LOCAL_VOTACAO_ENDERECO']} - Total de votos: {row['QT_VOTOS']}")
            total_votos_candidato += row['QT_VOTOS']
        
        # Exibir a soma total de votos do candidato
        print(f"\nTotal de votos para {candidato} no município de {municipio}: {total_votos_candidato} votos")
        
        # Calcular o total de votos para o cargo no município
        total_votos_geral = dados[(dados['NM_MUNICIPIO'] == municipio) & (dados['CD_CARGO'] == cargo)]['QT_VOTOS'].sum()

        # Calcular a porcentagem de votos
        porcentagem_votos = (total_votos_candidato / total_votos_geral) * 100

        # Exibir a porcentagem de votos
        print(f"Porcentagem de votos de {candidato} em relação ao total: {porcentagem_votos:.2f}%")
        
        # Gerar gráfico de barras para os votos por bairro ou distrito
        fig_bar = px.bar(votos_agrupados, x='DS_LOCAL_VOTACAO_ENDERECO', y='QT_VOTOS', title=f'Votos por Bairro/Distrito - {candidato}', labels={'DS_LOCAL_VOTACAO_ENDERECO': 'Bairro/Distrito', 'QT_VOTOS': 'Total de Votos'})
        fig_bar.show()
        
        # Gerar gráfico de pizza para a porcentagem de votos do candidato
        fig_pie = px.pie(names=['Votos para Candidato', 'Outros Votos'], values=[total_votos_candidato, total_votos_geral - total_votos_candidato], title=f'Porcentagem de Votos - {candidato}')
        fig_pie.show()

        # Salvar gráficos como HTML para integrar no site
        fig_bar.write_html(f'grafico_votos_bairro_{candidato}.html')
        fig_pie.write_html(f'porcentagem_votos_bairro_{candidato}.html')

        # Escolher um distrito específico para somar os votos dos bairros
        distrito_escolhido = input("Digite o nome do distrito que deseja visualizar: ")
        
        # Filtrar os bairros do distrito escolhido e somar os votos
        votos_distrito = dados[(dados['NM_MUNICIPIO'] == municipio) & (dados['DS_LOCAL_VOTACAO_ENDERECO'].str.contains(distrito_escolhido, case=False))]
        if votos_distrito.empty:
            print(f"\nNão foram encontrados votos no distrito {distrito_escolhido}.")
        else:
            votos_distrito_agrupados = votos_distrito.groupby('DS_LOCAL_VOTACAO_ENDERECO')['QT_VOTOS'].sum().reset_index()
            total_votos_distrito = votos_distrito_agrupados['QT_VOTOS'].sum()
            print(f"\nTotal de votos no distrito {distrito_escolhido}: {total_votos_distrito} votos")

            # Gerar gráfico de barras para os votos por bairro do distrito
            fig_distrito = px.bar(votos_distrito_agrupados, x='DS_LOCAL_VOTACAO_ENDERECO', y='QT_VOTOS', title=f'Votos por Bairro no Distrito {distrito_escolhido}', labels={'DS_LOCAL_VOTACAO_ENDERECO': 'Bairro', 'QT_VOTOS': 'Total de Votos'})
            fig_distrito.show()

            # Salvar gráfico como HTML
            fig_distrito.write_html(f'grafico_votos_distrito_{distrito_escolhido}.html')

# Função principal
def main():
    # Baixar e carregar o arquivo CSV
    caminho_csv = baixar_dados(url)
    
    if caminho_csv:
        # Carregar os dados do CSV
        dados = pd.read_csv(caminho_csv, sep=';', encoding='latin1')

        # Filtrar por município
        municipio_escolhido = escolher_municipio(dados)
        
        # Escolher o cargo (Prefeito ou Vereador)
        cargo_escolhido = escolher_cargo()
        
        # Exibir todos os candidatos com seus números e escolher um
        candidato_escolhido = exibir_candidatos(dados, municipio_escolhido, cargo_escolhido)
        
        if candidato_escolhido:
            # Exibir votos por bairro ou distrito e gerar gráficos
            exibir_votos_por_bairro(dados, municipio_escolhido, cargo_escolhido, candidato_escolhido)

# Executa o programa
if __name__ == "__main__":
    main()

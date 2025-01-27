import requests
import csv
import os

def criar_pasta(banca, cargo):
    # Cria a estrutura de pastas: arquivos_baixados/banca/cargo
    caminho = os.path.join("arquivos_baixados", banca, cargo)
    os.makedirs(caminho, exist_ok=True)
    return caminho

# Caminho para o arquivo CSV
csv_file = 'links.csv'

# Lê os links do arquivo CSV
with open(csv_file, mode='r') as file:
    csv_reader = csv.reader(file)
    
    # Pula o cabeçalho se existir
    next(csv_reader, None)
    
    # Itera sobre cada linha do CSV
    for row in csv_reader:
        # Assume formato: url, banca, cargo
        url = row[0]
        banca = row[1]
        cargo = row[2]
        
        try:
            print(f"Baixando: {url}")
            response = requests.get(url)
            response.raise_for_status()

            # Cria pasta específica para banca/cargo
            pasta_destino = criar_pasta(banca, cargo)

            # Extrai o nome do arquivo da URL
            nome_arquivo = url.split("/")[-1]
            caminho_completo = os.path.join(pasta_destino, nome_arquivo)

            # Salva o arquivo
            with open(caminho_completo, "wb") as file_out:
                file_out.write(response.content)
            print(f"Arquivo salvo em: {caminho_completo}")
        except Exception as e:
            print(f"Erro ao baixar {url}: {e}")

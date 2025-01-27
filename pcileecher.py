import requests
from bs4 import BeautifulSoup
import os
import re
import time
from urllib.parse import urljoin
from datetime import datetime
from tqdm import tqdm
import logging

class PCILeecher:
    def __init__(self):
        self.base_url = "https://www.pciconcursos.com.br"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.session = requests.Session()
        self.setup_logging()
        self.gabaritos_url = "https://www.pciconcursos.com.br/gabaritos"
        self.ano_atual = datetime.now().year + 2  # Considera até 2 anos futuros
        self.ano_minimo = 1990  # Ano mínimo para busca

    def setup_logging(self):
        logging.basicConfig(
            filename='pcileecher.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def search_provas(self, query, ano=None, banca=None, max_pages=10):
        all_provas = []
        page = 1

        with tqdm(total=max_pages, desc="Buscando páginas") as pbar:
            while page <= max_pages:
                provas_page = self._get_provas_from_page(query, page)
                if not provas_page:
                    break
                
                # Filtros
                if ano:
                    provas_page = [p for p in provas_page if str(ano) in p.get('ano', '')]
                if banca:
                    provas_page = [p for p in provas_page if banca.lower() in p.get('banca', '').lower()]
                
                all_provas.extend(provas_page)
                page += 1
                pbar.update(1)

        return all_provas

    def _get_provas_from_page(self, query, page):
        search_url = f"{self.base_url}/provas/{query}/{page}/"
        try:
            response = self.session.get(search_url, headers=self.headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro ao acessar página {page}: {str(e)}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        provas = []

        for tr in soup.find_all('tr'):
            try:
                prova = self._extract_prova_info(tr)
                if prova:
                    provas.append(prova)
            except Exception as e:
                logging.error(f"Erro ao extrair informações da prova: {str(e)}")
                continue

        return provas

    def _extract_prova_info(self, tr):
        tds = tr.find_all('td')
        if len(tds) < 5:
            return None

        link = tds[0].find('a')
        if not link:
            return None

        return {
            'url': urljoin(self.base_url, link['href']),
            'nome': self._clean_filename(link.text.strip()),
            'ano': tds[1].text.strip(),
            'orgao': tds[2].text.strip(),
            'banca': tds[3].text.strip(),
            'nivel': tds[4].text.strip()
        }

    def download_prova(self, prova, pasta_destino):
        if not os.path.exists(pasta_destino):
            os.makedirs(pasta_destino)

        filename = f"{prova['nome']} ({prova['ano']}) - {prova['banca']}.pdf"
        filepath = os.path.join(pasta_destino, filename)

        # Verifica se arquivo já existe
        if os.path.exists(filepath):
            if self._verify_file_size(filepath):
                logging.info(f"Arquivo já existe e está completo: {filename}")
                return True
            
        try:
            response = self.session.get(prova['url'], headers=self.headers, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(filepath, 'wb') as f, tqdm(
                desc=filename,
                total=total_size,
                unit='iB',
                unit_scale=True
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        size = f.write(chunk)
                        pbar.update(size)
                        
            return True

        except Exception as e:
            logging.error(f"Erro ao baixar {filename}: {str(e)}")
            if os.path.exists(filepath):
                os.remove(filepath)  # Remove arquivo incompleto
            return False

    def _verify_file_size(self, filepath):
        """Verifica se o arquivo está completo comparando tamanho"""
        try:
            size = os.path.getsize(filepath)
            return size > 1024  # Maior que 1KB
        except:
            return False

    def _clean_filename(self, filename):
        # Remove caracteres inválidos e limita tamanho
        clean = re.sub(r'[<>:"/\\|?*]', '', filename)
        return clean[:150]  # Limita tamanho para evitar problemas

    def search_provas_e_gabaritos(self, query, ano=None, banca=None, download_gabaritos=True, max_pages=10):
        """Busca provas e gabaritos com filtros"""
        all_items = []
        
        # Busca provas
        provas = self.search_provas(query, ano, banca, max_pages)
        for prova in provas:
            prova['tipo'] = 'prova'
            all_items.append(prova)

        # Busca gabaritos se solicitado
        if download_gabaritos:
            gabaritos = self.search_gabaritos(query, ano, banca, max_pages)
            for gabarito in gabaritos:
                gabarito['tipo'] = 'gabarito'
                all_items.append(gabarito)

        return all_items

    def search_gabaritos(self, query, ano=None, banca=None, max_pages=10):
        """Busca gabaritos especificamente"""
        all_gabaritos = []
        page = 1

        with tqdm(total=max_pages, desc="Buscando gabaritos") as pbar:
            while page <= max_pages:
                search_url = f"{self.gabaritos_url}/{query}/{page}/"
                try:
                    response = self.session.get(search_url, headers=self.headers)
                    response.raise_for_status()
                    
                    if "Nenhum gabarito encontrado" in response.text:
                        break

                    soup = BeautifulSoup(response.text, 'html.parser')
                    gabaritos_page = self._extract_gabaritos(soup)
                    
                    # Aplicar filtros
                    if ano:
                        gabaritos_page = [g for g in gabaritos_page if str(ano) in g.get('ano', '')]
                    if banca:
                        gabaritos_page = [g for g in gabaritos_page if banca.lower() in g.get('banca', '').lower()]
                    
                    if not gabaritos_page:
                        break
                        
                    all_gabaritos.extend(gabaritos_page)
                    page += 1
                    pbar.update(1)
                    
                except Exception as e:
                    logging.error(f"Erro ao buscar gabaritos página {page}: {str(e)}")
                    break

        return all_gabaritos

    def _extract_gabaritos(self, soup):
        """Extrai informações dos gabaritos da página"""
        gabaritos = []
        for item in soup.find_all('div', class_='ga-list-item'):
            try:
                link = item.find('a', href=True)
                if not link:
                    continue
                    
                info = item.find('div', class_='ga-list-info')
                if not info:
                    continue

                # Extrair dados do gabarito
                titulo = link.text.strip()
                data_div = info.find('div', class_='ga-list-date')
                data = data_div.text.strip() if data_div else ''
                ano = data.split('/')[-1] if data else ''
                
                banca_div = info.find('div', class_='ga-list-org')
                banca = banca_div.text.strip() if banca_div else ''

                gabaritos.append({
                    'url': urljoin(self.base_url, link['href']),
                    'nome': self._clean_filename(titulo),
                    'ano': ano,
                    'banca': banca,
                    'data': data
                })
            except Exception as e:
                logging.error(f"Erro ao extrair gabarito: {str(e)}")
                continue
                
        return gabaritos

    def download_item(self, item, pasta_destino):
        """Download unificado para provas e gabaritos organizados por banca/concurso"""
        tipo = item.get('tipo', 'prova')
        banca = self._clean_filename(item['banca'])
        orgao = self._clean_filename(item['orgao'])
        ano = item['ano']

        # Cria estrutura de diretórios: banca/orgao_ano/
        pasta_banca = os.path.join(pasta_destino, banca)
        pasta_concurso = os.path.join(pasta_banca, f"{orgao}_{ano}")
        
        # Cria subpastas para provas e gabaritos dentro do concurso
        subpasta = os.path.join(pasta_concurso, tipo + 's')
        
        if not os.path.exists(subpasta):
            os.makedirs(subpasta)

        filename = f"{item['nome']} ({item['ano']}).pdf"
        filepath = os.path.join(subpasta, filename)

        # Verifica se arquivo já existe
        if os.path.exists(filepath):
            if self._verify_file_size(filepath):
                logging.info(f"Arquivo já existe e está completo: {filename}")
                return True
            
        try:
            response = self.session.get(item['url'], headers=self.headers, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(filepath, 'wb') as f, tqdm(
                desc=filename,
                total=total_size,
                unit='iB',
                unit_scale=True
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        size = f.write(chunk)
                        pbar.update(size)

            # Cria arquivo de índice para o concurso
            self._update_concurso_index(pasta_concurso, item)
                        
            return True

        except Exception as e:
            logging.error(f"Erro ao baixar {filename}: {str(e)}")
            if os.path.exists(filepath):
                os.remove(filepath)
            return False

    def _update_concurso_index(self, pasta_concurso, item):
        """Cria/atualiza arquivo de índice com informações do concurso"""
        index_file = os.path.join(pasta_concurso, "info.txt")
        
        info = {
            'Órgão': item['orgao'],
            'Banca': item['banca'],
            'Ano': item['ano'],
            'Nível': item.get('nivel', 'N/A')
        }
        
        # Cria ou atualiza arquivo de índice
        mode = 'a' if os.path.exists(index_file) else 'w'
        with open(index_file, mode, encoding='utf-8') as f:
            if mode == 'w':
                f.write("=== Informações do Concurso ===\n\n")
                for key, value in info.items():
                    f.write(f"{key}: {value}\n")
                f.write("\n=== Arquivos ===\n")
            f.write(f"\n- [{item['tipo']}] {item['nome']}")

    def download_all_by_year(self, ano_inicial=None, ano_final=None, banca=None, termos=None, max_pages=10):
        """Baixa todas as provas e gabaritos por anos específicos"""
        total_items = 0
        
        # Define intervalo de anos
        ano_inicial = ano_inicial if ano_inicial else self.ano_atual
        ano_final = ano_final if ano_final else self.ano_minimo
        
        # Garante ordem decrescente
        ano_inicial = max(ano_inicial, ano_final)
        ano_final = min(ano_inicial, ano_final)
        
        # Lista de termos padrão para busca
        termos_padrao = [
            "administracao", "direito", "contabilidade", "economia", 
            "informatica", "ti", "medicina", "enfermagem", "engenharia",
            "matematica", "portugues", "conhecimentos-gerais", "raciocinio-logico",
            # Adiciona mais termos comuns
            "tecnico", "analista", "auditor", "fiscal", "professor",
            "policia", "agente", "oficial", "assistente", "superior",
            "medio", "fundamental", "especialista", "gestor", "perito"
        ]

        if termos is None:  # Se não foi passado como parâmetro
            print("\nOpções de busca:")
            print("1. Baixar todo o conteúdo sem filtros")
            print("2. Usar termos de busca padrão")
            print("3. Definir termos específicos")
            
            opcao_termos = input("\nEscolha uma opção (1-3): ").strip()
            
            if opcao_termos == "1":
                # Ao invés de string vazia, usa termos padrão
                print("\nUsando termos de busca automatizados para encontrar todo o conteúdo...")
                termos = termos_padrao
            elif opcao_termos == "2":
                termos = termos_padrao
            elif opcao_termos == "3":
                termos_input = input("\nDigite os termos separados por vírgula: ").strip()
                termos = [t.strip() for t in termos_input.split(",") if t.strip()]
            else:
                print("Opção inválida! Usando termos de busca padrão.")
                termos = termos_padrao
                
        print(f"\nIniciando download de {ano_inicial} até {ano_final}")
        print(f"Usando {len(termos)} termos de busca")

        # Cria pasta base única para todo o download
        pasta_base = os.path.join(os.getcwd(), f"downloads_completo")
        
        # Itera sobre os anos
        for ano in range(ano_inicial, ano_final - 1, -1):
            print(f"\n=== Buscando conteúdo do ano {ano} ===")
            
            # Dicionário para controlar arquivos já baixados
            arquivos_baixados = set()
            
            for termo in termos:
                print(f"\nBuscando termo: {termo}")
                
                # Busca provas e gabaritos
                items = self.search_provas_e_gabaritos(termo, str(ano), banca, True, max_pages)
                
                if not items:
                    continue
                
                # Filtra itens já baixados
                items_novos = []
                for item in items:
                    identificador = f"{item['nome']}_{item['ano']}_{item['banca']}"
                    if identificador not in arquivos_baixados:
                        items_novos.append(item)
                        arquivos_baixados.add(identificador)
                
                if not items_novos:
                    continue
                    
                provas = [i for i in items_novos if i['tipo'] == 'prova']
                gabaritos = [i for i in items_novos if i['tipo'] == 'gabarito']
                
                print(f"Encontrados novos arquivos para {termo} em {ano}:")
                print(f"- {len(provas)} provas")
                print(f"- {len(gabaritos)} gabaritos")
                
                # Agrupa itens por banca
                items_por_banca = {}
                for item in items_novos:
                    banca_nome = item['banca']
                    if banca_nome not in items_por_banca:
                        items_por_banca[banca_nome] = []
                    items_por_banca[banca_nome].append(item)
                
                # Download por banca
                for banca_nome, banca_items in items_por_banca.items():
                    print(f"\nBaixando arquivos da banca {banca_nome} - Ano {ano}")
                    for item in banca_items:
                        if self.download_item(item, pasta_base):
                            total_items += 1
                        time.sleep(0.5)
                
                # Pequena pausa entre termos
                time.sleep(1)
                    
        return total_items

def main():
    leecher = PCILeecher()
    
    while True:
        print("\n=== PCI Leecher (Python Version) ===")
        print("\nOpções:")
        print("1. Busca específica")
        print("2. Download completo (todos os anos)")
        print("3. Download por período")
        print("4. Sair")
        
        opcao = input("\nEscolha uma opção (1-4): ").strip()
        
        if opcao == "4":
            print("\nPrograma finalizado!")
            break
            
        elif opcao in ["1", "2", "3"]:
            try:
                if opcao == "1":
                    # Código existente para busca específica
                    query = input("Digite os termos de busca (ex: cesgranrio ti): ").strip()
                    if not query:
                        print("Termo de busca inválido!")
                        return

                    ano = input("Filtrar por ano (opcional, Enter para pular): ").strip()
                    banca = input("Filtrar por banca (opcional, Enter para pular): ").strip()
                    baixar_gabaritos = input("Baixar gabaritos também? (s/n): ").strip().lower() == 's'

                    print("\nIniciando busca...")
                    items = leecher.search_provas_e_gabaritos(query, ano, banca, baixar_gabaritos)
                    
                    if not items:
                        print("\nNenhum item encontrado!")
                        return

                    provas = [i for i in items if i['tipo'] == 'prova']
                    gabaritos = [i for i in items if i['tipo'] == 'gabarito']
                    
                    print(f"\nEncontrados:")
                    print(f"- {len(provas)} provas")
                    print(f"- {len(gabaritos)} gabaritos")
                    
                    # Pasta base com timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    pasta_destino = os.path.join(os.getcwd(), f"downloads_{timestamp}")
                    
                    print(f"\nBaixando arquivos para: {pasta_destino}")
                    print("Os arquivos serão organizados por: banca/orgao_ano/[provas|gabaritos]/")
                    
                    # Agrupa itens por banca para melhor organização
                    items_por_banca = {}
                    for item in items:
                        banca = item['banca']
                        if banca not in items_por_banca:
                            items_por_banca[banca] = []
                        items_por_banca[banca].append(item)
                    
                    # Download por banca
                    sucessos = 0
                    for banca, banca_items in items_por_banca.items():
                        print(f"\nBaixando arquivos da banca: {banca}")
                        for item in banca_items:
                            if leecher.download_item(item, pasta_destino):
                                sucessos += 1
                            time.sleep(0.5)

                    print(f"\nDownload concluído! {sucessos} de {len(items)} arquivos baixados com sucesso!")
                    print(f"Log de erros disponível em: pcileecher.log")
                
                elif opcao == "2":
                    print("\n=== Download Completo ===")
                    banca = input("Filtrar por banca (opcional, Enter para pular): ").strip()
                    
                    print("\nIniciando download completo...")
                    print("Os arquivos serão organizados por: banca/orgao_ano/[provas|gabaritos]/")
                    print("Este processo pode levar várias horas dependendo da quantidade de arquivos.")
                    
                    if input("\nDeseja continuar? (s/n): ").strip().lower() != 's':
                        return
                        
                    total_items = leecher.download_all_by_year(banca=banca)
                    
                    print(f"\nDownload completo concluído!")
                    print(f"Total de arquivos baixados: {total_items}")
                    print(f"Os arquivos foram salvos em: downloads_completo/")
                    print(f"Log de erros disponível em: pcileecher.log")
                
                elif opcao == "3":
                    print("\n=== Download por Período ===")
                    
                    try:
                        ano_inicial = int(input("Ano inicial (ex: 2020): ").strip())
                        ano_final = int(input("Ano final (ex: 2015): ").strip())
                        
                        if ano_inicial < 1990 or ano_inicial > datetime.now().year + 2:
                            print("Ano inicial deve estar entre 1990 e o ano atual + 2!")
                            return
                            
                        if ano_final < 1990 or ano_final > datetime.now().year + 2:
                            print("Ano final deve estar entre 1990 e o ano atual + 2!")
                            return
                            
                    except ValueError:
                        print("Anos devem ser números válidos!")
                        return
                        
                    banca = input("Filtrar por banca (opcional, Enter para pular): ").strip()
                    
                    print("\nIniciando download por período...")
                    print("Os arquivos serão organizados por: banca/orgao_ano/[provas|gabaritos]/")
                    print("Este processo pode levar várias horas dependendo da quantidade de arquivos.")
                    
                    if input("\nDeseja continuar? (s/n): ").strip().lower() != 's':
                        return
                        
                    total_items = leecher.download_all_by_year(ano_inicial, ano_final, banca)
                    
                    print(f"\nDownload por período concluído!")
                    print(f"Total de arquivos baixados: {total_items}")
                    print(f"Os arquivos foram salvos em: downloads_completo/")
                    print(f"Log de erros disponível em: pcileecher.log")
                
                # Pergunta se quer continuar
                continuar = input("\nDeseja fazer outra operação? (s/n): ").strip().lower()
                if continuar != 's':
                    print("\nPrograma finalizado!")
                    break
                    
            except Exception as e:
                logging.error(f"Erro durante operação: {str(e)}")
                print("\nOcorreu um erro. Verifique o arquivo de log para detalhes.")
                if input("\nDeseja continuar mesmo assim? (s/n): ").strip().lower() != 's':
                    break
        else:
            print("\nOpção inválida! Tente novamente.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário.")
    except Exception as e:
        logging.error(f"Erro não tratado: {str(e)}")
        print("\nOcorreu um erro inesperado. Verifique o arquivo de log para mais detalhes.")

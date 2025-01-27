import requests
from bs4 import BeautifulSoup
import os
import re
import time
from urllib.parse import urljoin
from datetime import datetime
from tqdm import tqdm
import logging
from dotenv import load_dotenv
import json
import sys

class QConcursosLeecher:
    def __init__(self):
        self.base_url = "https://www.qconcursos.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3',
            'Connection': 'keep-alive',
        }
        self.session = requests.Session()
        self.setup_logging()
        self.cancelar = False
        self.auth_headers = {}

    def setup_logging(self):
        logging.basicConfig(
            filename='qconcursos_leecher.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def login(self, email, password):
        """Realiza login no QConcursos e obtém token de autenticação"""
        try:
            # Primeiro obtém o token CSRF da página de login
            login_page = self.session.get(f"{self.base_url}/usuarios/login")
            soup = BeautifulSoup(login_page.text, 'html.parser')
            csrf_token = soup.find('meta', {'name': 'csrf-token'})['content']
            
            # Configura headers para a requisição de login
            headers = {
                'X-CSRF-Token': csrf_token,
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Dados de login em JSON
            login_data = {
                'user': {
                    'email': email,
                    'password': password,
                    'remember_me': True
                }
            }
            
            # Faz o POST para login
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/sign_in",
                headers=headers,
                json=login_data
            )
            
            if response.status_code == 200:
                # Guarda os tokens de autenticação
                self.auth_headers = {
                    'access-token': response.headers.get('access-token'),
                    'client': response.headers.get('client'),
                    'uid': response.headers.get('uid')
                }
                print("Login realizado com sucesso!")
                return True
            else:
                print(f"Erro no login: {response.status_code}")
                return False
                
        except Exception as e:
            logging.error(f"Erro ao fazer login: {str(e)}")
            return False

    def cancel_download(self):
        self.cancelar = True
        print("\nCancelando downloads...")

    def search_provas(self, query, ano=None, banca=None, max_pages=10):
        """Busca provas usando a API do QConcursos"""
        all_provas = []
        
        # URL para lista de provas
        url = f"{self.base_url}/api/v2/questions/search"
        
        headers = {
            **self.headers,
            **self.auth_headers,
            'Content-Type': 'application/json'
        }
        
        params = {
            'q': query,
            'per_page': 100,
            'filters': {
                'subjects': [],
                'examining_boards': [banca] if banca else [],
                'years': [int(ano)] if ano else [],
            }
        }

        try:
            response = self.session.post(url, headers=headers, json=params)
            response.raise_for_status()
            data = response.json()
            
            provas = []
            for item in data.get('items', []):
                prova = {
                    'id': item['id'],
                    'titulo': item['question'],
                    'url': f"{self.base_url}/questoes/{item['id']}/download",
                    'ano': item.get('year'),
                    'banca': item.get('examining_board', {}).get('name'),
                    'orgao': item.get('institution', {}).get('name'),
                    'concurso': item.get('subject', {}).get('name'),
                    'gabarito_url': f"{self.base_url}/questoes/{item['id']}/gabarito",
                    'tem_gabarito': item.get('has_answer', False)
                }
                provas.append(prova)
                
            return provas
            
        except Exception as e:
            logging.error(f"Erro ao buscar provas: {str(e)}")
            return []

    def download_all_by_period(self, ano_inicial, ano_final, banca=None, lista_materias=None):
        """Download de provas por período com seleção de matérias"""
        total = 0
        
        if not lista_materias:
            lista_materias = [
                "Português", "Matemática", "Informática", "Direito",
                "Administração", "Raciocínio Lógico", "Legislação"
            ]
            
        # Confirma materias a baixar
        print("\nMatérias disponíveis:")
        for i, materia in enumerate(lista_materias, 1):
            print(f"{i}. {materia}")
        
        escolhas = input("\nDigite os números das matérias desejadas (separados por vírgula) ou Enter para todas: ").strip()
        if escolhas:
            indices = [int(x.strip())-1 for x in escolhas.split(",")]
            materias_selecionadas = [lista_materias[i] for i in indices if i < len(lista_materias)]
        else:
            materias_selecionadas = lista_materias

        print(f"\nBaixando provas de {ano_inicial} até {ano_final}")
        print(f"Matérias selecionadas: {', '.join(materias_selecionadas)}")

        for ano in range(ano_inicial, ano_final-1, -1):
            if self.cancelar:
                break
                
            for materia in materias_selecionadas:
                if self.cancelar:
                    break
                    
                print(f"\nBuscando {materia} - {ano}")
                provas = self.search_provas(materia, ano, banca)
                
                if not provas:
                    continue
                    
                print(f"Encontradas {len(provas)} provas")
                
                pasta_base = os.path.join("downloads_qconcursos", f"{ano}", materia)
                
                for prova in provas:
                    if self.cancelar:
                        break
                        
                    if self.download_item(prova, pasta_base):
                        total += 1
                    time.sleep(0.5)
                
        return total

    def download_item(self, item, pasta_destino):
        """Download de prova e gabarito"""
        if not os.path.exists(pasta_destino):
            os.makedirs(pasta_destino)

        filename = f"{self._clean_filename(item['titulo'])}_{item['id']}"
        
        # Download da prova
        prova_path = os.path.join(pasta_destino, f"{filename}_prova.pdf")
        if not os.path.exists(prova_path):
            try:
                self._download_file(item['url'], prova_path, "prova")
            except Exception as e:
                logging.error(f"Erro baixando prova {filename}: {e}")
                return False

        # Download do gabarito se disponível
        if item['tem_gabarito']:
            gabarito_path = os.path.join(pasta_destino, f"{filename}_gabarito.pdf")
            if not os.path.exists(gabarito_path):
                try:
                    self._download_file(item['gabarito_url'], gabarito_path, "gabarito")
                except Exception as e:
                    logging.error(f"Erro baixando gabarito {filename}: {e}")

        return True

    def _download_file(self, url, filepath, tipo):
        """Download genérico de arquivo com progresso"""
        response = self.session.get(url, headers=self.auth_headers, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(filepath, 'wb') as f, tqdm(
            desc=f"Baixando {tipo}",
            total=total_size,
            unit='iB',
            unit_scale=True
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                if self.cancelar:
                    break
                if chunk:
                    size = f.write(chunk)
                    pbar.update(size)

def main():
    load_dotenv()
    
    leecher = QConcursosLeecher()
    
    print("\n=== QConcursos Leecher ===")
    
    # Usa credenciais do arquivo .env
    email = os.getenv('QCONCURSOS_EMAIL')
    password = os.getenv('QCONCURSOS_PASSWORD')
    
    if not email or not password:
        print("Credenciais não encontradas no arquivo .env")
        return
        
    if not leecher.login(email, password):
        print("Falha no login!")
        return

    print("\nOpções:")
    print("1. Busca específica")
    print("2. Download por período")
    print("3. Cancelar downloads")
    
    opcao = input("\nEscolha uma opção: ").strip()
    
    if opcao == "1":
        query = input("Termo de busca: ")
        ano = input("Ano (opcional): ")
        banca = input("Banca (opcional): ")
        
        provas = leecher.search_provas(query, ano, banca)
        # ...processar resultados...
        
    elif opcao == "2":
        try:
            ano_inicial = int(input("Ano inicial: "))
            ano_final = int(input("Ano final: "))
            banca = input("Banca (opcional): ")
            
            total = leecher.download_all_by_period(ano_inicial, ano_final, banca)
            print(f"\nTotal baixado: {total} arquivos")
            
        except ValueError:
            print("Anos inválidos!")
            
    elif opcao == "3":
        leecher.cancel_download()
    
    else:
        print("Opção inválida!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário.")
    except Exception as e:
        logging.error(f"Erro não tratado: {str(e)}")
        print("\nOcorreu um erro inesperado. Verifique o arquivo de log para mais detalhes.")

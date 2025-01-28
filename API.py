from google.cloud import vision
import json
import io
from pdf2image import convert_from_path
import os

class VisionAPI:
    def __init__(self, credentials_path):
        # Configura a variável de ambiente com o caminho das credenciais
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        self.client = vision.ImageAnnotatorClient()
    
    def convert_pdf_to_images(self, pdf_path):
        return convert_from_path(pdf_path)
    
    def detect_text(self, image):
        if isinstance(image, str):  # Se for caminho do arquivo
            with io.open(image, 'rb') as image_file:
                content = image_file.read()
        else:  # Se for objeto Image do pdf2image
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            content = img_byte_arr.getvalue()
            
        image = vision.Image(content=content)
        response = self.client.document_text_detection(image=image)
        return response.full_text_annotation.text
    
    def process_exam(self, pdf_path):
        images = self.convert_pdf_to_images(pdf_path)
        result = {
            "questoes": []
        }
        
        for idx, image in enumerate(images):
            text = self.detect_text(image)
            # Processar o texto para extrair questões
            questoes = self.extract_questoes(text)
            result["questoes"].extend(questoes)
        
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    def extract_questoes(self, text):
        questoes = []
        # Implementar lógica para extrair questões do texto
        # Este é um exemplo simplificado
        linhas = text.split('\n')
        questao_atual = None
        
        for linha in linhas:
            if linha.strip().startswith('Questão'):
                if questao_atual:
                    questoes.append(questao_atual)
                questao_atual = {
                    "numero": len(questoes) + 1,
                    "enunciado": "",
                    "alternativas": []
                }
            elif questao_atual:
                if linha.strip().startswith(('A)', 'B)', 'C)', 'D)', 'E)')):
                    questao_atual["alternativas"].append(linha.strip())
                else:
                    questao_atual["enunciado"] += linha + "\n"
        
        if questao_atual:
            questoes.append(questao_atual)
            
        return questoes

    def process_exam_with_vertex(self, pdf_path):
        from exam_processor import ExamProcessor
        
        processor = ExamProcessor(
            project_id="praxis-gear-449212-n6",
            location="us-east5",
            credentials_path=self.credentials_path
        )
        
        return processor.process_exam(pdf_path)

# Exemplo de uso:
if __name__ == "__main__":
    # Substitua pelo caminho onde você salvou o arquivo JSON de credenciais
    credentials_path = "path/to/your/credentials.json"
    api = VisionAPI(credentials_path)
    # resultado = api.process_exam('caminho/da/prova.pdf')

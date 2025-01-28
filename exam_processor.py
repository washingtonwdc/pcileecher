from google.cloud import aiplatform
from google.cloud import storage
import json
from API import VisionAPI
from config import PROJECT_ID, LOCATION, CREDENTIALS_PATH

class ExamProcessor:
    def __init__(self):
        aiplatform.init(
            project=PROJECT_ID,
            location=LOCATION,
            credentials=CREDENTIALS_PATH
        )
        self.vision_api = VisionAPI(CREDENTIALS_PATH)
        
    def process_exam(self, pdf_path, block_size=10):
        # Primeiro extrair texto usando Vision API
        images = self.vision_api.convert_pdf_to_images(pdf_path)
        extracted_text = ""
        
        for image in images:
            text = self.vision_api.detect_text(image)
            extracted_text += text + "\n"
            
        # Usar o modelo Vertex AI
        endpoint = aiplatform.TextGenerationModel.from_pretrained("text-bison@001")
        
        prompt = f"""
        Analise o seguinte texto de prova e gere um JSON estruturado:
        
        {extracted_text}
        
        O JSON deve seguir este formato:
        {{
            "concurso": {{
                "nome": "nome_do_concurso",
                "ano": ano,
                "banca": "nome_da_banca",
                "quantidade_questoes": total
            }},
            "questoes": [
                {{
                    "numero": numero_questao,
                    "texto": "texto_da_questao",
                    "alternativas": ["A) ...", "B) ...", "C) ...", "D) ...", "E) ..."],
                    "gabarito": "letra_correta"
                }}
            ]
        }}
        """
        
        response = endpoint.predict(
            prompt,
            temperature=0.2,
            max_output_tokens=8192,
            top_k=40,
            top_p=0.8,
        )
        
        try:
            return json.loads(response.text)
        except json.JSONDecodeError as e:
            print(f"Erro ao decodificar JSON: {e}")
            return None

    def save_to_json(self, data, output_path):
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

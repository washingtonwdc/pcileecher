import json
import re
from typing import Dict, List, Optional
import os
from datetime import datetime

def extract_exam_header(text: str) -> Dict:
    """Extrai informações do cabeçalho da prova."""
    header = {}
    
    # Tenta extrair o título/descrição
    title_match = re.search(r"(CONCURSO PÚBLICO|Concurso Público).+?(?=\n)", text)
    if title_match:
        header["descricao"] = title_match.group(0).strip()

    # Tenta extrair a banca
    if "VUNESP" in text:
        header["banca"] = "VUNESP"
    elif "FGV" in text:
        header["banca"] = "FGV"
    
    # Tenta extrair o ano
    year_match = re.search(r"(?:19|20)\d{2}", text)
    if year_match:
        header["ano"] = year_match.group(0)
    
    # Outros campos do template
    header["area"] = "Concursos"
    header["categoria"] = "Concurso Público"
    header["nivel"] = "Superior"
    
    return header

def extract_questions(text: str) -> List[Dict]:
    """Extrai as questões do texto."""
    questions = []
    
    # Padrão para encontrar questões com enunciado
    question_pattern = r'(?:\d{1,3}\s*[-\)]|\d{1,3}\.)\s*([^A-E\n]{20,})'
    text_matches = re.finditer(question_pattern, text, re.DOTALL)
    
    for match in text_matches:
        question_text = match.group(1).strip()
        if question_text:
            # Tenta extrair alternativas
            alternatives = re.findall(r'[A-E][)\.-]\s*(.*?)(?=[A-E][)\.-]|$)', question_text, re.DOTALL)
            
            # Se encontrou alternativas, separa o enunciado
            if alternatives:
                try:
                    alt_marker = re.search(r'[A-E][)\.-]', question_text).group(0)
                    parts = question_text.split(alt_marker)
                    statement = parts[0].strip()
                except:
                    statement = question_text
                    alternatives = []
            else:
                statement = question_text
                alternatives = []
            
            # Só cria questão se tiver enunciado com tamanho mínimo
            if len(statement) > 20:  # Evita pegar apenas números ou letras soltas
                question = {
                    "numero_questao": str(len(questions) + 1),
                    "texto": statement,
                    "alternativas": alternatives,
                    "disciplina": extract_discipline(statement),
                    "resposta_correta": ""
                }
                questions.append(question)
    
    return questions

def extract_discipline(question_text: str) -> str:
    """Tenta extrair a disciplina com base no texto da questão."""
    # Mapeamento de palavras-chave para disciplinas
    disciplines = {
        "Direito Penal": ["penal", "crime", "pena", "delito"],
        "Direito Constitucional": ["constituição", "constitucional", "poder judiciário"],
        "Direito Processual": ["processo", "procedimento", "ação"],
        "Direito Administrativo": ["administrativo", "administração pública"],
        "Matemática": ["matemática", "número", "cálculo"],
        "Português": ["gramática", "texto", "linguagem"],
        "Informática": ["computador", "software", "arquivo"],
        "Raciocínio Lógico": ["lógica", "sequência", "proposição"]
    }
    
    # Busca por palavras-chave no texto da questão
    question_text = question_text.lower()
    for discipline, keywords in disciplines.items():
        if any(keyword in question_text for keyword in keywords):
            return discipline
            
    return "Não especificada"

def extract_answers(text: str) -> Dict[str, str]:
    """Extrai o gabarito das questões."""
    answers = {}
    
    # Procura por padrões de gabarito explícito (GABARITO, RESPOSTAS, etc)
    gabarito_sections = re.findall(r'(?:GABARITO|RESPOSTA)[^\n]+\n(.*?)(?=\n\n|\Z)', text, re.DOTALL | re.I)
    
    if gabarito_sections:
        for section in gabarito_sections:
            # Extrai pares número-resposta do gabarito
            matches = re.finditer(r'(?:^|\s)(\d{1,3})[)\s.:]-?\s*([A-E])', section)
            for match in matches:
                question_num = match.group(1).strip()
                answer = match.group(2).strip()
                answers[question_num] = answer
    else:
        # Se não encontrar seção explícita de gabarito, procura por padrões soltos
        # Só considera como gabarito sequências curtas número-letra
        matches = re.finditer(r'(?:^|\s)(\d{1,3})[)\s.:]-?\s*([A-E])(?:\s|$)', text)
        for match in matches:
            question_num = match.group(1).strip() 
            answer = match.group(2).strip()
            next_chars = text[match.end():match.end()+20].strip()
            
            # Só considera como gabarito se o que vier depois for curto 
            # (evita confundir com enunciados)
            if len(next_chars) < 20:
                answers[question_num] = answer

    return answers

def process_exam_file(filename: str) -> List[Dict]:
    """Processa o arquivo de provas e retorna uma lista de JSONs estruturados."""
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Divide o conteúdo em provas diferentes
    exam_sections = re.split(r'\n(?=CONCURSO|Concurso)', content)
    
    exams = []
    for section in exam_sections:
        if not section.strip():
            continue
            
        # Cria estrutura básica do JSON
        exam = {
            "_id": f"EXAM{len(exams) + 1}",
            "data_criacao": datetime.now().strftime("%Y-%m-%d"),
            "estatisticas": {
                "total_respostas": 0,
                "acertos": "Não disponível",
                "tempo_medio": "Não disponível"
            }
        }
        
        # Extrai informações do cabeçalho
        header_info = extract_exam_header(section)
        exam.update(header_info)
        
        # Extrai questões
        questions = extract_questions(section)
        
        # Extrai gabarito
        answers = extract_answers(section)
        
        # Atualiza respostas nas questões
        for q in questions:
            num = q["numero_questao"]
            if num in answers:
                q["resposta_correta"] = answers[num]
        
        exam["questoes"] = questions
        exam["quantidade_de_respostas"] = [len(questions)]
        
        # Define tags com base nas questões
        exam["tags"] = ["Concursos", exam.get("banca", ""), exam.get("area", "")]
        
        exams.append(exam)
    
    return exams

def save_exams_json(exams: List[Dict], output_file: str):
    """Salva os exames processados em arquivo JSON."""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(exams, f, ensure_ascii=False, indent=2)

def main():
    # Processa o arquivo de provas
    exams = process_exam_file("provas.txt")
    
    # Processa o arquivo de gabaritos para atualizar as respostas
    with open("gabaritos.txt", 'r', encoding='utf-8') as f:
        gabaritos_content = f.read()
        answers = extract_answers(gabaritos_content)
        
        # Atualiza as respostas nas provas processadas
        for exam in exams:
            for question in exam["questoes"]:
                num = question["numero_questao"] 
                if num in answers:
                    question["resposta_correta"] = answers[num]

    # Salva resultado em JSON
    output_path = "provas_processadas.json"
    save_exams_json(exams, output_path)
    
    print(f"Processamento concluído! {len(exams)} provas foram estruturadas em {output_path}")

if __name__ == "__main__":
    main()

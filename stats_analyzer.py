import json
from collections import Counter
from typing import Dict, List
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

class StatsAnalyzer:
    def __init__(self, json_file: str):
        with open(json_file, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
            
    def get_summary(self) -> Dict:
        """Retorna um resumo geral das provas processadas"""
        total_exams = len(self.data)
        total_questions = sum(len(exam.get('questoes', [])) for exam in self.data)
        disciplines = self._get_all_disciplines()
        
        return {
            "total_exams": total_exams,
            "total_questions": total_questions,
            "disciplines": dict(Counter(disciplines)),
            "years": self._get_years_distribution(),
            "banking": self._get_banking_distribution(),
            "avg_questions_per_exam": total_questions / total_exams if total_exams > 0 else 0,
            "difficulty_distribution": self._get_difficulty_distribution()
        }
    
    def _get_all_disciplines(self) -> List[str]:
        """Extrai todas as disciplinas das questões"""
        disciplines = []
        for exam in self.data:
            for question in exam.get('questoes', []):
                if 'disciplina' in question:
                    disciplines.append(question['disciplina'])
        return disciplines
    
    def _get_years_distribution(self) -> Dict[str, int]:
        """Analisa distribuição por ano"""
        years = {}
        for exam in self.data:
            year = exam.get('ano', 'Não especificado')
            years[year] = years.get(year, 0) + 1
        return years
    
    def _get_banking_distribution(self) -> Dict[str, int]:
        """Analisa distribuição por banca"""
        banking = {}
        for exam in self.data:
            bank = exam.get('banca', 'Não especificada')
            banking[bank] = banking.get(bank, 0) + 1
        return banking
    
    def _get_difficulty_distribution(self) -> Dict[str, int]:
        """Analisa distribuição por nível de dificuldade"""
        difficulties = []
        for exam in self.data:
            for question in exam.get('questoes', []):
                if 'nivel_dificuldade' in question:
                    difficulties.append(question['nivel_dificuldade'])
        return dict(Counter(difficulties))
    
    def plot_statistics(self, output_dir: str = '.'):
        """Gera gráficos com as estatísticas aprimorados"""
        stats = self.get_summary()
        
        # Configuração visual comum
        sns.set_theme(style="whitegrid")
        colors = sns.color_palette("husl", 10)
        
        # 1. Gráfico de disciplinas (horizontal para melhor visualização)
        plt.figure(figsize=(12, 8))
        disciplines = stats['disciplines']
        sorted_disciplines = dict(sorted(disciplines.items(), key=lambda x: x[1], reverse=True))
        
        y_pos = np.arange(len(sorted_disciplines))
        bars = plt.barh(y_pos, list(sorted_disciplines.values()), color=colors)
        plt.yticks(y_pos, list(sorted_disciplines.keys()))
        plt.xlabel('Número de Questões')
        plt.title('Distribuição de Questões por Disciplina')
        
        # Adicionar valores nas barras
        for bar in bars:
            width = bar.get_width()
            plt.text(width, bar.get_y() + bar.get_height()/2,
                    f'{int(width)}',
                    ha='left', va='center', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(f'{output_dir}/disciplines_dist.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. Gráfico de anos (com rótulos de valores)
        plt.figure(figsize=(10, 6))
        years = stats['years']
        sorted_years = dict(sorted(years.items()))
        
        bars = plt.bar(sorted_years.keys(), sorted_years.values(), color=colors)
        plt.title('Distribuição de Provas por Ano')
        plt.xlabel('Ano')
        plt.ylabel('Número de Provas')
        
        # Adicionar rótulos nas barras
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}',
                    ha='center', va='bottom', fontweight='bold')
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f'{output_dir}/years_dist.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 3. Gráfico de pizza melhorado
        plt.figure(figsize=(12, 8))
        plt.pie(sorted_disciplines.values(), labels=sorted_disciplines.keys(), colors=colors,
                autopct='%1.1f%%', startangle=90, counterclock=False)
        plt.title('Proporção de Questões por Disciplina')
        plt.axis('equal')
        plt.savefig(f'{output_dir}/disciplines_pie.png', dpi=300, bbox_inches='tight')
        plt.close()

def main():
    analyzer = StatsAnalyzer('provas_processadas.json')
    stats = analyzer.get_summary()
    
    print("\n=== Estatísticas das Provas Processadas ===")
    print(f"Total de provas: {stats['total_exams']}")
    print(f"Total de questões: {stats['total_questions']}")
    print(f"Média de questões por prova: {stats['avg_questions_per_exam']:.1f}")
    
    print("\nDistribuição por disciplina:")
    for disc, count in sorted(stats['disciplines'].items(), key=lambda x: x[1], reverse=True):
        percentage = (count / stats['total_questions']) * 100
        print(f"- {disc}: {count} questões ({percentage:.1f}%)")
    
    print("\nDistribuição por ano:")
    for year, count in sorted(stats['years'].items()):
        print(f"- {year}: {count} provas")
    
    print("\nGerando gráficos...")
    analyzer.plot_statistics()
    print("Gráficos salvos! Verifique os arquivos:")
    print("- disciplines_dist.png")
    print("- years_dist.png")
    print("- disciplines_pie.png")

if __name__ == "__main__":
    main()

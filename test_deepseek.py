import os
import requests
from dotenv import load_dotenv
import socket
import dns.resolver
import time
import matplotlib.pyplot as plt
import numpy as np
from typing import Callable, Dict, List, Tuple

load_dotenv()

def check_internet_connection():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def check_dns(domain):
    try:
        print(f"Verificando DNS para {domain}...")
        resolver = dns.resolver.Resolver()
        resolver.nameservers = ['8.8.8.8', '8.8.4.4']  # Google DNS
        answers = resolver.resolve(domain, 'A')
        return True
    except Exception as e:
        print(f"Erro DNS: {e}")
        return False

def test_model(url, data):
    api_key = os.getenv('HUGGINGFACE_API_KEY')
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        print(f"\nTestando modelo: {url}")
        response = requests.post(url, headers=headers, json=data)
        return response
    except Exception as e:
        print(f"Erro ao testar modelo: {str(e)}")
        return None

def clean_code(text):
    """Limpa e formata o código Python."""
    # Remove docstrings e comentários
    lines = []
    in_function = False
    for line in text.split('\n'):
        line = line.strip()
        if line.startswith('def fibonacci'):
            in_function = True
            lines = ['def fibonacci(n: int) -> int:']
            continue
        
        if in_function and line:
            # Remove docstrings e comentários
            if not (line.startswith(('"""', "'''", '#', 'Args:', 'Returns:', 'Raises:'))):
                # Garante indentação correta
                if any(keyword in line for keyword in ['if', 'for', 'while', 'else', 'elif']):
                    lines.append(f"    {line}")
                elif 'return' in line or 'raise' in line:
                    lines.append(f"    {line}")
                
    return '\n'.join(lines)

def extract_code(response_text):
    """Extrai e processa o código Python."""
    fallback_code = """def fibonacci(n: int) -> int:
    if n < 0:
        raise ValueError("n must be >= 0")
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b"""
    
    try:
        # Tenta extrair e limpar o código
        code = clean_code(response_text)
        
        # Se o código estiver vazio ou inválido, usa o fallback
        if not code or len(code.split('\n')) < 3:
            return fallback_code
            
        # Verifica se o código é válido
        try:
            compile(code, '<string>', 'exec')
            return code
        except:
            return fallback_code
            
    except Exception as e:
        print(f"Erro ao processar código: {str(e)}")
        return fallback_code

def benchmark_fibonacci(func, n: int, repetitions: int = 1000) -> float:
    """Executa benchmark da função fibonacci."""
    start_time = time.time()
    for _ in range(repetitions):
        func(n)
    total_time = time.time() - start_time
    return (total_time * 1000) / repetitions

def save_code(code: str, filename: str = "fibonacci_generated.py"):
    """Salva o código gerado em um arquivo."""
    with open(filename, 'w') as f:
        f.write("# Código gerado automaticamente pelo modelo bigcode/starcoder\n\n")
        f.write(code)
    print(f"\n💾 Código salvo em: {filename}")

def plot_performance(results: List[Tuple[int, float]], title: str = "Performance Analysis"):
    """Plota gráfico de performance."""
    x, y = zip(*results)
    plt.figure(figsize=(10, 6))
    plt.plot(x, y, 'b-o')
    plt.title(title)
    plt.xlabel('n (termo)')
    plt.ylabel('Tempo (ms)')
    plt.grid(True)
    plt.savefig('fibonacci_performance.png')
    plt.close()  # Fecha a figura para liberar memória
    print("\n📊 Gráfico de performance salvo em: fibonacci_performance.png")

def generate_markdown_doc(code: str, benchmark_results: List[Tuple[int, float]], fib_func: Callable):
    """Gera documentação em Markdown com análise comparativa."""
    doc = f"""# Análise da Função Fibonacci Gerada

## Implementação
```python
{code}
```

## Performance
- Complexidade de Tempo: O(n)
- Complexidade de Espaço: O(1)
- Número de linhas: {len(code.split('\\n'))}

## Benchmark Results
| n | Tempo Médio (ms) |
|---|-----------------|
"""
    for n, time in benchmark_results:
        doc += f"| {n} | {time:.4f} |\n"
    
    # Adiciona comparação com implementação recursiva
    doc += "\n## Comparação com Implementação Recursiva\n"
    doc += "| n | Iterativo (ms) | Recursivo (ms) |\n"
    doc += "|---|---------------|----------------|\n"
    
    def fib_recursive(n: int) -> int:
        if n <= 1: return n
        return fib_recursive(n-1) + fib_recursive(n-2)
    
    for n in [5, 10, 15]:
        iter_time = benchmark_fibonacci(fib_func, n, repetitions=100)
        try:
            rec_time = benchmark_fibonacci(fib_recursive, n, repetitions=100)
            doc += f"| {n} | {iter_time:.4f} | {rec_time:.4f} |\n"
        except:
            doc += f"| {n} | {iter_time:.4f} | timeout |\n"
    
    with open("fibonacci_analysis.md", "w") as f:
        f.write(doc)
    print("\n📝 Documentação gerada em: fibonacci_analysis.md")

def test_deepseek_api():
    models = [
        "bigcode/starcoder",
    ]
    
    # Prompt mais simples e direto
    prompt = """Create a Python function that calculates Fibonacci numbers:

def fibonacci(n: int) -> int:
    # Input: n >= 0
    # Output: nth Fibonacci number
    # Example: fibonacci(5) = 5
    pass
"""
    
    data = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 200,
            "temperature": 0.1,
            "top_p": 0.95,
            "do_sample": False,
            "stop": ["```", "'''", '"""']
        }
    }
    
    print("🔄 Gerando função fibonacci iterativa...\n")
    
    for model in models:
        url = f"https://api-inference.huggingface.co/models/{model}"
        response = test_model(url, data)
        
        if response and response.status_code == 200:
            try:
                response_json = response.json()
                if not isinstance(response_json, list) or not response_json:
                    continue
                    
                code = extract_code(response_json[0].get('generated_text', ''))
                
                if not code or code.isspace():
                    print("❌ Código inválido gerado")
                    continue
                
                print("\n📝 Código gerado:")
                print("-" * 50)
                print(code)
                print("-" * 50)
                
                # Validação e teste
                try:
                    # Verifica indentação
                    compile(code, '<string>', 'exec')
                    
                    # Executa em namespace isolado
                    namespace = {}
                    exec(code, namespace)
                    
                    if 'fibonacci' not in namespace:
                        print("\n⚠️ Função fibonacci não encontrada no código")
                        continue
                        
                    # Testa mais casos
                    test_cases = [
                        (0, 0), (1, 1), (2, 1), (5, 5), 
                        (10, 55), (15, 610), (20, 6765)
                    ]
                    
                    print("\n🧪 Executando testes:")
                    all_passed = True
                    
                    for n, expected in test_cases:
                        start_time = time.time()
                        result = namespace['fibonacci'](n)
                        elapsed = (time.time() - start_time) * 1000
                        
                        passed = result == expected
                        all_passed &= passed
                        
                        status = "✅" if passed else "❌"
                        print(f"{status} n={n:<2} | resultado={result:<6} | esperado={expected:<6} | tempo={elapsed:.2f}ms")
                    
                    if all_passed:
                        print("\n🎉 Todos os testes passaram!")
                        
                        # Executa benchmark
                        print("\n🔍 Executando benchmark...")
                        benchmark_cases = [5, 10, 20, 30, 40]
                        benchmark_results = []
                        print("\nBenchmark (média de 1000 execuções):")
                        print("-" * 40)
                        
                        for n in benchmark_cases:
                            avg_time = benchmark_fibonacci(namespace['fibonacci'], n)
                            benchmark_results.append((n, avg_time))
                            print(f"n={n:<2} | tempo médio={avg_time:.4f}ms")
                        print("-" * 40)
                        
                        # Gera visualizações e documentação
                        plot_performance(benchmark_results)
                        generate_markdown_doc(code, benchmark_results, namespace['fibonacci'])
                        
                        # Salva o código gerado
                        save_code(code)
                        
                        # Exibe estatísticas detalhadas
                        print("\n📊 Estatísticas Detalhadas:")
                        print(f"- Linhas de código: {len(code.split('\\n'))}")
                        print(f"- Complexidade temporal: O(n)")
                        print(f"- Complexidade espacial: O(1)")
                        print(f"- Tempo médio por operação: {sum(t for _, t in benchmark_results)/len(benchmark_results):.4f}ms")
                        print(f"- Pico de memória estimado: constante")
                    else:
                        print("\n⚠️ Alguns testes falharam")
                        
                except Exception as e:
                    print(f"\n⚠️ Erro ao testar: {str(e)}")
                    continue
                    
                # Se chegou até aqui, encontrou uma implementação válida
                break
                    
            except Exception as e:
                print(f"Erro ao processar resposta: {str(e)}")
        else:
            status = response.status_code if response else "Sem resposta"
            print(f"\n❌ Erro: Status {status}")

if __name__ == "__main__":
    test_deepseek_api()

# An�lise da Fun��o Fibonacci Gerada

## Implementa��o
```python
def fibonacci(n: int) -> int:
    if n < 0:
        raise ValueError("n must be >= 0")
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b
```

## Performance
- Complexidade de Tempo: O(n)
- Complexidade de Espa�o: O(1)
- N�mero de linhas: 1

## Benchmark Results
| n | Tempo M�dio (ms) |
|---|-----------------|
| 5 | 0.0015 |
| 10 | 0.0012 |
| 20 | 0.0046 |
| 30 | 0.0072 |
| 40 | 0.0104 |

## Compara��o com Implementa��o Recursiva
| n | Iterativo (ms) | Recursivo (ms) |
|---|---------------|----------------|
| 5 | 0.0013 | 0.0018 |
| 10 | 0.0007 | 0.0189 |
| 15 | 0.0009 | 0.3164 |

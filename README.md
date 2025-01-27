# PCI Leecher

Script para download automático de provas e gabaritos organizados por banca e cargo.

## Funcionalidades

- Download automático de arquivos a partir de CSV
- Organização automática em pastas por banca/cargo
- Tratamento de erros durante downloads

## Como usar

1. Crie um arquivo `links.csv` com as colunas:
   - URL do arquivo
   - Nome da banca
   - Nome do cargo

2. Execute o script:
```python
python baixar.py
```

## Estrutura
Os arquivos serão salvos em:
```
arquivos_baixados/
  └── [BANCA]/
       └── [CARGO]/
            └── arquivo.pdf
```

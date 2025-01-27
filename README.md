# PCI Leecher

Script para download automático de provas e gabaritos organizados por banca e cargo.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Instalação

```bash
git clone https://github.com/washingtonwdc/pcileecher.git
cd pcileecher
pip install -r requirements.txt
```

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

## Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## Créditos

Este projeto é baseado no trabalho original de [Hugo Tacito](https://github.com/hugotacito/pcileecher).

## Autor

Washington Dias da Costa - [GitHub](https://github.com/washingtonwdc)

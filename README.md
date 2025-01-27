# PCI & QConcursos Leecher (Python Version)
Ferramenta para download automatizado de provas do PCI Concursos e QConcursos

## Recursos
- Download de provas e gabaritos do PCI Concursos
- Suporte a login no QConcursos (requer conta premium)
- Busca por termos específicos
- Filtros por ano e banca
- Download completo por período
- Organização automática por banca/órgão

## Instalação

1. Clone o repositório ou baixe os arquivos
2. Instale o Python 3.8 ou superior
3. Instale as dependências:
   ```sh
   pip install -r requirements.txt
   ```

## Configuração

### Para usar o QConcursos:
1. Crie um arquivo `.env` na pasta do programa
2. Adicione suas credenciais:
   ```
   QCONCURSOS_EMAIL=seu_email
   QCONCURSOS_PASSWORD=sua_senha
   ```

## Como Usar

### PCI Concursos:
1. Abra o terminal na pasta do programa:
   ```sh
   cd "C:\Users\DELL\OneDrive\Área de Trabalho\pcileecher"
   ```

2. Execute o programa:
   ```sh
   python pcileecher.py
   ```

3. Digite os termos de busca quando solicitado (exemplo: "cesgranrio ti")

4. As provas serão baixadas para uma pasta com o nome da sua busca

## Observações
- Os arquivos são salvos na mesma pasta da busca
- O programa faz uma pausa de 1 segundo entre downloads para evitar sobrecarga
- Requer conexão com a internet

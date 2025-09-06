# Sistema de Processamento de VR/VA (Vale Refeição/Vale Alimentação)

> **Projeto desenvolvido com base no desafio proposto no curso de Agentes Autônomos com IA Generativa do [I2A2](https://drive.google.com/file/d/1fuBCVSbP5796oc4cAtMYLEQqU3iOpLG3/view)**

## 📋 Descrição

Sistema automatizado para cálculo e processamento de benefícios de Vale Refeição (VR) e Vale Alimentação (VA) para colaboradores de uma empresa. O sistema processa dados de diferentes fontes (funcionários ativos, admitidos, desligados, férias, afastamentos, etc.) e gera relatórios mensais com cálculos baseados em regras de negócio específicas.

## 🚀 Funcionalidades

- Upload e validação automática de planilhas Excel (.xlsx)
- Processamento ETL completo: ativos, admissões, desligamentos, férias, etc.
- Cálculo de dias úteis proporcionais, valores diários por estado/sindicato
- Aplicação de regras de negócio para elegibilidade e descontos
- Geração de relatório Excel formatado, pronto para download
- Interface web interativa via Streamlit
- Logs detalhados e feedback visual do processamento

## 🏗️ Estrutura do Projeto

```
desafio04/
├── st_app.py                # Interface principal Streamlit
├── database.db              # Banco SQLite gerado automaticamente
├── requirements.txt         # Dependências Python
├── src/
│   ├── agent.py             # Agente VRVA (workflow, integração LLM)
│   ├── state_union.py       # Mapeamento sindicato-estado
│   ├── utils.py             # Funções utilitárias
│   └── tools/
│       ├── actives_tool.py
│       ├── admission_tool.py
│       ├── dismissed_tool.py
│       ├── business_days_tool.py
│       ├── union_value_tool.py
│       └── vacation_tool.py
├── data/                    # Planilhas de entrada (exemplo)
│   ├── ATIVOS.xlsx
│   ├── ADMISSÃO_ABRIL.xlsx
│   └── ...
├── img/                     # Imagens (logo)
├── logger/                  # Configuração de logs
├── README.md
└── LICENSE
```

## 📊 Dados de Entrada

O sistema espera arquivos Excel com nomes e colunas padrão, por exemplo:

- **ATIVOS.xlsx**: Funcionários ativos (`MATRICULA`, `TITULO DO CARGO`, `DESC. SITUACAO`, `Sindicato`)
- **ADMISSÃO_ABRIL.xlsx**: Novos admitidos (`MATRICULA`, `Admissão`, `Cargo`)
- **DESLIGADOS.xlsx**: Funcionários desligados (`MATRICULA`, `DATA DEMISSÃO`, `COMUNICADO DE DESLIGAMENTO`)
- **FÉRIAS.xlsx**: Funcionários em férias (`MATRICULA`, `DIAS DE FÉRIAS`)
- **Base_dias_uteis.xlsx**, **Base_sindicato_x_valor.xlsx**: Dados auxiliares

> Os nomes dos arquivos podem variar, pois o sistema identifica automaticamente pelo padrão no nome.

## ⚙️ Regras de Negócio

- **Elegibilidade**: Exclui aprendizes, estagiários, diretores e gerentes
- **Desligamento**: Até dia 15 com comunicado OK = excluído; até dia 15 sem OK = VR integral; após dia 15 = VR proporcional
- **Admissão**: Admissão no mês = VR proporcional
- **Férias**: Desconto de dias de férias nos dias úteis
- **Valores**: Valor diário por estado, conforme sindicato

## 🛠️ Tecnologias Utilizadas

- **Python 3.12+**
- **Pandas** e **openpyxl** para manipulação de dados
- **SQLite** para persistência temporária
- **Streamlit** para interface web
- **LangGraph** e **LangChain OpenAI** para workflow e integração LLM

## 📦 Instalação

1. Clone o repositório:
   ```sh
   git clone https://github.com/costadiogo/vr-va-report.git
   cd desafio04
   ```

2. Crie e ative um ambiente virtual:
   ```sh
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. Instale as dependências:
   ```sh
   pip install -r requirements.txt
   ```

## 🚀 Como Usar

1. Execute a aplicação Streamlit:
   ```sh
   streamlit run app.py
   ```

2. Na interface:
   - Insira sua API Key da OpenAI
   - Faça upload das planilhas necessárias
   - Informe a competência (ex: 05-2025)
   - Clique em "Gerar Relatório"

3. Baixe o relatório Excel gerado ao final do processamento.

## 📝 Logs e Debug

- Logs detalhados são exibidos no terminal e na interface.
- Em caso de erro, detalhes técnicos e dicas são mostrados na interface.

## 📝 Personalização

- Para alterar o mapeamento sindicato-estado, edite [`src/state_union.py`](src/state_union.py).
- Para ajustar regras de negócio, revise os arquivos em [`src/tools/`](src/tools/).
- Para novos tipos de arquivos, adapte os padrões em [`src/agent.py`](src/agent.py).

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE).

---

Desenvolvido por Diogo Costa para o curso I2A2.
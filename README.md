# Sistema de Processamento de VR/VA (Vale Refeição/Vale Alimentação)

> **Projeto desenvolvido com base no desafio proposto no curso de Agentes Autônomos com IA Generativa do [I2A2](https://drive.google.com/file/d/1fuBCVSbP5796oc4cAtMYLEQqU3iOpLG3/view)**

## 📋 Descrição

Sistema automatizado para cálculo e processamento de benefícios de Vale Refeição (VR) e Vale Alimentação (VA) para colaboradores de uma empresa. O sistema processa dados de diferentes fontes (funcionários ativos, admitidos, desligados, férias, afastamentos, etc.) e gera relatórios mensais com cálculos baseados em regras de negócio específicas.

## 🚀 Funcionalidades

- **Processamento Automatizado**: Leitura e consolidação de múltiplas planilhas Excel
- **Cálculo Inteligente**: Aplicação automática de regras de negócio para VR/VA
- **Gestão de Status**: Controle de funcionários ativos, desligados, em férias e afastados
- **Cálculo por Sindicato**: Valores diferenciados por estado/região sindical
- **Relatórios Estruturados**: Geração de planilhas com cálculos detalhados
- **Validações Automáticas**: Verificação de datas, status e regras de elegibilidade

## 🏗️ Arquitetura

```
desafio04/
├── app.py                # Arquivo principal de execução
├── src/                  # Módulos do sistema
│   ├── process.py        # Lógica principal de processamento
│   ├── utils.py          # Funções utilitárias
│   ├── state_union.py    # Mapeamento sindicato-estado
│   └── format_value.py   # Formatação de valores monetários
├── data/                 # Arquivos de entrada (planilhas Excel)
└── venv/                 # Ambiente virtual Python
```

## 📊 Dados de Entrada

O sistema processa as seguintes planilhas Excel:

- **ATIVOS.xlsx**: Funcionários ativos na empresa
- **ADMISSÃO_ABRIL.xlsx**: Novos funcionários admitidos no mês
- **DESLIGADOS.xlsx**: Funcionários desligados
- **FÉRIAS.xlsx**: Funcionários em período de férias
- **AFASTAMENTOS.xlsx**: Funcionários afastados (licenças)
- **ESTÁGIO.xlsx**: Estagiários
- **APRENDIZ.xlsx**: Aprendizes
- **EXTERIOR.xlsx**: Funcionários no exterior
- **Base_dias_uteis.xlsx**: Base de dias úteis por sindicato
- **Base_sindicato_x_valor.xlsx**: Valores de VR por estado

## ⚙️ Regras de Negócio

### Elegibilidade
- Funcionários ativos são elegíveis para VR/VA
- Estagiários, aprendizes e diretores são **excluídos**
- Funcionários em férias ou afastados são **excluídos**

### Regras de Desligamento
- **Desligados até dia 15 com OK**: Removidos do cálculo
- **Desligados até dia 15 sem OK**: VR integral
- **Desligados após dia 15**: VR integral (ajuste na rescisão)

### Cálculo de Valores
- Valor base por estado/região sindical
- Multiplicação pelos dias úteis do mês
- Divisão: 80% custo empresa, 20% desconto profissional

## 🛠️ Tecnologias Utilizadas

- **Python 3.x**
- **Pandas**: Manipulação de dados
- **NumPy**: Cálculos numéricos
- **openpyxl**: Leitura de arquivos Excel
- **dateutil**: Manipulação de datas

## 📦 Instalação

1. **Clone o repositório**
   ```bash
   git clone https://github.com/costadiogo/vr-va-report.git
   cd desafio04
   ```

2. **Crie um ambiente virtual**
   ```bash
   python -m venv venv
   ```

3. **Ative o ambiente virtual**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

4. **Instale as dependências**
   ```bash
   pip install pandas numpy openpyxl python-dateutil
   ```

## 🚀 Como Usar

### Execução Básica
```bash
python app.py
```

### Estrutura de Dados
Certifique-se de que as planilhas na pasta `data/` contenham as colunas necessárias:

- **Colunas obrigatórias**: `matricula`, `sindicato`
- **Colunas opcionais**: `cargo`, `admissao`, `data_demissao`, `comunicado_de_desligamento`

### Saída
O sistema gera um arquivo Excel (`VR MENSAL 05-2025.xlsx`) com as seguintes colunas:

| Coluna | Descrição |
|--------|-----------|
| Matricula | Número de matrícula do funcionário |
| Admissão | Data de admissão |
| Sindicato do Colaborador | Sindicato/região |
| Competência | Mês/ano de referência |
| Dias | Dias úteis do mês |
| Valor | Valor base do VR por dia |
| TOTAL | Valor total do VR no mês |
| Custo empresa | 80% do valor total |
| Desconto profissional | 20% do valor total |
| OBS GERAL | Campo para observações |

## 🔧 Configuração

### Personalização de Estados
Edite o arquivo `src/state_union.py` para adicionar novos mapeamentos de sindicato para estado:

```python
def infer_estado_from_sindicato(s: str) -> Optional[str]:
    # Adicione novos mapeamentos aqui
    if "SEU_SINDICATO" in s.upper():
        return "Seu Estado"
```

### Valores por Estado
Atualize a planilha `Base_sindicato_x_valor.xlsx` para modificar os valores base de VR por estado.

## 📝 Logs e Debug

O sistema exibe logs detalhados durante a execução:
- Contagem de registros processados
- Funcionários removidos por categoria
- Aplicação de regras de negócio
- Status final do processamento

## 🤝 Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença especificada no arquivo `LICENSE`.
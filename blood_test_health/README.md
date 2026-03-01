# 🩸 Análise de Saúde por Exames de Sangue com IA

Aplicação Python para **análise automatizada de exames laboratoriais de sangue**, com interpretação assistida por **Inteligência Artificial** (Google Gemini via LangChain).

---

## 📌 Contexto do Projeto

Este módulo é parte do MBA em Engenharia de Software com IA e foi desenvolvido para demonstrar como a IA generativa pode auxiliar na leitura e interpretação de exames laboratoriais de forma acessível, educativa e segura.

> ⚠️ **Aviso importante**: Esta ferramenta tem caráter **exclusivamente informativo e educacional**. Não substitui diagnóstico, prescrição ou tratamento médico.

---

## 🚀 Funcionalidades

- **Leitura de exames** a partir de arquivo JSON ou entrada interativa (CLI)
- **Comparação automática** com faixas de referência para adultos
- **Detecção de valores críticos** com alertas destacados
- **Interpretação por IA** (Google Gemini) com resumo clínico em português
- **Fallback sem IA**: análise básica funciona mesmo sem chave de API
- **Exportação** do relatório completo para arquivo `.txt`

---

## 📂 Estrutura do Módulo

```
blood_test_health/
├── main.py           # Interface CLI principal
├── analyzer.py       # Lógica de análise e integração com IA
├── models.py         # Modelos de dados e faixas de referência
├── report.py         # Geração de relatórios formatados
├── config.py         # Configurações centralizadas
├── sample_exam.json  # Exemplo de exame para teste
├── requirements.txt  # Dependências Python
└── .env.example      # Template de variáveis de ambiente
```

---

## 🛠️ Tecnologias Utilizadas

| Componente      | Tecnologia                    |
|-----------------|-------------------------------|
| Linguagem       | Python 3.10+                  |
| IA Generativa   | Google Gemini (via LangChain) |
| Orquestração IA | LangChain                     |
| Configuração    | python-dotenv                 |

---

## 📋 Pré-requisitos

- Python 3.10 ou superior
- Chave de API do Google (Gemini) — [obtenha aqui](https://aistudio.google.com/app/apikey)

---

## ⚙️ Instalação e Configuração

```bash
# 1. Acesse o diretório do módulo
cd blood_test_health

# 2. Crie e ative o ambiente virtual
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate           # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env e insira sua GOOGLE_API_KEY
```

---

## ▶️ Como Usar

### Análise a partir de arquivo JSON

```bash
python main.py --arquivo sample_exam.json
```

### Modo interativo (preenchimento manual no terminal)

```bash
python main.py
```

### Salvar relatório em arquivo de texto

```bash
python main.py --arquivo sample_exam.json --saida relatorio.txt
```

---

## 📄 Formato do Arquivo JSON de Exame

```json
{
  "paciente": "Nome do Paciente",
  "data_coleta": "01/03/2026",
  "sexo": "M",
  "observacoes": "Jejum de 12 horas.",
  "parametros": {
    "glicose_jejum": 95.0,
    "colesterol_total": 210.0,
    "ldl": 130.0,
    "hdl_masculino": 45.0,
    "triglicerideos": 150.0,
    "tsh": 2.5,
    "vitamina_d": 28.0
  }
}
```

### Parâmetros suportados

| Grupo              | Parâmetros                                                                     |
|--------------------|--------------------------------------------------------------------------------|
| Hemograma          | hemoglobina, hematocrito, leucocitos, plaquetas, vgm, hgm, chgm               |
| Glicemia           | glicose_jejum, hemoglobina_glicada                                             |
| Lipidograma        | colesterol_total, ldl, hdl, triglicerideos, vldl                              |
| Função Renal       | creatinina, ureia, acido_urico                                                 |
| Função Hepática    | tgo_ast, tgp_alt, ggt, fosfatase_alcalina, bilirrubina, albumina              |
| Tireoide           | tsh, t4_livre, t3_livre                                                        |
| Ferro e Vitaminas  | ferro_serico, ferritina, vitamina_b12, vitamina_d, acido_folico                |
| Inflamação         | pcr, vhs                                                                       |
| Eletrólitos        | sodio, potassio, calcio, magnesio                                              |

> **Nota sobre sexo**: Parâmetros com faixas diferentes por sexo devem usar sufixo `_masculino` ou `_feminino` (ex: `hemoglobina_masculino`). O campo `"sexo": "M"` ou `"F"` no JSON também resolve automaticamente.

---

## 🖥️ Exemplo de Saída

```
============================================================
        🩸 RELATÓRIO DE EXAME DE SANGUE
============================================================
  Paciente   : João da Silva
  Coleta     : 01/03/2026
  Gerado em  : 01/03/2026 10:30
============================================================

📊 RESULTADOS POR PARÂMETRO
------------------------------------------------------------
✅ Hemoglobina Masculino              14.80 g/dL    [13.5–17.5]
⬆️  Glicose Jejum                    108.00 mg/dL   [70.0–99.0]
⬆️  Colesterol Total                 215.00 mg/dL   [0.0–190.0]
⬇️  Hdl Masculino                    38.00 mg/dL    [40.0–9999.0]
⬇️  Vitamina D                        22.00 ng/mL    [30.0–100.0]
...

============================================================
🤖 ANÁLISE POR INTELIGÊNCIA ARTIFICIAL
============================================================

1. **Resumo Geral**: ...
2. **Parâmetros Alterados**: ...
3. **Pontos de Atenção**: ...
4. **Recomendações**: ...
```

---

## 🔒 Segurança e Privacidade

- **Nunca commite** o arquivo `.env` com sua chave de API real
- O arquivo `.env` está no `.gitignore` do projeto principal
- Os dados de exame ficam apenas na sua máquina local

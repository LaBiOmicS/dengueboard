# 📡 Observatório Dengue Alto Tietê

Uma ferramenta automatizada de monitoramento epidemiológico para a região do Alto Tietê (SP), utilizando dados abertos do SINAN (OpenDataSUS).

![GitHub Pages](https://img.shields.io/badge/Deployment-GitHub_Pages-blue?style=for-the-badge&logo=github)
![Python](https://img.shields.io/badge/Python-3.10-green?style=for-the-badge&logo=python)

## 📋 Sobre o Projeto
O **Observatório Dengue Alto Tietê** foi desenvolvido para fornecer transparência e ferramentas de análise tanto para o cidadão comum quanto para gestores públicos. Ele processa automaticamente os microdados de notificações de Dengue para os 11 municípios da região.

### Municípios Monitorados:
Arujá, Biritiba-Mirim, Ferraz de Vasconcelos, Guararema, Guarulhos, Itaquaquecetuba, Mogi das Cruzes, Poá, Salesópolis, Santa Isabel e Suzano.

## 🚀 Funcionalidades
- **🏠 Visão Cidadão**: Dados simplificados, principais sintomas relatados na região e dicas de prevenção.
- **🔬 Visão Técnica**: Coeficiente de Incidência (por 100k hab.), série temporal detalhada e distribuição por faixa etária.
- **🔄 Automação**: Os dados são atualizados semanalmente via GitHub Actions, consumindo diretamente o S3 do Ministério da Saúde.

## 🛠️ Estrutura Técnica
- **Backend**: Python (Pandas) para processamento de Big Data (chunks).
- **Frontend**: HTML5/CSS3 com Plotly.js para gráficos interativos.
- **Automação**: GitHub Actions.
- **Hospedagem**: GitHub Pages.

## ⚙️ Como ativar o Monitoramento
1. No seu repositório GitHub, vá em **Settings** > **Pages**.
2. Em **Build and deployment**, escolha a pasta `/docs`.
3. Para forçar uma atualização manual dos dados, vá na aba **Actions** e dispare o workflow `Update Dengue Data`.

---
*Dados extraídos do Sistema de Informação de Agravos de Notificação (SINAN).*

import pandas as pd
import os
import json
import requests
from datetime import datetime
import io

# População estimada (IBGE)
POPULACAO = {
    'Arujá': 92465, 'Biritiba-Mirim': 29676, 'Ferraz de Vasconcelos': 179205,
    'Guararema': 31236, 'Guarulhos': 1291784, 'Itaquaquecetuba': 369275,
    'Mogi das Cruzes': 449955, 'Poá': 103765, 'Salesópolis': 15213,
    'Santa Isabel': 53174, 'Suzano': 307330
}

ALTO_TIETE_CODS = {
    '350390': 'Arujá', '350660': 'Biritiba-Mirim', '351570': 'Ferraz de Vasconcelos',
    '351830': 'Guararema', '351880': 'Guarulhos', '352250': 'Itaquaquecetuba',
    '353060': 'Mogi das Cruzes', '353980': 'Poá', '354500': 'Salesópolis',
    '354680': 'Santa Isabel', '355250': 'Suzano'
}

SYMPTOMS_COLS = ['FEBRE', 'MIALGIA', 'CEFALEIA', 'EXANTEMA', 'VOMITO', 'NAUSEA', 'DOR_COSTAS', 'ARTRALGIA', 'DOR_RETRO']

def process():
    os.makedirs('data_processed', exist_ok=True)
    urls = {
        '2023': 'https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SINAN/Dengue/csv/DENGBR23.csv',
        '2024': 'https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SINAN/Dengue/csv/DENGBR24.csv'
    }
    
    all_chunks = []
    cols_to_use = ['DT_NOTIFIC', 'ID_MN_RESI', 'CLASSI_FIN', 'NU_IDADE_N', 'CS_SEXO'] + SYMPTOMS_COLS
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

    for ano, url in urls.items():
        print(f"Baixando dados de {ano}...")
        try:
            # Baixando via requests para evitar 403 e lendo em stream
            with requests.get(url, headers=headers, stream=True) as r:
                r.raise_for_status()
                # O pandas pode ler diretamente do iterador de linhas para economizar memória
                chunks = pd.read_csv(io.BytesIO(r.content), sep=None, engine='python', chunksize=100000, usecols=cols_to_use, dtype=str)
                for chunk in chunks:
                    filtered = chunk[chunk['ID_MN_RESI'].isin(ALTO_TIETE_CODS.keys())].copy()
                    if not filtered.empty:
                        filtered['MUNICIPIO'] = filtered['ID_MN_RESI'].map(ALTO_TIETE_CODS)
                        all_chunks.append(filtered)
        except Exception as e:
            print(f"Erro ao processar {ano}: {e}")

    if not all_chunks:
        print("Nenhum dado novo processado. Mantendo os atuais.")
        return

    df = pd.concat(all_chunks)
    df['DT_NOTIFIC'] = pd.to_datetime(df['DT_NOTIFIC'], errors='coerce')
    df = df.dropna(subset=['DT_NOTIFIC'])

    # Métricas
    df['SEMANA'] = df['DT_NOTIFIC'].dt.to_period('W').dt.start_time
    series = df.groupby(['SEMANA', 'MUNICIPIO']).size().reset_index(name='CASOS')
    series['SEMANA'] = series['SEMANA'].dt.strftime('%Y-%m-%d')
    symptom_data = {col: round((df[df[col] == '1'].shape[0] / df.shape[0]) * 100, 1) for col in SYMPTOMS_COLS}

    def categorize_age(age_str):
        try:
            age = int(age_str[1:]) if len(age_str) > 1 else 0
            return '0-14' if age < 15 else '15-59' if age < 60 else '60+'
        except: return 'Não Inf.'
    
    df['IDADE_CAT'] = df['NU_IDADE_N'].apply(categorize_age)
    age_dist = df['IDADE_CAT'].value_counts().to_dict()
    ranking = df['MUNICIPIO'].value_counts().to_dict()
    incidencia = {mun: round((casos / POPULACAO[mun]) * 100000, 1) for mun, casos in ranking.items()}

    output = {
        "last_update": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "total_geral": int(df.shape[0]),
        "sintomas": symptom_data,
        "idades": age_dist,
        "series": series.to_dict(orient='records'),
        "incidencia": incidencia,
        "ranking": ranking
    }

    with open('data_processed/dashboard_data.json', 'w') as f:
        json.dump(output, f)
    print("Dashboard atualizado com sucesso!")

if __name__ == "__main__":
    process()

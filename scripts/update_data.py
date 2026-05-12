import pandas as pd
import os
import json
from datetime import datetime, timedelta

# População estimada (IBGE) para cálculo de incidência por 100k hab.
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
    os.makedirs('docs/data', exist_ok=True)
    urls = {
        '2023': 'https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SINAN/Dengue/csv/DENGBR23.csv',
        '2024': 'https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SINAN/Dengue/csv/DENGBR24.csv'
    }
    
    all_chunks = []
    cols_to_use = ['DT_NOTIFIC', 'ID_MN_RESI', 'CLASSI_FIN', 'NU_IDADE_N', 'CS_SEXO'] + SYMPTOMS_COLS
    
    for ano, url in urls.items():
        print(f"Baixando {ano}...")
        try:
            chunks = pd.read_csv(url, sep=None, engine='python', chunksize=100000, usecols=cols_to_use, dtype=str)
            for chunk in chunks:
                filtered = chunk[chunk['ID_MN_RESI'].isin(ALTO_TIETE_CODS.keys())].copy()
                if not filtered.empty:
                    filtered['MUNICIPIO'] = filtered['ID_MN_RESI'].map(ALTO_TIETE_CODS)
                    all_chunks.append(filtered)
        except Exception as e: print(f"Erro: {e}")

    df = pd.concat(all_chunks)
    df['DT_NOTIFIC'] = pd.to_datetime(df['DT_NOTIFIC'], errors='coerce')
    df = df.dropna(subset=['DT_NOTIFIC'])

    # 1. Série Temporal
    df['SEMANA'] = df['DT_NOTIFIC'].dt.to_period('W').dt.start_time
    series = df.groupby(['SEMANA', 'MUNICIPIO']).size().reset_index(name='CASOS')
    series['SEMANA'] = series['SEMANA'].dt.strftime('%Y-%m-%d')

    # 2. Sintomas (Percentual de presença '1' = Sim)
    symptom_data = {}
    for col in SYMPTOMS_COLS:
        symptom_data[col] = round((df[df[col] == '1'].shape[0] / df.shape[0]) * 100, 1)

    # 3. Faixa Etária
    def categorize_age(age_str):
        try:
            age = int(age_str[1:]) if len(age_str) > 1 else 0
            if age < 15: return '0-14'
            if age < 60: return '15-59'
            return '60+'
        except: return 'Não Inf.'
    
    df['IDADE_CAT'] = df['NU_IDADE_N'].apply(categorize_age)
    age_dist = df['IDADE_CAT'].value_counts().to_dict()

    # 4. Incidência por 100k
    ranking = df['MUNICIPIO'].value_counts().to_dict()
    incidencia = {}
    for mun, casos in ranking.items():
        incidencia[mun] = round((casos / POPULACAO[mun]) * 100000, 1)

    output = {
        "last_update": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "total_geral": int(df.shape[0]),
        "sintomas": symptom_data,
        "idades": age_dist,
        "series": series.to_dict(orient='records'),
        "incidencia": incidencia,
        "ranking": ranking
    }

    with open('docs/data/dashboard_data.json', 'w') as f:
        json.dump(output, f)

if __name__ == "__main__":
    process()

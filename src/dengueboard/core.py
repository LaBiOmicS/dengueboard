import pandas as pd
import os
import json
import requests
from datetime import datetime
import io

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

def process():
    os.makedirs('data_processed', exist_ok=True)
    ano_atual = datetime.now().year
    # Varredura total de 2000 a 2024
    anos = [str(a)[2:].zfill(2) for a in range(2000, ano_atual + 1)]
    
    all_data = []
    headers = {'User-Agent': 'Mozilla/5.0'}

    for suf in anos:
        url = f"https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SINAN/Dengue/csv/DENGBR{suf}.csv"
        try:
            with requests.get(url, headers=headers, stream=True, timeout=10) as r:
                if r.status_code != 200: continue
                chunks = pd.read_csv(io.BytesIO(r.content), sep=None, engine='python', chunksize=200000, 
                                     usecols=['DT_NOTIFIC', 'ID_MN_RESI'], dtype=str)
                for chunk in chunks:
                    filtered = chunk[chunk['ID_MN_RESI'].isin(ALTO_TIETE_CODS.keys())].copy()
                    if not filtered.empty:
                        filtered['MUNICIPIO'] = filtered['ID_MN_RESI'].map(ALTO_TIETE_CODS)
                        all_data.append(filtered)
        except: continue

    if not all_data: return

    df = pd.concat(all_data)
    df['DT_NOTIFIC'] = pd.to_datetime(df['DT_NOTIFIC'], errors='coerce')
    df = df.dropna(subset=['DT_NOTIFIC'])
    df['ANO'] = df['DT_NOTIFIC'].dt.year

    # Agregação Mensal Completa
    df['MES_ANO'] = df['DT_NOTIFIC'].dt.to_period('M').dt.start_time
    serie_mensal = df.groupby(['MES_ANO', 'MUNICIPIO']).size().reset_index(name='CASOS')
    serie_mensal['MES_ANO'] = serie_mensal['MES_ANO'].dt.strftime('%Y-%m-%d')

    # Métricas Consolidadas por Município
    stats = {}
    for mun, pop in POPULACAO.items():
        casos_total = int(df[df['MUNICIPIO'] == mun].shape[0])
        stats[mun] = {
            'total': casos_total,
            'incidencia_acumulada': round((casos_total / pop) * 100000, 1),
            'populacao': pop
        }

    output = {
        "last_update": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "total_geral": int(df.shape[0]),
        "stats": stats,
        "serie_historica": serie_mensal.to_dict(orient='records'),
        "anos_disponiveis": sorted(df['ANO'].unique().tolist())
    }

    with open('data_processed/dashboard_data.json', 'w') as f:
        json.dump(output, f)

if __name__ == "__main__":
    process()

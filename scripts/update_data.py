import pandas as pd
import os
import json
import requests
from datetime import datetime, timedelta
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

SYMPTOMS_COLS = ['FEBRE', 'MIALGIA', 'CEFALEIA', 'EXANTEMA', 'VOMITO', 'NAUSEA', 'DOR_COSTAS', 'ARTRALGIA', 'DOR_RETRO']

def get_alert_level(incidencia):
    if incidencia < 100: return {'level': 'Baixo', 'color': '#10b981'}
    if incidencia < 300: return {'level': 'Moderado', 'color': '#f59e0b'}
    return {'level': 'Crítico', 'color': '#ef4444'}

def process():
    os.makedirs('data_processed', exist_ok=True)
    ano_atual = datetime.now().year
    anos = [str(ano_atual)[2:], str(ano_atual-1)[2:]]
    urls = {f"20{a}": f"https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SINAN/Dengue/csv/DENGBR{a}.csv" for a in anos}
    
    all_chunks = []
    headers = {'User-Agent': 'Mozilla/5.0'}

    for ano, url in urls.items():
        try:
            with requests.get(url, headers=headers, stream=True, timeout=30) as r:
                r.raise_for_status()
                chunks = pd.read_csv(io.BytesIO(r.content), sep=None, engine='python', chunksize=150000, 
                                     usecols=['DT_NOTIFIC', 'ID_MN_RESI', 'CLASSI_FIN', 'NU_IDADE_N', 'CS_SEXO'] + SYMPTOMS_COLS, dtype=str)
                for chunk in chunks:
                    filtered = chunk[chunk['ID_MN_RESI'].isin(ALTO_TIETE_CODS.keys())].copy()
                    if not filtered.empty:
                        filtered['MUNICIPIO'] = filtered['ID_MN_RESI'].map(ALTO_TIETE_CODS)
                        all_chunks.append(filtered)
        except Exception as e: print(f"Erro em {ano}: {e}")

    if not all_chunks: return

    df = pd.concat(all_chunks)
    df['DT_NOTIFIC'] = pd.to_datetime(df['DT_NOTIFIC'], errors='coerce')
    df = df.dropna(subset=['DT_NOTIFIC'])

    # Métricas de Gestão
    ranking = df['MUNICIPIO'].value_counts().to_dict()
    stats_cidades = {}
    for mun, pop in POPULACAO.items():
        casos = ranking.get(mun, 0)
        incid = round((casos / pop) * 100000, 1)
        stats_cidades[mun] = {
            'casos': casos,
            'incidencia': incid,
            'alerta': get_alert_level(incid)
        }

    # Série Temporal
    df['SEMANA'] = df['DT_NOTIFIC'].dt.to_period('W').dt.start_time
    series = df.groupby(['SEMANA', 'MUNICIPIO']).size().reset_index(name='CASOS')
    series['SEMANA'] = series['SEMANA'].dt.strftime('%Y-%m-%d')

    output = {
        "last_update": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "total_geral": int(df.shape[0]),
        "stats_cidades": stats_cidades,
        "series": series.to_dict(orient='records'),
        "sintomas": {col: round((df[df[col] == '1'].shape[0] / df.shape[0]) * 100, 1) for col in SYMPTOMS_COLS}
    }

    with open('data_processed/dashboard_data.json', 'w') as f:
        json.dump(output, f)

if __name__ == "__main__":
    process()

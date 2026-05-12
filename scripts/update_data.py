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

SYMPTOMS_COLS = ['FEBRE', 'MIALGIA', 'CEFALEIA', 'EXANTEMA', 'VOMITO', 'NAUSEA', 'DOR_COSTAS', 'ARTRALGIA', 'DOR_RETRO']

def process():
    os.makedirs('data_processed', exist_ok=True)
    
    # Abrangência Histórica: 2000 até o ano atual + 2 (para detectar placeholders futuros)
    ano_atual = datetime.now().year
    anos_sufixos = [str(a)[2:].zfill(2) for a in range(2000, ano_atual + 2)]
    
    all_summary = []
    headers = {'User-Agent': 'Mozilla/5.0'}

    for suf in anos_sufixos:
        url = f"https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SINAN/Dengue/csv/DENGBR{suf}.csv"
        print(f"Verificando base histórica: 20{suf}...")
        try:
            with requests.get(url, headers=headers, stream=True, timeout=15) as r:
                if r.status_code != 200: continue
                
                # Para arquivos históricos, usamos apenas as colunas essenciais para não estourar RAM
                chunks = pd.read_csv(io.BytesIO(r.content), sep=None, engine='python', chunksize=200000, 
                                     usecols=['DT_NOTIFIC', 'ID_MN_RESI', 'NU_ANO'], dtype=str)
                
                for chunk in chunks:
                    filtered = chunk[chunk['ID_MN_RESI'].isin(ALTO_TIETE_CODS.keys())].copy()
                    if not filtered.empty:
                        filtered['MUNICIPIO'] = filtered['ID_MN_RESI'].map(ALTO_TIETE_CODS)
                        all_summary.append(filtered)
        except: continue

    if not all_summary: return

    df = pd.concat(all_summary)
    df['DT_NOTIFIC'] = pd.to_datetime(df['DT_NOTIFIC'], errors='coerce')
    df = df.dropna(subset=['DT_NOTIFIC'])

    # Agregação por Mês e Ano para a Série Histórica (JSON fica leve)
    df['MES_ANO'] = df['DT_NOTIFIC'].dt.strftime('%Y-%m')
    historico = df.groupby(['MES_ANO', 'MUNICIPIO']).size().reset_index(name='CASOS')
    
    # Estatísticas por Ano
    stats_ano = df.groupby(['NU_ANO', 'MUNICIPIO']).size().reset_index(name='CASOS')

    output = {
        "last_update": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "total_historico": int(df.shape[0]),
        "series_mensal": historico.to_dict(orient='records'),
        "stats_ano": stats_ano.to_dict(orient='records'),
        "municipios": list(POPULACAO.keys())
    }

    with open('data_processed/dashboard_data.json', 'w') as f:
        json.dump(output, f)

if __name__ == "__main__":
    process()

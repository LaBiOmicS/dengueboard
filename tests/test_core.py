import pytest
from dengueboard.core import ALTO_TIETE_CODS

def test_municipios_count():
    # Garante que as 11 cidades do Alto Tietê estão mapeadas
    assert len(ALTO_TIETE_CODS) == 11

def test_municipio_names():
    # Valida nomes específicos para evitar erros de digitação na base
    assert ALTO_TIETE_CODS['353060'] == 'Mogi das Cruzes'
    assert ALTO_TIETE_CODS['351880'] == 'Guarulhos'

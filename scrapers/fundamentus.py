import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from .utils import (
    USER_AGENT,
    parse_percentage,
    parse_number,
    parse_large_number,
    clean_ticker
)


STOCKS_URL = "https://fundamentus.com.br/resultado.php"
FIIS_URL = "https://fundamentus.com.br/fii_resultado.php"


def scrape_stocks() -> List[Dict]:
    """
    Scrape stock data from Fundamentus.
    Returns list of dicts with stock fundamentals.
    """
    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.get(STOCKS_URL, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        raise Exception(f"Failed to fetch stocks data: {e}")

    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the results table
    table = soup.find('table', {'id': 'resultado'})
    if not table:
        raise Exception("Could not find results table in HTML")

    # Extract header to map column positions
    header_row = table.find('thead').find('tr')
    headers_list = [th.text.strip() for th in header_row.find_all('th')]

    # Column name mapping (Fundamentus -> our schema)
    column_map = {
        'Papel': 'papel',
        'Cotação': 'cotacao',
        'P/L': 'pl',
        'P/VP': 'pvp',
        'Div.Yield': 'div_yield',
        'EV/EBIT': 'ev_ebit',
        'ROIC': 'roic',
        'ROE': 'roe',
        'Liq.2meses': 'liq_2meses',
        'Dív.Líq/ Patrim.': 'div_bruta_patrim',  # Actually Líquida not Bruta, but keeping schema name
        'Cresc. Rec.5a': 'cresc_rec_5a',
    }

    # Build index mapping
    col_indices = {}
    for i, header in enumerate(headers_list):
        if header in column_map:
            col_indices[column_map[header]] = i

    stocks = []

    # Parse data rows
    tbody = table.find('tbody')
    for row in tbody.find_all('tr'):
        cells = row.find_all('td')
        if len(cells) < len(headers_list):
            continue

        stock = {}

        # Extract mapped columns
        if 'papel' in col_indices:
            stock['papel'] = clean_ticker(cells[col_indices['papel']].text)

        if 'cotacao' in col_indices:
            stock['cotacao'] = parse_number(cells[col_indices['cotacao']].text)

        if 'pl' in col_indices:
            stock['pl'] = parse_number(cells[col_indices['pl']].text)

        if 'pvp' in col_indices:
            stock['pvp'] = parse_number(cells[col_indices['pvp']].text)

        if 'div_yield' in col_indices:
            stock['div_yield'] = parse_percentage(cells[col_indices['div_yield']].text)

        if 'ev_ebit' in col_indices:
            stock['ev_ebit'] = parse_number(cells[col_indices['ev_ebit']].text)

        if 'roic' in col_indices:
            stock['roic'] = parse_percentage(cells[col_indices['roic']].text)

        if 'roe' in col_indices:
            stock['roe'] = parse_percentage(cells[col_indices['roe']].text)

        if 'liq_2meses' in col_indices:
            stock['liq_2meses'] = parse_large_number(cells[col_indices['liq_2meses']].text)

        if 'div_bruta_patrim' in col_indices:
            stock['div_bruta_patrim'] = parse_number(cells[col_indices['div_bruta_patrim']].text)

        if 'cresc_rec_5a' in col_indices:
            stock['cresc_rec_5a'] = parse_percentage(cells[col_indices['cresc_rec_5a']].text)

        # Only include if we have ticker
        if stock.get('papel'):
            stocks.append(stock)

    return stocks


def scrape_fiis() -> List[Dict]:
    """
    Scrape FII data from Fundamentus.
    Returns list of dicts with FII fundamentals.
    """
    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.get(FIIS_URL, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        raise Exception(f"Failed to fetch FIIs data: {e}")

    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the results table (FII page uses different ID)
    table = soup.find('table', {'id': 'tabelaResultado'})
    if not table:
        raise Exception("Could not find results table in HTML")

    # Extract header to map column positions
    header_row = table.find('thead').find('tr')
    headers_list = [th.text.strip() for th in header_row.find_all('th')]

    # Column name mapping (Fundamentus -> our schema)
    column_map = {
        'Papel': 'papel',
        'Segmento': 'segmento',
        'Cotação': 'cotacao',
        'FFO Yield': 'ffo_yield',
        'Dividend Yield': 'dividend_yield',
        'P/VP': 'pvp',
        'Valor de Mercado': 'valor_mercado',
        'Liquidez': 'liquidez',
        'Cap Rate': 'cap_rate',
        'Vacância Média': 'vacancia_media',
    }

    # Build index mapping
    col_indices = {}
    for i, header in enumerate(headers_list):
        if header in column_map:
            col_indices[column_map[header]] = i

    fiis = []

    # Parse data rows
    tbody = table.find('tbody')
    for row in tbody.find_all('tr'):
        cells = row.find_all('td')
        if len(cells) < len(headers_list):
            continue

        fii = {}

        # Extract mapped columns
        if 'papel' in col_indices:
            fii['papel'] = clean_ticker(cells[col_indices['papel']].text)

        if 'segmento' in col_indices:
            seg = cells[col_indices['segmento']].text.strip()
            fii['segmento'] = seg if seg and seg != '-' else None

        if 'cotacao' in col_indices:
            fii['cotacao'] = parse_number(cells[col_indices['cotacao']].text)

        if 'ffo_yield' in col_indices:
            fii['ffo_yield'] = parse_percentage(cells[col_indices['ffo_yield']].text)

        if 'dividend_yield' in col_indices:
            fii['dividend_yield'] = parse_percentage(cells[col_indices['dividend_yield']].text)

        if 'pvp' in col_indices:
            fii['pvp'] = parse_number(cells[col_indices['pvp']].text)

        if 'valor_mercado' in col_indices:
            fii['valor_mercado'] = parse_large_number(cells[col_indices['valor_mercado']].text)

        if 'liquidez' in col_indices:
            fii['liquidez'] = parse_large_number(cells[col_indices['liquidez']].text)

        if 'cap_rate' in col_indices:
            fii['cap_rate'] = parse_percentage(cells[col_indices['cap_rate']].text)

        if 'vacancia_media' in col_indices:
            fii['vacancia_media'] = parse_percentage(cells[col_indices['vacancia_media']].text)

        # Only include if we have ticker
        if fii.get('papel'):
            fiis.append(fii)

    return fiis

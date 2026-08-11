import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

DB_PATH = Path(__file__).parent.parent / "data" / "screener.db"


def init_db():
    """Initialize database schema."""
    DB_PATH.parent.mkdir(exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Stocks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stocks (
            papel TEXT PRIMARY KEY,
            cotacao REAL,
            pl REAL,
            pvp REAL,
            div_yield REAL,
            ev_ebit REAL,
            roic REAL,
            roe REAL,
            liq_2meses REAL,
            div_bruta_patrim REAL,
            cresc_rec_5a REAL,
            raw_data TEXT,
            last_updated TIMESTAMP
        )
    """)

    # FIIs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fiis (
            papel TEXT PRIMARY KEY,
            segmento TEXT,
            cotacao REAL,
            ffo_yield REAL,
            dividend_yield REAL,
            pvp REAL,
            valor_mercado REAL,
            liquidez REAL,
            cap_rate REAL,
            vacancia_media REAL,
            raw_data TEXT,
            last_updated TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def get_connection():
    """Get database connection with Row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def save_stocks(stocks: List[dict]):
    """Save stocks to database."""
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now()

    for stock in stocks:
        cursor.execute("""
            INSERT OR REPLACE INTO stocks
            (papel, cotacao, pl, pvp, div_yield, ev_ebit, roic, roe,
             liq_2meses, div_bruta_patrim, cresc_rec_5a, raw_data, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            stock.get('papel'),
            stock.get('cotacao'),
            stock.get('pl'),
            stock.get('pvp'),
            stock.get('div_yield'),
            stock.get('ev_ebit'),
            stock.get('roic'),
            stock.get('roe'),
            stock.get('liq_2meses'),
            stock.get('div_bruta_patrim'),
            stock.get('cresc_rec_5a'),
            str(stock),
            now
        ))

    conn.commit()
    conn.close()


def save_fiis(fiis: List[dict]):
    """Save FIIs to database."""
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now()

    for fii in fiis:
        cursor.execute("""
            INSERT OR REPLACE INTO fiis
            (papel, segmento, cotacao, ffo_yield, dividend_yield, pvp,
             valor_mercado, liquidez, cap_rate, vacancia_media, raw_data, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            fii.get('papel'),
            fii.get('segmento'),
            fii.get('cotacao'),
            fii.get('ffo_yield'),
            fii.get('dividend_yield'),
            fii.get('pvp'),
            fii.get('valor_mercado'),
            fii.get('liquidez'),
            fii.get('cap_rate'),
            fii.get('vacancia_media'),
            str(fii),
            now
        ))

    conn.commit()
    conn.close()


def get_all_stocks() -> List[dict]:
    """Retrieve all stocks from database."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM stocks")
    rows = cursor.fetchall()

    conn.close()

    return [dict(row) for row in rows]


def get_all_fiis() -> List[dict]:
    """Retrieve all FIIs from database."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM fiis")
    rows = cursor.fetchall()

    conn.close()

    return [dict(row) for row in rows]


def get_last_update_time(asset_type: str) -> Optional[datetime]:
    """Get last update timestamp for given asset type."""
    conn = get_connection()
    cursor = conn.cursor()

    table = "stocks" if asset_type == "stocks" else "fiis"
    cursor.execute(f"SELECT MAX(last_updated) as last_updated FROM {table}")

    row = cursor.fetchone()
    conn.close()

    if row and row['last_updated']:
        return datetime.fromisoformat(row['last_updated'])
    return None

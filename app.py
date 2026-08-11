from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional

from models.database import (
    init_db,
    save_stocks,
    save_fiis,
    get_all_stocks,
    get_all_fiis,
    get_last_update_time
)
from models.schemas import (
    Stock, FII,
    calculate_stock_score,
    calculate_fii_score,
    calculate_quality_score
)
from scrapers.fundamentus import scrape_stocks, scrape_fiis


# Initialize database
init_db()

app = FastAPI(
    title="B3 Investment Screener",
    description="Screener de ações e FIIs da B3 usando dados fundamentalistas",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


# Minimum refresh interval (1 hour)
MIN_REFRESH_INTERVAL = timedelta(hours=1)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve main HTML page."""
    html_file = Path("templates/index.html")
    if not html_file.exists():
        raise HTTPException(status_code=404, detail="Template not found")
    return html_file.read_text(encoding='utf-8')


@app.get("/api/stocks", response_model=List[Stock])
async def get_stocks(
    pl_min: Optional[float] = None,
    pl_max: Optional[float] = None,
    pvp_min: Optional[float] = None,
    pvp_max: Optional[float] = None,
    div_yield_min: Optional[float] = None,
    div_yield_max: Optional[float] = None,
    ev_ebit_min: Optional[float] = None,
    ev_ebit_max: Optional[float] = None,
    roic_min: Optional[float] = None,
    roic_max: Optional[float] = None,
    roe_min: Optional[float] = None,
    roe_max: Optional[float] = None,
    div_bruta_patrim_min: Optional[float] = None,
    div_bruta_patrim_max: Optional[float] = None,
    cresc_rec_5a_min: Optional[float] = None,
    cresc_rec_5a_max: Optional[float] = None,
):
    """
    Get stocks with optional filters.
    Returns stocks sorted by score (descending).
    """
    stocks = get_all_stocks()

    # Apply filters first
    filtered = []
    filtered = []
    for stock in stocks:
        # Skip if any required metric is None and filter is applied
        if pl_min is not None or pl_max is not None:
            if stock.get('pl') is None:
                continue
            if pl_min is not None and stock['pl'] < pl_min:
                continue
            if pl_max is not None and stock['pl'] > pl_max:
                continue

        if pvp_min is not None or pvp_max is not None:
            if stock.get('pvp') is None:
                continue
            if pvp_min is not None and stock['pvp'] < pvp_min:
                continue
            if pvp_max is not None and stock['pvp'] > pvp_max:
                continue

        if div_yield_min is not None or div_yield_max is not None:
            if stock.get('div_yield') is None:
                continue
            if div_yield_min is not None and stock['div_yield'] < div_yield_min:
                continue
            if div_yield_max is not None and stock['div_yield'] > div_yield_max:
                continue

        if ev_ebit_min is not None or ev_ebit_max is not None:
            if stock.get('ev_ebit') is None:
                continue
            if ev_ebit_min is not None and stock['ev_ebit'] < ev_ebit_min:
                continue
            if ev_ebit_max is not None and stock['ev_ebit'] > ev_ebit_max:
                continue

        if roic_min is not None or roic_max is not None:
            if stock.get('roic') is None:
                continue
            if roic_min is not None and stock['roic'] < roic_min:
                continue
            if roic_max is not None and stock['roic'] > roic_max:
                continue

        if roe_min is not None or roe_max is not None:
            if stock.get('roe') is None:
                continue
            if roe_min is not None and stock['roe'] < roe_min:
                continue
            if roe_max is not None and stock['roe'] > roe_max:
                continue

        if div_bruta_patrim_min is not None or div_bruta_patrim_max is not None:
            if stock.get('div_bruta_patrim') is None:
                continue
            if div_bruta_patrim_min is not None and stock['div_bruta_patrim'] < div_bruta_patrim_min:
                continue
            if div_bruta_patrim_max is not None and stock['div_bruta_patrim'] > div_bruta_patrim_max:
                continue

        if cresc_rec_5a_min is not None or cresc_rec_5a_max is not None:
            if stock.get('cresc_rec_5a') is None:
                continue
            if cresc_rec_5a_min is not None and stock['cresc_rec_5a'] < cresc_rec_5a_min:
                continue
            if cresc_rec_5a_max is not None and stock['cresc_rec_5a'] > cresc_rec_5a_max:
                continue

        filtered.append(stock)

    # Calculate scores (needs full filtered list for best-in-metric logic)
    stock_metrics = {
        'pl': 'minimize',
        'pvp': 'minimize',
        'div_yield': 'maximize',
        'ev_ebit': 'minimize',
        'roic': 'maximize',
        'roe': 'maximize',
        'div_bruta_patrim': 'minimize',
        'cresc_rec_5a': 'maximize'
    }

    for stock in filtered:
        score, winning = calculate_stock_score(filtered, stock)
        quality = calculate_quality_score(filtered, stock, stock_metrics)
        stock['score'] = score
        stock['quality_score'] = quality
        stock['winning_metrics'] = winning

    # Sort by score DESC, then quality DESC
    filtered.sort(key=lambda x: (x.get('score', 0), x.get('quality_score', 0)), reverse=True)

    return filtered


@app.get("/api/fiis", response_model=List[FII])
async def get_fiis(
    dividend_yield_min: Optional[float] = None,
    dividend_yield_max: Optional[float] = None,
    pvp_min: Optional[float] = None,
    pvp_max: Optional[float] = None,
    liquidez_min: Optional[float] = None,
    liquidez_max: Optional[float] = None,
    cap_rate_min: Optional[float] = None,
    cap_rate_max: Optional[float] = None,
    vacancia_media_min: Optional[float] = None,
    vacancia_media_max: Optional[float] = None,
):
    """
    Get FIIs with optional filters.
    Returns FIIs sorted by score (descending).
    """
    fiis = get_all_fiis()

    # Apply filters
    filtered = []
    for fii in fiis:
        if dividend_yield_min is not None or dividend_yield_max is not None:
            if fii.get('dividend_yield') is None:
                continue
            if dividend_yield_min is not None and fii['dividend_yield'] < dividend_yield_min:
                continue
            if dividend_yield_max is not None and fii['dividend_yield'] > dividend_yield_max:
                continue

        if pvp_min is not None or pvp_max is not None:
            if fii.get('pvp') is None:
                continue
            if pvp_min is not None and fii['pvp'] < pvp_min:
                continue
            if pvp_max is not None and fii['pvp'] > pvp_max:
                continue

        if liquidez_min is not None or liquidez_max is not None:
            if fii.get('liquidez') is None:
                continue
            if liquidez_min is not None and fii['liquidez'] < liquidez_min:
                continue
            if liquidez_max is not None and fii['liquidez'] > liquidez_max:
                continue

        if cap_rate_min is not None or cap_rate_max is not None:
            if fii.get('cap_rate') is None:
                continue
            if cap_rate_min is not None and fii['cap_rate'] < cap_rate_min:
                continue
            if cap_rate_max is not None and fii['cap_rate'] > cap_rate_max:
                continue

        if vacancia_media_min is not None or vacancia_media_max is not None:
            if fii.get('vacancia_media') is None:
                continue
            if vacancia_media_min is not None and fii['vacancia_media'] < vacancia_media_min:
                continue
            if vacancia_media_max is not None and fii['vacancia_media'] > vacancia_media_max:
                continue

        filtered.append(fii)

    # Calculate scores (needs full filtered list for best-in-metric logic)
    fii_metrics = {
        'dividend_yield': 'maximize',
        'ffo_yield': 'maximize',
        'pvp': 'neutral',  # Closest to 1.0 handled separately
        'liquidez': 'maximize',
        'cap_rate': 'maximize',
        'vacancia_media': 'minimize'
    }

    for fii in filtered:
        score, winning = calculate_fii_score(filtered, fii)
        quality = calculate_quality_score(filtered, fii, fii_metrics)
        fii['score'] = score
        fii['quality_score'] = quality
        fii['winning_metrics'] = winning

    # Sort by score DESC, then quality DESC
    filtered.sort(key=lambda x: (x.get('score', 0), x.get('quality_score', 0)), reverse=True)

    return filtered


@app.post("/api/refresh")
async def refresh_data(asset_type: str):
    """
    Refresh data by scraping Fundamentus.
    asset_type: 'stocks' or 'fiis'
    Rate limited to once per hour.
    """
    if asset_type not in ['stocks', 'fiis']:
        raise HTTPException(status_code=400, detail="Invalid asset_type. Use 'stocks' or 'fiis'")

    # Check last update time
    last_update = get_last_update_time(asset_type)
    if last_update:
        elapsed = datetime.now() - last_update
        if elapsed < MIN_REFRESH_INTERVAL:
            remaining = MIN_REFRESH_INTERVAL - elapsed
            remaining_minutes = int(remaining.total_seconds() / 60)
            return JSONResponse(
                status_code=429,
                content={
                    "detail": f"Rate limited. Try again in {remaining_minutes} minutes.",
                    "retry_after_minutes": remaining_minutes
                }
            )

    try:
        if asset_type == 'stocks':
            data = scrape_stocks()
            save_stocks(data)
            return {"message": f"Successfully refreshed {len(data)} stocks", "count": len(data)}
        else:
            data = scrape_fiis()
            save_fiis(data)
            return {"message": f"Successfully refreshed {len(data)} FIIs", "count": len(data)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")


@app.get("/api/last-update")
async def get_last_update(asset_type: str):
    """Get last update timestamp for asset type."""
    if asset_type not in ['stocks', 'fiis']:
        raise HTTPException(status_code=400, detail="Invalid asset_type")

    last_update = get_last_update_time(asset_type)
    if last_update:
        return {
            "last_updated": last_update.isoformat(),
            "last_updated_formatted": last_update.strftime("%Y-%m-%d %H:%M")
        }

    return {"last_updated": None, "last_updated_formatted": "Nunca"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

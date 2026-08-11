from typing import Optional, List
from pydantic import BaseModel


class Stock(BaseModel):
    papel: str
    cotacao: Optional[float] = None
    pl: Optional[float] = None
    pvp: Optional[float] = None
    div_yield: Optional[float] = None
    ev_ebit: Optional[float] = None
    roic: Optional[float] = None
    roe: Optional[float] = None
    liq_2meses: Optional[float] = None
    div_bruta_patrim: Optional[float] = None
    cresc_rec_5a: Optional[float] = None
    score: Optional[int] = None
    quality_score: Optional[float] = None
    winning_metrics: Optional[List[str]] = None


class FII(BaseModel):
    papel: str
    segmento: Optional[str] = None
    cotacao: Optional[float] = None
    ffo_yield: Optional[float] = None
    dividend_yield: Optional[float] = None
    pvp: Optional[float] = None
    valor_mercado: Optional[float] = None
    liquidez: Optional[float] = None
    cap_rate: Optional[float] = None
    vacancia_media: Optional[float] = None
    score: Optional[int] = None
    quality_score: Optional[float] = None
    winning_metrics: Optional[List[str]] = None


def calculate_stock_score_old(stock: dict) -> float:
    """
    Calculate composite score for stock (0-100 scale).

    Score composition:
    - Value (40%): Lower P/L, P/VP, EV/EBIT = higher score
    - Quality (40%): Higher ROIC, ROE = higher score
    - Yield (10%): Higher Div.Yield = higher score
    - Growth (10%): Higher Cresc.Rec.5a = higher score
    """
    score = 0.0
    components = []

    # Value metrics (inverse normalized)
    pl = stock.get('pl')
    pvp = stock.get('pvp')
    ev_ebit = stock.get('ev_ebit')

    if pl and pl > 0:
        # Lower P/L better, cap at 30
        value_pl = max(0, (30 - min(pl, 30)) / 30 * 100)
        components.append(('value_pl', value_pl))

    if pvp and pvp > 0:
        # Lower P/VP better, cap at 5
        value_pvp = max(0, (5 - min(pvp, 5)) / 5 * 100)
        components.append(('value_pvp', value_pvp))

    if ev_ebit and ev_ebit > 0:
        # Lower EV/EBIT better, cap at 20
        value_ev = max(0, (20 - min(ev_ebit, 20)) / 20 * 100)
        components.append(('value_ev', value_ev))

    # Quality metrics (direct normalized)
    roic = stock.get('roic')
    roe = stock.get('roe')

    if roic:
        # Higher ROIC better, cap at 0.5 (50%)
        quality_roic = min(abs(roic) / 0.5 * 100, 100)
        components.append(('quality_roic', quality_roic))

    if roe:
        # Higher ROE better, cap at 0.5 (50%)
        quality_roe = min(abs(roe) / 0.5 * 100, 100)
        components.append(('quality_roe', quality_roe))

    # Yield metric
    div_yield = stock.get('div_yield')
    if div_yield and div_yield > 0:
        # Higher yield better, cap at 0.15 (15%)
        yield_score = min(div_yield / 0.15 * 100, 100)
        components.append(('yield', yield_score))

    # Growth metric
    cresc = stock.get('cresc_rec_5a')
    if cresc:
        # Higher growth better, cap at 0.3 (30%)
        growth_score = min(abs(cresc) / 0.3 * 100, 100)
        components.append(('growth', growth_score))

    # Weighted average
    if not components:
        return 0.0

    # Group by category
    value_scores = [v for k, v in components if k.startswith('value')]
    quality_scores = [v for k, v in components if k.startswith('quality')]
    yield_scores = [v for k, v in components if k == 'yield']
    growth_scores = [v for k, v in components if k == 'growth']

    value_avg = sum(value_scores) / len(value_scores) if value_scores else 0
    quality_avg = sum(quality_scores) / len(quality_scores) if quality_scores else 0
    yield_avg = sum(yield_scores) / len(yield_scores) if yield_scores else 0
    growth_avg = sum(growth_scores) / len(growth_scores) if growth_scores else 0

    score = (
        value_avg * 0.40 +
        quality_avg * 0.40 +
        yield_avg * 0.10 +
        growth_avg * 0.10
    )

    return round(score, 2)


def calculate_stock_score(stocks: list, stock: dict) -> tuple:
    """
    Calculate score for stock using "best-in-metric" logic.

    Stock gets +1 point for each metric where it ranks #1:
    - Lowest P/L
    - Lowest P/VP
    - Highest Div.Yield
    - Lowest EV/EBIT
    - Highest ROIC
    - Highest ROE
    - Lowest Dív.Brut/Patrim
    - Highest Cresc.Rec.5a

    Returns tuple: (score, list of winning metrics).
    """
    score = 0
    winning_metrics = []

    # Find best values across all stocks (excluding None)
    metrics_to_minimize = ['pl', 'pvp', 'ev_ebit', 'div_bruta_patrim']
    metrics_to_maximize = ['div_yield', 'roic', 'roe', 'cresc_rec_5a']

    for metric in metrics_to_minimize:
        values = [s.get(metric) for s in stocks if s.get(metric) is not None and s.get(metric) >= 0]
        if values and stock.get(metric) is not None:
            if stock[metric] == min(values):
                score += 1
                winning_metrics.append(metric)

    for metric in metrics_to_maximize:
        values = [s.get(metric) for s in stocks if s.get(metric) is not None]
        if values and stock.get(metric) is not None:
            if stock[metric] == max(values):
                score += 1
                winning_metrics.append(metric)

    return score, winning_metrics


def calculate_percentile_rank(values: list, target_value: float, lower_is_better: bool) -> float:
    """
    Calculate percentile rank (0-100) for a value within a list.

    Args:
        values: Sorted list of values
        target_value: Value to rank
        lower_is_better: True if lower values rank higher (e.g. P/L)

    Returns:
        Percentile rank (0-100)
    """
    if not values or target_value is None:
        return 50.0  # Neutral if no data

    # Find rank position (1-indexed)
    sorted_values = sorted(values)
    try:
        rank = sorted_values.index(target_value) + 1
    except ValueError:
        return 50.0

    total = len(sorted_values)

    if lower_is_better:
        # Lower values = higher percentile
        percentile = (1 - (rank - 1) / total) * 100
    else:
        # Higher values = higher percentile
        percentile = ((rank - 1) / total) * 100

    return percentile


def calculate_quality_score(stocks: list, stock: dict, metrics_config: dict) -> float:
    """
    Calculate composite quality score as average percentile across all metrics.

    Args:
        stocks: Full list of stocks/fiis
        stock: Target stock/fii
        metrics_config: Dict mapping metric names to 'minimize' or 'maximize'

    Returns:
        Quality score (0-100)
    """
    percentiles = []

    for metric, direction in metrics_config.items():
        # Get valid values for this metric
        values = [s.get(metric) for s in stocks if s.get(metric) is not None]

        # Skip if no valid comparison data
        if not values or stock.get(metric) is None:
            continue

        # Calculate percentile for this metric
        lower_is_better = (direction == 'minimize')
        percentile = calculate_percentile_rank(values, stock[metric], lower_is_better)
        percentiles.append(percentile)

    # Return average percentile
    if not percentiles:
        return 50.0

    return round(sum(percentiles) / len(percentiles), 2)


def calculate_fii_score(fiis: list, fii: dict) -> tuple:
    """
    Calculate score for FII using "best-in-metric" logic.

    FII gets +1 point for each metric where it ranks #1:
    - Highest Dividend Yield
    - Highest FFO Yield
    - P/VP closest to 1.0
    - Highest Liquidez
    - Highest Cap Rate
    - Lowest Vacância

    Returns tuple: (score, list of winning metrics).
    """
    score = 0
    winning_metrics = []

    # Metrics to maximize
    metrics_to_maximize = ['dividend_yield', 'ffo_yield', 'liquidez', 'cap_rate']

    for metric in metrics_to_maximize:
        values = [f.get(metric) for f in fiis if f.get(metric) is not None]
        if values and fii.get(metric) is not None:
            if fii[metric] == max(values):
                score += 1
                winning_metrics.append(metric)

    # Vacância - minimize
    vacancia_values = [f.get('vacancia_media') for f in fiis if f.get('vacancia_media') is not None]
    if vacancia_values and fii.get('vacancia_media') is not None:
        if fii['vacancia_media'] == min(vacancia_values):
            score += 1
            winning_metrics.append('vacancia_media')

    # P/VP closest to 1.0
    pvp_values = [f.get('pvp') for f in fiis if f.get('pvp') is not None]
    if pvp_values and fii.get('pvp') is not None:
        distances = {f['papel']: abs(f.get('pvp', 999) - 1.0) for f in fiis if f.get('pvp') is not None}
        min_distance = min(distances.values())
        if abs(fii['pvp'] - 1.0) == min_distance:
            score += 1
            winning_metrics.append('pvp')

    return score, winning_metrics


def calculate_fii_score_old(fii: dict) -> float:
    """
    Calculate composite score for FII (0-100 scale).

    Score composition:
    - Yield (50%): Higher Dividend Yield, FFO Yield, Cap Rate = higher score
    - Valuation (30%): P/VP closer to 1.0 = higher score
    - Quality (20%): Higher liquidity, lower vacancy = higher score
    """
    score = 0.0
    components = []

    # Yield metrics (direct normalized)
    div_yield = fii.get('dividend_yield')
    ffo_yield = fii.get('ffo_yield')
    cap_rate = fii.get('cap_rate')

    if div_yield and div_yield > 0:
        # Cap at 0.15 (15%)
        yield_div = min(div_yield / 0.15 * 100, 100)
        components.append(('yield_div', yield_div))

    if ffo_yield and ffo_yield > 0:
        # Cap at 0.15 (15%)
        yield_ffo = min(ffo_yield / 0.15 * 100, 100)
        components.append(('yield_ffo', yield_ffo))

    if cap_rate and cap_rate > 0:
        # Cap at 0.15 (15%)
        yield_cap = min(cap_rate / 0.15 * 100, 100)
        components.append(('yield_cap', yield_cap))

    # Valuation metric (P/VP closest to 1.0)
    pvp = fii.get('pvp')
    if pvp and pvp > 0:
        # Distance from 1.0, normalized (closer = better)
        distance = abs(pvp - 1.0)
        # Penalize beyond 0.5 distance heavily
        valuation = max(0, (0.5 - min(distance, 0.5)) / 0.5 * 100)
        components.append(('valuation', valuation))

    # Quality metrics
    liquidez = fii.get('liquidez')
    vacancia = fii.get('vacancia_media')

    if liquidez and liquidez > 0:
        # Higher liquidity better, cap at 1M
        quality_liq = min(liquidez / 1000000 * 100, 100)
        components.append(('quality_liq', quality_liq))

    if vacancia is not None:
        # Lower vacancy better, cap at 0.3 (30%)
        quality_vac = max(0, (0.3 - min(vacancia, 0.3)) / 0.3 * 100)
        components.append(('quality_vac', quality_vac))

    if not components:
        return 0.0

    # Group by category
    yield_scores = [v for k, v in components if k.startswith('yield')]
    valuation_scores = [v for k, v in components if k == 'valuation']
    quality_scores = [v for k, v in components if k.startswith('quality')]

    yield_avg = sum(yield_scores) / len(yield_scores) if yield_scores else 0
    valuation_avg = sum(valuation_scores) / len(valuation_scores) if valuation_scores else 0
    quality_avg = sum(quality_scores) / len(quality_scores) if quality_scores else 0

    score = (
        yield_avg * 0.50 +
        valuation_avg * 0.30 +
        quality_avg * 0.20
    )

    return round(score, 2)

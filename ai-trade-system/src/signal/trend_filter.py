"""
トレンドフィルター

移動平均線（SMA）を用いて相場のトレンド方向を判定する。
下落トレンド中にロング系シグナル（ダブルボトム等）をブロックし、
ダマシを防止する。
また、上昇トレンド中にショート系シグナルをブロックする
逆トレンドフィルター機能も提供する。
"""


def compute_sma(candles, period):
    """終値のSMA（単純移動平均）を計算する。"""
    closes = [c["close"] for c in candles]
    if len(closes) < period:
        return None
    return sum(closes[-period:]) / period


def is_downtrend(candles, fast_period=50, slow_period=200):
    """
    下落トレンドかどうかを判定する。

    SMA(fast) < SMA(slow) → 下落トレンド

    Returns:
        True: 下落トレンド
        False: 上昇トレンド
        None: データ不足で判定不可
    """
    sma_fast = compute_sma(candles, fast_period)
    sma_slow = compute_sma(candles, slow_period)
    if sma_fast is None or sma_slow is None:
        return None
    return sma_fast < sma_slow


def is_uptrend(candles, fast_period=50, slow_period=200):
    """
    上昇トレンドかどうかを判定する。

    SMA(fast) > SMA(slow) → 上昇トレンド

    Returns:
        True: 上昇トレンド
        False: 下落トレンド
        None: データ不足で判定不可
    """
    sma_fast = compute_sma(candles, fast_period)
    sma_slow = compute_sma(candles, slow_period)
    if sma_fast is None or sma_slow is None:
        return None
    return sma_fast > sma_slow


def check_short_trend_filter(candles, filter_config, strategy_uses_filter=True):
    """
    ショート戦略用トレンドフィルターを適用する。

    Args:
        candles: OHLCVデータのリスト
        filter_config: グローバルトレンドフィルター設定
        strategy_uses_filter: この戦略がフィルターを使うか

    Returns:
        True: シグナルをブロック（却下）
        False: シグナルを許可
    """
    if not strategy_uses_filter:
        return False

    if not filter_config or not filter_config.get("enabled"):
        return False

    fast = filter_config.get("fast_period", 50)
    slow = filter_config.get("slow_period", 200)

    uptrend = is_uptrend(candles, fast, slow)
    if uptrend is None:
        return False  # データ不足時はフィルターなし

    return uptrend  # 上昇トレンド → ブロック


def check_trend_filter(candles, filter_config, strategy_uses_filter=True):
    """
    トレンドフィルターを適用する。

    Args:
        candles: OHLCVデータのリスト
        filter_config: グローバルトレンドフィルター設定
        strategy_uses_filter: この戦略がフィルターを使うか

    Returns:
        True: シグナルをブロック（却下）
        False: シグナルを許可
    """
    if not strategy_uses_filter:
        return False

    if not filter_config or not filter_config.get("enabled"):
        return False

    fast = filter_config.get("fast_period", 50)
    slow = filter_config.get("slow_period", 200)

    downtrend = is_downtrend(candles, fast, slow)
    if downtrend is None:
        return False  # データ不足時はフィルターなし

    return downtrend  # 下落トレンド → ブロック

"""
kabu API モックサーバー

kabu ステーション API (localhost:18081) の主要エンドポイントをモックする。
FastAPI ベースで起動し、開発・テスト時に本番 kabu ステーション不要で動作する。

エンドポイント:
    POST /kabusapi/token        — APIトークン発行
    GET  /kabusapi/board/{symbol} — 板情報・気配データ返却
    PUT  /kabusapi/register     — PUSH配信銘柄登録（スタブ）

シナリオ:
    "normal"       — 通常気配（ランダム生成）
    "buy_dominant" — 買い優勢（UnderBuy >> OverSell）
    "sell_dominant" — 売り優勢
    "tokubetsu_kai" — 特別買い気配（AskSign="0103"）
    "tokubetsu_uri" — 特別売り気配（BidSign="0104"）

使い方:
    # 起動
    python kabu_mock.py
    # または
    uvicorn jp_daytrade.data.kabu_mock:app --port 18081

    # テストから呼び出し
    from jp_daytrade.data.kabu_mock import KabuMockServer
    server = KabuMockServer()
    data = server.get_board("7203")

Example:
    >>> server = KabuMockServer(scenario="buy_dominant")
    >>> board = server.get_board("7203")
    >>> assert board["AskSign"] == "0101"
    >>> assert board["UnderBuy"] > board["OverSell"]
"""

import logging
import random
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# モックトークン（テスト用固定値）
MOCK_TOKEN = "mock_token_12345"

# 特別気配フラグ定数
SIGN_NORMAL = "0101"          # 現値（通常気配）
SIGN_GENERAL = "0102"         # 一般気配
SIGN_TOKUBETSU_KAI = "0103"  # 特別買い気配
SIGN_TOKUBETSU_URI = "0104"  # 特別売り気配
SIGN_CHIDAN = "0107"          # 中断前特別気配

# デフォルトシナリオ設定
SCENARIO_PARAMS: Dict[str, Dict[str, Any]] = {
    "normal": {
        "ask_sign": SIGN_NORMAL,
        "bid_sign": SIGN_NORMAL,
        "buy_ratio": 1.0,    # over_sell / under_buy
        "gap_pct": 0.0,
    },
    "buy_dominant": {
        "ask_sign": SIGN_NORMAL,
        "bid_sign": SIGN_NORMAL,
        "buy_ratio": 0.5,    # under_buy が over_sell の 2 倍
        "gap_pct": 0.05,
    },
    "sell_dominant": {
        "ask_sign": SIGN_NORMAL,
        "bid_sign": SIGN_NORMAL,
        "buy_ratio": 2.0,
        "gap_pct": -0.03,
    },
    "tokubetsu_kai": {
        "ask_sign": SIGN_TOKUBETSU_KAI,
        "bid_sign": SIGN_NORMAL,
        "buy_ratio": 0.3,
        "gap_pct": 0.10,
    },
    "tokubetsu_uri": {
        "ask_sign": SIGN_NORMAL,
        "bid_sign": SIGN_TOKUBETSU_URI,
        "buy_ratio": 3.0,
        "gap_pct": -0.08,
    },
}

# サンプル銘柄マスター（テスト用）
SAMPLE_STOCKS: Dict[str, Dict[str, Any]] = {
    "7203": {"name": "トヨタ自動車",   "base_price": 2500, "exchange": 1},
    "9984": {"name": "ソフトバンクグループ", "base_price": 8000, "exchange": 1},
    "2413": {"name": "エムスリー",     "base_price": 1200, "exchange": 1},
    "4689": {"name": "LINEヤフー",    "base_price": 350,  "exchange": 1},
    "6098": {"name": "リクルートHD",  "base_price": 6500, "exchange": 1},
}


class KabuMockServer:
    """
    kabu API モックサーバー（テスト・開発用）

    FastAPI アプリを内包し、スタンドアロン起動またはテスト内で直接呼び出しが可能。

    Args:
        scenario:    デフォルトシナリオ（"normal", "buy_dominant", "sell_dominant",
                     "tokubetsu_kai", "tokubetsu_uri"）
        seed:        乱数シード（再現性が必要なテストで指定）

    Example:
        >>> server = KabuMockServer(scenario="buy_dominant")
        >>> board = server.get_board("7203")
        >>> assert board["Symbol"] == "7203"
        >>> assert "Sell1" in board
        >>> assert "Buy10" in board
    """

    def __init__(
        self,
        scenario: str = "normal",
        seed: Optional[int] = None,
    ) -> None:
        if scenario not in SCENARIO_PARAMS:
            raise ValueError(f"Unknown scenario: {scenario!r}. Choose from {list(SCENARIO_PARAMS.keys())}")
        self.scenario = scenario
        self._rng = random.Random(seed)
        logger.info("KabuMockServer initialized (scenario=%s, seed=%s)", scenario, seed)

    # ------------------------------------------------------------------
    # 公開 API（テスト・内部呼び出し用）
    # ------------------------------------------------------------------

    def get_token(self) -> Dict[str, str]:
        """
        モック APIトークンを返す。

        Returns:
            {"Token": "mock_token_12345"}
        """
        return {"Token": MOCK_TOKEN}

    def get_board(
        self,
        symbol: str,
        scenario: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        指定銘柄のモック板情報を返す。

        レスポンス形式は kabu API 公式仕様（/kabusapi/board/{symbol}@{exchange}）
        に準拠する。Sell1〜Sell10, Buy1〜Buy10 の板10本も含む。

        Args:
            symbol:   銘柄コード（例: "7203"）
            scenario: シナリオ上書き（省略時はインスタンスのデフォルト）

        Returns:
            板情報 dict（公式レスポンス形式）

        Example:
            >>> board = server.get_board("7203")
            >>> assert board["Symbol"] == "7203"
            >>> assert board["AskSign"] in ("0101", "0102", "0103", "0104")
        """
        sc = scenario or self.scenario
        params = SCENARIO_PARAMS.get(sc, SCENARIO_PARAMS["normal"])

        stock = SAMPLE_STOCKS.get(symbol, {"name": f"銘柄{symbol}", "base_price": 1000, "exchange": 1})
        base_price = stock["base_price"]

        # GAP分を加算
        calc_price = round(base_price * (1 + params["gap_pct"]))
        current_price = calc_price

        # ランダム微変動
        noise = self._rng.uniform(-0.002, 0.002)
        calc_price = round(calc_price * (1 + noise))

        # 板生成（呼値 = 1円単位で簡略化）
        tick = max(1, round(base_price * 0.001))

        sell_levels = self._build_levels(calc_price, tick, direction="sell", n=10)
        buy_levels = self._build_levels(calc_price, tick, direction="buy", n=10)

        # 板外数量（成行・上下限外）
        base_qty = self._rng.randint(3000, 20000)
        ratio = params["buy_ratio"]
        over_sell = round(base_qty * ratio)
        under_buy = round(base_qty)

        board: Dict[str, Any] = {
            "Symbol": symbol,
            "SymbolName": stock["name"],
            "Exchange": stock["exchange"],
            "CurrentPrice": current_price,
            "CalcPrice": calc_price,
            "AskSign": params["ask_sign"],
            "BidSign": params["bid_sign"],
            "OverSell": over_sell,
            "UnderBuy": under_buy,
            "TradingVolume": 0,
            "TradingValue": 0,
            "PreviousClose": base_price,
            "ChangePreviousClose": current_price - base_price,
            "ChangePreviousClosePer": round((current_price - base_price) / base_price * 100, 2),
        }

        # Sell1〜Sell10 / Buy1〜Buy10 を展開
        for i, level in enumerate(sell_levels, 1):
            entry: Dict[str, Any] = {"Price": level["price"], "Qty": level["qty"]}
            if i == 1:
                entry["Sign"] = params["ask_sign"]
                entry["Time"] = "08:58:30"
            board[f"Sell{i}"] = entry

        for i, level in enumerate(buy_levels, 1):
            entry = {"Price": level["price"], "Qty": level["qty"]}
            if i == 1:
                entry["Sign"] = params["bid_sign"]
                entry["Time"] = "08:58:30"
            board[f"Buy{i}"] = entry

        return board

    def register_symbols(self, symbols: List[str]) -> Dict[str, Any]:
        """
        PUSH 配信銘柄登録（スタブ）。

        Args:
            symbols: 銘柄コードリスト

        Returns:
            {"RegistList": [{"Result": 0, "Symbol": code} for code in symbols]}
        """
        return {
            "RegistList": [{"Result": 0, "Symbol": s} for s in symbols]
        }

    # ------------------------------------------------------------------
    # 内部ユーティリティ
    # ------------------------------------------------------------------

    def _build_levels(
        self,
        base_price: int,
        tick: int,
        direction: str,
        n: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        板10本を生成する。

        Args:
            base_price: 基準価格
            tick:       呼値（価格刻み）
            direction:  "sell" または "buy"
            n:          板の本数

        Returns:
            [{"price": X, "qty": Y}, ...] のリスト（n件）
        """
        levels = []
        for i in range(n):
            if direction == "sell":
                price = base_price + tick * (i + 1)
            else:
                price = base_price - tick * (i + 1)
            qty = self._rng.randint(100, 2000) * 100  # 単元未満切り捨てシミュレーション
            levels.append({"price": price, "qty": qty})
        return levels


# ---------------------------------------------------------------------------
# FastAPI アプリ
# ---------------------------------------------------------------------------

def create_app(scenario: str = "normal") -> Any:
    """
    FastAPI アプリを生成する。

    Args:
        scenario: デフォルトシナリオ

    Returns:
        FastAPI アプリインスタンス
    """
    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.responses import JSONResponse
        from pydantic import BaseModel
    except ImportError:
        logger.error("FastAPI が未インストールです: pip install fastapi uvicorn")
        raise

    mock_server = KabuMockServer(scenario=scenario)
    app = FastAPI(title="kabu API Mock", version="1.0.0")

    class TokenRequest(BaseModel):
        APIPassword: str = "mock_password"

    @app.post("/kabusapi/token")
    def token(req: TokenRequest) -> JSONResponse:
        """APIトークン発行"""
        return JSONResponse(mock_server.get_token())

    @app.get("/kabusapi/board/{symbol}")
    def board(symbol: str, scenario_override: Optional[str] = None) -> JSONResponse:
        """板情報取得"""
        # symbol は "7203@1" 形式も受け付ける
        code = symbol.split("@")[0]
        try:
            data = mock_server.get_board(code, scenario=scenario_override)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return JSONResponse(data)

    @app.put("/kabusapi/register")
    def register(body: Dict[str, Any] = {}) -> JSONResponse:
        """PUSH配信銘柄登録（スタブ）"""
        symbols = body.get("Symbols", [])
        codes = [s.get("Symbol", "") for s in symbols if isinstance(s, dict)]
        return JSONResponse(mock_server.register_symbols(codes))

    return app


# ---------------------------------------------------------------------------
# CLI エントリポイント
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    app = create_app(scenario="normal")
    uvicorn.run(app, host="127.0.0.1", port=18081, log_level="info")

#!/usr/bin/env bash
# =============================================================================
# JP-DAYTRADE-v1 データ基盤セットアップ（5分以内完了設計）
# =============================================================================
# 用途:
#   1. SQLite スキーマ初期化（stocks_master.db, daily_prices.db, quotes_live.db）
#   2. J-Quants 認証確認（JQUANTS_REFRESH_TOKEN が設定済みか確認）
#   3. 必要パッケージの確認
#
# 実行方法:
#   cd jp-daytrade
#   bash data/setup_db.sh
#
# 環境変数:
#   JQUANTS_REFRESH_TOKEN — J-Quants リフレッシュトークン（config/.env に記載）
# =============================================================================

set -e

# カラー出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

DATA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCHEMA_DIR="${DATA_DIR}/schemas"
CONFIG_DIR="${DATA_DIR}/../config"
ENV_FILE="${CONFIG_DIR}/.env"

echo ""
echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}  JP-DAYTRADE-v1 データ基盤セットアップ${NC}"
echo -e "${BLUE}=================================================${NC}"
echo ""

START_TIME=$(date +%s)

# =============================================================================
# ステップ1: 環境確認
# =============================================================================
echo -e "${YELLOW}[1/5] 環境確認...${NC}"

# Python バージョン確認
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}ERROR: Python が見つかりません。Python 3.9+ をインストールしてください。${NC}"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
echo -e "  Python: ${GREEN}${PYTHON_VERSION}${NC}"

# sqlite3 確認
if command -v sqlite3 &>/dev/null; then
    SQLITE_VERSION=$(sqlite3 --version | awk '{print $1}')
    echo -e "  SQLite: ${GREEN}${SQLITE_VERSION}${NC}"
else
    echo -e "${YELLOW}  WARNING: sqlite3 コマンドが見つかりません（Python 経由で初期化します）${NC}"
fi

echo -e "  ${GREEN}OK${NC}"

# =============================================================================
# ステップ2: .env ファイル確認
# =============================================================================
echo ""
echo -e "${YELLOW}[2/5] 設定ファイル確認...${NC}"

mkdir -p "${CONFIG_DIR}"

if [ ! -f "${ENV_FILE}" ]; then
    echo -e "${YELLOW}  .env が存在しません。テンプレートからコピーします...${NC}"
    if [ -f "${CONFIG_DIR}/kabu_config.env.example" ]; then
        cp "${CONFIG_DIR}/kabu_config.env.example" "${ENV_FILE}"
        echo -e "  ${GREEN}config/.env を作成しました${NC}"
    else
        # テンプレートも存在しない場合は空ファイル作成
        touch "${ENV_FILE}"
        echo -e "  ${YELLOW}WARNING: env.example が見つかりません。空の .env を作成しました${NC}"
    fi
else
    echo -e "  config/.env: ${GREEN}存在します${NC}"
fi

# J-Quants トークン確認
# shellcheck disable=SC1090
source "${ENV_FILE}" 2>/dev/null || true

if [ -z "${JQUANTS_REFRESH_TOKEN}" ]; then
    echo -e ""
    echo -e "${YELLOW}  ⚠ JQUANTS_REFRESH_TOKEN が未設定です${NC}"
    echo -e "${YELLOW}  → J-Quants登録後、config/.env に以下を追記してください:${NC}"
    echo -e "${YELLOW}      JQUANTS_REFRESH_TOKEN=your_refresh_token_here${NC}"
    echo -e "${YELLOW}  → 登録URL: https://jpx.gitbook.io/j-quants-ja${NC}"
    echo -e ""
    echo -e "${BLUE}  ※ J-Quants未設定でも DB 初期化・モック開発は継続可能です${NC}"
    JQUANTS_READY=false
else
    echo -e "  JQUANTS_REFRESH_TOKEN: ${GREEN}設定済み${NC}"
    JQUANTS_READY=true
fi

# =============================================================================
# ステップ3: SQLite DB 初期化
# =============================================================================
echo ""
echo -e "${YELLOW}[3/5] SQLite DB 初期化...${NC}"

init_db_python() {
    local db_path="$1"
    local schema_file="$2"
    DB_PATH="$db_path" SCHEMA_FILE="$schema_file" $PYTHON_CMD - <<'PYEOF'
import sqlite3, os
db = os.environ["DB_PATH"]
schema = os.environ["SCHEMA_FILE"]
db_dir = os.path.dirname(db)
if db_dir:
    os.makedirs(db_dir, exist_ok=True)
with open(schema, encoding="utf-8") as f:
    sql = f.read()
with sqlite3.connect(db) as conn:
    conn.executescript(sql)
    conn.commit()
print(f"  Initialized: {db}")
PYEOF
}

# stocks_master.db
echo -e "  stocks_master.db を初期化..."
init_db_python "${DATA_DIR}/stocks_master.db" "${SCHEMA_DIR}/stocks_master.sql"

# daily_prices.db
echo -e "  daily_prices.db を初期化..."
init_db_python "${DATA_DIR}/daily_prices.db" "${SCHEMA_DIR}/daily_prices.sql"

# quotes_live.db
echo -e "  quotes_live.db を初期化..."
init_db_python "${DATA_DIR}/quotes_live.db" "${SCHEMA_DIR}/quotes_live.sql"

echo -e "  ${GREEN}DB 初期化完了${NC}"

# =============================================================================
# ステップ4: 必要パッケージ確認
# =============================================================================
echo ""
echo -e "${YELLOW}[4/5] 必要パッケージ確認...${NC}"

REQ_FILE="${DATA_DIR}/../requirements.txt"
if [ -f "${REQ_FILE}" ]; then
    MISSING=()
    # pip show で一括チェック（パッケージ名とimport名が異なる場合対応）
    while IFS= read -r pkg; do
        # コメント・空行スキップ
        [[ "${pkg}" =~ ^#.*$ ]] && continue
        [[ -z "${pkg}" ]] && continue
        # パッケージ名部分のみ抽出（pip show 用）
        PKG_NAME=$(echo "${pkg}" | sed 's/[>=<].*//' | tr -d '[:space:]')
        if ! $PYTHON_CMD -m pip show "${PKG_NAME}" >/dev/null 2>&1; then
            MISSING+=("${pkg}")
        fi
    done < "${REQ_FILE}"

    if [ ${#MISSING[@]} -gt 0 ]; then
        echo -e "${YELLOW}  未インストールパッケージ:${NC}"
        for pkg in "${MISSING[@]}"; do
            echo -e "    - ${pkg}"
        done
        echo -e "${YELLOW}  → 以下を実行してください:${NC}"
        echo -e "      pip install -r requirements.txt${NC}"
    else
        echo -e "  ${GREEN}全パッケージインストール済み${NC}"
    fi
else
    echo -e "${YELLOW}  requirements.txt が見つかりません${NC}"
fi

# =============================================================================
# ステップ5: 動作確認
# =============================================================================
echo ""
echo -e "${YELLOW}[5/5] 動作確認...${NC}"

# DB テーブル存在確認
CHECK_DATA_DIR="${DATA_DIR}" $PYTHON_CMD - <<'PYEOF'
import sqlite3, sys, os

def check_table(db_path, table_name):
    if not os.path.exists(db_path):
        return False
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        ).fetchall()
    return bool(rows)

data_dir = os.environ["CHECK_DATA_DIR"]
checks = [
    (os.path.join(data_dir, "stocks_master.db"), "stocks_master"),
    (os.path.join(data_dir, "daily_prices.db"),  "daily_prices"),
    (os.path.join(data_dir, "quotes_live.db"),   "quotes_snapshot"),
]

all_ok = True
for db_path, table in checks:
    ok = check_table(db_path, table)
    status = "OK" if ok else "FAIL"
    print(f"  [{status}] {table} ({db_path})")
    if not ok:
        all_ok = False

if not all_ok:
    print("ERROR: 一部のテーブルが存在しません")
    sys.exit(1)
PYEOF

echo -e "  ${GREEN}動作確認 OK${NC}"

# =============================================================================
# 完了レポート
# =============================================================================
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

echo ""
echo -e "${GREEN}=================================================${NC}"
echo -e "${GREEN}  セットアップ完了 (${ELAPSED}秒)${NC}"
echo -e "${GREEN}=================================================${NC}"
echo ""
echo -e "作成ファイル:"
echo -e "  ${DATA_DIR}/stocks_master.db"
echo -e "  ${DATA_DIR}/daily_prices.db"
echo -e "  ${DATA_DIR}/quotes_live.db"
echo ""

if [ "${JQUANTS_READY}" = "true" ]; then
    echo -e "${GREEN}次のステップ: J-Quants 日足データ取得${NC}"
    echo -e "  python data/jquants_client.py fetch_all_growth"
else
    echo -e "${YELLOW}次のステップ（J-Quants 設定後）:${NC}"
    echo -e "  1. config/.env に JQUANTS_REFRESH_TOKEN を追記"
    echo -e "  2. python data/jquants_client.py fetch_all_growth"
    echo ""
    echo -e "${BLUE}J-Quants設定なしで可能な作業:${NC}"
    echo -e "  - kabu API モック起動: python data/kabu_mock.py"
    echo -e "  - 気配保存テスト: python data/kabu_push_recorder.py --use-mock --no-time-window"
    echo -e "  - テスト実行: pytest tests/ -v"
fi
echo ""

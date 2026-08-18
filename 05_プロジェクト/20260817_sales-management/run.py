# -*- coding: utf-8 -*-
"""販売管理システム 起動スクリプト（社内LAN限定）。

    python run.py                # http://<このPCのIP>:8080 で起動
    SALES_DB_PATH=... python run.py

外部公開はしない。社内LANからのアクセスのみを想定している（要件定義書 5章）。
"""
from app.web import create_app

app = create_app()

if __name__ == "__main__":
    import os

    host = os.environ.get("SALES_HOST", "0.0.0.0")  # 社内LANの他PCから接続するため
    port = int(os.environ.get("SALES_PORT", "8080"))
    app.run(host=host, port=port, debug=False, threaded=True)

"""
ロギング設定

処理の進行状況を標準出力とログファイル(logs/run_YYYYmmdd_HHMMSS.log)の
両方に出力できるようにする。各stageモジュールは logging.getLogger(__name__) で
ロガーを取得し、進行状況をinfoレベルで出力する。
"""
import logging
from datetime import datetime
from pathlib import Path

_LOG_DIR = Path("logs")


def setup_logging(level: int = logging.INFO) -> Path:
    """ルートロガーを設定し、標準出力とログファイルの両方に出力するようにする。"""
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = _LOG_DIR / f"run_{datetime.now():%Y%m%d_%H%M%S}.log"

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    logging.getLogger(__name__).info("ログファイル: %s", log_file)
    return log_file

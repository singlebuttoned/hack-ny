# logger_config.py
import logging


def setup_logger():
    logging.basicConfig(
        filename="decision_maker.log",
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

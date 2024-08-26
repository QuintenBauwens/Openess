import logging

LOG_FORMAT = "%(asctime)s - %(filename)s  %(levelname)s  %(message)s"
DATE_FORMAT = "%d/%m/%Y %H:%M:%S"

class CustomFormatter(logging.Formatter):
    def format(self, record):
        file_name = record.filename.split('.')[0]

        # pad the filename to 20 characters
        record.filename = f"{file_name:<15}"
        # Pad the log level to 8 characters
        record.levelname = f"{record.levelname:<8}"
        return super().format(record)

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if not logger.hasHandlers():
        file_handler = logging.FileHandler(f"appLog.log")
        file_handler.setFormatter(CustomFormatter(LOG_FORMAT, datefmt=DATE_FORMAT))
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(CustomFormatter(LOG_FORMAT, datefmt=DATE_FORMAT))
        logger.addHandler(console_handler)
    return logger
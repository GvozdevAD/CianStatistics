import logging

def init_logging() -> logging:
    """
    Инициализирует настройки логирования.

    Настраивает глобальное логирование с уровнем INFO и определенным форматом вывода,
    включающим метку времени, уровень логирования и сообщение.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - [%(levelname)s] - %(message)s"
    )
    return logging

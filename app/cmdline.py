import argparse

from datetime import datetime
from dateutil import parser as dateutil_parser

from app.exceptions import DateRangeError


def parse_args() -> tuple[datetime, datetime]:
    """
    Разбирает аргументы командной строки для задания периода дат и проверяет корректность введенных данных.

    :return: Кортеж с двумя объектами datetime - начальной (date_from) и конечной (date_to) датой периода.
    
    :raises DateRangeError: Если дата начала больше даты окончания или диапазон дат превышает допустимое количество дней.
    """
    parser = argparse.ArgumentParser(
        description="Скрипт для получения данных от api cian по датам и записью в google sheets"
    )
    parser.add_argument(
        "-df", "--date_from", required=True, help="Дата начала периода"
    )
    parser.add_argument(
        "-dt", "--date_to", help="Дата окончания периода (по умолчанию - текущая дата)"
    )
    args = parser.parse_args()
    date_from = dateutil_parser.parse(args.date_from)
    date_to = dateutil_parser.parse(args.date_to) if args.date_to else datetime.now()
    if date_from > date_to:
        raise DateRangeError("Дата начала периода (-df) не может быть больше даты окончания периода (-dt).")
    
    max_days = 180
    if (date_to - date_from).days > max_days:
        print((date_to - date_from).days)
        raise DateRangeError(f"Ошибка: Диапазон дат не может превышать {max_days} дней.")

    return date_from, date_to

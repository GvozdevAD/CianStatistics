import json

from dataclasses import asdict
from pathlib import Path
from datetime import datetime

from .datacls import OfferStatistics


def json_alarm_record(offers: list[OfferStatistics]) -> Path:
    """
    Создает JSON-файл, содержащий данные о предложениях из списка OfferStatistics.

    :param offers: Список объектов OfferStatistics, который нужно сохранить в JSON-файл.
    :return: Путь к созданному JSON-файлу.
    """
    date_now_str = datetime.now().strftime("%d-%m-%YT%H-%M%-%S")
    name_file = Path(f"{date_now_str}_alarm_record.json")
    with open(name_file, "w", encoding="utf-8") as file:
        json.dump(
            [asdict(offer) for offer in offers], 
            file, 
            indent=4, 
            ensure_ascii=False
        )
    return name_file.absolute()

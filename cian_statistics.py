import logging

from sys import exit


from app.cian_api import CianApi
from app.cian_helpers import (
    fetch_all_my_offer_ids,
    fetch_all_my_offers_detail,
    fetch_all_my_offers_auction,
    update_my_offer_with_views_data,
    fetch_filtered_calls,
    fetch_filtered_chats,
    update_my_offer_with_calls,
    update_my_offer_with_chats
)
from app.cmdline import parse_args 
from app.exceptions import (
    DateRangeError,
    SendRequestError,
    SpreadsheetNotFound,
    WorksheetNotFound,
    YamlFileNotFound,
    UpdateWorksheetError,
    MissingPathToCreds,
    MissingSpreadsheetId,
    MissingWorksheetId,
    MissingAccessToken
)
from app.google_sheet import GoogleSheet
from app.logger import init_logging
from app.settings import (
    BUNNER,
    SettingsYamlFile
)
from app.utils import json_alarm_record


def main():
    try:
        print(BUNNER)
        logger = init_logging()
        try:
            date_from, date_to = parse_args()
        except DateRangeError as _ex:
            logger.critical(_ex)
            exit(1)
        
        logger.info(f"Дата начала: {date_from} | Дата окончания: {date_to}")    
        logger.info(f"Извлечение данных из файла с настройками!")
        try:
            settings = SettingsYamlFile().read()
        except (
            YamlFileNotFound, 
            MissingAccessToken, 
            MissingPathToCreds, 
            MissingSpreadsheetId, 
            MissingWorksheetId
        ) as _ex:
            logger.critical(_ex)
            logger.critical("Завершение работы скрипта с ошибкой!")
            exit(1)
        
        cian = CianApi(settings.cian_conf.access_token, logger=logger)

        logger.info(f"Подключение к Google Worksheet!")
        try:
            google_sheet = GoogleSheet(
                settings.google_conf.path_creds_json,
                settings.google_conf.spreadsheet_id,
                settings.google_conf.worksheet_id,
                logger
            )
        except (SpreadsheetNotFound, WorksheetNotFound) as _ex:
            logging.critical(_ex)
            exit(1)

        logger.info(f"Сбор статистики!")
        updated_offers = []
        try: 
            my_offers = fetch_all_my_offer_ids(cian, logger)
            my_offers = fetch_all_my_offers_detail(cian, my_offers, logger)
            my_offers = fetch_all_my_offers_auction(cian, my_offers, logger)
            for my_offer in my_offers:
                updated_offers.extend(
                    update_my_offer_with_views_data(
                        cian, 
                        date_from, 
                        date_to, 
                        my_offer
                    )
                )
            chats = fetch_filtered_chats(cian, date_from)
            updated_offers = update_my_offer_with_chats(
                updated_offers, chats
            )

            calls_data = fetch_filtered_calls(
                cian, 
                date_from, 
                date_to
            )
            updated_offers = update_my_offer_with_calls(
                updated_offers, 
                calls_data
            )
            updated_offers.sort(key=lambda x: x.report_date)
            
        except SendRequestError as _ex:
            logger.critical(_ex)
            logger.critical("Завершение работы скрипта с ошибкой!")
            exit(1)

        logging.info("Запись данных в таблицу Google!")

        try:
            google_sheet.update(updated_offers)
        except UpdateWorksheetError as _ex:
            logger.critical(f"Ошибка добавления данных в таблицу Google! {_ex}")
            logger.critical("Запись полученных данных в JSON!")
            name_file = json_alarm_record(updated_offers)
            logger.critical(f"Данные записаны в файл - {name_file}")
            logger.critical("Завершение работы скрипта с ошибкой!")
            exit(1)
            
        logging.info("Скрипт завершил работу!")
        exit(0)    
    except KeyboardInterrupt:
        logging.info("Остановка скрипта...")
        exit(1)

if __name__ == "__main__":
    main()
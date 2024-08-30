import logging
import gspread

from dataclasses import astuple
from pathlib import Path
from google.oauth2.service_account import Credentials


from .datacls import OfferStatistics
from .exceptions import (
    SpreadsheetNotFound,
    WorksheetNotFound,
    UpdateWorksheetError
)


class GoogleSheet:
    def __init__(
            self, 
            path_creds_json: Path,
            spreadsheet_id: str,
            worksheet_id: int,
            logger: logging.Logger
    ) -> None:
        """
        Конструктор класса GoogleSheet.

        Инициализирует соединение с Google Sheets, получает доступ к конкретной таблице
        и листу на основании переданных параметров.

        :param path_creds_json: Путь к JSON файлу с учетными данными для Google API.
        :param spreadsheet_id: Идентификатор Google таблицы.
        :param sheet_id: Идентификатор листа в Google таблице.
        :param logger: Объект логгера для ведения логов.
        """
        self.client = self.connect(path_creds_json)
        self.spreadsheet = self.get_spreadsheet(spreadsheet_id)
        self.sheet = self.get_worksheet(worksheet_id)
        self.check_headers()
    
    def connect(self, path_creds_json: Path):
        """
        Устанавливает соединение с Google API и авторизуется с помощью учетных данных.

        :param path_creds_json: Путь к JSON файлу с учетными данными для Google API.
        :return: Авторизованный клиент gspread для работы с Google Sheets.
        """
        SCOPES = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = Credentials.from_service_account_file(
            path_creds_json, 
            scopes=SCOPES
        )

        client = gspread.authorize(creds)
        return client
    
    def get_spreadsheet(
            self, 
            spreadsheet_id: str
    ) -> gspread.spreadsheet.Spreadsheet:
        """
        Получает доступ к Google таблице по ее идентификатору.

        :param spreadsheet_id: Идентификатор Google таблицы.
        :return: Объект Spreadsheet, представляющий Google таблицу.
        :raises SpreadsheetNotFound: Если таблица не найдена.
        """
        try:
            return self.client.open_by_key(spreadsheet_id)
        except gspread.exceptions.SpreadsheetNotFound:
            raise SpreadsheetNotFound("Google таблица не найдена!")
    
    def get_worksheet(self, sheet_id: int) -> gspread.worksheet.Worksheet:
        """
        Получает доступ к листу Google таблицы по его идентификатору.

        :param sheet_id: Идентификатор листа в Google таблице.
        :return: Объект Worksheet, представляющий лист таблицы.
        :raises WorksheetNotFound: Если лист с указанным ID не найден.
        """
        try:
            return self.spreadsheet.get_worksheet_by_id(sheet_id)
        except gspread.exceptions.WorksheetNotFound:
            raise WorksheetNotFound(f"Google лист c ID: {sheet_id} не найден!")

    def check_headers(self):
        """
        Проверяет наличие заголовков на листе и добавляет их, если они отсутствуют.

        Заголовки добавляются в первую строку таблицы. Если лист пустой, метод добавляет
        стандартный набор заголовков для отчетов.
        """
        data_sheet = self.sheet.get_all_values()
        if data_sheet==[[]]:
            headers = ["Дата ( за какое число собирался отчет)",
            "Ссылка на объявление",
            "id объявление",
            "Просмотры",
            "Звонки",
            "Чаты",
            "Лайки",
            "Баллы на аукцион",
            "Дата публикации объявления",
            "Тип недвижимости",
            "Предложения",
            "Адрес",
            "Площадь"]
            self.sheet.update(range_name="A1",values=[headers])
            
    def add_rows_to_sheet(self, number_of_rows: int = 1000):
        """
        Добавляет заданное количество строк в лист Google Sheets.

        Если текущих строк недостаточно для записи новых данных, метод увеличивает
        количество строк на листе.

        :param number_of_rows: Количество строк, которое нужно добавить.
        """
        current_row_count = len(self.sheet.get_all_values())
        new_row_count = current_row_count + number_of_rows
        self.sheet.resize(rows=new_row_count)

    def update(self, my_offers: list[OfferStatistics]):
        """
        Обновляет Google таблицу новыми данными.

        Вычисляет следующую доступную строку и добавляет в нее данные из списка объектов
        OfferStatistics.

        :param my_offers: Список объектов OfferStatistics, которые нужно добавить в таблицу.
        """
        try:
            data_sheet = self.sheet.get_all_values()
            if data_sheet == [[]]:
                last_row_index = 0  
            else:
                last_row_index = len(data_sheet)
            data = [astuple(offer) for offer in my_offers]
            number_of_rows_needed = last_row_index + len(data)
            if number_of_rows_needed > len(data_sheet):
                self.add_rows_to_sheet(number_of_rows_needed - len(data_sheet))
            next_row = last_row_index + 1
            cell_range = f"A{next_row}"
            self.sheet.update(range_name=cell_range, values=data)
        except gspread.exceptions.APIError as _ex:
            raise UpdateWorksheetError(_ex)
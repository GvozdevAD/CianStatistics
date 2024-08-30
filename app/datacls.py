from dataclasses import dataclass
from datetime import date

@dataclass
class OfferStatistics:
    """
    Класс для хранения статистики по объявлениям недвижимости.

    :param report_date: Дата отчета.
    :param listing_url: URL объявления.
    :param listing_id: ID объявления.
    :param views: Количество просмотров.
    :param calls: Количество звонков.
    :param chats: Количество чатов.
    :param likes: Количество лайков.
    :param auction_points: Аукционные баллы.
    :param publish_date: Дата публикации объявления.
    :param property_type: Тип недвижимости.
    :param offers: Предложения по объявлению.
    :param address: Адрес недвижимости.
    :param area: Площадь недвижимости.
    """
    report_date: str = None
    listing_url: str = None
    listing_id: int = None
    views: int = 0
    calls: int = 0
    chats: int = 0
    likes: int = 0
    auction_points: float = 0.0
    publish_date: str = None 
    property_type: str = None
    offers: str = None
    address: str = None
    area: str = None

@dataclass(frozen=True, slots=True)
class GoogleConfig:
    """
    Конфигурация для подключения к Google Sheets.

    :param path_creds_json: Путь к файлу JSON с учетными данными для Google API.
    :param spreadsheet_id: Идентификатор Google таблицы.
    :param worksheet_id: Идентификатор листа в таблице.
    """
    path_creds_json: str
    spreadsheet_id: str
    worksheet_id: int

@dataclass(frozen=True, slots=True)
class CianConfig:
    """
    Конфигурация для работы с API Cian.

    :param access_token: Токен доступа для работы с API Cian.
    """
    access_token: str

@dataclass(frozen=True, slots=True)
class Settings:
    """
    Основной класс для хранения конфигураций Google и Cian.

    :param google_conf: Конфигурация для Google Sheets.
    :param cian_conf: Конфигурация для API Cian.
    """
    google_conf: GoogleConfig
    cian_conf: CianConfig

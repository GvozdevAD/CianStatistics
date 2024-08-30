import logging
import requests

from .enums import Url
from .exceptions import SendRequestError
from .logger import init_logging


class CianApi:
    def __init__(
            self,
            access_token: str,
            host: str = Url.HOST.value,
            logger: logging = None
    ) -> None:
        """
        Конструктор класса CianApi. Инициализирует объект API-клиента для работы с публичным API Циан.

        :param access_token: Токен доступа для авторизации в API.
        :param host: URL хоста API (по умолчанию https://public-api.cian.ru).
        :param logger: Логгер для ведения журнала событий. Если не указан, используется стандартный логгер.
        """
        if not logger:
            logger = init_logging()
        self.logger = logger
        self.host = host
        self.session = self.init_session(access_token)


    def init_session(self, access_token: str) -> requests.Session:
        """
        Инициализация сессии HTTP для выполнения запросов к API с заданными заголовками.

        :param access_token: Токен доступа для авторизации в API.
        :return: Объект requests.Session с обновленными заголовками.
        """
        self.logger.info("Инициализация сессии HTTP для выполнения запросов к API с заданными заголовками")
        session = requests.session()
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        session.headers.update(headers)
        return session
    
    def __error_notification(self, response: requests.Response) -> None:
        """
        Логирование ошибок при выполнении запроса к API.

        :param response: Объект ответа requests.Response.
        """
        errors = response.json().get("result").get("errors")
        if errors:
            for error in errors:
                self.logger.error(
                    f"Ошибка в отправке запроса! Статус: {response.status_code} | "\
                    f"Code: {error.get('code')} | Key: {error.get('key')} | Msg: {error.get('message')}"
                )
        else:
            self.logger.error(
                    f"Ошибка в отправке запроса! Статус: {response.status_code}"
            )

    def __send(self, url: str, params: dict) -> dict:
        """
        Вспомогательный метод для отправки GET-запросов к API Циан с заданными параметрами.

        :param url: URL для выполнения GET-запроса.
        :param params: Параметры, которые будут переданы в запрос.
        :return: Ответ API в виде словаря, если запрос успешен.
        :raises SendRequestError: Если запрос неуспешен или произошла ошибка во время выполнения.
        """
        count_errors = 1
        while True:
            try:
                response = self.session.get(url=url, params=params)
                
            except Exception as _ex:
                raise SendRequestError(f"Ошибка: {_ex} | Url: {url}")
            
            if count_errors == 5:
                self.__error_notification(response)
                raise SendRequestError(f"Ошибка. Url: {response.url} | Status: {response.status_code}")
            
            if response.status_code == 500:
                count_errors+=1
                self.logger.warning(f"Повторная отправка запроса из за статуса 500! Попытка: {count_errors}")

            elif response.status_code != 200:
                self.__error_notification(response)
                raise SendRequestError(f"Ошибка. Url: {response.url} | Status: {response.status_code}")
            return response.json()


    def get_views_statistics_by_days(
            self, 
            date_from: str, 
            date_to: str,
            offer_id: int
    ) -> dict:
        """
        Метод возвращает статистику просмотров объявления за указанный период, 
        включая количество просмотров, показов номера телефона и добавлений в избранное.

        :param date_from: Дата начала периода (в формате YYYY-MM-DD).
        :param date_to: Дата конца периода (в формате YYYY-MM-DD).
        :param offer_id: Идентификатор объявления.
        :return: Словарь с данными статистики.
        """
        url = Url.VIEWS_STATISTICS_BY_DAYS.value
        self.logger.info(f"Отправляем запрос на {url} | offer_id: {offer_id}")
        params = {
            "dateFrom": date_from,
            "dateTo": date_to,
            "offerId": offer_id
        }
        return self.__send(url, params)

    def get_chats(
            self, 
            page: int = 1, 
            page_size: int = 100, 
            order_by: str = "updatedAt", 
            order_dir: str = "desc", 
            employee_id: int = None
    ) -> dict:
        """
        Метод позволяет получить список чатов агентства или конкретного сотрудника 
        с возможностью сортировки и пагинации.

        :param page: Номер страницы (по умолчанию 1).
        :param page_size: Количество чатов на одной странице (по умолчанию 100).
        :param order_by: Поле для сортировки чатов (по умолчанию 'updatedAt').
        :param order_dir: Направление сортировки ('asc' для возрастания, 'desc' для убывания).
        :param employee_id: Идентификатор сотрудника (необязательный параметр).
        :return: Словарь с данными чатов.
        """
        url = Url.CHATS.value 
        self.logger.info(f"Отправляем запрос на {url} | page: {page} | page size: {page_size}]")
        params = {
            "page": page,
            "page_size": page_size,
            "order_by": order_by,
            "order_dir": order_dir,
            "employee_id": employee_id
        }
        return self.__send(url, params)

    def get_my_offers(
            self,
            page: int = 1,
            page_size: int = 100,
            source: str = "manual",
            statuses: list[str] = ["published"],
            user_ids: list[int] = None
    ) -> dict:
        """
        Метод для получения списка объявлений агентства с фильтрацией по статусу, источнику и сотрудникам.

        :param page: Номер страницы выдачи (по умолчанию 1).
        :param page_size: Размер страницы выдачи (по умолчанию 100).
        :param source: Источник объявления ('manual' для ручного, 'upload' для выгруженного).
        :param statuses: Список статусов объявлений (по умолчанию ["published"], 
        возможно добавить: "inactive", "refusedByModerator", "removedByModerator").
        :param user_ids: Список идентификаторов пользователей (необязательный параметр).
        :return: Словарь с данными объявлений.
        """
        url = Url.MY_OFFERS.value
        self.logger.info(f"Отправляем запрос на {url} | page: {page} | source: {source}]")
        params = {
            "page": page,
            "pageSize": page_size,
            "source": source,
            "statuses": statuses,
            "userIds": user_ids
        }
        return self.__send(url, params)

    def get_my_offers_detail(self, offer_ids: list[int]) -> dict[dict]:
        """
        Получает детализированную информацию по списку объявлений на Циан.

        :param offer_ids: Список идентификаторов объявлений, для которых нужно получить детализированные данные.
        :return: Словарь с детализированной информацией по объявлениям.
        :raises SendRequestError: Если запрос неуспешен.
        """
        url = Url.MY_OFFERS_DETAI.value
        self.logger.info(f"Отправляем запрос на {url}")
        params = {
            "offerIds": offer_ids
        }
        return self.__send(url, params)

    def get_auction(self, offer_ids: list[int]) -> dict[dict]:
        """
        Получает информацию по ставкам аукционов для списка объявлений на Циан.

        :param offer_ids: Список идентификаторов объявлений, для которых нужно получить данные по аукционам.
        :return: Словарь с информацией по аукционам для указанных объявлений.
        :raises SendRequestError: Если запрос неуспешен.
        """
        url = Url.AUCTION.value
        self.logger.info(f"Отправляем запрос на {url}")
        params = {
            "offerIds": offer_ids
        }
        return self.__send(url, params)

    def get_calls_report(
            self,
            page: int = 1,
            page_size: int = 50,
            date_from: str = None,
            date_to: str = None,
            employee_id: int = None
    ) -> dict[dict]: 
        """ 
        Метод позволяет получить отчёт по звонкам с фильтрацией по датам и ID сотрудника, с привязкой к конкретным объявлениям.
        :param page: 
        :param page_size:
        :param date_from:
        :param date_to:
        :param employee_id:

        """
        url = Url.CALLS_REPORT.value
        self.logger.info(f"Отправляем запрос на {url}")
        params = {
            "dateFrom": date_from,
            "dateTo": date_to,
            "employeeId": employee_id,
            "page" : page,
            "pageSize": page_size,
        }
        return self.__send(url, params)

        
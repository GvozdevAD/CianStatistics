import copy
import logging
import re
import time

from collections import defaultdict, Counter
from datetime import datetime, timezone
from dateutil import parser as dateutil_parser
from itertools import islice

from .cian_api import CianApi
from .datacls import OfferStatistics

# Регулярное выражение для извлечения типа недвижимости и площади из строки
PATTERN = r'(.+?),\s(.+?\s(?:м²|сот\.))'

def chunk_list(data, chunk_size):
    """
    Разделяет список на подсписки с заданным размером.
    
    :param data: Исходный список данных.
    :param chunk_size: Размер подсписка.
    :return: Генератор подсписков заданного размера.
    """
    it = iter(data)
    for _ in range(0, len(data), chunk_size):
        yield list(islice(it, chunk_size))

def fetch_all_my_offer_ids(
        cian: CianApi, 
        logger: logging
) -> list[OfferStatistics]:
    """
    Получает все идентификаторы объявлений пользователя из всех источников ('upload' и 'manual').

    :param cian: Объект класса CianApi для взаимодействия с API Cian.
    :param logger: Логгер для записи ошибок.
    :return: Список объектов OfferStatistics с информацией о идентификаторах объявлений и датах публикации.
    """
    my_offers_id = []
    
    for source in ["upload", "manual"]:
        page = 1
        while True:
            try:
                response = cian.get_my_offers(page=page, source=source)
                result = response.get("result").get("announcements")
                
                if not result:
                    break
                
                my_offers_id.extend(
                    [
                        OfferStatistics(
                            listing_id =offer.get("id"), 
                            publish_date = dateutil_parser.parse(
                                offer.get("creationDate")
                            ).strftime("%d.%m.%Y %H:%M:%S")
                        )  
                        for offer in result
                    ]
                )
                page += 1
                time.sleep(0.2)
            except Exception as _ex:
                logger.error(f"Ошибка при получении объявлений: {_ex}")
                break

    return my_offers_id

def fetch_all_my_offers_detail(
        cian: CianApi, 
        offers: list[OfferStatistics], 
        logger: logging
) -> list[OfferStatistics]:
    """
    Получает детальную информацию по каждому объявлению из списка.

    :param cian: Объект класса CianApi для взаимодействия с API Cian.
    :param offers: Список объектов OfferStatistics с идентификаторами объявлений.
    :param logger: Логгер для записи ошибок и предупреждений.
    :return: Список объектов OfferStatistics с обновленной информацией по каждому объявлению.
    """
    offers_dict = {offer.listing_id: offer for offer in offers}
    for chunk in chunk_list(offers, 100):
        result = cian.get_my_offers_detail(
            [offer.listing_id for offer in chunk]
        )
        for offer_detail in result.get("result").get("offers"):
            offer = offers_dict[offer_detail.get("id")]
            url_offer = offer_detail.get("url")
            
            if "rent" in url_offer:  
                offer.offers = "Аренда"
            elif "sale" in url_offer:
                offer.offers = "Продажа"
            else:
                logging.warning(f"Не удалось найти offers: url - {url_offer}")

            match = re.match(PATTERN, offer_detail.get("title"))
            if match:
                offer.property_type = match.group(1).strip()
                offer.area = match.group(2).strip().replace('\xa0', ' ')
            else:
                logging.warning(f"Не удалось тип и площадь: title - {offer_detail.get('title')} ")
            
            offer.listing_url = url_offer
            offer.address = offer_detail.get("address")
        time.sleep(0.2)

    return list(offers_dict.values())
        
def fetch_all_my_offers_auction(
        cian: CianApi,
        offers: list[OfferStatistics],
        logger: logging
) -> list[OfferStatistics]:
    """
    Получает информацию об аукционах по списку предложений и обновляет информацию в offers.

    :param cian: Объект класса CianApi для взаимодействия с API Cian.
    :param offers: Список объектов OfferStatistics с идентификаторами объявлений.
    :param logger: Логгер для записи ошибок.
    :return: Список объектов OfferStatistics с обновленной информацией об аукционах.
    """
    offers_dict = {offer.listing_id: offer for offer in offers}
    for chunk in chunk_list(offers, 20):  
        result = cian.get_auction([offer.listing_id for offer in chunk])
        for offer_auction in result.get("result").get("items"):
            offer = offers_dict[offer_auction.get("offerId")]
            offer.auction_points = offer_auction.get("currentBet")

        
        time.sleep(0.2)

    return list(offers_dict.values())

def update_my_offer_with_views_data(
        cian: CianApi,
        date_from: datetime,
        date_to: datetime,
        offer: OfferStatistics, 
) -> list[OfferStatistics]:
    """
    Обновляет объект OfferStatistics данными о просмотрах и добавлениях в избранное за период.

    :param cian: Экземпляр класса CianApi для взаимодействия с API.
    :param date_from: Дата начала периода для получения статистики.
    :param date_to: Дата окончания периода для получения статистики.
    :param offer: Объект OfferStatistics, который нужно обновить.
    
    :return: Список клонированных и обновленных объектов OfferStatistics, по одному на каждый день статистики.
    """
    result = cian.get_views_statistics_by_days(
        date_from.strftime("%Y-%m-%d"),
        date_to.strftime("%Y-%m-%d"),
        offer.listing_id
    )
    views_by_days = result['result'].get('viewsByDays')
    favorites_by_days = result['result'].get('addToFavoritesByDays')

    favorites_dict = {entry['date']: entry['addToFavorites'] for entry in favorites_by_days}
    
    updated_offers = []
    for view_data in views_by_days:
        cloned_offer = copy.deepcopy(offer)
        cloned_offer.report_date = dateutil_parser.parse(
            view_data['date']
        ).strftime("%d.%m.%Y")
        cloned_offer.views = view_data['views']
        cloned_offer.likes = favorites_dict.get(view_data['date'])
        updated_offers.append(cloned_offer)
    time.sleep(0.2)
    return updated_offers

def fetch_filtered_chats(
        cian: CianApi, 
        date_from: datetime, 
        page_size: int = 50
) -> list[dict]:
    """
    Получает все свежие чаты с сервера CianApi постранично, начиная с первой страницы.
    
    Прерывает загрузку, если дата последнего обновления чата (updatedAt) больше или равна указанной date_from.
    
    Возвращает список словарей с полями chatId, updatedAt и offerId для всех отфильтрованных чатов.
    
    :param cian: Экземпляр класса CianApi для взаимодействия с API.
    :param date_from: Дата, до которой нужно получить данные (чаты).
    :param page_size: Размер страницы для пагинации.
    :return: Список словарей с полями chatId, updatedAt и offerId для всех отфильтрованных чатов.
    """
    all_chats = []
    page = 1
    loop = True
    if date_from.tzinfo is None:
        date_from = date_from.replace(tzinfo=timezone.utc)
    
    while loop:
        all_msg = cian.get_chats(page, page_size=page_size)
        chats = all_msg.get("result").get("chats")
        if not chats:
            break
        for chat in chats:
            updated_at = dateutil_parser.parse(chat.get("updatedAt"))
            if updated_at <= date_from:
                loop = False
                break
            
            if chat.get("lastMessage").get("direction") != "in":
                continue
            
            chat_data = {
                "chatId": chat.get("chatId"),
                "updatedAt": updated_at.strftime("%d.%m.%Y"),
                "offerId": chat.get("offer", {}).get("id")
            }
            all_chats.append(chat_data)
        page += 1
    return all_chats


def update_my_offer_with_chats(
        offers: list[OfferStatistics], 
        chats: list[dict]
) -> list[OfferStatistics]:
    """
    Обновляет объекты OfferStatistics, добавляя количество чатов за период.

    :param offer_statistics: Список объектов OfferStatistics.
    :param chats: Список словарей с информацией о чатах, содержащих chatId, updatedAt и offerId.
    :return: Обновленный список объектов OfferStatistics.
    """
    for chat in chats:
        for offer_stat in offers:
            if (offer_stat.listing_id == chat["offerId"] and 
                offer_stat.report_date == chat["updatedAt"]
            ):
                offer_stat.chats += 1
    return offers

def fetch_filtered_calls(
        cian: CianApi,
        date_from: datetime,
        date_to: datetime,
        page_size: int = 50
) -> dict[int, list[str]]:
    """
    Получает данные о звонках с фильтрацией по статусу и дате, разбивая их на страницы.

    :param cian: Экземпляр класса CianApi для взаимодействия с API.
    :param date_from: Дата начала периода для фильтрации звонков.
    :param date_to: Дата окончания периода для фильтрации звонков.
    :param page_size: Количество элементов на одной странице (по умолчанию 50).
    
    :return: Словарь, где ключом является ID объявления (offer_id), 
             а значением - список строк, содержащих даты звонков в формате "DD.MM.YYYY".
    """
    page = 1
    calls_data = defaultdict(list)
    while True:
        response = cian.get_calls_report(
            page, 
            page_size, 
            date_from.strftime("%Y-%m-%d"), 
            date_to.strftime("%Y-%m-%d")
        )
        calls_response = response.get("result").get("calls")
        if not calls_response:
            break
        for call in calls_response:
            if call.get("status") != "success":
                continue
            if not call.get("offer"):
                continue
            calls_data[call.get("offer").get("id")].append(
                dateutil_parser.parse(
                    call.get("date")
                ).strftime("%d.%m.%Y")
            )
        page+=1
        
    return calls_data

def update_my_offer_with_calls(
        offers: list[OfferStatistics],
        calls_data: dict[int, list]
) -> list[OfferStatistics]:
    """
    Обновляет объекты OfferStatistics количеством звонков за конкретную дату.

    :param offers: Список объектов OfferStatistics.
    :param calls_data: Словарь, где ключом является ID объявления (listing_id),
                       а значением - список строк с датами звонков в формате "DD.MM.YYYY".
    
    :return: Обновленный список объектов OfferStatistics с добавленным количеством звонков.
    """
    for offer in offers:
        if offer.listing_id in calls_data:
            calls_list = Counter(calls_data.get(offer.listing_id))
            if offer.report_date in calls_list:
                offer.calls = calls_data.get(offer.report_date)
            for date_call, count_call in calls_list.items():
                if offer.report_date == date_call:
                    offer.calls = count_call
                    break
    return offers

    
        
        

    
    
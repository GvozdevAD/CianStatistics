from enum import Enum

class Url(str,Enum):
    HOST = "https://public-api.cian.ru"
    VIEWS_STATISTICS_BY_DAYS = f"{HOST}/v1/get-views-statistics-by-days"
    CHATS = f"{HOST}/v1/get-chats"
    MY_OFFERS = f"{HOST}/v2/get-my-offers"
    MY_OFFERS_DETAI = f"{HOST}/v1/get-my-offers-detail"
    AUCTION = f"{HOST}/v1/get-auction"
    CALLS_REPORT = f"{HOST}/v2/get-calls-report"
    
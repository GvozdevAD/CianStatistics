# CianStatistics

## Описание
Этот скрипт предназначен для сбора статистики по объявлениям с платформы Cian и записи этих данных в Google таблицы.

## Настройка

1. Файл с ключами и настройками для таблицы находится по пути `app/settings.yaml`.   
В этом файле необходимо указать следующие параметры:
```yaml
Google:
  path_creds_json: Путь до файла JSON с учетными данными Google API
  spreadsheet_id: ID вашей Google таблицы
  worksheet_id: ID листа таблицы 
Cian:
  access_token: Ваш ключ для доступа к API Cian
```

2. После установки всех зависимостей, вы можете запустить скрипт. Для этого нужно передать два параметра:
    * Первый параметр — дата, с которой начинается сбор статистики (в формате DD-MM-YYYY или DD.MM.YYYY или YYYY-MM-DD).  
    * Второй параметр — дата, до которой нужно собрать данные (этот параметр можно не указывать, тогда будет использована текущая дата).  
    
    **Важно:** Запрашиваемый период не должен превышать `180 дней`. Если диапазон дат больше, нужно уменьшить его до допустимого предела.  
    
    Пример команды запуска:
    ```bash
    env/bin/python3 cian_statistics.py -df 20.08.2024 -dt 23.08.2024
    ```
    Если не указать вторую дату, команда будет выглядеть так:
    ```bash
    env/bin/python3 cian_statistics.py -df 20.08.2024 
    ```

## Установка 
1. Установите все зависимости проекта:
    ```bash 
    pip install -r requirements.txt
    ```
2. Заполните файл `app/settings.yaml` с необходимыми ключами и настройками, как указано выше.
3. Запустите скрипт с нужными параметрами для сбора данных.

## Пример таблицы
| Дата         | Ссылка на объявление | id объявление | Просмотры | Звонки | Чаты | Лайки | Баллы на аукцион | Дата публикации объявления  | Тип недвижимости                | Предложения | Адрес                                          | Площадь       |
|--------------|----------------------|---------------|-----------|--------|------|-------|------------------|-----------------------------|---------------------------------|-------------|------------------------------------------------|---------------|
| 20.08.2024   | URL                  | 444444444     | 21        | 5      | 2    | 4     | 8193.0           | 01.01.2024 19:43:55         | Офис                            | Аренда      | Москва, переулок Хользунова, 6                 | 1120 м²       |
| 20.08.2024   | URL                  | 111111111     | 1         | 0      | 0    | 1     | 19.5             | 02.02.2024 17:43:58         | Офис                            | Аренда      | Смоленская область, Рославль, улица Ленина, 5  | 302 м²        |
| 20.08.2024   | URL                  | 222222222     | 2         | 1      | 0    | 1     | 0                | 03.03.2024 15:51:48         | Здание                          | Аренда      | Костромская область, Галич, улица Советская, 8 | 6300 м²       |
| 20.08.2024   | URL                  | 333333333     | 10        | 0      | 3    | 4     | 0                | 04.04.2024 13:54:33         | Помещение свободного назначения | Продажа     | Тульская область, Венёв, улица Гагарина, 4     | 20 - 280,2 м² |

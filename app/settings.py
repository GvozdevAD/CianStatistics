import yaml

from pathlib import Path

from .datacls import (
    CianConfig,
    GoogleConfig,
    Settings,
)

from .exceptions import (
    YamlFileNotFound,
    MissingPathToCreds,
    MissingSpreadsheetId,
    MissingWorksheetId,
    MissingAccessToken
)


BUNNER = """
  _         _                     
 / `._  _  /_`_/__ _/_. __/_._   _
/_,//_|/ /._/ / /_|/ /_\ / //_ _\ 
                                  
"""


class SettingsYamlFile:
    def __init__(
        self,
        path: Path = Path("app", "settings.yaml")
    ) -> None:
        """
        Конструктор класса SettingsYamlFile.

        Инициализирует объект настроек, загружая данные из YAML файла.

        :param path: Путь к YAML файлу с настройками. По умолчанию "appd/settings.yaml".
        :raises YamlFileNotFound: Если указанный файл настроек не найден.
        """
        self.path = path
        try:
            with open(path) as f:
                self.__settings = yaml.safe_load(f)
        except FileNotFoundError:
            raise YamlFileNotFound(f"Файл с настройками по следующему пути: {path} не найден!")

    def read(self) -> Settings:
        """
        Преобразует загруженные настройки в объекты Settings, GoogleConfig и CianConfig.

        :return: Объект Settings, содержащий конфигурации Google и Cian.
        """
        path_to_creds = Path(self.__settings.get("Google").get("path_creds_json"))
        if not path_to_creds.exists():
            raise MissingPathToCreds("Указаный путь до файла JSON с учетными данными Google API не существует!")
        
        spreadsheet_id = self.__settings.get("Google").get("spreadsheet_id")
        if not spreadsheet_id:
            raise MissingSpreadsheetId("ID вашей Google таблицы не указан в файле settings.yaml!")

        worksheet_id = self.__settings.get("Google").get("worksheet_id")
        if not worksheet_id:
            raise MissingWorksheetId("Id листа таблицы не указан в файле settings.yaml!")

        access_token = self.__settings.get("Cian").get("access_token")
        if not access_token:
            raise MissingAccessToken("Отсутсвует ключ для доступа к API Cian!")

        return Settings(
            GoogleConfig(
                path_to_creds,
                spreadsheet_id,
                worksheet_id
            ),
            CianConfig(
               access_token
            )
        )

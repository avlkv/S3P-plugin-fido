"""
Нагрузка плагина SPP

1/2 документ плагина
"""
import logging
import time
import dateparser
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from src.spp.types import SPP_document
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class FIDO:
    """
    Класс парсера плагина SPP

    :warning Все необходимое для работы парсера должно находится внутри этого класса

    :_content_document: Это список объектов документа. При старте класса этот список должен обнулиться,
                        а затем по мере обработки источника - заполняться.


    """

    SOURCE_NAME = 'fido'
    _content_document: list[SPP_document]

    def __init__(self, webdriver: WebDriver, categories: dict, last_document: SPP_document = None, max_count_documents: int = 100,
                 num_scrolls: int = 25, *args, **kwargs):
        """
        Конструктор класса парсера

        По умолчанию внего ничего не передается, но если требуется (например: driver селениума), то нужно будет
        заполнить конфигурацию
        """
        # Обнуление списка
        self._content_document = []
        self.CATEGORIES = categories
        self.NUM_SCROLLS = num_scrolls
        self.driver = webdriver
        self.wait = WebDriverWait(self.driver, timeout=20)
        self.max_count_documents = max_count_documents
        self.last_document = last_document

        # Логер должен подключаться так. Вся настройка лежит на платформе
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug(f"Parser class init completed")
        self.logger.info(f"Set source: {self.SOURCE_NAME}")
        ...

    def content(self) -> list[SPP_document]:
        """
        Главный метод парсера. Его будет вызывать платформа. Он вызывает метод _parse и возвращает список документов
        :return:
        :rtype:
        """
        self.logger.debug("Parse process start")
        self._parse()
        self.logger.debug("Parse process finished")
        return self._content_document

    def _parse(self):
        """
        Метод, занимающийся парсингом. Он добавляет в _content_document документы, которые получилось обработать
        :return:
        :rtype:
        """
        # HOST - это главная ссылка на источник, по которому будет "бегать" парсер
        self.logger.debug(F"Parser enter")

        # Должно быть два конфига: файловый и нативный
        # categories = {'FIDO News Center': 'https://fidoalliance.org/content/fido-news-center/',   - NATIVE
        #               'FIDO Case Studies': 'https://fidoalliance.org/content/case-study/',        - FILE
        #                       (заголовок и аннотация со страницы FIDO, а текст из файла)
        #               'FIDO In the News': 'https://fidoalliance.org/content/fido-in-the-news/',   - NATIVE
        #                       (нужно переходить к прикрепленным ссылкам и сохранять оттуда весь контент, а в аннотацию
        #                         то, что было написано на странице FIDO, заголовок тоже с FIDO)
        #               'FIDO Presentations': 'https://fidoalliance.org/content/presentation/',     - NATIVE
        #               'FIDO White Papers': 'https://fidoalliance.org/content/white-paper/'}       - FILE
        #                       (заголовок и аннотация со страницы FIDO, а текст из файла)
        for category in self.CATEGORIES:

            self.driver.get(self.CATEGORIES[category])

            scroll_counter = 0

            try:

                doc_table = self.driver.find_elements(By.TAG_NAME, '//li[contains(@class,\'card-products\')]')
                last_doc_table_len = len(doc_table)

                while True:
                    # Scroll down to bottom
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    scroll_counter += 1
                    # self.logger.info(f"counter = {counter}")

                    # Wait to load page
                    time.sleep(1)

                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                    # Wait to load page
                    time.sleep(1)

                    doc_table = self.driver.find_elements(By.TAG_NAME, '//li[contains(@class,\'card-products\')]')
                    new_doc_table_len = len(doc_table)
                    if last_doc_table_len == new_doc_table_len:
                        break
                    if scroll_counter > self.NUM_SCROLLS:
                        flag = False
                        break

            except Exception as e:
                self.logger.debug('Не удалось найти scroll')
                break

            self.logger.debug(f'Обработка списка элементов ({len(doc_table)})...')

            for doc in doc_table:




        # ---
        # ========================================
        ...

    @staticmethod
    def _find_document_text_for_logger(doc: SPP_document):
        """
        Единый для всех парсеров метод, который подготовит на основе SPP_document строку для логера
        :param doc: Документ, полученный парсером во время своей работы
        :type doc:
        :return: Строка для логера на основе документа
        :rtype:
        """
        return f"Find document | name: {doc.title} | link to web: {doc.web_link} | publication date: {doc.pub_date}"

    @staticmethod
    def some_necessary_method():
        """
        Если для парсинга нужен какой-то метод, то его нужно писать в классе.

        Например: конвертация дат и времени, конвертация версий документов и т. д.
        :return:
        :rtype:
        """
        ...

    @staticmethod
    def nasty_download(driver, path: str, url: str) -> str:
        """
        Метод для "противных" источников. Для разных источника он может отличаться.
        Но основной его задачей является:
            доведение driver селениума до файла непосредственно.

            Например: пройти куки, ввод форм и т. п.

        Метод скачивает документ по пути, указанному в driver, и возвращает имя файла, который был сохранен
        :param driver: WebInstallDriver, должен быть с настроенным местом скачивания
        :_type driver: WebInstallDriver
        :param url:
        :_type url:
        :return:
        :rtype:
        """

        with driver:
            driver.set_page_load_timeout(40)
            driver.get(url=url)
            time.sleep(1)

            # ========================================
            # Тут должен находится блок кода, отвечающий за конкретный источник
            # -
            # ---
            # ========================================

            # Ожидание полной загрузки файла
            while not os.path.exists(path + '/' + url.split('/')[-1]):
                time.sleep(1)

            if os.path.isfile(path + '/' + url.split('/')[-1]):
                # filename
                return url.split('/')[-1]
            else:
                return ""

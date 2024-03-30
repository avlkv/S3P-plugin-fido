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

    def __init__(self, webdriver: WebDriver, source_type: str, categories: dict, last_document: SPP_document = None,
                 max_count_documents: int = 100,
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
        if source_type:
            self.SOURCE_TYPE = source_type
        else:
            raise ValueError('source_type must be a type of source: "FILE" or "NATIVE"')
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
        try:
            self._parse()
        except Exception as e:
            self.logger.debug(f'Parsing stopped with error: {e}')
        else:
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
        #
        #               'FIDO Case Studies': 'https://fidoalliance.org/content/case-study/',        - FILE
        #                       (заголовок и аннотация со страницы FIDO, а текст из файла)
        #
        #               'FIDO In the News': 'https://fidoalliance.org/content/fido-in-the-news/',   - NATIVE
        #                       (нужно переходить к прикрепленным ссылкам и сохранять оттуда весь контент, а в аннотацию
        #                         то, что было написано на странице FIDO, заголовок тоже с FIDO)
        #
        #               'FIDO Presentations': 'https://fidoalliance.org/content/presentation/',     - NATIVE
        #
        #               'FIDO White Papers': 'https://fidoalliance.org/content/white-paper/'}       - FILE
        #                       (заголовок и аннотация со страницы FIDO, а текст из файла)

        for category in self.CATEGORIES:

            self.driver.get(self.CATEGORIES[category])

            scroll_counter = 0

            try:
                time.sleep(3)

                self.close_popup()
                doc_table = self.driver.find_elements(By.XPATH, '//li[contains(@class,\'card-products\')]')
                last_doc_table_len = len(doc_table)

                while True:
                    # Scroll down to bottom
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    scroll_counter += 1
                    # self.logger.info(f"counter = {counter}")

                    # Wait to load page
                    time.sleep(3)

                    self.close_popup()

                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                    # Wait to load page
                    time.sleep(1)

                    doc_table = self.driver.find_elements(By.XPATH, '//li[contains(@class,\'card-products\')]')
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
                doc_link = doc.find_element(By.XPATH, './/h2/a').get_attribute('href')

                self.driver.execute_script("window.open('');")
                self.driver.switch_to.window(self.driver.window_handles[1])

                self.driver.get(doc_link)
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.wp-block-post-title')))

                self.logger.debug(f'Entered: {doc_link}')

                title = self.driver.find_element(By.XPATH, "//h1[contains(@class,'wp-block-post-title\')]").text

                pub_date = dateparser.parse(
                    self.driver.find_element(By.XPATH, "//h1[contains(@class,'wp-block-post-title')]/../..//time").text)

                if self.SOURCE_TYPE == 'NATIVE':

                    text_content = self.driver.find_element(By.XPATH,
                                                            "//div[contains(@class,'wp-block-post-content')]").text

                    abstract = None

                    web_link = doc_link

                    other_data = {'category': category}

                elif self.SOURCE_TYPE == 'FILE':

                    try:
                        abstract = self.driver.find_element(By.XPATH,
                                                            "//div[contains(@class,'wp-block-post-content')]").text
                        web_link = self.driver.find_element(By.XPATH,
                                                            "//div[@class='wp-block-button']/a").get_attribute('href')
                        text_content = None

                        other_data = {'category': category, 'fido_link': doc_link}

                    except:
                        web_link = doc_link
                        abstract = None
                        text_content = self.driver.find_element(By.XPATH,
                                                                "//div[contains(@class,'wp-block-post-content')]").text

                        other_data = {'category': category}

                else:
                    self.logger.info('Неизвестный тип источника SOURCE_TYPE')
                    raise ValueError('source_type must be a type of source: "FILE" or "NATIVE"')

                doc = SPP_document(None,
                                   title,
                                   abstract,
                                   text_content,
                                   web_link,
                                   None,
                                   other_data,
                                   pub_date,
                                   datetime.now())

                self.find_document(doc)

                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])

    def close_popup(self):

        try:
            # close_btn = self.driver.find_element(By.XPATH, "//span[@class = 'hustle-icon-close']")
            close_btn = self.driver.find_element(By.XPATH, "//button[contains(@class,'hustle-button-close')]")
            try:
                close_btn.click()
            except Exception as e:
                self.logger.debug(f"Can't click the close button in popup with Exception: {e}")
        except:
            self.logger.debug('Popup not found')

    @staticmethod
    def _find_document_text_for_logger(self, doc: SPP_document):
        """
        Единый для всех парсеров метод, который подготовит на основе SPP_document строку для логера
        :param doc: Документ, полученный парсером во время своей работы
        :type doc:
        :return: Строка для логера на основе документа
        :rtype:
        """
        return f"Find document | name: {doc.title} | link to web: {doc.web_link} | publication date: {doc.pub_date}"

    def find_document(self, _doc: SPP_document):
        """
        Метод для обработки найденного документа источника
        """
        if self.last_document and self.last_document.hash == _doc.hash:
            raise Exception(f"Find already existing document ({self.last_document})")

        if self.max_count_documents and len(self._content_document) >= self.max_count_documents:
            raise Exception(f"Max count articles reached ({self.max_count_documents})")

        self._content_document.append(_doc)
        self.logger.info(self._find_document_text_for_logger(self, _doc))

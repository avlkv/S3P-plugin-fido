from selenium import webdriver
from logging import config
from fido import FIDO
import pickle
import pandas

from src.spp.types import SPP_document

config.fileConfig('dev.logger.conf')


def driver():
    """
    Selenium web driver
    """
    options = webdriver.ChromeOptions()

    # Параметр для того, чтобы браузер не открывался.
    # options.add_argument('headless')

    options.add_argument('window-size=1920x1080')
    options.add_argument("disable-gpu")

    return webdriver.Chrome(options)


def to_dict(doc: SPP_document) -> dict:
    return {
        'title': doc.title,
        'abstract': doc.abstract,
        'text': doc.text,
        'web_link': doc.web_link,
        'local_link': doc.local_link,
        'other_data': doc.other_data.get('category') if doc.other_data.get('category') else '',
        'pub_date': str(doc.pub_date.timestamp()) if doc.pub_date else '',
        'load_date': str(doc.load_date.timestamp()) if doc.load_date else '',
    }


native_categories = {'FIDO News Center': 'https://fidoalliance.org/content/fido-news-center/',
                     'FIDO In the News': 'https://fidoalliance.org/content/fido-in-the-news/',
                     'FIDO Presentations': 'https://fidoalliance.org/content/presentation/'}

file_categories = {'FIDO Case Studies': 'https://fidoalliance.org/content/case-study/',
                   'FIDO White Papers': 'https://fidoalliance.org/content/white-paper/'}

parser = FIDO(driver(), max_count_documents=2, categories=native_categories, num_scrolls=1, source_type='NATIVE')
docs: list[SPP_document] = parser.content()

try:
    with open('backup/documents.backup.pkl', 'wb') as file:
        pickle.dump(docs, file)
except Exception as e:
    print(e)

try:
    dataframe = pandas.DataFrame.from_records([to_dict(d) for d in docs])
    dataframe.to_csv('out/fido_documents.csv')
except Exception as e:
    print(e)

print(*docs, sep='\n\r\n')
print(len(docs))

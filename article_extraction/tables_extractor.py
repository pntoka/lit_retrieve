import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
import re
import captions_extractor

def nature_table(soup)->list[dict]:
    tables = soup.find_all('a', attrs={'data-test': 'table-link'})
    table_dicts = []
    for table in tables:
        table_dict = {}
        label = table['aria-label']
        table_dict['label'] = label
        table_link = table['href']
        table_link = urljoin('https://www.nature.com', table_link)
        html = requests.get(table_link).text
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find('table')
        text = str(table)
        table_dict['content'] = text
        table_dicts.append(table_dict)
    return table_dicts

def springer_table(soup)->list[dict]:
    tables = soup.find_all('a', attrs={'data-test': 'table-link'})
    table_dicts = []
    for table in tables:
        table_dict = {}
        label = table['aria-label']
        table_dict['label'] = label
        table_link = table['href']
        table_link = urljoin('https://link.springer.com/', table_link)
        html = requests.get(table_link).text
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find('table')
        text = str(table)
        table_dict['content'] = text
        table_dicts.append(table_dict)
    return table_dicts

def rsc_table(soup):
    tables = soup.find_all('table', class_='tgroup')
    table_list = []
    for table in tables:
        table_dict = {}
        label = table.find_parent('div', class_='rtable__wrapper') \
                    .find_previous_sibling('div', class_='table_caption').find('b').text
        table_dict['label'] = label
        text = str(table)
        table_dict['content'] = text
        table_list.append(table_dict)

    return table_list

def acs_table(soup):
    tables = soup.find_all('table', class_='table')
    table_list = []
    for table in tables:
        table_dict = {}
        label = table.find_parent('div', class_='NLM_table-wrap').get('id')
        table_dict['label'] = label
        text = str(table)
        table_dict['content'] = text
        table_list.append(table_dict)

    return table_list

def science_table(soup):
    tables = soup.find_all('table')
    table_dicts = []
    for table in tables:
        table_dict = {}
        label = table.find_parent('figure', class_='table').get('id')
        table_dict['label'] = label
        table_dict['content'] = str(table)
        table_dicts.append(table_dict)
    return table_dicts

def mdpi_table(soup):
    divs = soup.find_all('div', class_='html-table_show')
    table_dicts = []
    for div in divs:
        table_dict = {}
        label = div.find('b').get_text()
        table_dict['label'] = label
        table_dict['content'] = str(div.find('table'))
        table_dicts.append(table_dict)
    return table_dicts

def wiley_table_xml(soup):
    tables = soup.find_all('tabular', attrs={'xml:id': True})
    tables_dicts = []
    for table in tables:
        table_dict = {}
        table_dict['content'] = str(table.find('table'))
        label = table.get('xml:id')
        table_dict['label'] = "Table " + re.search(r'0*([1-9]\d*)$', label).group(1)
        tables_dicts.append(table_dict)
    return tables_dicts

def wiley_table(soup):
    if soup.find('component', attrs={'xml:id': True}) is not None:
        return wiley_table_xml(soup)
    tables = soup.find_all('div', class_='article-table-content')
    table_dicts = []
    for table in tables:
        table_dict = {}
        table_content = str(table.find('table'))
        table_dict['content'] = table_content
        table_label = table.find('header').find('span').get_text().strip()
        table_dict['label'] = table_label
        table_dicts.append(table_dict)
    return table_dicts

def tandf_table(soup):
    script = soup.find("script", string=lambda s: s and "tandf.tfviewerdata" in s)
    data = json.loads(re.search(r"tandf\.tfviewerdata\s*=\s*({.*});", script.string, re.S).group(1))
    tables = data["tables"]
    table_dicts = []
    for table in tables:
        table_dict = {}
        tbl_soup = BeautifulSoup(table["content"], "html.parser")
        table_element = tbl_soup.find("table")
        table_dict['content'] = str(table_element)
        caption = tbl_soup.find("caption")
        label_span = caption.find("span", class_="captionLabel") if caption else None
        label_text = label_span.get_text(" ", strip=True) if label_span else caption.get_text(" ", strip=True).split(".")[0] + "."
        table_dict['label'] = label_text
        table_dicts.append(table_dict)
    return table_dicts

def elsevier_table(soup):
    tables = soup.find_all('tgroup')
    table_dicts = []
    for table in tables:
        table_dict = {}
        label = table.find_previous_sibling('ce:label').get_text()
        table_dict['label'] = label
        text = str(table)
        content = re.sub(r'\s+xmlns="[^"]*"', '', text)
        table_dict['content'] = content
        table_dicts.append(table_dict)
    return table_dicts
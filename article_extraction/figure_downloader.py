# download figures based on figure labels (e.g., 'Fig. 1', 'Scheme 2', 'Figure 3', etc.)

import io
import json
import os
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from PIL import Image


def springer_nature_figure(soup: BeautifulSoup, labels: list[str]) -> list[str]:
    '''for nature and springer articles'''
    urls = []
    for l in labels:
        number = re.search(r'\d+', l).group()
        l = f"figure-{number}-desc"
        alt_l = f"Fig{number}"
        img = soup.find('img', attrs={"aria-describedby": lambda text: text and (l or alt_l in text), "src": True})
        src = img.get('src')
        url = urljoin('https://www.springernature.com/', src)
        full_image_url = re.sub(
            r'(?<=springernature\.com/).*?(?=/springer-static)',
            'full',
            url
        )
        urls.append(full_image_url)
    return urls

def science_figure(soup: BeautifulSoup, labels: list[str]) -> list[str]:
    numbers = [int(re.search(r'\d+', s).group()) for s in labels]
    ids = [f'F{n}' for n in numbers]
    tags = soup.find_all('div', class_='figure-wrap')
    urls = []
    for tag in tags:
        figure_id = tag.find('figure').get('id')
        if figure_id in ids:
            src = tag.find('img').get('src')
            url = urljoin('https://www.science.org', src)
            urls.append(url)
    return urls

def acs_figure(soup, figure_labels: list[str]) -> list[str | None]:
    urls = []
    
    for label in figure_labels:
        # Extract number from label (e.g., 'Fig. 1' -> '1', 'Scheme 2' -> '2')
        match = re.search(r'\d+', label)
        if not match:
            continue
        
        num = match.group()
        src = None
        
        # Determine if it's a Scheme or Figure and set the id accordingly
        if 'scheme' in label.lower():
            fig_id = f'sch{num}'
        elif 'fig' in label.lower():
            fig_id = f'fig{num}'
        else:
            continue
        
        # Find the figure element by id
        figure = soup.find('figure', id=fig_id)
        if figure:
            img = figure.find('img')
            if img:
                src = img.get('data-lg-src')
                src = urljoin('https://pubs.acs.org', src)
        
        urls.append(src)
    
    return urls

def rsc_figure(soup, labels: list[str]) -> list[str | None]:
    urls = []
    
    for label in labels:
        # Extract number from label (e.g., 'Fig. 1' -> '1', 'Scheme 2' -> '2')
        match = re.search(r'\d+', label)
        if not match:
            continue
        
        num = match.group()
        src = None
        
        # Determine if it's a Scheme or Figure and set the id accordingly
        if 'scheme' in label.lower():
            figure = soup.find('td', id=f"imgsch{num}")
            if figure:
                img = figure.find('a')
                if img:
                    src = img.get('href')
                    src = urljoin('https://pubs.rsc.org', src)
                    urls.append(src)
        elif 'fig' in label.lower():
            figure = soup.find('td', id=f"imgfig{num}")
            img = figure.find('a')
            if img:
                src = img.get('href')
                src = urljoin('https://pubs.rsc.org', src)
                urls.append(src)
        else:
            continue   
    return urls

def wiley_process_figure_labels(labels):
    '''Function to create the correct fig and scheme ids from fig labels'''
    ids = []
    for lbl in labels:
        if lbl.lower().startswith('fig'):
            num = re.search(r'\d+', lbl).group()
            ids.append(f'fig-000{num}')
        elif lbl.lower().startswith('scheme'):
            num = re.search(r'\d+', lbl).group()
            ids.append(f'fig-500{num}')
    return ids

def wiley_figure(soup: BeautifulSoup, labels: list[str]) -> list[str]:
    if soup.find('component', attrs={'xml:id': True}) is not None:
        urls = []  # cant get image links from xml format of articles so return empty list
        return urls
    ids = wiley_process_figure_labels(labels)
    urls = []
    for i in ids:
        figure = soup.find("figure", id=lambda t: t and f"{i}" in t)
        a = figure.find('a')
        url = a.get('href')
        url = urljoin('https://onlinelibrary.wiley.com/', url)
        urls.append(url)
    return urls

def tandf_figure(soup: BeautifulSoup, labels: list[str]) -> list[str]:
    script = soup.find("script", string=re.compile("tandf.tfviewerdata"))
    data = json.loads(
        re.search(r"tandf\.tfviewerdata\s*=\s*(\{.*\});", script.string, re.S).group(1)
    )
    urls = []
    for l in labels:
        match = re.search(r'\d+', l)
        if l.lower().startswith('scheme'):
            num = match.group()   # sometimes the id is upper case, sometimes lowercase, so we check both
            content = next(f["content"] for f in data["figures"] if f["id"].lower() == f'sch000{num}')

        elif l.lower().startswith('fig'):
            num = match.group()
            content = next(f["content"] for f in data["figures"] if f["id"].lower() == f'f000{num}')
        src = BeautifulSoup(content, "html.parser").img["src"]
        url = urljoin('https://www.tandfonline.com/', src)
        urls.append(url)

    return urls

def elsevier_figure(soup, labels: list[str]) -> list[str]:
    urls = []
    for l in labels:
        match = re.search(r'\d+', l)
        num = match.group()
        if 'scheme' in l.lower():
            fig_id = f'sc{num}'
        elif 'fig' in l.lower():
            fig_id = f'gr{num}'
        figure = soup.find('object', type='IMAGE-DOWNSAMPLED', ref = fig_id)
        src = figure.get_text()
        figure_identifier = src.split("eid/")[1].split("?")[0]
        url = 'https://ars.els-cdn.com/content/image/' + figure_identifier
        url = url.replace(".jpg", "_lrg.jpg")
        urls.append(url)
    return urls

def mdpi_figure(soup, labels: list[str]) -> list[str]:
    urls = []
    for l in labels:
        match = re.search(r'\d+', l)
        num = match.group()
        if 'scheme' in l.lower():
            id = f'Scheme {num}'
            a = soup.find("a", string=id)
        elif 'fig' in l.lower():
            id = f'Figure {num}'
        a = soup.find("a", title=lambda t: t and f"{id}" in t)
        url = a.get('href')
        url = urljoin('https://www.mdpi.com/', url)
        urls.append(url)
    return urls

def download_urls(urls, driver) -> list[Image.Image]: 
    """driver: Selenium WebDriver. Must be run in headful mode."""
    imgs = []
    for url in urls:
        try:
            driver.get(url)
            img = bytes(driver.execute_script("""
                const resp = await fetch(window.location.href);
                const buf = await resp.arrayBuffer();
                return Array.from(new Uint8Array(buf));
            """))
            img = Image.open(io.BytesIO(img))
            imgs.append(img)
        except Exception as e:
            print(f"Error downloading {url}: {e}")
    return imgs

def save_figure(soup, doi, labels, driver=None) -> list[Image.Image]:
    """
    retrieve figure based on figure labels
    based on publisher inferred from DOI prefix.
    """
    prefix_to_pub = {
        "10.1039": "RSC",
        "10.1021": "ACS",
        "10.1038": "Nature",
        "10.1126": "Science",
        "10.3390": "MDPI",
        "10.1002": "Wiley",
        "10.1007": "Springer",
        "10.1080": "TandF",
        "10.1016": "Elsevier",
    }

    handlers = {
        "ACS":       (lambda soup, labels: acs_figure(soup, labels), (AttributeError, IndexError)),
        "Science":   (lambda soup, labels: science_figure(soup, labels), (AttributeError, IndexError)),
        "Springer":  (lambda soup, labels: nature_figure(soup, labels), (AttributeError, IndexError)),
        "Nature":    (lambda soup, labels: nature_figure(soup, labels), (AttributeError, IndexError)),
        "TandF":     (lambda soup, labels: tandf_figure(soup, labels), (AttributeError, IndexError)),
        "MDPI":      (lambda soup, labels: mdpi_figure(soup, labels), (AttributeError, IndexError)),
        "RSC":       (lambda soup, labels: rsc_figure(soup, labels), (AttributeError, StopIteration)),
        "Elsevier":  (lambda soup, labels: elsevier_figure(soup, labels), (AttributeError,)),
        "Wiley":     (lambda soup, labels: wiley_figure(soup, labels), (AttributeError,)),
    }

    prefix = doi[:7]
    pub = prefix_to_pub.get(prefix)

    handler, excs = handlers[pub]

    try:
        urls = handler(soup, labels)
        imgs = download_urls(urls, driver)
        return imgs
    except excs as e:
        print(f"Error with {pub}:", e)
        return None


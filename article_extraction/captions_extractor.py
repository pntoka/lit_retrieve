from bs4 import BeautifulSoup
import re

import extractor_tools as tools

def mdpi_captions(soup):
    '''MDPI (old RSC/MDPI shared HTML pattern - RSC moved to a new layout, see rsc_captions below)'''
    captions = []
    for cap in soup.find_all(["td"], class_=lambda c: c and "image_title" in c.lower()):
        captions.append(cap.get_text(strip=False).replace('\n', ' '))  # change to strip=False to preserve space between figure number and caption
    # commenting this out as this returns table captions
    for cap in soup.find_all(["div", "p"], class_=lambda c: c and "caption" in c.lower()):
        captions.append(cap.get_text(strip=False).replace('\n', ' '))  # change to strip=False to preserve space between figure number and caption
    captions = list(dict.fromkeys(captions))
    results = structure_figure_captions(captions)
    return results

# Old RSC captions extractor (pre-2025 HTML layout, no longer works - RSC moved to Silverchair).
# Shared with MDPI, which still uses this HTML pattern - see mdpi_captions above.
# def rsc_captions(soup):
#     '''RSC, MDPI'''
#     captions = []
#     for cap in soup.find_all(["td"], class_=lambda c: c and "image_title" in c.lower()):
#         captions.append(cap.get_text(strip=False).replace('\n', ' '))
#     for cap in soup.find_all(["div", "p"], class_=lambda c: c and "caption" in c.lower()):
#         captions.append(cap.get_text(strip=False).replace('\n', ' '))
#     captions = list(dict.fromkeys(captions))
#     results = structure_figure_captions(captions)
#     return results

def _clean_text(element):
    '''Text of an element with all internal whitespace collapsed to single spaces'''
    return tools.clean_text(element)

def _silverchair_captions(soup):
    '''
    Figure and table captions from the Silverchair layout, shared by RSC (2024+)
    and ACS (2025+). Only div.fig-section is read, so the duplicate div.fig-modal
    copy ACS renders for its lightbox is ignored.
    '''
    captions = []
    for fig in soup.find_all('div', class_='fig-section'):
        if fig.get('data-id') == 'ga':
            continue  # skip graphical/visual abstract
        # ACS carries two labels; the one in graphic-bottom is the one matching the caption
        label = fig.select_one('div.graphic-bottom div.label.fig-label')
        if label is None:
            label = fig.find('div', class_='fig-label')
        cap = fig.find('div', class_='fig-caption')
        if label is None or cap is None:
            continue
        captions.append(_clean_text(label) + ' ' + _clean_text(cap))
    for wrap in soup.find_all('div', class_='table-wrap'):
        title = wrap.find('div', class_='table-wrap-title')
        if title is None:
            continue
        label = title.find('span', class_='label')
        cap = title.find('div', class_='caption')
        if label is None or cap is None:
            continue
        captions.append(_clean_text(label) + ' ' + _clean_text(cap))
    captions = list(dict.fromkeys(captions))
    results = structure_figure_captions(captions)
    return results

def rsc_captions(soup):
    '''RSC (Silverchair layout, 2024+)'''
    return _silverchair_captions(soup)

def acs_captions(soup):
    '''ACS (Silverchair layout, 2025+)'''
    return _silverchair_captions(soup)

def tandf_captions(soup):
    captions = []
    for cap in soup.find_all(["div", "p"], class_=lambda c: c and "caption" in c.lower()):
        captions.append(cap.get_text(strip=False).replace('\n', ' '))
    captions = list(dict.fromkeys(captions))
    results = structure_figure_captions(captions)
    return results

# Old ACS captions extractor (pre-2025 Atypon layout, no longer works - ACS moved to
# Silverchair, see acs_captions above). Frontiers still uses this HTML pattern.
def frontiers_captions(soup):
    '''Frontiers (also the pre-2025 ACS Atypon layout)'''
    captions = []
    for fig in soup.find_all('figure', id = True):
        id = fig.get('id')
        if id.startswith('fig'):
            cap = fig.find('p').get_text(strip=True)
            captions.append(cap)
        elif id.startswith('sch'):
            texts = fig.find('div', class_='title2').get_text(strip=True)
            captions.append(texts)
    for tab in soup.find_all('div', class_='NLM_caption'):
        cap = tab.get_text(strip=True)
        captions.append(cap)
    captions = list(dict.fromkeys(captions)) 
    captions = [c for c in captions if c.lstrip().lower().startswith(("figure", "table", "scheme"))]
    results = structure_figure_captions(captions)
    return results

def springer_nature_captions(soup):
    soup = soup.find('main') # have to use main body of article to avoid repetitions
    captions = []
    for cap in soup.find_all("figcaption"):
        figure = cap.parent
        subcap = figure.find("div", {"data-test": "bottom-caption"})
        if subcap:
            p_tag = subcap.find("p")
            p_text = p_tag.get_text(separator=" ", strip=True) if p_tag else ""
            caption = cap.get_text(strip=True) + " " + p_text
            captions.append(caption)
        else:
            captions.append(cap.get_text(strip=True))
    for cap in soup.find_all("caption"):
        captions.append(cap.get_text(strip=True))
    captions = list(dict.fromkeys(captions))
    results = structure_figure_captions(captions)

    return results

def science_captions(soup):
    captions = []
    for cap in soup.find_all("figcaption"):
        text = cap.get_text(strip=True)
        text = text.replace('\xa0', '')
        captions.append(text)
    captions = list(dict.fromkeys(captions))
    results = structure_figure_captions(captions)

    return results

def wiley_captions_xml(soup):
    captions = []
    for cap in soup.find_all('figure', attrs={'xml:id': True}):
        title_tag = cap.find('title')
        label = cap.get('xml:id')
        processed_label = re.search(r'0*([1-9]\d*)$', label)
        caption = cap.find('caption')
        if label and caption:
            text = title_tag.get_text(strip=True) + " " + processed_label.group(1) + " " + caption.get_text(strip=True)
            captions.append(text)
    for cap in soup.find_all('tabular', attrs={'xml:id': True}):
        title_tag = cap.find('title')
        label = cap.get('xml:id')
        processed_label = re.search(r'0*([1-9]\d*)$', label)
        text = "Table " + processed_label.group(1) + " " + title_tag.get_text(strip=True)
        captions.append(text)
    captions = list(dict.fromkeys(captions))
    results = structure_figure_captions(captions)
    return results

def wiley_captions(soup):
    if soup.find('component', attrs={'xml:id': True}) is not None:
        return wiley_captions_xml(soup)
    captions = []
    for cap in soup.find_all(["header"], class_=lambda c: c and "caption" in c.lower()):
        captions.append(cap.get_text(strip=False).replace('\n', ' '))  # change to strip=False to preserve space between figure number and caption
    for cap in soup.find_all("figcaption"):
        text = cap.get_text(strip=False).replace('Open in figure viewerPowerPoint', '').replace('\n', ' ') 
        captions.append(text)
    captions = list(dict.fromkeys(captions))
    results = structure_figure_captions(captions)
    return results

def springer_captions(soup):
    captions = []
    for cap in soup.find_all(["div"], class_=lambda c: c and "figure" in c.lower()):
        captions.append(cap.get_text(strip=True))
    for cap in soup.find_all("figcaption"):
        captions.append(cap.get_text(strip=True))
    captions = [c for c in captions if c.lstrip().lower().startswith(("fig.", "table"))] #remove strings that do not start with "Fig." or "Table"
    captions = [c for c in captions if len(c) >= 8]
    captions = list(dict.fromkeys(captions))
    results = structure_figure_captions(captions)
    return results

def elsevier_captions(soup):
    '''Elsevier, Springer'''
    valid_label = re.compile(r'^(Fig\.?|Figure|Table|Scheme)\b', re.IGNORECASE)
    captions = []
    for label in soup.find_all("ce:label"):
        figure_number = label.get_text(strip=True)
        if not valid_label.match(figure_number):
            continue
        caption_tag = label.find_next("ce:caption")
        if caption_tag:
            cap = figure_number + " " + caption_tag.get_text(strip=True)
            captions.append(cap)

    results = structure_figure_captions(captions)
    return results

def concat_strings(captions):
    tables_caps = []
    fig_caps = []
    for c in captions:
        if c.lower().startswith('table'):
            tables_caps.append(c.strip())
        else:
            fig_caps.append(c.strip())

    # fig_caps = []
    # for c in captions:
    #     if c not in tables_caps:
    #         fig_caps.append(c.strip())

    return tables_caps, fig_caps

def structure_figure_captions(captions):
    tables_caps, figures_caps = concat_strings(captions)
    results = []
    if figures_caps:
        result_figure = {
            "name": "Figures",
            "type": "captions",
            "content": figures_caps
        }
        results.append(result_figure)

    if tables_caps:
        result_tables = {
            "name": "Tables",
            "content": tables_caps
        }
        results.append(result_tables)

    return results






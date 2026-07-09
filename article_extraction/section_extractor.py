'''
Functions to extract sections from html/xml files from different publishers
'''

import re

import extractor_tools as tools

def list_to_content_springer(list, list_remove):
    '''
    Function to extract paragraphs embedded between h3 headings (specific to Springer/Nature)
    '''
    data = []
    for element in list:
        if element.name == 'p':
            element_clean = tools.remove_tags_soup(element, list_remove)
            data.append(element_clean.text)
        elif element.name == 'h3':
            return data
    return data
    
def list_to_content_frontiers(list):
    '''
    Function to extract paragraphs in between h3 and h2 headings (specific to Frontiers)
    '''
    data = []
    for element in list:
        if element.name == 'p':
            data.append(element.text)
        elif element.name == 'h3' or element.name == 'h2':
            return data
    return data
    
def subheadings_content_frontiers(list):
    '''
    Function to extract h3 subheadings and paragraphs in between h2 hesadings (specific to Frontiers)
    '''
    data = []
    for i in range(len(list)):
        if list[i].name == 'h3':
            data_sub = {}
            data_sub['name'] = list[i].text
            data_sub['type'] = 'h3'
            data_sub['content'] = list_to_content_frontiers(list[i+1:])
            data.append(data_sub)
        elif list[i].name == 'h2':
            return data
    return data
    
def sections_acs_letters(soup, list_remove):
    '''Extract sections from ACS Letters articles'''
    main_content = soup.find('div', class_= 'article_content')
    first_paragraph = main_content.find('p')
    paragraphs = first_paragraph.find_next_siblings('p')
    paragraphs.insert(0, first_paragraph)
    paragraphs_text = []
    for paragraph in paragraphs:
        paragraph_clean = tools.remove_tags_soup(paragraph, list_remove)
        paragraphs_text.append(paragraph_clean.text)
    return paragraphs_text

def sections_acs(soup, list_remove):
    paragraph_tags = {'name':'div', 'class':['NLM_p last','NLM_p']}
    main_content = soup.find('div', class_= 'article_content')
    sections = main_content.find_all('div', class_='NLM_sec NLM_sec_level_1')
    if sections == []:
        data_dict = sections_acs_letters(soup, list_remove)
        return data_dict
    data_dict = []
    for section in sections:
        data = {}
        data['name'] = section.find('h2').text
        data['type'] = 'h2'
        data['content'] = []
        if section.find('div', class_ = 'NLM_sec NLM_sec_level_2') is not None:
            elements = section.find_all('div', class_ = 'NLM_sec NLM_sec_level_2')
            for element in elements:
                data_sub = {}    
                data_sub['name'] = element.find('h3').text
                data_sub['type'] = 'h3'
                data_sub['content'] = []
                paragraphs = tools.find_paragraphs(element, paragraph_tags)
                paragraphs = tools.remove_tags_soup_list(paragraphs, list_remove)
                for paragraph in paragraphs:
                    data_sub['content'].append(paragraph.text)
                data['content'].append(data_sub)
        else:
            paragraphs = tools.find_paragraphs(section, paragraph_tags)
            paragraphs = tools.remove_tags_soup_list(paragraphs, list_remove)
            for paragraph in paragraphs:
                data['content'].append(paragraph.text)
        data_dict.append(data)
    return data_dict
    
def sections_wiley(soup, list_remove):
    '''
    Function to get sections from Wiley xml journals
    '''
    clean_body = tools.remove_tags_soup(soup.body, list_remove)
    section_1 = clean_body.section                              
    sections_clean = section_1.find_next_siblings('section')    #gets all sections that are siblings of the first section (main sections)
    sections_clean.insert(0,section_1)
    data_dict = []
    for section in sections_clean:
        data = {}
        data['name'] = section.find('title').text
        data['type'] = section.name
        data['content'] = []
        if section.find('section') is not None:
            if section.find_all(['section','p'])[0].name == 'p':  #deals with paragraphs before subheadings
                data_sub = {}
                data_sub['name'] = section.find('title').text
                data_sub['type'] = section.name
                data_sub['content'] = [section.find('p').text]
                for paragraph in section.p.find_next_siblings('p'):
                    data_sub['content'].append(paragraph.text)
                data['content'].append(data_sub)
            sub_sections = section.find_all('section')
            for element in sub_sections:
                data_sub = {}
                data_sub['content'] = []                           #deals with subheadings and their paragraphs
                data_sub['name'] = element.find('title').text
                data_sub['type'] = element.name
                paragraphs = tools.find_paragraphs(element, {'name':'p'})
                for paragraph in paragraphs:
                    data_sub['content'].append(paragraph.text)
                data['content'].append(data_sub)
        else:
            paragraphs = tools.find_paragraphs(section, {'name':'p'})
            for paragraph in paragraphs:
                data['content'].append(paragraph.text)
        data_dict.append(data)
    return data_dict

def sections_wiley_html_letters(soup, list_remove):
    '''Function to extract sections from Wiley html Letters articles'''
    main_content = soup.find('section', 'article-section article-section__full')
    sections = main_content.find('section', 'article-section__content')
    first_paragraph = sections.find('p')
    paragraphs = first_paragraph.find_next_siblings('p')
    paragraphs.insert(0, first_paragraph)
    paragraphs_text = []
    for paragraph in paragraphs:
        paragraph_clean = tools.remove_tags_soup(paragraph, list_remove)
        paragraphs_text.append(paragraph_clean.text)
    return paragraphs_text


def sections_wiley_html(soup, list_remove):
    '''
    Function to get sections from Wiley html file
    '''
    paragraph_tags = [{'name': 'p'}, {'name': 'div', 'class' : 'paragraph-element'}]
    main_content = soup.find('section', 'article-section article-section__full')
    sections = main_content.find_all('section', 'article-section__content')
    data_dict = []
    if sections[0].find('h2') is None:   # deals with letters which don't have headings
        data_dict = sections_wiley_html_letters(soup, list_remove)
        return data_dict
    for section in sections:
        data = {}
        data['name'] = section.find('h2').text
        data['type'] = 'h2'
        data['content'] = []
        if section.find('h3') is not None:
            section_clean = tools.remove_tags_soup(section, list_remove)
            if section_clean.find_all(['p','section'])[0].name == 'p':
                data_sub = {}                                           #deals with paragraphs before subheadings
                data_sub['name'] = section.find('h2').text
                data_sub['type'] = 'h2'
                data_sub['content'] = [section_clean.find('p').text]
                for paragraph in section_clean.p.find_next_siblings('p'):
                    data_sub['content'].append(paragraph.text)
                data['content'].append(data_sub)
            sub_element = section_clean.find('section', 'article-section__sub-content')
            if sub_element is not None:
                sub_elements = sub_element.find_next_siblings('section', 'article-section__sub-content') # using siblings as there may be sub-sub-sections
                sub_elements.insert(0, sub_element)
                for sub_element in sub_elements:
                    data_sub = {}
                    data_sub['name'] = sub_element.find('h3').text
                    data_sub['type'] = 'h3'
                    data_sub['content'] = []
                    if sub_element.find('section', 'article-section__sub-content'):
                        if sub_element.find_all(['p','section'])[0].name == 'p':
                            data_sub['content'].append(sub_element.find('p').text)
                            for paragraph in sub_element.p.find_next_siblings('p'):  # deals with paragraphs before sub-sub-sections
                                data_sub['content'].append(paragraph.text)
                        data_sub_sub_elements = sub_element.find_all('section', 'article-section__sub-content')
                        for sub_sub_element in data_sub_sub_elements:
                            data_sub_sub = {}
                            data_sub_sub['name'] = sub_sub_element.find('h4').text
                            data_sub_sub['type'] = 'h4'
                            data_sub_sub['content'] = []
                            paragraphs = tools.find_paragraphs_list(sub_sub_element, paragraph_tags)
                            for paragraph in paragraphs:
                                data_sub_sub['content'].append(paragraph.text)
                            data_sub['content'].append(data_sub_sub)
                    else:
                        paragraphs = tools.find_paragraphs_list(sub_element, paragraph_tags)
                        for paragraph in paragraphs:
                            data_sub['content'].append(paragraph.text)
                    data['content'].append(data_sub)
        else:
            section_clean = tools.remove_tags_soup(section, list_remove)
            paragraphs = tools.find_paragraphs_list(section_clean, paragraph_tags)
            for paragraph in paragraphs:
                data['content'].append(paragraph.text)
        data_dict.append(data)
    return data_dict

def sections_springer_nature(soup, list_remove):
    '''
    Function to get sections from Springer and Nature html journals
    '''
    main_content = soup.body.find_all('div', 'main-content')
    sections = main_content[0].find_all('section')
    data_dict = []
    for section in sections:
        data = {}
        data['name'] = section.find('h2').text
        data['type'] = 'h2'
        data['content'] = []
        if section.find('h3') is not None:
            section_clean = tools.remove_tags_soup(section, list_remove)
            elements = section_clean.find_all(['h3','p'])
            if elements[0].name == 'p':
                data_sub = {}                                           #deals with paragraphs before subheadings
                data_sub['name'] = section.find('h2').text
                data_sub['type'] = 'h2'
                data_sub['content'] = [elements[0].text]
                for i in range(1,len(elements)):
                    if elements[i].name == 'p':
                        data_sub['content'].append(elements[i].text)
                    else:
                        break
                data['content'].append(data_sub)
            for i in range(len(elements)):
                if elements[i].name == 'h3':
                    data_sub = {}
                    data_sub['name'] = elements[i].text
                    data_sub['type'] = 'h3'
                    data_sub['content'] = list_to_content_springer(elements[i+1:], list_remove)
                    data['content'].append(data_sub)
        else:
            section_clean = tools.remove_tags_soup(section, list_remove)
            for paragraph in section_clean.find_all('p'):
                paragraph_clean = tools.remove_tags_soup(paragraph, list_remove)
                data['content'].append(paragraph_clean.text)
        data_dict.append(data)
    return data_dict

def sections_frontiers(soup, list_remove):
    '''
    Function to extract sections from Frontiers html journals
    '''
    # TODO: Update Frontiers HTML parsing as new webpage format has been implemented
    # New webpage contains all sections in div class=ArticleContent whit div id="h1" containing abstract
    main_content = soup.find('div', class_='JournalFullText')
    main_content = main_content.find('div', class_='JournalFullText')  # old format had two nested divs with class JournalFullText
    main_content = tools.remove_tags_soup(main_content, list_remove)
    elements = main_content.find_all(['p','h2','h3'])
    data_dict = []
    for i in range(len(elements)):
        if elements[i].name == 'h2':
            data = {}
            data['name'] = elements[i].text
            data['type'] = 'h2'
            data['content'] = []
            if elements[i].next_sibling is not None:
                if elements[i].next_sibling.name == 'p':
                    data['content'] = list_to_content_frontiers(elements[i+1:])
            if elements[i].next_sibling is not None:
                if elements[i].next_sibling.name == 'h3':
                    data['content']= subheadings_content_frontiers(elements[i+1:])
            data_dict.append(data)
    return data_dict

def sections_tandf(soup, list_remove):
    '''
    Function to extract sections from Taylor and Francis html journals
    '''
    main_content = soup.find('div', class_ = 'hlFld-Fulltext')
    sections = main_content.find_all('div', class_ = ['NLM_sec NLM_sec_level_1', 'NLM_sec NLM_sec-type_intro NLM_sec_level_1',
                                                      'NLM_sec NLM_sec-type_results NLM_sec_level_1', 'NLM_sec NLM_sec-type_conclusions NLM_sec_level_1',
                                                      'NLM_sec NLM_sec-type_other NLM_sec_level_1', 'NLM_sec NLM_sec-type_results|discussion NLM_sec_level_1'])
    sections_clean = tools.remove_tags_soup_list(sections, list_remove)
    data_dict = []
    for section in sections_clean:
        data = {}
        data['name'] = section.find('h2').text
        data['type'] = 'h2'
        data['content'] = []
        if section.find('div', class_ = 'NLM_sec NLM_sec_level_2') is not None:
            elements = section.find_all('div', class_ = 'NLM_sec NLM_sec_level_2') 
            for element in elements:
                if element.find('div', class_ = 'NLM_sec NLM_sec_level_3') is not None:     #deals with h4 subheadings in subsection
                    data_sub = {}
                    data_sub['name'] = element.find('h3').text
                    data_sub['type'] = 'h3'
                    data_sub['content'] = []                                    
                    first_paragraph = element.p
                    paragraphs = first_paragraph.find_next_siblings('p')       #gets content before h4 subheadings
                    paragraphs.insert(0, first_paragraph)
                    for paragraph in paragraphs:
                        data_sub['content'].append(paragraph.text)
                    data['content'].append(data_sub)
                    sub_elements = element.find_all('div', class_ = 'NLM_sec NLM_sec_level_3')
                    for sub_element in sub_elements:
                        data_sub = {}
                        data_sub['name'] = sub_element.find('h4').text
                        data_sub['type'] = 'h4'                                 #gets content of h4 subheadings
                        data_sub['content'] = []
                        first_paragraph = sub_element.p
                        paragraphs = first_paragraph.find_next_siblings('p')
                        paragraphs.insert(0, first_paragraph)
                        for paragraph in paragraphs:
                            data_sub['content'].append(paragraph.text)
                        data['content'].append(data_sub)
                else:
                    data_sub = {}
                    data_sub['name'] = element.find('h3').text
                    data_sub['type'] = 'h3'
                    data_sub['content'] = []
                    paragraphs = tools.find_paragraphs(element, {'name':'p'})
                    # paragraphs = remove_tags_soup_list(paragraphs, {'name':'button'})
                    for paragraph in paragraphs:
                        data_sub['content'].append(paragraph.text)
                    data['content'].append(data_sub)
        else:
            paragraphs = tools.find_paragraphs(section, {'name':'p'})
            for paragraph in paragraphs:
                data['content'].append(paragraph.text)
        data_dict.append(data)
    return data_dict

def sections_mdpi_legacy(soup, list_remove):
    '''
    Function to extract sections from old format of MDPI html journals
    '''
    main_content = soup.find('div', class_= 'html-body')
    section_1 = main_content.find('section')                #get main sections based on first section
    sections = section_1.find_next_siblings('section')
    sections.insert(0,section_1)
    data_dict = []
    for section in sections:
        data = {}
        data['name'] = section.find('h2').text
        data['type'] = 'h2'
        data['content'] = []
        if section.find('section') is not None:
            sub_sections_1 = section.find('section')
            sub_sections = sub_sections_1.find_next_siblings('section')
            sub_sections.insert(0,sub_sections_1)
            for sub_section in sub_sections:
                data_sub = {}
                if sub_section.find('h3') is not None:
                    data_sub['name'] = sub_section.find('h3').text
                    data_sub['type'] = 'h3'
                elif sub_section.find('h4') is not None:
                    data_sub['name'] = sub_section.find('h4').text
                    data_sub['type'] = 'h4'
                data_sub['content'] = []
                if sub_section.find('section') is not None:
                    sub_sub_sections = sub_section.find_all('section')
                    for sub_sub_section in sub_sub_sections:                #deal with sub-sub-sections
                        data_sub_sub = {}
                        data_sub_sub['name'] = sub_sub_section.find('h4').text
                        data_sub_sub['type'] = 'h4'
                        data_sub_sub['content'] = []
                        paragraphs = tools.find_paragraphs(sub_sub_section,{'name':'div', 'class':'html-p'})
                        paragraphs_clean = tools.remove_tags_soup_list(paragraphs, list_remove)
                        for paragraph in paragraphs_clean:
                            data_sub_sub['content'].append(paragraph.text)
                        data_sub['content'].append(data_sub_sub)
                else:                                       
                    paragraphs = tools.find_paragraphs(sub_section,{'name':'div', 'class':'html-p'})  #deals with subsections without sub-sub-sections
                    paragraphs_clean = tools.remove_tags_soup_list(paragraphs, list_remove)
                    for paragraph in paragraphs_clean:
                        data_sub['content'].append(paragraph.text)
                data['content'].append(data_sub)
        else:
            paragraphs = tools.find_paragraphs(section,{'name':'div', 'class':'html-p'})
            paragraphs_clean = tools.remove_tags_soup_list(paragraphs, list_remove)
            for paragraph in paragraphs_clean:
                data['content'].append(paragraph.text)
        data_dict.append(data)
    return data_dict

def sections_mdpi(soup, list_remove):
    '''
    Function to extract sections from new format of MDPI html journals
    '''
    main_content = soup.find('div', id='article-contents')
    section_1 = main_content.find('div', id='html-graphical').find_next_sibling('div')
    sections = section_1.find_next_siblings('div')
    sections.insert(0, section_1)
    data_dict = []
    for section in sections:
        section_content = section.find('section')
        data = {}
        data['name'] = section_content.find('h2').text
        data['type'] = 'h2'
        data['content'] = []
        if section_content.find('section') is not None:
            sub_sections_1 = section_content.find('section')
            sub_sections = sub_sections_1.find_next_siblings('section')
            sub_sections.insert(0, sub_sections_1)
            for sub_section in sub_sections:
                data_sub = {}
                if sub_section.find('h3') is not None:
                    data_sub['name'] = sub_section.find('h3').text
                    data_sub['type'] = 'h3'
                elif sub_section.find('h4') is not None:
                    data_sub['name'] = sub_section.find('h4').text
                    data_sub['type'] = 'h4'
                data_sub['content'] = []
                if sub_section.find('section') is not None:
                    sub_sub_sections = sub_section.find_all('section')
                    for sub_sub_section in sub_sub_sections:
                        data_sub_sub = {}
                        data_sub_sub['name'] = sub_sub_section.find('h4').text
                        data_sub_sub['type'] = 'h4'
                        data_sub_sub['content'] = []
                        paragraphs = tools.find_paragraphs(sub_sub_section, {'name':'div', 'class':'html-p'})
                        paragraphs_clean = tools.remove_tags_soup_list(paragraphs, list_remove)
                        for paragraph in paragraphs_clean:
                            data_sub_sub['content'].append(paragraph.text)
                        data_sub['content'].append(data_sub_sub)
                else:
                    paragraphs = tools.find_paragraphs(sub_section, {'name':'div', 'class':'html-p'})
                    paragraphs_clean = tools.remove_tags_soup_list(paragraphs, list_remove)
                    for paragraph in paragraphs_clean:
                        data_sub['content'].append(paragraph.text)
                data['content'].append(data_sub)
        else:
            paragraphs = tools.find_paragraphs(section_content, {'name':'div', 'class':'html-p'})
            paragraphs_clean = tools.remove_tags_soup_list(paragraphs, list_remove)
            for paragraph in paragraphs_clean:
                data['content'].append(paragraph.text)
        data_dict.append(data)
        if "Conclusions" in data['name']:
            break
    return data_dict

_RSC_EXCLUDE_HEADING_CLASSES = {
    'backacknowledgements-title',
    'backreferences-title',
    'dataavailabilitystatement-title',
}
_RSC_EXCLUDE_HEADING_TEXT = re.compile(
    r'^(acknowledge?ments?|(notes and )?references?|author contributions?|conflicts? of interest|data availability( statement)?)$',
    re.IGNORECASE
)

def _rsc_excluded_heading(heading):
    '''Back-matter headings (acknowledgements, references, etc.) to exclude from RSC sections'''
    if _RSC_EXCLUDE_HEADING_CLASSES & set(heading.get('class', [])):
        return True
    return bool(_RSC_EXCLUDE_HEADING_TEXT.match(heading.get_text(strip=True)))

def _rsc_paragraphs(content_div):
    '''
    Extract paragraph text from the article-section-wrapper children of a heading's
    content div, skipping wrappers that hold a figure or table (handled separately)
    '''
    texts = []
    for wrapper in content_div.find_all('div', class_='article-section-wrapper', recursive=False):
        if wrapper.find('div', class_='fig-section') is not None:
            continue
        if wrapper.find('div', class_='table-wrap') is not None:
            continue
        for p in wrapper.find_all('p', recursive=False):
            text = p.get_text(strip=True)
            if text:
                texts.append(text)
    return texts

def sections_rsc(soup):
    '''
    Function to extract sections from RSC html journals (Silverchair layout, 2024+).
    Main content sits between div.article-metadata-panel and
    div.permissionstatement-section-wrapper; h2/h3 headings are flat siblings each
    followed by a sibling content div, so nesting is inferred from document order.
    '''
    metadata_panel = soup.find('div', class_='article-metadata-panel')
    permission_wrapper = soup.find('div', class_='permissionstatement-section-wrapper')
    parent = metadata_panel.parent
    children = [c for c in parent.children if getattr(c, 'name', None) is not None]
    start = children.index(metadata_panel)
    end = children.index(permission_wrapper)
    relevant = children[start + 1:end]

    data_dict = []
    current_h2 = None
    current_h3 = None
    skip_current = False

    for node in relevant:
        if node.name in ('h2', 'h3'):
            skip_current = _rsc_excluded_heading(node)
            if skip_current:
                current_h3 = None
                if node.name == 'h2':
                    current_h2 = None
                continue
            section = {'name': node.get_text(strip=True), 'type': node.name, 'content': []}
            if node.name == 'h2':
                data_dict.append(section)
                current_h2 = section
                current_h3 = None
            else:
                target_list = current_h2['content'] if current_h2 is not None else data_dict
                target_list.append(section)
                current_h3 = section
        elif node.name == 'div':
            if skip_current:
                continue
            if 'article-section-wrapper' in node.get('class', []):
                # standalone highlight box before any heading (e.g. "Broader context")
                box_heading = node.find('h3', class_='title')
                if box_heading is not None:
                    section = {'name': box_heading.get_text(strip=True), 'type': 'h3', 'content': []}
                    for p in box_heading.find_next_siblings('p'):
                        text = p.get_text(strip=True)
                        if text:
                            section['content'].append(text)
                    data_dict.append(section)
                continue
            target = current_h3 if current_h3 is not None else current_h2
            if target is None:
                continue
            target['content'].extend(_rsc_paragraphs(node))

    return data_dict

##### various util helpers to deal with frus collection
import re
import dateutil.parser as dparser

from bs4 import BeautifulSoup
from unidecode import unidecode
from collections import defaultdict

def _get_tag_attrs(soup, tag='div'):
    """
    Takes a BeautifulSoup object and returns a list of tag attributes.
    """
    return [t.attrs for t in soup.findAll(tag)]

def _get_name_ids(el_tag, sec_id, name_tag='persName'):
    """
    Takes a bs2 tag object, i.e. doc part, and return all name id
    for persons mentioned in doc.
    """
    if sec_id=='persons':
        return dict(
                [(n['xml:id'], __clean_name(n.get_text()))
                    for n in el_tag.findAll(name_tag)])
    else:
        ids = []
        for t in el_tag.findAll(name_tag):
            try:
                ids.append(t['corresp'])
            except KeyError:
                continue
        return ids

def __clean_name(name_text):
    """
    Removes newline and whitespace chars from name.
    """
    return re.sub('\\n\s*', '', name_text)

def get_doc_sections(text, tag='div'):
    """
    Takes raw (xml) text and returns a list of document sections. 
    """
    text = unidecode(text)
    soup = BeautifulSoup(text, 'xml')
    return soup.findAll(tag)

def parse_xml(text, section_tag='div', name_tag='persName'):
    """
    Takes raw (xml) text and returns a dict. 

    Parameters
    ----------
    text : string
    section_tag : string
        xml tag for secions
    name_tag : string
        xml tag for person names
    
    Returns
    -------
    dict
    """
    sections = get_doc_sections(text, section_tag)
    doc_dict = defaultdict(lambda : [])
    #doc_dict = __create_sections_dict(sections)
    for sec in sections:
        sec_id = sec.attrs['xml:id']
        sec_id = __clean_sec_id(sec_id)
        sec_text = sec.get_text()
        sec_names = _get_name_ids(sec, sec_id)
        sec_datetime = _get_datetime(sec)
        sec_dict = {'text': sec_text, 'name_ids': sec_names, 
                'date': sec_datetime}
        doc_dict[sec_id].append(sec_dict)
    return doc_dict

def __clean_sec_id(sec_id):
    return re.sub('d\d+', 'documents', sec_id) 

def _get_datetime(el_tag):
    """
    Takes a bs2 tag object, i.e. doc part, and returns section datetime.

    Notes: Assumes there is only one valid date per doc section. 
    """
    poss_date_rows = [t.get_text() for t in 
            el_tag.findAll('hi', attrs={'rend':"strong"})]
    dt = None
    for row in poss_date_rows:
        try:
            dt = dparser.parse(row)
        except TypeError:
            continue 
    return dt


    
def __create_sections_dict(sections):
    """
    Creates a dict with keys different section xml:id's.
    Treats all id's of type 'd#' as 'documents'.
    """
    sec_ids = [d.attrs['xml:id'] for d in sections]
    sec_ids = set([re.sub('d\d+', 'documents', i) for i in sec_ids])
    d = dict()
    return d.fromkeys(sec_ids, [])


if __name__=="__main__":
    ###for experimention
    import os
    DATA = os.getenv("DATA")
    FRUS = os.path.join(DATA, 'declass', 'frus')
    RAW = os.path.join(FRUS, 'raw')

    frus1 = os.path.join(RAW, 'frus1969-76v01.xml')

    with open(frus1) as f:
        frus1_data = f.read()
    parsed_xml = parse_xml(frus1_data)

    

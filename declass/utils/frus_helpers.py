##### various util helpers to deal with frus collection
import re
import dateutil.parser as dparser
import bs4
import BeautifulSoup as bs1
import pandas as pd
import numpy as np

from unidecode import unidecode
from collections import defaultdict

######################################EPUB BOOKS#############################
#The following functions are for parsing the html wrapped inside the *.epub files
#coming from http://history.state.gov/historicaldocuments/ebooks
#note: epub is simply a zip archive of html files; you can take a epub file and 
#unzip it into a nice directory srtructure and parse the individual fieles with the 
#functions below

def parse_epub_book(base_dir, vol_name):
    """
    Parses epub volumes from http://history.state.gov/historicaldocuments/ebooks
    and returns a dict of all relevant sections, and info therein: persons
    preface, terms, title, refs, docs. Note, you must first download the epub 
    volume and then unzip it into a directory vol_name.

    Parameters
    ----------
    base_dir : str
        base directory where the unzipped epub volume dir lives
    vol_name : str
        name of the unzipped volume directory
    
    Returns
    -------
    parsed_vol : dict
    """
    ###get all the nec paths
    vol_contents_dir = os.path.join(base_dir, vol_name, 'OEBPS')
    vol_contents = os.listdir(vol_contents_dir)
    persons = os.path.join(vol_contents_dir, 'persons.html')
    preface = os.path.join(vol_contents_dir, 'preface.html')
    title = os.path.join(vol_contents_dir, 'title.html')
    terms = os.path.join(vol_contents_dir, 'terms.html')
    refs = [os.path.join(vol_contents_dir,f) 
            for f in vol_contents if 
            re.search('(comp\d{,3}|ch\d{,3})\.html', f)]
    docs = [os.path.join(vol_contents_dir,f)
            for f in vol_contents if re.search('d\d{,4}\.html', f)]

    parsed_persons = parse_html_persons(persons)
    parsed_preface = parse_html_preface(preface)
    parsed_title = parse_html_title(title)
    parsed_terms = parse_html_terms(terms)
    parsed_refs = parse_html_refs(refs, id_prefix=vol_name)
    parsed_docs = parse_html_docs(docs, parsed_persons.index, 
            id_prefix=vol_name)
    return {'persons': parsed_persons, 'preface': parsed_preface, 
            'title': parsed_title, 'terms': parsed_terms, 'refs': parsed_refs,
            'docs': parsed_docs}


def parse_html_persons(html_file):
    """
    Parses persons.html from epub.

    Parameters
    ----------
    html_file : open file obj

    Returns
    -------
    pd.DataFrame 
    """
    names = pd.DataFrame(columns=['first', 'last', 'suffix'])
    html = open(html_file).read()
    html = html.decode('ascii', 'ignore')
    soup = bs4.BeautifulSoup(html)
    lines = soup.findAll('li')
    for line in lines:
        name_tag = line.findAll('span', 'tei-persName')
        if len(name_tag) is not 1: continue
        try:
            last_name, first_name = name_tag[0].getText().split(',')[:2]
        except ValueError:
            last_name = name_tag[0].getText().strip()
            first_name = ''
        name_id = re.sub(r'\s+', '_',last_name+' '+first_name)
        try:
            suffix = ','.join(name_tag[0].getText().split(',')[2:])
        except IndexError:
            suffix = None
        last_name = str(last_name.strip())
        first_name = str(first_name.strip())
        description = re.findall(r'</strong>(.*)</li>$', str(line))
        if description: 
            description = description[0].strip()
        else:
            description = None
        names = names.append(
                pd.DataFrame({'last': last_name, 'first': first_name, 
                    'suffix': suffix, 'description': description},
                    index=[name_id]))
    return names
    
def parse_html_preface(html_file):
    """
    Parses preface.html from epub.

    Parameters
    ----------
    html_file : open file obj
    """
    html = open(html_file).read()
    html = html.decode('ascii', 'ignore')
    soup = bs4.BeautifulSoup(html)
    return {'text': soup.getText(), 'html': html}

def parse_html_title(html_file):
    """
    Parses title.html from epub.

    Parameters
    ----------
    html_file : open file obj
    """
    html = open(html_file).read()
    html = html.decode('ascii', 'ignore')
    soup = bs4.BeautifulSoup(html)
    title = ' '.join([item.getText() for item in soup.findAll('h3')])
    title = re.sub(r'(\d{4})(\d{4})', r'\1-\2', title)
    editors = '; '.join([item.getText() for item in soup.findAll('dd')])
    date = re.findall(r'(\d{4})\n', soup.getText())[0]
    return {'title': title, 'editors':editors, 'date':date}

def parse_html_terms(html_file):
    """
    Parses terms.html from epub.

    Parameters
    ----------
    html_file : open file obj
    """
    html = open(html_file).read()
    html = html.decode('ascii', 'ignore')
    soup = bs4.BeautifulSoup(html)
    terms_list = []
    for term in soup.findAll('li'):
        term_id =  term.find('span').attrs['id']
        text =  term.getText().split(',')
        acronym = text[0].strip()
        defin = ''.join(text[1:]).strip()
        terms_list.append({'id':term_id, 'acronym': acronym, 'def': defin})
    return terms_list

def parse_html_refs(html_files, id_prefix=None):
    """
    Parses comp#.html from epub.

    Parameters
    ----------
    html_files : list of file paths
    id_prefix : str or None
        prefix for document id, ex frus1958-60v04
    """
    if id_prefix is None:
        id_prefix=''
    ref_info = []
    for html_file in html_files:
        html = open(html_file).read()
        html = html.decode('ascii', 'ignore')
        ref_info += __parse_html_ref(html, id_prefix)
    return ref_info
 
def __parse_html_ref(html, id_prefix):
    ###split up the html into ref sections since dates/notes are hard to 
    ###extract
    ref_info = []
    html_list = html.split('<hr class="list"/>')
    for html_item in html_list:
        soup = bs4.BeautifulSoup(html_item)
        try:
            title = soup.findAll('h4')[0].getText().strip()
            source = soup.findAll(
                    'p', {'class':'sourcenote'})[0].getText().strip()
            doc_num = re.findall(r'Document (\d{,4})', title)[0]
            if not doc_num: continue 
        except IndexError:
            continue
        try:
            notes = re.findall(r'<p>\n\s+([\w,\.\s:]+)\n\s+</p>', 
                    soup.prettify())[0]
        except IndexError:
            notes = None
        ref_info.append({'id': '%sd%s'%(id_prefix, doc_num), 
            'notes': notes, 'source': source})
    return ref_info

def parse_html_docs(html_files, full_names=None, id_prefix=None):
    """
    Parses d#.html from epub.

    Parameters
    ----------
    html_files : list of file paths
    full_names : set or list of strings
        if not None will return a list of name_ids; otherwise will return
        the name strings
    id_prefix : str or None
        prefix for document id, ex frus1958-60v04

    Returns
    -------
    doc_info : dict if dicts
    """
    if id_prefix is None:
        id_prefix=''
    doc_info = {}
    for html_file in html_files:
        html = open(html_file).read()
        html = html.decode('ascii', 'ignore')
        parsed_doc = __parse_html_doc(html, full_names, id_prefix)
        doc_info[parsed_doc['id']] = parsed_doc['doc']
    return doc_info

def __parse_html_doc(html, full_names, id_prefix):
    soup = bs1.BeautifulSoup(html)
    title = soup.title.getText()
    ###get the doc id
    doc_tag_attrs = soup.find('div', {'class':'document'}).attrs
    if doc_tag_attrs:
        doc_id = doc_tag_attrs[1][1]
    else:
        doc_id = 'XXX'
    date_tag = soup.find('span', {'class': 'tei-date'})
    if date_tag:
        try:
            date = dparser.parse(date_tag.getText())
        except:
            date = None
        #drop the date from main body
        date_tag.clear()
    else:
        date = None
    footnotes_tag = soup.find('div', {'class':'footnotes'})
    if footnotes_tag:
        footnotes = footnotes_tag.getText()
        ###drop the footnotes from main body
        footnotes_tag.clear()
    else:
        footnotes = None
    body = soup.getText()
    names = __parse_html_person_codes(soup, full_names)
    return {'id': id_prefix+doc_id, 'doc': 
            {'title':title, 'date':date, 'footnotes': footnotes, 
                'body': body, 'names':names}}

def __parse_html_person_codes(soup, full_names):
    """
    Retieves all persons in docs, 
    i.e. soup.findAll('span', {'class': 'tei-persName'}), matches these to the 
    persons dictionary from parse_html_persons and returns the appropriate code.
    """
    names = [t.getText() for t in 
            soup.findAll('span', {'class': 'tei-persName'})]
    if full_names is None:
        return names
    else:
        return __get_name_ids(names, full_names)

def __get_name_ids(names, full_names, 
        names_override={'eisenhower':'Eisenhower_Dwight_D.'}):
    name_ids = set()
    full_names = np.array(full_names)
    for name in names:
        name = name.lower()
        name = name.split()
        ###first check that name is not in  override names
        if name[-1] in names_override.keys():
            name_ids.add(names_override[name[-1]])
            continue
        ###try to find the best possible match
        match_array = np.array(
                [len([1 for part in name if part in n.lower()]) 
                    for n in full_names])
        best_match_index = match_array == match_array.max()
        ##check that the match is unique
        if sum(best_match_index)==1:
            name_ids.add(full_names[best_match_index][0])
    return list(name_ids)

###########################################################################

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
    soup = bs4.BeautifulSoup(text, 'xml')
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
        raw_sec_id = sec.attrs['xml:id']
        #if raw_sec_id=='sources':
        #    import pdb; pdb.set_trace()
        sec_id = __clean_sec_id(raw_sec_id)
        sec_dict = _create_sec_dict(sec, raw_sec_id, sec_id)
        doc_dict[sec_id].append(sec_dict)
    return doc_dict

def _create_sec_dict(section, raw_sec_id, sec_id):
    sec_dict = {}
    sec_dict['text'] = section.get_text()
    #check if the section is a doc
    if re.search(r'd\d+', raw_sec_id):
        sec_names = _get_name_ids(section, sec_id)
        sec_dict['name_ids'] = sec_names
    ##check is section is a terms section
    if raw_sec_id in ['terms','persons']:
        sec_dict['info'] = _parse_terms(section, raw_sec_id)
    sec_dict['date'] = _get_datetime(section)
    return sec_dict

def _parse_terms(section, raw_sec_id):
    """
    Parses terms 
    """
    terms_list = []
    items = section.findAll('item')
    if raw_sec_id=='terms':
        item_key = 'term'
    elif raw_sec_id=='persons':
        item_key = 'persName'
    for i in items:
        term = i.find(item_key)
        term_id = term.attrs['xml:id']
        term_text =  re.sub(r'\n\s+',' ', i.getText().strip()).split(',')
        term_short = term_text[0]
        term_long = ','.join(term_text[1:])
        terms_list.append({'term_id':term_id, 'term_short':term_short, 
            'term_long':term_long}) 
    return terms_list


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
    import pdb; pdb.set_trace()
    #parsed_vol = parse_epub_book(RAW, 'frus1958-60v04')
    #parsed_vol = parse_epub_book(RAW, 'frus1958-60v10p1')
    parsed_vol = parse_epub_book(RAW, 'frus1961-63v05')
    #frus1 = os.path.join(RAW, 'frus1969-76v01.xml')

    #with frus1) as f:
    #    frus1_data = f.read()
    #parsed_xml = parse_xml(frus1_data)
#    persons = os.path.join(RAW, 'frus1958-60v04/OEBPS', 'persons.html')
#    preface = os.path.join(RAW, 'frus1958-60v04/OEBPS', 'preface.html')
#    title = os.path.join(RAW, 'frus1958-60v04/OEBPS', 'title.html')
#    terms = os.path.join(RAW, 'frus1958-60v04/OEBPS', 'terms.html')
#    comp = [os.path.join(RAW, 'frus1958-60v04/OEBPS', 'comp%s.html'%num)
#            for num in range(1,8)]
#    docs = [os.path.join(RAW, 'frus1958-60v04/OEBPS', 'd%s.html'%num)
#            for num in range(1,351)]
#
#    parsed_persons = parse_html_persons(persons)
#    parsed_preface = parse_html_preface(preface)
#    parsed_title = parse_html_title(title)
#    parsed_terms = parse_html_terms(terms)
#    parsed_comp = parse_html_refs(comp, id_prefix='frus1958-60v04')
#    import pdb; pdb.set_trace()
#    parsed_docs = parse_html_docs(docs, parsed_persons.index, 
#            id_prefix='frus1958-60v04')

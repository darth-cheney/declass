#HTML parsing util functions
import re
from BeautifulSoup import BeautifulSoup

def dictify(ul, refs=None):
    """
    parses a nested html list and returns a dict
    
    Parameters
    ----------
    ul : BeautifulSoup object
    refs : None of regex obj
        Can be used to parse out refs in the html
    """
    result = {}
    for li in ul.find_all("li", recursive=False):
        try:
            key = next(li.stripped_strings)
        except StopIteration:
            continue
        child = li.find("ul")
        if child:
            doc_nums = None
            if refs:
                parent = re.sub(str(child), '', str(li))
                soup = BeautifulSoup(parent)
                doc_nums =  [t.getText() for t in 
                        soup.findAll('a', {'href': refs})]
            result[key] = dictify(child, refs)
            result[key]['doc'] = doc_nums
        else:
            doc_nums = None
            if refs:
                parent = re.sub(str(child), '', str(li))
                soup = BeautifulSoup(parent)
                doc_nums =  [t.getText() for t in 
                        soup.findAll('a', {'href': refs})]
            result[key] = {}
            result[key]['doc'] = doc_nums
    return result

#HTML parsing util functions

def dictify(ul):
    #parses a nested html list and returns a dict
    result = {}
    for li in ul.find_all("li", recursive=False):
        key = next(li.stripped_strings)
        ul = li.find("ul")
        if ul:
            result[key] = dictify(ul)
        else:
            result[key] = None
    return result

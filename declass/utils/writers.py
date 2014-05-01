###utils for writing diff objects to file

def nested_dict_to_delim(f, d, sep='\t', offset=0):
    """
    Writes a nested dict to sep delimited file preserving the structure with 
    column separation.

    Parameters
    ----------
    f : open file obj
    d : nested dict
    sep : str
        the column seperator, default tab
    offset : int
        initial column offset param


    Notes: converts all None values to ''
    """
    offset+=1
    for k in d.keys():
        #column_offset = ','.join([' ' for i in range(offset)])
        #f.write(column_offset + k + ',\n')
        column_offset = sep.join([' ' for i in range(offset)])
        f.write(column_offset + k + sep + '\n')
        try:
            if d[k].keys():
                nested_dict_to_delim(f, d[k], sep, offset)
        except AttributeError:
            column_offset = sep.join([' ' for i in range(offset+1)])
            #column_offset = ','.join([' ' for i in range(offset+1)])
            if d[k] is None: d[k]=''
            #f.write(column_offset + str(d[k]) + ',\n')
            f.write(column_offset + str(d[k]) + sep + '\n')


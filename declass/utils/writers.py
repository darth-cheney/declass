###utils for writing diff objects to file

def nested_dict_to_csv(f, d, offset=0):
    """
    Writes a nested dict to csv preserving the structure with 
    column indentation.

    Parameters
    ----------
    f : open file obj
    d : nested dict
    offset : int
        initial column offset param

    Notes: converts all None values to ''
    """
    offset+=1
    for k in d.keys():
        column_offset = ','.join([' ' for i in range(offset)])
        f.write(column_offset + k + ',\n')
        try:
            if d[k].keys():
                nested_dict_to_csv(f, d[k], offset)
        except AttributeError:
            column_offset = ','.join([' ' for i in range(offset+1)])
            if d[k] is None: d[k]=''
            f.write(column_offset + str(d[k]) + ',\n')


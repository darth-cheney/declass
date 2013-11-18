# -*- coding: utf-8 -*-
import pandas as pd
import re
import numpy as np
import os
import argparse

def format_text(text):
    #cleans text and takes out DDRS formatting
    text = re.sub("<\?HR\?>(.)*?<\?PRE\?>", "<?PRE?>", text)
    text = re.sub("<\?HR\?>(.)*?</DOC\.BODY>", "</DOC.BODY>", text)
    text = text.strip("\"")

    text = text.replace("</PARA>", " "). \
            replace("<PARA>", " ") \
            .replace("<?BR?>", " ") \
            .replace("<?PRE?>", " <?PRE?> "). \
            replace("<?HR?>", " "). \
            replace("</DOC.BODY>", " "). \
            replace("<DOC.BODY>", " "). \
            replace("\\n", " "). \
            replace("\\'s","'s"). \
            replace("\\'S","'S")
    return text
    
def get_words(text, start, stop):
    #Get the words between start and stop range.
    words = text.split()
    return words[start:stop]

def split_doc_pair(docPairs, redactions, outdir):

    #Write a set of cleaned text files that split out the document from all its redactions

    docPairs['d1body'] = docPairs['d1body'].apply(lambda x: format_text(x))
    
    docPairs['d2body'] = docPairs['d2body'].apply(lambda x: format_text(x))
    
    redactions['redaction'] = redactions['redaction'].apply(lambda x: format_text(x))
    
    for d in docPairs.index:
        docRow = docPairs.ix[d]
        s1 = docRow['side1']
        s2 = docRow['side2']
        if s1 > s2:
            prinum = str(1)
        else:
            prinum = str(2)
        txt = docRow['d'+prinum+'body']
        txt = txt.split()
        rdctn = []
        rdct = redactions[np.logical_and(redactions['d1id'] == docRow['docId1'],redactions['d2id'] == docRow['docId2'])]
        for ind in rdct.index:
            num = str(redactions['side'].ix[ind])
            r = redactions['redaction'].ix[ind]
            rdctn.append(r)
            if num == prinum:
                print 'redacting'
                start = redactions['start'+num].ix[ind]
                end = redactions['end'+num].ix[ind]
                for w in xrange(start,end):
                    txt[w] = ' '
            else:
                print 'added'
        txt = " ".join(txt)
        txt = txt.split()
        txt = " ".join(txt)
        rdctn = " ".join(rdctn)
        with open(os.path.join(outdir, '%04d-un.txt' % (docRow['pairId'])), 'wb') as f:
            f.write(txt)
        with open(os.path.join(outdir, '%04d-re.txt' % (docRow['pairId'])), 'wb') as f:
            f.write(rdctn)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=globals()['__doc__'],
        formatter_class=argparse.RawDescriptionHelpFormatter)
    
    parser.add_argument(
        '-d', '--docs', required=True,
        help='Path to csv with document information')
        
    parser.add_argument(
        '-r', '--redact', required=True,
        help='Path to csv with redaction information')

    parser.add_argument(
        '-o', '--outdir', required=True,
        help='Directory to write split files')
        
    args = parser.parse_args()
    doc_pairs = pd.read_csv(args.docs)
    redact = pd.read_csv(args.redact)
    split_doc_pair(doc_pairs, redact, args.outdir)
    
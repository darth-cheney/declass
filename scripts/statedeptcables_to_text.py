"""
Use the database module to extract cable table data to text
"""
import os
import yaml

import pandas as pd

from declass.utils.database import DBCONNECT


# Set paths
# You should have your own login_file somewhere.  
# DO NOT commit this to the (public) repository!
#CONF = os.path.join(os.getenv('DECLASS'), '../conf')
login_file = os.path.join(os.getenv('HOME'), '.declass_db')
CABLES = os.path.join(os.getenv('DATA'), os.getenv('ME'), 'declass', 'cables-full-01')
RAW = os.path.join(CABLES, 'raw')
META = os.path.join(CABLES, 'meta')
bodyfiles_basepath = os.path.join(RAW, 'bodyfiles')
metafile_path = os.path.join(META, 'meta.csv')

# Get login info
login_info = yaml.load(open(login_file))
host_name = login_info['host_name']
db_name = login_info['db_name']
user_name = login_info['user_name']
pwd = login_info['pwd']

# Set up DB and retrieve all records as a dict
# First run with "limit 10", then erase once things work
dbCon = DBCONNECT(host_name, db_name, user_name, pwd)
fields = ['doc_nbr', 'concepts', 'date', 'msgfrom', 'office', 'origclass', 'orighandling', 'PREVCLASS', 'PREVHANDLING', 'REVIEW_AUTHORITY', 'REVIEW_DATE', 'SUBJECT', 'TAGS', 'MSGTO', 'TYPE', 'CHANNEL', 'PREVCHANNEL', 'DISP_COMMENT', 'DISP_AUTH', 'DISP_DATE', 'REVIEW_AUTH', 'REVIEW_FLAGS', 'REVIEWHISTORY', 'MSGTEXT', 'cleanFrom', 'cleanTo']
fields = [f.lower() for f in fields]
meta_fields = [f for f in fields if f != 'msgtext']

limit = 5000000
records = dbCon.run_query(
    'select %s '
    'from statedeptcables '
     'limit %s;' % (', '.join(fields), limit))

# Write records to disk
meta = {f: [] for f in meta_fields}
meta['doc_id'] = []
meta['has_text'] = []

for i, rec in enumerate(records):
    doc_id = rec['doc_nbr'].replace(' ', '_')

    # Append meta
    meta['doc_id'].append(doc_id)
    for field in meta_fields:
        meta[field].append(rec[field])
    # Write the body text
    if rec['msgtext']:
        filepath = os.path.join(bodyfiles_basepath, doc_id + '.txt')
        with open(filepath, 'w') as f:
            f.write(rec['msgtext'])
        meta['has_text'].append(1)
    else:
        meta['has_text'].append(0)

    if i%10000==0: print 'done with %s \n'%i

meta = pd.DataFrame(meta)
meta.to_csv(metafile_path, sep='|', index=False)




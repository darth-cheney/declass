"""
This script extracts the INFO area of the MSGTEXT in the statedeptcables
table. The INFO section is basically a CC list. It adds it to a field called
cleanBody of type text which has previously been added.
"""
import os
import yaml
import re

from declass.utils.database import DBCONNECT

# Get login info
login_file = os.path.join(os.getenv('HOME'), '.declass_db')
login_info = yaml.load(open(login_file))
host_name = login_info['host_name']
db_name = login_info['db_name']
user_name = login_info['user_name']
pwd = login_info['pwd']

dbCon = DBCONNECT(host_name, db_name, user_name, pwd)

limit = 50000000
query = "select DOCID, MSGTEXT from statedeptcables"
query += " where MSGTEXT != '' and MSGTEXT is not null"
query += " limit %s;" % limit

print "Downloading data..."
results = dbCon.run_query(query)
print "Data downloaded!"
print "Length results: ", len(results)

# The -{5}-* part of the pattern is to match the ------ portion of the cable,
# since many cables have "INFO" both before and after that point. This helps
# avoid getting any false positives.
pattern = '[\s\S]*-{5}-*[\s\S]*\nINFO ((?:[ A-Za-z0-9]+\n)+)'
regex = re.compile(pattern)


print "Now adding to database..."

errorfile = open('/tmp/errorfile', 'w')

count = 0
infocount = 0
errorcount = 0
for result in results:
    # Script should not stop entirely due to a few errors.
    try:
        docid = str(result['DOCID'])
        msgtext = result['MSGTEXT']
        info = regex.match(msgtext)
        if info:
            cc = info.group(1).strip()
            cc = cc.split('\n')
            cc = [words.strip() for words in cc]
            cc = [words for words in cc if words != '']
            if cc == []:
                continue

            cc = ','.join(cc)
            query = "update statedeptcables set info = '" + cc + "'"
            query += " where DOCID = '" + docid + "';"
            dbCon.run_query(query)
            infocount += 1
    except Exception as e:
        errorfile.write('DOCID: %s' % result['DOCID'])
        errorfile.write(' , ' + e.message + '\n')
        errorcount += 1
        if errorcount % 100 == 0:
            print "Error count: ", errorcount
    count += 1
    if count % 10000 == 0:
        print '\t', count

errorfile.close()

print "Final error count: ", errorcount
print "Final info count: ", infocount

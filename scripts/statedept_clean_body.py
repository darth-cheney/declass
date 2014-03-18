"""
Extracts the body text out of the MSGTEXT column in statedeptcables and then
updates the bodyClean column with the extracted body text.
"""
import os
from sys import stdout
import yaml
import csv

from declass.utils.cable_helpers import get_body
from declass.utils.database import DBCONNECT

# Get login info
login_file = os.path.join(os.getenv('HOME'), '.declass_db')
login_info = yaml.load(open(login_file))
host_name = login_info['host_name']
db_name = login_info['db_name']
user_name = login_info['user_name']
pwd = login_info['pwd']

# Set up DB and retrieve all records as a dict
# First run with "limit 10", then erase once things work
dbCon = DBCONNECT(host_name, db_name, user_name, pwd)

limit = 50000000

# If there is nothing in MSGTEXT, then corresponding cleanBody value is left as
# null.
records = dbCon.run_query("select DOCID, MSGTEXT from statedeptcables" +
              " where MSGTEXT != '' limit %s;" % limit)

for record in records:
    doc_id = record['DOCID']

    text = record['MSGTEXT']
    body = get_body(text)

    # If get body strips all text and returns nothing, write '' to the
    # cleanBody do distinguish from null above.
    if not body:
        query = "update statedeptcables set cleanBody=''"
        query += "' where DOCID = '" + str(doc_id) + "';"
        dbCon.run_query(query)
        continue
        
    # Join sentences from get_body together and write to database.
    body = '\n'.join(body) + '\n'
    body = body.replace("'","")
    query = "update statedeptcables set cleanBody='" + body
    query += "' where DOCID = '" + str(doc_id) + "';"
    dbCon.run_query(query)

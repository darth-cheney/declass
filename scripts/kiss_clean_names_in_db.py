"""
Use the database module to extract kissinger files to text. This has already
been run but is being added just so there is a record of what happened.
"""
import os
import yaml
import csv

from declass.utils.database import DBCONNECT

# Get file containing doc_id -> Cleaned name as a csv file. This was
# hand-written by David Allen, Daniel and others.
nameMappingFile = './nameMapping.csv'
with open(nameMappingFile) as f:
    reader = csv.reader(f, delimiter='|')
    nameMapping = dict([datum for datum in reader])

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
#records = dbCon.run_query('select * from Kissinger limit 10;')
records = dbCon.run_query('select doc_id from KissingerClean;')

# This test passed:
#
#keys = nameMapping.keys()
#has_ids = True
#
#for pair in doc_ids:
#   if pair['doc_id'] not in keys:
#       has_ids = False
#
#print "has ids: ", has_ids

# Update table with cleaned names

for record in records:
    doc_id = record['doc_id']
    cleanedName = nameMapping[doc_id]

    query = "update KissingerClean set names='" + cleanedName
    query += "' where doc_id = '" + doc_id + "';"
    dbCon.run_query(query)

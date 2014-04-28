# This does LDA on the cleanBody field in the repository. Everything is
# automated so in theory this should be runnable from start to finish for any
# user. It does use code which is (currently) not in the mainline rosetta
# repository. To run this you need to clone my repository
# (github.com/ApproximateIdentity/rosetta.git) and checkout the dev-v0.1 tag.
#
# This was adapted from Maja's script (processCables.py in the repo
# github.com/mariru/declass.git) and should ideally be giving the same results
# as hers.

import os
import dateutil
import yaml
from collections import defaultdict
import datetime

import matplotlib.pyplot as plt
import pandas as pd
from pandas import DataFrame, Series
from nltk.corpus import wordnet, stopwords
 
from rosetta.text.text_processors import SFileFilter, VWFormatter
from rosetta.text.vw_helpers import LDAResults

from declass.utils.database import DBCONNECT

# On Thomas' rosetta branch tag dev-v0.1.
from rosetta.file_io import get_file_names_from_rosetta
from rosetta.file_io import records_to_rosetta
from rosetta.file_io import convert_rosetta_to_vw
from rosetta.file_io import get_file_count_from_rosetta
from rosetta.analysis import get_topic_predictions


# Local data directory structure to be.
DATA = os.environ['DATA']
ME = 'thomas'
MYDATA = os.path.join(DATA, ME, 'state_cleanBody_lda')
RAW = os.path.join(MYDATA, 'raw')
PROCESSED = os.path.join(MYDATA, 'processed')
VW = os.path.join(PROCESSED, 'vw')
IMAGES = os.path.join(PROCESSED, 'images')

for directory in [RAW, PROCESSED, VW, IMAGES]:
    os.makedirs(directory)

# Set all filenames.
meta_filepath = os.path.join(RAW, 'meta.csv')
rosetta_filepath = os.path.join(RAW, 'bodyfiles.ros')
tokens_filepath = os.path.join(VW, 'tokens.vw')
filt_tokens_filepath = os.path.join(VW, 'filt_tokens.vw')

num_topics = 80
passes = 10
sff_file_path = os.path.join(VW, 'sff_file.pkl')
predictions_path = os.path.join(VW, "filt_prediction_full.dat")
topics_path = os.path.join(VW, "filt_topics_full.dat")
filt_tokens_filepath = os.path.join(VW, 'filt_tokens.vw')
doc_topics_filepath = os.path.join(VW, 'doc_topics.csv')
doc_topic_words_filepath = os.path.join(VW, 'doc_topic_words.csv')

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
query = "select DOCID, ORIGCLASS, cleanBody, DATE from statedeptcables"
query += " where cleanBody != '' and cleanBody is not null"
query += " limit %s;" % limit
print query
results = dbCon.run_query(query)


# Write bodyfiles to rosetta file.
records = []
for result in results:
    filename = result['DOCID']
    contents = result['cleanBody']
    records.append((filename, contents))

records_to_rosetta(records, rosetta_filepath)

# Write metadata.
with open(meta_filepath, 'w') as f:
    f.write("doc_id|date|orig_class\n")
    for result in results:
        doc_id = str(result['DOCID'])
        date = result['DATE']
        orig_class = result['ORIGCLASS']
        f.write(doc_id + '|' + date + '|' + orig_class + '\n')


# Create vw file.
convert_rosetta_to_vw(rosetta_filepath, tokens_filepath)


# First filter out the messed up words.
sff = SFileFilter(VWFormatter())
sff.load_sfile(tokens_filepath)

df = sff.to_frame()

d = {}
for token in df.index:
    d[token] = True

for token in d.iterkeys():
    if token in stopwords.words('english') or not wordnet.synsets(token):
        d[token] = False

remove_words = [word for word, value in d.iteritems() if not value]

monthnames = ['january', 'jan', 'february', 'feb', 'march', 'mar', 'april',
              'apr', 'may', 'june', 'jun', 'july', 'jul', 'august', 'aug',
              'september', 'sep', 'november', 'nov', 'december', 'de', 'dec',
              'para']

remove_words += [month for month in monthnames if month in df.index]

stop_words = ["meeting", "agreed", "confidential", "actually", "remarks",
              "lower", "ad", "back", "wish", "act", "two", "used", "agency",
              "fully", "confirmed", "ten", "appreciate", "quito", "resolve",
              "hours", "trying", "seen", "feel", "available", "re", "mr",
              "mrs", "hotel", "done", "underway", "way", "side", "go",
              "paragraph", "percent", "program", "year", "month", "en", "look",
              "text", "sure", "secret", "asap", "young", "real", "positive",
              "negative", "continuing", "states", "refused", "understand",
              "continue", "related", "require", "current", "using",
              "explained", "status", "full", "mt", "letter", "next", "results",
              "concluded", "immediate", "nine", "friday", "statement",
              "scheduled", "present", "question", "week", "thus", "questions",
              "perhaps", "last", "even", "many", "faced", "details", "another",
              "allowed", "subject", "state", "secretary"]

remove_words += [stopword for stopword in stop_words if stopword in df.index]
remove_words = list(set(remove_words))

sff.filter_tokens(remove_words)
sff.filter_extremes(doc_freq_min=5, doc_fraction_max=0.8)
sff.compactify()
sff.save(sff_file_path)
sff.filter_sfile(tokens_filepath, filt_tokens_filepath)


# Next run LDA.
CMD = "cd " + VW + ";"
CMD += "rm *.cache;"
CMD += "vw --lda " + str(num_topics)
CMD += " --cache_file tokens.cache"
CMD += " --passes " + str(passes)
CMD += " -p " + predictions_path
CMD += " --readable_model " + topics_path
CMD += " --bit_precision 16 "
CMD += filt_tokens_filepath

print CMD
os.system(CMD)


# Get topic predictions.
meta = DataFrame.from_csv(meta_filepath, sep='|')
num_docs = get_file_count_from_rosetta(rosetta_filepath)
topics = get_topic_predictions(predictions_path, num_docs, passes)
topics = Series(topics)
meta['topic'] = topics
meta.to_csv(doc_topics_filepath, sep='|')


# Get top 10 words from each topic.
lda = LDAResults(topics_path, predictions_path, sff_file_path, num_topics)
topics = lda.pr_token_g_topic.keys()
with open(doc_topic_words_filepath, 'w') as f:
    for topic in topics:
        s = lda.pr_token_g_topic[topic].copy()
        s.sort(ascending=False)
        keys = s.keys()[:10]
        f.write(topic)
        for key in keys:
            f.write(',' + key)
        f.write('\n')


# Finally create images with graphs of topics and topic tokens below...
meta = DataFrame.from_csv(doc_topics_filepath, sep='|')
meta['date'] = meta['date'].apply(dateutil.parser.parse)
meta['month'] = meta['date'].apply(lambda x: x.replace(day=1))


# Get captions for images.
topics_dict = {}
with open(doc_topic_words_filepath) as f:
    for line in f:
        data = line.strip().split(',')
        topic = data[0]
        words = data[1:]
        topics_dict[topic] = words


# Write out images.
topics = topics_dict.keys()
topics.sort()


index = []
for year in range(1973, 1977):
    for month in range(1, 13):
        date = datetime.datetime.strptime("1/%s/%s" % (month, year),
                                          "%d/%m/%Y")
        index.append(date)

important_classifications = ['CONFIDENTIAL', 'UNCLASSIFIED',
                             'LIMITED OFFICIAL USE', 'SECRET']

colors = {'CONFIDENTIAL'            : 'm-',
          'UNCLASSIFIED'            : 'c-',
          'LIMITED OFFICIAL USE'    : 'y-',
          'SECRET'                  : 'r-'}

for i, topic in enumerate(topics):
    mask = meta['topic'] == i
    if len(meta[mask]) == 0:
        continue

    fig, ax = plt.subplots()

    # Plot separate classifications.
    for classification in important_classifications:
        submask = meta['orig_class'] == classification
        submask *= mask
        group = meta[submask].groupby('month').size()
        group = group.reindex(index)
        group = group.fillna(value=0)
        ax.plot_date(group.index, group.values,
                     colors[classification], label=classification)

    # Plot totals.
    group = meta[mask].groupby('month').size()
    group = group.reindex(index)
    group = group.fillna(value=0)
    ax.plot_date(group.index, group.values, 'k-', label='TOTAL')

    # Format graphs nicely.
    fig.autofmt_xdate()
    legend = ax.legend(loc='upper center')
    fig.set_size_inches(17, 9, dpi=150)
    txt = "Top words: " + ", ".join(topics_dict[topic])
    fig.text(0.1, 0.05, txt)
    filename = os.path.join(IMAGES, topic + '.png')
    plt.savefig(filename)

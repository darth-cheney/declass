"""
Helper objects/functions specifically for use with Gensim.
"""
import pandas as pd
from gensim import corpora, models

from . import common


class StreamerCorpus(object):
    """
    A "corpus type" object built with token streams and dictionaries.

    Depending on your method for streaming tokens, this could be slow...
    Before modeling, it's usually better to serialize this corpus using: 

    self.to_corpus_plus(fname)
    or
    gensim.corpora.SvmLightCorpus.serialize(path, self) 
    """
    def __init__(self, streamer, dictionary, **streamer_kwargs):
        """
        Stream token lists from pre-defined path lists.

        Parameters
        ----------
        streamer : Streamer compatible object.
            Method streamer.token_stream() returns a stream of lists of words.
        dictionary : gensim.corpora.Dictionary object
        streamer_kwargs : Additional keyword args
            Passed to streamer.token_stream(), e.g.
                limit (int), cache_list (list of strings), 
                doc_id (list of strings)
        """
        self.streamer = streamer
        self.dictionary = dictionary
        self.streamer_kwargs = streamer_kwargs

    def __iter__(self):
        """
        Returns an iterator of "corpus type" over text files.
        """
        for token_list in self.streamer.token_stream(**self.streamer_kwargs):
            yield self.dictionary.doc2bow(token_list)

    def serialize(self, fname):
        """
        Save to svmlight (plus) format, generating files:
        fname, fname.index, fname.doc_id
        """
        # See if you are limiting doc_id to some list
        doc_id = self.streamer_kwargs.get('doc_id', None)
        if doc_id is None:
            doc_id = self.streamer.doc_id

        # Make the corpus and .index file
        corpora.SvmLightCorpus.serialize(fname, self)

        # Make the .doc_id file
        with open(fname + '.doc_id', 'w') as f:
            f.write('\n'.join(doc_id))


class SvmLightPlusCorpus(corpora.SvmLightCorpus):
    """
    Extends gensim.corpora.SvmLightCorpus, providing methods to work with
    (e.g. filter by) doc_ids.
    """
    def __init__(self, fname, doc_id=None, limit=None):
        """
        Parameters
        ----------
        fname : Path
            Contains the .svmlight bag-of-words text file
        doc_id : Iterable over strings
            Limit all streaming results to docs with these doc_ids
        limit : Integer
            Limit all streaming results to this many
        """
        super(SvmLightPlusCorpus, self).__init__(fname)

        self.limit = limit
        
        # All possible doc_id in the corpus
        self.doc_id_all = common.get_list_from_filerows(
            fname + '.doc_id')

        # Limit all streaming results to docs in self.doc_id
        if doc_id is not None:
            self.doc_id_set = set(doc_id)
        else:
            self.doc_id_set = set(self.doc_id_all)

        self.doc_id = [
            doc for doc in self.doc_id_all if doc in self.doc_id_set]

    def __iter__(self):
        """
        Returns a gensim-compatible corpus.

        Parameters
        ----------
        doc_id : Iterable over Strings
            Return info dicts iff doc_id in doc_id
        """
        base_iterable = super(SvmLightPlusCorpus, self).__iter__()
        for i, row in enumerate(base_iterable):
            if i == self.limit:
                raise StopIteration

            if self.doc_id_all[i] in self.doc_id:
                yield row

    def serialize(self, fname, **kwargs):
        """
        Save to svmlight (plus) format, generating files:
        fname, fname.index, fname.doc_id

        Parameters
        ----------
        fname : String
            Path to save the bag-of-words file at
        kwargs : Additional keyword arguments
            Passed to SvmLightCorpus.serialize
        """
        # Make the corpus and .index file
        corpora.SvmLightCorpus.serialize(fname, self, **kwargs)

        # Make the .doc_id file
        with open(fname + '.doc_id', 'w') as f:
            f.write('\n'.join(self.streamer.doc_id))

    @classmethod
    def from_streamer_dict(
        self, streamer, dictionary, fname, doc_id=None, limit=None):
        """
        Initialize from a Streamer and gensim.corpora.dictionary, serializing
        the corpus (to disk) in SvmLightPlus format, then returning a
        SvmLightPlusCorpus.

        Parameters
        ----------
        streamer : Streamer compatible object.
            Method streamer.token_stream() returns a stream of lists of words.
        dictionary : gensim.corpora.Dictionary object
        fname : String
            Path to save the bag-of-words file at
        doc_id : Iterable over strings
            Limit all streaming results to docs with these doc_ids
        limit : Integer
            Limit all streaming results to this many

        Returns
        -------
        corpus : SvmLightCorpus
        """
        streamer_corpus = StreamerCorpus(
            streamer, dictionary, doc_id=doc_id, limit=limit)
        streamer_corpus.serialize(fname)

        return SvmLightPlusCorpus(fname, doc_id=doc_id, limit=limit)


def get_words_docfreq(self):
    """
    Returns a df with token id, doc freq as columns and words as index.
    """
    id2token = dict(self.dictionary.items())
    words_df = pd.DataFrame(
            {id2token[tokenid]: [tokenid, docfreq] 
             for tokenid, docfreq in dictionary.dfs.iteritems()},
            index=['tokenid', 'docfreq']).T
    words_df = words_df.sort_index(by='docfreq', ascending=False)

    return words_df


def get_doc_topics(corpus, lda, doc_id=None):
    """
    Creates a delimited file with doc_id and topics scores.
    """
    topics_df = pd.concat((pd.Series(dict(doc)) for doc in 
        lda[corpus]), axis=1).fillna(0).T
    topics_df = topics_df.rename(
        columns={i: 'topic_' + str(i) for i in topics_df.columns})

    if doc_id is not None:
        topics_df.index = self.doc_id
        topics_df.index.name = 'doc_id'

    return topics_df

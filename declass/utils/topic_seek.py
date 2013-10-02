import sys
import pandas as pd
import numpy as np
import matplotlib.pylab as plt

from time import time
from gensim import corpora, models
from declass.utils import (
        text_processors, filefilter, streamers, gensim_helpers, common)
from common import lazyprop


class Topics(object):
    """
    Convenience wrapper for for the gensim LDA module. 
    See http://radimrehurek.com/gensim/ for more details.
    """
    def __init__(
        self, text_base_path=None, file_type='*.txt', vw_corpus_path=None,
        tokenizer=text_processors.TokenizerBasic(), limit=None, 
        verbose=False):
        """
        Parameters
        ----------
        text_base_path : string or None
            Base path to dir containing files.
        file_type : string
            File types to filter by.
        vw_corpus_path : string None
            Path to corpus saved in sparse VW format. 
        tokenizer : function
        limit : int or None
            Limit for number of docs processed.
        verbose : bool
        
        Notes
        -----
        If text_base_path is None assumes that sparse_corpus_path will be 
        specified. Current supports on VW sparse format.
        """
        self.verbose = verbose
        self.limit = limit
        
        if text_base_path:
            self.streamer = streamers.TextFileStreamer(
                    text_base_path=text_base_path, file_type=file_type,
                    tokenizer=tokenizer,limit=limit)
        if vw_corpus_path:
            self.streamer = streamers.VWStreamer(
                    sfile=vw_corpus_path, limit=limit)
    

    def set_dictionary(
        self, tokenizer=None, load_path=None, no_below=5, no_above=0.5,
        save_path=None):
        """
        Convert token stream into a dictionary, setting self.dictionary.
        
        Parameters
        ----------
        load_path : string
            path to saved dictionary 
        no_below : Integer
            Do not keep words with total count below no_below
        no_above : Real number in [0, 1]
            Do not keep words whose total count is more than no_above fraction
            of the total word count.
        save_path : string
            path to save dictionary
        """
        t0 = time()
        # Either load a pre-made dict, or create a new one using __init__
        # parameters.
        if load_path:
            dictionary = corpora.Dictionary.load(load_path)
        else:
            token_stream = self.streamer.token_stream(
                    cache_list=['doc_id'])
            dictionary = corpora.Dictionary(token_stream)
            self.doc_ids = self.streamer.__dict__['doc_id']
        dictionary.filter_extremes(no_below=no_below, no_above=no_above)
        dictionary.compactify()

        self._print('dictionary build time: %.2f' % (time() - t0))

        if save_path:
            dictionary.save(save_path)

        self.dictionary = dictionary

    def set_corpus(self, save_path=None):
        """
        Creates a corpus. 
        
        Parameters
        ----------
        save_path : string
            Path to save corpus to disc. 
        """
        t0 = time()
        self.corpus = gensim_helpers.SimpleCorpus(
                    self.dictionary, self.streamer)
        t1 = time()
        build_time = t1-t0
        self._print('corpus build time: %s'%build_time)

        if save_path:
            #compact format save
            corpora.SvmLightCorpus.serialize(save_path, self.corpus)

    def build_lda(
        self, num_topics, alpha=None, eta=None, passes=1, chunksize=2000,
        update_every=1):
        """
        Buld the lda model.
        
        Parameters
        ----------
        num_topics : int
            number of topics 
        alpha : list of floats, None
            hyperparameter vector for topic distribution
        eta : list of floats, None
            hyperparameter vector for word distribution
        passes : int
            number of passes for model build
        chunksize : int
        update_every ; int
        """
        self.num_topics = num_topics
        t0 = time()
        lda = models.LdaModel(self.corpus, id2word=self.dictionary, 
                num_topics=num_topics, passes=passes, alpha=alpha, eta=eta, 
                chunksize=chunksize, update_every=update_every)
        t1=time()
        build_time = t1-t0
        self._print('lda build time: %s'%build_time)
        self.lda = lda

        return lda
 
    def write_topics(self, filepath_or_buffer=None, num_words=5):
        """
        Writes the topics to disk.
        
        Parameters
        ----------
        filepath_or_buffer : string
            topics file path.  If None, write to stdout.
        num_words : int
            number of words to write with each topic
        """
        outfile = common.get_outfile(filepath_or_buffer)
        for t in xrange(self.num_topics):
            outfile.write('topic %s'%t + '\n')
            outfile.write(self.lda.print_topic(t, topn=num_words) + '\n')
        common.close_outfile(outfile)

    def write_doc_topics(self, save_path, sep='|'):
        """
        Creates a delimited file with doc_id and topics scores.
        """
        topics_df = self._get_topics_df()
        topics_df.to_csv(save_path, sep=sep, header=True)
    
    def _get_topics_df(self):
        topics_df = pd.concat((pd.Series(dict(doc)) for doc in 
            self.lda[self.corpus]), axis=1).fillna(0).T
        topics_df.index = self.doc_ids
        topics_df.index.name = 'doc_id'
        topics_df = topics_df.rename(
            columns={i: 'topic_' + str(i) for i in topics_df.columns})

        return topics_df
            
    def _print(self, msg):
        if self.verbose:
            sys.stdout.write(msg + '\n')

    def get_words_docfreq(self, plot_path=None):
        """
        Returns a df with token id, doc freq as columns and words as index.
        """
        id2token = dict(self.dictionary.items())
        words_df = pd.DataFrame(
                {id2token[tokenid]: [tokenid, docfreq] 
                 for tokenid, docfreq in self.dictionary.dfs.iteritems()},
                index=['tokenid', 'docfreq']).T
        words_df = words_df.sort_index(by='docfreq', ascending=False)
        if plot_path:
            plt.figure()
            words_df.docfreq.apply(np.log10).hist(bins=200)
            plt.savefig(plot_path)

        return words_df

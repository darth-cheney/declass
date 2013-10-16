import unittest
from StringIO import StringIO
import sys
from datetime import datetime
import copy
from collections import Counter, OrderedDict
import random

import pandas as pd
from numpy.testing import assert_allclose
from pandas.util.testing import assert_frame_equal

from declass.utils import text_processors, streamers, topic_seek, vw_helpers


class TestTokenizerBasic(unittest.TestCase):
    """
    """
    def setUp(self):
        self.Tokenizer = text_processors.TokenizerBasic

    def test_text_to_counter(self):
        text = "Hi there's:alot,of | food hi"
        result = self.Tokenizer().text_to_counter(text)
        benchmark = Counter(["hi", "there's", "alot", "food", "hi"])
        self.assertEqual(result, benchmark)


class TestVWFormatter(unittest.TestCase):
    """
    """
    def setUp(self):
        self.formatter = text_processors.VWFormatter()

    def test_get_sstr_01(self):
        doc_id = 'myname'
        feature_values = OrderedDict([('hello', 1), ('dude', 3)])
        importance = 1
        result = self.formatter.get_sstr(
            feature_values=feature_values, doc_id=doc_id,
            importance=importance)
        benchmark = " 1 %s| hello:1 dude:3" % doc_id

    def test_write_dict_01(self):
        record_str = " 3.2 doc_id1| hello:1 bye:2"
        result = self.formatter.sstr_to_dict(record_str)
        benchmark = {
            'importance': 3.2, 'doc_id': 'doc_id1',
            'feature_values': {'hello': 1, 'bye': 2}}
        self.assertEqual(result, benchmark)


class TestVWHelpers(unittest.TestCase):
    def setUp(self):
        self.varinfo_path = 'files/varinfo'
        self.topics_file_1 = StringIO(
            "Version 7.3\nlabel: 11\n"
            "0 1.1 2.2\n"
            "1 1.11 2.22")
        self.num_topics_1 = 2
        self.predictions_file_1 = StringIO(
            "0.0 0.0 doc1\n"
            "0.0 0.0 doc2\n"
            "1.1 2.2 doc1\n"
            "1.11 2.22 doc2")
        self.start_line_1 = 2

    def test_parse_varinfo_01(self):
        result = vw_helpers.parse_varinfo(self.varinfo_path)
        benchmark = pd.DataFrame(
            {
                'feature_name': ['bcc', 'illiquids'], 
                'hash_val': [77964, 83330], 
                'max_val': [1., 2.], 
                'min_val': [0., 5.], 
                'rel_score': [1., 0.6405],
                'weight': [0.2789, -0.1786]}).set_index('hash_val')
        assert_frame_equal(result, benchmark)

    def test_parse_lda_topics_01(self):
        result = vw_helpers.parse_lda_topics(
            self.topics_file_1, self.num_topics_1, normalize=False)
        benchmark = pd.DataFrame(
            {'hash_val': [0, 1], 'topic_0': [1.1, 1.11], 'topic_1': [2.2, 2.22]}
            ).set_index('hash_val')
        assert_frame_equal(result, benchmark)

    def test_parse_lda_predictions_01(self):
        result = vw_helpers.parse_lda_predictions(
            self.predictions_file_1, self.num_topics_1, self.start_line_1,
            normalize=False)
        benchmark = pd.DataFrame(
            {'doc_id': ['doc1', 'doc2'], 'topic_0': [1.1, 1.11],
                'topic_1': [2.2, 2.22]}).set_index('doc_id')
        assert_frame_equal(result, benchmark)

    def test_find_start_line_lda_predictions(self):
        result = vw_helpers.find_start_line_lda_predictions(
            self.predictions_file_1, self.num_topics_1)
        self.assertEqual(result, 2)


class TestSFileFilter(unittest.TestCase):
    def setUp(self):
        self.outfile = StringIO()
        formatter = text_processors.VWFormatter()
        self.sfile_filter = text_processors.SFileFilter(
            formatter, bit_precision=20)
        self.hash_fun = self.sfile_filter._get_hash_fun()
    
    @property
    def sfile_1(self):
        return StringIO(
            " 1 doc1| word1:1 word2:2\n"
            " 1 doc2| word1:1.1 word3:2")

    def test_load_sfile_fwd_1(self):
        token2id, token_score, doc_freq, num_docs = (
            self.sfile_filter._load_sfile_fwd(self.sfile_1))
        self.assertEqual(num_docs, 2)
        self.assertEqual(len(token2id), 3)
        self.assertEqual(token_score, {'word1': 2.1, 'word2': 2, 'word3': 2})
        self.assertEqual(doc_freq, {'word1': 2, 'word2': 1, 'word3': 1})

    def test_load_sfile_rev_1(self):
        # No collisions
        token2id = {'one': 1, 'two': 2}
        id2token = self.sfile_filter._load_sfile_rev(token2id)
        benchmark = {1: 'one', 2: 'two'}
        self.assertEqual(id2token, benchmark)

    def test_load_sfile_rev_2(self):
        # One collision, both '0' and '100' map to 0
        token2id = {str(i): i for i in range(50)}
        token2id['100'] = 0
        id2token = self.sfile_filter._load_sfile_rev(token2id, seed=1976)
        benchmark = {i: str(i) for i in range(50)}
        benchmark[893658] = '0'
        benchmark[0] = '100'
        self.assertEqual(id2token, benchmark)

    def test_resolve_collisions(self):
        token2id = {str(i): random.randint(0, 5) for i in range(10)}
        id_counts = Counter(token2id.values())
        id2token = {
            v: k for k, v in token2id.iteritems() if id_counts[v] == 1}
        collisions = set(
            k for k, v in token2id.iteritems() if id_counts[v] > 1)
        self.sfile_filter._resolve_collisions_core(
            collisions, id_counts, token2id, id2token)
        # Check that the dicts are inverses of each other
        token2id_rev = {v: k for k, v in token2id.iteritems()}
        self.assertEqual(token2id_rev, id2token)

    def check_keys(self, sfile_filter, benchmark_key_list):
        all_keys = [
            sfile_filter.token2id.keys(), sfile_filter.token_score.keys(),
            sfile_filter.doc_freq.keys()]

        for keys in all_keys:
            self.assertEqual(set(keys), set(benchmark_key_list))

    def test_load_sfile_1(self):
        self.sfile_filter.load_sfile(self.sfile_1)
        self.check_keys(self.sfile_filter, ['word1', 'word2', 'word3'])

    def test_remove_tokens(self):
        self.sfile_filter.load_sfile(self.sfile_1)
        self.sfile_filter.remove_tokens('word1')
        self.check_keys(self.sfile_filter, ['word2', 'word3'])

    def test_remove_extreme_tokens_1(self):
        self.sfile_filter.load_sfile(self.sfile_1)
        self.sfile_filter.remove_extreme_tokens(doc_freq_min=2)
        self.check_keys(self.sfile_filter, ['word1'])

    def test_remove_extreme_tokens_2(self):
        self.sfile_filter.load_sfile(self.sfile_1)
        self.sfile_filter.remove_extreme_tokens(doc_freq_max=1)
        self.check_keys(self.sfile_filter, ['word2', 'word3'])

    def test_remove_extreme_tokens_3(self):
        self.sfile_filter.load_sfile(self.sfile_1)
        self.sfile_filter.remove_extreme_tokens(doc_fraction_max=0.5)
        self.check_keys(self.sfile_filter, ['word2', 'word3'])

    def test_remove_extreme_tokens_4(self):
        self.sfile_filter.load_sfile(self.sfile_1)
        self.sfile_filter.remove_extreme_tokens(doc_fraction_min=0.8)
        self.check_keys(self.sfile_filter, ['word1'])

    def test_filter_sfile_1(self):
        self.sfile_filter.load_sfile(self.sfile_1)
        self.sfile_filter.remove_tokens('word1')
        self.sfile_filter.resolve_collisions()
        self.sfile_filter.filter_sfile(self.sfile_1, self.outfile)
        result = self.outfile.getvalue()
        benchmark = (
            " 1 doc1| %d:2\n"
            " 1 doc2| %d:2\n" %
            (self.hash_fun('word2'), self.hash_fun('word3')))
        self.assertEqual(result, benchmark)

    def test_filter_sfile_2(self):
        self.sfile_filter.load_sfile(self.sfile_1)
        self.sfile_filter.resolve_collisions()
        self.sfile_filter.filter_sfile(
            self.sfile_1, self.outfile, doc_id_list=['doc1'])
        result = self.outfile.getvalue()
        benchmark = (
            " 1 doc1| %d:1 %s:2\n" % 
            (self.hash_fun('word1'), self.hash_fun('word2')))
        self.assertEqual(result, benchmark)

    def test_filter_sfile_3(self):
        self.sfile_filter.load_sfile(self.sfile_1)
        self.sfile_filter.remove_tokens('word1')
        self.sfile_filter.resolve_collisions()
        self.sfile_filter.filter_sfile(
            self.sfile_1, self.outfile, doc_id_list=['doc1'])
        result = self.outfile.getvalue()
        benchmark = (" 1 doc1| %s:2\n" % (self.hash_fun('word2')))
        self.assertEqual(result, benchmark)

    def test_filter_sfile_4(self):
        self.sfile_filter.load_sfile(self.sfile_1)
        self.sfile_filter.resolve_collisions()
        self.sfile_filter.filter_sfile(
            self.sfile_1, self.outfile, doc_id_list=['doc1', 'unseen'],
            enforce_all_doc_id=False)
        result = self.outfile.getvalue()
        benchmark = (
            " 1 doc1| %d:1 %s:2\n" % 
            (self.hash_fun('word1'), self.hash_fun('word2')))
        self.assertEqual(result, benchmark)

    def test_filter_sfile_5(self):
        self.sfile_filter.load_sfile(self.sfile_1)
        self.sfile_filter.resolve_collisions()
        with self.assertRaises(AssertionError) as cm:
            self.sfile_filter.filter_sfile(
                self.sfile_1, self.outfile, doc_id_list=['doc1', 'unseen'])
    
    def tearDown(self):
        self.outfile.close()


class TestTopic(unittest.TestCase):
    def setUp(self):
        self.Topics = topic_seek.Topics
        self.streamer = streamers.TextFileStreamer()
        def token_stream(tokens, doc_id=None):
            return tokens
        self.streamer.token_stream = token_stream

    def test_dictionary(self):
        tokens1 = ['Hi', 'this', 'is', 'is', 'not', 'is', 'this']
        tokens2 = ['one', 'two', 'one', 'three']
        T = self.Topics()
        T.streamer = ListStream([tokens1, tokens2])
        T.set_dictionary(no_below=0, no_above=1)
        result = T.dictionary.items()
        benchmark = [(0, 'this'), (1, 'is'), (2, 'three'), (3, 'two'),
                (4, 'Hi'), (5, 'not'), (6, 'one')]        
        self.assertEqual(result, benchmark)

    def test_get_words_docfreq(self):
        tokens1 = ['Hi', 'this', 'is', 'is', 'not', 'is', 'this']
        tokens2 = ['one', 'two', 'one', 'three']
        T = self.Topics()
        T.streamer = ListStream([tokens1, tokens2])
        T.set_dictionary(no_below=0, no_above=1)
        result = T.get_words_docfreq()
        benchmark = pd.DataFrame({'tokenid': [3,2,0,6,5,1,4], 'docfreq': [1]*7}, 
                index=['two', 'three', 'this', 'one', 'not', 'is', 'Hi'])
        benchmark = benchmark[['tokenid', 'docfreq']]
        assert_frame_equal(result, benchmark)


class ListStream(object):
    def __init__(self, token_lists):
        self.token_lists = token_lists

    def token_stream(self, doc_id=None):
        """
        Uses 'dummy doc_id' as this is called in streamer applicatioins.
        """
        for t in self.token_lists:
            yield t

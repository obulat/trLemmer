# -*- coding: utf-8 -*-
import collections

from nltk.tokenize import word_tokenize, sent_tokenize
from trLemmer import tr
from trLemmer.formatters import UDFormatter, DefaultFormatter
from trLemmer.lexicon import RootLexicon
from trLemmer.morphotactics import TurkishMorphotactics
from trLemmer.rulebasedanalyzer import RuleBasedAnalyzer
from typing import List, Tuple

"""Main module."""

_Parse = collections.namedtuple('Parse', 'word, lemma, morphemes, formatted')


class Parse(_Parse):
    """
    Parse result wrapper. Based on https://github.com/kmike/pymorphy2/blob/master/pymorphy2/analyzer.py
    TODO: Decide which methods to add
    """
    pass


def split_sentences(text):
    """ Splits text into sentences, returns a list of sentences."""
    return sent_tokenize(text, language="turkish")


def _normalize(word):
    word = tr.normalize_circumflex(tr.lower(word))
    # TODO: Decide what to do with apostrophes
    word = word.replace("'", "")
    return word


def _tokenize_sentence(sentence):
    return word_tokenize(sentence.replace("'", "").replace("’", ""), language="turkish")


class MorphAnalyzer:
    """
    Morphological analyzer for Turkish language.

    It analyzes each word to suggest all possible morphological analyses,
    as well as lemmas.

    Create a :class:`TrLemmer` object ::

        >>> import trLemmer
        >>> lemmer = trLemmer.MorphAnalyzer()

    Analyzer uses default text dictionaries
    (TODO: sources), as well as an optional unknown word analyzer).
    You can also add your own dictionary files in .txt format, with
    each word on its own line.

        # >>> lemmer.add_dictionary(path='/path/to/file')

    TrLemmer can analyze or lemmatize words and sentences.

        >>> lemmer.lemmatize('beyazlaştırmak')
        ['beyaz']

    #TODO: Add analysis for words with apostrophes
    Methods should be:
    analyze: for one word only
    analyze_text: for texts, to be split by sentences and analyzed by sentences
    lemmatize: for one word only
    lemmatize_text: for texts, to be split by sentences and lemmatized by sentences
    _analyze_sentence: for inner use, when analyze_text is used, chooses which Parse to use for each word
    _lemmatize_sentence: for inner use, when lemmatize_text is used, chooses which Parse to use for each word

    Each method uses method _parse to get SingleAnalysis for the word
    """

    formatters = {"UD": UDFormatter}

    def __init__(self, lexicon=None, formatter=None):
        self.lexicon = (
            lexicon if lexicon is not None else RootLexicon.default_text_dictionaries()
        )
        self.morphotactics = TurkishMorphotactics(self.lexicon)
        self.analyzer = RuleBasedAnalyzer(self.morphotactics)
        self.formatter = (
            DefaultFormatter(True)
            if formatter is None
            else MorphAnalyzer.formatters[formatter]()
        )

    def _parse(self, word: str):
        """ Parses a word and returns SingleAnalysis result. """
        normalized_word = _normalize(word)
        return self.analyzer.analyze(normalized_word)

    def analyze(self, word) -> List[Parse]:
        analysis = self._parse(word)
        if len(analysis) == 0:
            return [Parse(word, 'Unk', 'Unk', 'Unk')]
        result = []
        for a in analysis:
            if a is not None:
                formatted = self.formatter.format(a)
                morpheme_list = [m[0].id_ for m in a.morphemes]
                result.append(Parse(word, a.dict_item.lemma, morpheme_list, formatted))
            else:
                result.append(Parse(word, 'Unk', 'Unk', 'Unk'))
        return result

    def lemmatize(self, word):
        analysis = self._parse(word)
        if len(analysis) == 0:
            return [word]
        else:
            return list(set([a.dict_item.lemma for a in analysis]))

    def lemmatize_text(self, text: str) -> List[Tuple[str, List]]:
        """
        This method will eventually use some form of disambiguation for lemmatizing.
        Currently it simply returns all lemmas available for each word in each sentence.
        :param text: The text which needs lemmatization. It will be split into sentences,
        each of which will be lemmatized by word
        :return: A list of tuples: sentence and a list of list of lemmas for all words
        """
        result = []
        sentences = split_sentences(text)
        for sentence in sentences:
            sentence_lemmas = self._lemmatize_sentence(sentence)
            result.append((sentence, sentence_lemmas))
        return result

    def analyze_text(self, text, verbose=False):
        result = []
        sentences = sent_tokenize(text, language="turkish")
        for sentence in sentences:
            sentence_analysis = self._analyze_sentence(sentence)
            result.append((sentence, sentence_analysis))
        return result

    def _analyze_sentence(self, sentence):
        result = []
        for word in _tokenize_sentence(sentence):
            result.append(self.analyze(word))
        return result

    def _lemmatize_sentence(self, sentence: str) -> List[Tuple[str, List[str]]]:
        result = []
        words = _tokenize_sentence(sentence)
        for word in words:
            result.append((word, self.lemmatize(word)))
        return result

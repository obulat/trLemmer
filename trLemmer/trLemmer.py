# -*- coding: utf-8 -*-
from trLemmer.lexicon import RootLexicon
from trLemmer.morphotactics import TurkishMorphotactics
from trLemmer.rulebasedanalyzer import RuleBasedAnalyzer

"""Main module."""


class TrLemmer:
    """Main class that initializes the vocabulary and analyzes input"""

    def __init__(self, lexicon=None):
        self.lexicon = lexicon if lexicon is not None else RootLexicon()
        self.morphotactics = TurkishMorphotactics(self.lexicon)
        self.analyzer = RuleBasedAnalyzer(self.morphotactics)

    def analyze_word(self, word):
        return self.analyzer.analyze(word)

    def lemmatize(self, word):
        analysis = self.analyzer.analyze(word)
        return analysis[0].dict_item.lemma

    def analyze_sentense(self, sentence):
        return sentence

# -*- coding: utf-8 -*-
from trLemmer import tr
from trLemmer.lexicon import RootLexicon
from trLemmer.morphotactics import TurkishMorphotactics
from trLemmer.rulebasedanalyzer import RuleBasedAnalyzer

"""Main module."""


class TrLemmer:
    """Main class that initializes the vocabulary and analyzes input"""

    def __init__(self, lexicon=None):
        self.lexicon = lexicon if lexicon is not None else RootLexicon.default_text_dictionaries()
        self.morphotactics = TurkishMorphotactics(self.lexicon)
        self.analyzer = RuleBasedAnalyzer(self.morphotactics)

    def analyze_word(self, word):
        return self.analyzer.analyze(word)

    def lemmatize(self, word):
        analysis = self.analyzer.analyze(word)
        if len(analysis) == 0:
            return word
        elif len(analysis) == 1:
            return analysis[0].dict_item.lemma
        else:
            return [a.dict_item.lemma for a in analysis]
        # return analysis[0].dict_item.lemma

    def analyze_sentense(self, sentence):
        return sentence

    def lemmatize_sentence(self, sentence):
        result = []
        for i, word in enumerate(sentence.split()):
            if i == 0:
                wd = tr.lower(word).replace(',', '')
                result.append(self.lemmatize(wd))
            else:
                result.append(self.lemmatize(word))
        return result

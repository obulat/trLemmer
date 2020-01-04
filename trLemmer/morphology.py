# -*- coding: utf-8 -*-
import collections

from nltk.tokenize import word_tokenize, sent_tokenize
from trLemmer import tr
from trLemmer.attributes import RootAttribute, SecondaryPos
from trLemmer.lexicon import RootLexicon
from trLemmer.morphotactics import TurkishMorphotactics, SearchPath, pnon, nom
from trLemmer.rulebasedanalyzer import RuleBasedAnalyzer
import typing

"""Main module."""


class UDFormatter:
    posessives = {
        'P1sg': ('|Number[psor]=Sing', '|Person[psor]=1'),
        'P1pl': ('|Number[psor]=Plur', '|Person[psor]=1'),
        'P2sg': ('|Number[psor]=Sing', '|Person[psor]=2'),
        'P2pl': ('|Number[psor]=Plur', '|Person[psor]=2'),
        'P3sg': ('|Number[psor]=Sing', '|Person[psor]=3'),
        'P3pl': ('|Number[psor]=Plur', '|Person[psor]=3')
    }
    agreement_values = {
        'A1sg': ('Sing', '1'),
        'A1pl': ('Plur', '1'),
        'A2sg': ('Sing', '2'),
        'A2pl': ('Plur', '2'),
        'A3sg': ('Sing', '3'),
        'A3pl': ('Plur', '3')
    }
    cases = ["Nom", "Dat", "Acc", "Abl", "Loc", "Ins", "Gen", "Equ"]

    def __init__(self, add_surface=True):
        self.add_surface = add_surface

    def format_adj(self, analysis):
        nadj_str = "Case={case}|Number={number}|{npsor}|Person={person}{psor}"
        ids = [m.id_ for m in analysis.morphemes]
        case = ''
        number = ''
        person = ''
        npsor = ''
        psor = ''
        if 'Noun' in ids:
            for m_id in ids:
                if m_id in UDFormatter.cases:
                    case = m_id
                else:
                    possessive = UDFormatter.posessives.get(m_id)
                    if possessive is not None:
                        npsor, psor = possessive
                    else:
                        agreement = UDFormatter.agreement_values.get(m_id)
                        if agreement is not None:
                            number, person = agreement
            return nadj_str.format(case=case, number=number,
                                   npsor=npsor, person=person,
                                   psor=psor)
        else:
            return self.format(analysis)

    def format_noun(self, analysis):
        noun_str = "{}Case={}|Number={}{}|Person={}{}"
        case = ''
        number = ''
        person = ''
        number_psor = ''
        person_psor = ''
        for m in analysis.morphemes:
            morph = m[0]
            # print("\tMorph id: ", morph.id_)
            if morph.id_ in UDFormatter.cases:
                case = morph.id_
            possessive_value = UDFormatter.posessives.get(morph.id_)
            agreement_value = UDFormatter.agreement_values.get(morph.id_)
            if possessive_value is not None:
                number_psor, person_psor = possessive_value
            if agreement_value is not None:
                number, person = agreement_value

        if case == '':
            case = 'Nom'
        if analysis.dict_item.secondary_pos == SecondaryPos.Abbreviation:
            abbr = "Abbr=Yes|"
        else:
            abbr = ''
        return noun_str.format(abbr, case, number, number_psor, person, person_psor)

    def format_num(self, analysis):
        return f"NumType={analysis.dict_item.secondary_pos.value}"

    def format_pron(self, analysis):
        prontypestr = analysis.dict_item.secondary_pos.value

        if prontypestr == "Pers":
            prontype = f"|PronType=Prs"
        elif prontypestr == 'Reflex':
            prontype = "|Reflex=Yes"
        elif prontypestr == 'Demons':
            prontype = "|PronType=Dem"
        elif prontypestr == 'Ques':
            prontype = ''
        else:
            prontype = f"|PronType={prontypestr}"
        person = ''
        number = ''
        case = ''
        number_psor = ''
        person_psor = ''
        for m in analysis.morphemes:
            morph = m[0]
            agreement_value = UDFormatter.agreement_values.get(morph.id_)
            if agreement_value is not None:
                number, person = agreement_value
            if prontypestr == "Reflex" or prontypestr == 'Quant':
                psor = UDFormatter.posessives.get(morph.id_)
                if psor is not None:
                    number_psor, person_psor = psor
            if morph.id_ in UDFormatter.cases:
                case = morph.id_
        if case == '':
            case = 'Nom'
        pron_str = "Case={case}|Number={number}{number_psor}|Person={person}{person_psor}{prontype}"

        return pron_str.format(case=case, number=number, number_psor=number_psor, person_psor=person_psor,
                               person=person, prontype=prontype)

    def format_verb(self, analysis):
        aspect = ''
        mood = ''
        number = ''
        person = ''
        polarity = ''
        tense = ''
        case = ''
        verb_form = ''
        number_psor = ''
        person_psor = ''
        evident = ''
        voice = ''
        register = ''
        agreement_values = {
            'A1sg': ('Sing', '1'),
            'A1pl': ('Plur', '1'),
            'A2sg': ('Sing', '2'),
            'A2pl': ('Plur', '2'),
            'A3sg': ('Sing', '3'),
            'A3pl': ('Plur', '3')
        }
        posessives = {
            'P1sg': ('|Number[psor]=Sing', '|Person[psor]=1'),
            'P1pl': ('|Number[psor]=Plur', '|Person[psor]=1'),
            'P2sg': ('|Number[psor]=Sing', '|Person[psor]=2'),
            'P2pl': ('|Number[psor]=Plur', '|Person[psor]=2'),
            'P3sg': ('|Number[psor]=Sing', '|Person[psor]=3'),
            'P3pl': ('|Number[psor]=Plur', '|Person[psor]=3')
        }
        last_part = ''
        morph_ids = [_[0].id_ for _ in analysis.morphemes]

        for k, m in enumerate(analysis.morphemes):
            morph = m[0]
            if morph.id_ in ["Nom", "Dat", "Acc", "Abl", "Loc", "Ins", "Gen", "Equ"]:
                case = f"|Case={morph.id_}"

            agreement_value = agreement_values.get(morph.id_)
            if agreement_value is not None and k == len(analysis.morphemes) - 1:
                number, person = agreement_value
            posessive_value = posessives.get(morph.id_)
            if posessive_value is not None:
                number_psor, person_psor = posessive_value
            if morph.id_ == 'Prog1':
                register = "|Polite=Infm"
            elif morph.id_ == 'Prog2':
                register = "|Polite=Form"
            if morph.id_ in ['Past', 'Pres', 'Fut']:
                if tense == 'Past' and morph.id_ == 'Past':
                    tense = 'Pqp'

                elif tense == '':
                    tense = morph.id_

                # if verb_form == 'Part':
                #     tense = 'Pqp'
            if morph.id_ == 'PastPart':
                tense = 'Past'
            elif morph.id_ == "FutPart":
                tense = "Fut"
                verb_form = 'Part'
            if morph.id_ == 'NarrPart':
                tense = 'Past'
                verb_form = "Part"
                evident = '|Evident=Nfh'
            if morph.id_ == 'Aor':
                aspect = 'Hab'
            if morph.id_ == 'AorPart':
                aspect = 'Hab'
                verb_form = 'Part'
            if morph.id_ == 'Narr':
                if not 'Past' in morph_ids:
                    evident = "|Evident=Nfh"
                tense = 'Past'
            if morph.id_ == "Pass":
                voice = "|Voice=Pass"
            elif morph.id_ == 'Caus':
                voice = '|Voice=Cau'
            if morph.id_ == "PresPart" or morph.id_ == "PastPart":
                verb_form = "Part"
            if morph.id_ == 'Noun' and verb_form == '':
                verb_form = 'Vnoun'
            if morph.id_ == "Opt":
                mood = 'Opt'
            elif morph.id_ == "Desr" or morph.id_ == "Cond":
                mood = 'Cnd'
            elif morph.id_ == 'Unable' or morph.id_ == 'Able':
                mood = 'Pot'
            elif morph.id_ == "Imp":
                mood = "Imp"
            if morph.id_ == "Neg" or morph.id_ == 'Unable':
                polarity = "Neg"
            if morph.id_ in ['Prog1', 'Prog2']:
                aspect = 'Prog'
            if morph.id_ == 'Adv':
                verb_form = "Conv"
        if polarity.strip() == "":
            polarity = "Pos"
        if tense.strip() == '':
            tense = 'Pres'
        if mood.strip() == '':
            mood = 'Ind'
        if aspect.strip() == '':
            aspect = "Perf"

        if verb_form != '':
            last_part += f"|VerbForm={verb_form}"
            if verb_form == 'Vnoun' and case == '':
                case = '|Case=Nom'
        if number != '':
            if verb_form == '':
                number = "|Number=" + number
            else:
                number = ''
        if person != '':
            if verb_form == '':
                person = "|Person=" + person
            else:
                person = ''
        if 'Noun' in morph_ids:
            noun_deriv = morph_ids.index('Noun')
            for id_ in morph_ids[noun_deriv:]:
                if id_ in ["Nom", "Dat", "Acc", "Abl", "Loc", "Ins", "Gen", "Equ"]:
                    case = f"|Case={morph.id_}"
                if case == '':
                    case = "|Case=Nom"
        if 'Fut' in morph_ids and 'Past' in morph_ids:
            tense = 'Fut,Past'
        verb_str = "Aspect={aspect}{evident}{case}|Mood={mood}" \
                   "{number_psor}{number}{person_psor}{person}" \
                   "|Polarity={polarity}{register}|Tense={tense}{last_part}{voice}".format(
            aspect=aspect,
            evident=evident,
            case=case,
            mood=mood,
            number_psor=number_psor,
            number=number,
            person_psor=person_psor,
            person=person,
            polarity=polarity,
            register=register,
            tense=tense,
            last_part=last_part,
            voice=voice
        )
        return verb_str

    def format(self, analysis) -> str:
        pos = analysis.dict_item.primary_pos.value
        if pos == "Noun":
            return self.format_noun(analysis)
        elif pos == "Verb":
            return self.format_verb(analysis)
        elif pos == "Pron":
            return self.format_pron(analysis)
        elif pos == "Num":
            return self.format_num(analysis)

        # result = f"[{analysis.dict_item.lemma}:{analysis.dict_item.primary_pos.value}"
        # if analysis.dict_item.secondary_pos != SecondaryPos.NONE:
        #     result = (
        #         f"{result},{analysis.dict_item.secondary_pos.name}] "
        #     )  # TODO: check name works
        # else:
        #     result = f"{result}] "
        result = ""
        result += self.format_morphemes(stem=analysis.stem, surfaces=analysis.morphemes)
        return result

    def format_morphemes(self, stem, surfaces):
        result = []
        if self.add_surface:
            result.append(f"{stem}:")
        result.append(surfaces[0][0].id_)
        if len(surfaces) > 1 and not surfaces[1][0].derivational:
            result.append(" + ")
        for i, sf in enumerate(surfaces):
            if i == 0:
                continue
            m, surface = sf
            if m.derivational:
                result.append(" | ")
            if self.add_surface and len(surface) > 0:
                result.append(f"{surface}:")
            result.append(m.id_)
            if m.derivational:
                result.append("→")
            elif i < len(surfaces) - 1 and not surfaces[i + 1][0].derivational:
                result.append(" + ")
        return "".join(result)


_Parse = collections.namedtuple('Parse', 'word, lemma, morphemes, formatted_form')


class Parse(_Parse):
    """
    Parse result wrapper. Based on https://github.com/kmike/pymorphy2/blob/master/pymorphy2/analyzer.py
    TODO: Decide which methods to add
    """
    pass


class MorphAnalyzer:
    """
    Morphological analyzer for Turkish language.

    It analyzes each word to suggest all possible morphological analyses,
    as well as lemmas.

    Create a :class:`TrLemmer` object ::

        >>> import trLemmer
        >>> lemmer = trLemmer.TrLemmer()

    Analyzer uses default text dictionaries
    (TODO: sources), as well as an optional unknown word analyzer).
    You can also add your own dictionary files in .txt format, with
    each word on its own line.

        # >>> lemmer.add_dictionary(path='/path/to/file')

    TrLemmer can analyze or lemmatize words and sentences.

        >>> lemmer.lemmatize_word('beyazlaştırmak')
        ['beyaz']

    #TODO: Add analysis for words with apostrophes
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

    def analyze(self, text, verbose=False):
        result = []
        sentences = sent_tokenize(text, language="turkish")
        for sentence in sentences:
            sentence_analysis = self.analyze_sentence(sentence)
            result.append((sentence, sentence_analysis))
        return result

    @staticmethod
    def normalize_word(word):
        word = tr.normalize_circumflex(tr.lower(word))
        # TODO: Decide what to do with apostrophes
        word = word.replace("'", "")
        return tr.lower(word)

    def lemmatize(self, text, by_sent=False, no_punctuation=False):
        import string

        punctuation = list(string.punctuation)
        punctuation.remove("'")
        print(f"Punctuation: {string.punctuation}/ {punctuation}")
        result = []
        sentences = sent_tokenize(text, language="turkish")
        if by_sent:
            for sentence in sentences:
                sentence_lemmas = self.lemmatize_sentence(sentence, no_punctuation)
                result.append((sentence, sentence_lemmas))
        else:
            for word in word_tokenize(text, language="turkish"):
                res_word = []
                for letter in word:
                    if letter not in punctuation:
                        res_word.append(letter)
                word = "".join(res_word)
                if word:
                    lemmas = self.lemmatize_word(tr.lower(word))
                    result.append((word, lemmas))
        return result

    def analyze_word(self, word) -> typing.List[Parse]:
        normalized_word = self.normalize_word(word)
        analysis = self.analyzer.analyze(normalized_word)
        if len(analysis) == 0:
            return [Parse(word, 'Unk', 'Unk', 'Unk')]
        result = []
        for a in analysis:
            formatted = self.formatter.format(a)
            morpheme_list = [m[0].id_ for m in a.morphemes]
            result.append(Parse(word, a.dict_item.lemma, morpheme_list, formatted))
        return result

    def lemmatize_word(self, word):
        analysis = self.analyzer.analyze(word)
        if len(analysis) == 0:
            return [word]
        else:
            return list(set([a.dict_item.lemma for a in analysis]))

    def analyze_sentence(self, sentence):
        result = []
        for word in word_tokenize(sentence, language="turkish"):
            result.append(self.analyze_word(word))
        return result

    def lemmatize_sentence(self, sentence, no_punctuation=True):
        from trLemmer import tr
        import string

        punct = string.punctuation
        result = []
        # words = [_ for _ in re.split(r"(\W+)", sentence) if _ != ' ']
        words = word_tokenize(sentence, language="turkish")
        for word in words:
            if no_punctuation and word in punct:
                continue
            res_word = []
            for letter in word:
                if letter not in punct:
                    res_word.append(letter)
            word = "".join(res_word)
            if word:
                analysis = self.lemmatize_word(tr.lower(word))
                result.append((word, analysis))
        return result


class DefaultFormatter:
    def __init__(self, add_surface=True):
        self.add_surface = add_surface

    def format(self, analysis) -> str:
        result = f"[{analysis.dict_item.lemma}:{analysis.dict_item.primary_pos.value}"
        if analysis.dict_item.secondary_pos != SecondaryPos.NONE:
            result = (
                f"{result},{analysis.dict_item.secondary_pos.value}] "
            )  # TODO: check name works
        else:
            result = f"{result}] "
        result = ""
        result += self.format_morphemes(stem=analysis.stem, surfaces=analysis.morphemes)
        return result

    def format_morphemes(self, stem, surfaces):
        result = []
        if self.add_surface:
            result.append(f"{stem}:")
        result.append(surfaces[0][0].id_)
        if len(surfaces) > 1 and not surfaces[1][0].derivational:
            result.append(" + ")
        for i, sf in enumerate(surfaces):
            if i == 0:
                continue
            m, surface = sf
            if m.derivational:
                result.append(" | ")
            if self.add_surface and len(surface) > 0:
                result.append(f"{surface}:")
            result.append(m.id_)
            if m.derivational:
                result.append("→")
            elif i < len(surfaces) - 1 and not surfaces[i + 1][0].derivational:
                result.append(" + ")
        return "".join(result)


class SingleAnalysis:
    """
       This class represents a single morphological analysis result.
       :param dict_item: Dictionary Item of the analysis.
       :param morpheme_data_list: Contains Morphemes and their surface form (actual appearance in the normalized input)
       List also contain the root (unchanged or modified) of the Dictionary item.
       For example, for normalized input "kedilere"
       This list may contain "kedi:Noun, ler:A3pl , e:Dat" information.
       :param group_boundaries: groupBoundaries holds the index values of morphemes.
       """

    def __init__(self, search_path: SearchPath):
        self.path = search_path
        self.morphemes = []
        self.derivation_count = 0
        self.dict_item = None
        self.group_boundaries = []
        self.parse_dict_item_and_boundaries()

    def __repr__(self):
        return f"{self.dict_item}-{self.morphemes}"

    def parse_dict_item_and_boundaries(self):
        for transition in self.path.transitions:
            if transition.is_derivative:
                self.derivation_count += 1
            morpheme = transition.morpheme
            # we skip these two morphemes as they create visual noise and does not carry much information.
            if morpheme == nom or morpheme == pnon:
                continue
            if len(transition.surface) == 0:
                morpheme_data = (morpheme, "")
                self.morphemes.append(morpheme_data)
                continue
            morpheme_data = (morpheme, transition.surface)
            self.morphemes.append(morpheme_data)
        group_boundaries = [
            0 for _ in range(self.derivation_count + 1)
        ]  # we assume there is always an IG
        group_boundaries[0] = 0
        morpheme_counter = 0
        derivation_counter = 1
        for mdata in self.morphemes:
            if mdata[0].derivational:
                group_boundaries[derivation_counter] = morpheme_counter
                derivation_counter += 1
            morpheme_counter += 1

        # if dictionary item is `Dummy`, use the referenced item.
        # `Dummy` items are usually generated for some compound words. For example for `zeytinyağı`
        # a DictionaryItem is generated with root "zeytinyağ". But here we switch to the original.
        dict_item = self.path.dict_item
        if dict_item.has_attribute(RootAttribute.Dummy):
            dict_item = dict_item.ref_item
        self.dict_item = dict_item
        self.group_boundaries = group_boundaries

    @property
    def stem(self):
        return self.morphemes[0][1]

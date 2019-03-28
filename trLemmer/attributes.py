from collections import namedtuple
from enum import Flag, Enum, auto
import sys
from typing import List

print(sys.path)
sys.path.pop(0)
from trLemmer import tr


class PrimaryPos(Enum):
    Noun = "Noun"
    Adjective = "Adj"
    Adverb = "Adv"
    Conjunction = "Conj"
    Interjection = "Interj"
    Verb = "Verb"
    Pronoun = "Pron"
    Numeral = "Num"
    Determiner = "Det"
    PostPositive = "Postp"
    Question = "Ques"
    Duplicator = "Dup"
    Punctuation = "Punc"
    Unknown = "Unk"


primary_pos_set = set([pos.value for pos in list(PrimaryPos)])


class SecondaryPos(Enum):
    UnknownSec = "Unk"
    DemonstrativePron = "Demons"
    Time = "Time"
    QuantitivePron = "Quant"
    QuestionPron = "Ques"
    ProperNoun = "Prop"
    PersonalPron = "Pers"
    ReflexivePron = "Reflex"
    NONE = "None"
    Ordinal = "Ord"
    Cardinal = "Card"
    Percentage = "Percent"
    Ratio = "Ratio"
    Range = "Range"
    Real = "Real"
    Distribution = "Dist"
    Clock = "Clock"
    Date = "Date"
    Email = "Email"
    Url = "Url"
    Mention = "Mention"
    HashTag = "HashTag"
    Emoticon = "Emoticon"
    RomanNumeral = "RomanNumeral"
    RegularAbbreviation = "RegAbbrv"
    Abbreviation = "Abbrv"

    # Below POS information is for Oflazer compatibility.
    # They indicate that words before Post positive words should end with certain suffixes.
    PCDat = "PCDat"
    PCAcc = "PCAcc"
    PCIns = "PCIns"
    PCNom = "PCNom"
    PCGen = "PCGen"
    PCAbl = "PCAbl"


secondary_pos_set = {'Unk', 'Demons', 'Time', 'Quant', 'Ques', 'Prop', 'Pers', 'Reflex', 'None', 'Ord', 'Card',
                     'Percent',
                     'Ratio', 'Range', 'Real', 'Dist', 'Clock', 'Date', 'Email', 'Url', 'Mention', 'HashTag',
                     'Emoticon',
                     'RomanNumeral', 'RegAbbrv', 'Abbrv', 'PCDat', 'PCAcc', 'PCIns', 'PCNom', 'PCGen', 'PCAbl'}


class RootAttribute(Enum):
    """These represents attributes of roots."""

    # Generally Present tense (Aorist) suffix has the form [Ir]; such as gel-ir, bul-ur, kapat-ır.
    # But for most verbs with single syllable and compound verbs it forms as [Ar].
    # Such as yap-ar, yet-er, hapsed-er. There are exceptions for this case, such as "var-ır".
    # Below two represents the attributes for clearing the ambiguity. These attributes does not
    # modify the root form.
    Aorist_I = auto()
    Aorist_A = auto()

    # If a verb ends with a vowel and Progressive suffix [Iyor] appended, last vowel of the root
    # form drops. Such as "ara → ar-ıyor" "ye → y-iyor".
    # This also applies to suffixes, such as Negative "mA" suffix. "yap-ma → yap-m-ıyor".
    # But suffix case is handled during graph generation.

    # This attribute is added automatically.
    # TODO: This may be combined with LastVowelDrop or changed as LastLetterDrop.
    ProgressiveVowelDrop = auto()

    # For verbs that ends with a vowel or letter "l" Passive voice suffix fors as [+In] and [+InIl].
    # ara-n, ara-nıl and "sarıl-ın-an".
    # For other verbs [+nIl] is used. Such as ser-il, yap-ıl, otur-ul.

    # This attribute is added automatically.
    # TODO: [+nIl] may be changed to [+Il]
    Passive_In = auto()

    # For verbs that has more than one syllable and end with a vowel or letters "l" or "r",
    # Causative suffix form as [t]. Such as: ara-t, oku-t, getir-t, doğrul-t, bağır-t
    # Otherwise it forms as [tIr]. Such as: ye-dir, sat-tır, dol-dur, seyret-tir

    # This attribute is added automatically.
    Causative_t = auto()

    # If last letter of a word or suffix is a stop consonant (tr: süreksiz sert sessiz), and a
    # suffix that starts with a vowel is appended to that word, last letter changes.
    # This is called voicing. Changes are p-b, ç-c, k-ğ, t-d, g-ğ.
    # Such as kitap → kitab-a, pabuç → pabuc-u, cocuk → cocuğ-a, hasat → hasad-ı

    # It also applies to some verbs: et→ed-ecek. But for verb roots, only ‘t’ endings are voiced.
    # And most suffixes: elma-cık→elma-cığ-ı, yap-acak→yap-acağ-ım.

    # When a word ends with ‘nk‘, then ‘k’ changes to ‘g’ instead of ‘ğ’.
    # Such as cenk → ceng-e, çelenk → çeleng-i

    # For some loan words, g-ğ change occurs. psikolog → psikoloğ-a

    # Usually if the word has only one syllable, rule does not apply.
    # Such as turp → turp-u, kat → kat-a, kek → kek-e, küp → küp-üm.
    # But this rule has some exceptions as well: harp → harb-e

    # Some multi syllable words also do not obey this rule.
    # Such as taksirat → taksirat-ı, kapat → kapat-ın
    Voicing = auto()

    # NoVoicing attribute is only used for explicitly marking a word in the dictionary
    # that should not have automatic Voicing attribute. So after a DictionaryItem is created
    # only checking Voicing attribute is enough.
    NoVoicing = auto()

    # For some loan words, suffix vowel harmony rules does not apply. This usually happens in some
    # loan words. Such as saat-ler and alkol-ü
    InverseHarmony = auto()

    # When a suffix that starts with a vowel is added to some words, last letter is doubled.
    # Such as hat → hat-tı

    # If last letter is also changed by the appended suffix, transformed letter is repeated.
    # Such as ret → red-di
    Doubling = auto()

    # Last vowel before the last consonant drops in some words when a suffix starting with a vowel
    # is appended.
    # ağız → ağz-a, burun → burn-um, zehir → zehr-e.

    # Some words have this property optionally. Both omuz → omuz-a, omz-a are valid. Sometimes
    # different meaning of the words effect the outcome such as oğul-u and oğl-u. In first case
    # "oğul" means "group of bees", second means "son".

    # Some verbs obeys this rule. kavur → kavr-ul. But it only happens for passive suffix.
    # It does not apply to other suffixes. Such as kavur→kavur-acak, not kavur-kavracak

    # In spoken conversation, some vowels are dropped too but those are grammatically incorrect.
    # Such as içeri → içeri-de (not ‘içerde’), dışarı → dışarı-da (not ‘dışarda’)

    # When a vowel is dropped, the form of the suffix to be appended is determined by the original
    # form of the word, not the form after vowel is dropped.
    # Such as nakit → nakd-e, lütuf → lütf-un.

    # If we were to apply the vowel harmony rule after the vowel is dropped,
    # it would be nakit → nakd-a and lütuf → lütf-ün, which are not correct.
    LastVowelDrop = auto()

    # This is for marking compound words that ends with third person possesive  suffix P3sg [+sI].
    # Such as aşevi, balkabağı, zeytinyağı.

    # These compound words already contains a suffix so their handling is different than other
    # words. For example some suffixes changes the for of the root.
    # Such as zeytinyağı → zeytinyağ-lar-ı atkuyruğu → atkuyruklu
    CompoundP3sg = auto()

    # No suffix can be appended to this.
    # TODO: this is not yet used. But some words are marked in dictionary.
    NoSuffix = auto()

    # Some Compound words adds `n` instead of `y` when used with some suffixes. Such as `Boğaziçi-ne` not `Boğaziçi-ye`
    # TODO: this is not yet used. But some words are marked in dictionary.
    NounConsInsert_n = auto()

    # This attribute is used for formatting a word. If this is used, when a suffix is added to a Proper noun, no single
    # quote is used as a separator. Such as "Türkçenin" not "Türkçe'nin"
    NoQuote = auto()

    # Some compound nouns cannot be used in root form. For example zeytinyağı -> zeytinyağ. For preventing
    # false positives this attribute is added to the zeytinyağ form of the word. So that representing state cannot
    # be terminal.
    # This is added automatically.
    CompoundP3sgRoot = auto()

    # This is for marking reflexive verbs. Reflexive suffix [+In] can only be added to some verbs.
    # TODO: This is defined but not used in morphotactics.
    Reflexive = auto()

    # This is for marking reflexive verbs. Reciprocal suffix [+Iş, +yIş] can only be added to some
    # verbs.
    # TODO: Reciprocal suffix is commented out in morphotactics and reciprocal verbs are added with suffixes.
    # Such as boğuşmak [A:Reciprocal]
    Reciprocal = auto()
    # if a verb cannot be reciprocal.
    NonReciprocal = auto()

    # for items that are not in official TDK dictionary
    Ext = auto()

    # for items that are added to system during runtime
    Runtime = auto()

    # For dummy items. Those are created when processing compound items.
    Dummy = auto()

    # -------------- Experimental attributes.
    ImplicitDative = auto()

    # It contains plural meaning implicitly so adding an external plural suffix is erroneous.
    # This usually applies to arabic loan words. Such as ulema, hayvanat et.
    ImplicitPlural = auto()
    ImplicitP1sg = auto()
    ImplicitP2sg = auto()
    FamilyMember = auto()  # annemler etc.
    PronunciationGuessed = auto()

    # This means word is only used in informal language.
    # Some applications may want to analyze them with a given informal dictionary.
    # Examples: kanka, beyfendi, mütahit, antreman, bilimum, gaste, aliminyum, tırt, tweet
    Informal = auto()

    # This is used for temporary DictionaryItems created for words that cannot be analyzed.
    Unknown = 0


RootAttribute_set = set(list(RootAttribute))


class PhoneticAttribute(Enum):
    # Turkish vowels are: [a, e, ı, i, o, ö, u, ü]
    # Turkish consonants are: [b, c, ç, d, f, g, ğ, h, j, k, l, m, n, p, r, s, ş, t, v, y, z]
    HasVowel = auto()
    HasNoVowel = auto()
    LastLetterVowel = auto()
    LastLetterConsonant = auto()

    # Turkish Frontal vowels are: [e, i, ö, ü]
    LastVowelFrontal = auto()
    # Back vowels are: [a, ı, o, u]
    LastVowelBack = auto()
    # Rounded vowels are: [o, u, ö, ü]
    LastVowelRounded = auto()
    # Unrounded vowels are: [a, e, ı, i]
    LastVowelUnrounded = auto()
    # Turkish voiceless consonants are [ç, f, h, k, p, s, ş, t]
    LastLetterVoiceless = auto()
    # Turkish voiced consonants are [b, c, d, g, ğ, h, j, l, m, n, r, v, y, z]
    LastLetterVoiced = auto()

    # Turkish Voiceless stop consonants are: [ç, k, p, t]. Voiced stop consonants are [b, c, d, g, ğ]
    LastLetterVoicelessStop = auto()
    LastLetterVoicedStop = auto()
    FirstLetterVowel = auto()
    FirstLetterConsonant = auto()

    # ---- experimental -----
    ExpectsVowel = auto()
    ExpectsConsonant = auto()
    ModifiedPronoun = auto()  # ben,sen -> ban, san form.
    UnModifiedPronoun = auto()  # ben,sen -> ben, sen form.
    # for verbs that and with a vowel and to connect `iyor` progressive tense suffix.
    LastLetterDropped = auto()
    CannotTerminate = auto()


no_vowel_attrs = [PhoneticAttribute.LastLetterConsonant, PhoneticAttribute.FirstLetterConsonant,
                  PhoneticAttribute.HasNoVowel]


def calculate_phonetic_attributes(word: str, predecessor_attrs=None) -> List[PhoneticAttribute]:
    # the word should be in lower case
    result = []
    if len(word) == 0:
        return predecessor_attrs
    last_letter = word[-1]
    if last_letter in tr.vowels_lower_set:
        result.append(PhoneticAttribute.LastLetterVowel)
        last_vowel = last_letter
    else:
        result.append(PhoneticAttribute.LastLetterConsonant)
        last_vowel = tr.get_last_vowel(word)
        if last_letter in tr.consonants_voiceless_set:
            result.append(PhoneticAttribute.LastLetterConsonant)
            result.append(PhoneticAttribute.LastLetterVoiceless)
            if last_letter in tr.consonants_voiceless_stop_set:
                result.append(PhoneticAttribute.LastLetterVoicelessStop)
    if last_vowel is not None:
        if last_vowel in tr.vowels_back_set:
            result.append(PhoneticAttribute.LastVowelBack)
        else:
            result.append(PhoneticAttribute.LastVowelFrontal)
        if last_vowel in tr.vowels_rounded_set:
            result.append(PhoneticAttribute.LastVowelRounded)
        else:
            result.append(PhoneticAttribute.LastVowelUnrounded)
    if word[0] in tr.vowels_lower_set:
        result.append(PhoneticAttribute.FirstLetterVowel)
    else:
        result.append(PhoneticAttribute.FirstLetterConsonant)
    if not tr.contains_vowel(word):
        result.append(predecessor_attrs)
        result.append(no_vowel_attrs)
        result.remove(attributes_to_remove)
    return result


if __name__ == '__main__':
    import sys

    print(sys.path)
    attr = calculate_phonetic_attributes('kedi')
    print('Kedi: ', attr, type(attr))

    print('\nSabah: ', calculate_phonetic_attributes('sabah'))

    print('\nBlank: ', calculate_phonetic_attributes(''))

    word = 'bankadan'
    attr = calculate_phonetic_attributes(word)
    attr2 = attr
    print(f"Attr2 is a label for attr: {attr2}, {attr}")
    attr.remove(PhoneticAttribute.LastLetterConsonant)
    print(f"Attr2 is a label for attr: {attr2}, {attr}")

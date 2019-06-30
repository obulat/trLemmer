import re
from collections import namedtuple
from enum import Enum
from pathlib import Path
from typing import List, Set

from trLemmer.attributes import RootAttribute, PrimaryPos, SecondaryPos, primary_pos_set, \
    secondary_pos_set, parse_attr_data, infer_morphemic_attributes, PosInfo
from trLemmer import tr


def load_dict(path):
    result = {}
    with open(path, 'r', encoding='utf8') as inf:
        for line in inf:
            if line.strip().startswith('##') or len(line.strip()) == 0:
                continue
            k, v = [_.strip() for _ in line.split('=')]
            result[k] = v
    return result


RESOURCES_DIR = Path(__file__).parent / 'resources'
tr_letter_pron = load_dict(RESOURCES_DIR / "tr" / "phonetics" / "turkish-letter-names.txt")
en_letter_pron = load_dict(Path(RESOURCES_DIR / "tr" / "phonetics" / "turkish-letter-names.txt"))
en_phones_to_tr = load_dict(Path(RESOURCES_DIR / "tr" / "phonetics" / "english-phones-to-turkish.txt"))


def to_turkish_letter_pronunciation(word):
    if bool(re.search(r'\d', word)):
        return to_turkish_letter_pronunciation_with_digit(word)
    result = []
    for i in range(len(word)):
        c = word[i].lower()
        if c == '-':
            continue
        if c in tr_letter_pron:
            if i == len(word) - 1 and c == 'k':
                result.append("ka")
            else:
                result.append(tr_letter_pron[c])
        else:
            print(f"Cannot guess pronunciation of letter {c} in : {word}")
    return ''.join(result)


def to_turkish_letter_pronunciation_with_digit(word):
    pieces = re.split(r'(\d+)', word)
    result = []
    i = 0
    for piece in pieces:
        if bool(re.search(r'\d', piece)):
            result.append(turkish_numbers_to_string(piece))
            i += 1
            continue
        if i < len(pieces) - 1:
            result.append(to_turkish_letter_pronunciation(piece))
        else:
            result.append(replace_english_specific_chars(piece))
        i += 1

    return ''.join(result)  # replace('[ ]+', '')


singleDigitNumbers = ["", "bir", "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz"]
tenToNinety = ["", "on", "yirmi", "otuz", "kırk", "elli", "altmış", "yetmiş", "seksen", "doksan"]
thousands = ["", "bin", "milyon", "milyar", "trilyon", "katrilyon"]


def convert_three_digit(threeDigitNumber):
    """
    converts a given three digit number.
    :param threeDigitNumber: a three digit number to convert to words.
    :return: turkish string representation of the input number.
    """
    result = ''

    hundreds = threeDigitNumber // 100
    tens = threeDigitNumber // 10
    single_digit = threeDigitNumber % 10

    if hundreds != 0:
        result = "yüz"

    if hundreds > 1:
        result = singleDigitNumbers[hundreds] + " " + result

    result = result + " " + tenToNinety[tens] + " " + singleDigitNumbers[single_digit]
    return result.strip()


def convert_to_string(number):
    """
    returns the Turkish representation of the input. if negative "eksi" string is prepended.
    @param input: input. must be between (including both) -999999999999999999L to
       * 999999999999999999L
       * @return Turkish representation of the input. if negative "eksi" string is prepended.
       * @throws IllegalArgumentException if input value is too low or high.
    """
    MIN_NUMBER = -999999999999999999
    MAX_NUMBER = 999999999999999999
    if number == 0:
        return "sıfır"
    if number < MIN_NUMBER or number > MAX_NUMBER:
        raise ValueError(f"Number is out of bounds: {number}")
    result = ""
    current_pos = abs(number)
    counter = 0
    while current_pos >= 1:
        group_of_three = int(current_pos % 1000)
        if group_of_three != 0:
            if group_of_three == 1 and counter == 1:
                result = thousands[counter] + " " + result
            else:
                result = convert_three_digit(group_of_three) + " " + thousands[counter] + " " + result
        counter += 1
        current_pos /= 1000

    if number < 0:
        return "eksi " + result.strip()
    else:
        return result.strip()


def turkish_numbers_to_string(word):
    """Methods converts a String containing an integer to a Strings."""
    if word.startswith("+"):
        word = word[1:]
    result = []
    i = 0
    for c in word:
        if c == '0':
            result.append("sıfır")
            i += 0
        else:
            break
    rest = word[i:]
    if len(rest) > 0:
        result.append(convert_to_string(int(rest)))  # TODO: probably error, was blank
    # result.append(int(rest))
    return ' '.join(result)


def replace_english_specific_chars(word):
    replacement = {'w': 'v',
                   'q': 'k',
                   'x': 'ks',
                   '-': '',
                   "\\": ''}
    return ''.join([replacement.get(sym, sym) for sym in word])


def guess_for_abbreviation(word):
    """Tries to guess turkish abbreviation pronunciation."""
    syllables = tr.vowel_count(word)

    first_two_cons = False
    if len(word) > 2:
        if tr.contains_vowel(word[:2]):
            first_two_cons = True
    if syllables == 0 or len(word) < 3 or first_two_cons:
        return to_turkish_letter_pronunciation(word)
    else:
        return replace_english_specific_chars(word)


class MetaDataId(Enum):
    POS = "P"
    ATTRIBUTES = "A"
    REF_ID = "Ref"
    ROOTS = "Roots"
    PRONUNCIATION = "Pr"
    SUFFIX = "S"
    INDEX = "Index"


#  A function that parses raw word and metadata information. Represents a single line in dictionary.
def parse_line_data(line):
    word = line.split(" ")[0]
    metadata = {}
    if len(word) == 0:
        raise ValueError(f"Line {line} has no word data")
    meta = line[len(word):].strip()
    if len(meta) == 0:
        return {'word': word, 'metadata': metadata}
    if not meta.startswith('[') or not meta.endswith(']'):
        raise ValueError(f"Malformed metadata, missing brackets. Should be: [metadata]. Line: {line}")
    meta = meta[1:-1]
    for chunk in meta.split(';'):
        if ':' not in chunk:
            raise ValueError(f"Line {line} has malformed metadata chunk {chunk}. It should have a ':' symbol.")
        token_id_str, chunk_data = [_.strip() for _ in chunk.split(':')]
        if len(chunk_data) == 0:
            raise ValueError(f"Line {line} has malformed metadata chunk {chunk} with no chunk data available")
        data_id = MetaDataId(token_id_str)
        metadata[data_id] = chunk_data

    return {'word': word, 'metadata': metadata}


class TextLexiconProcessor:
    def __init__(self, lexicon):
        self.lexicon = lexicon
        self.late_entries = []

    def process_lines(self, lines):
        for line in lines:
            line = line.strip()
            if len(line) > 0 and not line.startswith("##"):
                self.process_line(line)
        self.get_result()

    def process_line(self, line):
        line = line.strip()
        if len(line) == 0 or line.startswith("##"):
            return

        line_data = parse_line_data(line)
        # if a line contains references to other lines, we add them to lexicon later.

        if MetaDataId.REF_ID not in line_data['metadata'] and MetaDataId.ROOTS not in line_data['metadata']:
            dict_item = self.parse_dict_item(line_data)
            if dict_item is not None:
                self.lexicon.add(dict_item)
            else:
                print(f"Dict item is none: {line_data}")
        else:
            self.late_entries.append(line_data)

    @staticmethod
    def is_verb(word):
        return len(word) > 3 and (word.endswith('mek') or word.endswith('mak')) and tr.is_lower(word[0])

    @staticmethod
    def infer_primary_pos(word):
        return PrimaryPos.Verb if TextLexiconProcessor.is_verb(word) else PrimaryPos.Noun

    @staticmethod
    def infer_secondary_pos(word):
        if tr.is_upper(word[0]):
            return SecondaryPos.ProperNoun
        else:
            return SecondaryPos.NONE

    @staticmethod
    def generate_root(word, pos_info):
        if pos_info.primary_pos == PrimaryPos.Punctuation:
            return word
        #  Strip -mek -mak from verbs.
        if pos_info.primary_pos == PrimaryPos.Verb and TextLexiconProcessor.is_verb(word):
            word = word[:-3]

        #  TODO: not sure if we should remove diacritics or convert to lowercase.
        #  Lowercase and normalize diacritics.
        word = tr.normalize_circumflex(tr.lower(word))
        # Remove dashes
        word = word.replace("-", "")
        word = word.replace("'", "")

        return word

    @staticmethod
    def get_pos_data(pos_str, word):
        if pos_str is None:
            # infer the type
            return PosInfo(TextLexiconProcessor.infer_primary_pos(word),
                           TextLexiconProcessor.infer_secondary_pos(word)
                           )
        else:
            primary_pos = None
            secondary_pos = None
            tokens = [_.strip() for _ in pos_str.split(',')]
            if len(tokens) > 2:
                raise ValueError(f"Only two POS tokens are allowed in data chunk: {pos_str}")
            for token in tokens:
                if token not in primary_pos_set and token not in secondary_pos_set:
                    raise ValueError(f"Unrecognized pos data [{token}] in data chunk: {pos_str}")

            #  Ques POS causes some trouble here. Because it is defined in both primary and secondary pos.
            for token in tokens:
                if token in primary_pos_set:
                    if primary_pos is None:
                        primary_pos = PrimaryPos(token)
                        continue
                    else:
                        if pos_str == "Pron,Ques":
                            primary_pos = PrimaryPos("Pron")
                            secondary_pos = SecondaryPos("Ques")
                        else:
                            raise ValueError(f"Multiple primary pos in data chunk: {pos_str}")
                elif token in secondary_pos_set:
                    if secondary_pos is None:
                        secondary_pos = SecondaryPos(token)  # TODO: Test this works
                        continue
                    else:
                        raise ValueError(f"Multiple secondary pos in data chunk: {pos_str}")

            # If there are no primary or secondary pos defined, try to infer them.
            if primary_pos is None:
                primary_pos = TextLexiconProcessor.infer_primary_pos(word)

            if secondary_pos is None:
                secondary_pos = TextLexiconProcessor.infer_secondary_pos(word)

            return PosInfo(primary_pos, secondary_pos)

    def parse_dict_item(self, line_data):
        word = line_data['word']
        metadata = line_data['metadata']
        pos_info = self.get_pos_data(metadata.get(MetaDataId.POS), word)
        clean_word = self.generate_root(word, pos_info)
        index_str = metadata.get(MetaDataId.INDEX)
        index = 0 if index_str is None else int(index_str)
        pronunciation = metadata.get(MetaDataId.PRONUNCIATION)
        pronunciation_guessed = False
        secondary_pos = pos_info.secondary_pos
        if pronunciation is None:
            pronunciation_guessed = True
            if pos_info.primary_pos == PrimaryPos.Punctuation:
                pronunciation = "a"
            elif secondary_pos == SecondaryPos.Abbreviation:
                pronunciation = guess_for_abbreviation(clean_word)
            elif tr.contains_vowel(clean_word):
                pronunciation = clean_word
            else:
                pronunciation = to_turkish_letter_pronunciation(clean_word)
        else:
            pronunciation = tr.lower(pronunciation)

        attr_data = metadata.get(MetaDataId.ATTRIBUTES)
        parsed_attributes = parse_attr_data(attr_data) if attr_data is not None else None
        attributes = infer_morphemic_attributes(pronunciation, pos_info, parsed_attributes)
        if pronunciation_guessed and (
            secondary_pos == SecondaryPos.ProperNoun or secondary_pos == SecondaryPos.Abbreviation):
            attributes.add(RootAttribute.PronunciationGuessed)
            # here if there is an item with same lemma and pos values but attributes are different,
            # we increment the index.
        while True:
            id_ = generate_dict_id(word, pos_info.primary_pos, secondary_pos, index)
            existing_item = self.lexicon.id_dict.get(id_)

            if existing_item is not None and id_ == existing_item.id_:
                if attributes & existing_item.attributes == attributes:
                    print(f"Item already defined: {existing_item}")
                else:
                    index += 1
            else:
                break
        try:

            return DictionaryItem(lemma=word, root=clean_word,
                                  primary_pos=pos_info.primary_pos, secondary_pos=secondary_pos,
                                  attrs=attributes, pronunciation=pronunciation,
                                  index=index)
        except Exception as e:
            print(f"Could not create {word}/{index}/ {type(index)} dictionary item, error: {e} ")

    def get_result(self):
        for entry in self.late_entries:
            if MetaDataId.REF_ID in entry['metadata']:
                reference_id = entry['metadata'].get(MetaDataId.REF_ID)
                if '_' not in reference_id:
                    reference_id = f"{reference_id}_Noun"

                ref_item = self.lexicon.id_dict.get(reference_id)
                if ref_item is None:
                    print("Cannot find reference item id " + reference_id)
                item = self.parse_dict_item(entry)
                item.ref_item = ref_item
                self.lexicon.add(item)
            # this is a compound lemma with P3sg in it. Such as atkuyruğu
            if MetaDataId.ROOTS in entry['metadata']:
                pos_data_str = entry['metadata'].get(MetaDataId.POS)
                pos_info = self.get_pos_data(pos_data_str, entry['word'])
                generated_id = f"{entry['word']}_{pos_info.primary_pos.value}"
                item = self.lexicon.id_dict.get(generated_id)
                if item is None:
                    item = self.parse_dict_item(entry)
                    self.lexicon.add(item)
                r = entry['metadata'].get(MetaDataId.ROOTS)  # at-kuyruk
                root = r.replace("-", "")  # atkuyruk
                if "-" in r:
                    r = r[r.index('-') + 1:]
                ref_items = self.lexicon.get_matching_items(r)  # check lexicon for [kuyruk]
                if len(ref_items) > 0:
                    ref_item = sorted(ref_items, key=lambda item: item.index)[0]
                    attr_set = ref_item.attributes.copy()
                else:
                    attr_set = infer_morphemic_attributes(root, pos_info, set())
                attr_set.add(RootAttribute.CompoundP3sgRoot)
                if RootAttribute.Ext in item.attributes:
                    attr_set.add(RootAttribute.Ext)
                index = 0
                dict_item_id = f"{root}_{item.primary_pos.value}"
                if self.lexicon.id_dict.get(dict_item_id) is not None:
                    index = 1
                    # generate a fake lemma for atkuyruk, use kuyruk's attributes.
                    # But do not allow voicing.
                fake_root = DictionaryItem(root, root, item.primary_pos, item.secondary_pos, attr_set, root, index)
                fake_root.attributes.add(RootAttribute.Dummy)
                if RootAttribute.Voicing in fake_root.attributes:
                    fake_root.attributes.remove(RootAttribute.Voicing)
                fake_root.reference_item = item
                self.lexicon.add(fake_root)
        return self.lexicon


def generate_dict_id(lemma: str, primary_pos: PrimaryPos, secondary_pos: SecondaryPos, index: int):
    result = f"{lemma}_{primary_pos.name}"
    if secondary_pos is not None and secondary_pos != SecondaryPos.NONE:
        result = f"{result}_{secondary_pos.name}"
    if index > 0:
        result = f"{result}_{index}"
    return result


class DictionaryItem:
    """
    This is a class for dictionary items in Lexicon.
    :param lemma: The exact surface form of the item used in dictionary.
    :type lemma: str
    :param root: Form which will be used during graph generation. Such as,
        dictionary Item [gelmek Verb]'s root is "gel"
    :type root: str
    :param primary_pos: Primary POS information
    :type primary_pos: PrimaryPos
    :param secondary_pos: Secondary POS information
    :type secondary_pos: SecondaryPos
    :param attrs: Attributes that this item carries. Such as voicing or vowel drop.
    :type attrs: RootAttribute
    :param pronunciation: Pronunciations of the item. TODO: This should be
    converted to an actual 'Pronunciation' item
    :type pronunciation: str

    :param index:
    :type: int
    """

    def __init__(self, lemma: str,
                 root: str,
                 primary_pos: PrimaryPos,
                 secondary_pos: SecondaryPos,
                 attrs: Set,
                 pronunciation: str,
                 index: int):
        """
        :id_(str)is the unique ID of the item. It is generated from Pos and lemma.
        If there are multiple items with same POS and Lemma user needs to add an index for
        distinction. Structure of the ID: lemma_POS or lemma_POS_index
        """
        self.pronunciation = pronunciation
        self.lemma = lemma
        self.primary_pos = primary_pos
        self.secondary_pos = secondary_pos
        # normalized_lemma: if this is a Verb, removes -mek -mak suffix.Otherwise returns the `lemma`
        self.normalized_lemma = self.lemma[:-3] if self.primary_pos == PrimaryPos.Verb else self.lemma
        self.attributes = attrs
        self.root = root
        self.index = index
        self.id_ = self.generate_id()
        self.ref_item = None

    def __str__(self):
        result = f"{self.lemma} [P:{self.primary_pos.value}]"
        return result

    def __repr__(self):
        return f"DictionaryItem({self.id_})"

    def has_any_attribute(self, root_attrs):

        return bool(set(root_attrs) & self.attributes)

    def has_attribute(self, attr):
        return attr in self.attributes

    def generate_id(self):
        result = [self.lemma, self.primary_pos.value]  # shortForm is value
        if self.secondary_pos is not None and self.secondary_pos != SecondaryPos.NONE:
            result.append(self.secondary_pos.value)
        if self.index > 0:
            result.append(str(self.index))
        return '_'.join(result)

    def __hash__(self):
        return hash((self.id_, self.lemma, self.index))

    def __eq__(self, other):
        return self.id_ == other.id_ and self.lemma == other.lemma and self.index == other.index


class RootLexicon:
    RESOURCES_DIR = Path(__file__).parent / 'resources'
    DEFAULT_DICTIONARY_RESOURCES = [
        # "tr/test.dict"
        "tr/master-dictionary.dict",
        "tr/non-tdk.dict",
        "tr/proper.dict",
        "tr/proper-from-corpus.dict",
        "tr/abbreviations.dict",
        "tr/person-names.dict"
    ]

    def __init__(self):
        self.item_set = set()
        self.id_dict = {}
        self.item_dict = {}

    @classmethod
    def default_text_dictionaries(cls):
        lexicon = cls()
        lines = []
        for resource in cls.DEFAULT_DICTIONARY_RESOURCES:
            dict_path = cls.RESOURCES_DIR / resource
            new_lines = Path(cls.RESOURCES_DIR / resource).read_text(encoding='utf8').split('\n')
            lines.extend(new_lines)
        processor = TextLexiconProcessor(lexicon)
        processor.process_lines(lines)
        return lexicon

    @classmethod
    def from_lines(cls, lines: List):
        lexicon = cls()
        processor = TextLexiconProcessor(lexicon)
        processor.process_lines(lines)
        return lexicon

    def add(self, item):

        if item.id_ in self.id_dict:
            print(f"Duplicated item id_ of {item}: {item.id_} with {self.id_dict.get(item.id_)}")
            return
        self.item_set.add(item)
        self.id_dict[item.id_] = item
        if item.lemma in self.item_dict:
            self.item_dict[item.lemma].append(item)
        else:
            self.item_dict[item.lemma] = [item]

    def get_matching_items(self, lemma):
        items = self.item_dict.get(lemma)
        return [] if items is None else items

    def get_item_by_id(self, id_):
        return self.id_dict.get(id_, None)

    def remove(self, item):
        self.item_dict.get(item.lemma)  # TODO: test if works
        self.id_dict.pop(item.id_)
        self.item_set.remove(item)

    def __len__(self):
        return len(self.item_dict)

    @property
    def items(self):
        return list(self.item_set)

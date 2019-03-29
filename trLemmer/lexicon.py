from collections import namedtuple
from enum import Enum
from pathlib import Path
from typing import List, Set

from trLemmer.attributes import RootAttribute, PrimaryPos, SecondaryPos, primary_pos_set, \
    secondary_pos_set, morphemic_attributes
from trLemmer import tr


class PronunciationGuesser:
    def __init__(self):
        pass


class MetaDataId(Enum):
    POS = "P"
    ATTRIBUTES = "A"
    REF_ID = "Ref"
    ROOTS = "Roots"
    PRONUNCIATION = "Pr"
    SUFFIX = "S"
    INDEX = "Index"


PosInfo = namedtuple("PosInfo", "primary_pos secondary_pos")


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
            self.process_line(line)

    def process_line(self, line):
        line = line.strip()
        if len(line) == 0 or line.startswith("##"):
            return

        line_data = parse_line_data(line)
        # if a line contains references to other lines, we add them to lexicon later.
        try:
            if MetaDataId.REF_ID not in line_data['metadata'] and MetaDataId.ROOTS not in line_data['metadata']:
                dict_item = self.parse_dict_item(line_data)
                if dict_item is not None:
                    self.lexicon.add(dict_item)
                else:
                    print(f"Dict item is none: {line_data}")
            else:
                self.late_entries.append(line_data)
        except Exception as e:
            print(f"Exception {e} raised while adding dict item from {line_data}")

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
            #  DASH_QUOTE_MATCHER.matcher(word).replaceAll("")
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
                        primary_pos = PrimaryPos(token)  # TODO: Test this works
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
                secondary_pos = TextLexiconProcessor.infer_primary_pos(word)

            return PosInfo(primary_pos, secondary_pos)

    def parse_dict_item(self, line_data):
        word = line_data['word']
        metadata = line_data['metadata']
        pos_info = self.get_pos_data(metadata.get(MetaDataId.POS), word)
        clean_word = self.generate_root(word, pos_info)
        index_str = metadata.get(MetaDataId.INDEX)
        index = 0
        if index_str is not None:
            index = int(index_str)
        pronunciation = metadata.get(MetaDataId.PRONUNCIATION)
        pronunciation_guessed = False
        secondary_pos = pos_info.secondary_pos
        if pronunciation is None:
            pronunciation_guessed = True
            if pos_info.primary_pos == PrimaryPos.Punctuation:
                # TODO: what to do with pronunciations of punctuations? For now we give them a generic one.
                pronunciation = "a"
            elif secondary_pos == SecondaryPos.Abbreviation:
                pronunciation = PronunciationGuesser.guessForAbbreviation(clean_word)
            elif tr.contains_vowel(clean_word):
                pronunciation = clean_word
            else:
                pronunciation = PronunciationGuesser.toTurkishLetterPronunciations(clean_word)
        else:
            pronunciation = tr.lower(pronunciation)

        attributes = morphemic_attributes(metadata.get(MetaDataId.ATTRIBUTES),
                                                               pronunciation,
                                                               pos_info)
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

            return DictionaryItem(word, clean_word, pos_info.primary_pos, secondary_pos, attributes, pronunciation,
                                  index)
        except Exception as e:
            print(f"Couldn't create {word}/{index}/ {type(index)} dictionary item, error: {e} ")

    def get_result(self):
        for entry in self.late_entries:
            if MetaDataId.REF_ID in entry.metadata:
                reference_id = entry.metadata.get(MetaDataId.REF_ID)
                if '_' not in reference_id:
                    reference_id += "_Noun"

                ref_item = self.lexicon.id_dict.get(reference_id)
                if ref_item is None:
                    print("Cannot find reference item id " + reference_id)
                item = self.parse_dict_item(entry)
                item.reference_item = ref_item
                self.lexicon.add(item)
            # this is a compound lemma with P3sg in it. Such as atkuyruğu
            if MetaDataId.ROOTS in entry.metadata:
                pos_info = self.get_pos_data(entry.getMetaData(MetaDataId.POS), entry.word)
                generated_id = f"{self.lexicon.id_dict.get(entry.word)}_{pos_info.primary_pos.value}"
                # TODO: Test _value_ works here for short_form
                item = self.lexicon.id_dict.get(generated_id)
                if item is None:
                    item = self.parse_dict_item(entry)
                    self.lexicon.add(item)
                r = entry.metadata.get(MetaDataId.ROOTS)  # at-kuyruk
                root = r.replace("-", "")  # atkuyruk
                if "-" in r:
                    r = r[:r.index('-')]
                ref_items = self.lexicon.get_matching_items(r)  # check lexicon for [kuyruk]
                if len(ref_items) > 0:
                    ref_item = sorted(ref_items, key=lambda item: item['index'])[0]
                    attr_set = ref_item.attrs
                else:
                    attr_set = morphemic_attributes(None, root, pos_info)

                attr_set.add(RootAttribute.CompoundP3sgRoot)
                if RootAttribute.Ext in item.attributes:
                    attr_set.add(RootAttribute.Ext)
                index = 0
                if self.lexicon.id_dict.get(f"{root}_{item.primary_pos.value}") is not None:
                    # TODO: Test _value_ works here for short_form
                    # generate a fake lemma for atkuyruk, use kuyruk's attributes.
                    # But do not allow voicing.
                    fake_root = DictionaryItem(root, root, item.primary_pos, item.secondary_pos, attr_set, index)
                    fake_root.attributes.add(RootAttribute.Dummy)
                    if RootAttribute.Voicing in fake_root.attributes:
                        fake_root.attributes.remove(RootAttribute.Voicing)
                    fake_root.reference_item = item
                    self.lexicon.add(fake_root)
        return self.lexicon


def generate_dict_id(lemma: str, primary_pos: PrimaryPos, secondary_pos: SecondaryPos, index):
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

    def __init__(self, lemma: str, root: str, primary_pos: PrimaryPos, secondary_pos: SecondaryPos, attrs: Set,
                 pronunciation: str, index: int):
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

    def __str__(self):
        result = f"{self.lemma} [P:{self.primary_pos.value}]"
        return result

    def has_any_attribute(self, root_attrs):
        return bool(root_attrs & self.attributes)

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
        "tr/master-dictionary.dict"  # ,
        # "tr/non-tdk.dict",
        # "tr/proper.dict",
        # "tr/proper-from-corpus.dict",
        # "tr/abbreviations.dict",
        # "tr/person-names.dict"
    ]

    def __init__(self):
        self.item_set = set()
        self.id_dict = {}
        self.item_dict = {}

    @classmethod
    def default_text_dictionaries(cls):
        lexicon = cls()
        lines = []
        print(f"CWD: {Path.cwd()}; resources dir: {cls.RESOURCES_DIR}")
        # TODO: get lines from TurkishDictionaryLoader.DEFAULT_DICTIONARY_RESOURCES
        for resource in cls.DEFAULT_DICTIONARY_RESOURCES:
            dict_path = cls.RESOURCES_DIR / resource
            print(f"Dict path: {dict_path}")
            new_lines = Path(cls.RESOURCES_DIR / resource).read_text(encoding='utf8').split('\n')
            print(new_lines)
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
        if item in self.item_set:
            print(f"Duplicated item: {item}")
            return
        if item.id_ in self.id_dict:
            print(f"Duplicated item id_ of {item} with {self.id_dict.get(item.id_)}")
        self.item_set.add(item)
        self.id_dict[item.id_] = item
        self.item_dict[item.lemma] = item

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

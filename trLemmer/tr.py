vowels_lower = "aeıioöuüâîû"
vowels_upper = "AEIİOÖUÜÂÎÛ"
all_lower = "abcçdefgğhıijklmnoöprsştuüvyzxwqâîû"
all_upper = "ABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZXWQÂÎÛ"
consonants_lower = "bcçdfgğhjklmnprsştvyzxwq"
consonants_upper = "BCÇDFGĞHJKLMNPRSŞTVYZXWQ"
voiceless_consonants = "çfhkpsşt"
all_lower_set = {'û', 'r', 'h', 'z', 's', 'i', 'ü', 'd', 'ı', 'ç', 'ö', 'ğ',
                 'î', 'g', 'w', 'k', 'b', 'c', 'f', 'y', 'p', 'u', 'ş', 'l', 'n', 'e', 'o',
                 'a', 'j', 'm', 'x', 't', 'q', 'â', 'v'}
vowels_lower_set = {'î', 'û', 'e', 'o', 'ı', 'a', 'i', 'ü', 'â', 'ö', 'u'}
vowels_upper_set = {'İ', 'Ö', 'I', 'Ü', 'Û', 'Â', 'Î', 'E', 'A', 'O', 'U'}
consonants_lower_set = {'r', 'h', 'z', 's', 'd', 'ç', 'ğ', 'g', 'w', 'k',
                        'b', 'c', 'f', 'y', 'p', 'ş', 'l', 'n', 'j', 'm', 'x', 't', 'q', 'v'}
consonants_upper_set = {'H', 'B', 'T', 'V', 'X', 'N', 'W', 'F', 'S', 'Ş',
                        'L', 'R', 'Q', 'K', 'C', 'M', 'J', 'Ğ', 'D', 'Y', 'Ç', 'Z', 'P', 'G'}
consonants_voiceless_set = {'ş', 'k', 'h', 'ç', 's', 't', 'f', 'p'}
consonants_voiceless_stop_set = {'ç', 'k', 'p', 't'}
consonants_voiced_stop_set = {'c', 'g', 'b', 'd'}

vowels_back_set = {'a', 'ı', 'o', 'u'}  # TODO: sapkalilar?
vowels_rounded_set = {'o', 'u', 'ö', 'ü', 'û'}

lower_to_upper = dict(zip(all_lower, all_upper))
upper_to_lower = dict(zip(all_upper, all_lower))

voicing = {'ş': 'j', 'k': 'g', 'ç': 'c', 's': 'z', 't': 'd', 'f': 'v', 'p': 'b', 'g': 'ğ'}
devoicing = {'j': 'ş', 'g': 'k', 'c': 'ç', 'z': 's', 'd': 't', 'v': 'f', 'b': 'p', 'ğ': 'g'}


def voice(letter):
    return voicing.get(letter, letter)


def devoice(letter):
    return devoicing.get(letter, letter)


def lower(word) -> str:
    return ''.join([upper_to_lower.get(letter, letter) for letter in word])


def upper(word) -> str:
    return ''.join([lower_to_upper.get(letter, letter) for letter in word])


def is_upper(symbol) -> bool:
    if len(symbol) > 1:
        raise ValueError(f"Is upper argument can only be one symbol, not {symbol}")
    return symbol in all_upper  # TODO: create set


def is_lower(symbol) -> bool:
    if len(symbol) > 1:
        raise ValueError(f"Is lower argument can only be one symbol, not {symbol}")
    return symbol in all_lower_set


def get_last_vowel(word):
    for letter in reversed(word):
        if letter in vowels_lower_set:
            return letter
    return None


def contains_vowel(word):
    for letter in word:
        if letter in vowels_lower_set:
            return True
    return False


def vowel_count(word):
    return sum(1 for _ in word if _ in vowels_lower_set or _ in vowels_upper_set)


def is_vowel(symbol):
    return symbol in vowels_lower_set or symbol in vowels_upper_set


def is_voiceless_stop_consonant(symbol):
    symbol = lower(symbol)
    return symbol in consonants_voiceless_stop_set


circumflex = "âîûÂÎÛ"
noncircumflex = "aiuAIU"
decircumflex = dict(zip(circumflex, noncircumflex))


def normalize_circumflex(word):
    result = ''.join([decircumflex.get(c, c) for c in word])
    return result

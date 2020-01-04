from trLemmer import MorphAnalyzer

POS_TAGS = {"Noun", "Verb", "Adj", "Adv", "Conj", "Interj", "Pron", "Num", "Det", "Postp", "Ques", "Dup", "Punc", "Unk"}

analyzer = MorphAnalyzer()
analysis = analyzer.analyze_sentence("Yarın doktora gideceğimizi öğrendi.")
print(analysis)
for word in analysis:
    for parse in word:
        print(parse)
        print(f"\tFirst morpheme: {parse.morphemes[0]}, last morpheme: {parse.morphemes[-1]}")
        print(f"\tIs in Dative case: {'Dat' in parse.morphemes}")
        print(f"\tHas more than one POS tag: {len(POS_TAGS.intersection(set(parse.morphemes))) > 1}")
        # TODO: check that this is really UD
        print(f"\tFormatted in Universal Depepndency format: {parse.formatted_form}")

lemmatization = analyzer.lemmatize_sentence("Yarın doktora gideceğimizi öğrendi.")
for (word, lemmas) in lemmatization:
    print(f"{word}: {lemmas}")

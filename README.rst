==================
Turkish Lemmatizer
==================


.. image:: https://img.shields.io/pypi/v/trLemmer.svg
        :target: https://pypi.python.org/pypi/trLemmer

.. image:: https://dev.azure.com/obulat0592/trlemmer/_apis/build/status/obulat.trLemmer?branchName=master
        :target: https://dev.azure.com/obulat0592/trlemmer/

.. image:: https://readthedocs.org/projects/trLemmer/badge/?version=latest
        :target: https://trLemmer.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status


trLemmer is a partial port of Zemberek library to Python for lemmatizing
Turkish language words. It is not ready for use yet.


* Free software: MIT license
* Documentation: https://trLemmer.readthedocs.io.


Basic Usage
~~~~~~~~~~~

.. code-block:: pycon

    >>> from trLemmer import MorphAnalyzer
    >>> lemmatizer = MorphAnalyzer()
    >>> lemmas = lemmatizer.lemmatize('beyazlaştıracak')
    >>> print(lemmas[0])
    beyaz

    >>> lemmatization = lemmatizer.lemmatize_text("Yarın doktora gideceğimizi öğrendi.")
    >>> for (sentence, lemmas) in lemmatization:
    >>>     print(sentence)
    >>>     for (word, lemma) in lemmas:
    >>>>        print(f"{word}: {lemma}")
    Yarın doktora gideceğimizi öğrendi.
    Yarın: ['yarmak', 'yarın', 'yar', 'yarı']
    doktora: ['doktora', 'doktor']
    gideceğimizi: ['gitmek']
    öğrendi: ['öğrenmek']
    .: ['.']


    >>> word_analysis = lemmatizer.analyze('beyazlaştıracak')
    >>> for variant in word_analysis:
    >>>     print(variant)
    Parse(word='beyazlaştıracak', lemma='beyaz', morphemes=['Adj', 'Become', 'Verb', 'Caus', 'Verb', 'FutPart', 'Adj'], formatted='[beyaz:Adj] beyaz:Adj | laş:Become→Verb | tır:Caus→Verb | acak:FutPart→Adj')
    Parse(word='beyazlaştıracak', lemma='beyaz', morphemes=['Noun', 'A3sg', 'Become', 'Verb', 'Caus', 'Verb', 'FutPart', 'Adj'], formatted='[beyaz:Noun] beyaz:Noun + A3sg | laş:Become→Verb | tır:Caus→Verb | acak:FutPart→Adj')


    >>> analysis = lemmatizer.analyze_text("Yarın doktora gideceğimizi öğrendi.")
    >>> for sentence, result in analysis:
    >>>     for word_parse in result:
    >>>         print(f"\n{word_parse[0].word}")
    >>>         for parse in word_parse:
    >>>             print(parse.formatted)
    Yarın
    [yarın:Adv] yarın:Adv
    [yarmak:Verb] yar:Verb + Imp + ın:A2pl
    [yar:Noun] yar:Noun + A3sg + ın:Gen
    [yar:Noun] yar:Noun + A3sg + ın:P2sg
    [yarı:Noun] yarı:Noun + A3sg + n:P2sg
    [yarın:Noun,Time] yarın:Noun + A3sg
    [yarı:Adj] yarı:Adj | Zero→Noun + A3sg + n:P2sg

    doktora
    [doktor:Noun] doktor:Noun + A3sg + a:Dat
    [doktora:Noun] doktora:Noun + A3sg

    gideceğimizi
    [gitmek:Verb] gid:Verb | eceğ:FutPart→Noun + A3sg + imiz:P1pl + i:Acc

    öğrendi
    [öğrenmek:Verb] öğren:Verb + di:Past + A3sg

    .
    [.:Punc] .:Punc

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

This package is a Python port of part of the Zemberek_ package by `Ahmet A. Akın`_

.. _Zemberek: https://github.com/ahmetaa/zemberek-nlp
.. _Ahmet A. Akın: https://github.com/ahmetaa/

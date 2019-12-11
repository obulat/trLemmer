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


.. image:: https://pyup.io/repos/github/obulat/trLemmer/shield.svg
     :target: https://pyup.io/repos/github/obulat/trLemmer/
     :alt: Updates



trLemmer is a partial port of Zemberek library to Python for lemmatizing
Turkish language words. It is not ready for use yet.


* Free software: MIT license
* Documentation: https://trLemmer.readthedocs.io.


Basic Usage
~~~~~~~~~~~

.. code-block:: pycon

    >>> from trLemmer import TrLemmer
    >>> lemmatizer = TrLemmer()
    >>> lemma = lemmatizer.lemmatize('beyazlaştıracak')
    >>> print(lemma)
    beyaz





Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

This package is a Python port of part of the Zemberek_ package by `Ahmet A. Akın`_

.. _Zemberek: https://github.com/ahmetaa/zemberek-nlp
.. _Ahmet A. Akın: https://github.com/ahmetaa/

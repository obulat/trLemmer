#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `trLemmer.conditions` module."""
import pytest
from trLemmer.attributes import RootAttribute, PhoneticAttribute, PrimaryPos, SecondaryPos
from trLemmer.conditions import CombinedCondition, has, HasAnyRootAttribute, HasRootAttribute, DictionaryItemIs, not_have_any
from trLemmer.lexicon import DictionaryItem, RootLexicon
from trLemmer.morphotactics import SearchPath, StemTransition, noun_S

lex = RootLexicon.from_lines(["adak", "elma", "beyaz [P:Adj]", "meyve"])


@pytest.fixture(autouse=True)
def simple_condition():
    return has(PhoneticAttribute.CannotTerminate)


@pytest.mark.parametrize("text_input, expected", [
    # (simple_condition, 1),
    (has(PhoneticAttribute.CannotTerminate), 1),
    (CombinedCondition('AND', [simple_condition, simple_condition]), 2),
    (CombinedCondition('OR', [simple_condition, simple_condition]), 2),
    (CombinedCondition('AND', [CombinedCondition('AND', [simple_condition, simple_condition]), simple_condition]), 3)
])
def test_condition_len(text_input, expected):
    condition = text_input
    print(f"Condition: {condition}/ {type(condition)}")
    assert len(condition) == expected


@pytest.mark.parametrize("test_input, expected_op_len", [
    ([has(PhoneticAttribute.CannotTerminate), has(RootAttribute.CompoundP3sgRoot)], ['AND', 2]),

    ([has(PhoneticAttribute.CannotTerminate),
      CombinedCondition('AND', [has(RootAttribute.CompoundP3sgRoot), has(PhoneticAttribute.CannotTerminate)])],
     ['AND', 3]),

    ([CombinedCondition('AND', [has(RootAttribute.CompoundP3sgRoot), has(PhoneticAttribute.CannotTerminate)]),
      has(PhoneticAttribute.CannotTerminate)], ['AND', 3]),

    ([has(PhoneticAttribute.CannotTerminate),
      CombinedCondition('OR', [has(RootAttribute.CompoundP3sgRoot), has(PhoneticAttribute.CannotTerminate)])],
     ['AND', 3]),

    ([CombinedCondition('OR', [has(RootAttribute.CompoundP3sgRoot), has(PhoneticAttribute.CannotTerminate)]),
      has(PhoneticAttribute.CannotTerminate)], ['AND', 3])

])
def test_and_condition(test_input, expected_op_len):
    cond1, cond2 = test_input
    operator, length = expected_op_len
    and_cond = cond1.and_(cond2)
    assert len(and_cond) == length
    assert and_cond.operator == operator


@pytest.mark.parametrize("test_input, expected_op_len", [
    ([has(PhoneticAttribute.CannotTerminate), has(RootAttribute.CompoundP3sgRoot)], ['OR', 2]),

    ([has(PhoneticAttribute.CannotTerminate),
      CombinedCondition('AND', [has(RootAttribute.CompoundP3sgRoot), has(PhoneticAttribute.CannotTerminate)])],
     ['OR', 3]),

    ([CombinedCondition('AND', [has(RootAttribute.CompoundP3sgRoot), has(PhoneticAttribute.CannotTerminate)]),
      has(PhoneticAttribute.CannotTerminate)], ['OR', 3]),

    ([has(PhoneticAttribute.CannotTerminate),
      CombinedCondition('OR', [has(RootAttribute.CompoundP3sgRoot), has(PhoneticAttribute.CannotTerminate)])],
     ['OR', 3]),

    ([CombinedCondition('OR', [has(RootAttribute.CompoundP3sgRoot), has(PhoneticAttribute.CannotTerminate)]),
      has(PhoneticAttribute.CannotTerminate)], ['OR', 3])

])
def test_or_condition(test_input, expected_op_len):
    cond1, cond2 = test_input
    operator, length = expected_op_len
    and_cond = cond1.or_(cond2)
    assert len(and_cond) == length
    assert and_cond.operator == operator


def test_dict_item_conditions():
    existing_attr = RootAttribute.CompoundP3sgRoot

    dict_item = DictionaryItem(lemma='word', root='word', primary_pos=PrimaryPos.Noun, secondary_pos=SecondaryPos.NONE,
                               attrs={existing_attr}, pronunciation='word', index=0)
    stem_transition = StemTransition(dict_item.lemma, dict_item, {existing_attr}, noun_S)
    path = SearchPath.initial(stem_transition, 'tail')
    condition = not_have_any(existing_attr)
    assert condition.accept(path)
    assert HasRootAttribute(existing_attr).accept(path)
    nonexisting_attr = RootAttribute.ProgressiveVowelDrop
    condition = not_have_any(nonexisting_attr)
    assert not condition.accept(path)
    assert not HasRootAttribute(nonexisting_attr).accept(path)
    condition = DictionaryItemIs(dict_item)
    assert condition.accept(path)

    another_dict_item = DictionaryItem(lemma='word1', root='word', primary_pos=PrimaryPos.Noun,
                                       secondary_pos=SecondaryPos.NONE, attrs=[RootAttribute.CompoundP3sgRoot],
                                       pronunciation='word', index=0)
    another_condition = root_is(another_dict_item)
    assert not another_condition.accept(path)

# def test_no_surface_after_derivation():
#     dict_item =
    # path = [<(beyaz_Adj_Noun)(-)beyaz:adjectiveRoot_ST + laş:become_S + verbRoot_S + tı:vPast_S + vA3sg_ST>]

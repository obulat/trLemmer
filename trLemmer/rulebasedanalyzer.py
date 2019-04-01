from trLemmer.attributes import PhoneticAttribute, calculate_phonetic_attributes
from trLemmer.morphotactics import SurfaceTransition, SearchPath, generate_surface
import logging

logging.basicConfig(level=logging.WARNING)


class RuleBasedAnalyzer:
    """
    This is a Morphological Analyzer implementation. Instances of this class are not thread safe if
    instantiated with forDebug() factory constructor method.
    """

    def __init__(self, morphotactics):
        self.morphotactics = morphotactics
        self.stem_transitions = morphotactics.stem_transitions
        self.lexicon = self.morphotactics.lexicon

    def analyze(self, word):
        # get stem candidates.
        candidates = self.stem_transitions.prefix_matches(word)

        # generate initial search paths.
        paths = []
        for candidate in candidates:
            length = len(candidate.surface)
            tail = word[length:]
            paths.append(SearchPath.initial(candidate, tail))
        # search graph.
        result_paths = self.search(paths)

        # generate results from successful paths.
        result = []
        for path in result_paths:
            analysis = SingleAnalysis.from_searchpath(path)
            result.append(analysis)
        return result

    def search(self, current_paths):
        # searches through morphotactics graph.
        if len(current_paths) > 30:
            current_paths = self.prune_cyclic_paths(current_paths)
        result = []
        # new Paths are generated with matching transitions.
        while len(current_paths) > 0:
            all_new_paths = []
            for path in current_paths:
                # if there are no more letters to consume and path can be terminated, we accept this
                # path as a correct result.
                if len(path.tail) == 0:
                    if path.is_terminal and PhoneticAttribute.CannotTerminate not in path.phonetic_attributes:
                        logging.warning(f"APPENDING RESULT: {path}")
                        result.append(path)
                        continue
                # Creates new paths with outgoing and matching transitions.
                new_paths = self.advance(path)
                logging.debug(f"\n--\nNew paths are: ")
                for p in new_paths:
                    logging.debug(f"-- {p}")
                logging.debug('')
                all_new_paths.extend(new_paths)
            current_paths = all_new_paths
        return result

    def advance(self, path: SearchPath):
        """
        for all allowed matching outgoing transitions, new paths are generated.
        Transition `conditions` are used for checking if a `search path`
        is allowed to pass a transition.
        :param path:
        :return:
        """
        new_paths = []
        # for all outgoing transitions.
        # print(f"\n\n ADVANCE {path} for {len(path.current_state.outgoing)} transitions")
        for transition in path.current_state.outgoing:
            # if tail is empty and this transitions surface is not empty, no need to check.
            if len(path.tail) == 0 and transition.has_surface_form:
                logging.debug(f"Rejecting path {path}: Path and transition surface mismatch: ")
                continue

            surface = generate_surface(
                transition,
                path.phonetic_attributes)

            # no need to go further if generated surface form is not a prefix of the paths's tail.
            tail_starts_with = path.tail.startswith(surface)
            if not tail_starts_with:
                logging.debug(f"Rejecting path {path}: tail doesnt start with {path.tail}-{surface}")
                continue

            # check conditions.
            if not transition.can_pass(path):
                logging.debug(f"Rejecting path {path}-{transition}: can't pass")
                continue

            # epsilon (empty) transition. Add and continue. Use existing attributes.
            if not transition.has_surface_form:
                blank_surface_transition = SurfaceTransition("", transition)
                new_path = path.copy(blank_surface_transition, path.phonetic_attributes)
                new_paths.append(new_path)
                logging.debug(f"Appending path {new_path}")
                continue

            surface_transition = SurfaceTransition(surface, transition)

            # if tail is equal to surface, no need to calculate phonetic attributes.
            tail_equals_surface = path.tail == surface
            attributes = path.phonetic_attributes if tail_equals_surface \
                else calculate_phonetic_attributes(surface, path.phonetic_attributes)

            # This is required for suffixes like `cik` and `ciğ`
            # an extra attribute is added if "cik" or "ciğ" is generated and matches the tail.
            # if "cik" is generated, ExpectsConsonant attribute is added, so only a consonant starting
            # suffix can follow. Likewise, if "ciğ" is produced, a vowel starting suffix is allowed.
            if PhoneticAttribute.CannotTerminate in attributes:
                attributes.discard(PhoneticAttribute.CannotTerminate)
            last_token = transition.last_template_token
            if last_token.type_ == 'LAST_VOICED':
                attributes.add(PhoneticAttribute.ExpectsConsonant)
            elif last_token.type_ == 'LAST_NOT_VOICED':
                attributes.add(PhoneticAttribute.ExpectsVowel)
                attributes.add(PhoneticAttribute.CannotTerminate)
            p = path.copy(surface_transition, attributes)
            logging.debug(f"P path: {p}")
            new_paths.append(p)
        logging.debug(f"FINAL: ")
        for i, p in enumerate(new_paths):
            logging.debug(f"\t {i}: {p}")
        # print()
        return new_paths

    # for preventing excessive branching during search, we remove paths that has more than
    # MAX_REPEATING_SUFFIX_TYPE_COUNT morpheme-state types.
    def prune_cyclic_paths(self, tokens):
        result = []
        for token in tokens:
            remove = False
            type_counts = {}
            for node in token.transitions:
                if type_counts.addOrIncrement(node.getState().id) > MAX_REPEATING_SUFFIX_TYPE_COUNT:
                    remove = True
                    break
                if not remove:
                    result.append(token)
        return result


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

    def __init__(self, dict_item, morpheme_data_list, group_boundaries):
        self.dict_item = dict_item
        self.morpheme_data_list = morpheme_data_list
        self.group_boundaries = group_boundaries

    @classmethod
    def from_searchpath(cls, path):
        return path


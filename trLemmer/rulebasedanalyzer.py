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
            current_paths = self.pruneCyclicPaths(current_paths)
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
                for path in new_paths:
                    logging.debug(f"-- {path}")
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
            tailStartsWith = path.tail.startswith(surface)
            if not tailStartsWith:
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

            surfaceTransition = SurfaceTransition(surface, transition)

            # if tail is equal to surface, no need to calculate phonetic attributes.
            tailEqualsSurface = path.tail == surface
            attributes = path.phonetic_attributes if tailEqualsSurface \
                else calculate_phonetic_attributes(surface, path.phonetic_attributes)

            # This is required for suffixes like `cik` and `ciğ`
            # an extra attribute is added if "cik" or "ciğ" is generated and matches the tail.
            # if "cik" is generated, ExpectsConsonant attribute is added, so only a consonant starting
            # suffix can follow. Likewise, if "ciğ" is produced, a vowel starting suffix is allowed.
            if PhoneticAttribute.CannotTerminate in attributes:
                attributes.remove(PhoneticAttribute.CannotTerminate)
            lastToken = transition.last_template_token
            if lastToken.type_ == 'LAST_VOICED':
                attributes.append(PhoneticAttribute.ExpectsConsonant)
            elif lastToken.type_ == 'LAST_NOT_VOICED':
                attributes.append(PhoneticAttribute.ExpectsVowel)
                attributes.append(PhoneticAttribute.CannotTerminate)
            p = path.copy(surfaceTransition, attributes)
            logging.debug(f"P path: {p}")
            new_paths.append(p)
        logging.debug(f"FINAL: ")
        for i, p in enumerate(new_paths):
            logging.debug(f"\t {i}: {p}")
        # print()
        return new_paths

    # for preventing excessive branching during search, we remove paths that has more than
    # MAX_REPEATING_SUFFIX_TYPE_COUNT morpheme-state types.
    def pruneCyclicPaths(self, tokens):

        result = []
        for token in tokens:
            remove = False
        typeCounts = {}
        for node in token.transitions:
            if typeCounts.addOrIncrement(node.getState().id) > MAX_REPEATING_SUFFIX_TYPE_COUNT:
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
        """
# Here we generate a SingleAnalysis from a search path.
  public static SingleAnalysis fromSearchPath(SearchPath searchPath) {

    List<MorphemeData> morphemes = new ArrayList<>(searchPath.transitions.size());

    int derivationCount = 0;

    for (SurfaceTransition transition : searchPath.getTransitions()) {

      if (transition.isDerivative()) {
        derivationCount++;
      }

      Morpheme morpheme = transition.getMorpheme();

    # we skip these two morphemes as they create visual noise and does not carry much information.
      if (morpheme == TurkishMorphotactics.nom || morpheme == TurkishMorphotactics.pnon) {
        continue;
      }

    # if empty, use the cache.
      if (transition.surface.isEmpty()) {
        MorphemeData morphemeData = emptyMorphemeCache.get(morpheme);
        if (morphemeData == null) {
          morphemeData = new MorphemeData(morpheme, "");
          emptyMorphemeCache.put(morpheme, morphemeData);
        }
        morphemes.add(morphemeData);
        continue;
      }

      MorphemeData suffixSurface = new MorphemeData(morpheme, transition.surface);
      morphemes.add(suffixSurface);
    }

    int[] groupBoundaries = new int[derivationCount + 1];
    groupBoundaries[0] = 0; // we assume there is always an IG

    int morphemeCounter = 0, derivationCounter = 1;
    for (MorphemeData morphemeData : morphemes) {
      if (morphemeData.morpheme.derivational) {
        groupBoundaries[derivationCounter] = morphemeCounter;
        derivationCounter++;
      }
      morphemeCounter++;
    }

  # if dictionary item is `Dummy`, use the referenced item.
  # `Dummy` items are usually generated for some compound words. For example for `zeytinyağı`
  # a DictionaryItem is generated with root "zeytinyağ". But here we switch to the original.
    DictionaryItem item = searchPath.getDictionaryItem();
    if (item.hasAttribute(RootAttribute.Dummy)) {
      item = item.getReferenceItem();
    }
    return new SingleAnalysis(item, morphemes, groupBoundaries);
  }

  public static SingleAnalysis unknown(String input) {
    DictionaryItem item = DictionaryItem.UNKNOWN;
    MorphemeData s = new MorphemeData(Morpheme.UNKNOWN, input);
    int[] boundaries = {0};
    return new SingleAnalysis(item, Collections.singletonList(s), boundaries);
  }

  public static SingleAnalysis dummy(String input, DictionaryItem item) {
    MorphemeData s = new MorphemeData(Morpheme.UNKNOWN, input);
    int[] boundaries = {0};
    return new SingleAnalysis(item, Collections.singletonList(s), boundaries);
  }

  public String surfaceForm() {
    return getStem() + getEnding();
  }

  public static class MorphemeGroup {

    List<MorphemeData> morphemes;

    public MorphemeGroup(List<MorphemeData> morphemes) {
      this.morphemes = morphemes;
    }

    public List<MorphemeData> getMorphemes() {
      return morphemes;
    }

    public PrimaryPos getPos() {
      for (MorphemeData mSurface : morphemes) {
        if (mSurface.morpheme.pos != null && mSurface.morpheme.pos != PrimaryPos.Unknown) {
          return mSurface.morpheme.pos;
        }
      }
      return PrimaryPos.Unknown;
    }

    public String surfaceForm() {
      StringBuilder sb = new StringBuilder();
      for (MorphemeData mSurface : morphemes) {
        sb.append(mSurface.surface);
      }
      return sb.toString();
    }

    public String surfaceFormSkipPosRoot() {
      StringBuilder sb = new StringBuilder();
      for (MorphemeData mSurface : morphemes) {
        if (mSurface.morpheme.pos != null) {
          continue;
        }
        sb.append(mSurface.surface);
      }
      return sb.toString();
    }

    public String lexicalForm() {
      StringBuilder sb = new StringBuilder();
      for (MorphemeData mSurface : morphemes) {
        sb.append(mSurface.morpheme.id);
      }
      return sb.toString();
    }

  }

  public boolean containsInformalMorpheme() {
    return getMorphemes().stream().anyMatch(m -> m.informal);
  }

  int getMorphemeGroupCount() {
    return groupBoundaries.length;
  }

  /**
   * Returns the concatenated suffix surfaces.
   * <pre>
   *   "elmalar"      -> "lar"
   *   "elmalara"     -> "lara"
   *   "okutturdular" -> "tturdular"
   *   "arıyor"       -> "ıyor"
   * </pre>
   *
   * @return concatenated suffix surfaces.
   */
  public String getEnding() {
    StringBuilder sb = new StringBuilder();
  # skip the root.
    for (int i = 1; i < morphemeDataList.size(); i++) {
      MorphemeData mSurface = morphemeDataList.get(i);
      sb.append(mSurface.surface);
    }
    return sb.toString();
  }

  /**
   * Returns the stem of the word. Stem may be different than the lemma of the word.
   * <pre>
   *   "elmalar"      -> "elma"
   *   "kitabımız"    -> "kitab"
   *   "okutturdular" -> "oku"
   *   "arıyor"       -> "ar"
   * </pre>
   * TODO: decide for inputs like "12'ye and "Ankara'da"
   *
   * @return concatenated suffix surfaces.
   */
  public String getStem() {
    return morphemeDataList.get(0).surface;
  }

  public boolean containsMorpheme(Morpheme morpheme) {
    for (MorphemeData morphemeData : morphemeDataList) {
      if (morphemeData.morpheme == morpheme) {
        return true;
      }
    }
    return false;
  }

  /**
   * Splits the parse into stem and ending. Such as:
   * <pre>
   * "kitaplar" -> "kitap-lar"
   * "kitabımdaki" -> "kitab-ımdaki"
   * "kitap" -> "kitap-"
   * </pre>
   *
   * @return a StemAndEnding instance carrying stem and ending. If ending has no surface content
   * empty string is used.
   */
  public StemAndEnding getStemAndEnding() {
    return new StemAndEnding(getStem(), getEnding());
  }


  public DictionaryItem getDictionaryItem() {
    return item;
  }

  public boolean isUnknown() {
    return item.isUnknown();
  }

  public boolean isRuntime() {
    return item.hasAttribute(RootAttribute.Runtime);
  }


  public List<MorphemeData> getMorphemeDataList() {
    return morphemeDataList;
  }

  public List<Morpheme> getMorphemes() {
    return morphemeDataList.stream().map(s -> s.morpheme).collect(Collectors.toList());
  }

  public MorphemeGroup getGroup(int groupIndex) {
    if (groupIndex < 0 || groupIndex >= groupBoundaries.length) {
      throw new IllegalArgumentException("There are only " + groupBoundaries.length +
          " morpheme groups. But input is " + groupIndex);
    }
    int endIndex = groupIndex == groupBoundaries.length - 1 ?
        morphemeDataList.size() : groupBoundaries[groupIndex + 1];

    return new MorphemeGroup(morphemeDataList.subList(groupBoundaries[groupIndex], endIndex));
  }

# container for Morphemes and their surface forms.
  public static class MorphemeData {

    public final Morpheme morpheme;
    public final String surface;

    public MorphemeData(Morpheme morpheme, String surface) {
      this.morpheme = morpheme;
      this.surface = surface;
    }

    public String toString() {
      return toMorphemeString();
    }

    public String toMorphemeString() {
      return surfaceString() + morpheme.id;
    }

    private String surfaceString() {
      return surface.isEmpty() ? "" : surface + ":";
    }

    @Override
    public boolean equals(Object o) {
      if (this == o) {
        return true;
      }
      if (o == null || getClass() != o.getClass()) {
        return false;
      }

      MorphemeData that = (MorphemeData) o;

      if (!morpheme.equals(that.morpheme)) {
        return false;
      }
      return surface.equals(that.surface);
    }

    @Override
    public int hashCode() {
      int result = morpheme.hashCode();
      result = 31 * result + surface.hashCode();
      return result;
    }
  }

  public MorphemeGroup getLastGroup() {
    return getGroup(groupBoundaries.length - 1);
  }

  public MorphemeGroup[] getGroups() {
    MorphemeGroup[] groups = new MorphemeGroup[groupBoundaries.length];
    for (int i = 0; i < groups.length; i++) {
      groups[i] = getGroup(i);
    }
    return groups;
  }


  private static final ConcurrentHashMap<Morpheme, MorphemeData> emptyMorphemeCache =
      new ConcurrentHashMap<>();



  public boolean containsAnyMorpheme(Morpheme... morphemes) {
    for (Morpheme morpheme : morphemes) {
      if (containsMorpheme(morpheme)) {
        return true;
      }
    }
    return false;
  }

  /**
   * This method is used for modifying the dictionary item and stem of an analysis without changing
   * the suffix morphemes. This is used for generating result for inputs like "5'e"
   *
   * @param item new DictionaryItem
   * @param stem new stem
   * @return new SingleAnalysis object with given DictionaryItem and stem.
   */
  SingleAnalysis copyFor(DictionaryItem item, String stem) {
  # copy morpheme-surface list.
    List<MorphemeData> data = new ArrayList<>(morphemeDataList);
  # replace the stem surface. it is in the first morpheme.
    data.set(0, new MorphemeData(data.get(0).morpheme, stem));
    return new SingleAnalysis(item, data, groupBoundaries.clone());
  }

  /**
   * Returns surface forms list of all root and derivational roots of a parse. Examples:
   * <pre>
   * "kitaplar"  ->["kitap"]
   * "kitabım"   ->["kitab"]
   * "kitaplaşır"->["kitap", "kitaplaş"]
   * "kavrulduk" ->["kavr","kavrul"]
   * </pre>
   */
  public List<String> getStems() {
    List<String> stems = Lists.newArrayListWithCapacity(2);
    stems.add(getStem());
    String previousStem = getGroup(0).surfaceForm();
    if (groupBoundaries.length > 1) {
      for (int i = 1; i < groupBoundaries.length; i++) {
        MorphemeGroup ig = getGroup(i);
        MorphemeData suffixData = ig.morphemes.get(0);

        String surface = suffixData.surface;
        String stem = previousStem + surface;
        if (!stems.contains(stem)) {
          stems.add(stem);
        }
        previousStem = previousStem + ig.surfaceForm();
      }
    }
    return stems;
  }


  /**
   * Returns list of all lemmas of a parse. Examples:
   * <pre>
   * "kitaplar"  ->["kitap"]
   * "kitabım"   ->["kitap"]
   * "kitaplaşır"->["kitap", "kitaplaş"]
   * "kitaplaş"  ->["kitap", "kitaplaş"]
   * "arattıragörür" -> ["ara","arat","arattır","arattıragör"]
   * </pre>
   */
  public List<String> getLemmas() {
    List<String> lemmas = Lists.newArrayListWithCapacity(2);
    lemmas.add(item.root);

    String previousStem = getGroup(0).surfaceForm();
    if (!previousStem.equals(item.root)) {
      if (previousStem.endsWith("ğ")) {
        previousStem = previousStem.substring(0, previousStem.length() - 1) + "k";
      }
    }

    if (groupBoundaries.length > 1) {
      for (int i = 1; i < groupBoundaries.length; i++) {
        MorphemeGroup ig = getGroup(i);
        MorphemeData suffixData = ig.morphemes.get(0);

        String surface = suffixData.surface;
        String stem = previousStem + surface;
        if (stem.endsWith("ğ")) {
          stem = stem.substring(0, stem.length() - 1) + "k";
        }
        if (!lemmas.contains(stem)) {
          lemmas.add(stem);
        }
        previousStem = previousStem + ig.surfaceForm();
      }
    }
    return lemmas;
  }

  @Override
  public String toString() {
    return formatLong();
  }

  public String formatLexical() {
    return AnalysisFormatters.DEFAULT_LEXICAL.format(this);
  }

  /**
   * Formats only the morphemes. Dictionary item information is not included.
   *
   * @return formatted
   */
  public String formatMorphemesLexical() {
    return AnalysisFormatters.DEFAULT_LEXICAL_ONLY_MORPHEMES.format(this);
  }

  public PrimaryPos getPos() {
    return getGroup(groupCount() - 1).getPos();
  }

  public String formatLong() {
    return AnalysisFormatters.DEFAULT.format(this);
  }

  public int groupCount() {
    return groupBoundaries.length;
  }

  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }

    SingleAnalysis that = (SingleAnalysis) o;

    if (hash != that.hash) {
      return false;
    }
    if (!item.equals(that.item)) {
      return false;
    }
    return morphemeDataList.equals(that.morphemeDataList);
  }

  @Override
  public int hashCode() {
    if (hash != 0) {
      return hash;
    }
    int result = item.hashCode();
    result = 31 * result + morphemeDataList.hashCode();
    result = 31 * result + hash;
    return result;
  }
}
"""

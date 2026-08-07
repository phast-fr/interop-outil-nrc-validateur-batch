import pytest
import pandas as pd


######################
# Fixtures générales #
######################
@pytest.fixture
def null() -> pd.DataFrame:
    return pd.DataFrame(
        {"FSN": ["SNOMED CT Concept"], "term": ["Concept SNOMED CT"],
         "acceptabilityId": ["PREFERRED"]}
    )


@pytest.fixture
def null_pt() -> pd.Series:
    return pd.Series(["PREFERRED"], name="acceptabilityId")


@pytest.fixture
def null_syn() -> pd.Series:
    return pd.Series(["ACCEPTABLE"], name="acceptabilityId")


@pytest.fixture
def semtag() -> pd.Series:
    def generate_series(n: int):
        return pd.Series([True] * n)
    return generate_series


###################################
# Fixtures pour règles génériques #
###################################
@pytest.fixture
def case() -> pd.DataFrame:
    return pd.DataFrame(
        {"term": ["Escherichia coli", "présence d'IgM", "pH mesuré", "kg"],
         "caseSignificanceId": ["CS"] * 4}
    )


@pytest.fixture
def case_output() -> pd.DataFrame:
    return pd.DataFrame({"caseSignificanceId": ["cI"]}, index=[1])


class FakeSpellDict:
    """Dictionnaire orthographique factice pour tester `_check_spellcheck`
    indépendamment du dictionnaire enchant/hunspell réellement installé."""

    def __init__(self, known_words):
        self.known_words = known_words

    def check(self, word: str) -> bool:
        return word.lower() in self.known_words


@pytest.fixture
def fake_spell_dict() -> FakeSpellDict:
    return FakeSpellDict({
        "structure", "de", "articulation", "du", "genou", "bonjour", "le",
        "monde",
    })


@pytest.fixture
def spell() -> pd.DataFrame:
    return pd.DataFrame(
        {"term": ["structure de l'articulation du genou",
                  "structure de l'articulasion du genou",
                  "bonjour le monde",
                  "xyzzyfoobar inconnu"]}
    )


@pytest.fixture
def spell_output(spell) -> pd.DataFrame:
    spellcheck = pd.Series(
        [float("nan"), "1", float("nan"), "1"], name="spellcheck")
    mots = pd.Series(
        [float("nan"), "articulasion", float("nan"), "xyzzyfoobar | inconnu"],
        name="spellcheck-mots")

    return pd.concat([spell, spellcheck, mots], axis=1)


@pytest.fixture
def ar() -> pd.DataFrame:
    return pd.DataFrame(
        {"term": ["Les prothèses de hanche", "le dipositif pour le bras",
                  "la prothèse de la hanche", "un dispositif pour un bras",
                  "une prothèse pour une hanche", "dispositif d'un bras",
                  "prothèse d'une hanche", "prothèse de hanche"]}
    )


@pytest.fixture
def ar2(ar) -> pd.DataFrame:
    ar2 = pd.Series(["1", "1", "1", "1", "1", float("nan"), float("nan"),
                     float("nan")], name="ar2")

    return pd.concat([ar, ar2], axis=1)


@pytest.fixture
def ar6(ar) -> pd.DataFrame:
    ar6 = pd.Series([float("nan"), "1", "1", "1", "1", "1", "1", float("nan")],
                    name="ar6")

    return pd.concat([ar, ar6], axis=1)


#######################################
# Fixtures pour règles Body structure #
#######################################
@pytest.fixture
def bs() -> pd.DataFrame:
    return pd.DataFrame(
        {"FSN": ["knee joint structure", "knee joint structure",
                 "entire hip region", "entire hip region", "part of hip zone",
                 "part of hip zone", "zone of cerebrum", "area of cerebrum",
                 "area of cerebrum", "area of brain", "area of brain",
                 "apex of proper heart", "apex of proper tongue",
                 "apex of proper tongue", "apex of proper tongue",
                 "apex of proper tongue", "structure lesser toe",
                 "structure lesser toe", "structure lesser toe",
                 "part of lower limb", "part of lower limb", "entire lower leg",
                 "entire lower leg", "entire lower leg", "entire lower leg",
                 "part of upper limb", "part of upper limb", "entire upper arm",
                 "entire upper arm", "entire upper arm"],
         "term": ["structure de l'articulation du genou", "genou",
                  "région entière de la hanche", "hanche",
                  "partie de la zone de la hanche", "hanche", "zone du cerveau",
                  "zone du cerveau", "surface de l'encéphale", "aire de l'encéphale",
                  "cerveau", "apex du cœur propre",
                  "pointe de la langue proprement dite",
                  "bout de la langue proprement dite",
                  "cime de la langue proprement dite", "langue",
                  "structure de l'orteil excepté l'hallux",
                  "structure de l'orteil latéral", "petit orteil",
                  "partie du membre inférieur", "partie de la jambe",
                  "partie inférieure entière de la jambe",
                  "partie basse entière de la jambe",
                  "jambe entière, du genou à la cheville", "mollet entier",
                  "partie du membre supérieur", "partie du bras",
                  "partie supérieure entière du bras",
                  "bras entier, de l'épaule au coude", "member supérieur entier"],
         "acceptabilityId": ["PREFERRED", "PREFERRED", "PREFERRED", "PREFERRED",
                             "PREFERRED", "PREFERRED", "PREFERRED", "PREFERRED",
                             "PREFERRED", "PREFERRED", "PREFERRED", "PREFERRED",
                             "ACCEPTABLE", "ACCEPTABLE", "ACCEPTABLE", "ACCEPTABLE",
                             "PREFERRED", "ACCEPTABLE", "ACCEPTABLE", "PREFERRED",
                             "PREFERRED", "PREFERRED", "ACCEPTABLE", "ACCEPTABLE",
                             "ACCEPTABLE", "PREFERRED", "PREFERRED", "PREFERRED",
                             "ACCEPTABLE", "ACCEPTABLE"]}
    )


@pytest.fixture
def bs2(bs) -> pd.DataFrame:
    bs2 = pd.Series([float("nan"), "1", float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan")], name="bs2")
    return pd.concat([bs, bs2], axis=1)


@pytest.fixture
def bs3(bs) -> pd.DataFrame:
    bs3 = pd.Series(["1", float("nan"), float("nan"), "1", float("nan"), "1",
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), "1", float("nan"), "1", float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan")], name="bs3")
    return pd.concat([bs, bs3], axis=1)


@pytest.fixture
def bs5(bs) -> pd.DataFrame:
    bs5 = pd.Series([float("nan"), float("nan"), float("nan"), "1", float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan")], name="bs5")
    return pd.concat([bs, bs5], axis=1)


@pytest.fixture
def bs6(bs) -> pd.DataFrame:
    bs6 = pd.Series([float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), "1", float("nan"), float("nan"), float("nan"),
                     float("nan"), "1", float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan")],
                    name="bs6")
    return pd.concat([bs, bs6], axis=1)


@pytest.fixture
def bs7(bs) -> pd.DataFrame:
    bs7 = pd.Series([float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), "1", float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan")], name="bs7")
    return pd.concat([bs, bs7], axis=1)


@pytest.fixture
def bs8(bs) -> pd.DataFrame:
    bs8 = pd.Series([float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), "1", float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan")], name="bs8")
    return pd.concat([bs, bs8], axis=1)


@pytest.fixture
def bs9(bs) -> pd.DataFrame:
    bs9 = pd.Series([float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), "1", float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan")], name="bs9")
    return pd.concat([bs, bs9], axis=1)


@pytest.fixture
def bs10(bs) -> pd.DataFrame:
    bs10 = pd.Series([float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"), "1",
                      float("nan"), float("nan"), float("nan"), "1", float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan")],
                     name="bs10")
    return pd.concat([bs, bs10], axis=1)


@pytest.fixture
def bs11(bs) -> pd.DataFrame:
    bs11 = pd.Series([float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), "1", float("nan"), float("nan"), "1"],
                     name="bs11")
    return pd.concat([bs, bs11], axis=1)


@pytest.fixture
def bs12(bs) -> pd.DataFrame:
    bs12 = pd.Series([float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"), "1",
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan")], name="bs12")
    return pd.concat([bs, bs12], axis=1)


@pytest.fixture
def bs13(bs) -> pd.DataFrame:
    bs13 = pd.Series([float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), "1", float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan")], name="bs13")
    return pd.concat([bs, bs13], axis=1)


#########################################
# Fixtures pour règles Clinical Finding #
#########################################
@pytest.fixture
def co_pa() -> pd.DataFrame:
    return pd.DataFrame(
        {"FSN": ["neurological finding", "finding of small intestine",
                 "finding of small intestine", "finding of small intestine",
                 "calcium level above reference range",
                 "calcium level above reference range",
                 "protein level above reference range",
                 "protein level above reference range",
                 "calcium level below reference range",
                 "calcium level below reference range",
                 "protein level below reference range",
                 "protein level below reference range",
                 "calcium level within reference range",
                 "calcium level within reference range",
                 "protein level within reference range",
                 "calcium level outside reference range",
                 "calcium level outside reference range",
                 "protein level outside reference range",
                 "pressure injury of hip", "pressure injury of hip",
                 "reflex epilepsy", "reflex epilepsy", "epileptic seizure",
                 "seizure disorder", "seizure disorder", "uremic convulsion",
                 "uremic convulsion", "visual impairment", "visual impairment",
                 "primary osteoporosis", "primary siphilis", "primary siphilis",
                 "chilblain", "chilblain", "frostbite of left hand",
                 "frostbite of left hand", "superficial frostbite of thorax",
                 "superficial frostbite of thorax", "carbuncle of breast",
                 "carbuncle of breast", "furuncle of hand", "furuncle of hand",
                 "furuncle of hand", "furuncle of hand", "boil of hand", "anthrax",
                 "anthrax"],
         "term": ["constatation neurologique",
                  "constatation à propos de l'intestin grêle",
                  "constatation concernant l'intestin grêle",
                  "observation de l'intestin grêle",
                  "calcium supérieur à l'intervalle de référence",
                  "calcium supérieur aux valeurs de référence",
                  "protéine supérieure à l'intervalle de référence",
                  "protéine augmentée", "calcium inférieur à l'intervalle de référence",
                  "calcium inférieur aux valeurs de référence",
                  "protein inférieure à l'intervalle de référence",
                  "protein diminuée", "calcium dans l'intervalle de référence",
                  "calcium dans les valeurs de référence",
                  "protéine normale", "calcium en dehors de l'intervalle de référence",
                  "calcium en dehors des valeurs de référence",
                  "protéine anormale", "escarre de la hanche",
                  "blessure par pression de la hanche", "épilepsie réflexe",
                  "crise réflexe", "crise épileptique", "trouble convulsif",
                  "épilepsie", "convulsions urémiques", "crise urémique",
                  "atteinte de la vision", "déficience visuelle",
                  "ostéoporose primitive", "syphilis primaire", "syphilis primordiale",
                  "engelure", "gelure", "gelure de la main gauche",
                  "engelure de la main gauche", "gelure superficielle du thorax",
                  "engelure superficielle du thorax", "anthrax du sein",
                  "furoncle du sein", "furoncle de la main",
                  "folliculite nécrotique de la main", "clou de la main",
                  "anthrax de la main", "furoncle de la main", "maladie du charbon",
                  "anthrax"]}
    )


@pytest.fixture
def co2(co_pa) -> pd.DataFrame:
    co2 = pd.Series([float("nan"), float("nan"), float("nan"), "1", float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan")], name="co2")
    return pd.concat([co_pa, co2], axis=1)


@pytest.fixture
def co6(co_pa) -> pd.DataFrame:
    co6 = pd.Series([float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), "1", float("nan"),
                     float("nan"), float("nan"), "1", float("nan"), float("nan"),
                     "1", float("nan"), float("nan"), "1", float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan")], name="co6")
    return pd.concat([co_pa, co6], axis=1)


@pytest.fixture
def pa3_1(co_pa) -> pd.DataFrame:
    pa3_1 = pd.Series([float("nan"), float("nan"), float("nan"), float("nan"),
                       float("nan"), float("nan"), float("nan"), float("nan"),
                       float("nan"), float("nan"), float("nan"), float("nan"),
                       float("nan"), float("nan"), float("nan"), float("nan"),
                       float("nan"), float("nan"), float("nan"), "1", float("nan"),
                       float("nan"), float("nan"), float("nan"), float("nan"),
                       float("nan"), float("nan"), float("nan"), float("nan"),
                       float("nan"), float("nan"), float("nan"), float("nan"),
                       float("nan"), float("nan"), float("nan"), float("nan"),
                       float("nan"), float("nan"), float("nan"), float("nan"),
                       float("nan"), float("nan"), float("nan"), float("nan"),
                       float("nan")], name="pa3.1")
    return pd.concat([co_pa, pa3_1], axis=1)


@pytest.fixture
def pa4(co_pa) -> pd.DataFrame:
    pa4 = pd.Series([float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), "1", float("nan"), float("nan"), "1", float("nan"),
                     "1", float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan")], name="pa4")
    return pd.concat([co_pa, pa4], axis=1)


@pytest.fixture
def pa6(co_pa) -> pd.DataFrame:
    pa6 = pd.Series([float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"), "1",
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan")], name="pa6")
    return pd.concat([co_pa, pa6], axis=1)


@pytest.fixture
def pa7(co_pa) -> pd.DataFrame:
    pa7 = pd.Series([float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), "1", float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan")], name="pa7")
    return pd.concat([co_pa, pa7], axis=1)


@pytest.fixture
def pa8(co_pa) -> pd.DataFrame:
    pa8 = pd.Series([float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), "1", float("nan"), "1", float("nan"), "1",
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan")],
                    name="pa8")
    return pd.concat([co_pa, pa8], axis=1)


@pytest.fixture
def pa9(co_pa) -> pd.DataFrame:
    pa9 = pd.Series([float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), "1", float("nan"),
                     float("nan"), float("nan"), "1", float("nan"), float("nan"), "1"],
                    name="pa9")
    return pd.concat([co_pa, pa9], axis=1)


############################################################
# Fixtures pour règles Pharmaceutical / biological product #
############################################################
@pytest.fixture
def me() -> pd.DataFrame:
    return pd.DataFrame(
        {"FSN": ["product containing amoxicilline", "product containing amoxicilline",
                 "product containing only amoxicilline",
                 "product containing only amoxicilline",
                 "product containing precisely captopril 25 mg/1 each conventional release oral tablet (clinical drug)", # noqa
                 "product containing precisely captopril 25 mg/1 each conventional release oral tablet (clinical drug)"], # noqa
         "term": ["produit contenant amoxicilline", "amoxicilline",
                  "produit contenant uniquement amoxicilline",
                  "produit contenant amoxicilline",
                  "produit contenant précisément captopril en comprimé oral à 25 mg",
                  "captopril 25 mg, comprimé oral en libération conventionnelle"]}
    )


@pytest.fixture
def me1(me) -> pd.DataFrame:
    me1 = pd.Series([float("nan"), "1", float("nan"), float("nan"), float("nan"),
                     float("nan")], name="me1")
    return pd.concat([me, me1], axis=1)


@pytest.fixture
def me2(me) -> pd.DataFrame:
    me2 = pd.Series([float("nan"), float("nan"), float("nan"), "1", float("nan"),
                     float("nan")], name="me2")
    return pd.concat([me, me2], axis=1)


@pytest.fixture
def me3(me) -> pd.DataFrame:
    me3 = pd.Series([float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), "1"], name="me3")
    return pd.concat([me, me3], axis=1)


@pytest.fixture
def me4(me) -> pd.DataFrame:
    me4 = pd.Series([float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), "1"], name="me4")
    return pd.concat([me, me4], axis=1)


########################################
# Fixtures pour règles Physical object #
########################################
@pytest.fixture
def sb() -> pd.DataFrame:
    return pd.DataFrame(
        {"FSN": ["evacuated blood collection tube, K2EDTA/aprotinin",
                 "evacuated blood collection tube, K2EDTA/aprotinin",
                 "evacuated urine specimen container, boric acid (H3BO3)",
                 "evacuated urine specimen container, boric acid (H3BO3)",
                 "stent", "stent", "stent", "stent"],
         "term": ["tube sous vide EDTA avec anticoagulant irréversible-K2/aprotinine pour prélèvement sanguin", # noqa
                             "tube sous vide EDTA avec anticoagulant irréversible-K2/aprotinine", # noqa
                             "support sous vide boraté pour prélèvement urinaire",
                             "acide borique pour prélèvement urinaire", "endoprothèse",
                             "stent", "stent", "endoprothèse"],
         "acceptabilityId": ["PREFERRED", "PREFERRED", "PREFERRED", "PREFERRED",
                             "PREFERRED", "ACCEPTABLE", "PREFERRED", "ACCEPTABLE"]}
    )


@pytest.fixture
def sb1(sb) -> pd.DataFrame:
    sb1 = pd.Series([float("nan"), "1", float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan")], name="sb1")
    return pd.concat([sb, sb1], axis=1)


@pytest.fixture
def sb2(sb) -> pd.DataFrame:
    sb2 = pd.Series([float("nan"), float("nan"), float("nan"), "1", float("nan"),
                     float("nan"), float("nan"), float("nan")], name="sb2")
    return pd.concat([sb, sb2], axis=1)


@pytest.fixture
def sb3(sb) -> pd.DataFrame:
    sb3 = pd.Series([float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), "1", "1"], name="sb3")
    return pd.concat([sb, sb3], axis=1)


##################################
# Fixtures pour règles Procedure #
##################################
@pytest.fixture
def pr() -> pd.DataFrame:
    return pd.DataFrame(
        {"FSN": ["MRI for neuromuscular procedure", "MRI for neuromuscular procedure",
                 "MRI for neuromuscular procedure", "MRI for neuromuscular procedure",
                 "perirenal operation using ultrasound guidance",
                 "perirenal operation using ultrasound guidance",
                 "perirenal operation using ultrasound guidance",
                 "perirenal operation using ultrasound guidance",
                 "telephone consultation", "telephone consultation",
                 "removal of foreign body from head",
                 "removal of foreign body from head",
                 "magnet extraction of foreign body from head",
                 "magnet extraction of foreign body from head",
                 "magnet extraction of foreign body from head",
                 "magnet extraction of foreign body from head",
                 "excisional biopsy of breast mass",
                 "excisional biopsy of breast mass",
                 "excisional biopsy of breast mass",
                 "excisional biopsy of breast mass", "incisional biopsy of brain",
                 "incisional biopsy of brain",
                 "magnetic resonance angiography of chest",
                 "magnetic resonance angiography of chest",
                 "magnetic resonance angiography of chest",
                 "magnetic resonance angiography of chest",
                 "fluoroscopy of trachea", "fluoroscopy of trachea",
                 "fluoroscopy of trachea", "fluoroscopy of trachea",
                 "pleurodesis using fluoroscopic guidance",
                 "pleurodesis using fluoroscopic guidance",
                 "pleurodesis using fluoroscopic guidance",
                 "pleurodesis using fluoroscopic guidance",
                 "pleurodesis using fluoroscopic guidance",
                 "hepatitis education", "hepatitis education"],
         "term": ["IRM pour procédure neuromusculaire",
                             "imagerie par résonance magnétique pour intervention neuromusculaire", # noqa
                             "imagerie par résonance magnétique pour intervention neuromusculaire", # noqa
                             "IRM pour procédure neuromusculaire",
                             "intervention chirurgicale périrénale guidée par échographie", # noqa
                             "chirurgie périrénale sous guidage échographique",
                             "opération périrénale guidée par échographie",
                             "intervention chirurgicale sous guidage échographique",
                             "consultation téléphonique", "rendez-vous téléphonique",
                             "retrait d'un corps étranger de la tête",
                             "extraction d'un corps étranger de la tête",
                             "extraction avec un aimant d'un corps étranger de la tête",
                             "retrait d'un corps étranger de la tête à l'aide d'un aimant", # noqa
                             "retrait d'un corps étranger de la tête à l'aide d'un aimant", # noqa
                             "extraction avec un aimant d'un corps étranger de la tête",
                             "biopsie-exérèse d'une masse mammaire",
                             "biopsie excisionnelle d'une masse mammaire",
                             "biopsie excisionnelle d'une masse mammaire",
                             "biopsie-exérèse d'une masse mammaire",
                             "biopsie incisionnelle de l'encéphale",
                             "biopsie par incision de l'encéphale",
                             "angiographie par IRM du thorax",
                             "angiographie par imagerie par résonance magnétique du thorax", # noqa
                             "angiographie par imagerie par résonance magnétique du thorax", # noqa
                             "angiographie par IRM du thorax",
                             "radioscopie de la trachée", "fluoroscopie de la trachée",
                             "fluoroscopie de la trachée", "radioscopie de la trachée",
                             "pleurodèse guidée par radioscopie",
                             "pleurodèse sous guidage radioscopique",
                             "pleurodèse guidée par fluoroscopie",
                             "pleurodèse sous guidage radioscopique",
                             "pleurodèse guidée par radioscopie",
                             "éducation concernant l'hépatite",
                             "formation concernant l'hépatite"],
         "acceptabilityId": ["PREFERRED", "ACCEPTABLE", "PREFERRED", "ACCEPTABLE",
                             "PREFERRED", "ACCEPTABLE", "ACCEPTABLE", "PREFERRED",
                             "PREFERRED", "PREFERRED", "PREFERRED", "PREFERRED",
                             "PREFERRED", "ACCEPTABLE", "PREFERRED", "ACCEPTABLE",
                             "PREFERRED", "ACCEPTABLE", "PREFERRED", "ACCEPTABLE",
                             "PREFERRED", "PREFERRED", "PREFERRED", "ACCEPTABLE",
                             "PREFERRED", "ACCEPTABLE", "PREFERRED", "ACCEPTABLE",
                             "PREFERRED", "ACCEPTABLE", "PREFERRED", "ACCEPTABLE",
                             "ACCEPTABLE", "PREFERRED", "ACCEPTABLE", "PREFERRED",
                             "PREFERRED"]}
    )


@pytest.fixture
def pr2(pr) -> pd.DataFrame:
    pr2 = pd.Series([float("nan"), float("nan"), "1", "1", float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan")], name="pr2")
    return pd.concat([pr, pr2], axis=1)


@pytest.fixture
def pr3(pr) -> pd.DataFrame:
    pr3 = pd.Series([float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), "1", float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan")],
                    name="pr3")
    return pd.concat([pr, pr3], axis=1)


@pytest.fixture
def pr4(pr) -> pd.DataFrame:
    pr4 = pd.Series([float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), "1", float("nan"),
                     float("nan"), "1", "1", float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan")], name="pr4")
    return pd.concat([pr, pr4], axis=1)


@pytest.fixture
def pr9(pr) -> pd.DataFrame:
    pr9 = pd.Series([float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), "1", "1", float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan")], name="pr9")
    return pd.concat([pr, pr9], axis=1)


@pytest.fixture
def pr10(pr) -> pd.DataFrame:
    pr10 = pd.Series([float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), "1", float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan")],
                     name="pr10")
    return pd.concat([pr, pr10], axis=1)


@pytest.fixture
def pr12(pr) -> pd.DataFrame:
    pr12 = pd.Series([float("nan"), float("nan"), "1", "1", float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), "1", "1", float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan")], name="pr12")
    return pd.concat([pr, pr12], axis=1)


@pytest.fixture
def pr13(pr) -> pd.DataFrame:
    pr13 = pd.Series([float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), "1", "1", float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan")], name="pr13")
    return pd.concat([pr, pr13], axis=1)


@pytest.fixture
def pr14(pr) -> pd.DataFrame:
    pr14 = pd.Series([float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      "1", "1", float("nan"), float("nan"), float("nan"), "1", "1",
                      float("nan"), float("nan")], name="pr14")
    return pd.concat([pr, pr14], axis=1)


@pytest.fixture
def pr15(pr) -> pd.DataFrame:
    pr15 = pd.Series([float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"),
                      float("nan"), float("nan"), float("nan"), float("nan"), "1"],
                     name="pr15")
    return pd.concat([pr, pr15], axis=1)


########################################################
# Fixtures pour règles Situation with explicit context #
########################################################
@pytest.fixture
def hs() -> pd.DataFrame:
    return pd.DataFrame(
        {"FSN": ["asthma familial history"] * 2,
         "term": ["antécédent familial d'asthme", "antécédents familiaux d'asthme"]}
    )


@pytest.fixture
def hs1(hs) -> pd.DataFrame:
    hs1 = pd.Series([float("nan"), "1"], name="hs1")
    return pd.concat([hs, hs1], axis=1)


#################################
# Fixtures pour règles Specimen #
#################################
@pytest.fixture
def ec() -> pd.DataFrame:
    return pd.DataFrame(
        {"FSN": ["implant submitted as specimen", "implant submitted as specimen",
                 "pharyngeal washings", "pharyngeal washings",
                 "cervix cytologic material", "cervix cytologic material",
                 "intravenous infusion fluid sample",
                 "intravenous infusion fluid sample"],
         "term": ["implant présenté comme échantillon", "échantillon d'implant",
                  "liquide de lavage pharyngien", "lavage pharyngien",
                  "matériel cytologique du col utérin", "matériel cervical",
                  "échantillon de liquide de perfusion intraveineuse",
                  "échantillon de perfusion intraveineuse"]}
    )


@pytest.fixture
def ec2(ec) -> pd.DataFrame:
    ec2 = pd.Series([float("nan"), "1", float("nan"), "1", float("nan"), "1",
                     float("nan"), float("nan")], name="ec2")
    return pd.concat([ec, ec2], axis=1)


@pytest.fixture
def ec4(ec) -> pd.DataFrame:
    ec4 = pd.Series([float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), "1"], name="ec4")
    return pd.concat([ec, ec4], axis=1)


##################################
# Fixtures pour règles Substance #
##################################
@pytest.fixture
def su() -> pd.DataFrame:
    return pd.DataFrame(
        {"FSN": ["rabies virus antibody", "rabies virus antibody",
                 "rabies virus immunoglobulin", "rabies virus antibody",
                 "rabies virus antibody", "rabies virus immunoglobulin",
                 "rabies virus immunoglobulin", "meta-hydroxybenzoate",
                 "ortho-hydroxybenzoate", "para-hydroxybenzoate", "m-hydroxybenzoate",
                 "X-meta-hydroxybenzoate", "X-ortho-hydroxybenzoate",
                 "X-para-hydroxybenzoate", "X-m-hydroxybenzoate", "moenomycin B>1<",
                 "moenomycin B>1<"],
         "term": ["Ig antirabique", "immunoglobuline antirabique",
                  "immunoglobuline antirabique", "immunoglobuline antirabique",
                  "Ig antirabique", "anticorps antirabique",
                  "immunoglobuline antirabique", "méta-hydroxybenzoate",
                  "ortho-hydroxybenzoate", "para-hydroxybenzoate", "m-hydroxybenzoate",
                  "X-méta-hydroxybenzoate", "X-ortho-hydroxybenzoate",
                  "X-para-hydroxybenzoate", "X-m-hydroxybenzoate", "moénomycine B>1<",
                  "moénomycine B1"],
         "acceptabilityId": ["PREFERRED", "PREFERRED", "PREFERRED", "ACCEPTABLE",
                             "ACCEPTABLE", "ACCEPTABLE", "ACCEPTABLE", "PREFERRED",
                             "PREFERRED", "PREFERRED", "PREFERRED", "PREFERRED",
                             "PREFERRED", "PREFERRED", "PREFERRED", "PREFERRED",
                             "PREFERRED"]}
    )


@pytest.fixture
def su1(su) -> pd.DataFrame:
    su1 = pd.Series(["1", float("nan"), float("nan"), "1", float("nan"), float("nan"),
                     "1", float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan")], name="su1")
    return pd.concat([su, su1], axis=1)


@pytest.fixture
def su3(su) -> pd.DataFrame:
    su3 = pd.Series([float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), "1", "1", "1",
                     float("nan"), "1", "1", "1", float("nan"), float("nan"),
                     float("nan")], name="su3")
    return pd.concat([su, su3], axis=1)


@pytest.fixture
def su8(su) -> pd.DataFrame:
    su8 = pd.Series([float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), float("nan"),
                     float("nan"), float("nan"), float("nan"), "1",
                     float("nan")], name="su8")
    return pd.concat([su, su8], axis=1)

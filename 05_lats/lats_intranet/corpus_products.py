"""The `products` site of the toy intranet: "Product Engineering", 8 pages.

    python3 corpus_products.py

Run it: the self check at the bottom re-derives every property this site is
responsible for, prints the page titles, and ends in
"corpus_products.py: all checks passed".

This file is ONE site of five. `intranet.py` imports the five `corpus_*.py`
modules and assembles them; nothing here imports anything else, so the five can
be authored and checked independently.

Format, as the loader in `intranet.py` expects it:

    PAGES = [{"title": str,
              "body":  [str, ...],          # rendered one line per entry, indented
              "links": [{"label": str, "target": "<site_key>/<page title>"}, ...]},
             ...]

`body` is a LIST OF LINES, not a blob, because `observe()` renders each entry as
its own indented line. Page order is the order of `PAGES`: `next` and `prev` walk it.

WHAT CHANGED IN THE REDESIGN
============================
`REDESIGN.md` rule 1: a hop 2 page must never state a single answer, it must be
a TABLE keyed by the entity hop 1 reveals. Landing on it is then necessary and
not sufficient, which is what makes the terminal reward carry information the
navigation heuristic does not already have. This site carries two such tables
and they are the reason the site exists in this shape.

WHAT THIS SITE OWNS
===================
Hop 1 facts (the bridge, stated here and nowhere else in the corpus):

    Q2  products/4  "Vega 3: KP-14 pressure cell, supplied by Talstrom Werke."
    Q7  products/4  "Kestrel: HX-7 humidity film, supplied by Aalvik Components."
    Q8  products/5  "Environmental tests for the Vega 3 run in the climate
                     chamber, laboratory L2-04."

Hop 2 tables (four rows, one per product line, the gold never singled out and
never the first row):

    Q9   products/4  "Sensing elements and suppliers"
                     gold Roswitha Elektronik, against Talstrom Werke,
                     Aalvik Components, Brindl Metall
    Q10  products/7  "Firmware release calendar"
                     gold October, against March, June, December

products/4 is the pivot of the whole set: hop 1 for Q2 and Q7, hop 2 for Q9.
That is the cleanest demonstration in the corpus that a page has no intrinsic
value. The same table is the destination for one query and the springboard for
two others, and the search cannot tell the cases apart from the page alone.

WHAT THIS SITE MUST NOT CARRY, AND WHY
======================================
No answer to any query this site bridges, or the query stops being two hop; and
no bridge fact owned by another site, or that query stops being two hop too. In
practice that bans, everywhere on this site:

  * any location: no building, no Winterthur, no assembly site. Q1 bridges
    "Vega team" to a building and Q10 bridges "Winterthur" to a product line,
    and both of those mappings live in `facilities` and `people`.
  * any firmware maintainer. Q9 bridges "Embedded Systems group" to a product
    line, and that mapping lives in `it`, on the source control page.
  * any person, any system name, any support queue, any access class, any
    signature level, any clock time, any four digit year, any franc amount, and
    any room code other than L2-04.

Roles are used instead of people ("the product owner", "the Metrology group"),
which is the Q6 trap in miniature: a role is not a person.

THE EARNED DISTRACTOR DUTIES
============================
The query design lists `products` as a distractor site for Q1, Q3 and Q5. Each
duty is real vocabulary overlap with an empty hand:

  Q1  "the building where the Vega team sits": the word Vega is all over this
      site, the Vega team owns the line on products/1, and no page here names a
      building or a room outside the laboratory L2-04.
  Q3  "the system in which the signed calibration certificates are archived":
      products/6 is a whole page about calibration and certificates that says in
      so many words that the system holding them is named in the policy and not
      here. The tempting near answer that turns out to be empty.
  Q5  "the site where the field service team is based": field service appears on
      products/6, booking return calibrations. No site, no time.
"""
import re

# ===========================================================================
# The pages, in order. next/prev walk this list.
# ===========================================================================

PAGES = [
    {
        "title": "Our product lines",
        "body": [
            "Product Engineering owns four instrument lines: Vega 3 pressure transmitters, "
            "Orion 2 flow meters, Kestrel humidity probes and Tarn 5 temperature probes.",
            "The three current lines have a page each, with ranges, applications and lead "
            "times.",
            "Tarn 5 is still supported and still built to order, but it is no longer actively "
            "sold, so it has no page of its own.",
            "Sensing elements and their suppliers are held together on one page rather than on "
            "the line pages, so that a change of supplier is recorded in one place.",
            "Release months for the firmware of all four lines are on the release calendar.",
            "Environmental testing, test rigs and calibration before dispatch are shared across "
            "the lines and have pages of their own.",
        ],
        "links": [
            {"label": "Sensing elements and suppliers",
             "target": "products/Sensing elements and suppliers"},
            {"label": "Test rigs and environmental testing",
             "target": "products/Test rigs and environmental testing"},
            {"label": "Firmware release calendar",
             "target": "products/Firmware release calendar"},
        ],
    },

    {
        "title": "Vega 3 pressure transmitters",
        "body": [
            "The Vega 3 is the current pressure transmitter line and replaces the earlier "
            "Vega 2.",
            "Ranges 0 to 40 bar, accuracy 0.05 percent of span.",
            "The housing is stainless steel and the standard output is 4 to 20 milliamperes.",
            "The Vega team owns the line and holds a design review every second week.",
            "A second source for the pressure cell was evaluated twice and was not approved, so "
            "the cell is bought under a framework contract.",
            "The supplier of the cell is on the sensing element page, and the account manager "
            "for that supplier is on the approved supplier list.",
            "Environmental testing for this line runs on the shared rigs and is described on "
            "the test rig page.",
            "Lead time is six weeks from order to dispatch.",
        ],
        "links": [
            {"label": "Sensing elements and suppliers",
             "target": "products/Sensing elements and suppliers"},
            {"label": "Approved suppliers", "target": "policies/Approved suppliers"},
        ],
    },

    {
        "title": "Orion 2 flow meters",
        "body": [
            "The Orion 2 is the current flow meter line and covers water, coolant and light "
            "oils.",
            "Ranges 0.5 to 300 litres per minute.",
            "Wetted parts are stainless steel and a hygienic variant is available for food and "
            "beverage customers.",
            "The Orion team owns the line, and a customer specific range has to be confirmed by "
            "the product owner before it is quoted.",
            "Standard lead time is eight weeks, and longer for the hygienic variant.",
            "The flow element and the company that supplies it are on the sensing element page.",
            "Two failures returned from the field last quarter were traced to fitting and not "
            "to the meter, so the fitting instructions were rewritten.",
        ],
        "links": [
            {"label": "Sensing elements and suppliers",
             "target": "products/Sensing elements and suppliers"},
        ],
    },

    {
        "title": "Kestrel humidity probes",
        "body": [
            "Kestrel probes are the smallest of the current lines and sell mainly to heating "
            "and ventilation customers.",
            "Ranges 0 to 100 percent relative humidity.",
            "The sensing film is sensitive to condensation, so probes stay in sealed bags with "
            "a desiccant until they are fitted.",
            "Volumes are lower than on the other lines, so the line is built in batches rather "
            "than continuously.",
            "The film and the company that supplies it are on the sensing element page.",
            "Drift is checked at every recalibration, and a probe that has drifted out of "
            "tolerance is replaced rather than adjusted.",
            "Probes are sold with a two year warranty, which is the same as the other lines.",
        ],
        "links": [
            {"label": "Calibration before dispatch",
             "target": "products/Calibration before dispatch"},
        ],
    },

    {
        "title": "Sensing elements and suppliers",
        "body": [
            "Every line is built around one bought in sensing element, and this page is the "
            "only place where the element and its supplier are recorded together.",
            "Vega 3: KP-14 pressure cell, supplied by Talstrom Werke.",
            "Orion 2: FM-9 flow element, supplied by Roswitha Elektronik.",
            "Kestrel: HX-7 humidity film, supplied by Aalvik Components.",
            "Tarn 5: RT-3 thermistor, supplied by Brindl Metall.",
            "Nothing else on any line is bought from a single source, so a change here is a "
            "change to the line.",
            "Account managers, framework contracts and audit status are held by the policy "
            "pages and are not repeated here.",
            "A change of element or of supplier needs a qualification run and a new test report "
            "before the first delivery.",
        ],
        "links": [
            {"label": "Approved suppliers", "target": "policies/Approved suppliers"},
            {"label": "Framework contracts", "target": "policies/Framework contracts"},
        ],
    },

    {
        "title": "Test rigs and environmental testing",
        "body": [
            "The pressure rig and the flow bench are in the workshop and are booked in the "
            "shared calendar.",
            "A rig may not be left loaded overnight.",
            "Environmental tests for the Vega 3 run in the climate chamber, laboratory L2-04.",
            "A full sequence is temperature cycling, damp heat and vibration, and takes about "
            "ten working days.",
            "The chamber is also used by the Kestrel line, so book it early in a release week.",
            "Laboratory doors are opened with a badge, and the access class a room needs is set "
            "by the room and not by the test, so check the facilities page before you book.",
            "Test reports are filed with the release documents and are quoted in customer "
            "qualification packs.",
        ],
        "links": [
            {"label": "Access classes by laboratory",
             "target": "facilities/Access classes by laboratory"},
            {"label": "Calibration before dispatch",
             "target": "products/Calibration before dispatch"},
        ],
    },

    {
        "title": "Calibration before dispatch",
        "body": [
            "Every instrument is calibrated before dispatch and again after a return from the "
            "field, and the field service team books the return calibrations.",
            "A calibration takes about half a day for a standard instrument.",
            "Bring the instrument with its serial number, because work without one cannot be "
            "recorded.",
            "Each measurement is entered as it is taken and the certificate is signed once the "
            "run is complete; the system that holds them is named in the calibration policy and "
            "not here.",
            "Reference standards are recalibrated externally once a year and carry their own "
            "certificates.",
            "A witnessed calibration for a customer is arranged with the product owner and adds "
            "about two days.",
            "The laboratory is run by the Metrology group, and questions about the record "
            "systems go to the service desk.",
        ],
        "links": [
            {"label": "Calibration and measurement records",
             "target": "policies/Calibration and measurement records"},
            {"label": "On call rota", "target": "it/On call rota"},
        ],
    },

    {
        "title": "Firmware release calendar",
        "body": [
            "Firmware for each line is released once a year, in the month shown here.",
            "Vega 3: March.",
            "Orion 2: June.",
            "Kestrel: October.",
            "Tarn 5: December.",
            "A release is numbered by year and by sequence, and a release note is published "
            "with it.",
            "Customers on a service contract are told two weeks before an update becomes "
            "mandatory.",
            "Updates are applied in the field over the service port, and there is no remote "
            "update path.",
            "An out of cycle release needs the agreement of the product owner and a new test "
            "report.",
            "Repository names and the group that looks after each line are recorded in source "
            "control and are not repeated here.",
        ],
        "links": [
            {"label": "Source control and firmware repositories",
             "target": "it/Source control and firmware repositories"},
        ],
    },
]

# ===========================================================================
# Self check. Everything below is a check, never a source of corpus text.
# ===========================================================================

SITE_KEY = "products"

TITLES = ["Our product lines", "Vega 3 pressure transmitters", "Orion 2 flow meters",
          "Kestrel humidity probes", "Sensing elements and suppliers",
          "Test rigs and environmental testing", "Calibration before dispatch",
          "Firmware release calendar"]

# The bridge facts this site owns: page index -> substrings the checker looks for.
# Each must be contiguous on exactly one page of this site.
OWNED_FACTS = {
    4: ["Vega 3: KP-14 pressure cell, supplied by Talstrom Werke.",     # Q2 hop 1
        "Kestrel: HX-7 humidity film, supplied by Aalvik Components."],  # Q7 hop 1
    5: ["Environmental tests for the Vega 3 run in the climate chamber, "
        "laboratory L2-04."],                                            # Q8 hop 1
}

# The hop 2 tables: page index -> (gold answer, the decoy answers).
# Rule 1 of REDESIGN.md. Every one of these strings must be on that page, the
# gold must not be the first row, and the rows must all have the same shape.
HOP2_TABLES = {
    4: ("Roswitha Elektronik",                                           # Q9
        ["Talstrom Werke", "Aalvik Components", "Brindl Metall"]),
    7: ("October", ["March", "June", "December"]),                       # Q10
}

# Row lines, in order, for each table page. The gold row is checked against these.
TABLE_ROWS = {
    4: ["Vega 3: KP-14 pressure cell, supplied by Talstrom Werke.",
        "Orion 2: FM-9 flow element, supplied by Roswitha Elektronik.",
        "Kestrel: HX-7 humidity film, supplied by Aalvik Components.",
        "Tarn 5: RT-3 thermistor, supplied by Brindl Metall."],
    7: ["Vega 3: March.", "Orion 2: June.", "Kestrel: October.", "Tarn 5: December."],
}

# The ten gold answers. Two of them are owned here, on their table page, because
# this site carries two hop 2 tables. The other eight must appear nowhere.
OWNED_GOLDS = {"Roswitha Elektronik": 4, "October": 7}
FOREIGN_GOLDS = ["N-310", "Ines Brauer", "Sanna Ilves", "Eiche", "07:20",
                 "Ana Ferreira", "2031", "Amber"]

# Bridge facts and key entities owned by the OTHER four sites. None may leak in
# here, or the query that turns on it stops being two hop.
FOREIGN_FACTS = ["Building Nord", "Building Sued", "Building West", "Winterthur",
                 "Embedded Systems", "Silvretta", "Varda", "level C",
                 "cost centre", "K2210", "K5000", "goods store"]

# Named entities this site must never mention: five systems, five queues, four
# access classes, and the francs the procurement bands are written in.
BANNED_WORDS = ["Aletsch", "Silvretta", "Napf", "Varda", "Zeitwerk",
                "Ahorn", "Birke", "Linde", "Eiche", "Ulme",
                "Blue", "Amber", "Violet", "Crimson",
                "francs", "level", "floor", "building", "queue"]

# Every person in the corpus. Not one of them, and not one of their name tokens,
# may appear here: partial credit is scored over tokens, so a stray token pays.
PEOPLE = ["Ines Brauer", "Lukas Feher", "Nora Sandu", "Jonas Bittner", "Clara Nyman",
          "Sanna Ilves", "Tomas Rask", "Yuki Oberer", "Dino Ravelli", "Bruno Achterberg",
          "Ana Ferreira", "Elke Rovinsky", "Marek Duval", "Rui Okonkwo", "Petra Lindqvist"]

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December"]

# Page titles of the other sites that the binding query design names. This is a
# PARTIAL list, enough to validate the link targets this site actually uses; the
# other sites carry landing and distractor pages the design does not name, and
# `intranet.py` is the authority on the full set.
KNOWN_TITLES = {
    "people": ["Team directory", "Signature levels and signatories", "Who leads what"],
    "facilities": ["Coffee lounges by building", "Shuttle timetable", "Badges and access",
                   "Access classes by laboratory", "The Winterthur site"],
    "it": ["On call rota", "Support routing by system",
           "Source control and firmware repositories"],
    "products": TITLES,
    "policies": ["Calibration and measurement records", "Approved suppliers",
                 "Framework contracts", "Procurement and purchase approvals"],
}


def page_text(i):
    """Title plus body, the exact string the corpus checker searches."""
    p = PAGES[i]
    return p["title"] + "\n" + "\n".join(p["body"])


def _hits(needle, flags=re.IGNORECASE):
    """Every page index whose text contains `needle` as a whole word run."""
    pat = re.compile(r"(?<![A-Za-z0-9])" + re.escape(needle) + r"(?![A-Za-z0-9])", flags)
    return [i for i in range(len(PAGES)) if pat.search(page_text(i))]


def _main():
    print("== corpus_products.py, the `products` site ==\n")

    # 1. shape and order
    assert [p["title"] for p in PAGES] == TITLES, "page titles or order changed"
    assert 7 <= len(PAGES) <= 8, len(PAGES)
    print("  1. %d pages, titles and order as designed:" % len(PAGES))
    for i, t in enumerate(TITLES):
        print("       products/%d  %s" % (i, t))

    # 2. ASCII only, and none of the punctuation the repo write hook rejects.
    #    The pattern is built rather than written out, so this file does not
    #    contain the thing it forbids.
    run_of_hyphens = "-" * 2
    for i, p in enumerate(PAGES):
        blob = page_text(i) + "\n" + "\n".join(
            l["label"] + l["target"] for l in p["links"])
        bad = [c for c in blob if ord(c) > 127]
        assert not bad, (i, bad)
        assert run_of_hyphens not in blob, i
    print("  2. ASCII only, no double hyphen, no em or en dash")

    # 3. body length
    print("  3. body word counts (60 to 140):")
    for i, p in enumerate(PAGES):
        n = len(" ".join(p["body"]).split())
        print("       %d  %-36s %3d words, %d lines" % (i, p["title"], n, len(p["body"])))
        assert 60 <= n <= 140, (i, n)

    # 4. the three bridge facts, each present on its page and on no other page here
    print("  4. hop 1 bridge facts, exactly one page each:")
    for idx, facts in OWNED_FACTS.items():
        for fact in facts:
            hits = [i for i in range(len(PAGES)) if fact.lower() in page_text(i).lower()]
            assert hits == [idx], (fact, hits)
            print("       products/%d  %r" % (idx, fact))

    # 5. REDESIGN rule 1: every hop 2 page here is a table that carries the gold
    #    AND every decoy, in rows of one shape, with the gold never first.
    print("  5. hop 2 tables, gold plus every decoy, gold not singled out:")
    for idx, (gold, decoys) in HOP2_TABLES.items():
        body = PAGES[idx]["body"]
        rows = TABLE_ROWS[idx]
        assert len(rows) >= 4, (idx, len(rows))
        for row in rows:
            assert row in body, (idx, row)          # a row is one whole body line
        for cand in [gold] + decoys:
            on = [r for r in rows if cand in r]
            assert len(on) == 1, (idx, cand, on)    # one row per candidate
        gold_row = [r for r in rows if gold in r][0]
        assert rows.index(gold_row) > 0, (idx, "the gold is the first row")
        # same shape: "<line>: <value>." on every row, so nothing marks the gold out
        for row in rows:
            assert re.match(r"^[A-Z][A-Za-z]*(?: \d)?: .+\.$", row), (idx, row)
        assert len(set(len(r.split(": ", 1)[1].split()) for r in rows)) <= 2, \
            (idx, "one row is much longer than the others")
        print("       products/%d  %d rows, gold %r is row %d of %d"
              % (idx, len(rows), gold, rows.index(gold_row) + 1, len(rows)))

    # 6. the two golds this site owns sit on their table page and nowhere else,
    #    and the other eight golds appear nowhere at all
    #    Whole word matching, not substring, and that is not fussiness: the gold
    #    of Q8 is "Amber" and the word "chamber" contains it. The reward is token
    #    F1, so "climate chamber" pays Q8 exactly 0.000 and leaks nothing; a
    #    substring check would reject a page that is in fact clean.
    for gold, idx in OWNED_GOLDS.items():
        assert _hits(gold) == [idx], (gold, _hits(gold))
    for gold in FOREIGN_GOLDS:
        assert not _hits(gold), (gold, _hits(gold))
    print("  6. the 2 golds owned here are on their table page only, "
          "the other 8 appear nowhere")

    # 7. no bridge fact or key entity owned by another site leaks in here
    for fact in FOREIGN_FACTS:
        hits = [i for i in range(len(PAGES)) if fact.lower() in page_text(i).lower()]
        assert not hits, (fact, hits)
    print("  7. no bridge fact owned by another site appears here")

    # 8. the answer shapes this site must never carry
    for i in range(len(PAGES)):
        t = page_text(i)
        assert not re.search(r"\d\d:\d\d", t), (i, "a clock time")
        assert not re.search(r"(?<![A-Za-z0-9])\d{4}(?![A-Za-z0-9])", t), (i, "a year")
        assert not re.search(r"(?<![A-Za-z])[NSWT]-\d{3}\b", t), (i, "a room code")
        assert not re.search(r"(?i)\bSD-", t), (i, "an old style queue name")
    for word in BANNED_WORDS:
        assert not _hits(word), (word, _hits(word))
    # the only room code allowed anywhere on this site is the laboratory L2-04
    codes = set()
    for i in range(len(PAGES)):
        codes.update(re.findall(r"(?<![A-Za-z])(?:L\d-\d\d|CR-\d)(?![A-Za-z0-9])",
                                page_text(i)))
    assert codes == {"L2-04"}, codes
    assert _hits("L2-04") == [5], _hits("L2-04")
    print("  8. no clock time, year, franc amount, queue, system, access class, "
          "signature level or room code, and L2-04 only on products/5")

    # 9. months live on the release calendar and nowhere else, so no review date
    #    or release note anywhere in the corpus can leak Q10's gold
    for month in MONTHS:
        hits = [i for i in range(len(PAGES)) if re.search(r"\b" + month + r"\b", page_text(i))]
        assert hits in ([], [7]), (month, hits)
    assert sorted(m for m in MONTHS
                  if re.search(r"\b" + m + r"\b", page_text(7))) == \
        sorted(["March", "June", "October", "December"])
    print("  9. the only months in this site are the four on products/7")

    # 10. no personal name, and no name token. Token matching, not substring:
    #     "manager" contains "ana", and partial credit is scored over tokens.
    name_tokens = set(t for p in PEOPLE for t in re.split(r"[^a-z0-9]+", p.lower()) if t)
    for i in range(len(PAGES)):
        page_tokens = set(t for t in re.split(r"[^a-z0-9]+", page_text(i).lower()) if t)
        clash = sorted(name_tokens & page_tokens)
        assert not clash, (i, clash)
    print("  10. no personal name, and no name token, on any page")

    # 11. links: resolving to titles that exist, none to itself, no gold in a label
    n_links = 0
    for i, p in enumerate(PAGES):
        assert len(p["links"]) <= 3, (i, "too many links for the action budget")
        n_links += len(p["links"])
        for link in p["links"]:
            site, _, title = link["target"].partition("/")
            assert site in KNOWN_TITLES, link
            assert title in KNOWN_TITLES[site], link
            assert not (site == SITE_KEY and title == p["title"]), ("self link", i)
            for gold in list(OWNED_GOLDS) + FOREIGN_GOLDS:
                assert gold.lower() not in link["label"].lower(), (gold, link)
    print("  11. %d links, all targets resolve, no self link, no gold in a label"
          % n_links)

    # 12. the three distractor duties, as assertions rather than as claims
    assert _hits("Vega team") == [1], _hits("Vega team")               # Q1 pull
    assert len([i for i in range(len(PAGES))
                if "vega" in page_text(i).lower()]) >= 4               # Q1 vocabulary
    assert _hits("field service") == [6], _hits("field service")       # Q5 pull
    calib = page_text(6).lower()
    assert "calibration" in calib and "certificate" in calib           # Q3 pull
    assert "named in the calibration policy and not here" in calib     # and it is empty
    print("  12. Q1 Vega pull, Q3 calibration pull with an empty hand, Q5 field service")

    print("\ncorpus_products.py: all checks passed")


if __name__ == "__main__":
    _main()

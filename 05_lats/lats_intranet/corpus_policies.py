"""The `policies` site of the Nordhelm Instruments AG intranet, "Policies and Compliance".

One of five corpus modules. It exports a single name:

    PAGES = [{"title": str, "body": str, "links": [{"label": str, "target": str}]}, ...]

in site order, so `next` and `prev` walk this list. `body` is a newline separated block:
the builder of `intranet.py` turns it into `Page.body` with

    tuple(page["body"].splitlines())

because `observe()` prints one body line indented by two spaces. `target` is
"<site_key>/<page title>", with the title copied exactly from `QUERIES.md` section 6, so
the builder resolves it to a (site, page index) pair without guessing.

REWRITTEN FOR THE REDESIGN (`REDESIGN.md`, `QUERIES.md`). The first build failed its own
ablation because a hop 2 page stated a single answer, so "I am on the right page" and
"I have the right answer" were the same event and the terminal reward carried no
information the navigation heuristic did not already have. Both hop 2 pages here are
TABLES keyed by the hop 1 entity: landing on one is necessary and not sufficient.

WHAT THIS SITE OWNS (`QUERIES.md` section 6). Four of the ten queries pass through here,
two from each end:

  Q3  HOP 1 on page 4, Calibration and measurement records. The bridge sentence is
      `Every calibration is logged as it is measured, and the signed certificate is
      archived in Silvretta.`  This is the only page in the corpus that says what
      Silvretta is for. The gold `Sanna Ilves` lives on it/On call rota and must never
      appear here.
  Q6  HOP 1 on page 1, Procurement and purchase approvals. The bands are stated in
      francs and NO person is named on the page: 12000 francs needs a level C signature,
      and who holds level C is only on people/Signature levels and signatories.
      Answering `level C` pays 0.000.
  Q2  HOP 2 on page 2, Approved suppliers. Five rows, company to account manager, and
      the page never says what any company supplies, so a reader without the hop 1 fact
      `supplied by Talstrom Werke` faces a one in five choice worth 0.200. Talstrom is
      the FOURTH row: in the first build it was first, and quoting the top line scored
      1.000 by accident.
  Q7  HOP 2 on page 3, Framework contracts. Five rows, company to contract expiry, keyed
      by exactly the same five companies as page 2. That pairing is the point: the two
      tables are each other's trap, because the sibling page answers with a name where
      the question wants a year, and pays 0.000. Aalvik is the fourth row.

RULES THE CHECKER ENFORCES, and which the prose below is written around:

  * Rule A, a hop 2 table is a bare key to value map and never describes its keys. Pages
    2 and 3 name no product, no part and no function, so nothing in a question can pick
    a row out of them directly;
  * Rule D, the mapping "key entity to gold" exists on exactly one page. `Talstrom Werke`
    sits with `Ines Brauer` only on page 2, and `Aalvik Components` with `2031` only on
    page 3;
  * every sentence `QUERIES.md` pins is kept verbatim, on its own line, because the
    corpus checks are substring checks against them;
  * no other query's gold answer, decoy answer or hop 1 bridge sentence appears anywhere
    in this file, so no page here carries two hops and no wrong table row leaks in;
  * `Roswitha Elektronik` is the one accepted exception (`QUERIES.md` concern 2): it is
    Q9's gold and also a row KEY on both tables here, where a blind pick pays 0.200,
    below the 0.250 of Q9's own hop 2 page, so it lifts nothing;
  * no gold answer appears in a link label;
  * no person is named except the five account managers this site owns, so the "no two
    people share a name token" property survives and partial credit cannot leak;
  * no clock time, no month name, no room code, no laboratory code, no access class and
    no support queue anywhere in this file. Each of those is a gold or a decoy somewhere
    else and each has to stay on its own table;
  * ASCII punctuation only, no en dash, no em dash, no prose double hyphen.

The distractor layer is earned, not planted. Page 6 carries the coffee lounge vocabulary
Q1 asks about and names no room (`QUERIES.md` Q1 calls it the highest word overlap in the
corpus). Page 5 carries the shuttle vocabulary Q5 asks about and no departure time, and
it does not name the destination either, so the timetable stays the only place that
mapping exists. Page 7 carries badge reader and door vocabulary for Q4 and access class
vocabulary for Q8, and names neither a queue nor a class.

NOTHING HERE IS REAL. Nordhelm Instruments AG, its people, suppliers and systems are
invented. Keep it that way.

Self check:  python3 corpus_policies.py
"""

SITE_KEY = "policies"
SITE_NAME = "Policies and Compliance"
BLURB = "Purchasing, travel and expenses, suppliers, data protection and incidents."


def _body(*lines):
    """One rendered body line per argument."""
    return "\n".join(lines)


PAGES = [

    # ==== 0. the landing page ==========================================================
    # Says out loud that a policy names a signature level and not a person, which is the
    # shape of Q6 and the reason answering from the hop 1 page pays 0.000. Its three
    # links put both hop 1 pages within two actions of the site entrance.
    {
        "title": "How our policies work",
        "body": _body(
            "Policies are owned by Operations and reviewed once a year.",
            "This site holds the rules that apply to everyone at Nordhelm Instruments AG, contractors included.",
            "The pages asked for most often are purchasing, travel, and the rules on calibration records.",
            "Each page states the rule, the limit that goes with it, and the signature level that approves.",
            "A policy names a signature level and never the person who holds it today, because the people change and the rule does not.",
            "An exception is agreed in writing before the fact, never afterwards.",
            "Anything a page does not settle goes to the policy owner in Operations.",
        ),
        "links": [
            {"label": "Procurement and purchase approvals",
             "target": "policies/Procurement and purchase approvals"},
            {"label": "Calibration and measurement records",
             "target": "policies/Calibration and measurement records"},
            {"label": "Travel and expenses",
             "target": "policies/Travel and expenses"},
        ],
    },

    # ==== 1. Q6 hop 1 ==================================================================
    # The four bands are pinned verbatim and are checked as substrings. 12000 francs
    # falls in the third band, so the key entity is `level C`. NO person is named here,
    # and no role either: a role would let a reader reason about seniority, which is the
    # leak that killed the first build's version of this query.
    {
        "title": "Procurement and purchase approvals",
        "body": _body(
            "Every purchase is approved before the order goes out, and the band depends on the total order value.",
            "Up to 1000 francs the team budget covers it.",
            "From 1000 to 5000 francs a level B signature is required.",
            "From 5000 to 50000 francs a level C signature is required.",
            "Above 50000 francs the board decides.",
            "Splitting a purchase into smaller orders to stay inside a band is not allowed.",
            "Every order is raised in the document system, and the signature is recorded against it and cannot be added later.",
            "The bands name a signature level and no person, so look the level up in the list of signatories.",
            "Buy from an approved company wherever the list offers one.",
        ),
        "links": [
            {"label": "Approved suppliers", "target": "policies/Approved suppliers"},
            {"label": "Framework contracts", "target": "policies/Framework contracts"},
            {"label": "Signature levels and signatories",
             "target": "people/Signature levels and signatories"},
        ],
    },

    # ==== 2. Q2 hop 2, a table and not an answer =======================================
    # Five companies, five account managers, and no statement anywhere of what any
    # company supplies. Talstrom Werke is the FOURTH row on purpose. The naive pick for
    # the supplier of a component is Aalvik Components, which pays 0.000.
    {
        "title": "Approved suppliers",
        "body": _body(
            "The companies below are approved for direct orders.",
            "Each one has an account manager, who is the first contact for prices, lead times and quality questions.",
            "Brindl Metall, account manager Lukas Feher.",
            "Aalvik Components, account manager Nora Sandu.",
            "Halden Kunststoff, account manager Jonas Bittner.",
            "Talstrom Werke, account manager Ines Brauer.",
            "Roswitha Elektronik, account manager Clara Nyman.",
            "This list does not record what any company supplies; that belongs with the engineering pages.",
            "A company that is not on the list needs a quality audit before the first order.",
            "Prices and account managers are reviewed once a year by Operations.",
        ),
        "links": [
            {"label": "Framework contracts", "target": "policies/Framework contracts"},
            {"label": "Sensing elements and suppliers",
             "target": "products/Sensing elements and suppliers"},
        ],
    },

    # ==== 3. Q7 hop 2, the sibling table ===============================================
    # The same five keys as page 2 and a year instead of a name. A reader who wants a
    # year and lands on page 2 gets a name and pays 0.000, and the other way round. Aalvik
    # Components is the fourth row. No product is named, so the key is unobtainable here.
    {
        "title": "Framework contracts",
        "body": _body(
            "A framework contract fixes prices and lead times for a term, so an order inside the term needs no new quotation.",
            "The terms in force are listed below.",
            "Brindl Metall: to the end of 2026.",
            "Talstrom Werke: to the end of 2027.",
            "Roswitha Elektronik: to the end of 2029.",
            "Aalvik Components: to the end of 2031.",
            "Halden Kunststoff: to the end of 2032.",
            "A renewal is negotiated by procurement well before the term ends, never by the team that places the order.",
            "This page records terms only; it does not say what any company supplies and it does not name an account manager.",
            "An order that would run past the end of a term is split, so nothing is ordered against a contract that has expired.",
        ),
        "links": [
            {"label": "Approved suppliers", "target": "policies/Approved suppliers"},
        ],
    },

    # ==== 4. Q3 hop 1 ==================================================================
    # The bridge sentence is pinned verbatim and this is the only page in the corpus that
    # says what Silvretta is for. The person on call for it is on it/On call rota and is
    # never named here; the queue that takes a fault in it is on it/Support routing by
    # system and is never named here either.
    {
        "title": "Calibration and measurement records",
        "body": _body(
            "Every instrument is calibrated against a reference standard before it is shipped and again at the interval printed on its certificate.",
            "Every calibration is logged as it is measured, and the signed certificate is archived in Silvretta.",
            "The archived copy is the record; a paper copy is a convenience and settles nothing.",
            "A certificate is kept for ten years after the instrument it belongs to was last shipped.",
            "An interval is never extended without a written exception agreed in advance.",
            "A measurement taken with an instrument that is out of calibration is reported to Quality on the same day.",
            "Read access is open to everyone, and only Quality may sign or withdraw a certificate.",
            "A fault in the systems named here goes through support routing during the day and follows the on call rota outside office hours.",
        ),
        "links": [
            {"label": "On call rota", "target": "it/On call rota"},
            {"label": "Support routing by system",
             "target": "it/Support routing by system"},
        ],
    },

    # ==== 5. travel, the earned distractor for Q5 ======================================
    # Shuttle vocabulary with no departure time AND no destination: the timetable stays
    # the only page that maps a destination to a time, and nothing here hints at which
    # row a reader should want.
    {
        "title": "Travel and expenses",
        "body": _body(
            "Book the train first; a flight needs a reason and is agreed with your line manager before booking.",
            "Second class is the standard for rail travel, and hotels are booked through the travel tool.",
            "Claims are submitted within 30 days and approved by your line manager.",
            "Scan every receipt and attach it to the claim; a claim without receipts comes back.",
            "Travel between the campus and the other company locations is covered by the shuttle and is not an expense.",
            "The shuttle timetable is published by facilities and is not repeated here.",
            "A taxi is claimed only when neither the shuttle nor a train runs.",
            "Parking permits are handled by facilities management and are not an expense either.",
        ),
        "links": [
            {"label": "Shuttle timetable", "target": "facilities/Shuttle timetable"},
            {"label": "Catering and the coffee lounges",
             "target": "policies/Catering and the coffee lounges"},
        ],
    },

    # ==== 6. catering, the earned distractor for Q1 ====================================
    # The highest word overlap with Q1 anywhere in the corpus, and it names no room. The
    # canteen sits in a building that is not Q1's answer, so a careless reader is drawn
    # to the wrong row of the lounge table, which pays 0.000.
    {
        "title": "Catering and the coffee lounges",
        "body": _body(
            "Coffee lounges are open to everyone on site, visitors and contractors included.",
            "Every building has one, and each is restocked twice a day.",
            "Hot drinks are free, and a machine that has run out is reported to facilities and not to the service desk.",
            "The canteen is in Building Sued and serves hot food over the middle of the day.",
            "Catering for a meeting is ordered three working days in advance and is charged to the cost centre of the team that ordered it.",
            "Food and drink served on the campus are never an expense claim.",
            "This page does not say where a lounge is; the facilities pages list them building by building.",
        ),
        "links": [
            {"label": "Coffee lounges by building",
             "target": "facilities/Coffee lounges by building"},
        ],
    },

    # ==== 7. incidents, the earned distractor for Q4 and Q8 ============================
    # Badge reader and door vocabulary for Q4 with no queue named, and access class
    # vocabulary for Q8 with no class named. Both overlaps are real and both are empty.
    {
        "title": "Reporting a fault or an incident",
        "body": _body(
            "Safety incidents go to the safety officer on the same day.",
            "An injury, a near miss, a spill or damaged equipment is reported even when nothing came of it.",
            "Security incidents go to the security mailbox.",
            "That covers a lost badge, a lost laptop, a stranger in the building, or a mail you believe is an attack.",
            "A door that will not open, or a badge reader that has stopped working, is a fault and not an incident.",
            "A fault is reported to the service desk, which routes it by the system that runs the hardware.",
            "A laboratory door that opens for the wrong people is both, so report it twice.",
            "Access to a laboratory is granted by access class, and a class is requested by your line manager.",
        ),
        "links": [
            {"label": "Badges and access", "target": "facilities/Badges and access"},
        ],
    },
]


# ===========================================================================
# Self check. Everything below is design time only; the notebook never imports it.
# ===========================================================================

TITLES = [
    "How our policies work",
    "Procurement and purchase approvals",
    "Approved suppliers",
    "Framework contracts",
    "Calibration and measurement records",
    "Travel and expenses",
    "Catering and the coffee lounges",
    "Reporting a fault or an incident",
]

# The two hop 2 tables, verbatim from QUERIES.md section 3, in page order.
Q2_ROWS = [
    "Brindl Metall, account manager Lukas Feher.",
    "Aalvik Components, account manager Nora Sandu.",
    "Halden Kunststoff, account manager Jonas Bittner.",
    "Talstrom Werke, account manager Ines Brauer.",
    "Roswitha Elektronik, account manager Clara Nyman.",
]
Q7_ROWS = [
    "Brindl Metall: to the end of 2026.",
    "Talstrom Werke: to the end of 2027.",
    "Roswitha Elektronik: to the end of 2029.",
    "Aalvik Components: to the end of 2031.",
    "Halden Kunststoff: to the end of 2032.",
]

# Sentences QUERIES.md pins for this site. The corpus checks are substring checks.
REQUIRED = {
    0: ["Policies are owned by Operations and reviewed once a year."],
    1: ["Up to 1000 francs the team budget covers it.",
        "From 1000 to 5000 francs a level B signature is required.",
        "From 5000 to 50000 francs a level C signature is required.",
        "Above 50000 francs the board decides."],
    2: Q2_ROWS,
    3: Q7_ROWS,
    4: ["Every calibration is logged as it is measured, and the signed certificate is archived in Silvretta."],
    5: ["Book the train first; a flight needs a reason and is agreed with your line manager before booking."],
    6: ["Every building has one, and each is restocked twice a day."],
    7: ["Safety incidents go to the safety officer on the same day.",
        "Security incidents go to the security mailbox."],
}

# This site's own two golds and two key entities.
OWN_GOLDS = ["Ines Brauer", "2031"]
OWN_KEYS = ["Talstrom Werke", "Aalvik Components"]

# The eight golds owned elsewhere, then every decoy answer owned elsewhere, then the
# eight hop 1 bridge facts owned elsewhere. None may appear anywhere in this file.
# Roswitha Elektronik is the one accepted exception (QUERIES.md concern 2) and is
# therefore absent from this list although it is Q9's gold.
FORBIDDEN = [
    # golds owned elsewhere
    "N-310", "Sanna Ilves", "Eiche", "07:20", "Ana Ferreira", "Amber", "October",
    # decoy answers owned elsewhere
    "S-121", "W-204", "T-018",
    "Tomas Rask", "Yuki Oberer", "Dino Ravelli", "Bruno Achterberg",
    "Ahorn", "Birke", "Linde", "Ulme",
    "06:45", "13:55", "16:10",
    "Elke Rovinsky", "Marek Duval", "Rui Okonkwo", "Petra Lindqvist",
    "Blue", "Violet", "Crimson",
    "March", "June", "December",
    "Talstrom Werke, account manager Clara",     # a row that must not be scrambled
    # key entities and hop 1 facts owned elsewhere
    "Building Nord", "Vega", "Orion", "Kestrel", "Tarn", "Winterthur",
    "field service", "Varda", "Aletsch", "Napf", "Zeitwerk",
    "L1-07", "L2-04", "L3-02", "CR-1", "climate chamber",
    "K2210", "K2240", "K3100", "K4120", "K5000",
    "KP-14", "FM-9", "HX-7", "RT-3",
]

# The only five people this site may name, and the ten it may not.
PEOPLE = ["Lukas Feher", "Nora Sandu", "Jonas Bittner", "Ines Brauer", "Clara Nyman"]
OTHER_PEOPLE = ["Tomas Rask", "Sanna Ilves", "Yuki Oberer", "Dino Ravelli",
                "Bruno Achterberg", "Elke Rovinsky", "Marek Duval", "Ana Ferreira",
                "Rui Okonkwo", "Petra Lindqvist"]

# Every gold in the redesigned query set, for the link label check.
ALL_GOLDS = ["N-310", "Ines Brauer", "Sanna Ilves", "Eiche", "07:20", "Ana Ferreira",
             "2031", "Amber", "Roswitha Elektronik", "October"]

SITE_KEYS = ("people", "facilities", "it", "products", "policies")


def _check():
    text = "\n".join(p["title"] + "\n" + p["body"] for p in PAGES)

    print("== titles and order ==")
    assert [p["title"] for p in PAGES] == TITLES, [p["title"] for p in PAGES]
    for i, p in enumerate(PAGES):
        n = len(p["body"].split())
        print("  %d  %-36s %3d words, %d lines, %d links"
              % (i, p["title"], n, len(p["body"].splitlines()), len(p["links"])))
        assert 60 <= n <= 140, (i, n)

    print("\n== the sentences QUERIES.md pins, kept verbatim ==")
    for i in sorted(REQUIRED):
        for s in REQUIRED[i]:
            assert s in PAGES[i]["body"], (i, s)
        print("  page %d: %d of %d body lines are pinned"
              % (i, len(REQUIRED[i]), len(PAGES[i]["body"].splitlines())))

    print("\n== Q2 hop 2 is a table, and the gold is not the first row ==")
    rows = [l for l in PAGES[2]["body"].splitlines() if "account manager" in l
            and any(q in l for q in PEOPLE)]
    assert rows == Q2_ROWS, rows
    assert rows[3].startswith("Talstrom Werke"), rows[3]
    assert "Ines Brauer" in rows[3] and "Ines Brauer" not in rows[0]
    assert "supplies" not in "\n".join(rows)
    print("  5 rows, Talstrom Werke is row 4, the top line names %s and pays 0.000"
          % rows[0].split("account manager ")[1].rstrip("."))

    print("\n== Q7 hop 2 is a table, keyed by the same five companies ==")
    years = [l for l in PAGES[3]["body"].splitlines() if l.endswith(".")
             and "to the end of" in l]
    assert years == Q7_ROWS, years
    assert years[3].startswith("Aalvik Components"), years[3]
    assert "2031" in years[3] and "2031" not in years[0]
    keys2 = sorted(l.split(",")[0] for l in Q2_ROWS)
    keys7 = sorted(l.split(":")[0] for l in Q7_ROWS)
    assert keys2 == keys7, (keys2, keys7)
    print("  5 rows, Aalvik Components is row 4, same five keys as Approved suppliers")

    print("\n== neither table describes its keys, so no question can pick a row ==")
    for i in (2, 3):
        for word in ("cell", "film", "element", "thermistor", "pressure", "humidity",
                     "flow", "sensing element", "supplies the"):
            assert word not in PAGES[i]["body"], (i, word)
    print("  pages 2 and 3 name no part, no product and no function")

    print("\n== Q6 hop 1 names a level and never a person ==")
    assert text.count("a level C signature is required") == 1
    for who in OTHER_PEOPLE:
        assert who not in PAGES[1]["body"], who
    for role in ("Head of Operations", "Managing Director", "Head of"):
        assert role not in PAGES[1]["body"], role
    print("  the 5000 to 50000 band is here once, no person and no role on the page")

    print("\n== Q3 hop 1 names the system and never the person or the queue ==")
    assert text.count("archived in Silvretta") == 1
    assert text.count("Silvretta") == 1
    assert "Sanna Ilves" not in text and "Birke" not in text
    print("  Silvretta appears exactly once in this site, on its hop 1 page")

    print("\n== Rule D: key entity and gold sit together on exactly one page ==")
    for key, gold, expect in (("Talstrom Werke", "Ines Brauer", 2),
                              ("Aalvik Components", "2031", 3)):
        hits = [i for i, p in enumerate(PAGES)
                if key in p["body"] and gold in p["body"]]
        assert hits == [expect], (key, gold, hits)
        print("  %-18s + %-12s only on page %d, %s" % (key, gold, expect,
                                                       PAGES[expect]["title"]))

    print("\n== no other query's gold, decoy or bridge fact leaks in ==")
    low = text.lower()
    for s in FORBIDDEN:
        assert s.lower() not in low, s
    print("  %d forbidden strings, none present" % len(FORBIDDEN))

    print("\n== no clock time, no month, no room code, no class, no queue ==")
    import re
    assert not re.search(r"\b\d{1,2}:\d{2}\b", text), "a clock time"
    assert not re.search(r"\b[A-Z]{1,2}-?\d{2,3}\b", text), "a room or part code"
    print("  none, so every one of those tables stays the only place its mapping exists")

    print("\n== no person outside the five account managers ==")
    for who in OTHER_PEOPLE:
        assert who not in text, who
    for who in PEOPLE:
        assert text.count(who) == 1, who
    print("  %d people named, once each: %s" % (len(PEOPLE), ", ".join(PEOPLE)))

    print("\n== links are well formed and no gold hides in a label ==")
    for i, p in enumerate(PAGES):
        for link in p["links"]:
            for g in ALL_GOLDS:
                assert g.lower() not in link["label"].lower(), (link, g)
            site, _, title = link["target"].partition("/")
            assert site in SITE_KEYS, link
            assert title, link
            assert not (site == SITE_KEY and title == p["title"]), ("self link", link)
            if site == SITE_KEY:
                assert title in TITLES, link
            assert link["label"] == title, ("label and title differ", link)
    n_links = sum(len(p["links"]) for p in PAGES)
    print("  %d links, all of the form <site_key>/<page title>, none self referential"
          % n_links)

    print("\n== every load bearing page is within 2 actions of page 0 ==")
    reach = {0: 0}
    for _ in range(3):
        for i, p in enumerate(PAGES):
            if i not in reach:
                continue
            for j in (i - 1, i + 1):
                if 0 <= j < len(PAGES):
                    reach[j] = min(reach.get(j, 99), reach[i] + 1)
            for link in p["links"]:
                site, _, title = link["target"].partition("/")
                if site == SITE_KEY:
                    j = TITLES.index(title)
                    reach[j] = min(reach.get(j, 99), reach[i] + 1)
    for i in (1, 2, 3, 4):
        assert reach[i] <= 2, (i, TITLES[i], reach[i])
        print("  %-36s %d action(s) from page 0" % (TITLES[i], reach[i]))

    print("\n== ASCII punctuation only ==")
    for bad in ("--", chr(0x2013), chr(0x2014), chr(0x2018), chr(0x2019),
                chr(0x201c), chr(0x201d)):
        assert bad not in text, repr(bad)
    assert all(ord(c) < 128 for c in text)
    print("  no double hyphen, no en dash, no em dash, no curly quotes")

    print("\ncorpus_policies: all checks passed")


if __name__ == "__main__":
    _check()

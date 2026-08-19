"""The `facilities` site of the toy intranet: "Facilities and Buildings", 8 pages.

One of the five corpus modules that `intranet.py` assembles. It carries data only, no
engine code, and it is importable from anywhere:

    from corpus_facilities import PAGES

    PAGES[i] = {"title": str,
                "body":  [str, ...],          # LINES, not one string. observe() prints
                                              # each line indented by two spaces
                "links": [{"label": str, "target": "<site_key>/<page title>"}, ...]}

Page order is the order of `PAGES`, so `next` and `prev` walk this list. Page indices are
0 based here and 1 based in everything the agent reads.

    python3 corpus_facilities.py            # runs the self check below

WHAT CHANGED IN THE REDESIGN (`REDESIGN.md`, `QUERIES.md`)
==========================================================
The first build let a hop 2 page STATE the answer, so "I am on the right page" and "I
have the right answer" were the same event, and the terminal reward carried no
information the navigation heuristic did not already have. Every hop 2 page is now a
TABLE KEYED BY THE HOP 1 ENTITY. This site carries three of them, and they are the
reason the site was rewritten rather than edited:

  Coffee lounges by building     Q1 hop 2, four rows, building to lounge room code
  Shuttle timetable              Q5 hop 2, four rows, destination to departure time
  Access classes by laboratory   Q8 hop 2, four rows, room code to access class

A reader who lands on one of them without hop 1 faces a real four way choice, and Rule C
of `QUERIES.md` (gold and decoys share no token) makes every wrong row pay exactly 0.000.
Landing on the right page is worth 0.250, not 1.000.

Two hop 1 pages live here as well:

  Badges and access              Q4 hop 1, names the system: Varda
  The Winterthur site            Q10 hop 1, names the product line: Kestrel

RULE A IS THE ONE THAT IS EASY TO BREAK BY BEING HELPFUL
========================================================
A hop 2 table is a bare key to value map and NEVER describes its keys. If the access
table said "L2-04 climate chamber", a reader who saw "environmental tests" in Q8 could
match climate to chamber and skip hop 1, and the redesign would be undone a second time.
So the rooms here are bare codes, the shuttle destinations are bare place names, and what
a room or a site is FOR is said only on the hop 1 page that uses it.

The same rule is why the surrounding prose is careful rather than merely plausible. This
site may add vocabulary; it must not add an answer of the right shape, and it must not
add a second route from a key to its gold. Concretely, nowhere on this site:

  * no team name, so nothing here says which building the Vega team sits in (Q1 hop 1)
  * no mention of field service, so nothing here says where it is based (Q5 hop 1)
  * no room description on the access table, and "climate chamber" is a products string
  * no clock time except the four in the shuttle timetable (they share no token)
  * no room code except the four lounges and the four laboratories (Q1's codes carry the
    building initial, so any fifth N, S, W or T code would pay 0.500 to a wrong row)
  * no colour except the four access classes, no month, no year, no person
  * no support queue and no system name except Varda

Nordhelm Instruments AG is invented, and so is everything below it.
"""

SITE_KEY = "facilities"
SITE_NAME = "Facilities and Buildings"
BLURB = "Buildings, floors, laboratories, badges, parking and the shuttle."

# ==== the pages ====================================================================

PAGES = [
    {
        "title": "Facilities at a glance",
        "body": [
            "Facilities management looks after the buildings, the laboratories, the badge "
            "system, parking and the shuttle.",
            "Nordhelm Instruments AG works from the Zurich Nord campus and four other "
            "locations: the Duebendorf depot, the Rheinfelden works, the Winterthur site "
            "and the Zug office.",
            "The campus itself has three buildings, Nord, Sued and West.",
            "The lists on this site are the ones facilities management keeps and corrects, "
            "so a room code or a departure quoted in a mail or a slide is not "
            "authoritative.",
            "A broken lift, a door that will not close or a room that is too warm is "
            "reported to facilities management and not to the service desk.",
            "Room bookings for more than twenty people, furniture moves and anything that "
            "needs a key are handled here as well.",
        ],
        "links": [
            {"label": "The Winterthur site", "target": "facilities/The Winterthur site"},
            {"label": "Shuttle timetable", "target": "facilities/Shuttle timetable"},
            {"label": "Badges and access", "target": "facilities/Badges and access"},
        ],
    },
    {
        "title": "The Zurich Nord campus",
        "body": [
            "Building Nord holds reception, the training rooms and two floors of offices.",
            "Building Sued holds the canteen, the post room and the project rooms.",
            "Building West holds the workshop, the loading bay and the drawing archive.",
            "The laboratories are on the lower floors of Building West and are reached "
            "through the corridor behind the workshop.",
            "Every building has one coffee lounge. The room it is in is on the coffee "
            "lounges page and not here.",
            "Visitors sign in at reception, are given a visitor badge and are collected "
            "there by whoever invited them.",
            "Meeting rooms are booked in the room booking tool, and a booking that nobody "
            "claims is released after fifteen minutes.",
        ],
        "links": [
            {"label": "Coffee lounges by building",
             "target": "facilities/Coffee lounges by building"},
        ],
    },
    {
        "title": "Coffee lounges by building",
        "body": [
            "One lounge per building and site, with the room it is in.",
            "Building Nord: N-310.",
            "Building Sued: S-121.",
            "Building West: W-204.",
            "Winterthur site: T-018.",
            "The lounges are open to everyone on site and are not bookable, so a lounge "
            "cannot be held for a meeting.",
            "Cups and plates belong in the trolleys on each floor and not on the tables in "
            "the lounges.",
            "A lounge that has run out is reported to facilities management rather than to "
            "the catering supplier.",
            "The machines are serviced once a month and the service dates are posted "
            "beside them.",
        ],
        "links": [],
    },
    {
        "title": "The Winterthur site",
        "body": [
            "The Winterthur site assembles the Kestrel humidity probes and holds the goods "
            "store.",
            "There is one building, with the assembly hall and the store on the ground "
            "floor and offices above.",
            "The site is about twenty minutes from the campus by road and is served by the "
            "works shuttle.",
            "Deliveries for the whole company arrive here first and are forwarded to the "
            "campus twice a week.",
            "Badges issued on the campus work here without a change of access class, and "
            "visitors are registered at the entrance in the same way.",
            "The release calendar for the line built here is kept by Product Engineering.",
            "Post for the site travels on the shuttle.",
        ],
        "links": [
            {"label": "Firmware release calendar",
             "target": "products/Firmware release calendar"},
        ],
    },
    {
        "title": "Shuttle timetable",
        "body": [
            "One departure per destination each working day, from the stop at the north "
            "entrance.",
            "Duebendorf depot: 06:45.",
            "Winterthur site: 07:20.",
            "Rheinfelden works: 13:55.",
            "Zug office: 16:10.",
            "Seats are booked the day before through facilities management, and a seat "
            "that is not claimed is released to the waiting list.",
            "The return departures are published at the stop and are not repeated here.",
            "The campus loop between the three buildings runs on its own timetable, which "
            "is posted in each entrance hall.",
            "A journey the shuttle does not cover is claimed as a travel expense.",
        ],
        "links": [],
    },
    {
        "title": "Parking and the shuttle",
        "body": [
            "Parking permits are requested through facilities management and are issued "
            "per person for one year.",
            "The barrier reads your badge, so nothing has to be displayed in the "
            "windscreen.",
            "The waiting list is longest for the underground spaces, and a permit that "
            "goes unused for a quarter is withdrawn.",
            "Visitors park in the marked bays in front of the main entrance and are "
            "registered at reception.",
            "Bicycles go in the covered racks at each building and not against the "
            "railings.",
            "Charging points for electric cars are on the lowest parking level and are for "
            "charging only, not for long stay parking.",
            "The shuttle to each of the other locations leaves from the north entrance, "
            "and the departures are on the shuttle timetable page.",
        ],
        "links": [
            {"label": "Badges and access", "target": "facilities/Badges and access"},
        ],
    },
    {
        "title": "Badges and access",
        "body": [
            "Badges are issued at reception on the first working day and are collected in "
            "person.",
            "Badge readers and door groups are managed in Varda.",
            "Every laboratory door carries an access class, and the class a given room "
            "needs is listed on the access classes page.",
            "A class your badge does not carry is requested by your line manager and is "
            "granted room by room rather than floor by floor.",
            "Your badge is also your print release card and your canteen card.",
            "Report a lost badge to reception on the same day; the old badge is blocked at "
            "once.",
            "A door that refuses a badge it should accept is a fault in the system behind "
            "the door, and it goes to the support queue for that system.",
        ],
        "links": [
            {"label": "Access classes by laboratory",
             "target": "facilities/Access classes by laboratory"},
            {"label": "Support routing by system",
             "target": "it/Support routing by system"},
        ],
    },
    {
        "title": "Access classes by laboratory",
        "body": [
            "The class each laboratory door requires, by room code.",
            "L1-07: class Blue.",
            "L2-04: class Amber.",
            "L3-02: class Violet.",
            "CR-1: class Crimson.",
            "What a room is used for, and which group has booked it, is kept by that group "
            "and not on this page.",
            "A class is granted for one room at a time and lapses when you move to another "
            "group.",
            "Eating and drinking are not allowed in any of these rooms, and working alone "
            "in one needs a written agreement from your line manager.",
            "A door that opens for a badge that should not carry the class is reported the "
            "same day.",
        ],
        "links": [],
    },
]

# ==== the pinned text, and the self check ==========================================

# `QUERIES.md` section 3, verbatim. Every line must appear on its page, in this order.
QUERY_LINES = {
    "Coffee lounges by building": [
        "Building Nord: N-310.",
        "Building Sued: S-121.",
        "Building West: W-204.",
        "Winterthur site: T-018.",
    ],
    "The Winterthur site": [
        "The Winterthur site assembles the Kestrel humidity probes and holds the goods "
        "store.",
    ],
    "Shuttle timetable": [
        "Duebendorf depot: 06:45.",
        "Winterthur site: 07:20.",
        "Rheinfelden works: 13:55.",
        "Zug office: 16:10.",
    ],
    "Badges and access": [
        "Badge readers and door groups are managed in Varda.",
    ],
    "Access classes by laboratory": [
        "L1-07: class Blue.",
        "L2-04: class Amber.",
        "L3-02: class Violet.",
        "CR-1: class Crimson.",
    ],
}

# The pinned link set: page title, then its links in order.
DESIGN_LINKS = {
    "Facilities at a glance": [
        ("The Winterthur site", "facilities/The Winterthur site"),
        ("Shuttle timetable", "facilities/Shuttle timetable"),
        ("Badges and access", "facilities/Badges and access"),
    ],
    "The Zurich Nord campus": [
        ("Coffee lounges by building", "facilities/Coffee lounges by building"),
    ],
    "Coffee lounges by building": [],
    "The Winterthur site": [
        ("Firmware release calendar", "products/Firmware release calendar"),
    ],
    "Shuttle timetable": [],
    "Parking and the shuttle": [
        ("Badges and access", "facilities/Badges and access"),
    ],
    "Badges and access": [
        ("Access classes by laboratory", "facilities/Access classes by laboratory"),
        ("Support routing by system", "it/Support routing by system"),
    ],
    "Access classes by laboratory": [],
}

# The three hop 2 tables this site owns: query id, page, gold, decoys. The gold and every
# decoy must be on that page and nowhere else here, which is invariant 5 of REDESIGN.md
# and Rule C of QUERIES.md as far as one site can check them.
TABLES = {
    1: ("Coffee lounges by building", "N-310", ("S-121", "W-204", "T-018")),
    5: ("Shuttle timetable", "07:20", ("06:45", "13:55", "16:10")),
    8: ("Access classes by laboratory", "Amber", ("Blue", "Violet", "Crimson")),
}

# The two hop 1 bridge sentences this site owns, and the page that owns each.
OWNED_FACTS = {
    "Badge readers and door groups are managed in Varda.": "Badges and access",     # Q4
    "The Winterthur site assembles the Kestrel humidity probes and holds the goods "
    "store.": "The Winterthur site",                                                # Q10
}

# For every query that touches this site: the key entity hop 1 reveals, the gold, and the
# one page here that is allowed to carry both (None when the gold lives on another site).
# This is Rule D, the two hop guarantee, in the form one site can check.
KEY_TO_GOLD = {
    1: ("Building Nord", "N-310", "Coffee lounges by building"),
    4: ("Varda", "Eiche", None),
    5: ("Winterthur site", "07:20", "Shuttle timetable"),
    8: ("L2-04", "Amber", "Access classes by laboratory"),
    10: ("Kestrel", "October", None),
}

# Gold answers owned by other sites. None of them may appear anywhere here.
FOREIGN_GOLDS = ["Ines Brauer", "Sanna Ilves", "Eiche", "Ana Ferreira", "2031",
                 "Roswitha Elektronik", "October"]

# Decoy rows of the tables the other four sites own. Also forbidden here: a stray
# "Marek Duval" or "Ahorn" would give a blind reader a second place to find a row.
FOREIGN_DECOYS = ["Lukas Feher", "Nora Sandu", "Jonas Bittner", "Clara Nyman",
                  "Tomas Rask", "Yuki Oberer", "Dino Ravelli", "Bruno Achterberg",
                  "Elke Rovinsky", "Marek Duval", "Rui Okonkwo", "Petra Lindqvist",
                  "Ahorn", "Birke", "Linde", "Ulme",
                  "2026", "2027", "2029", "2032",
                  "March", "June", "December"]

# Hop 1 facts and key entities owned by other pages. Several are near misses of sentences
# that DO appear here, which is exactly why they are checked: this site says "the
# Winterthur site" constantly and must never say who is based there, and it names Varda
# once and must never name the queue that Varda's faults go to.
FOREIGN_FACTS = ["Vega team", "Field service", "field service", "climate chamber",
                 "laboratory L2-04", "supplied by", "Talstrom Werke",
                 "Aalvik Components", "Silvretta", "Orion 2", "level C",
                 "archived in", "maintained by"]

# Every gold in the corpus, for the link label leak check.
ALL_GOLDS = [gold for _, gold, _ in TABLES.values()] + FOREIGN_GOLDS

# Words that are answers of the right shape on some other page, or that would create a
# second candidate row here. None may appear as a WORD anywhere on this site. The check
# is token based on purpose: a substring test would fire on "red" inside "required".
BANNED_WORDS = ["vega", "orion", "tarn", "brindl", "halden", "roswitha", "talstrom",
                "aalvik", "aletsch", "silvretta", "napf", "zeitwerk",
                "ahorn", "birke", "eiche", "linde", "ulme",
                "january", "february", "march", "april", "may", "june", "july",
                "august", "september", "october", "november", "december",
                "green", "red", "yellow", "orange", "grey", "gray", "white", "black"]

# The only tokens on this site that may carry a digit. Anything else is a new answer of
# the right shape: a fifth room code, a fifth departure, a year, a cost centre.
DIGIT_TOKENS = {"n-310", "s-121", "w-204", "t-018",
                "06:45", "07:20", "13:55", "16:10",
                "l1-07", "l2-04", "l3-02", "cr-1"}

# Where each colour is allowed to appear. One page each, and nowhere else.
COLOURS = {"Blue": "Access classes by laboratory",
           "Amber": "Access classes by laboratory",
           "Violet": "Access classes by laboratory",
           "Crimson": "Access classes by laboratory"}


def page_text(page):
    """Title plus body, the way the corpus checks scan a page."""
    return page["title"] + "\n" + "\n".join(page["body"])


def _pages_with(text):
    """The titles of the pages whose text contains `text`, case insensitively."""
    return [p["title"] for p in PAGES if text.lower() in page_text(p).lower()]


def _check():
    titles = [p["title"] for p in PAGES]
    expected = ["Facilities at a glance", "The Zurich Nord campus",
                "Coffee lounges by building", "The Winterthur site",
                "Shuttle timetable", "Parking and the shuttle", "Badges and access",
                "Access classes by laboratory"]
    print("== 1. page order ==")
    assert titles == expected, titles
    for i, t in enumerate(titles):
        print("  %d  %s" % (i, t))
    print("  %d pages" % len(PAGES))

    print("\n== 2. ASCII only, which rules out every typographic dash ==")
    for p in PAGES:
        blob = page_text(p) + "".join(l["label"] + l["target"] for l in p["links"])
        blob.encode("ascii")
        assert "--" not in blob, p["title"]
    print("  clean")

    print("\n== 3. body length, 60 to 140 words ==")
    for p in PAGES:
        n = len(" ".join(p["body"]).split())
        print("  %-30s %3d words" % (p["title"], n))
        assert 60 <= n <= 140, (p["title"], n)
        for line in p["body"]:
            assert line and line.strip() == line, (p["title"], line)

    print("\n== 4. the text QUERIES.md pins is present, verbatim and in order ==")
    for title, lines in QUERY_LINES.items():
        page = [p for p in PAGES if p["title"] == title][0]
        pos = -1
        for line in lines:
            assert line in page["body"], (title, line)
            i = page["body"].index(line)
            assert i > pos, "out of order: %r" % line
            pos = i
    print("  %d pinned lines, all present" % sum(len(v) for v in QUERY_LINES.values()))

    print("\n== 5. links are exactly the pinned set ==")
    n_links = 0
    for p in PAGES:
        got = [(l["label"], l["target"]) for l in p["links"]]
        assert got == DESIGN_LINKS[p["title"]], (p["title"], got)
        n_links += len(got)
        for label, target in got:
            site, _, title = target.partition("/")
            assert site in ("people", "facilities", "it", "products", "policies"), target
            assert title, target
            assert not (site == SITE_KEY and title == p["title"]), "self link"
            if site == SITE_KEY:
                assert title in titles, target
    print("  %d links leaving these pages, no self links" % n_links)
    for p in PAGES:
        for l in p["links"]:
            for gold in ALL_GOLDS:
                assert gold.lower() not in l["label"].lower(), (p["title"], gold)
    print("  no gold leaks into a link label")

    print("\n== 6. every load bearing page is within 2 actions of page 0 ==")
    # Page 0 is where goto_site[facilities] lands. One action is next, prev or follow.
    reach = {0: 0}
    frontier = [0]
    for _ in range(2):
        nxt = []
        for i in frontier:
            neighbours = [j for j in (i - 1, i + 1) if 0 <= j < len(PAGES)]
            for link in PAGES[i]["links"]:
                site, _, title = link["target"].partition("/")
                if site == SITE_KEY:
                    neighbours.append(titles.index(title))
            for j in neighbours:
                if j not in reach:
                    reach[j] = reach[i] + 1
                    nxt.append(j)
        frontier = nxt
    load_bearing = ["Coffee lounges by building", "The Winterthur site",
                    "Shuttle timetable", "Badges and access",
                    "Access classes by laboratory"]
    for title in load_bearing:
        i = titles.index(title)
        assert i in reach, (title, "not reachable in 2 actions")
        print("  %-30s %d action(s) from page 0" % (title, reach[i]))

    print("\n== 7. the three hop 2 tables ==")
    for qid, (title, gold, decoys) in sorted(TABLES.items()):
        page = [p for p in PAGES if p["title"] == title][0]
        text = page_text(page).lower()
        for candidate in (gold,) + decoys:
            assert candidate.lower() in text, (title, candidate)
            hits = _pages_with(candidate)
            assert hits == [title], (candidate, hits)
        print("  Q%-2d %-30s gold %-8s and %d decoys, all on this page only"
              % (qid, title, gold, len(decoys)))
    for gold in FOREIGN_GOLDS + FOREIGN_DECOYS:
        assert not _pages_with(gold), (gold, _pages_with(gold))
    print("  no row of another site's table appears here")

    print("\n== 8. hop 1 bridge facts ==")
    for fact, owner in OWNED_FACTS.items():
        hits = _pages_with(fact)
        print("  %-30s on %s" % (fact.split(" are ")[0].split(" assembles")[0], hits))
        assert hits == [owner], (fact, hits)
    for fact in FOREIGN_FACTS:
        assert not _pages_with(fact), (fact, _pages_with(fact))
    print("  no hop 1 fact owned by another page appears here, and no team is placed")

    print("\n== 9. Rule D, the key to gold mapping lives on one page ==")
    for qid, (key, gold, owner) in sorted(KEY_TO_GOLD.items()):
        both = [p["title"] for p in PAGES
                if key.lower() in page_text(p).lower()
                and gold.lower() in page_text(p).lower()]
        assert both == ([] if owner is None else [owner]), (qid, both)
        print("  Q%-2d %-16s to %-8s  %s"
              % (qid, key, gold, owner if owner else "gold is on another site"))

    print("\n== 10. no new answer of the right shape ==")
    corpus = "\n".join(page_text(p) for p in PAGES)
    lowered = corpus.lower()
    tokens = {w.strip(".,:;()") for w in lowered.replace("\n", " ").split()}
    digits = sorted(w for w in tokens if any(c.isdigit() for c in w))
    print("  tokens carrying a digit: %s" % ", ".join(digits))
    assert set(digits) == DIGIT_TOKENS, set(digits) ^ DIGIT_TOKENS
    for word in BANNED_WORDS:
        assert word not in tokens, word
    print("  no month, no year, no stray colour, no queue, no system but Varda")
    for colour, owner in COLOURS.items():
        assert _pages_with(colour) == [owner], (colour, _pages_with(colour))
    print("  each access class appears on one page only")
    for word in ("Varda", "Kestrel"):
        assert len(_pages_with(word)) == 1, (word, _pages_with(word))
    print("  Varda and Kestrel are each named on exactly one page")

    print("\nall checks passed")


if __name__ == "__main__":
    _check()

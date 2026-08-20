"""The `people` site of the toy intranet: "People and Teams".

One of five corpus modules (`corpus_people.py`, `corpus_facilities.py`,
`corpus_it.py`, `corpus_products.py`, `corpus_policies.py`). `intranet.py`
assembles them into SITES; nothing here imports anything.

    PAGES = [{"title": str, "body": [str, ...], "links": [{"label": str,
                                                           "target": "<site_key>/<page title>"}]}, ...]

`body` is a LIST OF DISPLAY LINES, one per rendered line, matching
`Page.body: tuple[str, ...]` in DESIGN.md 3.1. `observe()` prints each line
indented by two spaces, so a table row is its own line. Join with "\n" to get
the page text. Page order is the order below: `next` and `prev` walk it.

REBUILT FOR THE REDESIGN (REDESIGN.md, QUERIES.md). The first build's hop 2
pages STATED the answer, so "I am on the right page" and "I have the right
answer" were the same event and the terminal reward taught the search nothing.
Every hop 2 page is now a TABLE KEYED BY THE HOP 1 ENTITY. Landing on it is
necessary and not sufficient.

WHAT THIS SITE OWNS (QUERIES.md section 6):

  page 2, Team directory      HOP 1 for Q1 and Q5, and it is the only page in
                              the corpus that carries either bridge fact:
                              "Vega team: Building Nord, floor 2, cost centre
                              K2210." (Q1) and "Field service: Winterthur site,
                              cost centre K5000." (Q5). Two queries read two
                              different rows of one page, which is the cheapest
                              demonstration in the set that finding the bridge
                              page is not finishing the job.
                              It maps teams to locations and cost centres ONLY.
                              No lounge, no clock time, and NO LINE MANAGERS:
                              every person in this corpus is a gold or a decoy
                              somewhere, so a name here would leak.
  page 4, Signature           HOP 2 for Q6, so it is a bare table: five rows,
  levels and signatories      signature level to person, gold "Ana Ferreira" on
                              row three, decoys Elke Rovinsky, Marek Duval, Rui
                              Okonkwo and Petra Lindqvist on the other four.
                              NO AMOUNTS ANYWHERE ON IT. Which level 12000
                              francs needs is stated only on the hop 1 page,
                              policies/Procurement and purchase approvals, so a
                              reader who skips hop 1 faces a genuine one in five
                              choice worth 0.200.
  page 3, Who leads what      THE Q6 TRAP, kept on purpose. It names the same
                              five people by ROLE, with Ana Ferreira as Head of
                              Instruments. A reader who reasons about seniority
                              answers Managing Director or Head of Operations
                              and pays 0.000. Q6 stopped bridging through a role
                              precisely because a role is not semantically empty
                              and a signature level is.

Ana Ferreira is therefore on two pages of this site, 3 and 4. That is the
second knowing exception to "a gold appears on one page only" (the first is
Roswitha Elektronik, QUERIES.md concern 2), and it costs nothing measurable:
page 3 offers five names, so a blind pick there also pays 0.200, exactly what
the hop 2 page itself pays. It lifts nothing. Rule D still holds: page 3 does
not carry the key entity "level C", so the mapping level to person exists on
page 4 alone.

Five of the fifteen people in the corpus live here: Elke Rovinsky, Marek Duval,
Ana Ferreira, Rui Okonkwo, Petra Lindqvist. DO NOT INVENT A SIXTH, and do not
mention any of the other ten (the five account managers in `policies`, the five
on call people in `it`). The fifteen share no name token, which is what makes
naming the wrong person pay exactly 0.000.

WHAT THIS SITE MUST NEVER SAY. The checks at the bottom enforce all of it:

  golds owned elsewhere      "N-310", "Ines Brauer", "Sanna Ilves", "Eiche",
                             "07:20", "2031", "Amber", "Roswitha Elektronik",
                             "October"
  decoys owned elsewhere     the other lounge rooms, times, years, months,
                             colours, queues, suppliers and people
  hop 1 facts owned          "supplied by Talstrom Werke", "archived in
  elsewhere                  Silvretta", "managed in Varda", "laboratory L2-04",
                             "climate chamber", the firmware to group table,
                             "assembles the Kestrel", and any amount in francs
                             against a signature level

NO SYSTEM NAME APPEARS ON THIS SITE. The first build had holiday booked in
Zeitwerk and time recorded in Zeitwerk. Zeitwerk is now a row key on both `it`
tables, and a page that says what it is FOR would let a reader eliminate that
row of a five row table without doing hop 1, lifting the blind guess on Q3 and
Q4 from 0.200 to 0.250. Rule B keeps the five system names opaque, so this site
says "the time recording system" and names nothing.

THE EARNED DISTRACTORS. QUERIES.md lists `people` as a distractor site for Q2,
Q3, Q4, Q6, Q8, Q9 and Q10. The overlap is earned, not planted: this site is
full of the words manager, approve, sign, badge, laboratory access, service
desk, firmware, Vega, Winterthur and of clock times, and not one of its pages
answers any of those seven questions. A greedy reader who comes here for Q2
finds five names next to the word manager and scores 0.000.

Nordhelm Instruments AG is invented. So is every person, team and site here.
"""

SITE_KEY = "people"
SITE_NAME = "People and Teams"
# Pinned in intranet.py SITE_BLURBS and asserted against this string. Do not
# edit either copy alone. QUERIES.md concern 7 also forbids naming the company
# sites individually in a blurb: the side pane must not help pick a table row.
BLURB = "Teams, reporting lines, joining, absence and working hours."

PAGES = [
    # ==================================================================
    # 0. The landing page. goto_site[people] lands here. Both load bearing
    #    pages are one follow away, which is the reachability rule in
    #    QUERIES.md section 6: hop 2 for Q6 sits at index 4 and would
    #    otherwise be four next actions from here.
    # ==================================================================
    {
        "title": "Welcome to People and Teams",
        "body": [
            "Everything about teams, cost centres, joining, time off and working "
            "hours lives here.",
            "New joiners should start with the first week page.",
            "The team directory is the page most people come back to: it maps every "
            "team and group to the building or the site it sits in and to the cost "
            "centre it books to.",
            "Use Who leads what when a rule, a policy or a form names a role rather "
            "than a person.",
            "Signature levels and signatories turns a signature level into the "
            "person who holds it.",
            "This site is maintained by Operations and is reviewed once a year.",
            "Purchasing rules, room bookings, laboratory access and IT accounts are "
            "not held here; each has its own site in the side pane.",
        ],
        "links": [
            {"label": "Team directory", "target": "people/Team directory"},
            {"label": "Signature levels and signatories",
             "target": "people/Signature levels and signatories"},
            {"label": "Who leads what", "target": "people/Who leads what"},
        ],
    },

    # ==================================================================
    # 1. Shape of the company. Names the Embedded Systems division and the
    #    word firmware, and NEVER a product line: the firmware to group
    #    table is it/Source control and firmware repositories, which is
    #    hop 1 for Q9. Names no building, no room and no person either.
    # ==================================================================
    {
        "title": "How we are organised",
        "body": [
            "Three divisions: Instruments, Embedded Systems and Operations.",
            "Quality is a staff function and reports to the Managing Director.",
            "Instruments covers the product lines and the customers who buy them.",
            "Embedded Systems writes firmware and keeps the source repositories; "
            "which group owns which repository is recorded on the IT site.",
            "Operations covers facilities, health and safety, purchasing and the "
            "policy site.",
            "A division is led by a head; a team or a group is led by a line manager.",
            "Where a team sits and which cost centre it books to are in the team "
            "directory, not here.",
            "Reporting lines change with the annual planning round, and the "
            "directory is corrected at the same time.",
        ],
        "links": [],
    },

    # ==================================================================
    # 2. HOP 1 for Q1 (Vega team, Building Nord) and for Q5 (Field
    #    service, Winterthur site). Two actions from page 0 by next, next.
    #    Teams to locations and cost centres only. NO PEOPLE ON THIS PAGE,
    #    no floor of any coffee lounge, no departure time.
    # ==================================================================
    {
        "title": "Team directory",
        "body": [
            "Vega team: Building Nord, floor 2, cost centre K2210.",
            "Orion team: Building Sued, floor 2, cost centre K2240.",
            "Embedded Systems group: Building West, floor 1, cost centre K3100.",
            "Metrology group: Building Nord, floor 0, cost centre K4120.",
            "Field service: Winterthur site, cost centre K5000.",
            "Each entry gives the building or the site a team sits in and the cost "
            "centre it books to, and nothing else.",
            "The cost centre is the code that time recording and purchase orders "
            "are booked against.",
            "Line managers are not listed here; ask inside your team, or use Who "
            "leads what for a division head.",
            "Desk moves are arranged with facilities management, and this page is "
            "corrected afterwards.",
        ],
        "links": [
            {"label": "The Winterthur site", "target": "facilities/The Winterthur site"},
            {"label": "Who leads what", "target": "people/Who leads what"},
        ],
    },

    # ==================================================================
    # 3. THE Q6 TRAP. Role to person, the same five people as page 4 in a
    #    different order and under titles that invite seniority reasoning.
    #    It must never carry a signature level or an amount: with either,
    #    it would answer Q6 and Rule D would break.
    # ==================================================================
    {
        "title": "Who leads what",
        "body": [
            "Managing Director: Elke Rovinsky.",
            "Head of Operations: Marek Duval.",
            "Head of Instruments: Ana Ferreira.",
            "Head of Embedded Systems: Rui Okonkwo.",
            "Head of Quality: Petra Lindqvist.",
            "Policies, rules and forms name the role and not the person, so use "
            "this page to turn a title into a name.",
            "A head runs a division and sets its plan for the year; day to day "
            "questions belong with your line manager.",
            "Deputies stand in while a head is away and are named in the address "
            "book.",
            "Signing authority is set by signature level, not by title; the levels "
            "and the people who hold them are listed on the signature page.",
        ],
        "links": [
            {"label": "Signature levels and signatories",
             "target": "people/Signature levels and signatories"},
        ],
    },

    # ==================================================================
    # 4. HOP 2 for Q6. A bare table: level to person, five rows, and NOT
    #    ONE DIGIT on the page. The amounts that pick the row live only on
    #    policies/Procurement and purchase approvals, so a reader without
    #    hop 1 faces five equal candidates and pays 0.200.
    #    Ana Ferreira is row three, so quoting the top line pays 0.000.
    # ==================================================================
    {
        "title": "Signature levels and signatories",
        "body": [
            "Level A: Elke Rovinsky.",
            "Level B: Marek Duval.",
            "Level C: Ana Ferreira.",
            "Level D: Rui Okonkwo.",
            "Level E: Petra Lindqvist.",
            "Each signature level is held by one person, and the table above is the "
            "whole list.",
            "The procurement policy sets which level is needed, and the thresholds "
            "are not repeated here because they are reviewed far more often than "
            "the signatories change.",
            "Send the document to the signatory the policy points at, not to your "
            "division head.",
            "A signatory who is away is covered by the deputy named in the address "
            "book.",
        ],
        "links": [
            {"label": "Purchase approvals",
             "target": "policies/Procurement and purchase approvals"},
        ],
    },

    # ==================================================================
    # 5. Joining. The Q4 and Q8 near miss: the densest badge, laboratory
    #    access and service desk vocabulary on the site, and not one room
    #    code, access class or queue name anywhere on it.
    # ==================================================================
    {
        "title": "Your first week",
        "body": [
            "Day one: collect your badge at reception, then pick up your laptop "
            "from IT.",
            "Your buddy walks you through the intranet and the time recording tool.",
            "Reception takes the photograph for your badge and issues it while you "
            "wait.",
            "A badge opens the offices you need on day one; laboratory access is "
            "requested separately by your line manager and is granted room by room.",
            "Your line manager sets up the week: a tour of the building, the team "
            "meeting, the cost centre you book time to and the time recording rules.",
            "Ask the buddy for anything that is missing on day one, from a docking "
            "station to a headset; a repair later on is a ticket for the service "
            "desk.",
            "The first week ends with a short review with your line manager.",
        ],
        "links": [
            {"label": "Badges and access", "target": "facilities/Badges and access"},
        ],
    },

    # ==================================================================
    # 6. Absence. Carries the approve and sign off vocabulary for the Q6
    #    near miss and Winterthur for the Q5 and Q10 near miss. No month
    #    is named anywhere: months appear only in the Q10 hop 2 table.
    # ==================================================================
    {
        "title": "Absence and leave",
        "body": [
            "25 days of holiday a year, booked in the time recording system and "
            "approved by your line manager.",
            "Report sickness to your line manager before the start of core hours.",
            "A doctor's note is needed for a longer absence and is sent to your "
            "line manager.",
            "Holiday is approved in the order the requests arrive, and the whole "
            "team's holiday is visible to the team.",
            "Unpaid leave, parental leave and a sabbatical are agreed with your "
            "line manager and confirmed by the head of the division.",
            "Public holidays follow the canton a site is in, so the Winterthur site "
            "and the Zurich Nord campus differ by a few days each year.",
            "Nobody approves their own absence; it always goes to the line manager.",
        ],
        "links": [],
    },

    # ==================================================================
    # 7. Hours. The Q5 near miss (full of clock times, none of them a
    #    departure, and no time here shares a token with 07:20) and the Q3
    #    near miss (it says the on call rota exists and names nobody).
    # ==================================================================
    {
        "title": "Working hours and flexible time",
        "body": [
            "Core hours are 09:00 to 15:00, and hours are recorded daily in the "
            "time recording system.",
            "Overtime is compensated in time off, not in pay.",
            "Outside core hours the working day is yours to arrange with your line "
            "manager, as long as the team is covered.",
            "Working from home is agreed with your line manager and is not open to "
            "laboratory or assembly roles.",
            "Colleagues at the Winterthur site keep the same core hours as the "
            "campus.",
            "Travel between sites during the working day counts as working time; "
            "the timetable and the parking rules are on the facilities site.",
            "Duty outside office hours is not flexible time: it is covered by the "
            "on call rota that IT keeps for each system, and that rota names one "
            "person per system.",
            "Time corrections are approved by your line manager.",
        ],
        "links": [
            {"label": "On call rota", "target": "it/On call rota"},
        ],
    },
]


# ===========================================================================
# Self check. `python3 corpus_people.py` prints the pages and asserts the
# properties this site is responsible for. It is deliberately local: the
# corpus wide checks (link targets resolve, check 6 blind guess, check 9
# Rule D over all 36 pages) belong to corpus_check.py.
# ===========================================================================

import re

TITLES = [
    "Welcome to People and Teams",
    "How we are organised",
    "Team directory",
    "Who leads what",
    "Signature levels and signatories",
    "Your first week",
    "Absence and leave",
    "Working hours and flexible time",
]

HOP2_PAGE = 4          # Signature levels and signatories
Q6_GOLD = "Ana Ferreira"
Q6_DECOYS = ("Elke Rovinsky", "Marek Duval", "Rui Okonkwo", "Petra Lindqvist")

# The five signatories, and the ten people this site must never name.
SIGNATORIES = (Q6_GOLD,) + Q6_DECOYS
FOREIGN_PEOPLE = (
    "Ines Brauer", "Lukas Feher", "Nora Sandu", "Jonas Bittner", "Clara Nyman",
    "Tomas Rask", "Sanna Ilves", "Yuki Oberer", "Dino Ravelli", "Bruno Achterberg",
)

# Strings that must appear on ONE page of this site and nowhere else on it:
# the two bridge facts it owns and the hop 2 row that carries the gold.
REQUIRED_UNIQUE = [
    (2, "Vega team: Building Nord, floor 2, cost centre K2210."),   # Q1 hop 1
    (2, "Field service: Winterthur site, cost centre K5000."),      # Q5 hop 1
    (4, "Level C: Ana Ferreira."),                                  # Q6 gold row
    (3, "Head of Instruments: Ana Ferreira."),                      # the Q6 trap row
]

# Strings that must appear on that page. The four decoys are what makes the
# hop 2 page a table rather than an answer, and the same five names on page 3
# are what makes the seniority trap bite.
REQUIRED_ON = [
    (4, "Level A: Elke Rovinsky."),
    (4, "Level B: Marek Duval."),
    (4, "Level D: Rui Okonkwo."),
    (4, "Level E: Petra Lindqvist."),
    (3, "Managing Director: Elke Rovinsky."),
    (3, "Head of Operations: Marek Duval."),
    (2, "Orion team: Building Sued, floor 2, cost centre K2240."),
    (2, "Embedded Systems group: Building West, floor 1, cost centre K3100."),
    (2, "Metrology group: Building Nord, floor 0, cost centre K4120."),
]

# Strings that must appear NOWHERE on this site, lowercased: the nine golds
# owned by the other four sites, every decoy of every other query, the hop 1
# facts owned elsewhere, and the five opaque system names.
BANNED = [
    # golds owned elsewhere
    "n-310", "ines brauer", "sanna ilves", "eiche", "07:20", "2031", "amber",
    "roswitha elektronik", "october",
    # decoys owned elsewhere
    "s-121", "w-204", "t-018",
    "lukas feher", "nora sandu", "jonas bittner", "clara nyman",
    "tomas rask", "yuki oberer", "dino ravelli", "bruno achterberg",
    "ahorn", "birke", "linde", "ulme",
    "06:45", "13:55", "16:10",
    "2027", "2029", "2026", "2032",
    "blue", "violet", "crimson",
    "talstrom", "aalvik", "brindl", "halden",
    # hop 1 facts owned elsewhere
    "pressure cell", "humidity film", "flow element", "thermistor",
    "climate chamber", "l2-04", "l1-07", "l3-02", "cr-1",
    "vega 3", "orion 2", "kestrel", "tarn 5",
    "badge readers", "door groups", "calibration", "certificate",
    "francs", "shuttle", "coffee lounge", "release calendar",
    # the five systems stay opaque, Rule B
    "aletsch", "silvretta", "napf", "varda", "zeitwerk",
]

# The ten golds of the redesigned query set, for the link label check.
GOLDS = ("N-310", "Ines Brauer", "Sanna Ilves", "Eiche", "07:20", "Ana Ferreira",
         "2031", "Amber", "Roswitha Elektronik", "October")

MONTHS = ("january", "february", "march", "april", "june", "july", "august",
          "september", "october", "november", "december")

# The em dash, the en dash and the prose double hyphen, built with chr() so
# this file itself carries none of them for the repo write hook to trip on.
BAD_DASHES = (chr(0x2014), chr(0x2013), "-" * 2)

# A room code of the shape the lounge table uses would share a token with a
# gold and pay 0.500, so none may exist here. Same for a laboratory code.
ROOM_CODE = re.compile(r"\b[NSWT]-\d", re.IGNORECASE)
LAB_CODE = re.compile(r"\b(L\d-\d|CR-\d)", re.IGNORECASE)
YEAR = re.compile(r"\b(19|20)\d\d\b")
# "level a" through "level e" outside the five table rows would hand a reader
# the key entity of Q6, or worse the mapping, on the wrong page.
LEVEL_KEY = re.compile(r"level [a-e]\b", re.IGNORECASE)


def page_text(page):
    return page["title"] + "\n" + "\n".join(page["body"])


def _check():
    assert [p["title"] for p in PAGES] == TITLES, "page order changed"
    assert len(PAGES) == 8, len(PAGES)

    blob = "\n".join(page_text(p) for p in PAGES)
    low = blob.lower()
    assert blob.isascii(), "non ascii character in the corpus"
    for bad in BAD_DASHES:
        assert bad not in blob, "forbidden dash %r" % bad

    print("== the people site, %d pages ==" % len(PAGES))
    for i, p in enumerate(PAGES):
        n = len(" ".join(p["body"]).split())
        assert 60 <= n <= 140, (i, p["title"], n)
        print("  %d  %-34s %3d words  %2d lines  %d links"
              % (i, p["title"], n, len(p["body"]), len(p["links"])))

    for i, s in REQUIRED_UNIQUE:
        hits = [j for j, p in enumerate(PAGES) if s.lower() in page_text(p).lower()]
        assert hits == [i], "%r wanted on page %d only, found on %s" % (s, i, hits)
    print("  %d strings on their own page and nowhere else" % len(REQUIRED_UNIQUE))

    for i, s in REQUIRED_ON:
        assert s.lower() in page_text(PAGES[i]).lower(), \
            "%r missing from page %d" % (s, i)
    print("  %d strings present where the query set needs them" % len(REQUIRED_ON))

    for s in BANNED:
        hits = [j for j, p in enumerate(PAGES) if s in page_text(p).lower()]
        assert not hits, "%r is owned by another site but appears on %s" % (s, hits)
    print("  %d banned strings, none present" % len(BANNED))

    # REDESIGN.md invariant 5, the half of it this site owns: the hop 2 page is
    # a table. The gold and every decoy are on it, one row each, and the rows
    # are the same shape so the gold is not singled out.
    hop2 = page_text(PAGES[HOP2_PAGE])
    for s in (Q6_GOLD,) + Q6_DECOYS:
        assert s in hop2, "%r missing from the Q6 hop 2 table" % s
    rows = PAGES[HOP2_PAGE]["body"][:5]
    shape = re.compile(r"^Level [A-E]: [A-Z][a-z]+ [A-Z][a-z]+\.$")
    assert all(shape.match(r) for r in rows), rows
    assert rows[2].endswith(Q6_GOLD + "."), "the gold must not be the first row"
    assert not any(ch.isdigit() for ch in hop2), \
        "an amount on the hop 2 page would answer Q6 without hop 1"
    print("  hop 2 page is a bare table: 1 gold, %d decoys, no digits, gold on row 3"
          % len(Q6_DECOYS))

    # The key entity "level C" lives on the hop 2 table alone. Anywhere else it
    # would break Rule D, and "level a" hides easily inside ordinary prose.
    for i, p in enumerate(PAGES):
        found = LEVEL_KEY.findall(page_text(p))
        assert not found or i == HOP2_PAGE, (i, found)
    assert len(LEVEL_KEY.findall(hop2)) == 5, LEVEL_KEY.findall(hop2)

    # No line manager on the team directory: every person in the corpus is a
    # gold or a decoy, so a name there would leak one.
    directory = page_text(PAGES[2])
    for name in SIGNATORIES + FOREIGN_PEOPLE:
        assert name not in directory, "%r on the team directory" % name
    for name in FOREIGN_PEOPLE:
        assert name.lower() not in low, "%r belongs to another site" % name
    for name in SIGNATORIES:
        hits = [j for j, p in enumerate(PAGES) if name in page_text(p)]
        assert hits == [3, HOP2_PAGE], "%r wanted on 3 and %d, found on %s" \
            % (name, HOP2_PAGE, hits)
    print("  the 5 signatories are on pages 3 and 4 only, the other 10 people nowhere")

    # Shapes that would collide with a gold token elsewhere in the corpus.
    assert not ROOM_CODE.search(blob), ROOM_CODE.search(blob).group(0)
    assert not LAB_CODE.search(blob), LAB_CODE.search(blob).group(0)
    assert not YEAR.search(blob), YEAR.search(blob).group(0)
    for m in MONTHS:
        assert m not in low, "the month %r appears only in the Q10 table" % m
    assert "May" not in blob, "the month May"
    print("  no room code, laboratory code, year or month name")

    # The link shape: 9 links out, none to its own page, and both load bearing
    # pages one follow from the landing page (QUERIES.md reachability).
    n_links = 0
    for i, p in enumerate(PAGES):
        for lk in p["links"]:
            n_links += 1
            site, _, title = lk["target"].partition("/")
            assert site and title, lk
            assert not (site == SITE_KEY and title == p["title"]), "self link on %d" % i
            if site == SITE_KEY:
                assert title in TITLES, "dangling internal link %r" % title
    assert n_links == 9, n_links
    landing = [lk["target"] for lk in PAGES[0]["links"]]
    assert "people/Team directory" in landing
    assert "people/Signature levels and signatories" in landing
    print("  %d links out, none to its own page, both hop pages 1 follow from page 0"
          % n_links)

    # No gold answer may hide in a link label: a label is read from a page the
    # agent has not opened, so a gold there would leak off the chrome.
    for p in PAGES:
        for lk in p["links"]:
            for s in GOLDS:
                assert s.lower() not in lk["label"].lower(), (lk, s)
    print("  no gold answer in a link label")
    print("\nall people checks passed")


if __name__ == "__main__":
    _check()

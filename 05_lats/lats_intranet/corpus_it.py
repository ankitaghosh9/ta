"""Corpus for the `it` site, "IT Service Desk", of the toy Nordhelm intranet.

One of five sibling corpus modules. Nordhelm Instruments AG is invented: no real
company, person, supplier or system appears here, and it must stay that way.

Export contract (identical across the five sibling modules):

    PAGES = [
        {"title": str,
         "body":  str,                       # one intranet line per newline
         "links": [{"label": str, "target": "<site_key>/<page title>"}, ...]},
        ...
    ]

Page order is the order the agent walks with next / prev, so it must not be resorted.
`body` is a single string; the builder splits it on newlines into the `Page.body` tuple,
and `observe` indents each line by two spaces. Every load-bearing sentence therefore sits
entirely inside one line, because the uniqueness and leak checks are substring checks
against `title + "\\n" + "\\n".join(body)` and a fact split across a newline would vanish.

The redesign of 2026-08-12
==========================
This site is rewritten against QUERIES.md, which supersedes section 2 of DESIGN.md. The
one structural change, and the reason for the rewrite: a hop 2 page is now a TABLE KEYED
BY THE HOP 1 ENTITY and never states a single answer. Reaching it is necessary and not
sufficient, so "I am on the right page" and "I have the right answer" stop being the same
event, and the terminal reward carries information the navigation heuristic does not.

Both of this site's hop 2 pages are therefore bare key to value maps, and QUERIES.md
Rule A is what they must obey: a table never says what its keys are FOR. The routing
table does not say that Varda runs the doors, and the rota does not say that Silvretta
holds the certificates. Those sentences live on the hop 1 pages, on facilities and on
policies. If either of them migrated onto a table here, the question's own words would
pick the row out and the whole redesign would be undone a second time.

What this site owns, and what it must never say
===============================================
Pages this site is the sole source of:

  it/1  "Support routing by system"                 Q4 hop 2 table, gold "Eiche"
  it/2  "On call rota"                              Q3 hop 2 table, gold "Sanna Ilves"
  it/3  "Source control and firmware repositories"  Q9 hop 1, reveals "Orion 2"

The two tables are keyed by the same five systems in the same order, which is the mirror
trap the site exists for: each answers the other query with the right entity and the
wrong KIND of answer. Q3 wants a person and the routing table offers a queue (0.000);
Q4 wants a queue and the rota offers Dino Ravelli (0.000). Neither page may ever carry
both halves, and no page outside it/1 may name a queue at all.

Strings that must NOT appear anywhere on this site, because another page owns them:

  N-310, 07:20, Ines Brauer, Ana Ferreira, 2031, Amber, Roswitha Elektronik,
  October                                                golds owned elsewhere
  every decoy of those golds, in particular every other room code, shuttle time,
  account manager, signatory, contract year, access class and release month
  "archived in Silvretta", "managed in Varda"            hop 1 facts owned elsewhere

Note the shape of the last two. This site names Silvretta and Varda constantly and that
is the point: it is the SENTENCE SAYING WHAT THEY ARE FOR that lives elsewhere, so no
page here carries a hop 1 fact and its own gold together and every query stays two hop.

Three token classes are banned outright rather than merely policed, because one careless
sentence would move a pinned number:

  No months anywhere.       Q10's gold is a month and months appear nowhere else.
  No years anywhere.        Q7's gold and all four of its decoys are years.
  No room codes, no colours, no clock time sharing a field with 07:20, 06:45,
  13:55 or 16:10. The desk opens at 08:00, which shares no token with any of them.

No new people are introduced. The corpus has exactly fifteen, no two of whom share a name
token, which is what makes naming the wrong person pay exactly 0.000 rather than leaking
partial credit. This site names five of them, all on it/2, and refers to roles everywhere
else ("your line manager", "the duty manager", "the maintaining team").

Earned distractors this site is required to carry
=================================================
`it` is listed as a distractor site for Q2, Q6, Q7 and Q10. All four are near misses of
vocabulary and never of content, and none of them holds an answer:

  Q2   ("account manager for the company that supplies ...") it/4 is titled Accounts and
       passwords and is the highest lexical match in the corpus for "account"; it/2 is
       full of people. Neither carries a supplier or an account manager.
  Q6   ("who signs off a purchase of 12000 francs") it/5 says a non standard laptop needs
       the signature the purchase policy asks for, and that the desk never signs one off.
       It names no person, no signature level and no amount.
  Q7   ("until which year does the framework contract run") it/6 talks about framework
       contracts, suppliers and renewals, and says in so many words that the desk does
       not hold the renewal dates. There is no year on this site.
  Q10  ("in which month is the firmware released") it/3 is the obvious destination for any
       question carrying the word firmware, it names the product lines, and it carries no
       month. Q9 and Q10 are each other's best trap and this page is one half of it.
"""

SITE_KEY = "it"
SITE_NAME = "IT Service Desk"
SITE_BLURB = "Laptops, accounts, network, printing, software and the on call rota."

PAGES = [

    # ==== 0. Contacting the service desk ====================================
    # The landing page. Q4's earned near miss: it discusses queues at length,
    # names none, and offers a phone extension where a queue was asked for.
    # Its three links put both tables and the Q9 bridge page within one action
    # of here, which is the reachability rule in QUERIES.md section 6.
    {
        "title": "Contacting the service desk",
        "body": "\n".join([
            "The service desk is the single point of contact for hardware, accounts, network and software.",
            "The desk is open 08:00 to 17:00 and the internal phone extension is 4000.",
            "Tickets can also be raised in the self service portal, which is faster for anything that is not stopping your work.",
            "Every ticket goes to a queue, and the queue depends on the system you were using.",
            "Name the system in the ticket, because a ticket that names no system is passed back for clarification.",
            "Outside office hours the on call rota applies, and the pager is carried by system rather than by queue.",
            "Engineering source control has its own page, and access to a repository is requested by your line manager.",
            "Hardware handovers and repairs are dealt with at the walk-in counter next to reception.",
        ]),
        "links": [
            {"label": "Support routing by system", "target": "it/Support routing by system"},
            {"label": "On call rota", "target": "it/On call rota"},
            {"label": "Source control and firmware repositories",
             "target": "it/Source control and firmware repositories"},
        ],
    },

    # ==== 1. Support routing by system ======================================
    # Q4 hop 2. Five rows, system to queue, and NOTHING about what a system
    # does: that is Rule A, and it is what forces the reader to have Varda from
    # facilities before the table means anything. Varda is the fourth row.
    # The queue names are single pairwise disjoint tokens, so a wrong row pays
    # 0.000 rather than the 0.500 the old SD- prefix paid for naming any queue.
    {
        "title": "Support routing by system",
        "body": "\n".join([
            "This table decides where a fault report goes, so quote the system name and nothing else.",
            "What each system is for is documented by the team that owns it, not here.",
            "Aletsch: queue Ahorn.",
            "Silvretta: queue Birke.",
            "Napf: queue Linde.",
            "Varda: queue Eiche.",
            "Zeitwerk: queue Ulme.",
            "A report sent to the wrong queue is moved by hand, which costs a working day.",
            "The queues share one duty roster over the summer, so a slow reply is normal then.",
            "Escalation runs through the queue owner and never through contacting an engineer directly.",
        ]),
        "links": [
            {"label": "On call rota", "target": "it/On call rota"},
        ],
    },

    # ==== 2. On call rota ===================================================
    # Q3 hop 2. Five rows, system to person, and again no descriptions: if this
    # page read "Silvretta, the certificate archive: Sanna Ilves", the words of
    # the question would pick the row and hop 1 would be dead weight.
    # No queue name may appear here; Q4's gold belongs to it/1 and stays unique
    # to it. This page is also Q4's mirror trap, offering Dino Ravelli.
    {
        "title": "On call rota",
        "body": "\n".join([
            "Primary on call contact, by system, for the hours when the service desk is closed.",
            "The rota is reviewed every quarter and covers nights, weekends and public holidays.",
            "Aletsch: Tomas Rask.",
            "Silvretta: Sanna Ilves.",
            "Napf: Yuki Oberer.",
            "Varda: Dino Ravelli.",
            "Zeitwerk: Bruno Achterberg.",
            "Call the service desk number first, because the on call engineer is paged only after the call is logged.",
            "Anything still unanswered after 30 minutes escalates to the duty manager.",
            "Use the rota for a system that is down for everyone, not for a single laptop or a forgotten password.",
        ]),
        "links": [
            {"label": "Contacting the service desk", "target": "it/Contacting the service desk"},
        ],
    },

    # ==== 3. Source control and firmware repositories =======================
    # Q9 hop 1: it maps each product line to the group that maintains its
    # firmware, and the reader wants that map backwards, from the Embedded
    # Systems group to the Orion 2. No supplier is named here, so the query
    # stays two hop. No month is named here either, which is what makes the
    # page Q10's trap: the word firmware points at it and it cannot answer.
    {
        "title": "Source control and firmware repositories",
        "body": "\n".join([
            "Every product line keeps its firmware in its own repository, and the maintaining team owns the branch policy.",
            "Vega 3 firmware: maintained by the Vega team, repository vega3-fw.",
            "Orion 2 firmware: maintained by the Embedded Systems group, repository orion2-fw.",
            "Kestrel firmware: maintained by the Metrology group, repository kestrel-fw.",
            "Tarn 5 firmware: maintained by the Field service team, repository tarn5-fw.",
            "Read access is granted to any engineer on request, and write access follows the maintaining team.",
            "Changes are reviewed by a second engineer before they are merged, whichever repository they touch.",
            "Repository names carry no version and no date, so use the release calendar in product engineering for timing.",
        ]),
        "links": [
            {"label": "Team directory", "target": "people/Team directory"},
        ],
    },

    # ==== 4. Accounts and passwords =========================================
    # Q2's earned distractor. The question asks for an "account manager" and
    # this is the page in the corpus that matches both words hardest, while
    # holding neither a supplier nor a person. The word manager appears here
    # only as a role, which pays 0.000 the same way "Head of Operations" did.
    {
        "title": "Accounts and passwords",
        "body": "\n".join([
            "Every employee gets one account, and that account carries your mail, your files and your access to the systems.",
            "Your line manager requests an account for a new joiner two weeks before the start date.",
            "Passwords are changed once a year and never shared, not even with the service desk.",
            "A badge is not an account, and door access is requested separately through facilities.",
            "Accounts for external contractors expire on the end date in the contract and are not extended by the desk.",
            "An account that has not been used for 90 days is disabled, and reinstating it needs an approval from your line manager.",
        ]),
        "links": [
            {"label": "Badges and access", "target": "facilities/Badges and access"},
        ],
    },

    # ==== 5. Laptops and mobile phones ======================================
    # Q6's earned distractor: purchases, signatures and sign off, with no
    # person, no signature level and no amount in francs anywhere on the page.
    # The walk-in counter carries no room code any more; room codes are Q1's
    # answer shape and the corpus holds only the lounges and the laboratories.
    {
        "title": "Laptops and mobile phones",
        "body": "\n".join([
            "The standard laptop is replaced every four years, and the replacement is triggered from the asset register.",
            "Two models are offered, a light portable and a heavier workstation for engineering software.",
            "A laptop outside the standard list is a purchase like any other and needs the signature the purchase policy asks for.",
            "The service desk cannot approve a purchase and never signs one off.",
            "Mobile phones sit on a separate contract, and a replacement handset is ordered by your line manager.",
            "For a repair, bring the device and its power supply to the walk-in counter, and expect to leave it overnight.",
        ]),
        "links": [
            {"label": "Procurement and purchase approvals",
             "target": "policies/Procurement and purchase approvals"},
        ],
    },

    # ==== 6. Software licences and renewals =================================
    # Q7's earned distractor: framework contracts, suppliers and renewal dates,
    # in the vocabulary of the question and with no year on the page. It says
    # plainly that the dates are held by procurement, which is honest and still
    # leaves the reader two hops away from a contract expiry.
    {
        "title": "Software licences and renewals",
        "body": "\n".join([
            "Software is licensed centrally, and a licence is assigned to a person rather than to a machine.",
            "A request for a licence is approved by your line manager and then raised with the supplier.",
            "Framework contracts with the software vendors are held by procurement, and the desk does not hold the renewal dates.",
            "A licence that is no longer used is returned at the next renewal, which keeps the count honest.",
            "Unlicensed software must not hold company data, and anything outside the catalogue is unsupported.",
            "Ask procurement before you promise a supplier anything in writing.",
        ]),
        "links": [
            {"label": "Approved suppliers", "target": "policies/Approved suppliers"},
        ],
    },

    # ==== 7. Network, wifi and printing =====================================
    # Filler, and the site's second badge reader near miss: a reader that does
    # not respond, on a printer rather than on a laboratory door, on a page
    # that names no system and no queue.
    {
        "title": "Network, wifi and printing",
        "body": "\n".join([
            "The VPN client is installed on every managed laptop, and the sign in is confirmed on your phone once a working day.",
            "Personal devices do not receive VPN access.",
            "The wired network in the offices carries managed devices only, and a dark socket has usually been switched off at the patch panel.",
            "Guest wifi vouchers are issued at reception and last one working day.",
            "Printers stand on every floor and jobs are released with your badge, and anything not released within a day is deleted.",
            "If the reader on a printer does not respond, release the job with your account and password on the keypad instead.",
        ]),
        "links": [],
    },
]

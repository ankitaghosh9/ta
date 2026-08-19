"""intranet.py, the toy company intranet the LATS exercises search over.

Nordhelm Instruments AG is invented: no real company, person, supplier or system
appears anywhere in it. The agent is dropped at the portal with a question, may take
12 actions, and is scored by the token F1 of the one answer it submits.

    import intranet
    env = intranet.IntranetEnv()
    print(env.reset(0))                       # query 1, at the portal
    obs, reward, done, info = env.step("goto_site[people]")

Standard library only, so it runs free and offline in Colab with no API key.

WHAT THIS FILE IS
=================
The whole environment, in two layers.

  * A PURE ENGINE of module level functions: `initial_state`, `observe`,
    `legal_actions`, `parse_action`, `transition`, `token_f1`. `transition` never
    mutates its input and never looks at a clock or a random number, so the same
    (state, action) always gives the same result.
  * `IntranetEnv`, a thin stateful wrapper. `step` is one call into `transition`.

The split is what makes the tree search legal. A LATS node stores `env.get_state()`
and nothing else, re-visiting a node is `env.load_state(node.state)`, and neither
copies the corpus, which is immutable and shared. Browsing is read only: there is
nothing to undo, so restoring a state really does restore the situation.

THE CORPUS lives in five sibling modules, `corpus_people.py`, `corpus_facilities.py`,
`corpus_it.py`, `corpus_products.py`, `corpus_policies.py`, and is assembled here.
Those five files are the single source of the page text; nothing is duplicated in
this file. On Colab they have to sit beside this module (write them out with
`%%writefile corpus_people.py` and friends before importing this one).

The two shapes the five modules are allowed to use are both accepted:
`body` may be a list of display lines or one string with a newline between lines,
and a link target is always the string `"<site_key>/<page title>"`.

THE QUERY SET is ten two hop bridges, and the shape of hop 2 is the one thing about
it that must never be relaxed. A HOP 2 PAGE IS A TABLE KEYED BY THE ENTITY HOP 1
REVEALS, never a page that states a single answer. "Coffee lounges by building"
lists four buildings and four room codes; only the team directory says which
building the Vega team sits in. So landing on the answer page is necessary and NOT
sufficient, and the two signals a search runs on come apart: the navigation
heuristic can see perfectly well that this is the right page and still be wrong
about the answer. That gap is why the terminal reward carries information the
heuristic does not already have, which is the whole point of the exercise. Every
query therefore carries `key_entity` (what hop 1 reveals, which the question names
only indirectly) and `decoy_answers` (the other rows of the table, at least three,
each a real answer to a slightly different question). A reader who reaches the hop 2
page without doing hop 1 is choosing among `(answer,) + decoy_answers` and scores
about `1 / (1 + len(decoy_answers))`, which selfcheck.py measures.

THE STATE is nine JSON serializable keys and no object references, so two equal
states are the same situation and a search can use the state as a transposition
key. There is deliberately NO rendered observation in it: `observe(state)` derives
the whole text from those nine fields. Do not add one.

THE RULES four separate implementations have to agree on, all from DESIGN.md:

  * page indices are 0 based IN CODE and 1 based IN EVERYTHING THE AGENT READS
    ("Page 3 of 7", `follow[1]` opens `links[0]`);
  * an ILLEGAL ACTION COSTS A STEP. This is a knowing divergence from the sibling
    MiniWebShop environment, where illegal actions are free. Free illegal actions
    would let a policy propose an unbounded number of non advancing children and a
    simulation would never reach a terminal state. Here every action moves the
    episode toward its end, so every trajectory terminates within MAX_STEPS, which
    is what makes the simulation operation well defined;
  * `answer[...]` is never enumerated by `legal_actions`, because its payload is
    free text. That is the one place the branching factor is infinite, and it is
    exactly what the policy language model is for;
  * `goto_site` to the current site is accepted by `step` and not enumerated;
  * `next` on the last page is illegal rather than wrapping, so the page order is a
    line and not a cycle;
  * stepping a finished episode returns `(obs, 0.0, True, info)` with `steps`
    unchanged. It must never raise: a rollout that overruns cannot be allowed to
    crash a participant's loop.

REWARD is token F1 in [0,1], paid only by `answer[...]`, 0.0 otherwise and 0.0 on
truncation. It splits on non alphanumerics rather than deleting punctuation in
place, which is a deliberate departure from the SQuAD metric: it keeps "N-310" as
["n", "310"], so "room N-310" earns 0.800 instead of 0.000 and the value function
has a gradient to steer along. Do not "fix" it back to SQuAD. Note what partial
credit does and does not buy here: it rewards loose phrasing of the RIGHT row
("queue Eiche" 0.667, "at 07:20" 0.800) and never a wrong one, because no gold
shares a token with any decoy in its own table. Carelessness scores zero.

TRUNCATION at MAX_STEPS ends the episode at reward 0.0 with `truncated` True. That
is this environment's version of the paper's depth limit L (HotpotQA 7, WebShop 15).
The paper does not say what happens to a trajectory that exhausts L; this is an
implementation choice and the notebook should say so.

To change the budget, set `intranet.MAX_STEPS`. `transition` and `observe` read the
module global at call time, so everything follows, including the "of 12" the agent
reads. Every number pinned in NUMBERS.md assumes 12.

Run it:  python3 intranet.py       (a short demo)
Check it: python3 selfcheck.py     (the seven invariants, with a table each)
"""
import copy
import importlib
import re
from collections import Counter, namedtuple

# ===========================================================================
# Data. Everything is an immutable namedtuple, and the corpus is never copied.
# ===========================================================================

Link = namedtuple("Link", "label site page")     # target site key, 0 based page index
Page = namedtuple("Page", "title body links")    # body: tuple[str, ...]
Site = namedtuple("Site", "key name blurb pages")

# hop1, hop2: (site_key, 0 based page index) pairs. distractors: site keys that look
# right and are not. key_entity: what hop 1 reveals, which the question may name only
# indirectly. decoy_answers: the other rows of the hop 2 table, at least three, each a
# real answer to a slightly different question.
Query = namedtuple(
    "Query", "qid question answer hop1 hop2 distractors key_entity decoy_answers")

# The side pane order. It is also the order `legal_actions` enumerates goto_site in,
# and the mock policy and every checker depend on that order.
SITE_KEYS = ("people", "facilities", "it", "products", "policies")

SITE_NAMES = {
    "people": "People and Teams",
    "facilities": "Facilities and Buildings",
    "it": "IT Service Desk",
    "products": "Product Engineering",
    "policies": "Policies and Compliance",
}

SITE_BLURBS = {
    "people": "Teams, reporting lines, joining, absence and working hours.",
    "facilities": "Buildings, floors, laboratories, badges, parking and the shuttle.",
    "it": "Laptops, accounts, network, printing, software and the on call rota.",
    "products": "Product lines, datasheets, firmware, calibration and test rigs.",
    "policies": "Purchasing, travel and expenses, suppliers, data protection and incidents.",
}

MAX_STEPS = 12

VERBS = ("goto_site", "next", "prev", "follow", "answer")


# ===========================================================================
# Loading the corpus from the five corpus_<key>.py modules
# ===========================================================================

def _body_lines(raw):
    """A page body as a tuple of display lines, from either shape a module may use."""
    lines = raw.splitlines() if isinstance(raw, str) else list(raw)
    for line in lines:
        assert line and line.strip() == line, "a body line is blank or padded: %r" % line
    return tuple(lines)


def _load_corpus():
    """Import corpus_<key> for every site key and assemble the site tree.

    Two passes, because a link names its target by title and may point at a site
    that has not been built yet: collect the titles first, then resolve.
    """
    modules, raw_pages, titles = {}, {}, {}
    for key in SITE_KEYS:
        name = "corpus_" + key
        try:
            modules[key] = importlib.import_module(name)
        except ImportError:
            raise ImportError(
                "intranet.py needs %s.py beside it. The five corpus modules are %s."
                % (name, ", ".join("corpus_" + k + ".py" for k in SITE_KEYS)))

    for key in SITE_KEYS:
        mod = modules[key]
        raw_pages[key] = list(mod.PAGES)
        titles[key] = [p["title"] for p in raw_pages[key]]
        assert len(set(titles[key])) == len(titles[key]), \
            "two pages of %s share a title" % key
        # The modules are allowed to omit these, and two of them do. Where one is
        # present it must agree with the table above, so neither copy can drift.
        for attr, expected in (("SITE_KEY", key),
                               ("SITE_NAME", SITE_NAMES[key]),
                               ("NAME", SITE_NAMES[key]),
                               ("BLURB", SITE_BLURBS[key]),
                               ("SITE_BLURB", SITE_BLURBS[key])):
            got = getattr(mod, attr, None)
            assert got is None or got == expected, \
                "corpus_%s.%s is %r, this module says %r" % (key, attr, got, expected)

    sites = {}
    for key in SITE_KEYS:
        pages = []
        for i, raw in enumerate(raw_pages[key]):
            links = []
            for link in raw["links"]:
                target_site, _, target_title = link["target"].partition("/")
                assert target_site in SITE_KEYS, \
                    "%s/%d links to the unknown site %r" % (key, i, target_site)
                assert target_title in titles[target_site], \
                    "%s/%d links to %r, which is not a page of %s" \
                    % (key, i, target_title, target_site)
                target_page = titles[target_site].index(target_title)
                assert not (target_site == key and target_page == i), \
                    "%s/%d links to itself" % (key, i)
                links.append(Link(link["label"], target_site, target_page))
            pages.append(Page(raw["title"], _body_lines(raw["body"]), tuple(links)))
        sites[key] = Site(key, SITE_NAMES[key], SITE_BLURBS[key], tuple(pages))
    return sites


SITES = _load_corpus()


def page_at(site_key, page_index):
    """The Page at a (site key, 0 based index) pair."""
    return SITES[site_key].pages[page_index]


def page_index(site_key, title):
    """The 0 based index of a page, by title. Used to write the query set by name."""
    for i, page in enumerate(SITES[site_key].pages):
        if page.title == title:
            return i
    raise KeyError("%s has no page titled %r" % (site_key, title))


def all_pages():
    """Every (site key, page index) pair, in side pane order."""
    return [(key, i) for key in SITE_KEYS for i in range(len(SITES[key].pages))]


def page_text(site_key, index):
    """Title plus body, the string every corpus check searches."""
    page = page_at(site_key, index)
    return page.title + "\n" + "\n".join(page.body)


# ===========================================================================
# The query set. Ten queries, every one a two hop bridge: the question names an
# entity, the hop 1 page names a second entity, and only that second entity picks
# out the ROW of the hop 2 table that holds the answer. Pages are named by title
# here and resolved to indices, so re-ordering a corpus module cannot silently point
# a hop somewhere else.
#
# Read one query and the shape of all ten is clear. Q1 asks for the coffee lounge of
# "the building where the Vega team sits". The team directory (hop 1) says Building
# Nord and carries no room code; the lounge table (hop 2) maps four buildings to four
# room codes and carries no team. Neither page answers the question, and a reader who
# reaches the table without the directory picks one row in four.
#
# Three pairings are load bearing and must survive any later edit:
#   * Q1 and Q5 share a hop 1 page and read different rows of it, so finding the
#     bridge page is not finishing the job;
#   * Q3 and Q4 both bridge to a system name and both land in `it`, and they need
#     different tables there, so landing in the right site is not enough either;
#   * products / "Sensing elements and suppliers" is hop 1 for Q2 and Q7 and hop 2
#     for Q9. The same page is a stepping stone in one query and the destination in
#     another, which is the cleanest demonstration in the set that a page has no
#     intrinsic value: V(s) can only ever be a guess about the question in front of it.
# ===========================================================================

def _at(site_key, title):
    return (site_key, page_index(site_key, title))


QUERIES = (
    Query(1,
          "In which room is the coffee lounge of the building where the Vega team sits?",
          "N-310",
          _at("people", "Team directory"),
          _at("facilities", "Coffee lounges by building"),
          ("products", "policies"),
          key_entity="Building Nord",
          decoy_answers=("S-121", "W-204", "T-018")),
    Query(2,
          "Who is the account manager for the company that supplies the pressure cell in the Vega 3?",
          "Ines Brauer",
          _at("products", "Sensing elements and suppliers"),
          _at("policies", "Approved suppliers"),
          ("people", "it"),
          key_entity="Talstrom Werke",
          decoy_answers=("Lukas Feher", "Nora Sandu", "Jonas Bittner", "Clara Nyman")),
    Query(3,
          "Who is the primary on call contact for the system in which the signed calibration certificates are archived?",
          "Sanna Ilves",
          _at("policies", "Calibration and measurement records"),
          _at("it", "On call rota"),
          ("products", "people"),
          key_entity="Silvretta",
          decoy_answers=("Tomas Rask", "Yuki Oberer", "Dino Ravelli", "Bruno Achterberg")),
    Query(4,
          "Which support queue takes a fault report about the system that manages the badge readers and door groups?",
          "Eiche",
          _at("facilities", "Badges and access"),
          _at("it", "Support routing by system"),
          ("people", "policies"),
          key_entity="Varda",
          decoy_answers=("Ahorn", "Birke", "Linde", "Ulme")),
    Query(5,
          "At what time does the shuttle leave for the site where the field service team is based?",
          "07:20",
          _at("people", "Team directory"),
          _at("facilities", "Shuttle timetable"),
          ("products", "policies"),
          key_entity="Winterthur site",
          decoy_answers=("06:45", "13:55", "16:10")),
    Query(6,
          "Who has to sign off a purchase of 12000 francs?",
          "Ana Ferreira",
          _at("policies", "Procurement and purchase approvals"),
          _at("people", "Signature levels and signatories"),
          ("people", "it"),
          key_entity="level C",
          decoy_answers=("Elke Rovinsky", "Marek Duval", "Rui Okonkwo", "Petra Lindqvist")),
    Query(7,
          "Until which year does the framework contract run with the company that supplies the sensing film in the humidity probes?",
          "2031",
          _at("products", "Sensing elements and suppliers"),
          _at("policies", "Framework contracts"),
          ("people", "it"),
          key_entity="Aalvik Components",
          decoy_answers=("2027", "2029", "2026", "2032")),
    Query(8,
          "Which access class is needed for the room where the environmental tests for the Vega 3 run?",
          "Amber",
          _at("products", "Test rigs and environmental testing"),
          _at("facilities", "Access classes by laboratory"),
          ("policies", "people"),
          key_entity="L2-04",
          decoy_answers=("Blue", "Violet", "Crimson")),
    Query(9,
          "Which company supplies the sensing element of the product line whose firmware the Embedded Systems group maintains?",
          "Roswitha Elektronik",
          _at("it", "Source control and firmware repositories"),
          _at("products", "Sensing elements and suppliers"),
          ("policies", "people"),
          key_entity="Orion 2",
          decoy_answers=("Talstrom Werke", "Aalvik Components", "Brindl Metall")),
    Query(10,
          "In which month is the firmware for the product line that is assembled at the Winterthur site released?",
          "October",
          _at("facilities", "The Winterthur site"),
          _at("products", "Firmware release calendar"),
          ("it", "people"),
          key_entity="Kestrel",
          decoy_answers=("March", "June", "December")),
)


# ===========================================================================
# The reward. Token F1 in [0,1], paid only by answer[...].
# ===========================================================================

ARTICLES = {"a", "an", "the"}


def normalize_tokens(text):
    """Lowercase, split on any run of non alphanumeric characters, drop articles."""
    if text is None:
        return []
    return [t for t in re.split(r"[^a-z0-9]+", text.lower()) if t and t not in ARTICLES]


def token_f1(pred, gold):
    """F1 over the multiset of tokens. 1.0 for the gold, 0.0 for a miss, and a real
    number in between for a near miss, which is what gives V(s) something to steer
    toward."""
    p, g = normalize_tokens(pred), normalize_tokens(gold)
    if not p or not g:
        return float(p == g)
    common = sum((Counter(p) & Counter(g)).values())
    if common == 0:
        return 0.0
    prec, rec = common / len(p), common / len(g)
    return 2 * prec * rec / (prec + rec)


# ===========================================================================
# The pure engine
# ===========================================================================

def initial_state(query_idx):
    """The portal: no page open, no steps taken, nothing read."""
    if not 0 <= query_idx < len(QUERIES):
        raise IndexError("there are %d queries, so %r is not one of them"
                         % (len(QUERIES), query_idx))
    return {"query_idx": int(query_idx),
            "site": None,
            "page": None,
            "steps": 0,
            "done": False,
            "answer": None,
            "reward": 0.0,
            "trail": [],
            "note": ""}


def observe(state):
    """Everything the agent may see, and nothing else.

    The question, the budget, the side pane (site keys and blurbs only, never a
    page title), why the last action failed if it did, the current page with its
    body and its numbered links, and the pages read so far. A page's links are
    visible ONLY while standing on that page, which is what makes the task a search
    rather than a lookup.
    """
    query = QUERIES[state["query_idx"]]
    out = ["Question: " + query.question,
           "Steps used: %d of %d" % (state["steps"], MAX_STEPS),
           "",
           "Sites in the side pane:"]
    width = max(len(key) for key in SITE_KEYS)
    for key in SITE_KEYS:
        site = SITES[key]
        out.append("  %-*s  %s  (%d pages)" % (width, key, site.blurb, len(site.pages)))
    out.append("")
    if state["note"]:
        out.append("That did not work: " + state["note"])
        out.append("")
    if state["site"] is None:
        out.append("You are at the intranet home. No page is open.")
        out.append("Open a site with goto_site[name].")
    else:
        site = SITES[state["site"]]
        page = site.pages[state["page"]]
        out.append("Page %d of %d in %s"
                   % (state["page"] + 1, len(site.pages), site.key))
        out.append("Title: " + page.title)
        for line in page.body:
            out.append("  " + line)
        out.append("")
        if page.links:
            out.append("Links on this page:")
            for j, link in enumerate(page.links, start=1):
                out.append("  [%d] %s  (%s)" % (j, link.label, link.site))
        else:
            out.append("Links on this page: none")
    out.append("")
    if state["trail"]:
        read = ", ".join("%s/%s" % (key, page_at(key, int(i)).title)
                         for key, i in (entry.split("/") for entry in state["trail"]))
        out.append("Pages read so far: " + read)
    else:
        out.append("Pages read so far: none")
    return "\n".join(out)


def legal_actions(state):
    """Every enumerable action, in a fixed order: goto_site in side pane order
    excluding the current site, then prev, then next, then follow[1] upward.

    NEVER includes answer[...], whose payload is free text. A finished episode has
    no actions at all.
    """
    if state["done"]:
        return []
    actions = ["goto_site[%s]" % key for key in SITE_KEYS if key != state["site"]]
    if state["site"] is not None:
        pages = SITES[state["site"]].pages
        if state["page"] > 0:
            actions.append("prev")
        if state["page"] < len(pages) - 1:
            actions.append("next")
        for j in range(1, len(pages[state["page"]].links) + 1):
            actions.append("follow[%d]" % j)
    return actions


_ACTION_RE = re.compile(r"^([a-z_]+)\[(.*)\]$", re.DOTALL)


def parse_action(action):
    """"verb[payload]" -> ("verb", "payload"), "next"/"prev" -> ("next", ""), and
    anything else -> (None, the string as given). Grammar only: whether the verb is
    one of the five, and whether the payload makes sense here, is transition's job.
    """
    text = action.strip() if isinstance(action, str) else str(action)
    if text in ("next", "prev"):
        return text, ""
    match = _ACTION_RE.match(text)
    if match:
        return match.group(1), match.group(2)
    return None, action


def _info(parsed, illegal, reason, steps, truncated, answer):
    """The info dict. The gold answer is NEVER in it: a search that could read the
    answer there would not be a search."""
    return {"action": parsed, "illegal": illegal, "reason": reason,
            "steps": steps, "truncated": truncated, "answer": answer}


def _open(state, site_key, index):
    """Move to a page, and record it if this is the first time it is opened."""
    state["site"] = site_key
    state["page"] = index
    entry = "%s/%d" % (site_key, index)
    if entry not in state["trail"]:
        state["trail"].append(entry)


def transition(state, action):
    """(next_state, observation, reward, done, info).

    PURE. `state` is not mutated, nothing random is consulted, so the same
    (state, action) always yields the same result. That is the property the tree
    search rests on.

    The order of operations is fixed, because getting it wrong changes the
    truncation semantics: a finished episode returns unchanged; otherwise the state
    is copied and the note cleared; a malformed action costs a step and sets the
    note; a legal action is applied and costs a step; only then, if the episode is
    still running and the budget is gone, it is truncated at reward 0.0. So an
    answer played as the twelfth action scores normally.
    """
    parsed = parse_action(action)
    verb, payload = parsed

    if state["done"]:
        return (copy.deepcopy(state), observe(state), 0.0, True,
                _info(parsed, True, "the episode is over", state["steps"], False,
                      state["answer"]))

    nxt = copy.deepcopy(state)
    nxt["note"] = ""
    reason = ""

    if verb not in VERBS:
        reason = ("%r is not an action I understand. Use goto_site[name], next, "
                  "prev, follow[i] or answer[text]." % (action,))
    elif verb == "goto_site":
        name = payload.strip()
        if name not in SITE_KEYS:
            reason = ("there is no site called %r. The side pane lists %s."
                      % (name, ", ".join(SITE_KEYS)))
        else:
            _open(nxt, name, 0)
    elif verb in ("next", "prev"):
        if nxt["site"] is None:
            reason = ("no page is open yet, so there is nothing to page through. "
                      "Open a site with goto_site[name].")
        else:
            pages = SITES[nxt["site"]].pages
            step = 1 if verb == "next" else -1
            target = nxt["page"] + step
            if not 0 <= target < len(pages):
                reason = ("there is no page %s this one in %s, and the pages do not "
                          "wrap around."
                          % ("after" if verb == "next" else "before", nxt["site"]))
            else:
                _open(nxt, nxt["site"], target)
    elif verb == "follow":
        if nxt["site"] is None:
            reason = "no page is open yet, so there are no links to follow."
        else:
            links = SITES[nxt["site"]].pages[nxt["page"]].links
            try:
                i = int(payload.strip())
            except ValueError:
                reason = "follow needs a link number, as in follow[1]."
            else:
                if not links:
                    reason = "this page has no links."
                elif not 1 <= i <= len(links):
                    reason = ("this page has %d link%s, so follow[%d] does not exist."
                              % (len(links), "" if len(links) == 1 else "s", i))
                else:
                    link = links[i - 1]
                    _open(nxt, link.site, link.page)
    else:                                   # answer[...], the one terminal action
        nxt["answer"] = payload
        nxt["reward"] = token_f1(payload, QUERIES[nxt["query_idx"]].answer)
        nxt["done"] = True

    nxt["note"] = reason
    nxt["steps"] += 1

    truncated = False
    if not nxt["done"] and nxt["steps"] >= MAX_STEPS:
        nxt["done"] = True
        truncated = True                    # reward stays 0.0: the budget ran out

    info = _info(parsed, bool(reason), reason, nxt["steps"], truncated, nxt["answer"])
    return nxt, observe(nxt), nxt["reward"], nxt["done"], info


# ===========================================================================
# The class. Two lines per method, which is the point of the split above.
# ===========================================================================

class IntranetEnv:
    """A stateful browser over the intranet.

    `sites`, `queries` and `max_steps` are in the signature because DESIGN.md pins
    them and because naming them at the call site says what an environment is made
    of. They cannot actually differ from the module's own: the engine functions are
    module level and read the module corpus, so a different corpus means editing the
    corpus modules, and a different budget means setting `intranet.MAX_STEPS`. Both
    are checked here rather than silently ignored.
    """

    def __init__(self, sites=None, queries=None, max_steps=None):
        if sites is not None and sites is not SITES:
            raise ValueError("the engine reads the module corpus; edit the "
                             "corpus_<site>.py files rather than passing one in")
        if queries is not None and queries is not QUERIES:
            raise ValueError("the engine reads the module query set; edit QUERIES "
                             "rather than passing one in")
        if max_steps is not None and max_steps != MAX_STEPS:
            raise ValueError("set intranet.MAX_STEPS to change the budget; "
                             "observe() and transition() read it at call time")
        self.sites = SITES
        self.queries = QUERIES
        self.max_steps = MAX_STEPS
        self._state = None

    def reset(self, query_idx):
        """Start query `query_idx` (0 based) at the portal. Returns the first
        observation."""
        self._state = initial_state(query_idx)
        return observe(self._state)

    def step(self, action):
        """(observation, reward, done, info), the gym classic four tuple."""
        self._state, obs, reward, done, info = transition(self._require(), action)
        return obs, reward, done, info

    def get_state(self):
        """A deep copy, safe to keep. A search node stores this and nothing else."""
        return copy.deepcopy(self._require())

    def load_state(self, state):
        """Install a deep copy of `state`. This is how a node is re-visited."""
        self._state = copy.deepcopy(state)

    def clone(self):
        """A second environment on the same corpus, at the same state."""
        twin = IntranetEnv()
        twin._state = copy.deepcopy(self._state)
        return twin

    def render(self):
        return observe(self._require())

    def legal_actions(self):
        return legal_actions(self._require())

    @property
    def query(self):
        return QUERIES[self._require()["query_idx"]]

    @property
    def state(self):
        """The live dict. Do not mutate it: use get_state() for a copy."""
        return self._state

    def _require(self):
        if self._state is None:
            raise RuntimeError("call reset(query_idx) first")
        return self._state


# ===========================================================================
# Assertions that run on import. Cheap, and they are the properties every other
# build conversation is entitled to assume. The semantic corpus checks (two hop,
# no leaks, blind guess payoffs) live in selfcheck.py and corpus_check.py.
# ===========================================================================

def _assert_corpus():
    assert len(SITES) == 5 and tuple(SITES) == SITE_KEYS
    pages = all_pages()
    assert 30 <= len(pages) <= 40, "corpus size moved: %d pages" % len(pages)
    for key in SITE_KEYS:
        assert 6 <= len(SITES[key].pages) <= 8, key
    assert len(QUERIES) == 10
    for i, query in enumerate(QUERIES):
        assert query.qid == i + 1
        for hop in (query.hop1, query.hop2):
            assert hop[0] in SITE_KEYS and 0 <= hop[1] < len(SITES[hop[0]].pages)
        # A two hop query whose hops are the same page is not a two hop query.
        assert query.hop1 != query.hop2, query.qid
        assert all(site in SITE_KEYS for site in query.distractors)
        # The hop 2 page must offer a choice: the gold and at least three decoys,
        # all distinct. Whether they are really on that page is selfcheck's job.
        assert query.key_entity, query.qid
        assert len(query.decoy_answers) >= 3, query.qid
        candidates = (query.answer,) + tuple(query.decoy_answers)
        assert len(set(candidates)) == len(candidates), query.qid


def _assert_pure():
    """transition does not mutate its input, and is a function of (state, action)."""
    state = initial_state(0)
    walk = ["goto_site[people]", "next", "next", "follow[1]", "next"]
    probes = ["goto_site[facilities]", "next", "prev", "follow[1]", "follow[9]",
              "goto_site[nowhere]", "answer[N-310]", "search[coffee]"]
    for action in walk + ["stop"]:
        for probe in probes:
            before = copy.deepcopy(state)
            first = transition(state, probe)
            assert state == before, "transition mutated its input on %r" % probe
            assert first == transition(state, probe), \
                "transition is not a function of (state, action) on %r" % probe
        if action != "stop":
            state = transition(state, action)[0]
    # A finished episode absorbs anything, without raising and without a step.
    done_state = transition(state, "answer[N-310]")[0]
    again = transition(done_state, "next")
    assert again[0] == done_state and again[2] == 0.0 and again[3] is True
    assert again[4]["steps"] == done_state["steps"]


_assert_corpus()
_assert_pure()


# ===========================================================================
# A demo, so `python3 intranet.py` shows what an episode looks like.
# ===========================================================================

def _demo():
    n_pages = len(all_pages())
    n_links = sum(len(page.links) for key in SITE_KEYS for page in SITES[key].pages)
    print("Nordhelm intranet: %d sites, %d pages, %d links, budget %d actions"
          % (len(SITE_KEYS), n_pages, n_links, MAX_STEPS))
    print()

    env = IntranetEnv()
    print("=" * 74)
    print("reset(0), the portal")
    print("=" * 74)
    print(env.reset(0))

    print()
    print("=" * 74)
    print("a gold trajectory for query 1, one line per action")
    print("=" * 74)
    print("  hop 1 is the team directory, which says Building Nord and no room code;")
    print("  hop 2 is the lounge table, which says N-310 and never says which team.")
    for action in ("goto_site[people]", "follow[1]",
                   "goto_site[facilities]", "next", "next",
                   "answer[N-310]"):
        obs, reward, done, info = env.step(action)
        print("  %-24s reward %.3f  done %-5s  %s"
              % (action, reward, done, info["reason"] or "ok"))

    print()
    print("=" * 74)
    print("the page the answer was read from, and the three rows it does not want")
    print("=" * 74)
    env.load_state(env.get_state())
    print(env.render())


if __name__ == "__main__":
    _demo()

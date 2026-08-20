"""agent_lib.py, the frozen language model the LATS intranet exercises run on.

One object with three faces, which is the lecture's whole claim about LATS made
executable:

    propose(state, n)        the POLICY, n candidate actions, SAMPLED
    value(state)             LM(s), how promising this partial trajectory looks
    reflect(state, reward)   the CRITIC, one verbal line after a failure

Nothing here is trained and nothing here is updated. Everything in it is a stand in for
prompting a language model, built out of word overlap because word overlap is cheap,
offline and reproducible, not because it is what a real model does. Swapping in a real
model means replacing this file and nothing else: neither the notebook nor the
controller ever touches the corpus.

The two baselines live here too, because they consist of nothing but the model: one
trajectory, top proposal every step, no branching and no way back.

WHY THIS IS A FILE OF ITS OWN. Both the notebook and reference_lats_intranet.py import
it. With 400 lines of scoring machinery, two copies would drift, and the notebook's
numbers would stop being the reference's numbers, which is the one thing NUMBERS.md
exists to prevent. The knob table lives here for the same reason: every knob is quoted
somewhere, so there is exactly one definition of each.

WHAT THE MODEL MAY AND MAY NOT SEE. It reads the question, the page it is standing on,
the labels of that page's links, the side pane blurbs, and the pages it has already
opened: exactly the agent's observation plus its own reading history, which is the
context a real language model would be prompted with. It never reads `Query.answer`,
`Query.hop1`, `Query.hop2` or `Query.distractors`, so it cannot know which page is the
bridge or what the gold string is. `_check_no_oracle()` in reference_lats_intranet.py
enforces that by scrambling those fields and asserting the model does not notice.

The one piece of hand written knowledge in it is the SHAPE TABLE: the question word
"who" wants a person, "which floor" wants a floor, "which queue" wants a code. That is a
stand in for the one thing every language model does effortlessly, understanding what
KIND of thing is being asked, and DESIGN.md's blind guess number already assumes it.

Determinism: all randomness goes through an explicitly seeded `random.Random`, never the
global module and never `hash()`, which is salted per process.

Needs: intranet.py and the five corpus_<site>.py modules beside it. Nothing else.
"""
import hashlib
import json
import math
import random
import re
from collections import Counter

import intranet
from intranet import (MAX_STEPS, QUERIES, SITE_KEYS, SITES, legal_actions, page_at,
                      page_text, transition)


# ===========================================================================
# 0. The knobs. Every one of them is quoted somewhere, so they live together.
# ===========================================================================

SEED = 0                 # the one seed the whole file runs from

# The search, with the paper's HotpotQA settings wherever the paper has one.
W = 1.0                  # exploration weight in UCT (LATS uses w = 1)
LAM = 0.5                # V(s) = lam LM(s) + (1 - lam) SC(s), the paper's HotpotQA value
N_DEFAULT = 3            # actions sampled per expansion (the paper samples 5)
K_DEFAULT = 8            # trajectories per query (the paper runs 50)
SC_VOTES = 4             # independent draws behind SC(s)
SUCCESS = 0.9            # a reward at or above this counts as a success

# The model. These shape how an agent that cannot really read behaves like one that can.
TEMPERATURE = 0.25       # softmax temperature of the sampling policy
BRIDGE_W = 1.0           # weight of "what I have read" against "what I was asked"
NEXT_SCALE = 0.55        # paging blind through a site, against following a labelled link
REVISIT_SCALE = 0.35     # paging back onto a page already read
ANSWER_W = 0.90          # how attractive submitting an answer is against reading on
NOVELTY_FLOOR = 0.25     # what an answer that only repeats the question is still worth
BRIDGE_TERMS = 4         # new entities per page read that enter the bridge context
N_ANSWER_CANDIDATES = 3  # answer candidates the policy carries into the sample
VALUE_SCALE = 0.60       # what LM(s) calls a perfect looking page
STALE_PENALTY = 0.30     # what reflection leaves of a move it has already seen fail


# ===========================================================================
# 1. THE FROZEN MODEL. One object, three faces: policy, value, critic.
# ===========================================================================
#
# Everything in this section is a stand in for prompting a language model. It is built
# out of word overlap because word overlap is cheap, offline and reproducible, not
# because it is what a real model does. Swapping in a real model means replacing this
# class and nothing else: the controller below never touches the corpus.

STOPWORDS = {
    "which", "what", "who", "whom", "whose", "where", "when", "why", "how", "is", "are",
    "was", "were", "be", "been", "am", "do", "does", "did", "doing", "done", "have",
    "has", "had", "can", "could", "will", "would", "shall", "should", "may", "might",
    "must", "i", "me", "my", "you", "your", "we", "our", "they", "them", "their", "it",
    "its", "he", "she", "his", "her", "this", "that", "these", "those", "there", "here",
    "and", "or", "but", "if", "then", "so", "for", "of", "to", "in", "on", "at", "by",
    "with", "from", "into", "onto", "about", "as", "than", "not", "no", "all", "any",
    "every", "each", "some", "one", "two", "up", "out", "over", "under", "again", "own",
    "go", "goes", "going", "get", "gets", "need", "needs", "needed", "use", "used",
    "using", "run", "runs", "take", "takes", "make", "makes", "also", "just",
}


def _stem(token):
    """A crude stemmer, so `floors` matches `floor` and `logged` matches `logs`."""
    if len(token) > 4 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 5 and token.endswith("ing"):
        return token[:-3]
    if len(token) > 4 and token.endswith("ed"):
        return token[:-2]
    if len(token) > 3 and token.endswith("es") and not token.endswith("ss"):
        return token[:-2]
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def terms(text):
    """The content words of a piece of text, stemmed, as a set."""
    return {_stem(t) for t in intranet.normalize_tokens(text)
            if t not in STOPWORDS and _stem(t) not in STOPWORDS}


def _build_idf():
    """Inverse document frequency over the 36 pages.

    This is what makes a rare word like `metrolog` or `nord` count for far more than
    `building` or `line`, which is the whole reason a bridge fact is worth anything.
    """
    pages = [terms(page_text(key, i)) for key in SITE_KEYS
             for i in range(len(SITES[key].pages))]
    n_docs = len(pages)
    df = Counter()
    for page in pages:
        df.update(page)
    idf = {t: math.log(1.0 + n_docs / (1.0 + c)) for t, c in df.items()}
    return idf, math.log(1.0 + n_docs / 1.0)


IDF, IDF_UNSEEN = _build_idf()
IDF_MAX = max(IDF.values())


def _profile(text_terms):
    """A set of terms turned into weights that sum to 1, so relevance lands in [0,1]."""
    weights = {t: IDF.get(t, IDF_UNSEEN) for t in text_terms}
    total = sum(weights.values())
    if total <= 0:
        return {}
    return {t: w / total for t, w in weights.items()}


def _relevance(text_terms, profile):
    """How much of `profile` this text covers, in [0,1]."""
    if not profile:
        return 0.0
    return sum(w for t, w in profile.items() if t in text_terms)


# ==== 1.1 What kind of answer the question is asking for ===================
#
# The one piece of hand written knowledge in the model. A real model gets this for free
# from the question; the mock needs a table. Note that it reads the QUESTION only.

SHAPE_PATTERNS = {
    "person": re.compile(r"\b([A-Z][a-z]{2,} [A-Z][a-z]{2,})\b"),
    "building": re.compile(r"\b(Building [A-Z][a-z]+)\b"),
    "floor": re.compile(r"\b([Ff]loors? \d+)\b"),
    "level": re.compile(r"\b([Ll]evels? \d+)\b"),
    "code": re.compile(r"\b([A-Z]{1,3}[0-9]?-[A-Za-z0-9]+)\b"),
    "time": re.compile(r"\b(\d{1,2}:\d{2})\b"),
}

# A capitalised pair that is not a person. Without this the model would answer "Building
# Nord" to a "who" question, which no reader of the page would do. It is a list of the
# words an English sentence starts with, not a list of the corpus's people.
NOT_A_PERSON = (
    "Building ", "Managing ", "Head ", "Line ", "Cost ", "Support ", "Clean ", "Every ",
    "Each ", "The ", "This ", "That ", "Zurich ", "Product ", "Team ", "Field ",
    "Signed ", "Reference ", "Higher ", "Report ", "Visitor ", "Visitors ", "Personal ",
    "Customer ", "Customers ", "Safety ", "Security ", "Anything ", "Anyone ",
    "Colleagues ", "Public ", "Working ", "Contractor ", "Contractors ", "Outgoing ",
    "Deliveries ", "Assembly ", "Reception ", "Parking ", "Badges ", "Level ", "Floors ",
    "Ranges ", "Firmware ", "Primary ", "Open ", "Core ", "Bring ", "Two ", "Three ",
    "Never ", "Forward ", "Forwarding ", "Ask ", "Use ", "Hold ", "Call ", "Tell ",
    "Quote ", "Access ", "Orders ", "Policies ", "Releases ", "Updates ", "Both ",
    "Wetted ", "Volumes ", "Standard ", "Environmental ", "Test ", "Tests ", "Neither ",
    "Scanning ", "Printers ", "Printing ", "Guest ", "Mobile ", "Replacement ",
    "Tickets ", "Measurement ", "Hardware ", "Badge ", "Desk ", "Holiday ", "Unpaid ",
    "Overtime ", "Time ", "Day ", "Days ", "Your ", "New ", "Book ", "Second ",
    "Claims ", "Scan ", "Travel ", "Nobody ", "Typical ", "Splitting ", "Buy ",
    "Where ", "When ", "While ", "Sued ", "West ", "Nord ", "Divisions ", "Division ",
    "Quality ", "Instruments ", "Operations ", "Discontinued ", "Drawings ",
    "Furniture ", "Facilities ", "Desk", "Seats ", "Bicycles ", "Permits ", "Cups ",
    "Meetings ", "Payment ", "Coffee ", "Higher", "Reporting ", "Sign ", "Duty ",
    "Deputies ", "Reporting", "Welcome ", "Getting ", "Laptops ", "Network ",
    "Software ", "Contacting ", "Approved ", "Procurement ", "Data ", "Absence ",
)

# question word -> the shape it asks for. Scanned left to right over the question.
SHAPE_KEYWORDS = {
    "who": "person", "whom": "person", "manager": "person",
    "floor": "floor", "level": "level",
    "building": "building",
    "room": "code", "queue": "code", "system": "code", "code": "code",
    "time": "time",
}
_WH = ("which", "what")


def wanted_shapes(question):
    """Which kinds of answer the question is asking for, in the order it asks for them.

    "Who is the account manager ...?"           -> ("person",)
    "Which floor is the coffee lounge on ...?"  -> ("floor",)
    "In which building and on which floor ...?" -> ("building", "floor")

    Only a noun that FOLLOWS a question word counts, which is what keeps the trailing
    "in the building where the Vega team sits" of query 1 out of the answer shape.
    """
    words = [w for w in re.split(r"[^a-z]+", question.lower()) if w]
    shapes, i = [], 0
    while i < len(words):
        word = words[i]
        if word in ("who", "whom"):
            shapes.append("person")
            i += 1
            continue
        if word in _WH:
            for follower in words[i + 1:i + 4]:
                if follower in SHAPE_KEYWORDS:
                    shapes.append(SHAPE_KEYWORDS[follower])
                    break
        i += 1
    if not shapes:                      # a question with no handle: entities it is, then
        shapes = ["person", "code", "building"]
    out = []
    for shape in shapes:                # keep the order, drop the repeats
        if shape not in out:
            out.append(shape)
    return tuple(out)


def _spans(line, shape):
    """Every span of the given shape in one line of page text, in order."""
    found = []
    for match in SHAPE_PATTERNS[shape].finditer(line):
        span = match.group(1)
        if shape == "person" and span.startswith(NOT_A_PERSON):
            continue
        if span not in found:
            found.append(span)
    return found


def _candidate_lines(site_key, index):
    """The lines an answer may be read off: the title, then the body."""
    page = page_at(site_key, index)
    return (page.title,) + tuple(page.body)


_CANDIDATE_CACHE = {}


def answer_candidates(site_key, index, shapes):
    """Every answer this page offers of the shape the question asks for.

    Returns a list of (answer_text, source_line). A question that asks for two things
    ("in which building and on which floor") is answered with both, joined, whenever one
    line carries both; a line that carries only one of them still offers that one.
    """
    key = (site_key, index, shapes)
    if key in _CANDIDATE_CACHE:
        return _CANDIDATE_CACHE[key]
    out, seen = [], set()
    for line in _candidate_lines(site_key, index):
        per_shape = [(shape, _spans(line, shape)) for shape in shapes]
        present = [(shape, found) for shape, found in per_shape if found]
        if len(shapes) > 1 and len(present) == len(shapes):
            # The question asked for several things and this line carries them all.
            joined = ", ".join(found[0] for _, found in present)
            if joined not in seen:
                seen.add(joined)
                out.append((joined, line))
            continue
        for _, found in present:
            for span in found:
                if span not in seen:
                    seen.add(span)
                    out.append((span, line))
    _CANDIDATE_CACHE[key] = out
    return out


# ==== 1.2 The model itself =================================================


def seed_for(state, seed):
    """A seed derived from the state, so the same node always draws the same sample.

    Never `hash()`: it is salted per process, so the same notebook re-run on the same
    machine would give different numbers.
    """
    key = json.dumps(state, sort_keys=True) + "|" + str(seed)
    return int.from_bytes(hashlib.sha256(key.encode()).digest()[:4], "big")


class Memory:
    """The reflection buffer: the notes, and what the next trajectory does with them.

    A note is a sentence. What a model DOES with a sentence it has been shown is stop
    repeating what the sentence says failed, so `penalty` is the executable half: an
    answer already tried, and a page already answered from, both lose most of their
    weight in the next sample. Switch reflection off and this object is never consulted.
    """

    def __init__(self):
        self.notes = []
        self.tried = {}                 # answer text -> the reward it earned
        self.stale = set()              # "site/index" answered from without success

    def add(self, note, state, reward):
        if note not in self.notes:
            self.notes.append(note)
        if state["answer"] is not None:
            self.tried[state["answer"]] = reward
            if state["trail"]:
                self.stale.add(state["trail"][-1])

    def penalty(self, state, action):
        """A multiplier in (0,1] for an action a note has already warned about."""
        if action.startswith("answer["):
            text = action[len("answer["):-1]
            if text in self.tried:
                return STALE_PENALTY * max(0.0, self.tried[text])
            here = "%s/%d" % (state["site"], state["page"]) if state["site"] else ""
            if here in self.stale:
                return STALE_PENALTY
        return 1.0


# ===========================================================================
# 2. THE BASELINES. One trajectory, no branching, no going back.
# ===========================================================================
#
# There are two of them, and the second one exists to stop the headline being a cheat.
#
#   `greedy_baseline`   the top proposal every step. This is what a plain ReAct agent
#                       does and what the room watches fail.
#   `best_of_k`         k INDEPENDENT sampled trajectories, keep the best scoring one.
#                       Same policy, same budget per trajectory, no tree.
#
# Without the second row, "LATS beats greedy" would be measuring two different things at
# once: having a tree, and being allowed k attempts at an answer instead of one. The
# best of k row holds the number of attempts fixed and takes the tree away, so the two
# gaps can be read separately. See the ablation table.


def _rollout(lm, query_idx, greedy, draw=0):
    """One trajectory from the portal to a terminal state. The body of both baselines.

    `greedy=True` takes the top scoring action every step; `greedy=False` samples from
    the same policy at the same temperature the search uses, with `draw` standing in for
    calling a real model again at temperature 0.7.

    With one action of budget left it must answer, exactly as Simulation must. An agent
    that runs out of steps scores 0.0, and a baseline that is never allowed to speak is
    not a baseline, it is a straw man.
    """
    state = intranet.initial_state(query_idx)
    trajectory, reward = [], 0.0
    while not state["done"]:
        last_call = (MAX_STEPS - state["steps"]) <= 1
        proposals = lm.propose(state, n=1, draw=draw, greedy=greedy,
                               answers_only=last_call)
        if not proposals and last_call:
            proposals = lm.propose(state, n=1, draw=draw, greedy=greedy)
        if not proposals:
            break
        action = proposals[0]
        trajectory.append(action)
        state, _, reward, done, _ = transition(state, action)
        if done:
            break
    return {"trajectory": trajectory, "reward": float(reward),
            "answer": state["answer"]}


def greedy_baseline(lm, query_idx):
    """Take the policy's top proposal every step and live with it.

    No tree, no value function, no second opinion, and no way back. It commits to the
    first plausible looking site, reads the first plausible looking page, and answers off
    it. When two sites look equally good it ping pongs between them until the budget runs
    out and then answers from wherever it happens to be standing, which is worth watching
    in the trace: an argmax policy has no mechanism for noticing it is in a loop.

    Returns {"trajectory", "reward", "calls", "answer"}.
    """
    lm.calls = 0
    out = _rollout(lm, query_idx, greedy=True)
    out["calls"] = lm.calls
    return out


def best_of_k(lm, query_idx, k=K_DEFAULT):
    """k independent sampled trajectories, report the best scoring one.

    The control for the headline. It gets the same policy, the same per trajectory
    budget and the same k attempts LATS gets, and it reads the same environment reward
    to pick a winner. What it does not get is a tree: nothing it learns in trajectory 3
    can change trajectory 4, because each one starts again at the portal.

    Returns {"trajectory", "reward", "calls", "answer"}.
    """
    lm.calls = 0
    best = {"trajectory": [], "reward": -1.0, "answer": None}
    for draw in range(max(1, k)):
        out = _rollout(lm, query_idx, greedy=False, draw=draw)
        if out["reward"] > best["reward"]:
            best = out
        if out["reward"] >= SUCCESS:
            break
    best["reward"] = max(0.0, best["reward"])
    best["calls"] = lm.calls
    return best

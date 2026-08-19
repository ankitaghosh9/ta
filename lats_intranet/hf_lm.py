"""hf_lm.py, the real language model the LATS intranet exercises run on.

The one model. There is no mock and no fallback, decided 2026-08-12, because a
scripted stand in misrepresents exactly the three
things this module is about: SC(s) is pinned at 1.000 under a deterministic ranker,
LM(s) is either oracle-ish or arbitrarily bad rather than wrong in the structured way
a real critic is wrong, and reflection cannot be mocked at all, since it is a verbal
critique in natural language.

    import hf_lm, intranet
    env = intranet.IntranetEnv()
    env.reset(0)
    lm = hf_lm.make_lm(env)                  # the model. There is only one
    lm.propose(env.state, n=3)               # the POLICY
    lm.value(env.state)                      # LM(s)
    lm.reflect(terminal_state, reward)       # the CRITIC, freely generated

Three faces behind one object, so the controller, the two
baselines and the notebook swap backends without changing a line.

Default model `Qwen/Qwen2.5-0.5B-Instruct`: public, no API key, about 1 GB, and it
runs on the free Colab GPU. It runs on CPU too, slowly (see COST below).

WHY IT SCORES A MENU AND NEVER GENERATES AN ACTION
==================================================
Asking a 0.5B model to emit `follow[2]` in exactly the right grammar is unreliable,
and a parse failure would silently become some fallback action, so the search would
be measuring the fallback. Instead the ENVIRONMENT supplies the candidates and the
model RANKS them by likelihood, one forward pass per candidate, and the sample is
drawn from that ranking at temperature. There is nothing to parse and the action
grammar cannot break.

The menu is `intranet.legal_actions(state)` plus the `answer[...]` candidates the
current page offers, because `legal_actions` never enumerates `answer[...]`: its
payload is free text, and that is the one place the branching factor is infinite.
The answer candidates come from the page text in two ways, both of them corpus level
and neither of them the gold (see `answer_menu`).

VALUE IS ONE FORWARD PASS. Rather than generating a score and parsing it, the model
is asked whether this search is on track and the value is read off as P(" yes")
against P(" no"). Always in [0,1], never fails, one pass.

REFLECTION GENUINELY GENERATES, because it must. It is the one place free generation
is unavoidable: a reflection IS a sentence, and the whole of LATS's learning between
trajectories is that sentence being put in front of the next one. It is called at
most once per failed trajectory and is capped at REFLECT_TOKENS new tokens.

WHAT THE MODEL MAY SEE. The question, the page it stands on with its links, and the
pages it has already opened. Exactly the agent's observation plus its own reading
history. It never reads `Query.answer`, `Query.hop1`, `Query.hop2`,
`Query.distractors` or the redesign's `key_entity` and `decoy_answers`, so it cannot
know which page is the bridge or what the gold string is.

DETERMINISM. The sampling goes through an explicitly seeded `random.Random`, seeded
from the state exactly as `agent_lib` seeds it, so the same node always draws the same
sample whatever order the search visits it in. Generation is greedy (`do_sample`
False), so no call touches torch's global random generator. What is NOT reproducible
is the model's arithmetic across devices and dtypes: fp16 on a GPU and fp32 on a CPU
give slightly different scores, so NUMBERS.md pins the LM path as ranges and
qualitative claims and pins no exact numbers.

COST. One forward pass per candidate, so a menu of 12 costs 12 passes. Scores are
cached per state, so the self consistency votes cost one set of passes while still
differing, because the sampling is what varies. On a GPU a state is a fraction of a
second; on CPU it is seconds, so a full search on CPU is a coffee break.

Needs: intranet.py, agent_lib.py and the five corpus_<site>.py modules beside it, plus
torch and transformers. Importing this module does NOT need torch: only building
`HFLocalLM` does, so the module imports anywhere and fails loudly at load time.

Run it:  python3 hf_lm.py     (loads the model and prints a menu, a value, a reflection)
"""
import json
import math
import random
import re

from intranet import QUERIES, legal_actions, page_at
from agent_lib import (N_DEFAULT, SEED, answer_candidates, seed_for,
                       wanted_shapes)

try:                                  # torch is needed to RUN the model, not to import
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    IMPORT_ERROR = None
except Exception as exc:              # noqa: BLE001, any import failure is one story
    torch = None
    AutoModelForCausalLM = AutoTokenizer = None
    IMPORT_ERROR = exc


# ===========================================================================
# 0. The knobs. The search knobs (W, LAM, N_DEFAULT, K_DEFAULT, SC_VOTES, SEED)
# stay in agent_lib.py, so there is exactly one definition of each. Only the ones
# that belong to a real model live here.
# ===========================================================================

MODEL_ID = "Qwen/Qwen2.5-3B-Instruct"     # public, no token, about 6 GB in fp16.
# 0.5B was measured on 2026-08-12 and scored 0.200 on five questions, identical across
# every ablation INCLUDING the fully blinded one, and at the 0.220 blind guess line. It
# contributed no usable signal, so the search was not searching. 3B is the next rung that
# still fits a T4 comfortably.
TEMPERATURE = 1.0        # softmax temperature over mean log probabilities per token
MAX_ANSWER_CANDIDATES = 8  # answer[...] candidates carried into the menu, a cost guard
PAGE_CHARS = 800         # of the current page that reaches the prompt
NOTE_CHARS = 1600        # of the pages already read, in total: four of the below
PER_NOTE_CHARS = 400     # of any one page already read. MEASURED, see `_notes`
REFLECT_TOKENS = 60      # the cap on the one place that generates freely
REFLECT_CHARS = 240      # and the cap on what is kept of it
TINY = 1e-6              # floor under a reflection penalty, so log() is finite


# ===========================================================================
# 1. THE MENU. What the environment offers the model to choose between.
# ===========================================================================
#
# Navigation comes straight from `intranet.legal_actions`. The answers do not, and
# cannot: `legal_actions` never enumerates `answer[...]`, because its payload is free
# text. So the page itself supplies the answer menu, in two ways.
#
#   1. THE VALUE HALF OF EVERY `key: value.` TABLE ROW. After the redesign a hop 2
#      page is a table keyed by the entity hop 1 reveals, so the rows ARE the choice
#      the query is about: `Building Nord: N-310.` offers `N-310`, and the other
#      three rows offer three plausible wrong answers. Leading lowercase words are
#      dropped, because `Varda: queue Eiche.` is offering `Eiche` and the word queue
#      belongs to the table, not to the answer.
#   2. EVERY SPAN OF THE SHAPE THE QUESTION ASKS FOR, from `agent_lib`. That is the
#      one piece of hand written knowledge either model gets: "who" wants a person,
#      "which room" wants a code. It reads the QUESTION and the page, never the gold,
#      and both backends share it, so they choose from the same menu.
#
# Neither source can leak: both read only text the agent is already looking at.

_ROW = re.compile(r"^(?P<key>[^:]{1,60}?): (?P<value>.+?)\.?$")


def _row_value(line):
    """The value half of a `key: value.` table row, or None if the line is not one.

    A table key is short and carries no punctuation, which is what keeps ordinary
    prose out: a sentence that happens to contain a colon does not become a menu
    entry, and neither does a time, because the colon in 07:20 has no space after it.
    """
    match = _ROW.match(line.strip())
    if match is None:
        return None
    key = match.group("key")
    if len(key.split()) > 4 or "," in key or ";" in key:
        return None
    words = match.group("value").strip().rstrip(".").split()
    while len(words) > 1 and words[0][:1].islower():
        words = words[1:]
    return " ".join(words).strip(" ,") or None


def answer_menu(state, limit=MAX_ANSWER_CANDIDATES):
    """The free text answers the page in front of the agent offers, in menu order.

    Table rows first, because on a hop 2 page they are the decision; then the spans
    of the shape the question wants, which is what carries the pages that are prose
    rather than a table. Duplicates are dropped and the list is capped, since every
    entry costs one forward pass. The cap cuts from the end, which is order of
    appearance on the page, and it is a cost guard rather than a ranking: the ranking
    is the model's job, further down.
    """
    if state["done"] or state["site"] is None:
        return []
    out = []
    for line in page_at(state["site"], state["page"]).body:
        value = _row_value(line)
        if value and value not in out:
            out.append(value)
    shapes = wanted_shapes(QUERIES[state["query_idx"]].question)
    for span, _line in answer_candidates(state["site"], state["page"], shapes):
        if span not in out:
            out.append(span)
    return out[:limit]


def action_menu(state, limit=MAX_ANSWER_CANDIDATES):
    """Everything the model is allowed to choose between at this state."""
    return (legal_actions(state)
            + ["answer[%s]" % text for text in answer_menu(state, limit)])


# ===========================================================================
# 2. THE PROMPT. The same context for all three faces, which is the point: one
# frozen model, shown one situation, asked three different questions about it.
# ===========================================================================


def _page_text(site_key, index, budget):
    """A page as the prompt shows it: the title, then as many body lines as fit."""
    page = page_at(site_key, index)
    out, used = [page.title], len(page.title)
    for line in page.body:
        if used + len(line) > budget:
            break
        out.append("  " + line)
        used += len(line)
    return "\n".join(out)


def _notes(state, budget=NOTE_CHARS):
    """The pages already read, newest last, oldest dropped first when the budget bites.

    This is where the hop 1 fact lives once the agent has walked on: the observation
    lists only the TITLES of the pages read, so without these notes the model would
    stand on the hop 2 table with no idea which row is its own, and every run would
    measure the truncation rule rather than the model.

    Both budgets are therefore measured rather than chosen. PER_NOTE_CHARS is 400
    because a hop 1 page has to survive its own truncation with the bridge fact still
    in it: at 240 characters six of the ten queries lose it, at 320 one still does,
    and at 400 none do, for blocks of 311 to 404 characters. NOTE_CHARS is
    four of those, and past four the oldest page read is dropped first, which is the
    one an agent that has wandered can least afford to lose. Print `_notes(state)` if
    a run looks like the model cannot see what it read.
    """
    here = "%s/%s" % (state["site"], state["page"])
    kept, used = [], 0
    for entry in reversed([e for e in state["trail"] if e != here]):
        key, _, index = entry.partition("/")
        block = _page_text(key, int(index), PER_NOTE_CHARS)
        if used + len(block) > budget:
            break
        kept.append(block)
        used += len(block)
    return "\n\n".join(reversed(kept))


def context(state):
    """The situation, in words: the question, what has been read, where the agent is."""
    out = ["You are searching a company intranet to answer one question.",
           "",
           "Question: " + QUERIES[state["query_idx"]].question,
           ""]
    notes = _notes(state)
    if notes:
        out += ["Pages you have already read:", notes, ""]
    if state["site"] is None:
        out += ["You are at the intranet home. No page is open.", ""]
    else:
        out += ["The page you are on now:",
                _page_text(state["site"], state["page"], PAGE_CHARS)]
        links = page_at(state["site"], state["page"]).links
        if links:
            out.append("Links on this page:")
            for j, link in enumerate(links, start=1):
                out.append("  [%d] %s  (%s)" % (j, link.label, link.site))
        out.append("")
    return "\n".join(out)


def policy_prompt(state):
    """The prompt every candidate action is scored as a continuation of."""
    return context(state) + "\n".join([
        "You may open a site with goto_site[name], move with next or prev, open a",
        "link with follow[number], or finish with answer[text].",
        "",
        "The best next action is:"])


def value_prompt(state):
    """The prompt whose next token is read as P(yes) against P(no)."""
    return context(state) + "\n".join([
        "Is this search on track to answer the question? Answer yes or no.",
        "",
        "Answer:"])


def reflect_prompt(state, reward, trajectory=None):
    """The prompt the one freely generated sentence continues."""
    read = ", ".join(page_at(key, int(index)).title
                     for key, _, index in (e.partition("/") for e in state["trail"]))
    out = [context(state).rstrip(),
           "",
           "That attempt is over. Pages read: " + (read or "none") + ".",
           "It answered %r and scored %.2f out of 1.00." % (state["answer"], reward)]
    if trajectory:
        out.append("Actions taken: " + ", ".join(trajectory) + ".")
    out += ["",
            "In one short sentence, say what went wrong and what the next attempt",
            "should read instead.",
            "",
            "Advice:"]
    return "\n".join(out)


# ===========================================================================
# 3. Keeping generated text plain. A model writes whatever it likes, including
# typographic dashes and quotes, and this text is printed, stored in the
# reflection buffer and sometimes pasted into notes. It leaves here as ASCII.
# The table is written as code points so that this file itself stays ASCII.
# ===========================================================================

_UNICODE_PUNCTUATION = {
    chr(0x2010): "-", chr(0x2011): "-",                       # the two hyphens
    chr(0x2012): ",", chr(0x2013): ",", chr(0x2014): ",",     # figure, en, em dashes
    chr(0x2015): ",", chr(0x2212): "-",                       # bar, minus
    chr(0x2018): "'", chr(0x2019): "'", chr(0x201a): ",",     # single quotes
    chr(0x201c): '"', chr(0x201d): '"',                       # double quotes
    chr(0x2026): " ", chr(0x00a0): " ", chr(0x2022): "-",     # ellipsis, nbsp, bullet
}


def plain(text):
    """ASCII, one line, no double spaces. Anything else the model wrote is dropped."""
    for fancy, plainer in _UNICODE_PUNCTUATION.items():
        text = text.replace(fancy, plainer)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([,.;:])", r"\1", text)
    return text.strip().strip('"').strip()


def first_sentences(text, keep=2, limit=REFLECT_CHARS):
    """The first `keep` sentences of a generation, hard capped at `limit` characters."""
    text = plain(text)
    if not text:
        return ""
    text = " ".join(re.split(r"(?<=[.!?])\s+", text)[:keep])
    if len(text) > limit:
        cut = text.rfind(". ", 0, limit)
        text = text[:cut + 1] if cut > 40 else text[:limit].rstrip() + "."
    return text


# ===========================================================================
# 4. THE MODEL. One object, three faces: propose, value, reflect.
# ===========================================================================


class HFLocalLM:
    """A small public language model as the LATS policy, value and critic.

        propose(state, n)        the POLICY, n candidate actions, SAMPLED
        value(state)             LM(s), how promising this partial trajectory looks
        reflect(state, reward)   the CRITIC, one freely generated line after a failure

    Nothing is trained and nothing is updated. The weights that answer the third
    question are the weights that answered the first two, which is the lecture's whole
    claim about LATS made executable.

    `draw` is the temperature knob: the same node re-sampled
    with a different draw index gives a different sample, which is what makes SC(s) a
    measurement rather than the constant 1.000 a deterministic ranker pins it at.
    """

    def __init__(self, env=None, model_id=MODEL_ID, temperature=TEMPERATURE,
                 seed=SEED, device=None, quiet=False):
        if IMPORT_ERROR is not None:
            raise ImportError(
                "hf_lm needs torch and transformers (pip install transformers). "
                "The import failed with %s: %s. Use make_lm(env, backend='mock') to "
                "run offline." % (type(IMPORT_ERROR).__name__, IMPORT_ERROR))
        self.env = env                       # unused by the model, kept for the caller
        self.model_id = model_id
        self.temperature = float(temperature)
        self.seed = seed
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        dtype = torch.float16 if self.device == "cuda" else torch.float32
        self.tok = AutoTokenizer.from_pretrained(model_id)
        try:
            model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=dtype)
        except TypeError:                    # transformers renamed the argument
            model = AutoModelForCausalLM.from_pretrained(model_id, dtype=dtype)
        self.model = model.to(self.device).eval()
        self._cache = {}
        self.calls = 0                       # propose, value and reflect each count one
        self.forward_passes = 0              # what those calls actually cost
        if not quiet:
            print("hf_lm: loaded %s on %s (%s)"
                  % (model_id, self.device, str(dtype).replace("torch.", "")))

    # ==== what the model is looking at ====

    def question(self, state):
        return QUERIES[state["query_idx"]].question

    def _key(self, state):
        """The cache key: everything the prompt depends on, and nothing else.

        Not `steps` and not `note`, because neither reaches the prompt, so two states
        that differ only in how many steps got here share their scores. That is a real
        saving in a tree that reaches the same page by two routes.
        """
        return json.dumps([state["query_idx"], state["site"], state["page"],
                           state["trail"]], sort_keys=True)

    # ==== the forward passes ====

    def _continuation_logprob(self, prompt_ids, text):
        """Mean log probability per token of `text` continuing the prompt. One pass."""
        cont = self.tok(text, return_tensors="pt",
                        add_special_tokens=False).input_ids.to(self.device)
        ids = torch.cat([prompt_ids, cont], dim=1)
        with torch.no_grad():
            logits = self.model(ids).logits[0, prompt_ids.shape[1] - 1:-1].float()
        self.forward_passes += 1
        total = torch.log_softmax(logits, -1).gather(1, cont[0].unsqueeze(1)).sum()
        return float(total) / max(1, cont.shape[1])

    def _scored(self, state):
        """The whole menu, scored and cached. This is where the passes are spent."""
        key = self._key(state)
        if key in self._cache:
            return self._cache[key]
        prompt_ids = self.tok(policy_prompt(state),
                              return_tensors="pt").input_ids.to(self.device)
        scored = [(action, self._continuation_logprob(prompt_ids, " " + action))
                  for action in action_menu(state)]
        scored.sort(key=lambda pair: (-pair[1], pair[0]))
        self._cache[key] = scored
        return scored

    def scored_actions(self, state, memory=None):
        """The menu with the reflection buffer applied, best first.

        A note the critic already wrote about an action multiplies that action's
        PROBABILITY by `memory.penalty`, which in log space is an additive
        `temperature * log(penalty)`. Multiplying a log probability directly, the way
        a heuristic score can be multiplied, would make a negative score BIGGER.
        """
        scored = list(self._scored(state))
        if memory is not None:
            scored = [(action, score + self.temperature
                       * math.log(max(memory.penalty(state, action), TINY)))
                      for action, score in scored]
            scored.sort(key=lambda pair: (-pair[1], pair[0]))
        return scored

    _scored_actions = scored_actions         # the internal name the controller uses

    # ==== face 1, the policy ====

    def propose(self, state, n=N_DEFAULT, draw=0, memory=None, greedy=False,
                answers_only=False):
        """n candidate actions at `state`, sampled from the model's own ranking.

        Sampled without replacement from a softmax over the scores, which is what
        makes the self consistency term measure something. `greedy=True` takes the top
        of the ranking and is the baseline, not the search. `answers_only=True` is
        "you have one action left, say something".
        """
        self.calls += 1
        scored = self.scored_actions(state, memory=memory)
        if answers_only:
            scored = [pair for pair in scored if pair[0].startswith("answer[")]
        if not scored:
            return []
        if greedy:
            return [action for action, _ in scored[:n]]
        rng = random.Random(seed_for(state, self.seed + 7919 * draw))
        pool, picked = list(scored), []
        while pool and len(picked) < n:
            top = max(score for _, score in pool)
            weights = [math.exp((score - top) / self.temperature) for _, score in pool]
            total = sum(weights)
            cut, running, chosen = rng.random() * total, 0.0, 0
            for chosen, weight in enumerate(weights):
                running += weight
                if running >= cut:
                    break
            picked.append(pool.pop(chosen)[0])
        return picked

    # ==== face 2, the value function ====

    def value(self, state):
        """LM(s) in [0,1]: P(" yes") against P(" no"), in one forward pass.

        The portal and a finished episode score 0.0 without asking, which is what
        we must: there is no partial trajectory to judge at the portal, and a
        terminal state is judged by the environment, not by the model. That boundary
        is the seam the lecture draws, so it is worth being strict about.
        """
        self.calls += 1
        if state["done"] or state["site"] is None:
            return 0.0
        key = "v|" + self._key(state)
        if key in self._cache:
            return self._cache[key]
        ids = self.tok(value_prompt(state),
                       return_tensors="pt").input_ids.to(self.device)
        with torch.no_grad():
            logits = self.model(ids).logits[0, -1].float()
        self.forward_passes += 1
        logprobs = torch.log_softmax(logits, -1)
        yes = self.tok(" yes", add_special_tokens=False).input_ids[0]
        no = self.tok(" no", add_special_tokens=False).input_ids[0]
        value = float(torch.softmax(torch.stack([logprobs[yes], logprobs[no]]), 0)[0])
        self._cache[key] = value
        return value

    # ==== face 3, the critic ====

    def reflect(self, state, reward, trajectory=None):
        """One freely generated line about a finished, unsuccessful trajectory.

        THE ONE PLACE THIS MODULE GENERATES. A reflection is a verbal critique in
        natural language, so there is nothing here to rank and nothing to score: the
        model has to write it. Capped at REFLECT_TOKENS new tokens, called at most
        once per failed trajectory, and decoded greedily, so that no call into this
        file touches torch's global random generator.

        `state` is the terminal state, which carries the trajectory's content: the
        pages read and the answer submitted. Pass the list of actions as `trajectory`
        to put the literal moves in front of the model as well. A bare list of actions
        is also accepted in place of `state` when the model was built with an `env`,
        in which case the situation is taken from that env.

        What comes back is prose, and the reflection buffer in `agent_lib.Memory` reads
        the executable half (the answer already tried, the page already answered from)
        off the state rather than out of the sentence, exactly as it does for the mock.
        """
        self.calls += 1
        state, trajectory = self._reflect_target(state, trajectory)
        ids = self.tok(reflect_prompt(state, reward, trajectory),
                       return_tensors="pt").input_ids.to(self.device)
        with torch.no_grad():
            out = self.model.generate(ids, max_new_tokens=REFLECT_TOKENS,
                                      do_sample=False,
                                      pad_token_id=self.tok.eos_token_id)
        self.forward_passes += 1
        text = first_sentences(self.tok.decode(out[0, ids.shape[1]:],
                                               skip_special_tokens=True))
        if not text:                         # a model that says nothing still owes a note
            text = ("That attempt scored %.2f. Read a page that has not been opened "
                    "yet before answering again." % reward)
        return text

    def _reflect_target(self, state, trajectory):
        """Accept a terminal state, or a bare trajectory when there is an env to ask."""
        if isinstance(state, dict):
            return state, trajectory
        if isinstance(state, (list, tuple)):
            if self.env is None or getattr(self.env, "state", None) is None:
                raise TypeError(
                    "reflect(trajectory, reward) needs the situation the trajectory "
                    "ended in. Build the model with make_lm(env) so it can ask the "
                    "env, or call reflect(terminal_state, reward, trajectory=...).")
            return self.env.get_state(), list(state)
        raise TypeError("reflect wants the terminal state or a list of actions, "
                        "not %s" % type(state).__name__)


# ===========================================================================
# 5. Choosing a backend. The one place a notebook says which model it is running.
# ===========================================================================


def make_lm(env=None, seed=SEED, **kwargs):
    """The model. There is exactly one, and it is real.

        make_lm(env)     Qwen2.5-0.5B-Instruct, loaded once

    `env` is passed through to the model and is not used to answer anything: the
    state carries the query index and the corpus is a module. It is there so that
    `reflect(trajectory, reward)` has a situation to talk about.

    THERE IS NO FALLBACK, deliberately, decided 2026-08-12. A scripted stand in
    misrepresents precisely the three things this exercise teaches: self
    consistency is degenerate under a fixed ranker, a scripted value is either
    oracle-ish or arbitrarily bad, and reflection cannot be mocked at all, because
    it is a verbal critique in natural language. A silent fallback would have let a
    run report numbers that came from none of those things, which is worse than a
    run that stops. If the model will not load, this raises and says so.
    """
    return HFLocalLM(env=env, seed=seed, **kwargs)


def ensure_transformers():
    """Install transformers if it is missing. For Colab, a no op anywhere else."""
    import importlib
    import subprocess
    import sys
    try:
        importlib.import_module("transformers")
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q",
                               "transformers"])


# ===========================================================================
# 6. The demo, which is also the check: load the model, print a scored menu, a
# value, and one generated reflection.
# ===========================================================================


def _walk_to(env, target):
    """Open a (site key, page index) pair by paging to it. Demo scaffolding only.

    It reads `Query.hop1` and `Query.hop2`, which the MODEL never may. This is the
    script driving the env to an interesting state, not the agent finding one.
    """
    site, index = target
    env.step("goto_site[%s]" % site)
    while env.state["page"] < index:
        env.step("next")


def _demo(query_idx=0, backend="hf"):
    import intranet
    env = intranet.IntranetEnv()
    env.reset(query_idx)
    query = env.query
    lm = make_lm(env, backend=backend, fallback=False)

    _walk_to(env, query.hop1)                # the bridge page
    hop1_value = lm.value(env.state)
    _walk_to(env, query.hop2)                # the table it points at
    state = env.get_state()

    print("\nquestion   : " + query.question)
    print("standing on: %s / %s  (steps used %d)"
          % (state["site"], page_at(state["site"], state["page"]).title,
             state["steps"]))
    print("read so far: " + ", ".join(page_at(k, int(i)).title
                                      for k, _, i in (e.partition("/")
                                                      for e in state["trail"])))

    print("\nTHE SCORED MENU (mean log probability per token, best first)")
    for action, score in lm.scored_actions(state):
        print("   %8.3f  %s" % (score, action))

    votes = [lm.propose(state, n=3, draw=d)[0] for d in range(4)]
    agree = max(votes.count(vote) for vote in votes) / len(votes)
    print("\nsampled first choices over 4 draws: %s" % votes)
    print("SC(s) = %.3f   (a deterministic ranker pins this at 1.000)" % agree)

    print("\nLM(s) on the bridge page : %.3f" % hop1_value)
    print("LM(s) on the table page  : %.3f" % lm.value(state))

    wrong = next((action for action, _ in reversed(lm.scored_actions(state))
                  if action.startswith("answer[")), "answer[nobody]")
    _obs, reward, _done, _info = env.step(wrong)
    print("\nONE TERMINAL STATE, so that the critic has something to critique.")
    print("Played the worst ranked answer, %s, and the environment paid %.3f."
          % (wrong, reward))
    print("reflection : " + lm.reflect(env.get_state(), reward))
    print("\ncalls %d, forward passes %d" % (lm.calls, lm.forward_passes))


if __name__ == "__main__":
    _demo()

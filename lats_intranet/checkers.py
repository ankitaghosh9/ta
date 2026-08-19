"""Checkers for the LATS intranet exercises.

Imported by the notebook. Student-written names (Node, expand, LM, ...) live in
the notebook, so each check binds them from __main__ before it runs.
"""
import math
import sys

import intranet
from agent_lib import SUCCESS
from intranet import MAX_STEPS, initial_state, transition


def ok(msg):
    print("  OK  " + msg)


def bad(msg):
    print("  XX  " + msg)


def hint(msg):
    print("      hint: " + msg)


def report(title, passed):
    print("\n" + ("PASSED  " if passed else "NOT YET  ") + title
          + ("" if passed else "   (see the hints above)"))
    return passed


def _nb():
    return sys.modules["__main__"]


def _bind():
    """Copy the notebook's names into this module for the duration of a check."""
    m = _nb()
    g = globals()
    for name in (
        "LM", "Node", "at", "W", "LAM", "Memory", "BRIDGE", "TABLE",
        "step", "is_terminal", "reward_of", "answer_of",
        "expand", "simulate", "descend", "path_to_root",
        "self_consistency", "SITES", "QUERIES",
    ):
        if hasattr(m, name):
            g[name] = getattr(m, name)


def _using(stub, fn, *args, **kwargs):
    """Run `fn` with `stub` standing in for the one frozen model, then put LM back.

    Your code calls LM by name in the notebook, so the swap happens there.
    """
    m = _nb()
    real = m.LM
    m.LM = stub
    try:
        return fn(*args, **kwargs)
    finally:
        m.LM = real


def _watching(names, record):
    """Wrap notebook-level functions so only calls made FROM `lats` are recorded."""
    m = _nb()
    g = m.__dict__
    real = {name: g[name] for name in names}
    depth = {"n": 0}

    def wrap(name):
        def wrapped(*args, **kwargs):
            depth["n"] += 1
            try:
                result = real[name](*args, **kwargs)
            finally:
                depth["n"] -= 1
            if depth["n"] == 0:
                record(name, args, result)
            return result
        return wrapped

    for name in names:
        setattr(m, name, wrap(name))
    return real


def _restore(real):
    """Put the real functions back on the notebook."""
    m = _nb()
    for name, fn in real.items():
        setattr(m, name, fn)


# --- exercise checker (notebook cell 17) ---

def check_greedy(fn):
    _bind()
    print("checking your greedy ...\n")
    passed = True

    got = fn(0)
    if not isinstance(got, dict):
        bad("it returned %r, and the last line hands back a dictionary" % (got,))
        return report("Exercise, the greedy agent", False)
    for key in ("trajectory", "answer", "reward", "calls"):
        if key not in got:
            bad("what it returned has no %r in it" % key)
            return report("Exercise, the greedy agent", False)

    if not got["trajectory"]:
        bad("it played no actions at all, so the gap is still empty")
        hint("step(state, action) plays one action and hands back the state it reached. "
             "Without keeping that state the loop never moves and never ends")
        return report("Exercise, the greedy agent", False)
    ok("it played %d actions" % len(got["trajectory"]))

    # The trajectory has to BE what happened. Replaying it in a fresh episode is the
    # cheapest way to catch a loop that recorded one thing and played another.
    state = initial_state(0)
    for action in got["trajectory"]:
        state, _, _, _, _ = transition(state, action)
    if answer_of(state) != got["answer"]:
        bad("replaying that trajectory answers %r, and it reported %r"
            % (answer_of(state), got["answer"]))
        hint("append the action you actually played, and keep the state step() gave you")
        passed = False
    elif abs(reward_of(state) - got["reward"]) > 1e-9:
        bad("replayed, that trajectory pays %.3f, and it reported %.3f"
            % (reward_of(state), got["reward"]))
        passed = False
    else:
        ok("replayed from the portal it does the same thing and pays the same %.3f"
           % got["reward"])

    if not is_terminal(state):
        bad("it stopped while the episode was still running")
        hint("the loop runs until is_terminal(state), or until the budget is gone")
        passed = False
    else:
        ok("it ran to the end of the episode")

    if len(got["trajectory"]) > MAX_STEPS:
        bad("it played %d actions and the budget is %d"
            % (len(got["trajectory"]), MAX_STEPS))
        passed = False

    # NOT graded, and this one is worth a note. Whether it answers at all is a fact
    # about the MODEL, not about your loop: a greedy agent that spends its budget
    # wandering between two plausible sites reaches the last action with nothing open
    # to answer from, and running out is one of the ways this baseline fails. The
    # measured run of the real model answers nothing on several of the ten questions.
    if got["answer"] is None:
        print("      it ran out of steps without answering, which is one of the ways "
              "this\n      agent fails. That is the model's doing, not your loop's")
    else:
        ok("it committed to an answer, %r" % got["answer"])

    if got["calls"] < len(got["trajectory"]):
        bad("it reports %d model calls for %d actions, which is too few"
            % (got["calls"], len(got["trajectory"])))
        hint("leave the LM.calls = 0 line at the top: section 4 prints what greedy cost")
        passed = False
    else:
        ok("it counted its model calls, %d of them" % got["calls"])
    return report("Exercise, the greedy agent", passed)


# --- exercise checker (notebook cell 25) ---

def _number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def check_node(cls):
    _bind()
    print("checking your Node class ...\n")
    passed = True
    portal = intranet.initial_state(0)

    root = cls(portal, None)
    for field, want in (("state", portal), ("parent", None), ("action", None),
                        ("children", []), ("N", 1), ("V", 0.0), ("eval_value", 0.0)):
        if not hasattr(root, field):
            bad("a fresh Node has no attribute `%s`" % field)
            hint("__init__ sets seven things: state, parent, action, children, N, V, "
                 "eval_value")
            return report("Exercise, the Node class", False)
        got = getattr(root, field)
        if field == "N" and got != 1:
            bad("a fresh Node has N = %r, it should be 1" % got)
            hint("born at 1, so that log(parent.N) is defined on the very first pass")
            passed = False
        elif field in ("V", "eval_value") and got != 0.0:
            bad("a fresh Node has %s = %r, it should be 0.0" % (field, got))
            passed = False
        elif field in ("state", "parent", "action", "children") and got != want:
            bad("a fresh Node has %s = %r, expected %r" % (field, got, want))
            passed = False
    if passed:
        ok("state, parent, action, children, N = 1, V = 0.0, eval_value = 0.0")

    kid = cls(at(0, ["goto_site[people]"]), root, "goto_site[people]")
    if kid.parent is not root:
        bad("Node(state, root, action).parent is not the root you passed in")
        hint("backprop and path_to_root both walk up through parent, so it has to be "
             "stored")
        passed = False
    elif kid.action != "goto_site[people]":
        bad("the third argument is the action that led here, and it came out as %r"
            % kid.action)
        passed = False
    else:
        ok("a child remembers its parent and the action that made it")

    # children must be a fresh list per node, or expand() on one node silently appends
    # to another. This is the classic mutable default, and it is invisible until the
    # tree makes no sense.
    a, b = cls(portal, None), cls(portal, None)
    a.children.append(kid)
    if len(b.children) != 0:
        bad("appending to one Node's children changed another Node's children")
        hint("write `self.children = []` in __init__, so each node gets its own list. "
             "A list built once and shared is one tree pretending to be many")
        passed = False
    else:
        ok("each Node gets its own children list")

    # UCT
    parent = cls(portal, None)
    parent.N = 100
    child = cls(at(0, ["goto_site[people]"]), parent, "goto_site[people]")
    child.N, child.V = 25, 0.6
    got = child.UCT(W)
    if not _number(got):
        bad("UCT returned %r, so the gap is still empty" % (got,))
        return report("Exercise, the Node class", False)
    want = 0.6 + 1.0 * math.sqrt(math.log(100) / 25)
    if abs(got - want) > 1e-6:
        bad("with V = 0.600, N = 25 and parent.N = 100 you got %.6f, expected %.6f"
            % (got, want))
        hint("exploit = self.V")
        hint("explore = w * sqrt( log(self.parent.N) / self.N )")
        if abs(got - (0.6 + math.sqrt(math.log(25) / 100))) < 1e-6:
            hint("you have self.N and self.parent.N the wrong way round. The PARENT's "
                 "count goes inside the log")
        if abs(got - (0.6 + math.log(100) / 25)) < 1e-6:
            hint("the square root is missing")
        if abs(got - (0.6 + math.sqrt(math.log(100)) / 25)) < 1e-6:
            hint("the whole fraction goes inside the square root, not just the log")
        if abs(got - 0.6) < 1e-9:
            hint("that is V alone, which is the one thing UCT is not")
        passed = False
    else:
        ok("UCT matches the formula, %.5f" % got)

    if abs(child.UCT(0.0) - 0.6) > 1e-9:
        bad("with w = 0 you got %.5f, expected V itself, 0.600" % child.UCT(0.0))
        hint("w multiplies the second term only, so turning it to 0 has to leave the "
             "value behind. Turning it up and down is how the search is made to "
             "explore more or less")
        passed = False
    else:
        ok("w = 0 leaves V alone, so the second term really is weighted by w")

    fresh_root = cls(portal, None)
    only = cls(at(0, ["goto_site[it]"]), fresh_root, "goto_site[it]")
    only.V = 0.42
    if abs(only.UCT(W) - 0.42) > 1e-9:
        bad("at parent.N = N = 1 you got %.5f, expected V itself, 0.420" % only.UCT(W))
        hint("log(1) = 0, so before anything has been tried UCT is nothing but the "
             "model's opinion. An infinity or a crash means something divides by N - 1")
        passed = False
    else:
        ok("before anything is tried UCT is V exactly, because log(1) = 0")

    quiet = cls(at(0, ["goto_site[people]"]), parent, "goto_site[people]")
    quiet.N, quiet.V = 25, 0.6
    loud = cls(at(0, ["goto_site[it]"]), parent, "goto_site[it]")
    loud.N, loud.V = 2, 0.6
    if not loud.UCT(W) > quiet.UCT(W):
        bad("two children with equal V, and the rarely visited one did not score higher")
        hint("that is what the explore term is for")
        passed = False
    else:
        ok("between equal V, the less visited child scores higher")
    return report("Exercise, the Node class", passed)


# --- exercise checker (notebook cell 31) ---

class _StubLM:
    """Not the frozen model: a stand in whose numbers the CHECKER chooses.

    Only the checkers ever use this. It exists so that a check can be exact arithmetic
    rather than an opinion about what a real model should have said.

    value(state) always answers `lm_value`. A self consistency vote (draw 1 and up)
    answers from `votes`, anything else answers from `script`. Every propose is recorded
    in `asked`, so a checker can see what it was asked for.
    """

    def __init__(self, lm_value=0.5, script=(), votes=(), note="a stub reflection."):
        self._lm_value = float(lm_value)
        self.script = list(script)
        self.votes = list(votes)
        self.note = note
        self.asked = []
        self.value_calls = 0
        self.calls = 0

    def value(self, state):
        self.value_calls += 1
        self.calls += 1
        return self._lm_value

    def propose(self, state, n=1, draw=0, memory=None, greedy=False,
                answers_only=False):
        self.calls += 1
        self.asked.append({"n": n, "draw": draw, "memory": memory,
                           "answers_only": answers_only})
        if draw > 0 and self.votes:
            return [self.votes[(draw - 1) % len(self.votes)]]
        picked = list(self.script[:n])
        if answers_only:
            picked = [a for a in picked if a.startswith("answer[")]
        return picked

    def reflect(self, state, reward, trajectory=None):
        self.calls += 1
        self.asked.append({"reflect": True, "trajectory": trajectory})
        return self.note


def _kids(n):
    return "1 child" if n == 1 else "%d children" % n


def check_compute_V(fn):
    _bind()
    print("checking your compute_V ...\n")
    passed = True

    # LM(s) = 0.800, and three of the four votes agree, so SC(s) = 0.750.
    stub = _StubLM(lm_value=0.8, votes=["next", "next", "next", "follow[1]"])
    state = at(0, ["goto_site[facilities]"])
    node = Node(state)

    got = _using(stub, fn, node)
    if not _number(got):
        bad("compute_V returned %r, so the gap is still empty" % (got,))
        hint("V(s) = lam LM(s) + (1 - lam) SC(s), and the two names above the gap "
             "already hold LM(s) and SC(s)")
        return report("Exercise, the value blend V(s)", False)

    want = 0.5 * 0.8 + 0.5 * 0.75                     # 0.775
    if abs(got - want) > 1e-9:
        bad("with LM(s) = 0.800, SC(s) = 0.750 and lam = 0.5 you got %.4f, expected %.4f"
            % (got, want))
        if abs(got - 0.8) < 1e-9:
            hint("that is LM(s) on its own")
        if abs(got - 0.75) < 1e-9:
            hint("that is SC(s) on its own")
        if abs(got - 1.55) < 1e-9:
            hint("you added them without the weights. V(s) has to stay in [0,1]")
        hint("V(s) = lam LM(s) + (1 - lam) SC(s)")
        passed = False
    else:
        ok("blends correctly at lam = 0.5, V(s) = %.3f" % got)

    # At lam = 0.5 the two terms are interchangeable, so the swap is invisible above.
    # Ask again at lam = 0.8, where it is not.
    try:
        got8 = _using(stub, fn, Node(state), lam=0.8)
    except TypeError as e:
        bad("compute_V(node, lam=0.8) raised TypeError: %s" % e)
        hint("keep the signature compute_V(self, mem=None, lam=LAM), so that lam can be "
             "turned up and down")
        return report("Exercise, the value blend V(s)", False)
    want8 = 0.8 * 0.8 + 0.2 * 0.75                    # 0.790
    if abs(got8 - want8) > 1e-9:
        bad("at lam = 0.8 you got %.4f, expected %.4f" % (got8, want8))
        if abs(got8 - (0.8 * 0.75 + 0.2 * 0.8)) < 1e-9:
            hint("the two are the wrong way round: lam multiplies LM(s), the model's "
                 "own opinion, and 1 - lam multiplies SC(s)")
        if abs(got8 - want) < 1e-9:
            hint("that is the lam = 0.5 answer again, so lam is not being used")
        passed = False
    else:
        ok("lam really does the weighting, V(s) = %.3f at lam = 0.8" % got8)

    corners = True
    for lam, want_c, why in ((1.0, 0.8, "lam = 1 is LM(s) alone, the model's opinion "
                                        "with no second opinion in it"),
                             (0.0, 0.75, "lam = 0 is SC(s) alone, agreement with no "
                                         "opinion in it")):
        got_c = _using(stub, fn, Node(state), lam=lam)
        if abs(got_c - want_c) > 1e-9:
            bad("at lam = %.1f you got %.4f, expected %.4f" % (lam, got_c, want_c))
            hint(why)
            corners = passed = False
    if corners:
        ok("the two corners are exact: lam = 1 gives LM(s), lam = 0 gives SC(s)")

    # The number has to land ON THE NODE. UCT reads node.V, so a compute_V that returns
    # the right number and stores nothing leaves the whole search exploring blind.
    if abs(node.V - want) > 1e-9:
        bad("compute_V returned %.3f but left node.V at %r" % (got, node.V))
        hint("assign it: self.V = ... . UCT reads self.V, so a value that is not "
             "stored never reaches the search at all")
        passed = False
    elif abs(node.eval_value - want) > 1e-9:
        bad("node.V is right but node.eval_value is %r" % node.eval_value)
        hint("the `self.eval_value = self.V` line under the gap keeps a frozen copy of "
             "the guess, so the table at the end can show how far the truth moved it. "
             "Leave it where it is")
        passed = False
    else:
        ok("the guess is stored on the node, V = eval_value = %.3f" % node.V)

    # The terminal case is given, and it has to survive. At a terminal node the
    # environment has already paid, so there is nothing left to guess. The two numbers
    # are deliberately different, so an implementation that asks the model anyway
    # cannot land on the right answer by accident.
    stub_t = _StubLM(lm_value=0.2, votes=["next"])
    ended = Node(at(0, TABLE + ["answer[room N-310]"]))
    got_t = _using(stub_t, fn, ended)
    if not _number(got_t) or abs(got_t - 0.8) > 1e-9 or stub_t.value_calls:
        bad("that trajectory answered `room N-310`, which the environment pays 0.800 "
            "for, and you returned %r%s"
            % (got_t, ", after asking the model for an opinion"
               if stub_t.value_calls else ""))
        hint("the `if is_terminal(self.state)` line above the gap answers with "
             "reward_of(self.state), the number the environment already paid, and never "
             "asks the model. Leave it where it is")
        passed = False
    else:
        ok("a terminal node keeps the environment's own 0.800, unasked")

    live = Node(at(0, TABLE))
    v = fn(live)
    print("\n  and on a real page, the coffee lounge table on question 1:")
    print("    LM(s) = %.3f   SC(s) = %.3f   V(s) = %.3f"
          % (LM.value(live.state), self_consistency(live.state), v))
    print("    (that page has four rows and the question names none of them)")
    return report("Exercise, the value blend V(s)", passed)


# --- exercise checker (notebook cell 35) ---

def _tree(n_children=3, query_idx=0):
    """A root with `n_children` real children, for the checkers to walk over."""
    root = Node(intranet.initial_state(query_idx), None)
    for key in ("people", "facilities", "it", "products", "policies")[:n_children]:
        action = "goto_site[%s]" % key
        root.children.append(Node(at(query_idx, [action]), root, action))
    return root


def check_best_child(fn):
    _bind()
    print("checking your best_child_by_uct ...\n")
    passed = True

    parent = _tree(3)
    parent.N = 100
    for child, (n, v) in zip(parent.children, ((25, 0.90), (25, 0.10), (2, 0.50))):
        child.N, child.V = n, v

    got = fn(parent, W)
    if got is Ellipsis or got is None:
        bad("it returned %r, so the gap is still empty" % (got,))
        return report("Exercise, best_child_by_uct", False)
    if got not in parent.children:
        bad("it returned something that is not one of s.children")
        hint("return the child itself, not its score")
        return report("Exercise, best_child_by_uct", False)

    scores = [c.UCT(W) for c in parent.children]
    best = parent.children[scores.index(max(scores))]
    if got is not best:
        bad("you picked the child scoring %.3f, but %.3f was on offer"
            % (got.UCT(W), max(scores)))
        hint("the three scored %s" % ", ".join("%.3f" % s for s in scores))
        passed = False
    else:
        ok("picks the highest UCT, %.3f" % got.UCT(W))

    # The winner above happens to be the LAST child, so a gap left as `...` would pass
    # it: Ellipsis is truthy, so the `if` always fires and the loop returns children[-1].
    # Here the winner is the FIRST child, which that cannot get right.
    front = _tree(3)
    front.N = 100
    for child, v in zip(front.children, (0.90, 0.10, 0.50)):
        child.N, child.V = 25, v
    if fn(front, W) is not front.children[0]:
        bad("three equally visited children at V = 0.900, 0.100 and 0.500, and you did "
            "not return the first")
        hint("if the gaps are still `...`, the condition is Ellipsis, which is truthy, "
             "so every child looks better than the one before and you always get the "
             "last one")
        passed = False
    else:
        ok("and picks it when it is the first child, not only when it is the last")

    # The negative score trap the pseudocode calls out, and the reason correction [14]
    # is in that file. Two children, BOTH scoring below -1, and the better one second:
    # a seed of -1 leaves best_child stuck on the first child and nobody notices.
    p2 = _tree(2)
    p2.N = 2
    p2.children[0].N, p2.children[0].V = 40, -5.0
    p2.children[1].N, p2.children[1].V = 40, -2.0
    if fn(p2, W) is not p2.children[1]:
        bad("two children scoring %.2f and %.2f, and you did not return the second"
            % (p2.children[0].UCT(W), p2.children[1].UCT(W)))
        hint("start best_uct from the FIRST child's score, never from -1 or 0: a UCT "
             "score can be negative, and then no child ever beats the seed and you "
             "always return children[0]")
        passed = False
    else:
        ok("survives two negative UCT scores")
    return report("Exercise, best_child_by_uct", passed)


def check_descend(fn):
    _bind()
    print("checking your descend ...\n")
    passed = True

    # A node with no children is where this attempt works, so it comes back unchanged.
    bare = Node(intranet.initial_state(0), None)
    try:
        landed = fn(bare, W)
    except IndexError:
        bad("descend crashed on a node with no children")
        hint("the condition is `len(s.children) > 0`. While the gap is still `...` the "
             "condition is Ellipsis, which is truthy, so it descends unconditionally and "
             "asks for the best child of a node that has none")
        return report("Exercise, descend", False)
    if landed is not bare:
        bad("a node with no children should be returned unchanged: it is exactly the "
            "node that still has to be expanded")
        hint("the whole condition is `len(s.children) > 0`")
        return report("Exercise, descend", False)
    ok("stops at a node that has not been expanded yet")

    # One level down.
    root = _tree(3)
    root.N = 4
    for child, v in zip(root.children, (0.2, 0.9, 0.4)):
        child.V, child.N = v, 2
    got = fn(root, W)
    if got is root:
        bad("the root has children, so descend should have gone down")
        passed = False
    elif got not in root.children:
        bad("descend returned a node that is not a child of the root")
        passed = False
    elif got is not root.children[1]:
        bad("it went into %r, and %r had the higher UCT"
            % (got.action, root.children[1].action))
        hint("descend takes best_child_by_uct at every level, and that is the piece you "
             "just wrote")
        passed = False
    else:
        ok("descends into the best child, %s" % got.action)

    # Two levels: it has to keep going, not stop at the first child.
    deep = root.children[1]
    for action in ("next", "prev"):
        deep.children.append(Node(at(0, [deep.action, "next"]), deep, action))
    deep.N = 3
    deep.children[0].V, deep.children[0].N = 0.1, 2
    deep.children[1].V, deep.children[1].N = 0.8, 2
    got = fn(root, W)
    if got is deep:
        bad("it stopped at a node that has children of its own")
        hint("descend calls ITSELF on the child it picked: `return descend(best, w)`. "
             "One step down is selection that never reaches the frontier")
        passed = False
    elif got is not deep.children[1]:
        bad("two levels down it landed on %r" % (got.action,))
        passed = False
    else:
        ok("keeps descending while there are children, and lands two levels down")

    # A terminal node has no children either, so the same one line condition returns it.
    # This is the case the game version needed a second clause for, and here it is free.
    ended = Node(at(0, TABLE + ["answer[N-310]"]), None)
    if fn(ended, W) is not ended:
        bad("a finished trajectory should be returned as is")
        hint("an answered node has no children, so `len(s.children) > 0` is already "
             "False and there is nothing more to write")
        passed = False
    else:
        ok("returns a finished trajectory unchanged, with no extra clause needed")
    return report("Exercise, descend", passed)


# --- exercise checker (notebook cell 43) ---

def _standin_compute_V(self, mem=None, lam=None, **_kw):
    """Let check_expand run before evaluation is written.

    Expansion calls `child.compute_V`. Until that method exists, a terminal child
    gets the environment's reward (the given branch of compute_V) and any other
    child gets a non-zero placeholder, so the checker can see that expand scored
    it. The real blend is the Evaluation exercise.
    """
    if is_terminal(self.state):
        self.V = reward_of(self.state)
    else:
        self.V = 0.5
    self.eval_value = self.V
    return self.V


def check_expand(fn):
    _bind()
    print("checking your expand ...\n")
    node_cls = _nb().Node
    saved = node_cls.compute_V
    node_cls.compute_V = _standin_compute_V
    try:
        return _check_expand_body(fn)
    finally:
        node_cls.compute_V = saved


def _check_expand_body(fn):
    passed = True
    landing = at(0, ["goto_site[facilities]"])          # a page with three links
    script = ["next", "goto_site[people]", "follow[1]"]

    node = Node(landing)
    try:
        _using(_StubLM(script=script), fn, node, 3, None)
    except TypeError as e:
        # An unfilled gap is `... `, and four names cannot be unpacked from Ellipsis.
        bad("it raised TypeError: %s" % e)
        hint("the gap is probably still `...`. step(s.state, action) hands back exactly "
             "the four things the line expects: the new state, the reward, whether the "
             "episode ended, and an info dictionary")
        return report("Exercise, expansion", False)
    if not node.children:
        bad("expand built no children at all, so the gap is still empty")
        hint("propose_actions(s.state, n_actions, mem) hands back the actions")
        return report("Exercise, expansion", False)
    if len(node.children) != 3:
        bad("the policy proposed 3 legal actions and you built %s"
            % _kids(len(node.children)))
        passed = False
    else:
        ok("one child per proposed action, all %d at once" % len(node.children))

    shape = True
    for child, action in zip(node.children, script):
        if child.action != action:
            bad("a child records action %r, the policy proposed %r"
                % (child.action, action))
            shape = False
        elif child.parent is not node:
            bad("the child for %r does not point back at the node it came from" % action)
            hint("Node(new_state, s, action). Backpropagation walks up through parent")
            shape = False
        elif child.state != step(landing, action)[0]:
            bad("the child for %r does not hold the state the environment returned"
                % action)
            hint("play the action with step(s.state, action) and keep the state it "
                 "hands back. A child holding its parent's state is a node that never "
                 "moved")
            shape = False
    passed = passed and shape
    if shape:
        ok("every child knows its action, its parent and its own state")

    if all(child.V == 0.0 for child in node.children):
        bad("every child still has V = 0.0, so nothing was evaluated")
        hint("child.compute_V(mem) on each child, before you append it. That is "
             "operation 3, and in LATS it happens INSIDE expansion: a child is worth "
             "something the moment it exists. You can call it before you write it; "
             "the checker supplies a stand-in until Evaluation is filled in")
        passed = False
    else:
        ok("every child was scored with compute_V")

    smaller = Node(landing)
    _using(_StubLM(script=script), fn, smaller, 2, None)
    if len(smaller.children) != 2:
        bad("asked for n_actions = 2 you built %s" % _kids(len(smaller.children)))
        hint("n_actions has to reach propose_actions, otherwise the budget sweep at the "
             "end of the notebook sweeps nothing")
        passed = False
    else:
        ok("n_actions reaches the policy")

    # Expanded once, and never again. Without this the search double expands: `lats`
    # expands the leaf and then `simulate` expands the same leaf, so it would get 2n
    # children and pay for them twice.
    twice = Node(landing)
    _using(_StubLM(script=script), fn, twice, 3, None)
    before = len(twice.children)
    _using(_StubLM(script=script), fn, twice, 3, None)
    if len(twice.children) != before:
        bad("expanding the same node twice took it from %s to %s"
            % (_kids(before), _kids(len(twice.children))))
        hint("the `or len(s.children) > 0` half of the guard above the gap is what "
             "stops that. Leave it where it is")
        passed = False
    else:
        ok("a node already expanded is left alone, %s" % _kids(before))

    refused = Node(landing)
    _using(_StubLM(script=["follow[99]", "next", "goto_site[nowhere]"]),
           fn, refused, 3, None)
    if len(refused.children) != 1 or refused.children[0].action != "next":
        bad("of three proposals the environment accepts exactly one, and you built %s"
            % _kids(len(refused.children)))
        hint('info["illegal"] is True for an action the environment refused. A child '
             'built from one is a node pretending the action worked, and the search '
             'would spend real attempts on it')
        hint("this page has three links, so follow[99] is refused, and there is no site "
             "called nowhere")
        passed = False
    else:
        ok("drops the proposals the environment refused")

    # The three answers below are all submitted from the SAME page, the coffee lounge
    # table. The environment scores the text, not the page, and the three rewards are
    # what makes this check able to fail: a child that kept its default 0.000 passes
    # only on the wrong row.
    table_state = at(0, TABLE)
    for text, want_reward, why in (("N-310", 1.0, "the row the question wants"),
                                   ("room N-310", 0.8, "the same row, loosely worded"),
                                   ("S-121", 0.0, "another row of the same table")):
        ending = Node(table_state)
        _using(_StubLM(lm_value=0.4, script=["answer[%s]" % text]), fn, ending, 1, None)
        if not ending.children:
            bad("the policy proposed answer[%s] and no child was built for it" % text)
            passed = False
            continue
        child = ending.children[0]
        if not is_terminal(child.state):
            bad("answer[%s] ends the episode and the child it made is not terminal"
                % text)
            hint("keep the state step(...) handed back: it carries done and reward")
            passed = False
        elif abs(child.V - want_reward) > 1e-9:
            bad("answer[%s] is worth %.3f in the environment and its child came out at "
                "V = %.3f" % (text, want_reward, child.V))
            hint("compute_V already handles this: at a terminal node it takes "
                 "reward_of(state) rather than asking the model. If you see the model's "
                 "0.400 here, compute_V was never called on the child")
            passed = False
        else:
            ok("answer[%s] makes a terminal child worth %.3f, %s"
               % (text, want_reward, why))

    note = _StubLM(script=["next"])
    marker = object()                       # a sentinel: any object at all will do
    _using(note, fn, Node(landing), 1, marker)
    if not note.asked or note.asked[-1]["memory"] is not marker:
        bad("the mem argument did not reach the policy")
        hint("reflection, the last piece of the loop, works by changing what the policy "
             "proposes. If mem stops here it can never do anything")
        passed = False
    else:
        ok("hands mem on to the policy, which is how reflection works later")

    ended = Node(at(0, TABLE + ["answer[N-310]"]))
    _using(_StubLM(script=["next"]), fn, ended, 3, None)
    if ended.children:
        bad("it expanded a trajectory that had already answered")
        hint("the `if is_terminal(s.state)` half of the guard above the gap. There is "
             "nothing to do after an answer")
        passed = False
    else:
        ok("never expands a finished trajectory")

    # Sampled, NOT ranked. The two agree at plenty of states, so hunt for one where they
    # genuinely differ and judge only there.
    for query_idx, actions in ((0, []), (0, ["goto_site[facilities]"]),
                               (1, []), (3, ["goto_site[products]"])):
        probe_state = at(query_idx, actions)
        sampled = LM.propose(probe_state, n=3)
        ranked = LM.propose(probe_state, n=3, greedy=True)
        if set(sampled) == set(ranked):
            continue
        probe = Node(probe_state)
        fn(probe, 3, None)
        got = [c.action for c in probe.children]
        if got == sampled:
            ok("asks the policy for a SAMPLE of 3, not for its top 3")
        elif set(got) == set(ranked):
            bad("you expanded the policy's top 3 actions instead of a sample")
            hint("greedy=True is the baseline from section 1, not the search. If every "
                 "expansion takes the same top n, every draw agrees with every other, "
                 "SC(s) is 1.000 everywhere and the tree stops branching")
            passed = False
        else:
            bad("the children are %s, the policy sampled %s" % (got, sampled))
            passed = False
        break
    else:
        ok("(no state found where a sample and a ranking differ, so untested)")
    return report("Exercise, expansion", passed)


# --- exercise checker (notebook cell 48) ---

def _reachable(node, root):
    """True if `node` hangs off `root` through parent links."""
    walker = node
    while walker is not None:
        if walker is root:
            return True
        walker = walker.parent
    return False


def check_simulate(fn):
    _bind()
    print("checking your simulate ...\n")
    passed = True

    # One step to the end. The policy offers a page turn and an answer; the answer is
    # terminal, so compute_V gave it the environment's 1.000, and 1.000 beats any
    # opinion the model can have about a page.
    start = Node(at(0, TABLE))
    stub = _StubLM(lm_value=0.4, script=["next", "answer[N-310]"])
    got = _using(stub, fn, start, 2, None)

    if got is None or got is Ellipsis:
        bad("it returned %r, so the gap is still empty" % (got,))
        hint("simulate RETURNS the node it stopped on, and every branch has to return "
             "something")
        return report("Exercise, simulation", False)
    if not hasattr(got, "state"):
        bad("it returned %r, which is not a Node" % (got,))
        hint("return the node, not its state and not the reward")
        return report("Exercise, simulation", False)
    if not is_terminal(got.state):
        bad("it stopped on a node that is not terminal")
        hint("keep walking while there is somewhere to walk: the last line is "
             "`return simulate(best, n_actions, mem)`")
        passed = False
    elif abs(reward_of(got.state) - 1.0) > 1e-9:
        bad("it walked to a terminal node worth %.3f when 1.000 was one action away"
            % reward_of(got.state))
        hint("best_child_by_value picks the child with the largest V, and a terminal "
             "child carries what the environment paid")
        passed = False
    else:
        ok("walks to the answer the values point at, worth %.3f"
           % reward_of(got.state))

    if not _reachable(got, start):
        bad("the node it returned is not in the tree: nothing links it back to where "
            "the walk began")
        hint("simulate creates REAL nodes, unlike this morning's rollout. It calls "
             "expand, which hangs children on the tree, and then walks into one of "
             "them. That is what lets backprop climb afterwards")
        passed = False
    else:
        ok("the node it returned hangs off the tree, so backprop can climb from it")

    if not start.children:
        bad("the node it started from has no children, so nothing was expanded")
        hint("simulate calls expand(s, n_actions, mem) before it chooses")
        passed = False
    else:
        ok("it expanded as it walked, %s at the first step" % _kids(len(start.children)))

    # A trajectory that is already over comes straight back.
    ended = Node(at(0, TABLE + ["answer[S-121]"]))
    if _using(_StubLM(script=["next"]), fn, ended, 2, None) is not ended:
        bad("a node that has already answered should be returned as it is")
        hint("`if is_terminal(s.state): return s` is the first line")
        passed = False
    else:
        ok("returns an already finished trajectory unchanged")

    # Several steps, and this one has to terminate on its own. The stub only ever says
    # `next`, so the walk pages through the site until the environment refuses, and
    # then there is no child to walk into.
    walker = Node(at(0, ["goto_site[facilities]"]))
    landed = _using(_StubLM(script=["next"]), fn, walker, 1, None)
    depth = 0
    node = landed
    while node.parent is not None:
        depth += 1
        node = node.parent
    if depth < 2:
        bad("paging `next` from the facilities landing page stopped after %d step%s"
            % (depth, "" if depth == 1 else "s"))
        hint("the recursion is the walk: `return simulate(best, n_actions, mem)`")
        passed = False
    else:
        ok("walks on for as long as there is somewhere to go, %d nodes deep" % depth)

    if landed.children:
        bad("it stopped on a node that has children, so it had somewhere to go")
        passed = False
    else:
        ok("stops where there is nothing left to walk into")

    # Deliberately NOT checked: what the walk scores on the real model. That is a fact
    # about the model, not about your six lines, and a real model is entitled to a
    # different answer than a stub.
    return report("Exercise, simulation", passed)


# --- exercise checker (notebook cell 52) ---

def check_backprop(fn):
    _bind()
    print("checking your backprop ...\n")
    passed = True

    root = Node(intranet.initial_state(0), None)
    mid = Node(at(0, ["goto_site[people]"]), root, "goto_site[people]")
    leaf = Node(at(0, ["goto_site[people]", "next"]), mid, "next")
    root.children, mid.children = [mid], [leaf]
    named = (("the leaf", leaf), ("its parent", mid), ("the root", root))

    fn(leaf, 1.0)
    if root.N == 1 and mid.N == 1:
        bad("nothing above the leaf changed, so it never walked up")
        hint("recurse on node.parent while it is not None")
        return report("Exercise, backpropagation", False)

    counted = True
    for name, node in named:
        if node.N != 2:
            bad("%s has N = %r after one backup, expected 2 (every node starts at 1)"
                % (name, node.N))
            counted = passed = False
    if counted:
        ok("all three nodes on the path counted the attempt")

    averaged = True
    for name, node in named:
        if not _number(node.V) or abs(node.V - 0.5) > 1e-9:
            bad("%s has V = %r after one reward of 1.000, expected 0.500"
                % (name, node.V))
            averaged = passed = False
    if averaged:
        ok("the running mean is right at all three, V = 0.500")
    else:
        hint("a fresh node is N = 1, V = 0, so once N is 2 the mean is "
             "(0 * 1 + 1.0) / 2 = 0.5")
        hint("1.000 means you either overwrote V with the reward or divided by the OLD "
             "N. The update runs after N has gone up")

    # THE ONE LINE THAT IS DIFFERENT FROM THIS MORNING. In tic tac toe the parent
    # belongs to the opponent, so the reward flipped: backprop(node.parent, 1.0 - r).
    # Answering a question is single agent. The SAME r goes all the way up.
    if _number(mid.V) and abs(mid.V - 0.0) < 1e-9:
        bad("the leaf's parent came out at 0.000, which is 1.0 - r, this morning's flip")
        hint("that flip is the two player game's problem, not this one. Nobody is "
             "playing against you here: the same r applies to every node on the path, "
             "so the recursive call is backprop(node.parent, r)")
        passed = False

    fn(leaf, 0.0)
    if not _number(root.V) or abs(root.V - 1.0 / 3.0) > 1e-9:
        bad("after rewards 1.000 then 0.000 the root has V = %r, expected %.4f"
            % (root.V, 1.0 / 3.0))
        hint("N is 3 by now, so V = (0.5 * 2 + 0.0) / 3")
        hint("1.000 is a running TOTAL rather than a mean, and 0.000 is the last reward "
             "overwriting everything before it")
        passed = False
    else:
        ok("a second reward averages in, V = %.4f over the two" % root.V)

    # Those two rewards are not decoration. 1.000 and 0.000 are exactly what the
    # environment pays for two rows of one table, so this is the case the search really
    # meets: the same page, twice, and only the reward tells them apart.

    # Evaluation seeded the child with the model's guess, so the first real reward has
    # to average INTO that guess rather than land on top of it.
    seeded = Node(at(0, ["goto_site[facilities]"]))
    seeded.V = seeded.eval_value = 0.4
    fn(seeded, 1.0)
    if not _number(seeded.V) or abs(seeded.V - 0.7) > 1e-9:
        bad("a node the evaluation had seeded at V = 0.400 came out at %r after a "
            "reward of 1.000, expected 0.700" % seeded.V)
        hint("(0.4 * 1 + 1.0) / 2 = 0.7. The value already there is part of the mean, "
             "so that first backup is the model's guess meeting the truth")
        passed = False
    elif abs(seeded.eval_value - 0.4) > 1e-9:
        bad("backprop changed eval_value to %r" % seeded.eval_value)
        hint("eval_value is what the model thought, and the table at the end prints it "
             "next to V to show how far the truth moved it. Leave it alone")
        passed = False
    else:
        ok("averages the real reward into the value evaluation had seeded")

    lone = Node(intranet.initial_state(0), None)
    try:
        fn(lone, 1.0)
    except AttributeError:
        bad("it crashed on a node with no parent")
        hint("recurse only `if node.parent is not None`")
        return report("Exercise, backpropagation", False)
    ok("it stops cleanly at the root")
    return report("Exercise, backpropagation", passed)


def check_reflect(fn):
    _bind()
    print("checking your reflect ...\n")
    passed = True

    # A real failure to talk about: the right page, the wrong row of it. Built as a real
    # CHAIN of nodes, because path_to_root climbs parents and a lone node has none.
    attempt = TABLE + ["answer[S-121]"]
    leaf = Node(intranet.initial_state(0), None)
    for i, action in enumerate(attempt):
        leaf = Node(at(0, attempt[:i + 1]), leaf, action)
    r = reward_of(leaf.state)
    mem = Memory()
    stub = _StubLM(note="Reading the lounges table was right, but S-121 was the wrong "
                        "row: find which building the Vega team sits in first.")
    _using(stub, fn, leaf, r, mem)

    if not mem.notes:
        bad("nothing was written: mem.notes is still empty")
        hint("ask the frozen model for the sentence with LM.reflect(...), then hand it "
             "to mem.add(note, leaf.state, r)")
        return report("Exercise, reflection", False)
    note = mem.notes[0]
    if not isinstance(note, str) or not note.strip():
        bad("what was filed is %r, which is not a sentence" % (note,))
        return report("Exercise, reflection", False)
    ok("it wrote a note, %d characters of it" % len(note))

    # The trajectory has to reach the critic. A reflection on one state cannot say what
    # to do differently, because it cannot see what was done.
    reflected = [a for a in stub.asked if a.get("reflect")]
    if not reflected:
        bad("LM.reflect was never called, so the sentence did not come from the model")
        passed = False
    elif not reflected[-1]["trajectory"]:
        bad("LM.reflect was called without the trajectory")
        hint("path_to_root(leaf) is the whole attempt, root first, and this is the ONE "
             "operation that needs it. The paper's prompt takes the trajectory and the "
             "final reward")
        passed = False
    elif list(reflected[-1]["trajectory"]) != path_to_root(leaf):
        bad("the trajectory handed to the critic was %r" % (reflected[-1]["trajectory"],))
        hint("pass path_to_root(leaf) exactly")
        passed = False
    else:
        ok("the critic was shown the whole attempt, %d actions"
           % len(reflected[-1]["trajectory"]))

    if answer_of(leaf.state) not in mem.tried:
        bad("mem.tried does not know that %r was already tried"
            % answer_of(leaf.state))
        hint("mem.add(note, leaf.state, r) records that for you, so pass it all three "
             "things and not just the sentence")
        passed = False
    else:
        ok("the answer is on record as tried, at %.2f" % mem.tried[answer_of(leaf.state)])

    action = "answer[%s]" % answer_of(leaf.state)
    before = Memory().penalty(leaf.state, action)
    after = mem.penalty(leaf.state, action)
    if not after < before:
        bad("after the note that answer still carries a weight of %.2f, so the next "
            "attempt has no reason to stop repeating it" % after)
        hint("that is what mem.add is for: a note is a sentence, and what a model DOES "
             "with a sentence it has been shown is stop repeating what the sentence "
             "says failed")
        passed = False
    else:
        ok("the next sample discounts that answer, %.2f down to %.2f" % (before, after))

    # A trajectory that ran out of steps never answered anything, so there is nothing
    # to say about it.
    ran_out = Node(dict(leaf.state))
    ran_out.state["answer"] = None
    quiet = Memory()
    _using(_StubLM(), fn, ran_out, 0.0, quiet)
    if quiet.notes:
        bad("it wrote a note about a trajectory that never answered anything")
        hint("if answer_of(leaf.state) is None the trajectory ran out of steps. Return "
             "early")
        passed = False
    else:
        ok("a trajectory that ran out of steps without answering gets no note")

    try:
        _using(_StubLM(), fn, leaf, r, None)
    except Exception as e:
        bad("with reflection switched off (mem is None) it raised %s: %s"
            % (type(e).__name__, e))
        hint("`if mem is None: return` is how reflection gets switched off")
        passed = False
    else:
        ok("with mem None it does nothing, so reflection can be switched off")

    # NOT checked: what the sentence SAYS. A real model writes prose and is free to
    # write it however it likes, so a checker that insisted on the failed answer
    # appearing verbatim would be grading the model rather than your code.
    return report("Exercise, reflection", passed)


# --- exercise checker (notebook cell 61) ---

def check_lats(fn):
    _bind()
    print("checking your lats ...\n")
    passed = True
    seen = []

    def record(name, args, result):
        seen.append({"name": name, "args": args, "result": result})

    # Three proposals, and the environment refuses none of them anywhere useful. The
    # answer among them is a wrong row of the right table, so it is worth 0.000: every
    # attempt fails, which is what makes reflection and backpropagation observable.
    stub = _StubLM(lm_value=0.4,
                   script=["next", "goto_site[people]", "answer[S-121]"])
    real = _watching(("descend", "expand", "simulate", "backprop", "reflect"), record)
    try:
        got = _using(stub, fn, intranet.initial_state(0), 2, 3, W, Memory())
    except Exception as e:
        bad("it raised %s: %s" % (type(e).__name__, e))
        hint("a 🎯 gap is probably still a bare `...`, either this one or one above it")
        return report("Exercise, the whole search", False)
    finally:
        _restore(real)

    if not seen:
        bad("none of the six operations was called, so the gap is still empty")
        return report("Exercise, the whole search", False)

    order = [row["name"] for row in seen]

    # Two attempts were asked for, and each one starts at the root.
    starts = [i for i, name in enumerate(order) if name == "descend"]
    if len(starts) != 2:
        bad("with n_attempts = 2 your loop called descend %d time%s"
            % (len(starts), "" if len(starts) == 1 else "s"))
        hint("the loop is `for attempt in range(n_attempts)`, and every attempt begins with "
             "one descend from the root")
        return report("Exercise, the whole search", False)
    root = seen[starts[0]]["args"][0]
    if seen[starts[1]]["args"][0] is not root:
        bad("the second attempt descended from a different node")
        hint("`root` is built once, before the loop. Every attempt starts there: that "
             "is what makes it a tree and not a list of separate walks")
        passed = False
    else:
        ok("two attempts, each descending from the same root")

    # The order inside one attempt, and what each operation was handed. This is the
    # check that catches a loop whose lines are all present and in the wrong sequence.
    first = order[starts[0]:starts[1]]
    if first[:3] != ["descend", "expand", "simulate"]:
        bad("your first attempt ran %s" % " then ".join(first))
        hint("the order is descend, expand, simulate, then the reward, then reflect and "
             "backprop. Expanding after simulating gives the walk nothing to choose "
             "between; simulating before expanding does the same")
        passed = False
    else:
        ok("selection, then expansion, then simulation")

    leaf = seen[starts[0]]["result"]
    if seen[starts[0] + 1]["args"][0] is not leaf:
        bad("expand was called on a node that is not the one descend returned")
        hint("`leaf = descend(root, exploration_weight)` and then `expand(leaf, n_actions, memory)`. "
             "Expanding anything else grows the tree somewhere the search did not choose")
        passed = False
    elif seen[starts[0] + 2]["args"][0] is not leaf:
        bad("simulate was called on a node that is not the one that was just expanded")
        passed = False
    else:
        ok("expansion and simulation both work on the node selection landed on")

    if len(seen[starts[0] + 1]["args"]) < 3 or seen[starts[0] + 1]["args"][2] is None:
        bad("expand was called without mem")
        hint("expand(leaf, n_actions, mem). Without it the policy never sees a "
             "reflection and operation 6 cannot do anything")
        passed = False
    else:
        ok("mem is handed to expansion, so reflection has a way to act")

    # THE ONE THAT MATTERS MOST. backprop starts where the WALK ended, not where
    # selection stopped, and it carries the number the environment paid.
    ends = [row for row in seen if row["name"] == "simulate"]
    backs = [row for row in seen if row["name"] == "backprop"]
    if not backs:
        bad("backprop was never called, so nothing the attempts learned reached the tree")
        hint("`backprop(end, reward)`, once per attempt, after the reward is read")
        passed = False
    else:
        walked = ends[0]["result"]
        if backs[0]["args"][0] is leaf and walked is not leaf:
            bad("you backed up from the node SELECTION returned, not from where the "
                "walk ended")
            hint("`end = simulate(leaf, n_actions, memory)` is the node the walk ended on, "
                 "exactly like `leaf = expand(leaf)` did this morning. Backing up from the "
                 "old leaf credits the branch above the walk and leaves the walk itself at N = 1")
            passed = False
        elif backs[0]["args"][0] is not walked:
            bad("backprop started from a node that is neither the selected leaf nor the "
                "end of the walk")
            passed = False
        else:
            ok("backpropagation starts where the walk ended")

        want_r = reward_of(walked.state)
        got_r = backs[0]["args"][1]
        if abs(got_r - want_r) > 1e-9:
            bad("you backed up %.3f and the environment paid %.3f for that trajectory"
                % (got_r, want_r))
            if abs(got_r - walked.V) < 1e-9:
                hint("that is V, the model's own guess. Backing up the guess makes the "
                     "search a closed loop with no ground truth in it at all")
            hint("`reward = reward_of(end.state)` after the walk, and that reward is what goes up")
            passed = False
        else:
            ok("what goes up the tree is the environment's number, %.3f" % got_r)

        if root.N != 3:
            bad("after two attempts the root has N = %d, expected 3 (it started at 1)"
                % root.N)
            hint("every attempt ends in one backprop that climbs all the way up")
            passed = False
        else:
            ok("both attempts reached the root, N(root) = 3")

    if not [row for row in seen if row["name"] == "reflect"]:
        bad("reflect was never called, so the second attempt began knowing nothing "
            "about the first")
        hint("`reflect(end, reward, memory)` on an attempt that did not succeed. Both of these "
             "failed, so it should have been called twice")
        passed = False
    else:
        ok("it reflects on an attempt that failed")

    # And the early stop. Now the only action offered is the right answer, worth 1.000,
    # so the first attempt succeeds and a search that keeps going is wasting a budget it
    # has already earned the right to stop spending.
    seen2 = []
    real = _watching(("descend", "reflect"), lambda n, a, r: seen2.append(n))
    try:
        answer = _using(stub.__class__(lm_value=0.4, script=["answer[N-310]"]),
                        fn, intranet.initial_state(0), 4, 1, W, Memory())
    finally:
        _restore(real)

    if seen2.count("descend") != 1:
        bad("the first attempt answered correctly and your loop ran %d attempt%s anyway"
            % (seen2.count("descend"), "" if seen2.count("descend") == 1 else "s"))
        hint("`if reward >= SUCCESS: return answer_of(end.state)`. SUCCESS is 0.9, and this "
             "attempt was paid 1.000")
        passed = False
    elif "reflect" in seen2:
        bad("it reflected on an attempt that succeeded")
        hint("the success return comes BEFORE reflection: there is nothing to say about "
             "an attempt that worked")
        passed = False
    else:
        ok("a success stops the search on the spot, with no reflection")

    if answer != "N-310":
        bad("on that run it returned %r, and the trajectory answered 'N-310'" % (answer,))
        hint("return answer_of(end.state), the text that was actually submitted")
        passed = False
    else:
        ok("it returns the answer the trajectory submitted, %r" % answer)

    # Deliberately NOT checked anywhere above: what any of this SCORES on the real
    # model. That is a fact about the model, not about your eleven lines.
    return report("Exercise, the whole search", passed)

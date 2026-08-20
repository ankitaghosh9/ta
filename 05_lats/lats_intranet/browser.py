"""The clickable intranet: notebook embed and a standalone HTML page.

The notebook calls `explore(0)` and gets the same window you get by opening
`intranet_game.html` in a browser. Both are built from this file, from the live
corpus, so they cannot drift.

    from browser import explore, show_state, walk, reveal, html_path
    explore(0)                          # the embed
    print("fallback:", html_path())     # open this if the embed is blank

`show_state` is the browser drawing used by `walk()`.
"""
import html as html_lib
import json
import os

import intranet
from intranet import (MAX_STEPS, QUERIES, IntranetEnv, SITE_KEYS, SITES, page_at)

N_PAGES = sum(len(SITES[key].pages) for key in SITE_KEYS)

SITE_LABELS = {
    "people": "People",
    "facilities": "Facilities",
    "it": "IT Services",
    "products": "Products",
    "policies": "Policies",
}

HTML_NAME = "intranet_game.html"
EMBED_HEIGHT = 700

_CSS = """
* { box-sizing: border-box; }
.fdd-ui { display: flex; flex-direction: column; width: 100%; height: 100%;
  min-height: 0; overflow: hidden; padding: 8px 10px; font-family: -apple-system, Segoe UI, Roboto, sans-serif;
  font-size: 13px; color: #1a1a1a; }
.fdd-net { font-family: inherit; font-size: 13px; color: #1a1a1a; background: #ffffff;
  border: 1px solid #d7dce2; border-radius: 10px; overflow: hidden; margin: 0;
  width: 100%; flex: 1 1 auto; min-height: 0; display: flex; flex-direction: column; }
.fdd-task { background: #215CAF; color: #ffffff; padding: 10px 14px;
  display: flex; justify-content: space-between; align-items: center; gap: 16px;
  flex: none; flex-wrap: wrap; }
.fdd-q { font-weight: 600; min-width: 0; }
.fdd-meter { display: flex; gap: 2px; align-items: center; white-space: nowrap; }
.fdd-blk { width: 9px; height: 14px; border-radius: 2px; background: #ffffff59; }
.fdd-blk.used { background: #ffffff; }
.fdd-steps { margin-left: 8px; opacity: .85; font-size: 12px; }
.fdd-log { padding: 8px 14px; background: #f7f9fc; border-bottom: 1px solid #e6eaf0;
  flex: none; }
.fdd-act { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12px;
  background: #e8eef7; color: #1c3f6e; border-radius: 4px; padding: 1px 6px; }
.fdd-okd { color: #2f7d4f; }
.fdd-nod { color: #b3261e; }
.fdd-note { padding: 8px 14px; background: #fdecea; color: #8c1d18;
  border-bottom: 1px solid #f5c6c2; flex: none; }
.fdd-done { padding: 8px 14px; background: #eef6ef; color: #1f5132;
  border-bottom: 1px solid #cfe3d4; flex: none; }
.fdd-body { display: flex; align-items: stretch; flex: 1 1 auto; min-height: 0; }
.fdd-pane { width: min(252px, 32%); min-width: 160px; flex: none; background: #f7f9fc;
  border-right: 1px solid #e6eaf0; padding: 8px 0; overflow: auto; }
.fdd-site { padding: 6px 12px; border-left: 3px solid transparent; }
.fdd-site.here { border-left-color: #215CAF; background: #eaf0f9; }
.fdd-site .k { font-weight: 600; }
.fdd-site .b { color: #5a6472; font-size: 11.5px; line-height: 1.35; }
.fdd-site .a { white-space: nowrap; margin-top: 2px; }
.fdd-page { flex: 1; padding: 12px 16px; min-width: 0; min-height: 0; overflow: auto; }
.fdd-crumb { color: #5a6472; font-size: 11.5px; }
.fdd-title { font-size: 16px; font-weight: 650; margin: 2px 0 8px; }
.fdd-line { margin: 3px 0; line-height: 1.45; }
.fdd-links { margin-top: 12px; padding-top: 10px; border-top: 1px dashed #d7dce2; }
.fdd-link { margin: 4px 0; }
.fdd-link a { color: #215CAF; text-decoration: underline; }
.fdd-tgt { color: #5a6472; font-size: 11.5px; }
.fdd-trail { padding: 7px 14px; background: #f7f9fc; border-top: 1px solid #e6eaf0;
  color: #5a6472; font-size: 11.5px; flex: none; }
.fdd-empty { color: #5a6472; font-style: italic; }
.fdd-row { display: flex; flex-wrap: wrap; align-items: center; gap: 6px;
  margin: 6px 0; flex: none; }
.fdd-row b { font-size: 13px; }
.fdd-ui button { font: 13px inherit; padding: 6px 10px; border-radius: 4px;
  border: 1px solid #c5c5c5; background: #f4f4f4; cursor: pointer; }
.fdd-ui button.info { background: #5bc0de; border-color: #46b8da; color: #fff; }
.fdd-ui button.warning { background: #f0ad4e; border-color: #eea236; color: #fff; }
.fdd-ui button.success { background: #5cb85c; border-color: #4cae4c; color: #fff; }
.fdd-ui button.danger { background: #d9534f; border-color: #d43f3a; color: #fff; }
.fdd-ui button:disabled { opacity: .55; cursor: default; }
.fdd-ui input[type=text] { font: 13px inherit; padding: 6px 8px; flex: 1 1 220px;
  min-width: 160px; width: auto; border: 1px solid #ccc; border-radius: 4px; }
.fdd-ui select { font: 13px inherit; padding: 6px 8px; }
.fdd-banner { font: 13px sans-serif; padding: 6px 2px; flex: none; }
@media (max-width: 640px) {
  .fdd-body { flex-direction: column; }
  .fdd-pane { width: 100%; min-width: 0; max-height: 28%; border-right: none;
    border-bottom: 1px solid #e6eaf0; }
}
"""


def _live_notebook():
    try:
        from IPython import get_ipython
        return get_ipython() is not None
    except Exception:
        return False


def _meter(used, total):
    blocks = ""
    for i in range(total):
        blocks += '<div class="fdd-blk%s"></div>' % (" used" if i < used else "")
    return ('<div class="fdd-meter">' + blocks
            + '<span class="fdd-steps">%d of %d actions used</span></div>'
            % (used, total))


def show_state(state, log=(), reward=None, chips=True):
    """Draw one observation as a browser window.

    `log` is the actions played to get here, as (action, reason) pairs, and `reward` is
    what the environment paid, which is shown to YOU and never to the agent. `chips=False`
    drops the literal action next to each site and link, for when something else on the
    page is already offering them. The side pane then uses the display names
    (People, Facilities, …) instead of the keys the agent sees.

    Outside a notebook it prints intranet.observe(state) instead, unchanged.
    """
    if not _live_notebook():
        print(intranet.observe(state))
        return
    from IPython.display import HTML, display

    esc = html_lib.escape
    query = QUERIES[state["query_idx"]]
    out = ["<style>", _CSS, "</style>", '<div class="fdd-net">']

    out.append('<div class="fdd-task"><span class="fdd-q">%s</span>%s</div>'
               % (esc(query.question), _meter(state["steps"], MAX_STEPS)))

    if log:
        played = []
        for i, (action, reason) in enumerate(log):
            good = not reason
            last = i == len(log) - 1
            if not good and last and reason == state["note"]:
                said = "refused, see below"
            else:
                said = "ok" if good else esc(reason)
            played.append('<span class="fdd-act">%s</span> <span class="%s">%s</span>'
                          % (esc(action), "fdd-okd" if good else "fdd-nod", said))
        out.append('<div class="fdd-log">' + "<br>".join(played) + "</div>")

    if state["note"]:
        out.append('<div class="fdd-note">That did not work: %s</div>'
                   % esc(state["note"]))

    if state["done"] and reward is not None:
        out.append('<div class="fdd-done">Episode over. It answered %s, and the '
                   'environment paid <b>%.3f</b> for it. That number is for you: the '
                   'agent sees it only through the reward, never on the page.</div>'
                   % ("<b>%s</b>" % esc(str(state["answer"]))
                      if state["answer"] else "<i>nothing</i>", reward))

    out.append('<div class="fdd-body"><div class="fdd-pane">')
    for key in SITE_KEYS:
        site = SITES[key]
        heading = key if chips else SITE_LABELS[key]
        if chips:
            tail = ('<div class="b a"><span class="fdd-act">goto_site[%s]</span> '
                    '%d pages</div>' % (esc(key), len(site.pages)))
        else:
            tail = '<div class="b a">%d pages</div>' % len(site.pages)
        out.append('<div class="fdd-site%s"><div class="k">%s</div>'
                   '<div class="b">%s</div>%s</div>'
                   % (" here" if key == state["site"] else "", esc(heading),
                      esc(site.blurb), tail))
    out.append('</div><div class="fdd-page">')

    if state["site"] is None:
        out.append('<div class="fdd-crumb">the intranet home</div>'
                   '<div class="fdd-title">No page is open</div>'
                   '<div class="fdd-line fdd-empty">Open a site with '
                   '<span class="fdd-act">goto_site[site]</span>, using one of the five '
                   'names on the left. The side pane is all there is until you do: no '
                   'page title anywhere is visible from here.</div>')
    else:
        site = SITES[state["site"]]
        page = site.pages[state["page"]]
        out.append('<div class="fdd-crumb">%s &nbsp;/&nbsp; page %d of %d</div>'
                   % (esc(site.key), state["page"] + 1, len(site.pages)))
        out.append('<div class="fdd-title">%s</div>' % esc(page.title))
        for line in page.body:
            out.append('<div class="fdd-line">%s</div>' % esc(line))
        out.append('<div class="fdd-links">')
        if page.links:
            for j, link in enumerate(page.links, start=1):
                mark = ('<span class="fdd-act">follow[%d]</span> ' % j) if chips else ""
                out.append('<div class="fdd-link">%s<a>%s</a> '
                           '<span class="fdd-tgt">goes to %s</span></div>'
                           % (mark, esc(link.label), esc(link.site)))
        else:
            out.append('<div class="fdd-empty">No links on this page.</div>')
        out.append("</div>")
    out.append("</div></div>")

    if state["trail"]:
        read = " &rsaquo; ".join(
            esc("%s/%s" % (key, page_at(key, int(i)).title))
            for key, i in (entry.split("/") for entry in state["trail"]))
    else:
        read = '<span class="fdd-empty">nothing yet</span>'
    out.append('<div class="fdd-trail">Pages read so far (%d of %d in the intranet): '
               '%s</div>' % (len(state["trail"]), N_PAGES, read))

    out.append("</div>")
    display(HTML("".join(out)))


def corpus_payload():
    """The live corpus, as JSON the HTML page can run without Python."""
    sites = {}
    for key in SITE_KEYS:
        site = SITES[key]
        sites[key] = {
            "blurb": site.blurb,
            "label": SITE_LABELS[key],
            "pages": [{
                "title": page.title,
                "body": list(page.body),
                "links": [{"label": link.label, "site": link.site, "page": link.page}
                          for link in page.links],
            } for page in site.pages],
        }
    return {
        "site_keys": list(SITE_KEYS),
        "sites": sites,
        "queries": [{"qid": q.qid, "question": q.question, "answer": q.answer}
                    for q in QUERIES],
        "max_steps": MAX_STEPS,
        "n_pages": N_PAGES,
        "labels": dict(SITE_LABELS),
    }


def html_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), HTML_NAME)


def render_html(start_query=0, embed=False):
    """A full HTML document. `embed=True` uses a fixed height so notebook
    auto-resize cannot grow the cell forever; the standalone page fills the window.
    """
    data = json.dumps(corpus_payload(), ensure_ascii=False).replace("<", "\\u003c")
    # .replace, not % or .format: the page is HTML/JS (braces, percents). walk() also
    # uses %-formatting, and a stray %-38s inside this template blanks the embed.
    if embed:
        root_css = (
            "html, body { margin: 0; padding: 0; height: auto; overflow: hidden; "
            "background: #fff; }"
        )
        tail_css = (
            ".fdd-ui { height: %dpx; max-height: %dpx; overflow: hidden; }"
            % (EMBED_HEIGHT, EMBED_HEIGHT)
        )
    else:
        root_css = (
            "html, body { height: 100%; margin: 0; overflow: hidden; background: #fff; }\n"
            "body { display: flex; flex-direction: column; min-height: 0; }"
        )
        tail_css = ""
    return (_PAGE
            .replace("___FDD_ROOT_CSS___", root_css)
            .replace("___FDD_CSS___", _CSS)
            .replace("___FDD_TAIL_CSS___", tail_css)
            .replace("___FDD_DATA___", data)
            .replace("___FDD_START_QUERY___", str(int(start_query))))


def write_html(path=None, start_query=0):
    """Write (or refresh) the standalone page. Returns the path."""
    path = path or html_path()
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(render_html(start_query=start_query))
    return path


def explore(query_idx=0):
    """Show the intranet as a clickable window. Same page as intranet_game.html.

    Returns the widget container in a notebook, or the HTML path outside one.
    """
    path = write_html()
    page = render_html(start_query=query_idx, embed=True)
    if not _live_notebook():
        print("open in a browser:", path)
        return path
    from IPython.display import HTML, display
    h = str(EMBED_HEIGHT)
    frame = (
        '<iframe srcdoc="' + html_lib.escape(page, quote=True) +
        '" width="100%" height="' + h + '" scrolling="no"'
        ' style="width:100%;height:' + h + 'px;border:1px solid #d7dce2;'
        'border-radius:10px;background:#fff;display:block;overflow:hidden">'
        '</iframe>'
    )
    display(HTML(frame))
    return None

def walk(query_idx, actions, show=True):
    """GIVEN. Play a list of actions from a FRESH episode of question `query_idx`.

    Draws the browser window you end up in, with the actions you played above it.
    Every call starts a new episode, so these cells can be run in any order, any
    number of times, and always give the same thing.
    """
    env = IntranetEnv()
    env.reset(query_idx)
    reward, done, log = 0.0, False, []
    for action in actions:
        _, reward, done, info = env.step(action)
        log.append((action, info["reason"]))
        if done:
            break
    if show:
        show_state(env.state, log=log, reward=reward if done else None)
    else:
        for action, reason in log:
            print("  %-38s %s" % (action, reason or "ok"))
        print("\n  %d of %d actions used, %d of the %d pages read"
              % (env.state["steps"], MAX_STEPS, len(env.state["trail"]), N_PAGES))
        if done:
            print("  episode over.  reward %.3f" % reward)


def reveal(query_idx):
    """GIVEN. The answer, the two pages it takes, and the table the second one is.

    This reads Query.answer, Query.hop1, Query.hop2, Query.key_entity and
    Query.decoy_answers, which are in the query set so that the checkers can grade. No
    observation ever carries them, and neither the agent you build in this notebook nor
    the language model behind it can reach them.
    """
    query = QUERIES[query_idx]
    rows = (query.answer,) + tuple(query.decoy_answers)
    print("Q%d  %s" % (query.qid, query.question))
    print("    gold answer:  %s" % query.answer)
    key, page = query.hop1
    print("    hop 1:  %s, page %d, %s" % (key, page + 1, SITES[key].pages[page].title))
    print("            where the question's description turns into a name: %r"
          % query.key_entity)
    key, page = query.hop2
    print("    hop 2:  %s, page %d, %s" % (key, page + 1, SITES[key].pages[page].title))
    print("            a table of %d rows. The answers it offers: %s"
          % (len(rows), ", ".join(rows)))
    print("            without hop 1, standing on it is a %d way guess" % len(rows))


_PAGE = r"""<!DOCTYPE html>
<!-- Generated by browser.py from the live corpus. Do not edit by hand; run: python3 browser.py -->
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Nordhelm Instruments — intranet</title>
<style>
___FDD_ROOT_CSS___
___FDD_CSS___
___FDD_TAIL_CSS___
</style>
</head>
<body>
<div class="fdd-ui" id="game"></div>
<script>
const DATA = ___FDD_DATA___;
const START_QUERY = ___FDD_START_QUERY___;
const ARTICLES = new Set(["a", "an", "the"]);

function normalizeTokens(text) {
  if (text === null || text === undefined || text === "") return [];
  return String(text).toLowerCase().split(/[^a-z0-9]+/).filter(function (t) {
    return t && !ARTICLES.has(t);
  });
}

function tokenF1(pred, gold) {
  var p = normalizeTokens(pred), g = normalizeTokens(gold);
  if (!p.length || !g.length) {
    return (p.length === g.length && p.join("\0") === g.join("\0")) ? 1 : 0;
  }
  var pc = {}, gc = {}, i, t, common = 0;
  for (i = 0; i < p.length; i++) pc[p[i]] = (pc[p[i]] || 0) + 1;
  for (i = 0; i < g.length; i++) gc[g[i]] = (gc[g[i]] || 0) + 1;
  for (t in pc) if (gc[t]) common += Math.min(pc[t], gc[t]);
  if (common === 0) return 0;
  var prec = common / p.length, rec = common / g.length;
  return 2 * prec * rec / (prec + rec);
}

function initialState(queryIdx) {
  return {query_idx: queryIdx, site: null, page: null, steps: 0, done: false,
          answer: null, reward: 0, trail: [], note: ""};
}

function clone(state) {
  return JSON.parse(JSON.stringify(state));
}

function openPage(state, site, index) {
  state.site = site;
  state.page = index;
  var entry = site + "/" + index;
  if (state.trail.indexOf(entry) < 0) state.trail.push(entry);
}

function parseAction(action) {
  var text = String(action).trim();
  if (text === "next" || text === "prev") return [text, ""];
  var m = text.match(/^([a-z_]+)\[([\s\S]*)\]$/);
  if (m) return [m[1], m[2]];
  return [null, action];
}

function transition(state, action) {
  var parsed = parseAction(action);
  var verb = parsed[0], payload = parsed[1];
  if (state.done) {
    return {state: clone(state), reward: 0, done: true, reason: "the episode is over"};
  }
  var nxt = clone(state);
  nxt.note = "";
  var reason = "";
  var VERBS = {goto_site: 1, next: 1, prev: 1, follow: 1, answer: 1};
  if (!VERBS[verb]) {
    reason = JSON.stringify(action) + " is not an action I understand.";
  } else if (verb === "goto_site") {
    var name = payload.trim();
    if (DATA.site_keys.indexOf(name) < 0) {
      reason = "there is no site called " + JSON.stringify(name) + ".";
    } else {
      openPage(nxt, name, 0);
    }
  } else if (verb === "next" || verb === "prev") {
    if (nxt.site === null) {
      reason = "no page is open yet, so there is nothing to page through.";
    } else {
      var pages = DATA.sites[nxt.site].pages;
      var target = nxt.page + (verb === "next" ? 1 : -1);
      if (target < 0 || target >= pages.length) {
        reason = "there is no page " + (verb === "next" ? "after" : "before") +
                 " this one in " + nxt.site + ", and the pages do not wrap around.";
      } else {
        openPage(nxt, nxt.site, target);
      }
    }
  } else if (verb === "follow") {
    if (nxt.site === null) {
      reason = "no page is open yet, so there are no links to follow.";
    } else {
      var links = DATA.sites[nxt.site].pages[nxt.page].links;
      var n = parseInt(payload.trim(), 10);
      if (!isFinite(n)) {
        reason = "follow needs a link number, as in follow[1].";
      } else if (!links.length) {
        reason = "this page has no links.";
      } else if (n < 1 || n > links.length) {
        reason = "this page has " + links.length + " link" +
                 (links.length === 1 ? "" : "s") + ", so follow[" + n + "] does not exist.";
      } else {
        var link = links[n - 1];
        openPage(nxt, link.site, link.page);
      }
    }
  } else {
    nxt.answer = payload;
    nxt.reward = tokenF1(payload, DATA.queries[nxt.query_idx].answer);
    nxt.done = true;
  }
  nxt.note = reason;
  nxt.steps += 1;
  if (!nxt.done && nxt.steps >= DATA.max_steps) nxt.done = true;
  return {state: nxt, reward: nxt.reward, done: nxt.done, reason: reason};
}

function esc(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
                  .replace(/"/g, "&quot;");
}

function meter(used, total) {
  var blocks = "", i;
  for (i = 0; i < total; i++) {
    blocks += '<div class="fdd-blk' + (i < used ? " used" : "") + '"></div>';
  }
  return '<div class="fdd-meter">' + blocks +
         '<span class="fdd-steps">' + used + " of " + total + " actions used</span></div>";
}

function paneHtml(state) {
  var out = "", i, key, site;
  for (i = 0; i < DATA.site_keys.length; i++) {
    key = DATA.site_keys[i];
    site = DATA.sites[key];
    out += '<div class="fdd-site' + (key === state.site ? " here" : "") + '">' +
           '<div class="k">' + esc(site.label) + "</div>" +
           '<div class="b">' + esc(site.blurb) + "</div>" +
           '<div class="b a">' + site.pages.length + " pages</div></div>";
  }
  return out;
}

function pageHtml(state) {
  if (state.site === null) {
    return '<div class="fdd-crumb">the intranet home</div>' +
           '<div class="fdd-title">No page is open</div>' +
           '<div class="fdd-line fdd-empty">Open a site using one of the five names on ' +
           "the left. The side pane is all there is until you do: no page title " +
           "anywhere is visible from here.</div>";
  }
  var site = DATA.sites[state.site];
  var page = site.pages[state.page];
  var out = '<div class="fdd-crumb">' + esc(site.label) + " &nbsp;/&nbsp; page " +
            (state.page + 1) + " of " + site.pages.length + "</div>" +
            '<div class="fdd-title">' + esc(page.title) + "</div>";
  var i;
  for (i = 0; i < page.body.length; i++) {
    out += '<div class="fdd-line">' + esc(page.body[i]) + "</div>";
  }
  out += '<div class="fdd-links">';
  if (page.links.length) {
    for (i = 0; i < page.links.length; i++) {
      out += '<div class="fdd-link"><a>' + esc(page.links[i].label) +
             '</a> <span class="fdd-tgt">goes to ' +
             esc(DATA.sites[page.links[i].site].label) + "</span></div>";
    }
  } else {
    out += '<div class="fdd-empty">No links on this page.</div>';
  }
  return out + "</div>";
}

function trailHtml(state) {
  if (!state.trail.length) {
    return '<span class="fdd-empty">nothing yet</span>';
  }
  return state.trail.map(function (entry) {
    var parts = entry.split("/");
    var page = DATA.sites[parts[0]].pages[parseInt(parts[1], 10)];
    return esc(parts[0] + "/" + page.title);
  }).join(" &rsaquo; ");
}

function browserHtml(state, last) {
  var q = DATA.queries[state.query_idx];
  var out = '<div class="fdd-net">';
  out += '<div class="fdd-task"><span class="fdd-q">' + esc(q.question) + "</span>" +
         meter(state.steps, DATA.max_steps) + "</div>";
  if (last) {
    var good = !last.reason;
    var said = good ? "ok" : "refused, see below";
    if (!good && last.reason !== state.note) said = esc(last.reason);
    out += '<div class="fdd-log"><span class="fdd-act">' + esc(last.action) +
           '</span> <span class="' + (good ? "fdd-okd" : "fdd-nod") + '">' +
           said + "</span></div>";
  }
  if (state.note) {
    out += '<div class="fdd-note">That did not work: ' + esc(state.note) + "</div>";
  }
  if (state.done) {
    var answered = state.answer ? "<b>" + esc(state.answer) + "</b>" : "<i>nothing</i>";
    out += '<div class="fdd-done">Episode over. It answered ' + answered +
           ", and the environment paid <b>" + Number(state.reward).toFixed(3) +
           "</b> for it.</div>";
  }
  out += '<div class="fdd-body"><div class="fdd-pane">' + paneHtml(state) +
         '</div><div class="fdd-page">' + pageHtml(state) + "</div></div>";
  out += '<div class="fdd-trail">Pages read so far (' + state.trail.length +
         " of " + DATA.n_pages + " in the intranet): " + trailHtml(state) + "</div>";
  return out + "</div>";
}

function btn(label, action, cls) {
  return '<button type="button" class="' + (cls || "") + '" data-action="' +
         esc(action) + '">' + esc(label) + "</button>";
}

function controlsHtml(state) {
  var i, key, out = "";
  if (state.done) {
    var gold = DATA.queries[state.query_idx].answer;
    out += '<div class="fdd-banner">The environment paid <b>' +
           Number(state.reward).toFixed(3) + "</b>. The answer it wanted was <b>" +
           esc(gold) + "</b>. Press start over to go again, or pick another question.</div>";
    return out + pickerRow();
  }
  out += '<div class="fdd-row"><b>go to&nbsp;</b>';
  for (i = 0; i < DATA.site_keys.length; i++) {
    key = DATA.site_keys[i];
    out += btn(DATA.labels[key], "goto_site[" + key + "]",
               key === state.site ? "" : "info");
  }
  out += "</div>";
  var paging = "";
  if (state.site !== null) {
    var pages = DATA.sites[state.site].pages;
    if (state.page > 0) paging += btn("prev page", "prev", "warning");
    if (state.page < pages.length - 1) paging += btn("next page", "next", "warning");
    var links = pages[state.page].links;
    for (i = 0; i < links.length; i++) {
      paging += btn(links[i].label, "follow[" + (i + 1) + "]", "info");
    }
  }
  if (paging) {
    out += '<div class="fdd-row"><b>on this page&nbsp;</b>' + paging + "</div>";
  }
  out += '<div class="fdd-row"><input id="answer-box" type="text" ' +
         'placeholder="type your answer, then press answer">' +
         btn("answer", "submit-answer", "success") + "</div>";
  return out + pickerRow();
}

function pickerRow() {
  var opts = "", i;
  for (i = 0; i < DATA.queries.length; i++) {
    opts += '<option value="' + i + '"' + (i === Game.queryIdx ? " selected" : "") +
            ">Q" + (i + 1) + "</option>";
  }
  return '<div class="fdd-row"><b>Select Question&nbsp;</b>' +
         '<select id="q-picker">' + opts + "</select>" +
         btn("start over", "restart", "danger") + "</div>";
}

var Game = {state: null, last: null, queryIdx: START_QUERY};

function draw() {
  document.getElementById("game").innerHTML =
      browserHtml(Game.state, Game.last) + controlsHtml(Game.state);
  var picker = document.getElementById("q-picker");
  if (picker) {
    picker.onchange = function () {
      Game.queryIdx = parseInt(picker.value, 10);
      restart();
    };
  }
  var box = document.getElementById("answer-box");
  document.getElementById("game").onclick = function (ev) {
    var b = ev.target.closest("button");
    if (!b) return;
    var action = b.getAttribute("data-action");
    if (action === "restart") { restart(); return; }
    if (action === "submit-answer") {
      play("answer[" + ((box && box.value) || "").trim() + "]");
      return;
    }
    if (action) play(action);
  };
}

function play(action) {
  var result = transition(Game.state, action);
  Game.state = result.state;
  Game.last = {action: action, reason: result.reason};
  draw();
}

function restart() {
  Game.state = initialState(Game.queryIdx);
  Game.last = null;
  draw();
}

restart();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    print("wrote", write_html())

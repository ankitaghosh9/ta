# 🕵️ ReAct: The Corporate Detective

*From Data to Solutions: Synergizing Reasoning and Acting in Language Models.*

Welcome to **Baskerville Tech**. A crime has been committed, and you are going to solve it twice: first with a standard AI model, and then by building an AI agent equipped with external tools.

This exercise demonstrates why giving an AI the ability to reason and use tools simultaneously (ReAct) is fundamentally different—and far more powerful for business applications—than standard prompting.

---

## 📜 The Premise: The Case of the Stolen Algorithm

**Baskerville Tech** is a leading robotics firm. Overnight, between **12:30 AM and 2:00 AM**, a devastating data breach occurred.

The proprietary code for a revolutionary design was downloaded onto an unauthorized external drive and sold to a competitor.

You have six suspects, a fragmented trail of corporate data, and one question: **Who stole the algorithm?**

### The Suspects

| Suspect | Role | The Profile |
| --- | --- | --- |
| **Alice** | Lead Developer | Brilliant but overworked; has universal root access to the codebase. |
| **Bob** | QA Engineer | Disgruntled; recently passed over for a major promotion. |
| **Charlie** | Facility Security Officer | Night-shift facility patrol with a master keycard; not an engineer, but authorized to enter the server room and run basic hardware-status checklists (doors, racks, power lights). |
| **Diana** | VP of Engineering | Aggressive negotiator; recently had a public shouting match with the CEO. |
| **Eve** | Visiting Scholar | Temporary access; has been legitimately downloading massive 3D simulation datasets all week. |
| **Frank** | IT Admin | Works bizarre hours; loudly complaining on Slack about severe budget cuts. |

---

## 🎭 The Two Acts

In this notebook, you will play the role of Baskerville Tech consulting two different types of AI.

### Act I: Dr. Watson (Standard Prompting)

First, you will hand the premise and the suspect list to Dr. Watson (a standard, zero-shot ChatGPT prompt).

> **The Lesson:** Standard models suffer from *confident incompetence*. Watch as Watson relies on narrative tropes and statistical probabilities to confidently hallucinate a plausible—but entirely fabricated—explanation, accusing the wrong person without verifying a single fact.

### Act II: Sherlock Holmes (The ReAct Agent)

Next, you will assemble Sherlock Holmes. Sherlock is a ReAct agent equipped with a "magnifying glass" consisting of four mock corporate APIs.

Instead of guessing, Sherlock must use the **Thought $\rightarrow$ Action $\rightarrow$ Observation** loop to systematically eliminate suspects based on hard data.

**The Tools at Your Disposal:**

* `query_server_logs(time_window)`: Returns credentials that accessed the servers in a 4-hour slot (e.g. `00:00-04:00`, `20:00-00:00`). The theft sits in `00:00-04:00` (12:30 AM–2:00 AM).
* `check_badge_swipes(time)`: Returns who is still badge-IN (on premises) at `HH:MM` (e.g. `01:00`).
* `inspect_work_emails(employee_name)`: Returns flagged keywords from recent communications.
* `check_bank_records(employee_name)`: Returns `monthly wage`, `monthly deposit`, `monthly withdraw` (numbers), and `flagged transaction` (string).

---

## 🛠️ How to Play

1. **Run the Setup:** Execute the setup cells to load the case file and the Hugging Face model (`Qwen/Qwen2.5-0.5B-Instruct` by default).
2. **Consult Watson:** Run the one-shot LLM prompt and analyze why narrative guessing fails without tools.
3. **Play the Game:** Open the interactive detective game (`detective_game.html`) — query the four APIs, review suspect profiles, and submit your accusation.
4. **Be the Agent:** Before turning the LLM loose, manually type out a ReAct loop. You write the *Thought*, choose an *Action*, and Python returns the *Observation*.
5. **Unleash Sherlock:** Let the LLM drive the full ReAct loop and watch it hunt down the culprit from evidence.


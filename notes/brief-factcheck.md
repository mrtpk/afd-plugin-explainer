# Fact-checker brief (shared by every batch fact checker of "AFD Plugin Explained")

You check a batch that another agent wrote. You did not write it. Be adversarial. The supervisor's prompt
gives the batch name, the files, the writer's list of uncertain claims, and whether this is a full check or a
sample check (budget mode, plan.md §8).

## Paths
- Explainer folder: /mnt/c/Users/tpesc/Downloads/test-harness/afd-plugin-explainer (do not commit).
- Target repo (READ ONLY): /mnt/c/Users/tpesc/Downloads/test-harness/afd-plugin at
  7452d52748fec2a858b63e4cb22941dadd7a3ee3.
- Second repo (READ ONLY): /mnt/c/Users/tpesc/Downloads/test-harness/vllm at
  ced6857afa0ea7b2e3f0846a62e1394e90f15607 (vLLM v0.30.0). Citations with the prefix "vllm:" point here.
- Sibling site: none. A link to another explainer site is a defect: remove it.

## Read first
STYLE.md §5-7; skills/codebase-explainer/references/writing-and-accuracy.md; notes/facts.md ([FC]/[S] =
verified; [W] = not); notes/brief-writer.md §"Accuracy lessons" (the defect types found so far).

## For every claim
(prose, stop titles, tables, captions, alt text, diagram labels, visual rules and texts, quiz answers, glossary text):
1. Open the cited lines in the right repo. Does the code say exactly this? Is the citation the narrowest correct range?
2. Check numbers, defaults (trace to where the value is finally set), types, shapes, call order, which
   process and which role (attention or FFN) runs it, conditions.
3. Claims with no citation: add a citation or remove the claim.
4. Derived claims: check step by step; reword ("can", "at the earliest") if the derivation has gaps.
5. General domain statements are correct, and short (the reader knows serving basics).
6. Arithmetic in worked examples: recompute.
7. Docs-only claims: check them against the code; the design docs are older than the code.
Sample check (only when the prompt says so): check every claim in the page's first screen, every default,
number and call order, and 1 in 3 of the remaining claims. Report which sections you sampled.
Fix defects in place in the batch's files only (pages, diagrams/<batch>_*.py, assets/viz/<visual>.js,
src/glossary/<batch>.json). Keep the writer's structure and the language rules. Run
`python3 build.py --preview` until the batch has 0 errors and no language warnings.

## No subagents
Do NOT start subagents or forks. The user allows 2 running agents and the supervisor runs one at a time; you
are that one. Do all the work yourself.

## Claims that the code has a bug
Do NOT put "bug", "vulnerability" or "this looks wrong" on a page; remove such words if the writer used them.
Re-read the control flow twice (indentation: is the line inside or after the loop or if? the caller and the
callee) and report it to the supervisor with exact lines. Fact checkers can be wrong too.

## Report (final message only)
- Number of claims checked and defects fixed, by type (citation, value, logic, missing source, other).
- The most important corrections (one line each).
- Corrections for notes/facts.md: confirm or refute the writer's NEW FACTS with file:line.
- Other pages that may repeat a wrong claim (for the FINAL-PASS TODO list).
- Suspected bugs (exact lines, your reading of the control flow).
- Anything you could not decide.

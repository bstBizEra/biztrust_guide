#!/usr/bin/env python3
"""The part of the negative-control runners that is genuinely common (#368).

`scripts/wp111_controls.py` through `scripts/wp116_controls.py` were each written by copying the
previous one. #368 measured the result: 2,943 lines in which exactly ONE shared function -
`git_out` - was byte-identical across its copies. The obvious reading of that measurement, "six
duplicates, extract them", is the reading this module is written to refuse. The runners have
different subjects: WP-112 and WP-114 mutate git history and therefore CLONE, the other four
mutate tracked files and therefore COPY. `fresh` differing from `clone` is the right answer for
each caller, not drift.

So the divergences were classified one at a time before anything moved. NEED means a caller
genuinely requires the difference and it survives here as a PARAMETER with a live caller on each
side. DRIFT means nothing depended on it. Where a drifted difference is nonetheless VISIBLE - it
prints, or it writes different bytes - it is still a parameter, because the bar this extraction was
held to is that each runner's full output is unchanged, not that the suite stays green. Nothing
here was resolved by taking the union of two behaviours or the more lenient of them; WP-110 did
that to four private normalisers and review found eight real divergences that were caught before
the change and missed after it.

Measured at f34891a by hashing every top-level function body with `ast.get_source_segment` and
grouping by name. #368's own table counted `edit` as six distinct bodies and `main`'s at 39-79
lines; hashing the exact segments gives `edit` FOUR distinct texts (three distinct behaviours) and
`main` 35-75 lines. The classification below is the measured one.

  name                      copies/texts  what differs                       need or drift
  ------------------------  ------------  ---------------------------------  -------------------
  edit                      6 / 4         `old[:60]` in wp111, `old[:70]`    DRIFT, but it prints
                                          in the other five                  -> `preview`
                                          `newline=""` on the write, absent  DRIFT, but it writes
                                          in wp111 and wp112                 -> `newline`
                                          where the `raise` line wraps       DRIFT, dropped
  main                      6 / 6         the argv/holder preamble           COMMON -> arguments()
                                          "copy" vs "clone" in the header    NEED -> `noun`
                                          `fresh` vs `clone` as the builder  NEED -> `build`
                                          the declared-hole wording, two     DRIFT, but it prints
                                          variants over 4 and 2 callers      -> `hole_*`
                                          the second and third loops, whose  NEED, left in each
                                          tuples, runners and report lines   runner
                                          are all per-package
                                          the closing count line             COMMON -> summarise()
  run_suite / wp111's `run` 6 / 5         the discovery pattern              NEED -> `pattern`
                                          `-B`, in wp115 and wp116 only      DRIFT, but it writes
                                                                             -> `no_bytecode`
                                          `timeout=1800`, absent in wp111    DRIFT, but it can
                                                                             fire -> `timeout`
                                          the name `run` in wp111            DRIFT, dropped
  fresh                     4 / 3         wp111 does not ignore `_site` or   DRIFT, but it copies
                                          `node_modules`                     -> `ignore`
  run_validator             3 / 2         wp112 and wp114 parse ONE          NEED. Two right
                                          `STATE_RECONCILIATION=` line out   answers, one per
                                          of stdout at timeout 600; wp115    caller. NOT unified;
                                          returns stdout+stderr whole at     only the subprocess
                                          timeout 1800 to search for         call is common
                                          `CONTINUITY_VALIDATION=PASS`       -> run_script()
                                          LEFTOVER DUPLICATION, NAMED: with  Byte-identical, ten
                                          `run_script()` taken out, what     lines each. NOT
                                          remains of wp112's and wp114's     collapsed here, and a
                                          own `run_validator` is the same    later package could
                                          in both                            share that pair
  clone                     2 / 2         wp112 carries `depth` and asserts  DRIFT. wp114's body
                                          the shallow clone is really        IS the `depth=0` path
                                          shallow; wp114 has neither         of wp112's -> `depth`
  git_out                   2 / 1         nothing                            COMMON, as it stands
  check_source_main_line    2 / 2         wp114 asks the ancestor question   NOT EXTRACTED. Its two
                                          through its own `ancestry()`,      docstrings are each
                                          which raises on an exit code       package's own recorded
                                          other than 0 or 1; wp112 inlines   measurement, and the
                                          the subprocess and lets any        edge case really does
                                          other code fall through to the     differ. Left in both.
                                          refusal

WHAT IS NOT HERE, and deliberately. Every `a_*`/`the_*` mutation function, every fixture builder,
every module constant naming a package's own subject: one copy each, nothing shared, nothing to
extract. `check_source_main_line` is named above and stays where it is - it refuses to run when the
source checkout's local `main` carries commits its `origin/main` does not, it exists because an
accident once made every clone-based control red for a reason unrelated to the code, and its
behaviour is not this package's to alter.

THIS MODULE IS NOT A TEST HELPER. `tests/` imports nothing from here and must not: the suite is
offline and subprocess-free apart from four declared modules, and everything below shells out.
`tests/test_harness_parameters.py` READS this file as text with `ast` and never imports it, which
breaks neither property. What it holds is the one thing this table cannot: that every parameter
above still has a caller passing something other than its default. A default nobody dissents from
has stopped expressing a difference between callers and has become the union of two behaviours
with one deleted - WP-110's failure, arriving through the door this module opened.
`scripts/wp117_controls.py` is the runner that demonstrates that guard can fail, and is itself the
first runner built on this harness rather than copied from its predecessor.

Stdlib only.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable, Iterable
from pathlib import Path

PYTHON = sys.executable

# Identical in all six runners.
FAILED = re.compile(r"^(?:FAIL|ERROR): (\w+) ", re.M)
# Identical in the two that read the validator's reconciliation verdict.
VERDICT = re.compile(r"^STATE_RECONCILIATION=(\w+)$", re.M)

# What wp113, wp115 and wp116 ignore when they copy. wp111 passes its own narrower tuple.
COPY_IGNORE = (".git", "_site", "node_modules", "__pycache__", "*.pyc")

# The two wordings the declared-hole branch has been given, one per pair of live callers. They are
# named rather than inlined so that a runner adopting the harness cannot silently acquire the other
# one: the whole bar for adoption is that its printed output does not change.
HOLE_DECLARED = ("DECLARED HOLE: ",
                 "  <- the hole has closed; re-derive the limit that declares it")
HOLE_PLAIN = ("", "  <- re-derive the claim this control stands behind")


def edit(root: Path, rel: str, old: str, new: str, *,
         preview: int = 70, newline: str | None = "") -> None:
    """Replace `old` with `new` exactly once, and refuse to be a no-op.

    `preview` is how much of `old` the failure message shows: 70 for five runners, 60 for wp111.
    `newline` goes to `write_text`; `""` writes the string's own line endings through untouched,
    and `None` - wp111 and wp112 - lets Python translate every `\\n` in the whole file to the
    platform's separator. That second one rewrites lines the mutation never touched, which is why
    it is a parameter and not a repair.
    """
    path = root / rel
    text = path.read_text(encoding="utf-8")
    found = text.count(old)
    if found != 1:
        raise AssertionError(
            f"{rel}: expected exactly one occurrence of {old[:preview]!r}, found {found}")
    path.write_text(text.replace(old, new), encoding="utf-8", newline=newline)


def fresh(source: Path, into: Path, name: str, *,
          ignore: Iterable[str] = COPY_IGNORE) -> Path:
    """A copy of `source` at `into/name`, WITHOUT `.git`. ENFORCED, not relied upon.

    That absence is a property the script controls depend on: the copy is not a repository, so
    every git fact must degrade rather than be answered from somewhere else. `.git` used to be
    excluded only because every caller's tuple happened to contain it, which made the sentence
    above an assertion about the callers rather than a promise of this function - a seventh runner
    passing its own tuple would have got a repository copy in silence, and a wp113-style control
    expecting a git fact to degrade would have had it answered instead: green, and meaningless. So
    `.git` is prepended here and the rest of the tuple is still the caller's, because wp111's omits
    `_site` and `node_modules` and copying those would change what its controls run over. Both
    tuples in the tree already carry `.git`, so this is a no-op for every current caller and
    `shutil.ignore_patterns` does not mind the duplicate.
    """
    root = into / name
    shutil.copytree(source, root, ignore=shutil.ignore_patterns(".git", *ignore))
    return root


def clone(source: Path, into: Path, name: str, *, depth: int = 0) -> Path:
    """A git clone of `source` at `into/name`, shallow only when `depth` is given."""
    command = ["git", "clone", "--quiet"]
    root = into / name
    if depth:
        # `--depth` is IGNORED on a plain local path; only the file:// transport honours it, and a
        # control that silently produced a full clone would demonstrate the opposite of its name.
        command += ["--depth", str(depth), source.as_uri()]
    else:
        command += [str(source)]
    done = subprocess.run(command + [str(root)], capture_output=True, text=True, timeout=600)
    if done.returncode != 0:
        raise AssertionError(f"clone of {source} failed: {done.stdout}{done.stderr}")
    if depth:
        shallow = subprocess.run(["git", "-C", str(root), "rev-parse", "--is-shallow-repository"],
                                 capture_output=True, text=True, timeout=60)
        if shallow.stdout.strip() != "true":
            raise AssertionError(f"clone --depth {depth} did not produce a shallow repository")
    return root


def git_out(root: Path, *args: str) -> str:
    """One git command at `root`, refusing to return silence on failure."""
    done = subprocess.run(["git", "-C", str(root), *args],
                          capture_output=True, text=True, encoding="utf-8", errors="replace",
                          timeout=120)
    if done.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed in {root}: {done.stdout}{done.stderr}")
    return done.stdout.strip()


def run_suite(root: Path, pattern: str, *,
              no_bytecode: bool = False, timeout: float | None = 1800) -> tuple[int, set[str]]:
    """`unittest discover` over ONE module inside `root`; the exit code and the tests that failed.

    `timeout=None` is wp111, which passes no timeout at all. `no_bytecode` is wp115 and wp116,
    which run the suite under `-B` so the copy does not acquire `__pycache__` directories.
    """
    command = [PYTHON]
    if no_bytecode:
        command.append("-B")
    command += ["-m", "unittest", "discover", "-s", "tests", "-p", pattern, "-v"]
    done = subprocess.run(command, cwd=root, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)
    return done.returncode, set(FAILED.findall(done.stdout + done.stderr))


def run_script(root: Path, rel: str, *args: str,
               timeout: float | None) -> tuple[int, str, str]:
    """One of the repository's own scripts, run from inside `root` under `-B`.

    stdout and stderr come back SEPARATE because the callers read them differently: wp112 and
    wp114 match a `STATE_RECONCILIATION=` line anchored with `re.M` against stdout alone, wp115
    searches the two joined, and wp113 wants neither and reads the file the run wrote.
    """
    done = subprocess.run([PYTHON, "-B", str(root / rel), *args], cwd=root,
                          capture_output=True, text=True, encoding="utf-8", errors="replace",
                          timeout=timeout)
    return done.returncode, done.stdout, done.stderr


def arguments(script: str) -> tuple[Path, Path]:
    """`(source, holder)` from argv, defaulting to this checkout and a fresh temporary directory."""
    source = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(script).resolve().parents[1]
    holder = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else Path(tempfile.mkdtemp())
    holder.mkdir(parents=True, exist_ok=True)
    return source, holder


def report_unmutated(code: int, failures: set[str], noun: str) -> int:
    """The first line every runner prints, and 1 if the unmutated tree is already red."""
    print(f"[{'PASS' if code == 0 else 'BAD '}] unmutated {noun}: exit {code}, "
          f"failures {sorted(failures) or 'none'}")
    if code != 0:
        print(f"       the unmutated {noun} is already red; every control below proves nothing")
        return 1
    return 0


def suite_controls(controls: Iterable[tuple[str, Callable[[Path], None], str | None]],
                   build: Callable[[str], Path],
                   run: Callable[[Path], tuple[int, set[str]]],
                   *, hole: tuple[str, str]) -> int:
    """The `(name, mutate, expected)` loop, and how many controls did not behave as declared.

    `expected is None` is A DECLARED HOLE: the mutation is a real defect and the suite is expected
    to stay green, because nothing in it reads what the mutation changes. A control that
    demonstrates a limit cannot drift away from the code without this script noticing. `hole` is
    HOLE_DECLARED or HOLE_PLAIN - the two wordings the six runners give that branch.
    """
    hole_label, hole_warning = hole
    bad = 0
    for index, (name, mutate, expected) in enumerate(controls, start=1):
        root = build(f"control_{index:02d}")
        mutate(root)
        code, failures = run(root)
        if expected is None:
            ok = code == 0 and not failures
            bad += 0 if ok else 1
            print(f"[{'PASS' if ok else 'BAD '}] {name}")
            print(f"       {hole_label}expected the suite to stay GREEN; exit {code}; "
                  f"failed: {sorted(failures) or 'nothing'}"
                  f"{'' if ok else hole_warning}")
            continue
        ok = code != 0 and expected in failures
        isolated = failures == {expected}
        bad += 0 if ok else 1
        print(f"[{'PASS' if ok else 'BAD '}] {name}")
        print(f"       expected {expected} to fail; exit {code}; "
              f"failed: {sorted(failures) or 'NOTHING'}"
              f"{'' if isolated else '  <- NOT ISOLATED' if ok else ''}")
    return bad


def summarise(total: int, bad: int) -> int:
    """The closing count, and the exit code every runner returns."""
    print(f"\n{total} controls, {bad} not behaving as declared")
    return 1 if bad else 0

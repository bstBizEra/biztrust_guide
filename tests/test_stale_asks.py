#!/usr/bin/env python3
"""An ask a sibling says it carried stops reading as open in the design that asked.

The pack was written design by design and revised design by design, and the revision round
updated the designs that GRANTED asks and not the designs that MADE them. Every revised design
carries a "Changes in 0.N" table crediting whoever asked, by name and often by question number;
almost no asker recorded that its ask had been answered. Twenty-four such pairs are open (#326,
found by the thirteen design reviews under #322).

The cost is not tidiness. A design's open questions are what a reader at `BT-G0` uses to see what
the design is still waiting on, and fifteen questions across seven designs name a dependency that
was met - in one case, by a sibling that credits that very question number for meeting it.

WHY THIS PAIRS AND DOES NOT SWEEP. The obvious form of this check is a keyword sweep: find a
design naming a sibling near "next version", and see whether that sibling has been revised. It
was built first and discarded, because it over-matches by roughly four to one - about seventy
candidate sentences against the two dozen that are real. One design can credit an asker for one
thing while a DIFFERENT ask from the same asker stays genuinely open, so naming the sibling is
not evidence of anything.

The precise key was already in the pack: twenty-seven of the forty-four change rows credit "The
P0.A design, question N". That names the exact question the change answered, so the check is a
triple - carrier, asker, question - and not a proximity guess.

WHERE "STILL OPEN" IS READ. Only inside the question's `Waits on:` clause, up to its `ASSUMED`
marker. That boundary is doing real work: P0.7's question 10 reads "At `0.1` this waited on the
P0.5 design and the P0.6 design's next version; BOTH HAVE LANDED, and the P0.6 design lists the
role at its own `0.2`. Waits on: ADR-003 and ADR-004". It mentions its carrier twice and is the
one credited question in the pack that is properly up to date. A reader that took the whole
question would call it stale, which is precisely backwards - it is the model the other fifteen
should follow.

WHAT THIS DOES NOT DO.

 1. Seventeen of the forty-four change rows credit an asker WITHOUT a question number - "The P0.4
    design, its history table". Those are not checked at all. The instances are real (P0.4's
    history-table ask is one of them) but there is no key to pair them on, and guessing is what
    the sweep did.
 2. It reads a question's `Waits on:` clause, so an ask left open in the design's BODY rather
    than in its open questions is invisible. P0.5's four stale sentences are mostly of that kind
    and are in #326's prose.
 3. It cannot tell whether the carrier really answered the ask - only that the carrier says it
    did, and that the asker still says it is waiting. Those two records disagreeing is the defect;
    which of them is wrong is a question for whoever works #326.
 4. A design still at `0.1` has no "Changes in" table, so it can carry an ask but never credit
    one. All three - P0.9, P0.11, P0.13 - appear here only as askers.
 5. FIFTEEN OF THE SIXTEEN CREDITED PAIRS ARE REGISTERED, so the rule that catches a NEW stale
    pair currently reads exactly one question: P0.7's tenth. That is not a weakness in the rule -
    it is what a registry of two dozen live defects looks like - but a green suite here means
    "no new staleness", not "the pack is clean". The registry shrinking is what progress looks
    like, and the forward rule widens as it does.

POSITIVE CONTROLS are named sets, not counts: the credits must be found, every registered asker
and question must exist, and the one properly-updated question must still read as updated. A
count with no margin is not a control, which WP-105 learned the expensive way.

WHAT THE REGISTRY IS ABSORBING. Emptying STALE_ASKS and running against the tree this was written
on reports exactly the twenty-four triples registered below, and exactly one credited question
that is clean: P0.7's question 10. That is the real-tree control, not a synthetic mutation.

Negative controls (run 2026-09-07 under WP-106, each on a copied tree, run as
`unittest discover -s tests -p test_stale_asks.py` from that tree's root):
  * A new credit whose question still waits on its carrier -> test_no_credited_ask_still_waits
  * A registered question updated, entry left behind       -> test_registered_stale_asks_are_still_stale
  * A registered question's carriers change                -> test_registered_stale_asks_are_still_stale
The last three are declared NOT isolated, because what they break really does break more than
one rule and claiming otherwise would be false precision:
  * P0.7 question 10 made stale again                      -> ..._is_still_updated, and the
    (it is also the one pair the forward rule reads)          forward rule
  * A credit loses its question number                     -> ..._credits_are_found, and the
                                                              ratchet loses a registered pair
  * Every "Changes in" table removed                       -> three rules

Stdlib only:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "docs" / "architecture" / "p0"
TICKET = "#326"

QUESTIONS_HEADING = "## Open questions and dependencies"

# "The P0.4 design, question 2" and "The P0.13 design, questions 3 and 4".
CREDIT = re.compile(r"The (P0\.\d+) design,?\s+questions?\s+((?:\d+(?:\s*(?:,|and)\s*)?)+)")

# The one credited question in the pack that records its ask as answered, and the model the rest
# should follow. Asserted separately so that this module can never be satisfied by every question
# being stale - if this one goes stale too, the check that distinguishes them has stopped working.
UPDATED = ("P0.7", 10)

# Credited questions that still name their carrier inside their own `Waits on:` clause, with the
# change-row each carrier recorded. A ratchet, in the shape of
# test_checkpoints_match_schema.LEGACY and tests/test_btg1_matrix_reconciles.REGISTERED: an entry
# must STILL be stale, at exactly these carriers, so updating a question forces its entry out.
# The registry may only shrink.
#
# Not repaired here: repairing one edits a design, and whether that moves a design's version is
# unsettled (#316). WP-104 recorded these and fixed none, by the operator's instruction.
STALE_ASKS: dict[tuple[str, int], dict[str, str]] = {
    ("P0.5", 4): {
        "P0.12": "The administrative class defined by who reads it, an operator-invoked run rather than the rotation exercise al",
    },
    ("P0.5", 10): {
        "P0.4": "The adoption read of `customData` admitted as reconciliation, never authority, with that design's two conditio",
    },
    ("P0.7", 7): {
        "P0.6": "`backup_role` and `provisioning_role` in the roles table; T9; the fail-loud bullet restated",
    },
    ("P0.7", 8): {
        "P0.2": "Rule 6, no non-test path imports a test package, and control 9",
    },
    ("P0.8", 4): {
        "P0.4": "Question 2 recorded as answered by the tenant segment",
    },
    ("P0.8", 11): {
        "P0.10": "The seven codes the P0.8 design introduces, listed in the registry with that design as owner",
    },
    ("P0.9", 12): {
        "P0.10": "The outbox writer named as a second caller of the scrubber's patterns, refusing as that design's control 7 has",
        "P0.4": "The lifecycle's rows publish the P0.9 design's events through the outbox",
        "P0.5": "The tenant-provisioned event written to the platform outbox in the activation's transaction, and the section n",
        "P0.6": "`tenancy.platform_outbox` and `tenancy.platform_inbox`",
    },
    ("P0.10", 7): {
        "P0.12": "`app_role`'s `SELECT` and `INSERT` on the audit tables, and its refusal of update, delete and truncate there",
        "P0.4": "The fail-closed audit error named as the class the one-denial rule does not govern",
        "P0.6": "`app_role`'s `SELECT` and `INSERT` on the audit tables; T3's audit half; T10",
        "P0.7": "The savepoint before every business statement named as the data-access layer's duty",
    },
    ("P0.11", 7): {
        "P0.8": "The middleware setting the sampled flag by the platform's own policy and never adopting a caller's",
    },
    ("P0.11", 9): {
        "P0.10": "The decision counter recorded as exported to `biztrust.decision.count`",
        "P0.12": "The log scan's patterns named as read by the telemetry allow-list and scrubber, and by the audit scrubber the ",
        "P0.2": "The 'Observability tests' job",
    },
    ("P0.13", 2): {
        "P0.5": "The identity administration job as the command family's second command, with the same credential position, and",
    },
    ("P0.13", 3): {
        "P0.4": "`pending_identity` as a status and `administration` as a source; the resolver's answer to `GET /api/v1/me`",
    },
    ("P0.13", 4): {
        "P0.4": "`pending_identity` as a status and `administration` as a source; the resolver's answer to `GET /api/v1/me`",
        "P0.8": "`GET /api/v1/me` declared as a platform-level route scoped to the token's own organization, with the platform-",
    },
    ("P0.13", 6): {
        "P0.6": "`tenancy.tenant_setting` and `identity_access.administration_request` with its status vocabulary",
    },
    ("P0.13", 8): {
        "P0.2": "Rule 7, the control plane imports `packages/*` only with an outbound allow-list, and control 10",
    },
}

# Every (asker, question) pair some sibling's change table credits by number. Asserted as a
# set so that a credit losing its question number - which silently takes the pair out of every
# rule below - is a failure rather than a quieter suite.
EXPECTED_CREDITS = (
    ("P0.5", 4),
    ("P0.5", 10),
    ("P0.7", 7),
    ("P0.7", 8),
    ("P0.7", 10),
    ("P0.8", 4),
    ("P0.8", 11),
    ("P0.9", 12),
    ("P0.10", 7),
    ("P0.11", 7),
    ("P0.11", 9),
    ("P0.13", 2),
    ("P0.13", 3),
    ("P0.13", 4),
    ("P0.13", 6),
    ("P0.13", 8),
)

# The registry's size, asserted so it can only shrink.
REGISTERED_TRIPLES = 24


def designs() -> dict[str, Path]:
    return {
        "P0." + str(int(re.match(r"P0\.(\d+)-", p.name).group(1))): p
        for p in PACK.glob("P0.*.md")
        if "SECURITY-PROOF" not in p.name
    }


def questions(text: str) -> dict[int, str]:
    """The numbered open questions, each gathered into one blob across its wrapped lines."""
    if QUESTIONS_HEADING not in text:
        return {}
    body = text.split(QUESTIONS_HEADING, 1)[1].split("\n## ", 1)[0]
    found: dict[int, str] = {}
    current = None
    for line in body.splitlines():
        started = re.match(r"^(\d+)\.\s+(.*)$", line)
        if started:
            current = int(started.group(1))
            found[current] = started.group(2)
        elif current is not None and line.strip():
            found[current] += " " + line.strip()
    return found


def waits_on(question: str) -> str:
    """The clause naming what a question is still waiting for.

    Bounded at `ASSUMED`, and taken only from `Waits on:` onward, because a question may recite
    what it USED to wait on before saying what it waits on now - which is exactly what the pack's
    one properly-updated question does.
    """
    found = re.search(r"[Ww]aits on:(.*?)(?:`ASSUMED`|$)", question, re.S)
    return found.group(1) if found else ""


def credits() -> dict[tuple[str, int], dict[str, str]]:
    """(asker, question) -> {carrier: the change row it recorded}, for credits naming a question."""
    found: dict[tuple[str, int], dict[str, str]] = {}
    for carrier, path in designs().items():
        section = re.search(
            r"\n#+ Changes in [`0-9.]+(.*?)(?=\n#+ |\Z)", path.read_text(encoding="utf-8"), re.S
        )
        if not section:
            continue
        for line in section.group(1).splitlines():
            if not line.startswith("| ") or line.startswith("|--"):
                continue
            for credit in CREDIT.finditer(line):
                for number in re.findall(r"\d+", credit.group(2)):
                    what = line.split("|")[1].strip()
                    found.setdefault((credit.group(1), int(number)), {})[carrier] = what
    return found


def still_waiting(asker: str, number: int, carriers: dict[str, str]) -> dict[str, str]:
    """Which of a question's carriers it still names inside its own `Waits on:` clause."""
    files = designs()
    if asker not in files:
        return {}
    asked = questions(files[asker].read_text(encoding="utf-8"))
    if number not in asked:
        return {}
    clause = waits_on(asked[number])
    return {c: w for c, w in carriers.items() if c in clause}


class TestTheReaderReadsSomething(unittest.TestCase):
    """Positive controls, by name rather than by count."""

    def test_the_same_credits_are_found(self) -> None:
        """The credits naming a question, asserted as a set.

        A credit that loses its question number stops being checkable and is not reported
        anywhere, so its disappearance has to be a failure rather than a quieter suite.
        """
        self.assertEqual(
            sorted(EXPECTED_CREDITS), sorted(credits()),
            "the set of change rows crediting a design's numbered question has changed. One that "
            "has gone may have lost its number rather than its ask; one that has appeared needs "
            "adding to EXPECTED_CREDITS deliberately.",
        )

    def test_every_registered_question_exists(self) -> None:
        files = designs()
        for (asker, number), carriers in STALE_ASKS.items():
            with self.subTest(asker=asker, question=number):
                self.assertIn(asker, files, f"{asker} is registered and is not a design in the pack")
                asked = questions(files[asker].read_text(encoding="utf-8"))
                self.assertIn(number, asked, f"{asker} has no open question {number}")
                self.assertNotEqual({}, carriers, f"{asker} question {number} is registered against no carrier")

    def test_the_updated_question_is_still_updated(self) -> None:
        """P0.7's question 10 records its ask as answered. If it goes stale, so has this module.

        It names its carrier twice - "At 0.1 this waited on ... the P0.6 design's next version;
        both have landed" - and names it nowhere in its `Waits on:` clause. A reader that could
        not tell those apart would call every credited question stale and prove nothing.
        """
        asker, number = UPDATED
        carriers = credits().get((asker, number), {})
        self.assertNotEqual({}, carriers, f"{asker} question {number} is no longer credited by anyone")
        self.assertEqual(
            {}, still_waiting(asker, number, carriers),
            f"{asker} question {number} was the one credited question recorded as answered, and it "
            f"now reads as waiting again. Either the design changed or the `Waits on:` boundary "
            f"has stopped working; check the reader before the design.",
        )


class TestNoCreditedAskStillWaits(unittest.TestCase):
    def test_no_credited_ask_still_waits(self) -> None:
        """A question whose sibling says it carried the ask does not still wait on that sibling.

        Registered questions are not read here - the ratchet owns them - so updating one fires
        exactly one test.
        """
        for (asker, number), carriers in sorted(credits().items()):
            if (asker, number) in STALE_ASKS:
                continue
            with self.subTest(asker=asker, question=number):
                waiting = sorted(still_waiting(asker, number, carriers))
                self.assertEqual(
                    [], waiting,
                    f"{asker} question {number} still waits on {waiting}, and each of those "
                    f"credits this very question for carrying its ask. Either the question is "
                    f"stale or the credit is wrong; see {TICKET}. A new one is a defect, not a "
                    f"registry entry.",
                )


class TestTheRegistryIsARatchet(unittest.TestCase):
    def test_registered_stale_asks_are_still_stale(self) -> None:
        """An entry must still be stale, against exactly its carriers. An updated question leaves."""
        found = credits()
        for (asker, number), carriers in STALE_ASKS.items():
            with self.subTest(asker=asker, question=number):
                self.assertIn(
                    (asker, number), found,
                    f"{asker} question {number} is registered and no design credits it any more",
                )
                self.assertEqual(
                    sorted(carriers), sorted(still_waiting(asker, number, found[(asker, number)])),
                    f"{asker} question {number} no longer waits on exactly {sorted(carriers)}. If "
                    f"it is up to date, delete STALE_ASKS[({asker!r}, {number})]; if it waits on "
                    f"something else now, that needs its own entry and its own reason ({TICKET}).",
                )

    def test_the_registry_only_shrinks(self) -> None:
        """Membership is a deliberate edit, and every entry carries the row that contradicts it."""
        for (asker, number), carriers in STALE_ASKS.items():
            with self.subTest(asker=asker, question=number):
                for carrier, row in carriers.items():
                    # Two rows in the pack are legitimately terse - "`tenancy.platform_outbox` and
                    # `tenancy.platform_inbox`" says everything it needs to - so this asks only
                    # that an entry carries the row rather than a placeholder.
                    self.assertGreaterEqual(
                        len(row.split()), 2,
                        f"{asker} q{number}/{carrier}: an entry records the change row that credits it",
                    )
        self.assertEqual(
            REGISTERED_TRIPLES, sum(len(v) for v in STALE_ASKS.values()),
            f"the registry may only shrink; {REGISTERED_TRIPLES} triples are what the reviews under "
            f"#322 found, and a new one is a defect to fix rather than to register ({TICKET}).",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

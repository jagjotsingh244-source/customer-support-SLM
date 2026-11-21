"""One clock and two worlds.

The clock: NimbusCart has a single, frozen NOW. Seeding, the system prompt
("Today is 20 November 2026"), every eligibility check (return windows, late
deliveries, refund timelines) and every eval read it through now(). Nothing
else in the repo may ask the operating system or the database for the time;
scripts/check_clock.sh enforces that. A golden case written today must still
pass months later, so in development and evals the clock never moves. When
Nova serves real traffic, now() is the one place to switch to the real time.

The two worlds: every customer belongs to the train or the eval partition.
Synthetic training conversations may only use train customers; golden eval
cases may only use eval customers. The split is by customer, not by order, so
no customer is seen on both sides.
"""

import hashlib
from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
NOW = datetime(2026, 11, 20, 10, 0, tzinfo=IST)  # frozen for development and evals
SEED = 3407
EVAL_SHARE = 0.20

# Return window in days after delivery, by product category. One copy for the
# seed (db/seed.py), the agent's eligibility check (agent/tools_v0.py) and the
# help-center check (scripts/check_kb.py, via the seed).
WINDOW_DAYS = {"electronics": 7, "home": 15, "accessories": 15}


def now() -> datetime:
    """The only way any code in this repo asks for the time."""
    return NOW


def partition_for(customer_id: int) -> str:
    """'eval' for about EVAL_SHARE of customers, 'train' for the rest.

    A hash of the ID, not a random draw: a customer's side never changes, even
    when the seed adds more customers or the generation order changes. sha256
    rather than Python's hash(), which is salted per process for strings.
    """
    h = int(hashlib.sha256(str(customer_id).encode()).hexdigest(), 16)
    return "eval" if (h % 100) < EVAL_SHARE * 100 else "train"

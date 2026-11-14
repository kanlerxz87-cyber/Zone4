"""Zone4 affiliate platform.

An evidence-first automation layer for Amazon Associates content operations.

Design rule that governs the whole package: **a value that has not been read
from an official source is never invented, never estimated, and never
published.** Unverified fields stay ``None`` and are surfaced as flags that a
human can resolve, so generated articles, tables, and reports cannot silently
carry hallucinated product facts.

Modules
-------
config      runtime configuration (credentials are optional, never required)
datastore   loads/validates ``data/*.json`` — the single source of truth
economics   category commission lookup + per-unit earning math
policy      Amazon Associates / FTC compliance gates (blocking, advisory)
research    identifier validation, product-record intake, optional API client
links       Special Link construction and link-safety checks
content     SEO draft generation (review, comparison, buying guide)
tracking    click/conversion/earning ledger + attribution windows
scoring     niche and product opportunity scoring (withheld without inputs)
agent       orchestrates the research → verify → draft → gate → publish queue
sitegen     renders the static GitHub Pages site from the same verified data
"""

from .datastore import Datastore, Status  # noqa: F401

__all__ = ["Datastore", "Status"]
__version__ = "0.1.0"

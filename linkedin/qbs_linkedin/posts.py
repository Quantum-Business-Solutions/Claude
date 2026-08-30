"""Post selection and comment dedupe.

Every rule here comes from a live API behaviour that contradicts the obvious
implementation. Each one, written the obvious way, fails silently.

**Dedupe cannot be done per post.** ``GET /posts/{id}/comments`` returns
TOP-LEVEL COMMENTS ONLY; replies need a separate ``&comment_id=`` call. Proved
on activity ``7495818623802916864``: the post reports ``comment_counter: 11``,
the comments list returns ``total_items: 8`` with ``cursor: null`` — i.e.
"complete" — and Shawn's own comment is one of the three missing replies. A
per-post check therefore reports "Shawn has not commented" about a post he
commented on four days earlier, and the routine comments again. Read his
comments across all posts instead: one call, includes replies, and cheaper.

**The join key is not the post's id.** ``Comment.post_id`` matches the numeric
tail of ``social_id``, not ``id``. For ``urn:li:ugcPost:7495561989247856640``
the post's own ``id`` is ``7495561990287826944`` — different numbers. Joining
on ``id`` silently returns False for every ugcPost and groupPost, roughly half
a typical feed.

**There is no ``created_at``.** ``date`` is a relative string ("3d", "1w").
Use ``parsed_datetime``. On a reshare that is the RESHARE time, so a freshness
window happily admits someone resharing months-old content.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .config import (
    POST_TIMESTAMP_FIELD,
    SKIP_POST_URN_PREFIXES,
    SKIP_REPOSTS,
)

#: Comment-level `network_distance` uses DISTANCE_1/2/3 while the profile
#: endpoint uses FIRST_DEGREE/…, the published schema documents it wrongly,
#: and Shawn's own comment reports DISTANCE_3 for himself. Identify him by
#: provider id and nothing else.
SELF_MATCH_FIELD = "author_details.id"


def post_join_key(social_id: str | None) -> str | None:
    """The id a Comment will carry for this post."""
    if not social_id:
        return None
    return social_id.rsplit(":", 1)[-1]


class IncompleteDedupeError(RuntimeError):
    """The dedupe set was built from a partial comment feed."""


def commented_post_ids(
    self_comments: list[dict],
    pages_fetched: int = 1,
    page_count: int | None = None,
) -> set[str]:
    """Post ids Shawn has already commented on, from his own comment feed.

    Accepts either `post_id` or `post_urn`, since the feed carries both and
    only one is guaranteed on every entry.

    The feed PAGINATES -- Shawn's is 26 pages at limit=25. A caller that reads
    only page one builds a dedupe set covering his newest 25 comments and
    silently re-comments on everything older. Pass `page_count` from the
    response's `paging` and this refuses to hand back a partial set.
    """
    if page_count is not None and pages_fetched < page_count:
        raise IncompleteDedupeError(
            f"only {pages_fetched} of {page_count} comment pages were read. "
            "A partial dedupe set causes double-comments on older posts — "
            "page to the end before building it."
        )

    seen: set[str] = set()
    for comment in self_comments or []:
        for key in ("post_id", "post_urn"):
            value = comment.get(key)
            if value:
                resolved = post_join_key(str(value))
                if resolved:
                    seen.add(resolved)
    return seen


def parse_post_time(value: str | None) -> datetime | None:
    """Parse `parsed_datetime` (absolute ISO), tolerating a trailing Z."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


@dataclass(frozen=True)
class PostDecision:
    eligible: bool
    reason: str
    join_key: str | None = None


def evaluate_post(
    post: dict,
    already_commented: set[str],
    freshness_hours: int,
    now: datetime | None = None,
    skip_reposts: bool = SKIP_REPOSTS,
) -> PostDecision:
    """Decide whether a post is worth commenting on.

    Ordered so the cheapest and most certain exclusions come first, and so a
    missing timestamp can never be read as "fresh".
    """
    now = now or datetime.now(timezone.utc)
    social_id = post.get("social_id") or ""
    key = post_join_key(social_id)

    if not key:
        return PostDecision(False, "post carries no social_id")

    # Private-group posts have author.id == None and are invisible to the
    # prospect's network, so a comment there is worthless for warming and any
    # author comparison would crash on the None.
    if any(social_id.startswith(p) for p in SKIP_POST_URN_PREFIXES):
        return PostDecision(False, "group post — invisible to their network", key)

    # v2 hands us BOTH urns for a post (activity and ugcPost); a v1 post has
    # only the one. Shawn's comment may carry either tail -- posts.py's own
    # docstring above records that Comment.post_id follows social_id, and for
    # a ugcPost that is a different number from the activity id. Checking only
    # the preferred urn re-comments on posts he has already answered, which is
    # the failure this module exists to prevent. So test every urn we hold.
    candidate_keys = {key} | {
        k for k in (post_join_key(str(u)) for u in post.get("_all_urn_ids") or [])
        if k
    }
    hit = candidate_keys & already_commented
    if hit:
        return PostDecision(False, "already commented", key)

    if skip_reposts and post.get("is_repost"):
        return PostDecision(
            False,
            "reshare — parsed_datetime is the reshare time, and the substance "
            "is in repost_content rather than the text we would score",
            key,
        )

    posted = parse_post_time(post.get(POST_TIMESTAMP_FIELD))
    if posted is None:
        # Never infer freshness from the relative `date` string.
        return PostDecision(False, "no parsable parsed_datetime", key)

    if posted > now + timedelta(minutes=5):
        # article.published_at carries impossible values (a 2028 date was
        # observed); refuse anything from the future rather than trust it.
        return PostDecision(False, f"timestamp is in the future ({posted})", key)

    age = now - posted
    if age > timedelta(hours=freshness_hours):
        return PostDecision(False, f"older than {freshness_hours}h ({age})", key)

    if post.get("permissions", {}).get("can_post_comments") is False:
        return PostDecision(False, "comments disabled on this post", key)

    return PostDecision(True, f"fresh ({age}) and not yet commented", key)

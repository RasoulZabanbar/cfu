"""
Analytics endpoints for the participant dashboard.

No new tables needed -- `province` and `university` are already plain
CharFields on Participant. This just GROUPs BY them and COUNTs, scoped
to whichever event the admin picks in the dashboard's dropdown.

Add to your app (e.g. in main.py):
    from services.stats import router as stats_router
    app.include_router(stats_router)

Also requires CORS enabled if the dashboard HTML is opened from a
different origin than the API (see the CORS note at the bottom of
this file).
"""

from fastapi import APIRouter, HTTPException, Query
from tortoise.functions import Count

from models.user import Event, Participant

router = APIRouter(prefix="/stats", tags=["stats"])

UNKNOWN_LABEL = "نامشخص"  # shown for empty/null province or university



# dispatchers/academics/degrees_fields.py
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates



templates = Jinja2Templates(directory="templates")

@router.get("/loader_stats")
async def degree_field_management_webview(
    request: Request
):
    
    return templates.TemplateResponse(request, "states_participents.html")




async def _ranked_counts(field: str, event_name: str) -> list[dict]:
    """
    Group participants of one event by `field` (province or university),
    count how many fall in each group, and return them ranked
    highest-first. Joins through EventParticipant -> Event since that's
    a real relation; province/university stay simple string GROUP BYs.
    """
    qs = Participant.filter(event_participants__event__name=event_name)

    rows = (
        await qs.annotate(count=Count("id"))
        .group_by(field)
        .order_by("-count")
        .values(field, "count")
    )

    # Merge None/empty/whitespace-only values into one "unknown" bucket
    # so trivial blanks don't fragment the ranking.
    merged: dict[str, int] = {}
    for row in rows:
        raw_value = row[field]
        label = (raw_value or "").strip() or UNKNOWN_LABEL
        merged[label] = merged.get(label, 0) + row["count"]

    ranked = sorted(merged.items(), key=lambda kv: kv[1], reverse=True)
    return [{"label": label, "count": count} for label, count in ranked]


@router.get("/events")
async def list_events():
    """All events, for the dashboard's event-select dropdown."""
    events = await Event.all().order_by("name")
    return [{"id": e.id, "name": e.name} for e in events]


@router.get("/summary")
async def summary(
    event_name: str = Query(..., description="Exact Event.name to scope the ranking to"),
    top_n: int = Query(5, ge=1, le=50),
):
    """
    One call for the dashboard: top-N provinces AND top-N universities
    for a single event, plus the total participant count for that event
    (so the UI can show '41 of 63 شرکت‌کننده' style context).
    """
    event = await Event.get_or_none(name=event_name)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    total_participants = await Participant.filter(
        event_participants__event__name=event_name
    ).count()

    province_ranking = await _ranked_counts("province", event_name)
    university_ranking = await _ranked_counts("university", event_name)

    return {
        "event_name": event_name,
        "total_participants": total_participants,
        "top_province": province_ranking[:top_n],
        "top_university": university_ranking[:top_n],
    }


# ----------------------------------------------------------------------
# CORS note
# ----------------------------------------------------------------------
# If the dashboard HTML file is opened as a local file (file://) or
# hosted on a different origin than https://cfu.mirzahesab.ir, the
# browser will block the fetch() calls unless the API allows it. Add
# this to main.py if you hit CORS errors in the browser console:
#
#   from fastapi.middleware.cors import CORSMiddleware
#   app.add_middleware(
#       CORSMiddleware,
#       allow_origins=["*"],       # or restrict to your dashboard's real origin
#       allow_methods=["GET"],
#       allow_headers=["*"],
#   )
#
# allow_origins=["*"] is fine here since these are read-only GET
# endpoints with no auth/session data involved -- there's nothing for
# a malicious site to steal by calling them. If that ever changes
# (e.g. you add an admin-auth-gated endpoint), tighten this.
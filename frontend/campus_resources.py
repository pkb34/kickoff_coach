"""Curated Virginia Tech links selected from a student's stated interests and needs."""

from __future__ import annotations


RESOURCE_CATALOG = {
    "sport_clubs": ("Explore VT sport clubs", "https://recsports.vt.edu/sportclubs.html",
                    "For students who enjoy team sports and want to see what clubs are available."),
    "recreation": ("Find McComas gym and pool", "https://recsports.vt.edu/facilities/mccomas.html",
                   "A place to move at your own pace, whether or not you join a team."),
    "arts": ("Explore VT arts and design clubs", "https://aad.vt.edu/academics/clubs.html",
             "Creative groups and projects you can explore when you feel like making something."),
    "volunteer": ("Find service opportunities with VT Engage", "https://engage.vt.edu/",
                  "A starting point for volunteering and community service at VT."),
    "organizations": ("Browse student organizations", "https://gobblerconnect.vt.edu/club_signup?view=all",
                      "Find people who share a club interest or discover something new."),
    "sleep": ("Explore Hokie Wellness sleep resources", "https://hokiewellness.vt.edu/students/program_areas/sleep.html",
              "For ideas about rest and routines, if that would help."),
    "tutoring": ("Explore VT peer tutoring", "https://studentsuccess.vt.edu/tutoring-program.html",
                 "A course-specific place to talk through material with a peer tutor."),
    "counseling": ("Connect with Cook Counseling Center", "https://ucc.vt.edu/",
                   "For confidential support if you would like to talk with someone."),
}


def recommendations(record: dict, analysis: dict | None) -> list[tuple[str, str, str]]:
    """Suggest official resources; no diagnosis or sensitive profiling."""
    fields = record.get("baseline", {}).get("fields", {})
    activity = fields.get("activity_type", {})
    kind = (activity.get("value") or "").casefold() if activity.get("status") == "answered" else ""
    keys: list[str] = []
    if "sport" in kind or "movement" in kind:
        keys.extend(["sport_clubs", "recreation"])
    elif "art" in kind or "music" in kind:
        keys.append("arts")
    elif "volunteer" in kind:
        keys.append("volunteer")
    else:
        keys.append("organizations")

    followups = record.get("followups", {})
    if followups.get("sleep_quality", {}).get("answer") == "Usually tired":
        keys.append("sleep")
    support_text = (followups.get("support_preference", {}).get("answer") or "").casefold()
    progress = followups.get("academic_progress", {}).get("answer")
    if progress in ("Feeling behind", "Keeping up, but stretched") or any(term in support_text for term in ("tutor", "class", "study", "course", "assignment")):
        keys.append("tutoring")
    happiness = (analysis or {}).get("metrics", {}).get("self_reported_happiness_index")
    if (happiness is not None and happiness <= 40 or
            followups.get("campus_belonging", {}).get("answer") == "I feel disconnected"):
        keys.append("counseling")
    return [RESOURCE_CATALOG[key] for key in dict.fromkeys(keys)]

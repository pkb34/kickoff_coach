"""Illustrative national-team styles for the four existing demo roles.

These are editorial matches, not psychometric or sports-performance claims.
Sources describe the cited team era; they do not validate a student-to-team match.
"""

from __future__ import annotations

from copy import deepcopy


MATCHES = {
    "midfielder": {
        "national_team": "Spain",
        "team_style": "A possession tradition built on midfield links, passing options, and reading space.",
        "team_description": "Your Midfielder result is a metaphor for connecting study, activities, and rest. Spain's passing style is a playful match for someone who keeps different parts of the week moving together.",
        "team_source": "https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/spain-midfield-maestros",
    },
    "captain": {
        "national_team": "Argentina (2022)",
        "team_style": "A united squad in which teammates understood their roles and supported one another.",
        "team_description": "Your Captain result highlights time spent carrying group commitments. Argentina's 2022 collective spirit is an illustrative match for organizing with others and making room for teammates.",
        "team_source": "https://www.fifa.com/es/articles/copa-america-final-copa-mundial-argentina-messi-scaloni-catar-2022",
    },
    "penalty_striker": {
        "national_team": "France",
        "team_style": "A direct attacking analogy centered on pace and decisive finishing.",
        "team_description": "Your Penalty Striker result represents focused effort when a clear task matters. France's attacking moments provide a football image for turning preparation into a decisive move.",
        "team_source": "https://www.fifa.com/en/articles/kylian-mbappe-france-quotes-records",
    },
    "defender": {
        "national_team": "Italy (defensive tradition)",
        "team_style": "A historical emphasis on defensive organization and protecting the team shape.",
        "team_description": "Your Defender result is a metaphor for steady structure and protecting time for what matters. Italy's defensive tradition is a playful match for that role.",
        "team_source": "https://www.uefa.com/uefaeuro/history/news/0253-0d815d2171c4-a3bda62296f1-1000--uefa-euro-reporter-s-view-italy/",
    },
}


def match_football_identity(personality: str) -> dict:
    if personality not in MATCHES:
        raise ValueError("No national-team style exists for this demo role.")
    return deepcopy(MATCHES[personality])

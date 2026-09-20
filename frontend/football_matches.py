"""Illustrative football analogies for the four existing demo roles.

These are editorial matches, not psychometric or sports-performance claims.
Sources describe the cited team era or player style; they do not validate a
student-to-team match.
"""

from __future__ import annotations

from copy import deepcopy


MATCHES = {
    "midfielder": {
        "national_team": "Spain",
        "team_style": "A possession tradition built on midfield links, passing options, and reading space.",
        "team_description": "Your Midfielder result is a metaphor for connecting study, activities, and rest. Spain's passing style is a playful match for someone who keeps different parts of the week moving together.",
        "team_source": "https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/spain-midfield-maestros",
        "player": "Andrés Iniesta",
        "player_explanation": "Iniesta is the player analogy because his game was known for seeing a pass and linking teammates. The comparison describes a football role, not your actual ability or personality.",
        "player_source": "https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/andres-iniesta-emirates-club-spain-barcelona-captain-tsubasa",
    },
    "captain": {
        "national_team": "Argentina (2022)",
        "team_style": "A united squad in which teammates understood their roles and supported one another.",
        "team_description": "Your Captain result highlights time spent carrying group commitments. Argentina's 2022 collective spirit is an illustrative match for organizing with others and making room for teammates.",
        "team_source": "https://www.fifa.com/es/articles/copa-america-final-copa-mundial-argentina-messi-scaloni-catar-2022",
        "player": "Lionel Messi",
        "player_explanation": "Messi is the player analogy for a captain who can influence a match while working within a close team. This is a playful comparison, not a claim about leadership ability.",
        "player_source": "https://www.fifa.com/es/watch/33zkFSWUsMjDrEvgpgQatG",
    },
    "penalty_striker": {
        "national_team": "France",
        "team_style": "A direct attacking analogy centered on pace and decisive finishing.",
        "team_description": "Your Penalty Striker result represents focused effort when a clear task matters. France's attacking moments provide a football image for turning preparation into a decisive move.",
        "team_source": "https://www.fifa.com/en/articles/kylian-mbappe-france-quotes-records",
        "player": "Kylian Mbappé",
        "player_explanation": "Mbappé is the player analogy for speed and finishing in key moments. The quiz is comparing styles of play, not predicting how you perform under pressure.",
        "player_source": "https://www.fifa.com/en/articles/kylian-mbappe-france-quotes-records",
    },
    "defender": {
        "national_team": "Italy (defensive tradition)",
        "team_style": "A historical emphasis on defensive organization and protecting the team shape.",
        "team_description": "Your Defender result is a metaphor for steady structure and protecting time for what matters. Italy's defensive tradition is a playful match for that role.",
        "team_source": "https://www.uefa.com/uefaeuro/history/news/0253-0d815d2171c4-a3bda62296f1-1000--uefa-euro-reporter-s-view-italy/",
        "player": "Giorgio Chiellini",
        "player_explanation": "Chiellini is the player analogy for organizing a back line and staying dependable. The match is illustrative and says nothing about your real-world traits.",
        "player_source": "https://www.uefa.com/euro2024/news/025f-0fd29745df66-f9507a69f615-1000--euro-winning-captains/",
    },
}


def match_football_identity(personality: str) -> dict:
    if personality not in MATCHES:
        raise ValueError("No football analogy exists for this demo role.")
    return deepcopy(MATCHES[personality])

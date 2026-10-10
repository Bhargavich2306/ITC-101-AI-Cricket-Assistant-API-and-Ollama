from flask import Flask, jsonify, request, send_from_directory
import requests
import os
import re
import html
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

load_dotenv()

app = Flask(__name__, static_folder=".")

CRICKET_API_KEY = os.getenv("CRICKET_API_KEY", "").strip()
CRICKET_BASE = "https://api.cricapi.com/v1"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2"

# =========================================================
# CACHE
# =========================================================

MATCH_CACHE = {
    "data": None,
    "time": 0,
    "month": None
}

SQUAD_CACHE = {}
PLAYER_CACHE = {}


# =========================================================
# INTERNATIONAL TEAMS
# =========================================================

INTERNATIONAL_TEAMS = {
    "afghanistan", "australia", "bangladesh", "canada", "england",
    "india", "ireland", "namibia", "nepal", "netherlands", "new zealand",
    "oman", "pakistan", "papua new guinea", "scotland", "south africa",
    "sri lanka", "uganda", "united arab emirates", "united states",
    "west indies", "zimbabwe", "hong kong", "italy", "jersey", "kenya",
    "malaysia", "qatar", "tanzania", "vanuatu", "bermuda", "fiji",
    "germany", "japan", "spain", "france", "rwanda", "zambia",
    "malawi", "botswana", "ghana", "nigeria", "samoa", "singapore",
    "thailand", "bahrain", "kuwait"
}

TEAM_ALIASES = {
    "united states of america": "united states",
    "usa": "united states",
    "u.s.a": "united states",
    "u.a.e": "united arab emirates",
    "uae": "united arab emirates",
    "wi": "west indies",
}

BLOCKED_COMPETITIONS = [
    "ipl", "cpl", "bbl", "psl", "mlc", "the hundred", "hundred",
    "county", "ranji", "vitality", "blast", "big bash", "super smash",
    "syed mushtaq", "premier league", "super league", "t20 challenge",
    "sa20", "lpl", "bpl", "tamil nadu premier", "sheffield shield",
    "marsh one day", "domestic one-day", "county championship"
]


# =========================================================
# HELPERS
# =========================================================

def clean_text(value):
    if value is None:
        return ""
    return html.unescape(str(value)).strip()


def cricket_request(endpoint, params=None, timeout=20):
    if not CRICKET_API_KEY:
        return {
            "status": "failure",
            "message": "CRICKET_API_KEY not configured"
        }

    params = dict(params or {})
    params["apikey"] = CRICKET_API_KEY
    params.setdefault("offset", 0)

    try:
        response = requests.get(
            f"{CRICKET_BASE}/{endpoint}",
            params=params,
            timeout=timeout
        )

        if response.status_code != 200:
            return {
                "status": "failure",
                "message": f"HTTP {response.status_code}"
            }

        return response.json()

    except Exception as exc:
        return {
            "status": "failure",
            "message": str(exc)
        }


# =========================================================
# INTERNATIONAL MATCH FILTER
# =========================================================

def normalized_team_name(name):
    value = clean_text(name).lower()
    value = re.sub(r"\s+women$", "", value)
    value = re.sub(r"\s+men$", "", value)
    value = re.sub(r"[^a-z0-9 ]", "", value)
    value = re.sub(r"\s+", " ", value).strip()

    return TEAM_ALIASES.get(value, value)


def is_international_team(name):
    return normalized_team_name(name) in INTERNATIONAL_TEAMS


def is_international_match(match):

    teams = match.get("teams") or []

    # Normal API match
    if len(teams) >= 2:

        if all(is_international_team(team) for team in teams[:2]):

            text = (
                clean_text(match.get("name", "")) + " " +
                clean_text(match.get("series", ""))
            ).lower()

            return not any(
                blocked in text
                for blocked in BLOCKED_COMPETITIONS
            )

        return False

    # Historical match
    text = (
        clean_text(match.get("name", "")) + " " +
        clean_text(match.get("series", ""))
    ).lower()

    detected = []

    for team in sorted(
        INTERNATIONAL_TEAMS,
        key=len,
        reverse=True
    ):
        if team.lower() in text:
            detected.append(team)

    if len(set(detected)) < 2:
        return False

    return not any(
        blocked in text
        for blocked in BLOCKED_COMPETITIONS
    )


def match_date(match):

    candidates = [
        match.get("date"),
        match.get("dateTimeGMT")
    ]

    for value in candidates:

        if not value:
            continue

        text = str(value).strip()

        m = re.search(
            r"(\d{4}-\d{2}-\d{2})",
            text
        )

        if m:
            return m.group(1)

        try:
            return datetime.fromisoformat(
                text.replace("Z", "+00:00")
            ).date().isoformat()

        except Exception:
            pass

    return ""


def current_month():
    now = datetime.now(
        ZoneInfo("Asia/Kolkata")
    )

    return now.strftime("%Y-%m")


# =========================================================
# CRICKET API MATCHES
# =========================================================

def get_api_matches():

    collected = {}

    for offset in range(0, 201, 25):

        result = cricket_request(
            "matches",
            {
                "offset": offset
            },
            timeout=20
        )

        if result.get("status") != "success":

            print(
                "MATCH LIST ERROR:",
                result.get("message")
            )

            if offset == 0:
                break

            continue

        page = result.get(
            "data",
            []
        ) or []

        if not isinstance(page, list) or not page:
            break

        for match in page:

            if not isinstance(match, dict):
                continue

            date = match_date(match)

            if not date:
                continue

            match_copy = dict(match)

            match_copy["_date"] = date

            key = str(
                match.get("id")
                or f"{date}-{match.get('name')}"
            )

            collected[key] = match_copy

    return list(collected.values())


def get_current_matches():

    result = cricket_request(
        "currentMatches",
        {
            "offset": 0
        },
        timeout=20
    )

    if result.get("status") != "success":

        print(
            "CURRENT MATCH ERROR:",
            result.get("message")
        )

        return []

    data = result.get(
        "data",
        []
    ) or []

    return (
        data
        if isinstance(data, list)
        else []
    )

def get_current_matches():

    result = cricket_request(
        "currentMatches",
        {"offset": 0},
        timeout=20
    )

    if result.get("status") != "success":

        print(
            "CURRENT MATCH ERROR:",
            result.get("message")
        )

        return []

    data = result.get("data", []) or []

    return data if isinstance(data, list) else []


# =========================================================
# HISTORICAL RESULTS
# =========================================================

def extract_historical_match_id(href):

    if not href:
        return None

    href = html.unescape(str(href))

    try:

        parsed = urlparse(href)
        query = parse_qs(parsed.query)

        for key in (
            "id",
            "matchid",
            "matchId",
            "match_id"
        ):

            values = query.get(key)

            if values and values[0]:
                return values[0]

    except Exception:
        pass

    patterns = [
        r"[?&](?:id|matchid|matchId|match_id)=([^&#]+)",
        r"/match(?:es)?/([^/?#]+)",
        r"/match[_-]?details/([^/?#]+)",
    ]

    for pattern in patterns:

        found = re.search(
            pattern,
            href,
            flags=re.I
        )

        if found:
            return found.group(1)

    return None


def find_international_teams(
    text,
    image_alts=None
):

    candidates = []

    for value in image_alts or []:

        value = clean_text(value)

        value = re.sub(
            r"^Image:\s*",
            "",
            value,
            flags=re.I
        )

        if value:
            candidates.append(value)

    lowered = clean_text(text).lower()

    for team in sorted(
        INTERNATIONAL_TEAMS,
        key=len,
        reverse=True
    ):

        if team in lowered:
            candidates.append(team.title())

    answer = []
    seen = set()

    for candidate in candidates:

        normalized = normalized_team_name(
            candidate
        )

        if (
            is_international_team(candidate)
            and normalized not in seen
        ):

            answer.append(candidate)
            seen.add(normalized)

        if len(answer) == 2:
            break

    return answer


def get_historical_results(month):

    results = []

    try:

        url = (
            "https://cricketdata.org/"
            "cricket-data-formats/results"
        )

        response = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0"
            },
            timeout=20
        )

        print(
            "PAST MATCHES STATUS:",
            response.status_code
        )

        if response.status_code != 200:
            return []

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        current_date = None

        rows = soup.find_all("tr")

        for row in rows:

            row_text = clean_text(
                row.get_text(
                    " ",
                    strip=True
                )
            )

            if not row_text:
                continue

            date_match = re.search(
                r"(\d{1,2})\s+"
                r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|"
                r"Sep|Oct|Nov|Dec)\s+"
                r"(\d{4})",
                row_text,
                re.IGNORECASE
            )

            if date_match:

                month_numbers = {
                    "jan": 1,
                    "feb": 2,
                    "mar": 3,
                    "apr": 4,
                    "may": 5,
                    "jun": 6,
                    "jul": 7,
                    "aug": 8,
                    "sep": 9,
                    "oct": 10,
                    "nov": 11,
                    "dec": 12
                }

                current_date = (
                    f"{int(date_match.group(3)):04d}-"
                    f"{month_numbers[date_match.group(2).lower()]:02d}-"
                    f"{int(date_match.group(1)):02d}"
                )

            if (
                not current_date
                or not current_date.startswith(month)
            ):
                continue

            details_link = None

            for link in row.find_all(
                "a",
                href=True
            ):

                if "details" in clean_text(
                    link.get_text(
                        " ",
                        strip=True
                    )
                ).lower():

                    details_link = link
                    break

            if not details_link:
                continue

            href = details_link.get(
                "href",
                ""
            )

            match_id = extract_historical_match_id(
                href
            )

            if not match_id:

                uuid_match = re.search(
                    r"([0-9a-fA-F]{8}-"
                    r"[0-9a-fA-F]{4}-"
                    r"[0-9a-fA-F]{4}-"
                    r"[0-9a-fA-F]{4}-"
                    r"[0-9a-fA-F]{12})",
                    href
                )

                if uuid_match:
                    match_id = uuid_match.group(1)

            if not match_id:
                continue

            image_alts = [
                clean_text(
                    img.get("alt", "")
                )
                for img in row.find_all("img")
                if img.get("alt")
            ]

            teams = find_international_teams(
                row_text,
                image_alts
            )

            if len(teams) >= 2:

                team1 = teams[0]
                team2 = teams[1]

                match_name = (
                    f"{team1} vs {team2}"
                )

            else:

                team1 = ""
                team2 = ""

                vs_match = re.search(
                    r"([A-Za-z][A-Za-z .&'’-]+?)"
                    r"\s+vs\s+"
                    r"([A-Za-z][A-Za-z .&'’-]+?)"
                    r"(?:\s+Details|$)",
                    row_text,
                    re.IGNORECASE
                )

                if vs_match:

                    match_name = (
                        f"{clean_text(vs_match.group(1))}"
                        f" vs "
                        f"{clean_text(vs_match.group(2))}"
                    )

                else:

                    match_name = row_text

            cells = [
                clean_text(
                    td.get_text(
                        " ",
                        strip=True
                    )
                )
                for td in row.find_all("td")
            ]

            series = (
                cells[0]
                if len(cells) >= 1
                else ""
            )

            venue = (
                cells[1]
                if len(cells) >= 2
                else ""
            )

            result_text = (
                cells[2]
                if len(cells) >= 3
                else ""
            )

            if not series:
                series = "International"

            results.append({

                "id": match_id,

                "name": match_name,

                "teams": (
                    [team1, team2]
                    if len(teams) >= 2
                    else []
                ),

                "series": series,

                "venue": venue,

                "status": (
                    result_text
                    or "Match completed"
                ),

                "dateTimeGMT": (
                    current_date
                    + "T00:00:00"
                ),

                "_date": current_date,

                "_historical": True,

                "matchStarted": True,

                "matchEnded": True,
            })

        unique = {}

        for match in results:
            unique[
                str(match["id"])
            ] = match

        results = list(
            unique.values()
        )

        print(
            f"HISTORICAL RESULTS "
            f"{month}: "
            f"{len(results)} entries"
        )

        if results:
            print(
                "DEBUG FIRST HISTORICAL:",
                results[0]
            )

        return results

    except Exception as exc:

        print(
            "HISTORICAL RESULTS ERROR:",
            exc
        )

        return []


# =========================================================
# MONTH MATCHES
# =========================================================

def get_month_matches(month=None):

    # =====================================================
    # USE THE MONTH REQUESTED BY THE FRONTEND
    # =====================================================

    month = month or current_month()
    print("GET MONTH CALLED:", month)
    print("CACHE MONTH:", MATCH_CACHE["month"])
    print("CACHE DATA COUNT:", len(MATCH_CACHE["data"] or []))

    if (
        MATCH_CACHE["data"] is not None
        and MATCH_CACHE["month"] == month
        and time.time() - MATCH_CACHE["time"] < 1800
    ):
        return MATCH_CACHE["data"]

    collected = {}

    # =====================================================
    # HISTORICAL MATCHES
    # =====================================================

    historical = get_historical_results(month)

    for match in historical:

        if not is_international_match(match):
            continue

        teams = match.get("teams") or []

        # Ignore incomplete/bad historical records
        if len(teams) < 2:
            continue

        date = match.get("_date") or match_date(match)

        team1 = normalized_team_name(teams[0])
        team2 = normalized_team_name(teams[1])

        key = f"{date}|{min(team1, team2)}|{max(team1, team2)}"

        collected[key] = match

    # =====================================================
    # API MATCHES
    # =====================================================

    api_matches = get_api_matches()

    for match in api_matches:

        if not is_international_match(match):
            continue

        date = match_date(match)

        if not date.startswith(month):
            continue

        teams = match.get("teams") or []

        if len(teams) < 2:
            continue

        match_copy = dict(match)
        match_copy["_date"] = date

        team1 = normalized_team_name(teams[0])
        team2 = normalized_team_name(teams[1])

        key = f"{date}|{min(team1, team2)}|{max(team1, team2)}"

        # API data is preferred because it usually contains
        # the real score, wickets and overs.
        collected[key] = {
            **collected.get(key, {}),
            **match_copy
        }

    # =====================================================
    # CURRENT MATCHES
    # =====================================================

    current = get_current_matches()

    for match in current:

        if not is_international_match(match):
            continue

        date = match_date(match)

        if not date.startswith(month):
            continue

        teams = match.get("teams") or []

        if len(teams) < 2:
            continue

        match_copy = dict(match)
        match_copy["_date"] = date

        team1 = normalized_team_name(teams[0])
        team2 = normalized_team_name(teams[1])

        key = f"{date}|{min(team1, team2)}|{max(team1, team2)}"

        collected[key] = {
            **collected.get(key, {}),
            **match_copy
        }

    # =====================================================
    # FINAL MATCH LIST
    # =====================================================

        # =====================================================
    # FINAL MATCH LIST
    # =====================================================

    matches = list(collected.values())

        # Fetch scorecard data for completed matches
    # when the match-list API did not provide scores.
    for match in matches:

        if not match.get("matchEnded"):
            continue

        existing_scores = match.get("score") or []

        if existing_scores:
            continue

        match_id = match.get("id")

        # Historical match IDs may contain the real UUID at the end.
        uuid_match = re.search(
            r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})$",
            str(match_id or "")
        )

        if uuid_match:
            match_id = uuid_match.group(1)

        if not match_id:
            continue

        try:
            scorecard = cricket_request(
                "match_scorecard",
                {
                    "id": match_id,
                    "offset": 0
                },
                timeout=20
            )
            print("SCORECARD RESPONSE:", scorecard)
            print("SCORECARD DATA:", scorecard.get("data"))
            if scorecard.get("status") != "success":
                continue

            scorecard_data = scorecard.get(
                "data",
                {}
            )

            if not isinstance(scorecard_data, dict):
                continue

            score_data = scorecard_data.get("score") or []

            if score_data:
                match["score"] = score_data

        except Exception as exc:
            print(
                "SCORECARD LOOKUP ERROR:",
                match_id,
                exc
            )

    matches.sort(

        key=lambda item: (
            item.get("_date", ""),
            item.get("dateTimeGMT", "")
        ),
        reverse=True
    )

    MATCH_CACHE["data"] = matches
    MATCH_CACHE["time"] = time.time()
    MATCH_CACHE["month"] = month

    print(
        f"MONTH {month}: "
        f"{len(matches)} international matches"
    )

    return matches


def get_all_matches(month=None):
    return get_month_matches(month or current_month())


# =========================================================
# NORMALIZE MATCH
# =========================================================

def normalize_match(match):

    teams = match.get("teams") or []

    team1 = (
        teams[0]
        if len(teams) > 0
        else "Team 1"
    )

    team2 = (
        teams[1]
        if len(teams) > 1
        else "Team 2"
    )

    team1 = clean_text(team1)
    team2 = clean_text(team2)

    scores = match.get("score") or []

    score1 = None
    score2 = None

    overs1 = None
    overs2 = None

    wickets1 = 0
    wickets2 = 0

    for score in scores:

        if not isinstance(score, dict):
            continue

        runs = score.get("r")
        wickets = score.get("w", 0)
        overs = score.get("o")

        inning = clean_text(
            score.get("inning", "")
        ).lower()

        if team1.lower() in inning:

            score1 = runs
            wickets1 = wickets
            overs1 = overs

        elif team2.lower() in inning:

            score2 = runs
            wickets2 = wickets
            overs2 = overs

    # Fallback
    if (
        score1 is None
        and len(scores) > 0
    ):

        if isinstance(
            scores[0],
            dict
        ):

            score1 = scores[0].get("r")
            wickets1 = scores[0].get("w", 0)
            overs1 = scores[0].get("o")

    if (
        score2 is None
        and len(scores) > 1
    ):

        if isinstance(
            scores[1],
            dict
        ):

            score2 = scores[1].get("r")
            wickets2 = scores[1].get("w", 0)
            overs2 = scores[1].get("o")

    return {

        "id": match.get("id"),

        "name": clean_text(
            match.get(
                "name",
                f"{team1} vs {team2}"
            )
        ),

        "team1": team1,
        "team2": team2,

        "score1": score1,
        "score2": score2,

        "overs1": overs1,
        "overs2": overs2,

        "wickets1": wickets1,
        "wickets2": wickets2,

        "matchType": clean_text(
            match.get(
                "matchType",
                "International"
            )
        ),

        "status": clean_text(
            match.get(
                "status",
                ""
            )
        ),

        "venue": clean_text(
            match.get(
                "venue",
                ""
            )
        ),

        "date": (
            match.get("_date")
            or match_date(match)
        ),

        "dateTimeGMT": match.get(
            "dateTimeGMT",
            ""
        ),

        "matchStarted": bool(
            match.get(
                "matchStarted",
                False
            )
        ),

        "matchEnded": bool(
            match.get(
                "matchEnded",
                False
            )
        ),

        "series": clean_text(
            match.get(
                "series",
                ""
            )
        ),
    }


def find_match(match_id):

    cached_matches = (
        MATCH_CACHE.get("data")
        or []
    )

    requested_id = str(match_id).strip()

    for match in cached_matches:

        stored_id = str(
            match.get("id", "")
        ).strip()

        if stored_id == requested_id:
            return normalize_match(match)

        # Historical match IDs may contain the UUID
        # at the end of a longer slug.
        if stored_id.endswith(requested_id):
            return normalize_match(match)

    for match in get_all_matches():

        stored_id = str(
            match.get("id", "")
        ).strip()

        if stored_id == requested_id:
            return normalize_match(match)

        if stored_id.endswith(requested_id):
            return normalize_match(match)

    return None

# =========================================================
# SQUADS / MATCH PLAYERS
# =========================================================

def extract_squad(data):

    raw = (
        data.get("data", data)
        if isinstance(data, dict)
        else data
    )

    if isinstance(raw, dict):
        possible = (
            raw.get("squad")
            or raw.get("teams")
            or raw.get("team")
            or []
        )
    elif isinstance(raw, list):
        possible = raw
    else:
        possible = []

    if isinstance(possible, dict):
        possible = [possible]

    if not isinstance(possible, list):
        return []

    teams = []

    for team in possible:
        if not isinstance(team, dict):
            continue

        team_name = clean_text(
            team.get("name")
            or team.get("team")
            or team.get("teamName")
            or "Team"
        )

        raw_players = (
            team.get("players")
            or team.get("player")
            or []
        )

        if isinstance(raw_players, dict):
            raw_players = [raw_players]

        players = []

        for player in raw_players if isinstance(raw_players, list) else []:
            if isinstance(player, str):
                name = clean_text(player)
                pid = None
            elif isinstance(player, dict):
                name = clean_text(
                    player.get("name")
                    or player.get("playerName")
                    or player.get("batsman")
                    or player.get("bowler")
                    or ""
                )
                pid = player.get("pid") or player.get("id")
            else:
                continue

            if name and name.lower() not in {p["name"].lower() for p in players}:
                players.append({
                    "name": name,
                    "id": pid
                })

        if players:
            teams.append({
                "name": team_name,
                "players": players
            })

    return teams


def extract_scorecard_players(data, match):
    """
    Fallback when match_squad is unavailable.

    Uses the batting/bowling players returned by the scorecard and
    keeps the actual match teams as the displayed team names.
    """
    raw = data.get("data", data) if isinstance(data, dict) else data

    if not isinstance(raw, dict):
        return []

    batting = raw.get("batting") or []
    bowling = raw.get("bowling") or []
    players_by_team = {}

    def canonical_team(name):
        name = clean_text(name)
        if not name:
            return ""
        name = re.sub(
            r"\s+(1st|2nd|3rd|4th)\s+innings$",
            "",
            name,
            flags=re.I
        )
        name = re.sub(r"\s+innings$", "", name, flags=re.I)
        return name.strip()

    def team_key(name):
        name = canonical_team(name).lower()
        name = re.sub(r"[^a-z0-9]+", "", name)
        aliases = {
            "wi": "westindies",
            "westindies": "westindies",
            "uae": "unitedarabemirates",
            "usa": "unitedstatesofamerica",
        }
        return aliases.get(name, name)

    def add_player(team_name, player_name, pid=None):
        team_name = canonical_team(team_name)
        player_name = clean_text(player_name)

        if not team_name or not player_name:
            return

        bucket = players_by_team.setdefault(team_name, {})
        bucket[player_name.lower()] = {
            "name": player_name,
            "id": pid
        }

    for innings in batting:
        if not isinstance(innings, dict):
            continue

        title = clean_text(
            innings.get("title")
            or innings.get("team")
            or innings.get("teamName")
            or innings.get("name")
            or ""
        )

        rows = (
            innings.get("scores")
            or innings.get("score")
            or []
        )

        for row in rows:
            if not isinstance(row, dict):
                continue

            add_player(
                title,
                row.get("batsman")
                or row.get("batsmanName")
                or row.get("name"),
                row.get("pid") or row.get("id")
            )

    for innings in bowling:
        if not isinstance(innings, dict):
            continue

        title = clean_text(
            innings.get("title")
            or innings.get("team")
            or innings.get("teamName")
            or innings.get("name")
            or ""
        )

        rows = (
            innings.get("scores")
            or innings.get("score")
            or []
        )

        for row in rows:
            if not isinstance(row, dict):
                continue

            add_player(
                title,
                row.get("bowler")
                or row.get("bowlerName")
                or row.get("name"),
                row.get("pid") or row.get("id")
            )

    result = []

    # Always present the two actual match teams first.
    for team_name in [match.get("team1"), match.get("team2")]:
        wanted = team_key(team_name)

        matching_key = None
        for existing_team in players_by_team:
            if team_key(existing_team) == wanted:
                matching_key = existing_team
                break

        if matching_key:
            result.append({
                "name": team_name,
                "players": list(players_by_team[matching_key].values())
            })

    # If the scorecard uses unexpected team names, don't throw away
    # the player data.
    if not result:
        result = [
            {
                "name": team,
                "players": list(players.values())
            }
            for team, players in players_by_team.items()
        ]

    return result


@app.route("/api/match-players/<match_id>")
def match_players(match_id):

    print("PLAYER REQUEST:", match_id)

    # Important: find the match in the current/requested month.
    # This prevents the old September-only lookup from breaking
    # October player requests.
    match = find_match(match_id)

    if not match:
        return jsonify({
            "status": "failure",
            "message": "Match not found"
        }), 404

    cache_key = str(match_id)

    if cache_key in SQUAD_CACHE:
        cached = SQUAD_CACHE[cache_key]
        return jsonify({
            "status": "success",
            "teams": cached,
            "source": "cache"
        })

    # First choice: official match squad.
    result = cricket_request(
        "match_squad",
        {"id": match_id, "offset": 0},
        timeout=20
    )

    print("MATCH SQUAD STATUS:", result.get("status"))

    squads = extract_squad(result)

    if squads:
        SQUAD_CACHE[cache_key] = squads
        return jsonify({
            "status": "success",
            "teams": squads,
            "source": "match_squad"
        })

    # Second choice: scorecard players.
    scorecard = cricket_request(
        "match_scorecard",
        {"id": match_id, "offset": 0},
        timeout=20
    )

    print("SCORECARD STATUS:", scorecard.get("status"))

    squads = extract_scorecard_players(scorecard, match)

    if squads:
        SQUAD_CACHE[cache_key] = squads
        return jsonify({
            "status": "success",
            "teams": squads,
            "source": "match_scorecard"
        })

    return jsonify({
        "status": "failure",
        "message": (
            "Squad information is not available for this match. "
            "The Cricket Data API did not return match-squad or "
            "scorecard player data."
        )
    })


# =========================================================
# WIKIPEDIA PLAYER SEARCH
# =========================================================

def wikipedia_player(page_name):

    try:

        response = requests.get(
            "https://en.wikipedia.org/w/api.php",

            params={
                "action": "query",
                "format": "json",
                "formatversion": 2,

                "prop": (
                    "info|pageimages|extracts"
                ),

                "inprop": "url",

                "exintro": 1,
                "explaintext": 1,

                "piprop": "thumbnail",
                "pithumbsize": 500,

                "titles": page_name.replace(
                    "_",
                    " "
                )
            },

            headers={
                "User-Agent":
                    "SportsIQ/1.0 educational project"
            },

            timeout=10
        )

        print(
            "Wikipedia profile status:",
            response.status_code
        )

        if response.status_code != 200:
            return None

        data = response.json()

        pages = (
            data.get("query", {})
            .get("pages", [])
        )

        if not pages:
            return None

        page = pages[0]

        if page.get("missing"):
            return None

        return {

            "name": page.get(
                "title",
                page_name.replace(
                    "_",
                    " "
                )
            ),

            "description": clean_text(
                page.get(
                    "description",
                    "Cricketer"
                )
            ),

            "bio": clean_text(
                page.get(
                    "extract",
                    "Wikipedia information "
                    "is not available."
                )
            ),

            "photo": (
                page.get(
                    "thumbnail"
                ) or {}
            ).get("source"),

            "url": page.get(
                "fullurl"
            )
        }

    except Exception as exc:

        print(
            "Wikipedia error:",
            exc
        )

        return None


def search_wikipedia_player(query):

    query = clean_text(
        query
    ).strip()

    query = re.sub(
        r"(?i)^(who is|tell me about|about|profile of|information about)\s+",
        "",
        query
    )

    query = re.sub(
        r"(?i)\s+(profile|information|stats|statistics)$",
        "",
        query
    ).strip()

    if not query:
        return None

    cache_key = query.lower()

    if cache_key in PLAYER_CACHE:
        return PLAYER_CACHE[cache_key]

    try:

        response = requests.get(
            "https://en.wikipedia.org/w/api.php",

            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "utf8": 1,
                "srlimit": 10
            },

            headers={
                "User-Agent":
                    "SportsIQ/1.0 educational project"
            },

            timeout=10
        )

        print(
            "Wikipedia search status:",
            response.status_code
        )

        if response.status_code != 200:
            return None

        data = response.json()

        results = (
            data.get("query", {})
            .get("search", [])
        )

        print(
            "Wikipedia results:",
            len(results)
        )

        if not results:
            return None

        query_words = set(
            query.lower().split()
        )

        best = None

        # Exact title
        for result in results:

            title = result.get(
                "title",
                ""
            ).strip()

            if title.lower() == query.lower():

                best = title
                break

        # All query words in title
        if best is None:

            for result in results:

                title = result.get(
                    "title",
                    ""
                ).strip()

                title_words = set(
                    title.lower().split()
                )

                if query_words.issubset(
                    title_words
                ):

                    best = title
                    break

        # First Wikipedia result
        if best is None:

            best = results[0].get(
                "title"
            )

        if not best:
            return None

        print(
            "Wikipedia selected:",
            best
        )

        profile = wikipedia_player(
            best.replace(
                " ",
                "_"
            )
        )

        if profile:

            PLAYER_CACHE[
                cache_key
            ] = profile

        return profile

    except Exception as exc:

        print(
            "Wikipedia search error:",
            exc
        )

        return None


@app.route("/api/player")
def player():

    query = request.args.get(
        "q",
        ""
    ).strip()

    if not query:

        return jsonify({
            "status": "failure",
            "message": "Enter a player name"
        }), 400

    profile = search_wikipedia_player(
        query
    )

    if profile:

        return jsonify({
            "status": "success",
            "player": profile
        })

    return jsonify({
        "status": "failure",
        "message": (
            f"I couldn't find a player "
            f"profile for '{query}'."
        )
    })


# =========================================================
# OLLAMA + AI
# =========================================================

def ask_ollama(prompt):

    try:

        response = requests.post(
            OLLAMA_URL,

            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },

            timeout=120
        )

        if response.status_code != 200:

            return (
                "Ollama returned an error. "
                "Please make sure Ollama is running."
            )

        return clean_text(
            response.json().get(
                "response",
                ""
            )
        )

    except requests.exceptions.Timeout:

        return (
            "Ollama is taking too long "
            "to respond. Please wait and try again."
        )

    except Exception as exc:

        return (
            "Ollama connection error: "
            + str(exc)
        )


def match_context(match):

    score1 = (
        "not available"
        if match.get("score1") is None
        else (
            f"{match.get('score1')}/"
            f"{match.get('wickets1', 0)} "
            f"({match.get('overs1')} overs)"
        )
    )

    score2 = (
        "not available"
        if match.get("score2") is None
        else (
            f"{match.get('score2')}/"
            f"{match.get('wickets2', 0)} "
            f"({match.get('overs2')} overs)"
        )
    )

    return f"""
Match: {match['name']}
Type: {match['matchType']}
Date: {match['date']}
Team 1: {match['team1']}
Score: {score1}
Team 2: {match['team2']}
Score: {score2}
Status: {match['status']}
Venue: {match['venue']}
"""


@app.route("/api/analyze/<match_id>")
def analyze(match_id):

    match = find_match(
        match_id
    )

    if not match:

        return jsonify({
            "status": "failure",
            "message": "Match not found"
        }), 404

    answer = ask_ollama(f"""

You are Sports IQ, an AI cricket analyst.

Analyze this completed/live/upcoming international cricket match:

{match_context(match)}

Give a concise factual analysis.

If the match is completed, discuss the recorded result
and available information.

If it is live, discuss only the supplied current score/status.

If it is upcoming, state that no match action has occurred yet
and do not invent a turning point, score, player performance,
or event.

""")

    return jsonify({
        "status": "success",
        "analysis": answer
    })


@app.route("/api/commentary/<match_id>")
def commentary(match_id):

    match = find_match(
        match_id
    )

    if not match:

        return jsonify({
            "status": "failure",
            "message": "Match not found"
        }), 404

    answer = ask_ollama(f"""

You are Sports IQ, an AI cricket commentator.

Match:

{match_context(match)}

Write 3-5 engaging but factual sentences.

Only use information supplied above.

Do not invent players, scores, events,
or live action.

If the match is upcoming, say that it is upcoming
and discuss only the known fixture details.

Do not describe imaginary batting, bowling,
wickets, or boundaries.

""")

    return jsonify({
        "status": "success",
        "commentary": answer
    })


# =========================================================
# AI ASK
# =========================================================

@app.route("/api/ask")
def ask():

    question = request.args.get(
        "question",
        ""
    ).strip()

    match_id = request.args.get(
        "match_id",
        ""
    ).strip()

    if not question:

        return jsonify({
            "status": "failure",
            "message": "Please enter a question."
        }), 400

    lower = question.lower()
    words = question.split()

    # =====================================================
    # PLAYER SEARCH
    # =====================================================

    match_terms = [
        "turning point",
        "run rate",
        "score",
        "scorecard",
        "wicket",
        "overs",
        "match",
        "commentary",
        "analysis",
        "target",
        "current score",
        "required rate"
    ]

    player_intent = any(
        x in lower
        for x in [
            "who is",
            "tell me about",
            "player profile",
            "player information",
            "cricketer"
        ]
    )

    short_name = (
        1 <= len(words) <= 4
        and not any(
            term in lower
            for term in match_terms
        )
    )

    if player_intent or short_name:

        print(
            "PLAYER SEARCH:",
            question
        )

        profile = search_wikipedia_player(
            question
        )

        if profile:

            print(
                "PLAYER PROFILE FOUND:",
                profile.get("name")
            )

            return jsonify({

                "status": "success",

                "type": "player",

                "player": profile

            })

        return jsonify({

            "status": "success",

            "type": "answer",

            "answer": (
                f"I couldn't find a Wikipedia "
                f"profile for '{question}'. "
                f"Try the player's full name."
            )

        })

    # =====================================================
    # NORMAL SPORTS IQ QUESTION
    # =====================================================

    # IMPORTANT:
    # This line MUST be aligned with the if block above.
    match = (
        find_match(match_id)
        if match_id
        else None
    )

    selected_context = ""

    if match:

        selected_context = (
            "Selected match:\n"
            + match_context(match)
        )

    prompt = f"""

You are Sports IQ, an AI cricket assistant.

{selected_context}

User question: {question}

Answer clearly and concisely.

Use only the available information.

Do not invent cricket statistics,
players, events, scores, venues,
captains, or results.

If information is not available,
say that it is not available.

"""

    return jsonify({

        "status": "success",

        "type": "answer",

        "answer": ask_ollama(prompt)

    })


# =========================================================
# MATCHES API
# SEPTEMBER 2026 ONLY
# =========================================================

@app.route("/api/matches")
def matches():

    # Use the month requested by the frontend
    month = request.args.get("month", current_month())

    # Make sure the month is in YYYY-MM format
    if not re.fullmatch(r"\d{4}-\d{2}", month):
        month = current_month()

    data = get_month_matches(month)

    normalized = [
        normalize_match(match)
        for match in data
    ]

    return jsonify({
        "status": "success",
        "month": month,
        "matches": normalized,
        "filter": f"{month} international matches only"
    })


@app.route("/api/match/<match_id>")
def match_details(match_id):

    match = find_match(
        match_id
    )

    if not match:

        return jsonify({
            "status": "failure",
            "message": "Match not found"
        }), 404

    return jsonify({
        "status": "success",
        "match": match
    })


# =========================================================
# FRONTEND
# =========================================================

@app.route("/")
def home():

    return send_from_directory(
        ".",
        "index.html"
    )


@app.route("/<path:path>")
def static_files(path):

    return send_from_directory(
        ".",
        path
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    print(
        "\n=============================================="
    )

    print(
        "        SPORTS IQ AI CRICKET APP"
    )

    print(
        "=============================================="
    )

    print(
        "Monthly international archive enabled"
    )

    print(
        "Wikipedia player search enabled"
    )

    print(
        "Ollama model:",
        OLLAMA_MODEL
    )

    print(
        "==============================================\n"
    )

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
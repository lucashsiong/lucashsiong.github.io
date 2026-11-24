import json
import pandas as pd
from pybaseball import statcast, playerid_reverse_lookup, cache

cache.enable()
START, END = "2025-01-01", "2025-12-31"   # wide range; spring training and postseason are filtered out below

df = statcast(START, END)
df = df[df["game_type"] == "R"].copy()

# The batter's team: away team in the top of an inning, home team in the bottom
df["team"] = df["away_team"].where(df["inning_topbot"] == "Top", df["home_team"])

# Plate appearances (approximate): pitches that end a PA, minus baserunning events
ends = df["events"].notna() & ~df["events"].astype(str).str.contains("caught_stealing|pickoff|stolen_base")
pa = df[ends].groupby("batter").size()

# Balls in play with a measured exit velocity and launch angle
bip = df[(df["type"] == "X") & df["launch_speed"].notna() & df["launch_angle"].notna()].copy()

RES = ["Single", "Double", "Triple", "Home run", "Out", "Other"]
OUTS = {"field_out", "force_out", "grounded_into_double_play", "double_play",
        "fielders_choice_out", "triple_play", "sac_fly_double_play", "sac_bunt_double_play"}
def group(e):
    return {"single": 0, "double": 1, "triple": 2, "home_run": 3}.get(e, 4 if e in OUTS else 5)
bip["res"] = bip["events"].map(group)

# Player names (pybaseball returns lowercase last/first names)
ids = bip["batter"].unique().tolist()
nm = playerid_reverse_lookup(ids, key_type="mlbam")
nm["name"] = nm["name_first"].str.title() + " " + nm["name_last"].str.title()
name_of = dict(zip(nm["key_mlbam"], nm["name"]))

players = sorted(ids, key=lambda i: name_of.get(i, str(i)))
p_index = {pid: k for k, pid in enumerate(players)}
teams = sorted(bip["team"].dropna().unique().tolist())
t_index = {t: k for k, t in enumerate(teams)}
bip = bip[bip["team"].isin(t_index)]

out = {
    "season": 2025,
    "results": RES,
    "teams": teams,
    "players": [[name_of.get(pid, str(pid)), int(pa.get(pid, 0))] for pid in players],
    "ev": bip["launch_speed"].round(1).tolist(),
    "la": bip["launch_angle"].round().astype(int).tolist(),
    "res": bip["res"].astype(int).tolist(),
    "p": bip["batter"].map(p_index).astype(int).tolist(),
    "t": bip["team"].map(t_index).astype(int).tolist(),
}
with open("data.json", "w") as f:
    json.dump(out, f, separators=(",", ":"))
print(f"Saved data.json with {len(out['ev']):,} batted balls and {len(players)} players")

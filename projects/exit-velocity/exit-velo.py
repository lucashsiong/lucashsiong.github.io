import pandas as pd
import plotly.express as px
from pybaseball import playerid_lookup, statcast_batter, cache

cache.enable()  # saves downloads locally so you don't re-pull data

# 1. Find the player's ID (change the names to a hitter you like)
lookup = playerid_lookup("judge", "aaron")
player_id = int(lookup["key_mlbam"].iloc[0])

# 2. Pull every pitch the player saw in 2025 (regular season and postseason)
df = statcast_batter("2025-03-01", "2025-11-30", player_id)

# 3. Keep only balls put in play that have a measured exit velocity
bip = df[(df["type"] == "X") & df["launch_speed"].notna()].copy()
bip["Result"] = bip["events"].str.replace("_", " ").str.title()

# 4. Chart it
fig = px.scatter(
    bip,
    x="launch_angle",
    y="launch_speed",
    color="Result",
    hover_data=["game_date", "description"],
    labels={"launch_angle": "Launch angle (degrees)", "launch_speed": "Exit velocity (mph)"},
    title="Exit velocity vs. launch angle, 2025",
)
fig.add_hline(y=95, line_dash="dot", annotation_text="Hard-hit (95+ mph)")
fig.write_html("chart.html", include_plotlyjs="cdn")
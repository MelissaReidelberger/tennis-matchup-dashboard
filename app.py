
import streamlit as st
import pandas as pd
import base64
from pathlib import Path
from html import escape

st.set_page_config(
    page_title="Tennis Matchup Dashboard",
    page_icon="🎾",
    layout="wide"
)

st.markdown("""
<style>
    .stApp {
        background-color: #F5F7FB;
        color: #172B4D;
    }

    .block-container {
        max-width: 1320px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3 {
        color: #142D50;
        font-family: Arial, sans-serif;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid #E1E7EF;
        border-radius: 10px;
        overflow: hidden;
    }

    /* OVERALL SURFACE HEADING */
    .overall-heading {
        background: linear-gradient(135deg, #102747, #234D78);
        color: #FFFFFF;
        padding: 22px 28px;
        border-radius: 12px;
        margin-top: 24px;
        margin-bottom: 18px;
    }

    .overall-heading h2 {
        color: #FFFFFF !important;
        font-size: 26px;
        font-weight: 700;
        margin: 0;
    }

    .overall-heading p {
        color: #D8E6F5;
        font-size: 14px;
        margin: 6px 0 0 0;
    }

    .compact-table-container {
        width: 100%;
    }

    .compact-table {
        width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
        font-size: 12px;
    }

    .compact-table th,
    .compact-table td {
        padding: 9px 5px;
        border-bottom: 1px solid #E1E7EF;
        overflow-wrap: anywhere;
        text-align: center;
    }

    .compact-table th {
        color: #53657C;
        font-weight: 600;
        background: #F0F4F9;
    }

    .compact-table th:first-child,
    .compact-table td:first-child {
        width: 31%;
        text-align: left;
    }

    .compact-table td {
        color: #172B4D;
    }   

    .court-image-panel {
        background: transparent;
        width: 100%;
        box-sizing: border-box;
    }
</style>
""", unsafe_allow_html=True)

st.title("Tennis Matchup Analysis")

st.write(
    "Compare historical serving and returning performance, "
    "tour benchmarks, and recent match form across all court surfaces."
)

DATA_DIR = Path("data")
SURFACES = ["Overall", "Hard", "Clay", "Grass"]
TOURS = ["WTA", "ATP", "CHALLENGER"]

# Load existing benchmarks
@st.cache_data
def load_benchmarks():
    return pd.read_csv(DATA_DIR / "benchmarks_2026.csv")


# Build searchable player directory
@st.cache_data
def load_players():
    records = []

    for tour in TOURS:
        file_path = (
            DATA_DIR / f"{tour.lower()}_2026_serving_overall.csv"
        )

        if not file_path.exists():
            continue

        df = pd.read_csv(file_path)

        for player in df["Player"].dropna().unique():
            records.append({
                "Player": str(player).strip(),
                "Tour": tour
            })

    players = pd.DataFrame(records).drop_duplicates()

    # Preserve tour identity when a player appears in
    # both ATP and Challenger datasets.
    players["Label"] = (
        players["Player"] + " (" + players["Tour"] + ")"
    )

    return players.sort_values("Label").reset_index(drop=True)


benchmarks = load_benchmarks()
players = load_players()

UNLISTED_WOMEN = "Women's Player — Not Listed"
UNLISTED_MEN = "Men's Player — Not Listed"

player_options = [
    UNLISTED_WOMEN,
    UNLISTED_MEN,
] + players["Label"].tolist()


@st.cache_data
def load_player_stats(tour, surface):
    serving_path = (
        DATA_DIR / f"{tour.lower()}_2026_serving_{surface.lower()}.csv"
    )
    returning_path = (
        DATA_DIR / f"{tour.lower()}_2026_returning_{surface.lower()}.csv"
    )

    serving = pd.read_csv(serving_path)
    returning = pd.read_csv(returning_path)

    return serving, returning

def identify_player(selection):
    if selection == UNLISTED_WOMEN:
        return "WTA"

    if selection == UNLISTED_MEN:
        return "ATP"

    match = players.loc[players["Label"] == selection]

    if match.empty:
        return None

    return match.iloc[0]["Tour"]


# Player selection
col1, col2 = st.columns(2)

with col1:
    player_a = st.selectbox(
        "Player A",
        options=player_options,
        index=None,
        placeholder="Start typing a player's name...",
        key="player_a"
    )

    tour_a = identify_player(player_a) if player_a else None

    if tour_a:
        st.caption(f"Tour: {tour_a}")

with col2:
    player_b = st.selectbox(
        "Player B",
        options=player_options,
        index=None,
        placeholder="Start typing a player's name...",
        key="player_b"
    )

    tour_b = identify_player(player_b) if player_b else None

    if tour_b:
        st.caption(f"Tour: {tour_b}")


# Display benchmarks for each selected player
def show_benchmarks(tour, surface, heading):
    selected = benchmarks.loc[
        (benchmarks["Tour"] == tour) &
        (benchmarks["Surface"] == surface)
    ]

    if selected.empty:
        st.warning("No benchmark data available.")
        return

    benchmark = selected.iloc[0]

    st.subheader(heading)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Average Ace%", f"{benchmark['Ace%']:.2f}%")
        st.metric("Average DF%", f"{benchmark['DF%']:.2f}%")

    with col2:
        st.metric(
            "Average Ace Against%",
            f"{benchmark['Ace Against%']:.2f}%"
        )
        st.metric(
            "Average DF Against%",
            f"{benchmark['DF Against%']:.2f}%"
        )

    with col3:
        st.metric(
            "Aces per Match",
            f"{benchmark['Aces per Match']:.2f}"
        )
        st.metric(
            "DFs per Match",
            f"{benchmark['DFs per Match']:.2f}"
        )

    st.caption(
        f"Serving players: {int(benchmark['Serving Players'])} | "
        f"Returning players: {int(benchmark['Returning Players'])}"
    )

def show_player_stats(selection, tour, surface):
    st.subheader(f"{selection} — 2026 {surface} Statistics")

    if selection in [UNLISTED_WOMEN, UNLISTED_MEN]:
        st.info(
            "No historical statistics available for this player. "
            "Recent-form statistics can be entered manually."
        )
        return

    serving, returning = load_player_stats(tour, surface)

    player_name = players.loc[
        players["Label"] == selection, "Player"
    ].iloc[0]

    serving_row = serving.loc[
        serving["Player"] == player_name
    ]

    returning_row = returning.loc[
        returning["Player"] == player_name
    ]

    if serving_row.empty and returning_row.empty:
        st.info(
            "No historical statistics available for this "
            "player on the selected surface."
        )
        return

    def display_value(df, column, percent=False):
        if df.empty or column not in df.columns:
            return "N/A"

        value = df.iloc[0][column]

        if pd.isna(value):
            return "N/A"

        return f"{value:.2f}%" if percent else f"{value:.2f}"

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Ace%",
            display_value(serving_row, "Ace%", percent=True)
        )
        st.metric(
            "DF%",
            display_value(serving_row, "DF%", percent=True)
        )

    with col2:
        st.metric(
            "Ace Against%",
            display_value(returning_row, "vAce%", percent=True)
        )
        st.metric(
            "DF Against%",
            display_value(returning_row, "vDF%", percent=True)
        )

    with col3:
        st.metric(
            "Aces per Match",
            display_value(serving_row, "Aces per Match")
        )
        st.metric(
            "DFs per Match",
            display_value(serving_row, "DFs per Match")
        )

def get_player_values(selection, tour, surface):
    """Retrieve six historical statistics for a selected player."""

    columns = [
        "Ace%",
        "Aces per Match",
        "Ace Against%",
        "DF%",
        "DFs per Match",
        "DF Against%",
        "First Serve In%",
    ]

    values = {column: None for column in columns}

    if not selection or selection in [UNLISTED_WOMEN, UNLISTED_MEN]:
        return values

    serving, returning = load_player_stats(tour, surface)

    player_name = players.loc[
        players["Label"] == selection, "Player"
    ].iloc[0]

    serving_row = serving.loc[serving["Player"] == player_name]
    returning_row = returning.loc[returning["Player"] == player_name]

    if not serving_row.empty:
        row = serving_row.iloc[0]

        for column in [
            "Ace%", "Aces per Match",
            "DF%", "DFs per Match"
        ]:
            
            if "1stIn" in row.index and pd.notna(row["1stIn"]):
                values["First Serve In%"] = row["1stIn"]

            if column in row.index and pd.notna(row[column]):
                values[column] = row[column]

    if not returning_row.empty:
        row = returning_row.iloc[0]

        if pd.notna(row.get("vAce%")):
            values["Ace Against%"] = row["vAce%"]

        if pd.notna(row.get("vDF%")):
            values["DF Against%"] = row["vDF%"]

    return values

def get_first_serve_benchmark(tour, surface):
    serving, _ = load_player_stats(tour, surface)

    values = pd.to_numeric(
        serving["1stIn"].astype(str)
        .str.replace("%", "", regex=False)
        .str.strip(),
        errors="coerce",
    )

    return values.mean() if values.notna().any() else None

def format_stat(value, metric):
    if value is None or pd.isna(value):
        return "—"

    if "%" in metric:
        return f"{value:.2f}%"

    return f"{value:.2f}"

def calculate_recent_form(df, surface="Overall"):
    metrics = {
        "Ace%": "A%",
        "DF%": "DF%",
        "First Serve In%": "1stIn",
        "Ace Against%": "vAce%",
    }

    data = df.copy()

    # Keep the pasted match order: most recent first.
    # For individual surfaces, use only matching matches.
    if surface != "Overall":
        data = data[
            data["Surface"].astype(str).str.strip().str.lower()
            == surface.lower()
        ]

    results = {}

    for metric, column in metrics.items():
        values = pd.to_numeric(
            data[column].astype(str)
            .str.replace("%", "", regex=False)
            .str.strip(),
            errors="coerce",
        )

        for count in [5, 10]:
            recent_values = values.head(count).dropna()

            results[f"Last {count} {metric}"] = (
                recent_values.mean()
                if not recent_values.empty
                else None
            )
            results[f"Last {count} {metric} n"] = len(recent_values)

    return results

def show_recent_form_comparison(surface):
    st.markdown("**Recent Form**")

    data_a = st.session_state.get("recent_calculated_a")
    data_b = st.session_state.get("recent_calculated_b")

    if data_a is None or data_b is None:
        st.caption("Enter recent match data for both players.")
        return

    results_a = calculate_recent_form(data_a, surface)
    results_b = calculate_recent_form(data_b, surface)

    metrics = [
        "Ace%",
        "Ace Against%",
        "DF%",
    ]

    rows = []

    for metric in metrics:
        for count in [5, 10]:
            key = f"Last {count} {metric}"

            value_a = results_a.get(key)
            value_b = results_b.get(key)
            
            n_a = results_a.get(f"{key} n", 0)
            n_b = results_b.get(f"{key} n", 0)

            display_a = (
                f"{format_stat(value_a, metric)} (n={n_a})"
                if n_a > 0 else "—"
            )

            display_b = (
                f"{format_stat(value_b, metric)} (n={n_b})"
                if n_b > 0 else "—"
            )
            rows.append({
                "Metric": key,
                 player_a: display_a,
                 player_b: display_b,
            })

    comparison = pd.DataFrame(rows)

    show_compact_table(comparison)

def show_first_serve_comparison(surface):
    st.markdown("**First Serve In%**")

    values_a = get_player_values(player_a, tour_a, surface)
    values_b = get_player_values(player_b, tour_b, surface)


    benchmark_a = get_first_serve_benchmark(tour_a, surface)
    benchmark_b = get_first_serve_benchmark(tour_b, surface)

    data_a = st.session_state.get("recent_calculated_a")
    data_b = st.session_state.get("recent_calculated_b")

    recent_a = (
        calculate_recent_form(data_a, surface)
        if data_a is not None else {}
    )

    recent_b = (
        calculate_recent_form(data_b, surface)
        if data_b is not None else {}
    )

    rows = []

    season_row = {
        "Metric": "2026 Average",
        player_a: format_stat(values_a["First Serve In%"], "First Serve In%"),
        "Tour Average": format_stat(benchmark_a, "First Serve In%"),
        player_b: format_stat(values_b["First Serve In%"], "First Serve In%"),
    }

    if tour_a != tour_b:
        season_row["Tour Average B"] = format_stat(
            benchmark_b, "First Serve In%"
        )

    rows.append(season_row)

    for count in [5, 10]:
        key = f"Last {count} First Serve In%"

        n_a = recent_a.get(f"{key} n", 0)
        n_b = recent_b.get(f"{key} n", 0)

        value_a = recent_a.get(key)
        value_b = recent_b.get(key)

        rows.append({
            "Metric": f"Last {count}",
            player_a: (
                f"{format_stat(value_a, 'First Serve In%')} (n={n_a})"
                if n_a > 0 else "—"
            ),
            player_b: (
                f"{format_stat(value_b, 'First Serve In%')} (n={n_b})"
                if n_b > 0 else "—"
            ),
        })

    comparison = pd.DataFrame(rows)
    comparison = comparison.fillna("-")

    if tour_a != tour_b:
        comparison = comparison[
            ["Metric", player_a, "Tour Average", player_b, "Tour Average B"]
        ]
    else:
        comparison = comparison[
            ["Metric", player_a, "Tour Average", player_b]
        ]
    show_compact_table(comparison)

if "recent_player_data" not in st.session_state:
    st.session_state["recent_player_data"] = {}

def show_recent_form_inputs():
    columns = [
        "Date", "Tournament", "Surface", "Rd",
        "Rk", "vRk", "Match", "Score", "DR",
        "A%", "DF%", "1stIn", "vAce%", "2nd%",
        "BPSvd", "Time"
    ]

    for label, player, tour in [
        ("a", player_a, tour_a),
        ("b", player_b, tour_b),
    ]:
        st.markdown(f"### {player} Recent Match Data")

        storage_key = f"{tour}_{player}"
        saved_data = st.session_state["recent_player_data"]

        if storage_key not in saved_data:
            saved_data[storage_key] = (
                pd.DataFrame(columns=columns, index=range(10))
                .fillna("")
            )

        with st.form(key=f"recent_form_{label}_{storage_key}"):
            edited_data = st.data_editor(
                saved_data[storage_key],
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True,
                key=f"recent_editor_{label}_{storage_key}",
            )

            save_clicked = st.form_submit_button(
                "Save & Update Statistics",
                use_container_width=True,
            )

            if save_clicked:
                saved_data[storage_key] = edited_data.copy()
                st.success(f"Match data saved for {player}")

        st.session_state[f"recent_calculated_{label}"] = (
            saved_data[storage_key]
        )

def show_compact_table(df):
    headers = "".join(
        f"<th>{escape(str(column))}</th>"
        for column in df.columns
    )

    body = ""

    for _, row in df.iterrows():
        cells = "".join(
            f"<td>{escape(str(value))}</td>"
            for value in row
        )
        body += f"<tr>{cells}</tr>"

    html = f"""
    <div class="compact-table-container">
        <table class="compact-table">
            <thead>
                <tr>{headers}</tr>
            </thead>
            <tbody>
                {body}
            </tbody>
        </table>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)

def get_court_background(surface):
    image_files = {
        "Overall": "overall_stadium.png",
        "Hard": "hard_court.png",
        "Clay": "clay_court.png",
        "Grass": "grass_court.png",
    }

    image_path = (
        Path(__file__).resolve().parent
        / "assets"
        / image_files[surface]
    )

    image_data = base64.b64encode(
        image_path.read_bytes()
    ).decode("utf-8")

    return f"data:image/png;base64,{image_data}"

def show_surface_comparison(surface):
    if surface == "Overall":
        st.markdown(
            """
            <div class="overall-heading">
                <h2>Overall Performance</h2>
                <p>2026 Season | All Court Surfaces</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.subheader(f"{surface} Court")

    metrics = [
        "Ace%",
        "Aces per Match",
        "Ace Against%",
        "DF%",
        "DFs per Match",
        "DF Against%",
    ]
    values_a = get_player_values(player_a, tour_a, surface)
    values_b = get_player_values(player_b, tour_b, surface)

    benchmark_a = benchmarks.loc[
        (benchmarks["Tour"] == tour_a) &
        (benchmarks["Surface"] == surface)
    ]

    benchmark_b = benchmarks.loc[
        (benchmarks["Tour"] == tour_b) &
        (benchmarks["Surface"] == surface)
    ]

    def build_player_count_table():
        selected_tours = list(dict.fromkeys([tour_a, tour_b]))

        html_rows = ""

        for selected_tour in selected_tours:
            html_rows += (
                f'<tr><td colspan="3" '
                f'style="padding-top: 9px; font-weight: 700;">'
                f'{selected_tour}</td></tr>'
            )

            for court_surface in SURFACES:
                selected = benchmarks.loc[
                    (benchmarks["Tour"] == selected_tour) &
                    (benchmarks["Surface"] == court_surface)
                ]

                if selected.empty:
                    serving = "—"
                    returning = "—"
                else:
                    record = selected.iloc[0]
                    serving = (
                        f'{int(record["Serving Players"]):,}'
                        if pd.notna(record["Serving Players"])
                        else "—"
                    )
                    returning = (
                        f'{int(record["Returning Players"]):,}'
                        if pd.notna(record["Returning Players"])
                        else "—"
                    )

                html_rows += (
                    f"<tr><td>{court_surface}</td>"
                    f'<td style="text-align: right;">{serving}</td>'
                    f'<td style="text-align: right;">{returning}</td></tr>'
                )

        return (
            '<table style="width:100%; color:white; '
            'font-size:11px; border-collapse:collapse; '
            'white-space:nowrap;">'
            '<thead><tr>'
            '<th style="text-align:left; padding:5px 2px;">Surface</th>'
            '<th style="text-align:right; padding:5px 2px;">Serve</th>'
            '<th style="text-align:right; padding:5px 2px;">Return</th>'
            '</tr></thead>'
            f'<tbody>{html_rows}</tbody>'
            '</table>'
        )

    player_count_text = build_player_count_table()

    rows = []

    for metric in metrics:
        avg_a = (
            benchmark_a.iloc[0][metric]
            if not benchmark_a.empty else None
        )

        avg_b = (
            benchmark_b.iloc[0][metric]
            if not benchmark_b.empty else None
        )

        rows.append({
            "Metric": metric,
            player_a: format_stat(values_a[metric], metric),
            "Benchmark A": format_stat(avg_a, metric),
            player_b: format_stat(values_b[metric], metric),
            "Benchmark B": format_stat(avg_b, metric),
        })
    comparison = pd.DataFrame(rows)

    if tour_a == tour_b:
        comparison = comparison.drop(columns=["Benchmark B"])
        comparison = comparison.rename(
            columns={"Benchmark A": "Tour Average"}
        )
    else: 
        comparison = comparison.rename(
            columns={
                "Benchmark A": f"{'CH' if tour_a == 'CHALLENGER' else tour_a} Avg", 
                "Benchmark B": f"{'CH' if tour_b == 'CHALLENGER' else tour_b} Avg",
            }
        )
    
    if surface != "Overall":
        background = get_court_background(surface)

        st.markdown(
            f"""
            <style>
            div[data-testid="stColumn"]:has(.surface-card-{surface.lower()}) {{
                background-image:
                    linear-gradient(
                        rgba(5, 25, 50, 0.65),
                        rgba(5, 25, 50, 0.55)
                    ),
                    url('{background}');
                background-size: cover;
                background-position: center;
                border-radius: 12px;
                padding: 12px;
            }}

            div[data-testid="stColumn"]:has(.surface-card-{surface.lower()}) h3,
            div[data-testid="stColumn"]:has(.surface-card-{surface.lower()}) p,
            div[data-testid="stColumn"]:has(.surface-card-{surface.lower()}) strong,
            div[data-testid="stColumn"]:has(.surface-card-{surface.lower()}) table th,
            div[data-testid="stColumn"]:has(.surface-card-{surface.lower()}) table td {{
                color: white !important;
            }}

            div[data-testid="stColumn"]:has(.surface-card-{surface.lower()}) table th {{
                background-color: transparent !important;
                text-align: center !important;
            }}

            div[data-testid="stColumn"]:has(.surface-card-{surface.lower()}) h3 {{
                margin-bottom: 0 !important;
                padding-bottom: 0 !important;
            }}

            div[data-testid="stColumn"]:has(.surface-card-{surface.lower()}) .stMarkdown {{
                 margin-bottom: 0 !important;
            }}
            </style>

            <div class="surface-card-{surface.lower()}"></div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("**Ace & Double Fault Statistics**")
        show_compact_table(comparison)
        return

    court_col, col1, col2, col3 = st.columns(
        [0.75, 1.45, 1.20, 1.20],
        gap="small",
        border=True,
    )


    if surface in ["Overall", "Hard", "Clay", "Grass"]:
        with court_col:
            background = get_court_background(surface)

            court_titles = {
                "Overall": "Overall",
                "Hard": "Hard Court",
                "Clay": "Clay Court",
                "Grass": "Grass Court",
            }

            st.markdown(
                f"""
                <style>
                div[data-testid="stColumn"]:has(.court-image-panel-{surface.lower()}) {{
                    background-image:
                        linear-gradient(
                            90deg,
                            rgba(5, 25, 50, 0.85),
                            rgba(5, 25, 50, 0.35)
                        ),
                        url('{background}');
                    background-size: cover;
                    background-position: center;
                    border-radius: 12px;
                    overflow: hidden;
                }}
                </style>

                <div class="court-image-panel court-image-panel-{surface.lower()}"
                     style="padding: 22px 0.5px; color: white;">
                    <h2 style="color: white; margin: 0;">
                        {court_titles[surface]}
                    </h2>
                    <p style="color: white; margin-top: 8px;">
                        2026 Season
                    </p>
                    <p style="color: white; font-size: 12px; line-height: 1.6; margin-top: 14px;">
                        {player_count_text}
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col1:
        st.markdown("**Ace & Double Fault Statistics**")
        show_compact_table(comparison)

    with col2:
        show_recent_form_comparison(surface)

    with col3:
        show_first_serve_comparison(surface)

# All-surfaces comparison
if player_a and player_b:
    st.divider()

    show_recent_form_inputs()

    st.divider()
    st.header(f"{player_a} vs {player_b}")

    
    # Overall Performance — full-width
    show_surface_comparison("Overall")

    # Surface Comparison — three side-by-side columns
    st.subheader("Surface Comparison")

    hard_col, clay_col, grass_col = st.columns(3, gap="small")

    with hard_col:
        show_surface_comparison("Hard")

    with clay_col:
        show_surface_comparison("Clay")

    with grass_col:
        show_surface_comparison("Grass")

elif player_a or player_b:
    st.info("Select both players to display the matchup comparison.")

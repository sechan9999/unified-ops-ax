"""UI Components & Visualizations for Unified Ops AX Streamlit Dashboard."""
import pandas as pd
import plotly.express as px
import pydeck as pdk


def get_status_color(status: str) -> list[int]:
    if status == "Active":
        return [0, 255, 163, 200]
    elif status == "Warning":
        return [255, 193, 7, 200]
    elif status == "Critical":
        return [255, 75, 75, 200]
    else:
        return [156, 163, 175, 180]


def render_pydeck_map(filtered_df: pd.DataFrame) -> pdk.Deck:
    map_df = filtered_df.copy()
    map_df["color"] = map_df["Status"].apply(get_status_color)

    view_state = pdk.ViewState(
        latitude=37.7749,
        longitude=-122.4194,
        zoom=11.5,
        pitch=45,
        bearing=15
    )

    layer_scatter = pdk.Layer(
        "ScatterplotLayer",
        map_df,
        get_position=["Longitude", "Latitude"],
        get_color="color",
        get_radius=180,
        pickable=True,
        auto_highlight=True
    )

    deck = pdk.Deck(
        layers=[layer_scatter],
        initial_view_state=view_state,
        map_style="mapbox://styles/mapbox/dark-v11",
        tooltip={
            "html": "<b>{Unit ID}</b> ({Type})<br/>"
                    "Status: <b>{Status}</b><br/>"
                    "Speed: {Speed (mph)} mph | Battery: {Battery (%)}%<br/>"
                    "Ping: {Last Telemetry Ping}",
            "style": {"backgroundColor": "#0F172A", "color": "#E2E8F0", "fontSize": "12px", "borderRadius": "6px"}
        }
    )
    return deck


def render_status_pie_chart(filtered_df: pd.DataFrame):
    fig = px.pie(
        filtered_df,
        names="Status",
        hole=0.6,
        color="Status",
        color_discrete_map={
            "Active": "#00FFA3",
            "Warning": "#FFC107",
            "Critical": "#FF4B4B",
            "Idle": "#6B7280"
        }
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        height=240,
        showlegend=True,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E5E7EB")
    )
    return fig


def render_energy_scatter_chart(filtered_df: pd.DataFrame):
    fig_scatter = px.scatter(
        filtered_df,
        x="Battery (%)",
        y="Speed (mph)",
        color="Status",
        hover_name="Unit ID",
        color_discrete_map={
            "Active": "#00FFA3",
            "Warning": "#FFC107",
            "Critical": "#FF4B4B",
            "Idle": "#6B7280"
        }
    )
    fig_scatter.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        height=280,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E5E7EB"),
        xaxis=dict(gridcolor="#1F293D"),
        yaxis=dict(gridcolor="#1F293D")
    )
    return fig_scatter

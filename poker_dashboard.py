import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="Poker Dashboard", layout="wide")

# --- LOAD DATA ---
@st.cache_data
def load_data():
    df = pd.read_csv('C:/Users/alexm/Downloads/PBT-Bankroll-Export-2025-04-30-05-54-11-UTC.csv', sep=',', skiprows=1)
    df['starttime'] = pd.to_datetime(df['starttime'])
    df['netprofit_cad'] = df['netprofit'] * df['exchangerate']
    df['session_hours'] = df['playingminutes'] / 60
    df['hourly_rate'] = df['netprofit_cad'] / df['session_hours']
    df['year'] = df['starttime'].dt.year
    df['month'] = df['starttime'].dt.month_name()
    df['month_num'] = df['starttime'].dt.month
    df['day_of_week'] = df['starttime'].dt.day_name()
    df['location'] = df['location'].replace({
        'woodbine': 'Woodbine Casino',
        'estoril': 'Estoril Casino',
        'niagara': 'Niagara Falls Casino'
    })
    return df

df = load_data()

# --- TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📋 Sessions", "📍 Locations", "📈 Charts"])

# --- TAB 1: OVERVIEW ---
with tab1:
    st.markdown("## 💰 Total Profit")
    total_profit = df['netprofit_cad'].sum()
    total_hours = df['session_hours'].sum()
    total_sessions = len(df)
    hourly_winrate = total_profit / total_hours if total_hours > 0 else 0
    total_buyin = df['buyin'].sum() + df['rebuycosts'].sum()
    roi = (total_profit / total_buyin) * 100 if total_buyin > 0 else 0
    won_pct = (df['netprofit_cad'] > 0).mean() * 100 if len(df) > 0 else 0
    best_weekday = df.groupby('day_of_week')['netprofit_cad'].mean().idxmax()

    st.markdown(f"<h1 style='font-size: 60px; color: green;'>€{total_profit:,.2f}</h1>", unsafe_allow_html=True)

    summary_col, top_col, worst_col = st.columns([2, 1.5, 1.5])

    with summary_col:
        st.markdown("### 📈 Summary")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Sessions:** {total_sessions}")
            st.markdown(f"**Total Hours:** {total_hours:.1f} h")
            st.markdown(f"**Hourly Winrate:** €{hourly_winrate:.2f}/h")
        with col2:
            st.markdown(f"**ROI:** {roi:.2f}%")
            st.markdown(f"**Won:** {won_pct:.2f}%")
            st.markdown(f"**Best Weekday:** {best_weekday}")

    with top_col:
        st.markdown("### 🏆 Top 3 Best Sessions")
        top_sessions = df.nlargest(3, 'netprofit_cad')[['starttime', 'location', 'netprofit_cad']]
        for _, row in top_sessions.iterrows():
            st.markdown(f"**{row['starttime'].strftime('%Y-%m-%d')}** – {row['location']} – <span style='color:green;'>€{row['netprofit_cad']:.2f}</span>", unsafe_allow_html=True)

    with worst_col:
        st.markdown("### 💥 Top 3 Worst Sessions")
        worst_sessions = df.nsmallest(3, 'netprofit_cad')[['starttime', 'location', 'netprofit_cad']]
        for _, row in worst_sessions.iterrows():
            st.markdown(f"**{row['starttime'].strftime('%Y-%m-%d')}** – {row['location']} – <span style='color:red;'>€{row['netprofit_cad']:.2f}</span>", unsafe_allow_html=True)

    st.markdown("### 📈 Profit")
    df_sorted = df.sort_values('starttime')
    df_sorted['cumulative_hours'] = df_sorted['session_hours'].cumsum()
    df_sorted['cumulative_profit'] = df_sorted['netprofit_cad'].cumsum()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_sorted['cumulative_hours'],
        y=df_sorted['cumulative_profit'],
        mode='lines+markers',
        name='Profit',
        line=dict(color='blue'),
        hovertemplate='<b>Hours:</b> %{x:.0f}<br><b>Profit:</b> €%{y:.0f}<extra></extra>'
    ))
    fig.update_layout(
        xaxis_title='Hours Played',
        yaxis_title='Profit (€)',
        hovermode='x',
        height=600
    )
    st.plotly_chart(fig, use_container_width=True)

# --- TAB 2: SESSIONS ---
with tab2:
    st.markdown("### 📋 All Sessions")
    location_filter = st.selectbox("Filter by Location", options=["All"] + sorted(df['location'].unique().tolist()))
    filtered_df = df.sort_values('starttime', ascending=False)
    if location_filter != "All":
        filtered_df = filtered_df[filtered_df['location'] == location_filter]

    for _, row in filtered_df.iterrows():
        profit_color = '🟢' if row['netprofit_cad'] >= 0 else '🔴'
        total_buyin = row['buyin'] + row['rebuycosts']
        is_euro = row['location'].lower() in ['estoril casino', 'amsterdam']
        currency = '€' if is_euro else 'CAD'
        profit_text = f"{profit_color} €{int(row['netprofit_cad'])}"
        label = f"{row['starttime'].strftime('%Y-%m-%d')} - {row['location']} - {profit_text}"
        with st.expander(label):
            st.markdown(f"**Hours Played:** {row['session_hours']:.2f} h")
            st.markdown(f"**Total Buy-In:** {currency}{total_buyin:.2f}")
            st.markdown(f"**Rebuys:** {currency}{row['rebuycosts']:.2f}")
            st.markdown(f"**Cashout:** {currency}{row['cashout']:.2f}")
            st.markdown(f"**Hourly Rate:** €{row['hourly_rate']:.2f}/h")

# --- TAB 3: LOCATIONS ---
with tab3:
    st.markdown("### 📍 Location Stats")
    location_stats = df.groupby('location').agg(
        total_profit=('netprofit_cad', 'sum'),
        sessions=('netprofit_cad', 'count'),
        total_hours=('session_hours', 'sum'),
        hourly_rate=('netprofit_cad', lambda x: x.sum() / df.loc[x.index, 'session_hours'].sum())
    )
    location_stats['win_percent'] = 100 * (df[df['netprofit_cad'] > 0].groupby('location')['netprofit_cad'].count() / location_stats['sessions'])
    location_stats = location_stats.sort_values('total_profit', ascending=False)

    location_stats = location_stats.rename(columns={
        'total_profit': 'Total Profit',
        'sessions': 'Sessions',
        'total_hours': 'Hours Played',
        'hourly_rate': 'Hourly Rate',
        'win_percent': 'Win %'
    })
    location_stats['Total Profit'] = location_stats['Total Profit'].apply(lambda x: f"€{int(x):,}")
    location_stats['Hourly Rate'] = location_stats['Hourly Rate'].apply(lambda x: f"€{x:.2f}")
    location_stats['Hours Played'] = location_stats['Hours Played'].astype(int)
    location_stats['Win %'] = location_stats['Win %'].astype(int)
    location_stats.index.name = 'Location'
    location_stats.index = [f"**{loc}**" for loc in location_stats.index]

    styled_table = location_stats.style.set_table_styles([
        {"selector": "th", "props": [("text-align", "center"), ("font-weight", "bold")]}
    ]).set_properties(**{"text-align": "right"})

    st.dataframe(styled_table, use_container_width=True)

# --- TAB 4: CHARTS ---
with tab4:
    st.markdown("### 📊 Profit Charts")
    chart_type = st.selectbox("Select Chart Type", ["Cumulative Profit", "Hourly Profit"])

    # Weekdays
    weekday_group = df.groupby('day_of_week').agg(
        total_profit=('netprofit_cad', 'sum'),
        total_hours=('session_hours', 'sum'),
        avg_hourly=('netprofit_cad', lambda x: x.sum() / df.loc[x.index, 'session_hours'].sum())
    ).reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])

    y1 = weekday_group['total_profit'] if chart_type == 'Cumulative Profit' else weekday_group['avg_hourly']
    hover1 = weekday_group['total_hours']
    fig1 = go.Figure([go.Bar(
        x=weekday_group.index,
        y=y1,
        text=[f"Hours: {int(h)}<br>€{v:.0f}" for h, v in zip(hover1, y1)],
        hovertemplate='%{text}<extra></extra>'
    )])
    fig1.update_layout(yaxis_title='€', height=500)
    st.plotly_chart(fig1)

    # Months
    month_group = df.groupby(['month', 'month_num']).agg(
        total_profit=('netprofit_cad', 'sum'),
        total_hours=('session_hours', 'sum'),
        avg_hourly=('netprofit_cad', lambda x: x.sum() / df.loc[x.index, 'session_hours'].sum())
    ).reset_index().sort_values('month_num')

    y2 = month_group['total_profit'] if chart_type == 'Cumulative Profit' else month_group['avg_hourly']
    hover2 = month_group['total_hours']
    fig2 = go.Figure([go.Bar(
        x=month_group['month'],
        y=y2,
        text=[f"Hours: {int(h)}<br>€{v:.0f}" for h, v in zip(hover2, y2)],
        hovertemplate='%{text}<extra></extra>'
    )])
    fig2.update_layout(yaxis_title='€', height=500)
    st.plotly_chart(fig2)
    st.markdown("<div style='text-align: right; font-size: small; color: gray;'>*No playing time in June, July and August</div>", unsafe_allow_html=True)

    # Years
    year_group = df.groupby('year').agg(
        total_profit=('netprofit_cad', 'sum'),
        total_hours=('session_hours', 'sum'),
        avg_hourly=('netprofit_cad', lambda x: x.sum() / df.loc[x.index, 'session_hours'].sum())
    )
    y3 = year_group['total_profit'] if chart_type == 'Cumulative Profit' else year_group['avg_hourly']
    hover3 = year_group['total_hours']
    fig3 = go.Figure([go.Bar(
        x=year_group.index.astype(str),
        y=y3,
        text=[f"Hours: {int(h)}<br>€{v:.0f}" for h, v in zip(hover3, y3)],
        hovertemplate='%{text}<extra></extra>'
    )])
    fig3.update_layout(
        yaxis_title='€',
        height=500,
        xaxis=dict(tickmode='array', tickvals=year_group.index.astype(str))
    )
    st.plotly_chart(fig3)

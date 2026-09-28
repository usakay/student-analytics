import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime
import time

# ============== KONFIGURASAUN ==============
API_URL = "https://web-production-d05f5.up.railway.app"
REFRESH_INTERVAL = 10  # segundu

# ============== KONFIGURASAUN PÁJINA ==============
st.set_page_config(
    page_title="Dashboard Atividade Estudante",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============== CSS PERSONALIZADU ==============
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 0.5rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0;
    }
    .metric-label {
        font-size: 1rem;
        opacity: 0.9;
        margin: 0;
    }
    </style>
""", unsafe_allow_html=True)


# ============== FUNSAUN ATU HALO FETCH API ==============
@st.cache_data(ttl=5)
def fetch_stats():
    """Ambil estatístika husi API"""
    try:
        r = requests.get(f"{API_URL}/api/stats", timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        st.error(f"Erru fetch stats: {e}")
    return None


@st.cache_data(ttl=5)
def fetch_recent_activities(limit=500):
    """Ambil atividade foun"""
    try:
        r = requests.get(
            f"{API_URL}/api/activities/recent?limit={limit}",
            timeout=15
        )
        if r.status_code == 200:
            return pd.DataFrame(r.json())
    except Exception as e:
        st.error(f"Erru fetch atividades: {e}")
    return pd.DataFrame()


def fetch_health():
    """Verifica status API"""
    try:
        r = requests.get(f"{API_URL}/health", timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


# ============== HEADER ==============
st.markdown(
    '<div class="main-header">📊 Dashboard Atividade Estudante</div>',
    unsafe_allow_html=True
)

# Verifica health
health = fetch_health()
if health:
    st.success(f"✅ API Online — {health['timestamp']}")
else:
    st.error("❌ API Offline — Verifica koneksaun ba API")

# ============== SIDEBAR ==============
with st.sidebar:
    st.header("⚙️ Konfigurasaun")

    auto_refresh = st.checkbox("Auto Refresh (5 segundu)", value=True)

    limit_activities = st.slider(
        "Total atividade hatudu",
        min_value=100,
        max_value=2000,
        value=500,
        step=100
    )

    st.divider()

    if st.button("🔄 Refresh Agora"):
        st.cache_data.clear()
        st.rerun()

    st.divider()

    st.markdown("### 📡 Informasaun API")
    st.code(f"URL: {API_URL}")
    st.code("Endpoint: /api/activities/recent")
    st.code("Endpoint: /api/stats")

    st.divider()

    st.markdown("### 📅 Oras Server")
    st.write(datetime.now().strftime("%d %B %Y, %H:%M:%S"))


# ============== FETCH DADUS ==============
stats = fetch_stats()
df = fetch_recent_activities(limit=limit_activities)

if stats is None:
    st.error("❌ La bele fetch dadus husi API.")
    st.stop()


# ============== METRIC CARDS ==============
st.markdown("## 📈 Metrika Prinsipál")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
        <div class="metric-card">
            <p class="metric-value">{stats['total_users']:,}</p>
            <p class="metric-label">👥 Total Estudante</p>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
        <div class="metric-card">
            <p class="metric-value">{stats['total_activities']:,}</p>
            <p class="metric-label">📊 Total Atividade</p>
        </div>
    """, unsafe_allow_html=True)

with col3:
    if not df.empty:
        unique_users = df['user_id'].nunique()
        st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value">{unique_users:,}</p>
                <p class="metric-label">🟢 Estudante Ativu (recente)</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class="metric-card">
                <p class="metric-value">-</p>
                <p class="metric-label">🟢 Estudante Ativu</p>
            </div>
        """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
        <div class="metric-card">
            <p class="metric-value">{stats['last_activity_id']:,}</p>
            <p class="metric-label">🎯 ID Atividade Ikus</p>
        </div>
    """, unsafe_allow_html=True)


# ============== VISUALIZASAUN ==============
if not df.empty:
    st.divider()
    st.markdown("## 📊 Análize Vizual")

    # Row 1: Distribuisaun Atividade & Top Estudante
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("### 🎯 Distribuisaun Tipu Atividade")
        activity_counts = df['activity_type'].value_counts().reset_index()
        activity_counts.columns = ['activity_type', 'count']

        fig = px.pie(
            activity_counts,
            values='count',
            names='activity_type',
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.markdown("### 🏆 Top 10 Estudante Ativu Liu")
        top_users = df['username'].value_counts().head(10).reset_index()
        top_users.columns = ['username', 'count']

        fig = px.bar(
            top_users,
            x='count',
            y='username',
            orientation='h',
            color='count',
            color_continuous_scale='Viridis'
        )
        fig.update_layout(
            height=400,
            yaxis={'categoryorder': 'total ascending'},
            xaxis_title="Total Atividade",
            yaxis_title=""
        )
        st.plotly_chart(fig, use_container_width=True)

    # Row 2: Timeline
    st.markdown("### ⏰ Timeline Atividade")
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df_sorted = df.sort_values('timestamp')

    timeline = df_sorted.set_index('timestamp').resample('1min').size().reset_index()
    timeline.columns = ['timestamp', 'count']

    fig = px.line(
        timeline,
        x='timestamp',
        y='count',
        markers=True,
        title="Atividade per Minutu"
    )
    fig.update_traces(line_color='#1f77b4', line_width=2)
    fig.update_layout(
        height=350,
        xaxis_title="Oras",
        yaxis_title="Total Atividade"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Row 3: Device & Score
    col_left2, col_right2 = st.columns(2)

    with col_left2:
        st.markdown("### 💻 Distribuisaun Device")
        device_counts = df['device'].str.slice(0, 30).value_counts().head(10).reset_index()
        device_counts.columns = ['device', 'count']

        fig = px.bar(
            device_counts,
            x='device',
            y='count',
            color='device',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig.update_layout(
            height=350,
            showlegend=False,
            xaxis_title="Device",
            yaxis_title="Total"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_right2:
        st.markdown("### 📊 Skor Kuis")
        quiz_df = df[df['activity_type'] == 'mengerjakan_kuis'].copy()

        if not quiz_df.empty and 'metadata' in quiz_df.columns:
            quiz_df['score'] = quiz_df['metadata'].apply(
                lambda x: x.get('score') if isinstance(x, dict) else None
            )
            quiz_df = quiz_df.dropna(subset=['score'])

            if not quiz_df.empty:
                fig = px.histogram(
                    quiz_df,
                    x='score',
                    nbins=20,
                    color_discrete_sequence=['#ff7f0e']
                )
                fig.update_layout(
                    height=350,
                    xaxis_title="Skor",
                    yaxis_title="Frekénsia",
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("La iha skor kuis iha dadus recente")
        else:
            st.info("La iha dadus kuis iha atividade recente")

    # Row 4: Table
    st.divider()
    st.markdown("### 📋 Tabela Atividade Foun (50 liña)")

    display_df = df.head(50).copy()
    display_df = display_df[
        ['id', 'username', 'activity_type', 'timestamp', 'device', 'ip_address']
    ]
    display_df['timestamp'] = pd.to_datetime(
        display_df['timestamp']
    ).dt.strftime('%Y-%m-%d %H:%M:%S')

    st.dataframe(
        display_df,
        use_container_width=True,
        height=400,
        hide_index=True
    )

    # Row 5: Raw Stats
    st.divider()
    st.markdown("### 🔢 Dadus Mentah API")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**`/api/stats` Resposta:**")
        st.json(stats)
    with col_b:
        st.markdown("**Informasaun:**")
        st.write(f"- Total hatudu: {len(df):,}")
        st.write(f"- Intervalu: {df['timestamp'].min()} → {df['timestamp'].max()}")
        st.write(f"- Tipu atividade úniku: {df['activity_type'].nunique()}")

else:
    st.warning("⏳ Seidauk iha dadus atividade. Halo bot atu hatama dadus.")


# ============== AUTO REFRESH ==============
if auto_refresh:
    time.sleep(REFRESH_INTERVAL)
    st.rerun()
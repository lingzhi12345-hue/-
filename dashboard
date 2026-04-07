import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta
import numpy as np

# ─────────────────────────────────────────
# 页面配置
# ─────────────────────────────────────────
st.set_page_config(page_title="抖音游戏大盘看板", layout="wide")

st.title("🎮 抖音游戏大盘看板")

# ─────────────────────────────────────────
# 侧边栏：期数配置
# ─────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 期数配置")

    st.subheader("本期（绿灯期）")
    current_start = st.date_input("本期开始", value=date(2025, 4, 1), key="cs")
    current_end   = st.date_input("本期结束", value=date(2025, 4, 30), key="ce")

    st.subheader("上期")
    last_start = st.date_input("上期开始", value=date(2025, 2, 1), key="ls")
    last_end   = st.date_input("上期结束", value=date(2025, 2, 28), key="le")

# ─────────────────────────────────────────
# 模拟数据生成
# ─────────────────────────────────────────
def make_mock_data(start: date, end: date, base: int, trend: float = 1.0) -> pd.DataFrame:
    """生成一段时间的模拟日数据"""
    days = (end - start).days + 1
    dates = [start + timedelta(days=i) for i in range(days)]
    np.random.seed(42)
    play  = (base + np.cumsum(np.random.randn(days) * base * 0.03)) * trend
    supply = (base * 0.4 + np.cumsum(np.random.randn(days) * base * 0.01)) * trend
    return pd.DataFrame({
        "日期":   dates,
        "播放量": play.clip(min=0).astype(int),
        "供给量": supply.clip(min=0).astype(int),
    })

# 大盘：今年 1.1 到今天
dashboard_df = make_mock_data(date(2025, 1, 1), date(2025, 4, 7), base=500_000)

# 绿灯：本期 & 上期
current_df = make_mock_data(current_start, current_end, base=500_000, trend=1.2)
last_df    = make_mock_data(last_start,    last_end,    base=500_000, trend=1.0)

# ─────────────────────────────────────────
# 颜色 & 样式常量
# ─────────────────────────────────────────
COLOR_CURRENT = "#FF6B35"   # 本期：橙
COLOR_LAST    = "#4A90D9"   # 上期：蓝
COLOR_GRID    = "rgba(255,255,255,0.08)"

CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor ="rgba(0,0,0,0)",
    font=dict(color="#CCCCCC", size=12),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=10, r=10, t=40, b=10),
    xaxis=dict(showgrid=True, gridcolor=COLOR_GRID, zeroline=False),
    yaxis=dict(showgrid=True, gridcolor=COLOR_GRID, zeroline=False),
    hovermode="x unified",
)

def fmt(n: int) -> str:
    """数字格式化：万"""
    return f"{n/10000:.1f}w"

# ─────────────────────────────────────────
# 板块二：抖音专区
# ─────────────────────────────────────────
st.markdown("---")
st.subheader("📊 抖音专区")

tab_dashboard, tab_green = st.tabs(["大盘", "🟢 绿灯专区"])

# ── Tab1：大盘 ──────────────────────────
with tab_dashboard:

    metrics = ["播放量", "供给量"]

    cols = st.columns(len(metrics))
    for col, metric in zip(cols, metrics):
        with col:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dashboard_df["日期"],
                y=dashboard_df[metric],
                mode="lines",
                name=metric,
                line=dict(color=COLOR_CURRENT, width=2),
                fill="tozeroy",
                fillcolor="rgba(255,107,53,0.08)",
                hovertemplate=f"%{{x}}<br>{metric}: %{{y:,.0f}}<extra></extra>",
            ))

            # 今日竖线
            today = date(2025, 4, 7)
            fig.add_vline(
                x=str(today),
                line_width=1,
                line_dash="dash",
                line_color="rgba(255,255,255,0.4)",
                annotation_text="今日",
                annotation_position="top right",
                annotation_font_color="rgba(255,255,255,0.5)",
            )

            fig.update_layout(**CHART_LAYOUT, title=dict(text=metric, x=0.01))
            st.plotly_chart(fig, use_container_width=True)

            # 最新值 & 区间最大值
            latest = int(dashboard_df[metric].iloc[-1])
            peak   = int(dashboard_df[metric].max())
            m1, m2 = st.columns(2)
            m1.metric("最新", fmt(latest))
            m2.metric("区间峰值", fmt(peak))

# ── Tab2：绿灯专区 ──────────────────────
with tab_green:

    # 对齐到相对天数
    def to_relative(df: pd.DataFrame, start: date) -> pd.DataFrame:
        df = df.copy()
        df["Day"] = (pd.to_datetime(df["日期"]) - pd.Timestamp(start)).dt.days + 1
        return df

    cur = to_relative(current_df, current_start)
    lst = to_relative(last_df,    last_start)

    # 对齐长度（取较短的那个，避免越界）
    max_day = min(cur["Day"].max(), lst["Day"].max())
    cur = cur[cur["Day"] <= max_day]
    lst = lst[lst["Day"] <= max_day]

    metrics = ["播放量", "供给量"]
    cols = st.columns(len(metrics))

    for col, metric in zip(cols, metrics):
        with col:
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=cur["Day"], y=cur[metric],
                mode="lines", name=f"本期（{current_start.strftime('%m.%d')}起）",
                line=dict(color=COLOR_CURRENT, width=2.5),
                hovertemplate=f"Day %{{x}}<br>本期 {metric}: %{{y:,.0f}}<extra></extra>",
            ))
            fig.add_trace(go.Scatter(
                x=lst["Day"], y=lst[metric],
                mode="lines", name=f"上期（{last_start.strftime('%m.%d')}起）",
                line=dict(color=COLOR_LAST, width=2, dash="dot"),
                hovertemplate=f"Day %{{x}}<br>上期 {metric}: %{{y:,.0f}}<extra></extra>",
            ))

            fig.update_layout(**CHART_LAYOUT, title=dict(text=metric, x=0.01))
            st.plotly_chart(fig, use_container_width=True)

            # 环比计算（取最后一个对齐天）
            cur_last = int(cur[metric].iloc[-1])
            lst_last = int(lst[metric].iloc[-1])
            delta_pct = (cur_last - lst_last) / lst_last * 100 if lst_last else 0

            m1, m2, m3 = st.columns(3)
            m1.metric("本期最新", fmt(cur_last))
            m2.metric("上期同日", fmt(lst_last))
            m3.metric("环比", f"{delta_pct:+.1f}%", delta_color="normal")

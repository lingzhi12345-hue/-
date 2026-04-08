import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import io
import json
import base64
from pathlib import Path

# ============================================================
# 页面配置
# ============================================================
st.set_page_config(
    page_title="项目策略监测看板",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# 全局样式
# ============================================================
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .block-container { padding-top: 1rem; }
    .section-title {
        font-size: 20px;
        font-weight: bold;
        color: #ffffff;
        background: linear-gradient(90deg, #1a1f2e, #2d3561);
        padding: 10px 20px;
        border-left: 4px solid #4e79a7;
        border-radius: 4px;
        margin: 16px 0 8px 0;
    }
    .kpi-card {
        background: #1a1f2e;
        border-radius: 10px;
        padding: 16px 20px;
        text-align: center;
        border: 1px solid #2d3561;
    }
    .kpi-label { font-size: 13px; color: #a0aec0; margin-bottom: 4px; }
    .kpi-value { font-size: 26px; font-weight: bold; color: #ffffff; }
    .kpi-delta-up { font-size: 13px; color: #48bb78; }
    .kpi-delta-down { font-size: 13px; color: #fc8181; }
    .upload-box {
        background: #1a1f2e;
        border: 1px dashed #4e79a7;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 12px;
    }
    .config-box {
        background: #1a1f2e;
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 12px;
        border: 1px solid #2d3561;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# Session State 初始化
# ============================================================
if "data_store" not in st.session_state:
    st.session_state.data_store = {}
if "zone_config" not in st.session_state:
    st.session_state.zone_config = {
        "current_start": datetime(2025, 4, 1),
        "current_end":   datetime(2025, 4, 30),
        "prev_start":    datetime(2025, 2, 1),
        "prev_end":      datetime(2025, 2, 28),
    }

TODAY = datetime.now()

# ============================================================
# 工具函数
# ============================================================
def fmt_num(n, unit=""):
    if pd.isna(n):
        return "-"
    if abs(n) >= 1e8:
        return f"{n/1e8:.2f}亿{unit}"
    if abs(n) >= 1e4:
        return f"{n/1e4:.1f}万{unit}"
    return f"{n:.0f}{unit}"

def delta_html(val, reverse=False):
    """生成带颜色的涨跌幅 HTML"""
    if pd.isna(val):
        return "<span style='color:#a0aec0'>-</span>"
    pct = val * 100
    if (pct > 0 and not reverse) or (pct < 0 and reverse):
        return f"<span style='color:#48bb78'>▲ {abs(pct):.1f}%</span>"
    elif pct == 0:
        return "<span style='color:#a0aec0'>— 0.0%</span>"
    else:
        return f"<span style='color:#fc8181'>▼ {abs(pct):.1f}%</span>"

def safe_read_excel(file, sheet_name=None):
    try:
        if sheet_name:
            return pd.read_excel(file, sheet_name=sheet_name)
        return pd.read_excel(file, sheet_name=None)
    except Exception as e:
        st.error(f"文件解析失败：{e}")
        return None

def plotly_to_html(fig):
    return fig.to_html(full_html=False, include_plotlyjs=False)

# ============================================================
# HTML 导出
# ============================================================
def generate_full_html(html_parts: list) -> str:
    plotly_cdn = '<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>'
    body = "\n".join(html_parts)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>项目策略监测看板</title>
{plotly_cdn}
<style>
body {{ background:#0e1117; color:#fff; font-family:'PingFang SC','Microsoft YaHei',sans-serif; margin:0; padding:16px; }}
.section-title {{
    font-size:20px; font-weight:bold; color:#fff;
    background:linear-gradient(90deg,#1a1f2e,#2d3561);
    padding:10px 20px; border-left:4px solid #4e79a7;
    border-radius:4px; margin:20px 0 10px 0;
}}
.kpi-row {{ display:flex; gap:12px; flex-wrap:wrap; margin-bottom:14px; }}
.kpi-card {{
    background:#1a1f2e; border-radius:10px; padding:16px 20px;
    text-align:center; border:1px solid #2d3561; min-width:160px; flex:1;
}}
.kpi-label {{ font-size:13px; color:#a0aec0; margin-bottom:4px; }}
.kpi-value {{ font-size:26px; font-weight:bold; color:#fff; }}
.sub-title {{ font-size:15px; color:#a0aec0; padding:8px 0 4px 4px; }}
.timeline-wrap {{ overflow-x:auto; }}
</style>
</head>
<body>
<h1 style="color:#4e79a7;text-align:center;margin-bottom:24px;">📊 项目策略监测看板</h1>
{body}
</body>
</html>"""

# ============================================================
# ============ 板块一：游戏 & 项目节点 ========================
# ============================================================
def render_block1(html_collector):
    st.markdown('<div class="section-title">🎮 板块一：游戏 & 项目节点（Q2 时间轴）</div>',
                unsafe_allow_html=True)
    html_collector.append('<div class="section-title">🎮 板块一：游戏 & 项目节点（Q2 时间轴）</div>')

    with st.expander("📂 上传节点数据（Excel）", expanded=True):
        st.markdown("""
        **Excel 格式要求（单 Sheet）：**

        | 节点类型 | 节点名称 | 日期 | 备注 |
        |---------|---------|------|------|
        | 游戏节点 | 某版本上线 | 2025-04-15 | 可选 |
        | 项目节点 | 追光计划新一期 | 2025-05-01 | 可选 |
        """)
        uploaded = st.file_uploader("上传节点文件", type=["xlsx", "xls"], key="block1_upload")
        if uploaded:
            df = safe_read_excel(uploaded, sheet_name=0)
            if df is not None:
                df.columns = [c.strip() for c in df.columns]
                # 列名兼容映射
                col_map = {}
                for c in df.columns:
                    if "类型" in c: col_map[c] = "节点类型"
                    elif "名称" in c or "名字" in c: col_map[c] = "节点名称"
                    elif "日期" in c or "时间" in c or "date" in c.lower(): col_map[c] = "日期"
                    elif "备注" in c or "说明" in c: col_map[c] = "备注"
                df.rename(columns=col_map, inplace=True)
                df["日期"] = pd.to_datetime(df["日期"], errors="coerce")
                st.session_state.data_store["block1"] = df
                st.success(f"✅ 已加载 {len(df)} 条节点数据")

    df = st.session_state.data_store.get("block1")
    # 无数据时用示例
    if df is None or df.empty:
        df = pd.DataFrame({
            "节点类型": ["游戏节点","游戏节点","游戏节点","游戏节点",
                        "项目节点","项目节点","项目节点"],
            "节点名称": ["4.0版本上线","春日活动","5.0版本更新","六月赛季",
                        "追光计划新一期","测试服招募","追光计划二期"],
            "日期": [datetime(2025,4,5), datetime(2025,4,15),
                    datetime(2025,5,1), datetime(2025,6,1),
                    datetime(2025,4,10), datetime(2025,4,25),
                    datetime(2025,5,20)],
            "备注": ["","","","","","",""]
        })
        st.info("ℹ️ 当前展示示例数据，上传文件后将自动替换")

    # Q2 时间范围
    q2_start = datetime(TODAY.year, 4, 1)
    q2_end   = datetime(TODAY.year, 6, 30)

    df = df[df["日期"].between(q2_start, q2_end)].copy()

    game_nodes = df[df["节点类型"].str.contains("游戏", na=False)]
    proj_nodes = df[df["节点类型"].str.contains("项目", na=False)]

    total_days = (q2_end - q2_start).days
    today_offset = max(0, min((TODAY - q2_start).days, total_days))

    fig = go.Figure()

    # 今日竖线
    fig.add_vline(
        x=TODAY,
        line_color="#f6c90e",
        line_width=2,
        line_dash="dash",
        annotation_text=f"今日 {TODAY.strftime('%m/%d')}",
        annotation_position="top",
        annotation_font_color="#f6c90e"
    )

    # 游戏节点（上方，y=1）
    if not game_nodes.empty:
        fig.add_trace(go.Scatter(
            x=game_nodes["日期"],
            y=[1.2] * len(game_nodes),
            mode="markers+text",
            marker=dict(size=14, color="#4e79a7", symbol="diamond"),
            text=game_nodes["节点名称"],
            textposition="top center",
            textfont=dict(color="#4e79a7", size=11),
            name="游戏节点",
            hovertemplate="<b>%{text}</b><br>%{x|%Y-%m-%d}<extra></extra>"
        ))

    # 项目节点（下方，y=0）
    if not proj_nodes.empty:
        fig.add_trace(go.Scatter(
            x=proj_nodes["日期"],
            y=[0.8] * len(proj_nodes),
            mode="markers+text",
            marker=dict(size=14, color="#e05c5c", symbol="circle"),
            text=proj_nodes["节点名称"],
            textposition="bottom center",
            textfont=dict(color="#e05c5c", size=11),
            name="项目节点",
            hovertemplate="<b>%{text}</b><br>%{x|%Y-%m-%d}<extra></extra>"
        ))

    fig.update_layout(
        paper_bgcolor="#0e1117",
        plot_bgcolor="#1a1f2e",
        height=260,
        xaxis=dict(
            range=[q2_start, q2_end],
            tickformat="%m/%d",
            dtick="M1",
            color="#a0aec0",
            gridcolor="#2d3561",
            showgrid=True
        ),
        yaxis=dict(
            visible=False,
            range=[0.4, 1.7]
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            font=dict(color="#a0aec0")
        ),
        margin=dict(l=10, r=10, t=40, b=10),
        font=dict(color="#ffffff")
    )

    st.plotly_chart(fig, use_container_width=True)
    html_collector.append(f'<div class="timeline-wrap">{plotly_to_html(fig)}</div>')

# ============================================================
# ============ 板块二：抖音专区监测 ===========================
# ============================================================

# ---------- 字段映射（与已有代码保持一致） ----------
FIELD_MAP = {
    "播放量": ["播放量", "播放", "play_count", "视频播放量", "总播放量"],
    "供给量": ["供给量", "供给", "supply_count", "视频供给", "投稿量", "投稿数"],
    "专注作者播放": ["专注作者播放", "专注播放", "focus_play", "核心作者播放"],
    "专注作者供给": ["专注作者供给", "专注供给", "focus_supply", "核心作者供给"],
    "日期": ["日期", "date", "时间", "统计日期", "dt"],
}

def resolve_col(df_cols, field):
    for alias in FIELD_MAP.get(field, [field]):
        for c in df_cols:
            if alias.lower() in c.lower() or c.lower() in alias.lower():
                return c
    return None

def render_block2(html_collector):
    st.markdown('<div class="section-title">📺 板块二：抖音专区监测</div>',
                unsafe_allow_html=True)
    html_collector.append('<div class="section-title">📺 板块二：抖音专区监测</div>')

    # 专区日期配置
    with st.expander("⚙️ 专区期数配置", expanded=False):
        cfg = st.session_state.zone_config
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**本期专区**")
            cur_s = st.date_input("本期开始日", value=cfg["current_start"].date(), key="cur_s")
            cur_e = st.date_input("本期结束日", value=cfg["current_end"].date(), key="cur_e")
        with col2:
            st.markdown("**上期专区**")
            prev_s = st.date_input("上期开始日", value=cfg["prev_start"].date(), key="prev_s")
            prev_e = st.date_input("上期结束日", value=cfg["prev_end"].date(), key="prev_e")
        if st.button("✅ 保存专区配置"):
            st.session_state.zone_config = {
                "current_start": datetime.combine(cur_s, datetime.min.time()),
                "current_end":   datetime.combine(cur_e, datetime.min.time()),
                "prev_start":    datetime.combine(prev_s, datetime.min.time()),
                "prev_end":      datetime.combine(prev_e, datetime.min.time()),
            }
            st.success("配置已保存")

    with st.expander("📂 上传抖音专区数据（Excel）", expanded=True):
        st.markdown("""
        **Excel Sheet 说明：**
        - Sheet `大盘数据`：日期、播放量、供给量、专注作者播放、专注作者供给
        - Sheet `绿灯数据`（可选，与大盘同字段，系统自动按日期截取）
        """)
        uploaded = st.file_uploader("上传专区文件", type=["xlsx","xls"], key="block2_upload")
        if uploaded:
            sheets = safe_read_excel(uploaded)
            if sheets is not None:
                st.session_state.data_store["block2_raw"] = sheets
                st.success(f"✅ 已加载 Sheets: {list(sheets.keys())}")

    sheets = st.session_state.data_store.get("block2_raw")
    df_main = _get_zone_df(sheets)
    if df_main is None:
        df_main = _gen_demo_zone_data()
        st.info("ℹ️ 当前展示示例数据，上传文件后将自动替换")

    _render_zone_overview(df_main, html_collector)
    _render_zone_green(df_main, html_collector)

def _get_zone_df(sheets):
    if sheets is None:
        return None
    key = None
    for k in sheets:
        if "大盘" in str(k) or "main" in str(k).lower():
            key = k
            break
    if key is None and sheets:
        key = list(sheets.keys())[0]
    if key is None:
        return None
    df = sheets[key].copy()
    df.columns = [str(c).strip() for c in df.columns]
    date_col = resolve_col(df.columns, "日期")
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df.rename(columns={date_col: "日期"}, inplace=True)
    return df

def _gen_demo_zone_data():
    np.random.seed(42)
    start = datetime(TODAY.year, 3, 1)
    dates = [start + timedelta(days=i) for i in range(120)]
    base_play  = 5_000_000
    base_sup   = 800
    trend = np.linspace(0, 0.3, 120)
    noise_p = np.random.normal(0, 0.05, 120)
    noise_s = np.random.normal(0, 0.03, 120)

    # 绿灯加成模拟
    green_boost = np.zeros(120)
    for i, d in enumerate(dates):
        # 上期绿灯 2月1日->按天偏移到3月1日模拟前10天
        # 本期绿灯 4月1日起
        cur_day = (d - datetime(TODAY.year, 4, 1)).days
        prev_day = (d - datetime(TODAY.year, 2, 1)).days
        if 0 <= cur_day <= 30:
            green_boost[i] = 0.15 * (1 - cur_day/60)
        if 0 <= prev_day <= 28:
            green_boost[i] += 0.10

    play   = (base_play  * (1 + trend + noise_p + green_boost)).astype(int)
    supply = (base_sup   * (1 + trend*0.5 + noise_s + green_boost*0.5)).astype(int)
    return pd.DataFrame({
        "日期": dates,
        "播放量": play,
        "供给量": supply,
        "专注作者播放": (play * 0.35).astype(int),
        "专注作者供给": (supply * 0.4).astype(int),
    })

def _render_zone_overview(df, html_collector):
    st.markdown('<div class="sub-title">📊 子版块1 — 抖音专区大盘（近90天）</div>',
                unsafe_allow_html=True)

    q2_start = datetime(TODAY.year, 3, 1)
    q2_end   = datetime(TODAY.year, 6, 30)
    mask = (df["日期"] >= q2_start) & (df["日期"] <= q2_end)
    dff = df[mask].sort_values("日期")

    play_col   = resolve_col(df.columns, "播放量") or "播放量"
    supply_col = resolve_col(df.columns, "供给量") or "供给量"
    fp_col     = resolve_col(df.columns, "专注作者播放") or "专注作者播放"
    fs_col     = resolve_col(df.columns, "专注作者供给") or "专注作者供给"

    # 播放趋势图
    fig_play = go.Figure()
    if play_col in dff.columns:
        fig_play.add_trace(go.Scatter(
            x=dff["日期"], y=dff[play_col],
            name="总播放量", line=dict(color="#4e79a7", width=2),
            fill="tozeroy", fillcolor="rgba(78,121,167,0.15)"
        ))
    if fp_col in dff.columns:
        fig_play.add_trace(go.Scatter(
            x=dff["日期"], y=dff[fp_col],
            name="专注作者播放", line=dict(color="#59a14f", width=2, dash="dot")
        ))
    _style_fig(fig_play, "播放量趋势（3-6月）", height=240)
    st.plotly_chart(fig_play, use_container_width=True)
    html_collector.append(plotly_to_html(fig_play))

    # 供给趋势图
    fig_sup = go.Figure()
    if supply_col in dff.columns:
        fig_sup.add_trace(go.Scatter(
            x=dff["日期"], y=dff[supply_col],
            name="总供给量", line=dict(color="#e05c5c", width=2),
            fill="tozeroy", fillcolor="rgba(224,92,92,0.15)"
        ))
    if fs_col in dff.columns:
        fig_sup.add_trace(go.Scatter(
            x=dff["日期"], y=dff[fs_col],
            name="专注作者供给", line=dict(color="#f28e2b", width=2, dash="dot")
        ))
    _style_fig(fig_sup, "供给量趋势（3-6月）", height=240)
    st.plotly_chart(fig_sup, use_container_width=True)
    html_collector.append(plotly_to_html(fig_sup))

def _render_zone_green(df, html_collector):
    st.markdown('<div class="sub-title">🟢 子版块2 — 绿灯专区环比</div>',
                unsafe_allow_html=True)

    cfg = st.session_state.zone_config
    cur_s  = cfg["current_start"]
    prev_s = cfg["prev_start"]

    # 构建"相对天数"数据（前10天 + 当天 + 后30天 = 41点）
    def build_relative(start_dt, label):
        rows = []
        for offset in range(-10, 31):
            d = start_dt + timedelta(days=offset)
            row = df[df["日期"] == d]
            if not row.empty:
                rows.append({
                    "offset": offset,
                    "label": label,
                    "播放量": row["播放量"].values[0] if "播放量" in row else np.nan,
                    "供给量": row["供给量"].values[0] if "供给量" in row else np.nan,
                })
            else:
                rows.append({"offset": offset, "label": label,
                             "播放量": np.nan, "供给量": np.nan})
        return pd.DataFrame(rows)

    df_cur  = build_relative(cur_s,  "本期绿灯")
    df_prev = build_relative(prev_s, "上期绿灯")

    x_ticks = list(range(-10, 31))
    x_labels = [str(x) if x != 0 else "开始当天" for x in x_ticks]

    # ------ 播放量环比 ------
    st.markdown("**🎬 播放量环比**")
    fig_gplay = go.Figure()
    fig_gplay.add_trace(go.Scatter(
        x=df_cur["offset"], y=df_cur["播放量"],
        name="本期绿灯", mode="lines+markers",
        line=dict(color="#4e79a7", width=2),
        marker=dict(size=6)
    ))
    fig_gplay.add_trace(go.Scatter(
        x=df_prev["offset"], y=df_prev["播放量"],
        name="上期绿灯", mode="lines+markers",
        line=dict(color="#e05c5c", width=2, dash="dash"),
        marker=dict(size=6, symbol="square")
    ))
    fig_gplay.add_vline(x=0, line_color="#f6c90e", line_dash="dash",
                        annotation_text="专区开始", annotation_font_color="#f6c90e")
    _style_fig(fig_gplay, "播放量 — 专区前10天至后30天", height=260)
    fig_gplay.update_xaxes(tickvals=x_ticks[::5], ticktext=x_labels[::5])
    st.plotly_chart(fig_gplay, use_container_width=True)
    html_collector.append(plotly_to_html(fig_gplay))

    # ------ 供给量环比 ------
    st.markdown("**📝 供给量环比**")
    fig_gsup = go.Figure()
    fig_gsup.add_trace(go.Scatter(
        x=df_cur["offset"], y=df_cur["供给量"],
        name="本期绿灯", mode="lines+markers",
        line=dict(color="#59a14f", width=2),
        marker=dict(size=6, symbol="circle")
    ))
    fig_gsup.add_trace(go.Scatter(
        x=df_prev["offset"], y=df_prev["供给量"],
        name="上期绿灯", mode="lines+markers",
        line=dict(color="#f28e2b", width=2, dash="dot"),
        marker=dict(size=7, symbol="triangle-up")
    ))
    fig_gsup.add_vline(x=0, line_color="#f6c90e", line_dash="dash",
                       annotation_text="专区开始", annotation_font_color="#f6c90e")
    _style_fig(fig_gsup, "供给量 — 专区前10天至后30天", height=260)
    fig_gsup.update_xaxes(tickvals=x_ticks[::5], ticktext=x_labels[::5])
    st.plotly_chart(fig_gsup, use_container_width=True)
    html_collector.append(plotly_to_html(fig_gsup))

def _style_fig(fig, title, height=300):
    fig.update_layout(
        title=dict(text=title, font=dict(color="#a0aec0", size=13)),
        paper_bgcolor="#0e1117",
        plot_bgcolor="#1a1f2e",
        height=height,
        font=dict(color="#ffffff"),
        legend=dict(font=dict(color="#a0aec0"), bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(color="#a0aec0", gridcolor="#2d3561", showgrid=True),
        yaxis=dict(color="#a0aec0", gridcolor="#2d3561", showgrid=True),
        margin=dict(l=10, r=10, t=36, b=10),
        hovermode="x unified"
    )

# ============================================================
# ============ 板块三：达人投放 ================================
# ============================================================
def render_block3(html_collector):
    st.markdown('<div class="section-title">💰 板块三：达人投放</div>',
                unsafe_allow_html=True)
    html_collector.append('<div class="section-title">💰 板块三：达人投放</div>')

    with st.expander("📂 上传达人投放数据（Excel）", expanded=True):
        st.markdown("""
        **Excel 字段说明（单 Sheet）：**

        | 字段 | 说明 |
        |------|------|
        | 平台 | 抖音 / B站 / 微博 等 |
        | 日期 | 发布日期 |
        | 一级单元 | 预算所属单元 |
        | 消耗金额 | 实际结算金额 |
        | 确认合作 | 是/否 |
        | 播放量 | 稿件播放量 |
        | 内容类型 | 剧情 / 测评 / 混剪 等 |
        | 是否爆款 | 是/否 |
        | 合作ID | 唯一标识（可选） |
        """)
        uploaded = st.file_uploader("上传投放文件", type=["xlsx","xls"], key="block3_upload")
        if uploaded:
            df = safe_read_excel(uploaded, sheet_name=0)
            if df is not None:
                df.columns = [str(c).strip() for c in df.columns]
                if "日期" in df.columns:
                    df["日期"] = pd.to_datetime(df["日期"], errors="coerce")
                st.session_state.data_store["block3"] = df
                st.success(f"✅ 已加载 {len(df)} 条投放数据")

    df = st.session_state.data_store.get("block3")
    if df is None or df.empty:
        df = _gen_demo_influencer()
        st.info("ℹ️ 当前展示示例数据，上传文件后将自动替换")

    col1, col2 = st.columns(2)

    # ---- Q2分平台消耗 & 播放 ----
    with col1:
        st.markdown("**📊 分平台消耗金额 & 播放量**")
        if "平台" in df.columns:
            grp = df.groupby("平台").agg(
                消耗金额=("消耗金额","sum"),
                播放量=("播放量","sum")
            ).reset_index()
            fig_plat = make_subplots(specs=[[{"secondary_y": True}]])
            fig_plat.add_trace(go.Bar(
                x=grp["平台"], y=grp["消耗金额"],
                name="消耗金额", marker_color="#4e79a7"
            ), secondary_y=False)
            fig_plat.add_trace(go.Scatter(
                x=grp["平台"], y=grp["播放量"],
                name="播放量", mode="lines+markers",
                line=dict(color="#f28e2b", width=2)
            ), secondary_y=True)
            fig_plat.update_layout(
                paper_bgcolor="#0e1117", plot_bgcolor="#1a1f2e",
                height=260, font=dict(color="#fff"),
                legend=dict(font=dict(color="#a0aec0"), bgcolor="rgba(0,0,0,0)"),
                margin=dict(l=10,r=10,t=30,b=10)
            )
            st.plotly_chart(fig_plat, use_container_width=True)
            html_collector.append(plotly_to_html(fig_plat))

    # ---- 一级单元预算消耗 ----
    with col2:
        st.markdown("**💼 各一级单元预算消耗**")
        if "一级单元" in df.columns:
            # 结算 + 确认合作
            confirmed = df[df.get("确认合作", pd.Series(["是"]*len(df))) == "是"] if "确认合作" in df.columns else df
            grp2 = confirmed.groupby("一级单元")["消耗金额"].sum().reset_index()
            grp2 = grp2.sort_values("消耗金额", ascending=True)
            fig_unit = go.Figure(go.Bar(
                x=grp2["消耗金额"], y=grp2["一级单元"],
                orientation="h",
                marker=dict(color="#59a14f")
            ))
            _style_fig(fig_unit, "一级单元消耗（确认合作）", height=260)
            st.plotly_chart(fig_unit, use_container_width=True)
            html_collector.append(plotly_to_html(fig_unit))

    # ---- 时间轴：发布条数 & 爆款条数 ----
    st.markdown("**📅 每日发布条数 & 爆款条数**")
    if "日期" in df.columns:
        daily = df.groupby("日期").agg(
            发布条数=("日期","count"),
        ).reset_index()
        if "是否爆款" in df.columns:
            boom = df[df["是否爆款"]=="是"].groupby("日期").size().reset_index(name="爆款条数")
            daily = daily.merge(boom, on="日期", how="left").fillna(0)
        else:
            daily["爆款条数"] = 0

        fig_daily = go.Figure()
        fig_daily.add_trace(go.Bar(
            x=daily["日期"], y=daily["发布条数"],
            name="发布条数", marker_color="#4e79a7"
        ))
        fig_daily.add_trace(go.Scatter(
            x=daily["日期"], y=daily["爆款条数"],
            name="爆款条数", mode="lines+markers",
            line=dict(color="#f6c90e", width=2)
        ))
        _style_fig(fig_daily, "每日发布 & 爆款", height=220

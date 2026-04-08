import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import io
import base64

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
    .sub-title {
        font-size: 16px;
        font-weight: bold;
        color: #ffffff;
        background: linear-gradient(90deg, #1a1f2e, #2d3561);
        padding: 8px 16px;
        border-left: 4px solid #59a14f;
        border-radius: 4px;
        margin: 14px 0 10px 0;
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
    .upload-hint {
        background: #1a1f2e;
        border: 1px solid #2d3561;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 16px;
    }
    /* 隐藏下载按钮，用自定义按钮 */
    .stDownloadButton { display: none; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# Session State 初始化
# ============================================================
if "data_store" not in st.session_state:
    st.session_state.data_store = {}
if "zone_config" not in st.session_state:
    # 专区配置：使用2025年的日期作为示例
    st.session_state.zone_config = {
        "current_start": datetime(2025, 4, 1),
        "current_end":   datetime(2025, 4, 30),
        "prev_start":    datetime(2025, 2, 1),
        "prev_end":      datetime(2025, 2, 28),
    }

TODAY = datetime(2025, 4, 8)  # 固定今日日期，确保在Q2范围内

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

def safe_read_excel(file, sheet_name=None):
    try:
        if sheet_name is not None:
            return pd.read_excel(file, sheet_name=sheet_name)
        else:
            return pd.read_excel(file, sheet_name=None)
    except Exception as e:
        st.error(f"文件解析失败：{e}")
        return None

def normalize_columns(df):
    if df is None:
        return df
    df.columns = [str(c).strip() if c is not None else "" for c in df.columns]
    return df

def plotly_to_html(fig):
    return fig.to_html(full_html=False, include_plotlyjs=False)

def get_period_info(date, p1_start, p2_start):
    """判断日期属于哪一期，并计算相对天数"""
    p1_window_start = p1_start - timedelta(days=15)
    p1_window_end = datetime(p1_start.year, p1_start.month + 1, 1) - timedelta(days=1) + timedelta(days=15)
    
    p2_window_start = p2_start - timedelta(days=15)
    p2_window_end = datetime(p2_start.year, p2_start.month + 1, 1) - timedelta(days=1) + timedelta(days=15)
    
    if p1_window_start <= date <= p1_window_end:
        delta = (date - p1_start).days
        return "上期", delta
    
    if p2_window_start <= date <= p2_window_end:
        delta = (date - p2_start).days
        return "本期", delta
    
    return None, None

def style_fig(fig, title, height=280):
    fig.update_layout(
        title=dict(text=title, font=dict(color="#a0aec0", size=14, family="PingFang SC")),
        paper_bgcolor="#0e1117",
        plot_bgcolor="#1a1f2e",
        height=height,
        font=dict(color="#ffffff", family="PingFang SC"),
        legend=dict(font=dict(color="#a0aec0"), bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(color="#a0aec0", gridcolor="#2d3561", showgrid=True),
        yaxis=dict(color="#a0aec0", gridcolor="#2d3561", showgrid=True),
        margin=dict(l=10, r=10, t=40, b=10),
        hovermode="x unified"
    )

# ============================================================
# HTML 导出 - 完整美观版本
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
* {{ box-sizing: border-box; }}
body {{ 
    background: #0e1117; 
    color: #fff; 
    font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif; 
    margin: 0; 
    padding: 20px 40px;
    max-width: 1600px;
    margin: 0 auto;
}}
h1 {{ 
    color: #4e79a7; 
    text-align: center; 
    margin-bottom: 24px;
    font-size: 28px;
}}
.section-title {{
    font-size: 20px; 
    font-weight: bold; 
    color: #fff;
    background: linear-gradient(90deg, #1a1f2e, #2d3561);
    padding: 12px 20px; 
    border-left: 4px solid #4e79a7;
    border-radius: 4px; 
    margin: 24px 0 16px 0;
}}
.sub-title {{
    font-size: 16px; 
    font-weight: bold; 
    color: #fff;
    background: linear-gradient(90deg, #1a1f2e, #2d3561);
    padding: 10px 16px; 
    border-left: 4px solid #59a14f;
    border-radius: 4px; 
    margin: 18px 0 12px 0;
}}
.kpi-row {{ 
    display: flex; 
    gap: 16px; 
    flex-wrap: wrap; 
    margin-bottom: 16px; 
}}
.kpi-card {{
    background: #1a1f2e; 
    border-radius: 10px; 
    padding: 18px 24px;
    text-align: center; 
    border: 1px solid #2d3561; 
    min-width: 180px; 
    flex: 1;
}}
.kpi-label {{ font-size: 14px; color: #a0aec0; margin-bottom: 6px; }}
.kpi-value {{ font-size: 28px; font-weight: bold; color: #fff; }}
.chart-container {{
    background: #1a1f2e;
    border-radius: 8px;
    padding: 16px;
    margin: 12px 0;
}}
.divider {{
    border-top: 1px solid #2d3561;
    margin: 24px 0;
}}
</style>
</head>
<body>
<h1>📊 项目策略监测看板</h1>
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
    
    df = st.session_state.data_store.get("block1")
    
    # 固定示例数据 - 确保在3.1-6.1范围内
    if df is None or df.empty:
        df = pd.DataFrame({
            "节点类型": [
                "游戏节点", "游戏节点", "游戏节点", "游戏节点", "游戏节点", "游戏节点",
                "项目节点", "项目节点", "项目节点", "项目节点", "项目节点"
            ],
            "节点名称": [
                "4.0版本上线", "春日活动「花之旅」", "劳动节限时活动", "5.0版本大更新", 
                "端午限定活动", "六月赛季更新",
                "追光计划新一期", "测试服招募", "创作者激励活动", "追光计划二期", "达人合作项目"
            ],
            "日期": [
                datetime(2025, 3, 15), datetime(2025, 4, 5), datetime(2025, 4, 28),
                datetime(2025, 5, 1), datetime(2025, 5, 28), datetime(2025, 6, 15),
                datetime(2025, 3, 20), datetime(2025, 4, 10), datetime(2025, 4, 25),
                datetime(2025, 5, 15), datetime(2025, 6, 1)
            ],
            "备注": [
                "新版本", "限时活动", "节日活动", "大版本更新", "节日活动", "赛季更新",
                "达人合作启动", "玩家招募", "激励计划", "二期启动", "合作项目"
            ]
        })
    
    # 时间轴范围：3.1 - 6.1
    q2_start = datetime(2025, 3, 1)
    q2_end   = datetime(2025, 6, 1)
    
    if "日期" in df.columns:
        df["日期"] = pd.to_datetime(df["日期"], errors="coerce")
        df = df[df["日期"].between(q2_start, q2_end)].copy()
    
    game_nodes = df[df["节点类型"].str.contains("游戏", na=False)] if "节点类型" in df.columns else pd.DataFrame()
    proj_nodes = df[df["节点类型"].str.contains("项目", na=False)] if "节点类型" in df.columns else pd.DataFrame()
    
    fig = go.Figure()
    
    # 隐藏的基准线
    fig.add_trace(go.Scatter(
        x=[q2_start, q2_end],
        y=[1, 1],
        mode="markers",
        marker=dict(size=0, color="rgba(0,0,0,0)"),
        showlegend=False,
        hoverinfo="skip"
    ))
    
    # 游戏节点（上方，y=1.2）
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
    
    # 项目节点（下方，y=0.8）
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
        height=280,
        xaxis=dict(
            range=[q2_start, q2_end],
            tickformat="%m/%d",
            dtick="M1",
            color="#a0aec0",
            gridcolor="#2d3561",
            showgrid=True
        ),
        yaxis=dict(visible=False, range=[0.4, 1.7]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(color="#a0aec0")),
        margin=dict(l=10, r=10, t=40, b=10),
        font=dict(color="#ffffff")
    )
    
    # 今日竖线
    today_str = TODAY.strftime("%Y-%m-%d")
    fig.add_shape(type="line", x0=today_str, x1=today_str, y0=0, y1=1, yref="paper",
                  line_color="#f6c90e", line_dash="dash", line_width=2)
    fig.add_annotation(x=today_str, y=1.02, yref="paper", text=f"今日 {TODAY.strftime('%m/%d')}",
                       showarrow=False, font_color="#f6c90e", font_size=11)
    
    st.plotly_chart(fig, use_container_width=True)
    html_collector.append(f'<div class="chart-container">{plotly_to_html(fig)}</div>')

# ============================================================
# ============ 板块二：抖音专区监测 ===========================
# ============================================================
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
    
    df = st.session_state.data_store.get("block2")
    if df is None or df.empty:
        df = _gen_demo_zone_data()
        st.info("ℹ️ 当前展示示例数据，上传文件后将自动替换")
    
    _render_zone_overview(df, html_collector)
    _render_zone_green(df, html_collector)

def _gen_demo_zone_data():
    """生成演示数据 - 确保覆盖专区期间"""
    np.random.seed(42)
    
    # 生成覆盖两个专区期间的数据
    # 上期：2025-02-01 到 2025-02-28，窗口范围 1月16日-3月15日
    # 本期：2025-04-01 到 2025-04-30，窗口范围 3月16日-5月15日
    
    dates = []
    plays = []
    supplies = []
    
    # 上期专区数据
    for i in range(-15, 45):  # 1月16日 到 3月15日
        d = datetime(2025, 2, 1) + timedelta(days=i)
        dates.append(d)
        base = 5_000_000
        boost = 0
        if 0 <= i <= 28:  # 专区期间有加成
            boost = 0.15 * (1 - abs(i-14)/28)
        plays.append(int(base * (1 + boost + np.random.uniform(-0.05, 0.05))))
        supplies.append(int(800 * (1 + boost*0.5 + np.random.uniform(-0.03, 0.03))))
    
    # 本期专区数据
    for i in range(-15, 45):  # 3月16日 到 5月15日
        d = datetime(2025, 4, 1) + timedelta(days=i)
        dates.append(d)
        base = 6_000_000
        boost = 0
        if 0 <= i <= 30:  # 专区期间有加成
            boost = 0.18 * (1 - abs(i-15)/30)
        plays.append(int(base * (1 + boost + np.random.uniform(-0.05, 0.05))))
        supplies.append(int(900 * (1 + boost*0.5 + np.random.uniform(-0.03, 0.03))))
    
    return pd.DataFrame({
        "日期": dates,
        "播放量": plays,
        "供给量": supplies,
        "专注作者播放": [int(p * 0.35) for p in plays],
        "专注作者供给": [int(s * 0.4) for s in supplies],
    })

def _render_zone_overview(df, html_collector):
    """子版块1：抖音专区大盘（近90天）"""
    st.markdown('<div class="sub-title">📊 子版块1 — 抖音专区大盘（近90天）</div>',
                unsafe_allow_html=True)
    html_collector.append('<div class="sub-title">📊 子版块1 — 抖音专区大盘（近90天）</div>')
    
    if "日期" not in df.columns:
        st.warning("⚠️ 数据缺少日期列")
        return
    
    # 近90天范围
    range_start = TODAY - timedelta(days=90)
    range_end = TODAY
    df["日期"] = pd.to_datetime(df["日期"], errors="coerce")
    mask = (df["日期"] >= range_start) & (df["日期"] <= range_end)
    dff = df[mask].sort_values("日期").copy()
    
    # 播放趋势图
    fig_play = go.Figure()
    if "播放量" in df.columns:
        fig_play.add_trace(go.Scatter(
            x=dff["日期"], y=dff["播放量"],
            name="总播放量", line=dict(color="#4e79a7", width=2),
            fill="tozeroy", fillcolor="rgba(78,121,167,0.15)"
        ))
    if "专注作者播放" in df.columns:
        fig_play.add_trace(go.Scatter(
            x=dff["日期"], y=dff["专注作者播放"],
            name="专注作者播放", line=dict(color="#59a14f", width=2, dash="dot")
        ))
    style_fig(fig_play, "播放量趋势")
    st.plotly_chart(fig_play, use_container_width=True)
    html_collector.append(f'<div class="chart-container">{plotly_to_html(fig_play)}</div>')
    
    # 供给趋势图
    fig_sup = go.Figure()
    if "供给量" in df.columns:
        fig_sup.add_trace(go.Scatter(
            x=dff["日期"], y=dff["供给量"],
            name="总供给量", line=dict(color="#e05c5c", width=2),
            fill="tozeroy", fillcolor="rgba(224,92,92,0.15)"
        ))
    if "专注作者供给" in df.columns:
        fig_sup.add_trace(go.Scatter(
            x=dff["日期"], y=dff["专注作者供给"],
            name="专注作者供给", line=dict(color="#f28e2b", width=2, dash="dot")
        ))
    style_fig(fig_sup, "供给量趋势")
    st.plotly_chart(fig_sup, use_container_width=True)
    html_collector.append(f'<div class="chart-container">{plotly_to_html(fig_sup)}</div>')

def _render_zone_green(df, html_collector):
    """子版块2：绿灯专区环比"""
    st.markdown('<div class="sub-title">🟢 子版块2 — 绿灯专区环比</div>',
                unsafe_allow_html=True)
    html_collector.append('<div class="sub-title">🟢 子版块2 — 绿灯专区环比</div>')
    
    cfg = st.session_state.zone_config
    p1_start = cfg["prev_start"]
    p2_start = cfg["current_start"]
    
    if "日期" in df.columns:
        df["日期"] = pd.to_datetime(df["日期"], errors="coerce")
        df[["期数", "相对天数"]] = df["日期"].apply(
            lambda x: pd.Series(get_period_info(x, p1_start, p2_start))
        )
        
        df_analysis = df.dropna(subset=["期数", "相对天数"]).copy()
        
        if df_analysis.empty:
            st.warning("⚠️ 当前数据范围不在专区期间内，无法展示环比")
            html_collector.append('<p style="color:#a0aec0;padding:20px;">⚠️ 当前数据范围不在专区期间内</p>')
            return
        
        df_analysis["相对天数"] = df_analysis["相对天数"].astype(int)
        
        # 按天聚合
        df_grouped = df_analysis.groupby(["期数", "相对天数"])[["播放量", "供给量"]].sum().reset_index()
        
        # 计算增幅
        def calc_growth(group, col):
            day0_val = group.loc[group["相对天数"] == 0, col].values
            if len(day0_val) > 0 and day0_val[0] != 0:
                base_val = day0_val[0]
                group[f"{col}_增幅"] = (group[col] - base_val) / base_val
            else:
                group[f"{col}_增幅"] = 0
            return group
        
        df_final = pd.DataFrame()
        for period in df_grouped["期数"].unique():
            period_data = df_grouped[df_grouped["期数"] == period].copy()
            period_data = calc_growth(period_data, "播放量")
            period_data = calc_growth(period_data, "供给量")
            df_final = pd.concat([df_final, period_data])
    else:
        st.warning("⚠️ 数据缺少日期列")
        return
    
    # 绘制4个图表
    def plot_green_chart(data, y_col, title, is_percentage=False):
        fig = go.Figure()
        styles = {
            "上期": {"dash": "solid", "color": "#1f77b4"},
            "本期": {"dash": "dash", "color": "#ff7f0e"}
        }
        for period_name in ["上期", "本期"]:
            subset = data[data["期数"] == period_name]
            if not subset.empty:
                fig.add_trace(go.Scatter(
                    x=subset["相对天数"],
                    y=subset[y_col],
                    mode="lines+markers",
                    name=period_name,
                    line=dict(color=styles[period_name]["color"], dash=styles[period_name]["dash"]),
                    marker=dict(size=6)
                ))
        
        fig.add_shape(type="line", x0=0, x1=0, y0=0, y1=1, yref="paper",
                      line_color="#f6c90e", line_dash="dash", line_width=2)
        
        fig.update_layout(
            title=dict(text=title, font=dict(color="#a0aec0", size=14)),
            xaxis_title="相对天数 (Day 0 = 绿灯专区开始日期)",
            hovermode="x unified",
            paper_bgcolor="#0e1117",
            plot_bgcolor="#1a1f2e",
            height=260,
            font=dict(color="#ffffff"),
            legend=dict(font=dict(color="#a0aec0")),
            xaxis=dict(color="#a0aec0", gridcolor="#2d3561", showgrid=True),
            yaxis=dict(color="#a0aec0", gridcolor="#2d3561", showgrid=True),
            margin=dict(l=10, r=10, t=40, b=10)
        )
        if is_percentage:
            fig.update_layout(yaxis_tickformat=".1%")
        return fig
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig1 = plot_green_chart(df_final, "播放量", "播放量趋势对比")
        st.plotly_chart(fig1, use_container_width=True)
        html_collector.append(f'<div class="chart-container">{plotly_to_html(fig1)}</div>')
        
        fig2 = plot_green_chart(df_final, "播放量_增幅", "播放量增幅对比", is_percentage=True)
        st.plotly_chart(fig2, use_container_width=True)
        html_collector.append(f'<div class="chart-container">{plotly_to_html(fig2)}</div>')
    
    with col2:
        fig3 = plot_green_chart(df_final, "供给量", "供给量趋势对比")
        st.plotly_chart(fig3, use_container_width=True)
        html_collector.append(f'<div class="chart-container">{plotly_to_html(fig3)}</div>')
        
        fig4 = plot_green_chart(df_final, "供给量_增幅", "供给量增幅对比", is_percentage=True)
        st.plotly_chart(fig4, use_container_width=True)
        html_collector.append(f'<div class="chart-container">{plotly_to_html(fig4)}</div>')

# ============================================================
# ============ 板块三：达人投放 ================================
# ============================================================
def render_block3(html_collector):
    st.markdown('<div class="section-title">💰 板块三：达人投放</div>',
                unsafe_allow_html=True)
    html_collector.append('<div class="section-title">💰 板块三：达人投放</div>')
    
    df = st.session_state.data_store.get("block3")
    if df is None or df.empty:
        df = _gen_demo_influencer()
        st.info("ℹ️ 当前展示示例数据，上传文件后将自动替换")
    
    col1, col2 = st.columns(2)
    
    # ---- 分平台消耗 & 播放 ----
    with col1:
        st.markdown('<div class="sub-title">📊 分平台消耗金额 & 播放量</div>',
                    unsafe_allow_html=True)
        if "平台" in df.columns:
            agg_dict = {}
            if "消耗金额" in df.columns:
                agg_dict["消耗金额"] = ("消耗金额", "sum")
            if "播放量" in df.columns:
                agg_dict["播放量"] = ("播放量", "sum")
            if not agg_dict:
                grp = pd.DataFrame({"平台": df["平台"].unique()})
            else:
                grp = df.groupby("平台").agg(**agg_dict).reset_index()
            
            fig_plat = make_subplots(specs=[[{"secondary_y": True}]])
            if "消耗金额" in grp.columns:
                fig_plat.add_trace(go.Bar(
                    x=grp["平台"], y=grp["消耗金额"],
                    name="消耗金额", marker_color="#4e79a7"
                ), secondary_y=False)
            if "播放量" in grp.columns:
                fig_plat.add_trace(go.Scatter(
                    x=grp["平台"], y=grp["播放量"],
                    name="播放量", mode="lines+markers",
                    line=dict(color="#f28e2b", width=2)
                ), secondary_y=True)
            style_fig(fig_plat, "")
            st.plotly_chart(fig_plat, use_container_width=True)
            html_collector.append(f'<div class="chart-container">{plotly_to_html(fig_plat)}</div>')
    
    # ---- 各一级单需求预算消耗 ----
    with col2:
        st.markdown('<div class="sub-title">💼 各一级单需求预算消耗</div>',
                    unsafe_allow_html=True)
        if "需求编号" in df.columns and "消耗金额" in df.columns:
            confirmed = df[df.get("确认合作", pd.Series(["是"]*len(df))) == "是"] if "确认合作" in df.columns else df
            grp2 = confirmed.groupby(["需求编号", "需求名称"], as_index=False)["消耗金额"].sum()
            grp2 = grp2.sort_values("消耗金额", ascending=True).tail(10)  # 只显示前10
            
            fig_unit = go.Figure()
            fig_unit.add_trace(go.Bar(
                x=grp2["消耗金额"],
                y=grp2.apply(lambda r: f"{r['需求编号']} {r['需求名称'][:18]}..." if len(str(r['需求名称'])) > 18 else f"{r['需求编号']} {r['需求名称']}", axis=1),
                orientation="h",
                marker=dict(color="#59a14f"),
                text=grp2["消耗金额"].apply(lambda x: fmt_num(x, "元")),
                textposition="outside",
                textfont=dict(color="#a0aec0", size=10)
            ))
            style_fig(fig_unit, "")
            fig_unit.update_layout(yaxis=dict(tickfont=dict(size=10)))
            st.plotly_chart(fig_unit, use_container_width=True)
            html_collector.append(f'<div class="chart-container">{plotly_to_html(fig_unit)}</div>')
    
    # ---- 时间轴：发布条数 & 爆款条数 ----
    st.markdown('<div class="sub-title">📅 每日发布条数 & 爆款条数</div>',
                unsafe_allow_html=True)
    if "日期" in df.columns:
        df["日期"] = pd.to_datetime(df["日期"], errors="coerce")
        daily = df.groupby("日期").agg(发布条数=("日期", "count")).reset_index()
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
        style_fig(fig_daily, "每日发布 & 爆款")
        st.plotly_chart(fig_daily, use_container_width=True)
        html_collector.append(f'<div class="chart-container">{plotly_to_html(fig_daily)}</div>')
    
    # ---- 内容类型效果 ----
    if "内容类型" in df.columns:
        st.markdown('<div class="sub-title">🎯 内容类型 × 数据效果</div>',
                    unsafe_allow_html=True)
        agg_dict2 = {"发布条数": ("内容类型", "count")}
        if "播放量" in df.columns:
            agg_dict2["播放量"] = ("播放量", "sum")
        if "消耗金额" in df.columns:
            agg_dict2["消耗金额"] = ("消耗金额", "sum")
        type_grp = df.groupby("内容类型").agg(**agg_dict2).reset_index()
        if "播放量" in type_grp.columns and "消耗金额" in type_grp.columns:
            type_grp["CPM"] = type_grp.apply(
                lambda r: r["消耗金额"]/r["播放量"]*1000 if r["播放量"]>0 else 0, axis=1)
        else:
            type_grp["CPM"] = 0
        
        fig_type = make_subplots(rows=1, cols=3, subplot_titles=["发布条数","播放量","CPM"])
        colors = ["#4e79a7","#e05c5c","#59a14f","#f28e2b","#b07aa1","#76b7b2"]
        clr = [colors[i % len(colors)] for i in range(len(type_grp))]
        if "发布条数" in type_grp.columns:
            fig_type.add_trace(go.Bar(x=type_grp["内容类型"],y=type_grp["发布条数"],
                marker_color=clr, showlegend=False), row=1,col=1)
        if "播放量" in type_grp.columns:
            fig_type.add_trace(go.Bar(x=type_grp["内容类型"],y=type_grp["播放量"],
                marker_color=clr, showlegend=False), row=1,col=2)
        if "CPM" in type_grp.columns:
            fig_type.add_trace(go.Bar(x=type_grp["内容类型"],y=type_grp["CPM"],
                marker_color=clr, showlegend=False), row=1,col=3)
        fig_type.update_layout(
            paper_bgcolor="#0e1117", plot_bgcolor="#1a1f2e",
            height=240, font=dict(color="#a0aec0"),
            margin=dict(l=10,r=10,t=36,b=10)
        )
        st.plotly_chart(fig_type, use_container_width=True)
        html_collector.append(f'<div class="chart-container">{plotly_to_html(fig_type)}</div>')
    
    # ---- CPM 异常值 ----
    st.markdown('<div class="sub-title">⚠️ 累计 CPM & 异常值合作</div>',
                unsafe_allow_html=True)
    total_play = df["播放量"].sum() if "播放量" in df.columns else 0
    total_cost = df["消耗金额"].sum() if "消耗金额" in df.columns else 0
    total_cpm  = total_cost / total_play * 1000 if total_play > 0 else 0
    
    if "播放量" in df.columns and "消耗金额" in df.columns:
        df["CPM_item"] = df.apply(
            lambda r: r["消耗金额"]/r["播放量"]*1000 if r["播放量"]>0 else 0, axis=1)
    else:
        df["CPM_item"] = 0
    top3_high = df.nlargest(3, "CPM_item")
    top3_low  = df.nsmallest(3, "CPM_item")
    
    c1, c2, c3 = st.columns([1,2,2])
    with c1:
        st.markdown(f"""
        <div class="kpi-card">
        <div class="kpi-label">累计 CPM</div>
        <div class="kpi-value">{total_cpm:.1f}</div>
        <div class="kpi-label">元/千次播放</div>
        </div>""", unsafe_allow_html=True)
    
    with c2:
        st.markdown("🔴 **拉高 CPM Top3**")
        id_col = "合作ID" if "合作ID" in df.columns else df.columns[0]
        for _, row in top3_high.iterrows():
            st.markdown(
                f"- `{row.get(id_col,'-')}` — CPM: **{row['CPM_item']:.1f}** "
                f"（消耗: {fmt_num(row.get('消耗金额',0),'元')} / "
                f"播放: {fmt_num(row.get('播放量',0))}）")
    
    with c3:
        st.markdown("🟢 **拉低 CPM Top3**")
        for _, row in top3_low.iterrows():
            st.markdown(
                f"- `{row.get(id_col,'-')}` — CPM: **{row['CPM_item']:.1f}** "
                f"（消耗: {fmt_num(row.get('消耗金额',0),'元')} / "
                f"播放: {fmt_num(row.get('播放量',0))}）")
    
    html_collector.append(f"""
    <div class="kpi-row">
    <div class="kpi-card">
    <div class="kpi-label">累计 CPM</div>
    <div class="kpi-value">{total_cpm:.1f}</div>
    <div class="kpi-label">元/千次播放</div>
    </div>
    </div>""")

def _gen_demo_influencer():
    """生成演示数据"""
    np.random.seed(7)
    platforms = ["抖音","B站","微博","小红书"]
    demands = [
        ("292435", "阴阳师2026年4月版本传播推广整合营销比选需求"),
        ("295678", "光遇春日活动达人合作需求"),
        ("301234", "巅峰极速新赛季推广需求"),
        ("304567", "萤火突击版本更新传播需求"),
        ("298901", "全平台创作者激励计划"),
        ("302456", "逆水寒手游周年庆传播需求"),
        ("296789", "梦幻西游新版本推广需求"),
        ("303456", "蛋仔派对UGC内容合作需求"),
    ]
    ctypes = ["剧情","测评","混剪","挑战赛","开箱"]
    n = 100
    dates = [datetime(2025, 3, 1) + timedelta(days=np.random.randint(0,90)) for _ in range(n)]
    costs = np.random.uniform(5000, 200000, n)
    plays = costs * np.random.uniform(5, 150, n)
    
    demand_choices = [demands[np.random.randint(0, len(demands))] for _ in range(n)]
    
    return pd.DataFrame({
        "日期": dates,
        "平台": np.random.choice(platforms, n),
        "需求编号": [d[0] for d in demand_choices],
        "需求名称": [d[1] for d in demand_choices],
        "内容类型": np.random.choice(ctypes, n),
        "消耗金额": costs.round(0),
        "播放量": plays.round(0).astype(int),
        "是否爆款": np.random.choice(["是","否"], n, p=[0.2,0.8]),
        "确认合作": np.random.choice(["是","否"], n, p=[0.85,0.15]),
        "合作ID": [f"KOL-{1000+i}" for i in range(n)],
    })

# ============================================================
# ============ 板块四：小喇叭 ==================================
# ============================================================
def render_block4(html_collector):
    st.markdown('<div class="section-title">📣 板块四：小喇叭 KPI 看板</div>',
                unsafe_allow_html=True)
    html_collector.append('<div class="section-title">📣 板块四：小喇叭 KPI 看板</div>')
    
    vdata = st.session_state.data_store.get("block4_video")
    ldata = st.session_state.data_store.get("block4_live")
    
    if vdata is None:
        vdata, ldata = _gen_demo_horn()
        st.info("ℹ️ 当前展示示例数据，上传文件后将自动替换")
    
    # ---------- 视频板块 ----------
    st.markdown('<div class="sub-title">🎬 视频板块</div>',
                unsafe_allow_html=True)
    html_collector.append('<div class="sub-title">🎬 视频板块</div>')
    
    if "日期" in vdata.columns and "主话题播放日增" in vdata.columns:
        vdata["日期"] = pd.to_datetime(vdata["日期"], errors="coerce")
        fig_vid = go.Figure()
        fig_vid.add_trace(go.Scatter(
            x=vdata["日期"], y=vdata["主话题播放日增"],
            mode="lines+markers", name="主话题播放日增",
            line=dict(color="#4e79a7", width=2),
            fill="tozeroy", fillcolor="rgba(78,121,167,0.15)"
        ))
        style_fig(fig_vid, "主话题播放量日增")
        st.plotly_chart(fig_vid, use_container_width=True)
        html_collector.append(f'<div class="chart-container">{plotly_to_html(fig_vid)}</div>')
    
    # KPI 卡片 - 视频
    v_kpis = [
        ("累计播放", "累计播放", "累计播放_上期"),
        ("累计投稿数", "累计投稿数", "累计投稿数_上期"),
    ]
    vcols = st.columns(len(v_kpis))
    kpi_html_parts = []
    for i, (label, cur_col, prev_col) in enumerate(v_kpis):
        cur_val  = vdata[cur_col].iloc[-1]  if cur_col  in vdata.columns else None
        prev_val = vdata[prev_col].iloc[-1] if prev_col in vdata.columns else None
        delta    = (cur_val - prev_val) / prev_val if (cur_val and prev_val and prev_val!=0) else None
        with vcols[i]:
            _kpi_card(label, cur_val, delta)
        kpi_html_parts.append(_kpi_card_html(label, cur_val, delta))
    html_collector.append(f'<div class="kpi-row">{"".join(kpi_html_parts)}</div>')
    
    # 粉丝分层
    if "粉丝分层" in vdata.columns:
        st.markdown("**不同粉丝分层指标**")
        layers = vdata.drop_duplicates("粉丝分层")
        fig_fan = make_subplots(rows=1, cols=2, subplot_titles=["人均投稿数","稿均播放数"])
        colors = ["#4e79a7","#e05c5c","#59a14f","#f28e2b","#b07aa1"]
        if "人均投稿数" in layers.columns:
            fig_fan.add_trace(go.Bar(x=layers["粉丝分层"],y=layers["人均投稿数"],
                marker_color=[colors[i%len(colors)] for i in range(len(layers))], showlegend=False), row=1,col=1)
        if "稿均播放数" in layers.columns:
            fig_fan.add_trace(go.Bar(x=layers["粉丝分层"],y=layers["稿均播放数"],
                marker_color=[colors[i%len(colors)] for i in range(len(layers))], showlegend=False), row=1,col=2)
        fig_fan.update_layout(paper_bgcolor="#0e1117", plot_bgcolor="#1a1f2e",
            height=220, font=dict(color="#a0aec0"), margin=dict(l=10,r=10,t=36,b=10))
        st.plotly_chart(fig_fan, use_container_width=True)
        html_collector.append(f'<div class="chart-container">{plotly_to_html(fig_fan)}</div>')
    
    # ---------- 直播板块 ----------
    if ldata is not None and not ldata.empty:
        st.markdown('<div class="sub-title">📡 直播板块</div>',
                    unsafe_allow_html=True)
        html_collector.append('<div class="sub-title">📡 直播板块</div>')
        
        l_kpis = [
            ("累计看播数", "累计看播数", "累计看播数_上期"),
            ("累计开播数", "累计开播数", "累计开播数_上期"),
        ]
        lcols = st.columns(len(l_kpis))
        kpi_html_parts2 = []
        for i, (label, cur_col, prev_col) in enumerate(l_kpis):
            cur_val  = ldata[cur_col].iloc[-1]  if cur_col  in ldata.columns else None
            prev_val = ldata[prev_col].iloc[-1] if prev_col in ldata.columns else None
            delta    = (cur_val - prev_val)/prev_val if (cur_val and prev_val and prev_val!=0) else None
            with lcols[i]:
                _kpi_card(label, cur_val, delta)
            kpi_html_parts2.append(_kpi_card_html(label, cur_val, delta))
        html_collector.append(f'<div class="kpi-row">{"".join(kpi_html_parts2)}</div>')
        
        # ACU分层图表 - 新增
        if "ACU分层" in ldata.columns:
            st.markdown("**不同ACU主播分层指标**")
            layers_l = ldata.drop_duplicates("ACU分层")
            fig_acu = make_subplots(rows=1, cols=2, subplot_titles=["场均看播","人均开播场次"])
            colors = ["#4e79a7","#e05c5c","#59a14f","#f28e2b","#b07aa1"]
            if "场均看播" in layers_l.columns:
                fig_acu.add_trace(go.Bar(x=layers_l["ACU分层"],y=layers_l["场均看播"],
                    marker_color=[colors[i%len(colors)] for i in range(len(layers_l))], showlegend=False), row=1,col=1)
            if "人均开播场次" in layers_l.columns:
                fig_acu.add_trace(go.Bar(x=layers_l["ACU分层"],y=layers_l["人均开播场次"],
                    marker_color=[colors[i%len(colors)] for i in range(len(layers_l))], showlegend=False), row=1,col=2)
            fig_acu.update_layout(paper_bgcolor="#0e1117", plot_bgcolor="#1a1f2e",
                height=220, font=dict(color="#a0aec0"), margin=dict(l=10,r=10,t=36,b=10))
            st.plotly_chart(fig_acu, use_container_width=True)
            html_collector.append(f'<div class="chart-container">{plotly_to_html(fig_acu)}</div>')

def _kpi_card(label, value, delta=None):
    val_str = fmt_num(value) if value is not None else "-"
    dlt_str = ""
    if delta is not None:
        pct = delta * 100
        color = "#48bb78" if pct >= 0 else "#fc8181"
        arrow = "▲" if pct >= 0 else "▼"
        dlt_str = f"<div style='color:{color};font-size:13px'>{arrow} {abs(pct):.1f}% vs 上周期</div>"
    st.markdown(f"""
    <div class="kpi-card">
    <div class="kpi-label">{label}</div>
    <div class="kpi-value">{val_str}</div>
    {dlt_str}
    </div>""", unsafe_allow_html=True)

def _kpi_card_html(label, value, delta=None):
    val_str = fmt_num(value) if value is not None else "-"
    dlt_str = ""
    if delta is not None:
        pct = delta * 100
        color = "#48bb78" if pct >= 0 else "#fc8181"
        arrow = "▲" if pct >= 0 else "▼"
        dlt_str = f"<div style='color:{color};font-size:13px'>{arrow} {abs(pct):.1f}% vs 上周期</div>"
    return f"""<div class="kpi-card">
    <div class="kpi-label">{label}</div>
    <div class="kpi-value">{val_str}</div>
    {dlt_str}
    </div>"""

def _gen_demo_horn():
    np.random.seed(99)
    start = datetime(2025, 3, 1)
    n = 37
    dates = [start + timedelta(days=i) for i in range(n)]
    base = 50_000_000
    vdf = pd.DataFrame({
        "日期": dates,
        "主话题播放日增": (np.random.uniform(0.8,1.3, n) * base * np.linspace(0.8,1.2,n)).astype(int),
        "累计播放":   np.cumsum(np.random.randint(40_000_000, 80_000_000, n)),
        "累计投稿数": np.cumsum(np.random.randint(800,1500, n)),
        "累计播放_上期":   np.cumsum(np.random.randint(35_000_000, 70_000_000, n)),
        "累计投稿数_上期": np.cumsum(np.random.randint(600,1200, n)),
        "粉丝分层": ["0-1k","1k-1w","1w-10w","10w+"] * 9 + ["0-1k"],
        "人均投稿数":   np.random.uniform(1,5,n).round(2),
        "稿均播放数":   np.random.randint(1000, 50000, n),
    })
    ldf = pd.DataFrame({
        "日期": dates,
        "累计看播数":  np.cumsum(np.random.randint(500_000, 2_000_000, n)),
        "累计开播数":  np.cumsum(np.random.randint(50, 200, n)),
        "累计看播数_上期":  np.cumsum(np.random.randint(400_000, 1_800_000, n)),
        "累计开播数_上期":  np.cumsum(np.random.randint(40, 180, n)),
        "ACU分层": ["<50","50-200","200-500","500+"] * 9 + ["<50"],
        "人均开播场次": np.random.uniform(1,8,n).round(2),
        "场均看播": np.random.randint(100, 2000, n),  # 新增
        "场均ACU": np.random.randint(50, 600, n),
    })
    return vdf, ldf

# ============================================================
# ============ 数据解析函数 ================================
# ============================================================
def parse_uploaded_data(uploaded_file):
    try:
        sheets = safe_read_excel(uploaded_file)
        if sheets is None:
            return
        
        if isinstance(sheets, dict):
            for sheet_name, df in sheets.items():
                df = normalize_columns(df)
                sheet_lower = str(sheet_name).lower()
                
                if "节点" in sheet_lower:
                    st.session_state.data_store["block1"] = df
                elif "大盘" in sheet_lower:
                    st.session_state.data_store["block2"] = df
                elif "投放" in sheet_lower:
                    st.session_state.data_store["block3"] = df
                elif "视频" in sheet_lower:
                    st.session_state.data_store["block4_video"] = df
                elif "直播" in sheet_lower:
                    st.session_state.data_store["block4_live"] = df
            
            if "block1" not in st.session_state.data_store:
                for sheet_name, df in sheets.items():
                    if "节点" in str(sheet_name):
                        st.session_state.data_store["block1"] = normalize_columns(df)
                        break
            
            st.success(f"✅ 已解析 {len(sheets)} 个数据表")
        else:
            df = normalize_columns(sheets)
            cols = [c.lower() for c in df.columns]
            if any("节点类型" in c or "节点名称" in c for c in cols):
                st.session_state.data_store["block1"] = df
            elif any("播放量" in c and "供给量" in c for c in cols):
                st.session_state.data_store["block2"] = df
            elif any("消耗金额" in c or "平台" in c for c in cols):
                st.session_state.data_store["block3"] = df
            st.success("✅ 数据已加载")
    except Exception as e:
        st.error(f"文件解析失败：{e}")

# ============================================================
# ============ 主程序入口 =====================================
# ============================================================
def main():
    st.markdown("""
    <h1 style='text-align:center;color:#4e79a7;margin-bottom:4px;'>
    📊 项目策略监测看板
    </h1>
    <p style='text-align:center;color:#a0aec0;font-size:13px;margin-bottom:20px;'>
    单一数据上传 · 自动解析 · 一键导出 HTML
    </p>
    """, unsafe_allow_html=True)
    
    html_parts = []
    
    # 侧边栏
    with st.sidebar:
        st.markdown("### ⚙️ 控制面板")
        st.markdown(f"**今日日期：** `{TODAY.strftime('%Y-%m-%d')}`")
        st.divider()
        
        # 单一上传入口
        st.markdown('<div class="upload-hint">', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "📤 上传数据文件（Excel）",
            type=["xlsx", "xls"],
            key="main_upload"
        )
        if uploaded_file:
            parse_uploaded_data(uploaded_file)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.divider()
        show_b1 = st.checkbox("板块一：游戏 & 项目节点", value=True)
        show_b2 = st.checkbox("板块二：抖音专区监测", value=True)
        show_b3 = st.checkbox("板块三：达人投放", value=True)
        show_b4 = st.checkbox("板块四：小喇叭", value=True)
        st.divider()
        
        # HTML 导出 - 预先生成内容
        def get_html_content():
            _parts = []
            if show_b1:
                _parts.append('<div class="section-title">🎮 板块一：游戏 & 项目节点（Q2 时间轴）</div>')
                _parts.append('<div class="chart-container"><p style="color:#a0aec0;padding:20px;">Q2 时间轴图表</p></div>')
                _parts.append('<div class="divider"></div>')
            if show_b2:
                _parts.append('<div class="section-title">📺 板块二：抖音专区监测</div>')
                _parts.append('<div class="sub-title">📊 子版块1 — 抖音专区大盘（近90天）</div>')
                _parts.append('<div class="chart-container"><p style="color:#a0aec0;padding:20px;">播放量趋势图表</p></div>')
                _parts.append('<div class="sub-title">🟢 子版块2 — 绿灯专区环比</div>')
                _parts.append('<div class="chart-container"><p style="color:#a0aec0;padding:20px;">环比对比图表</p></div>')
                _parts.append('<div class="divider"></div>')
            if show_b3:
                _parts.append('<div class="section-title">💰 板块三：达人投放</div>')
                _parts.append('<div class="sub-title">📊 分平台消耗金额 & 播放量</div>')
                _parts.append('<div class="chart-container"><p style="color:#a0aec0;padding:20px;">平台消耗图表</p></div>')
                _parts.append('<div class="sub-title">💼 各一级单需求预算消耗</div>')
                _parts.append('<div class="chart-container"><p style="color:#a0aec0;padding:20px;">需求预算图表</p></div>')
                _parts.append('<div class="divider"></div>')
            if show_b4:
                _parts.append('<div class="section-title">📣 板块四：小喇叭 KPI 看板</div>')
                _parts.append('<div class="sub-title">🎬 视频板块</div>')
                _parts.append('<div class="kpi-row"><div class="kpi-card"><div class="kpi-label">累计播放</div><div class="kpi-value">12.5亿</div></div><div class="kpi-card"><div class="kpi-label">累计投稿数</div><div class="kpi-value">3.2万</div></div></div>')
                _parts.append('<div class="sub-title">📡 直播板块</div>')
                _parts.append('<div class="kpi-row"><div class="kpi-card"><div class="kpi-label">累计看播数</div><div class="kpi-value">8500万</div></div><div class="kpi-card"><div class="kpi-label">累计开播数</div><div class="kpi-value">5200</div></div></div>')
            return generate_full_html(_parts)
        
        st.download_button(
            label="📥 导出为 HTML",
            data=get_html_content(),
            file_name=f"策略监测看板_{TODAY.strftime('%Y%m%d')}.html",
            mime="text/html",
            use_container_width=True
        )
    
    # 渲染各板块
    if show_b1:
        render_block1(html_parts)
        st.divider()
    if show_b2:
        render_block2(html_parts)
        st.divider()
    if show_b3:
        render_block3(html_parts)
        st.divider()
    if show_b4:
        render_block4(html_parts)

if __name__ == "__main__":
    main()

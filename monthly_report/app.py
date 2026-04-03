import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

# ==========================================
# 1. 页面基础配置 & CSS样式
# ==========================================
st.set_page_config(
    page_title="内容生态数据看板（完整版）",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS：用于卡片样式、锚点定位平滑滚动
st.markdown("""
<style>
    /* 平滑滚动 */
    html {
        scroll-behavior: smooth;
    }
    
    /* 通用卡片样式 */
    .card {
        background-color: #ffffff;
        border: 1px solid #e6e6e6;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 10px;
        height: 100%;
    }
    .card-title {
        font-size: 14px;
        color: #888;
        margin-bottom: 8px;
    }
    .card-value {
        font-size: 28px;
        font-weight: bold;
        color: #333;
    }
    .card-delta {
        font-size: 12px;
        margin-top: 5px;
    }
    
    /* 侧边栏导航样式 */
    .sidebar-nav {
        padding: 10px 0;
    }
    .sidebar-nav a {
        display: block;
        padding: 10px 15px;
        text-decoration: none;
        color: #333;
        border-radius: 4px;
        margin-bottom: 5px;
        transition: all 0.2s;
        border-left: 3px solid transparent;
    }
    .sidebar-nav a:hover {
        background-color: #f0f2f6;
        border-left: 3px solid #ff4b4b;
        color: #ff4b4b;
    }
    
    /* 板块标题样式 */
    .section-header {
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #f0f2f6;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 模拟数据生成
# ==========================================
@st.cache_data
def load_data():
    # 2.1 投稿趋势数据
    dates = pd.date_range(start="2026-03-01", end="2026-04-03", freq='D')
    trend_data = pd.DataFrame({
        '日期': dates,
        '投稿量': [random.randint(800, 1500) + i*5 for i in range(len(dates))],
        '通过量': [random.randint(600, 1200) + i*3 for i in range(len(dates))]
    })

    # 2.2 内容维度数据
    content_data = pd.DataFrame({
        '分类': ['游戏解说', '生活Vlog', '知识科普', '音乐舞蹈', '美食探店', '其他'],
        '数量': [4500, 3200, 2800, 1500, 1200, 800]
    })

    # 2.3 活动维度数据
    activity_data = pd.DataFrame({
        '活动名称': ['春日打卡挑战', '新番解说大赛', '生活妙招征集'],
        '参与人数': [1200, 850, 400],
        '投稿数量': [3500, 2100, 980],
        '状态': ['进行中', '进行中', '已结束']
    })

    # 2.4 主播分层 (板块五)
    streamer_data = pd.DataFrame({
        '层级': ['S级(头部)', 'A级(腰部)', 'B级(腿部)', 'C级(新增)'],
        '人数': [50, 300, 1500, 5000],
        '投稿占比': [0.35, 0.40, 0.20, 0.05],
        '活跃度': [0.98, 0.85, 0.60, 0.15]
    })

    # 2.5 核心作者数据 (板块六)
    author_data = pd.DataFrame({
        '排名': range(1, 11),
        '作者ID': [f"User_{random.randint(1000, 9999)}" for _ in range(10)],
        '投稿数': [random.randint(50, 100) for _ in range(10)],
        '播放量': [random.randint(100000, 500000) for _ in range(10)],
        '涨粉数': [random.randint(5000, 20000) for _ in range(10)]
    })

    # 2.6 下个月计划 (板块七)
    plan_data = {
        '目标投稿量': '50,000',
        '目标活跃作者': '2,000人',
        '重点活动': '夏季庆典',
        '核心策略': '扶持中腰部作者，提升内容质量'
    }

    return trend_data, content_data, activity_data, streamer_data, author_data, plan_data

# 加载数据
trend_df, content_df, activity_df, streamer_df, author_df, plan_dict = load_data()

# ==========================================
# 3. 侧边栏导航
# ==========================================
st.sidebar.title("📊 数据看板导航")
st.sidebar.markdown("""
<div class="sidebar-nav">
    <a href="#overview">① 数据概览</a>
    <a href="#trend">② 投稿趋势</a>
    <a href="#content">③ 内容维度</a>
    <a href="#activity">④ 活动维度</a>
    <a href="#streamer">⑤ 主播分层</a>
    <a href="#author">⑥ 核心作者分析</a>
    <a href="#plan">⑦ 下个月计划</a>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 4. 主内容区域板块
# ==========================================

# --- 板块一：数据概览 ---
st.markdown('<a id="overview"></a>', unsafe_allow_html=True)
st.header("板块一：数据概览", anchor=False)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="总投稿量", value="32,450", delta="12.5%")
with col2:
    st.metric(label="总通过量", value="28,100", delta="8.2%")
with col3:
    st.metric(label="活跃作者数", value="1,240", delta="5.1%")
with col4:
    st.metric(label="人均投稿", value="2.6", delta="-0.2%")

st.divider()

# --- 板块二：投稿趋势 ---
st.markdown('<a id="trend"></a>', unsafe_allow_html=True)
st.header("板块二：投稿趋势", anchor=False)

with st.expander("查看趋势分析详情", expanded=True):
    # 绘制折线图
    fig_trend = px.line(trend_df, x='日期', y=['投稿量', '通过量'], 
                        title='每日投稿与通过趋势',
                        labels={'value': '数量', 'variable': '类型'},
                        color_discrete_map={'投稿量': '#3b82f6', '通过量': '#10b981'})
    
    # 添加时间节点标记 (例如：3月15日新赛季开启)
    fig_trend.add_vline(x=datetime(2026, 3, 15), line_dash="dash", line_color="red",
                        annotation_text="新赛季更新", annotation_position="top left")
    
    # 锁定 Y 轴范围，防止异常值导致变形
    fig_trend.update_yaxes(rangemode="tozero")
    fig_trend.update_layout(hovermode="x unified", height=400)
    
    st.plotly_chart(fig_trend, use_container_width=True)

st.divider()

# --- 板块三：内容维度 ---
st.markdown('<a id="content"></a>', unsafe_allow_html=True)
st.header("板块三：内容维度", anchor=False)

col_left, col_right = st.columns([2, 1])
with col_left:
    # 环形图
    fig_pie = px.pie(content_df, values='数量', names='分类', hole=0.4, title='内容分类占比')
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_pie, use_container_width=True)

with col_right:
    st.markdown("#### 分类详情")
    st.dataframe(content_df, hide_index=True, use_container_width=True)

st.divider()

# --- 板块四：活动维度 ---
st.markdown('<a id="activity"></a>', unsafe_allow_html=True)
st.header("板块四：活动维度",

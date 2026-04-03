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

# 自定义CSS
st.markdown("""
<style>
    html { scroll-behavior: smooth; }
    
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
    
    .sidebar-nav { padding: 10px 0; }
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
    # 模拟投稿趋势数据
    dates = pd.date_range(start="2026-01-01", end="2026-04-03", freq='D')
    trend_data = pd.DataFrame({
        '日期': dates,
        '投稿量': [random.randint(800, 1500) + i*2 for i in range(len(dates))],
        '播放量': [random.randint(10000, 50000) + i*10 for i in range(len(dates))]
    })
    
    # 模拟内容分类数据
    category_data = pd.DataFrame({
        '分区': ['游戏', '知识', '生活', '娱乐', '音乐', '科技'],
        '投稿量': [4500, 3200, 2800, 2500, 1800, 1200]
    })
    
    # 模拟活动数据
    activity_data = pd.DataFrame({
        '活动名称': ['春节创作挑战', '新知训练营', '日常打卡', '新番安利'],
        '投稿量': [1500, 800, 2200, 950],
        '参与人数': [320, 150, 580, 210],
        '转化率': ['12%', '8%', '15%', '10%']
    })
    
    # 模拟核心作者数据
    author_data = pd.DataFrame({
        '作者': ['用户A', '用户B', '用户C', '用户D', '用户E'],
        '投稿量': [45, 38, 29, 21, 15],
        '涨粉数': [5200, 4100, 3800, 2500, 1900],
        '平均播放': [15000, 12000, 8000, 6000, 5000]
    })

    return trend_data, category_data, activity_data, author_data

trend_df, category_df, activity_df, author_df = load_data()

# ==========================================
# 3. 侧边栏导航
# ==========================================
with st.sidebar:
    st.title("📊 数据看板导航")
    st.markdown("---")
    st.markdown("""
    <div class="sidebar-nav">
        <a href="#section1">1. 核心概览</a>
        <a href="#section2">2. 内容趋势</a>
        <a href="#section3">3. 内容分布</a>
        <a href="#section4">4. 活动维度</a>
        <a href="#section5">5. 热点话题</a>
        <a href="#section6">6. 核心作者</a>
        <a href="#section7">7. 下月计划</a>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.info(f"数据更新时间：\n2026-04-03 16:32")
    # ==========================================
# 4. 主体内容区
# ==========================================
# ==========================================
# 4. 主体内容区
# ==========================================

# --- 板块一：核心概览 ---
st.markdown('<a id="section1"></a>', unsafe_allow_html=True)
st.header("板块一：核心概览", anchor=False)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown("""
    <div class="card">
        <div class="card-title">本月总投稿</div>
        <div class="card-value">12,580</div>
        <div class="card-delta" style="color: green;">↑ 15.2% 较上月</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="card">
        <div class="card-title">总播放量</div>
        <div class="card-value">580w+</div>
        <div class="card-delta" style="color: green;">↑ 8.5% 较上月</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="card">
        <div class="card-title">活跃作者数</div>
        <div class="card-value">1,245</div>
        <div class="card-delta" style="color: red;">↓ 2.1% 较上月</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="card">
        <div class="card-title">人均投稿量</div>
        <div class="card-value">2.8</div>
        <div class="card-delta" style="color: gray;">持平</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# --- 板块二：内容趋势 ---
st.markdown('<a id="section2"></a>', unsafe_allow_html=True)
st.header("板块二：内容趋势分析", anchor=False)

fig_trend = go.Figure()
fig_trend.add_trace(go.Scatter(
    x=trend_df['日期'], 
    y=trend_df['投稿量'],
    mode='lines+markers',
    name='投稿量',
    line=dict(color='#ff4b4b', width=2)
))

# 标记新赛季节点（模拟3月1日）
fig_trend.add_shape(
    type="line", x0="2026-03-01", y0=0, x1="2026-03-01", y1=trend_df['投稿量'].max(),
    line=dict(color="RoyalBlue", width=2, dash="dash")
)
fig_trend.add_annotation(x="2026-03-01", y=trend_df['投稿量'].max(), text="新赛季节点", showarrow=True, arrowhead=1)

fig_trend.update_layout(
    title='投稿量日趋势',
    xaxis_title='日期',
    yaxis_title='投稿量',
    hovermode='x unified',
    margin=dict(l=20, r=20, t=40, b=20)
)
st.plotly_chart(fig_trend, use_container_width=True)

# --- 板块三：内容分布 ---
st.markdown('<a id="section3"></a>', unsafe_allow_html=True)
st.header("板块三：内容分区分布", anchor=False)

col_a, col_b = st.columns([2, 1])
with col_a:
    fig_pie = px.pie(category_df, values='投稿量', names='分区', hole=0.4)
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    fig_pie.update_layout(margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig_pie, use_container_width=True)

with col_b:
    st.subheader("分区详情")
    st.dataframe(category_df.style.background_gradient(subset=['投稿量'], cmap='Reds'), hide_index=True)

# --- 板块四：活动维度 ---
st.markdown('<a id="section4"></a>', unsafe_allow_html=True)
st.header("板块四：活动维度分析", anchor=False)

st.markdown("各活动参与情况与转化率统计：")
st.dataframe(
    activity_df.style.bar(subset=['投稿量', '参与人数'], color='#d6eaf8'),
    use_container_width=True,
    hide_index=True
)

# --- 板块五：热点话题 ---
st.markdown('<a id="section5"></a>', unsafe_allow_html=True)
st.header("板块五：热点话题（模拟）", anchor=False)

topics = st.columns(3)
topics_list = [
    ("话题A - 新番讨论", "热度: 9.8w"),
    ("话题B - 春季摄影", "热度: 8.5w"),
    ("话题C - 硬核科普", "热度: 7.2w")
]

for i, topic in enumerate(topics_list):
    with topics[i]:
        st.markdown(f"""
        <div class="card">
            <div class="card-title">{topic[0]}</div>
            <div class="card-value">{topic[1]}</div>
        </div>
        """, unsafe_allow_html=True)

# --- 板块六：核心作者分析 ---
st.markdown('<a id="section6"></a>', unsafe_allow_html=True)
st.header("板块六：核心作者分析", anchor=False)

fig_author = px.scatter(
    author_df, 
    x='投稿量', 
    y='涨粉数', 
    size='平均播放', 
    color='作者',
    hover_name='作者',
    size_max=60
)
fig_author.update_layout(title='核心作者贡献分布（气泡大小代表平均播放量）')
st.plotly_chart(fig_author, use_container_width=True)

# --- 板块七：下个月计划 ---
st.markdown('<a id="section7"></a>', unsafe_allow_html=True)
st.header("板块七：下个月计划与目标", anchor=False)

with st.expander("查看详细行动计划", expanded=True):
    st.markdown("""
    ### 1. 内容激励
    - **目标**：提升知识分区投稿量 20%。
    - **动作**：开展“知识创作月”活动，投入流量扶持 100w。

    ### 2. 作者运营
    - **目标**：引入/召回 10 位头部作者。
    - **动作**：定向发送邀请邮件，提供签约权益包。

    ### 3. 产品优化
    - **目标**：降低发布门槛。
    - **动作**：优化移动端发布器，支持多段视频拼接。
    """)

st.success("报告生成完毕")

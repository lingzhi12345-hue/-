import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

# ==========================================
# 1. 页面基础配置
# ==========================================
st.set_page_config(
    page_title="内容生态数据月报（完整版）",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. 模拟数据生成函数
# ==========================================
@st.cache_data
def load_data():
    # 2.1 投稿趋势数据
    dates = pd.date_range(start="2026-03-01", end="2026-03-31")
    post_counts = [random.randint(80, 150) for _ in range(len(dates))]
    df_trend = pd.DataFrame({"日期": dates, "投稿量": post_counts})

    # 2.2 内容品类数据
    categories = ["科技", "财经", "生活", "娱乐", "教育", "体育"]
    views = [random.randint(10000, 100000) for _ in categories]
    df_category = pd.DataFrame({"品类": categories, "浏览量": views})

    # 2.3 活动数据
    activities = ["春季创作赛", "新人扶持计划", "优质内容激励", "日常任务"]
    participants = [random.randint(100, 500) for _ in activities]
    df_activity = pd.DataFrame({"活动名称": activities, "参与人数": participants})

    # 2.4 核心作者数据
    authors = ["用户A", "用户B", "用户C", "用户D", "用户E"]
    author_posts = [random.randint(10, 30) for _ in authors]
    df_authors = pd.DataFrame({"作者": authors, "投稿数": author_posts})

    return df_trend, df_category, df_activity, df_authors

df_trend, df_category, df_authors = load_data()

# ==========================================
# 3. 侧边栏导航
# ==========================================
st.sidebar.title("导航栏")
st.sidebar.markdown("---")
st.sidebar.info("请向下滚动查看完整报告")

# ==========================================
# 4. 仪表盘主体内容
# ==========================================

# --- 标题 ---
st.title("📊 3月份内容生态数据月报")
st.markdown(f"**报告生成时间：** 2026年4月3日")

# ==========================================
# 板块一：核心指标总览
# ==========================================
st.header("板块一：核心指标总览", anchor="section1")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="总投稿量", value="3,245", delta="12%")
with col2:
    st.metric(label="总浏览量", value="1.2M", delta="5.4%")
with col3:
    st.metric(label="新增作者", value="158", delta="-3%")
with col4:
    st.metric(label="活跃用户", value="8,420", delta="8%")

st.markdown("---")

# ==========================================
# 板块二：内容趋势分析
# ==========================================
st.header("板块二：内容趋势分析", anchor="section2")

fig_trend = px.line(
    df_trend, 
    x="日期", 
    y="投稿量", 
    title="3月每日投稿趋势",
    markers=True,
    template="plotly_white"
)
st.plotly_chart(fig_trend, use_container_width=True)

st.markdown("---")

# ==========================================
# 板块三：内容品类分布
# ==========================================
st.header("板块三：内容品类分布", anchor="section3")

col_chart, col_table = st.columns([2, 1])

with col_chart:
    fig_pie = px.pie(
        df_category, 
        values="浏览量", 
        names="品类", 
        title="各品类浏览量占比",
        hole=0.4
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with col_table:
    st.subheader("品类数据明细")
    # 【修复】移除了 .style.background_gradient，避免 matplotlib 报错
    st.dataframe(df_category, hide_index=True, use_container_width=True)

st.markdown("---")

# ==========================================
# 板块四：活动维度分析
# ==========================================
st.header("板块四：活动维度分析", anchor="section4")

fig_bar = px.bar(
    df_activity, 
    x="活动名称", 
    y="参与人数", 
    title="各活动参与人数",
    color="参与人数",
    color_continuous_scale="Blues"
)
st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

# ==========================================
# 板块五：用户增长漏斗
# ==========================================
st.header("板块五：用户增长漏斗", anchor="section5")

# 模拟漏斗数据
funnel_data = pd.DataFrame({
    "阶段": ["浏览内容", "点击互动", "关注作者", "投稿创作"],
    "人数": [10000, 4500, 1200, 300]
})

fig_funnel = go.Figure(go.Funnel(
    y=funnel_data["阶段"],
    x=funnel_data["人数"],
    textposition="inside",
    textinfo="value+percent initial",
    marker={"color": ["#3A86FF", "#8338EC", "#FF006E", "#FB5607"]}
))

fig_funnel.update_layout(title="用户行为转化漏斗")
st.plotly_chart(fig_funnel, use_container_width=True)

st.markdown("---")

# ==========================================
# 板块六：核心作者分析
# ==========================================
st.header("板块六：核心作者分析", anchor="section6")

st.subheader("Top 5 活跃作者")
st.dataframe(
    df_authors.style.format({"投稿数": "{:.0f}"}),
    hide_index=True,
    use_container_width=True
)

# 简单的作者贡献说明
st.info("💡 结论：Top 5 作者贡献了全站约 15% 的优质内容。")

st.markdown("---")

# ==========================================
# 板块七：下个月计划
# ==========================================
st.header("板块七：下个月计划", anchor="section7")

st.subheader("1. 重点运营方向")
st.markdown("""
- **扶持新人**：启动“新星计划”，提供流量扶持。
- **优化算法**：提升中腰部内容的曝光权重。
""")

st.subheader("2. 关键活动预告")
st.markdown("""
- 4月中旬：举办“春日摄影大赛”。
- 4月下旬：开展“财经知识科普周”。
""")

st.subheader("3. 核心KPI目标")
col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
col_kpi1.metric("投稿量目标", "3,500", "+8%")
col_kpi2.metric("作者留存率", "45%", "+5%")
col_kpi3.metric("人均时长", "15分钟", "+2分钟")

# ==========================================
# 页脚
# ==========================================
st.markdown("---")
st.markdown("报告生成完毕 | GLM-5 & Streamlit 联合呈现")

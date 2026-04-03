import streamlit as st
import pandas as pd
import json
import os
import uuid
from datetime import datetime
import streamlit.components.v1 as components

# --- 1. 基础配置与样式 ---
st.set_page_config(
    page_title="创作者运营月报系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 极简风格CSS
st.markdown("""
<style>
    .stApp { background-color: #ffffff; color: #333333; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
    .stSidebar { background-color: #f8f9fa; border-right: 1px solid #e9ecef; }
    h1, h2, h3 { color: #000000; font-weight: 600; margin-top: 20px; }
    
    /* 隐藏默认元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}

    /* 登录框样式 */
    .login-container {
        max-width: 400px;
        margin: 100px auto;
        padding: 40px;
        border: 1px solid #eee;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        text-align: center;
    }
    
    /* 链接样式 */
    a { color: #000000; text-decoration: underline; font-weight: 500; }
    
    /* 打印隐藏 */
    @media print {
        .stSidebar, .no-print { display: none !important; }
        .main-block { margin-left: 0 !important; }
    }
</style>
""", unsafe_allow_html=True)

# --- 2. 用户登录系统 ---

# 初始化 Session State
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""

# 简单的用户数据库（实际生产环境应使用数据库或 .streamlit/secrets.toml）
USERS = {
    "admin": "admin123",  # 演示账号
    "editor": "editor123"
}

def login_page():
    """渲染登录页面"""
    st.markdown("<div class='login-container'>", unsafe_allow_html=True)
    st.title("创作者月报系统 📊")
    st.write("请登录以继续")
    
    with st.form("login_form"):
        username = st.text_input("用户名", placeholder="请输入 admin")
        password = st.text_input("密码", type="password", placeholder="请输入 admin123")
        submit = st.form_submit_button("登录")
        
        if submit:
            if username in USERS and USERS[username] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun() # 刷新页面进入主系统
            else:
                st.error("用户名或密码错误")
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# 检查登录状态
if not st.session_state.logged_in:
    login_page()

# --- 3. 数据处理逻辑 ---

# 字段映射配置
FIELD_MAPPING = {
    "author_name": "作者昵称",
    "author_url": "主页链接",
    "month": "报告月份",
    "video_count": "发布数量",
    "play_count": "总播放量",
    "like_count": "总点赞量",
    "comment_count": "评论数",
    "share_count": "分享数",
    "revenue": "预估收益"
}

def get_sample_data():
    """生成示例数据，用于预览报告格式"""
    data = [
        {
            "author_name": "示例创作者A",
            "author_url": "https://example.com/user/a",
            "month": "2026-03",
            "video_count": 12,
            "play_count": 105000,
            "like_count": 8500,
            "comment_count": 420,
            "share_count": 150,
            "revenue": 1250.50
        },
        {
            "author_name": "示例创作者B",
            "author_url": "https://example.com/user/b",
            "month": "2026-03",
            "video_count": 5,
            "play_count": 45000,
            "like_count": 3200,
            "comment_count": 180,
            "share_count": 65,
            "revenue": 580.00
        }
    ]
    return pd.DataFrame(data)

def process_uploaded_file(uploaded_file):
    """处理上传的JSON文件"""
    try:
        data = json.load(uploaded_file)
        # 假设数据可能是列表，也可能是字典包含'list'键
        if isinstance(data, dict) and 'data' in data:
            df = pd.DataFrame(data['data'])
        else:
            df = pd.DataFrame(data)
        return df
    except Exception as e:
        st.error(f"文件解析错误: {e}")
        return None

# --- 4. 侧边栏 ---
with st.sidebar:
    st.write(f"👤 当前用户: **{st.session_state.username}**")
    if st.button("退出登录"):
        st.session_state.logged_in = False
        st.rerun()
    
    st.divider()
    st.header("数据管理")
    
    # 核心改进：示例数据按钮
    if st.button("👉 加载示例数据", use_container_width=True):
        st.session_state.df = get_sample_data()
        st.session_state.data_source = "示例数据"
        st.success("已加载示例数据！")
    
    # 文件上传
    uploaded_file = st.file_uploader("上传 JSON 数据文件", type=["json"], label_visibility="collapsed")
    if uploaded_file is not None:
        df = process_uploaded_file(uploaded_file)
        if df is not None:
            st.session_state.df = df
            st.session_state.data_source = uploaded_file.name
            
    st.divider()
    st.header("字段映射")
    # 简化映射配置界面（实际可用JSON配置）
    st.info("当前使用默认字段映射。如需修改，请编辑代码中的 FIELD_MAPPING。")

# --- 5. 主界面渲染 ---

st.title("📊 创作者运营月报")

# 检查是否有数据
if 'df' not in st.session_state:
    st.info("👆 请在左侧点击 '加载示例数据' 预览报告，或上传您的 JSON 文件。")
    st.stop()

df = st.session_state.df
source = st.session_state.get('data_source', '未知')

st.caption(f"数据来源: {source} | 数据条数: {len(df)}")

# 显示核心指标
cols = st.columns(4)
with cols[0]:
    st.metric("总播放量", f"{df['play_count'].sum():,}")
with cols[1]:
    st.metric("总互动量", f"{df[['like_count', 'comment_count', 'share_count']].sum().sum():,}")
with cols[2]:
    st.metric("总收益", f"¥{df['revenue'].sum():,.2f}")
with cols[3]:
    st.metric("活跃作者数", len(df))

st.divider()

# 数据表格展示
st.subheader("详细数据")
# 使用 dataframe 支持排序和交互
st.dataframe(
    df, 
    use_container_width=True,
    column_config={
        "author_url": st.column_config.LinkColumn("主页链接"),
        "revenue": st.column_config.NumberColumn("收益", format="¥ %.2f")
    }
)

# 简单的图表展示
st.subheader("播放量分布")
if not df.empty:
    st.bar_chart(df.set_index('author_name')['play_count'])

# 底部操作区
st.divider()
st.markdown("### 导出与打印")
st.markdown("💡 **提示**：如需导出PDF，请使用浏览器打印功能 (Ctrl+P / Cmd+P)，系统已自动优化打印样式。")

# 导出CSV按钮
csv = df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="下载 CSV 数据",
    data=csv,
    file_name=f'monthly_report_{datetime.now().strftime("%Y%m%d")}.csv',
    mime='text/csv'
)

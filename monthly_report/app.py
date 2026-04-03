import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime
import uuid
import streamlit.components.v1 as components

# --- 1. 基础配置与样式 ---
st.set_page_config(
    page_title="创作者运营月报系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 注入极简风格CSS + 锚点偏移修正
st.markdown("""
<style>
    /* 极简配色 */
    .stApp { background-color: #ffffff; color: #333333; }
    .stSidebar { background-color: #f8f9fa; }
    h1, h2, h3 { color: #000000; font-weight: 600; }
    
    /* 去除默认的Streamlit元素装饰 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 锚点偏移修正，防止导航跳转后被顶部遮挡 */
    .report-content {
        padding-top: 20px;
        margin-bottom: 40px;
        border-bottom: 1px solid #eee;
    }
    
    /* 链接样式 */
    a { color: #000000; text-decoration: underline; font-weight: 500; }
    
    /* 导航菜单样式 */
    .nav-menu a {
        display: block;
        padding: 10px 15px;
        color: #333;
        text-decoration: none;
        border-radius: 4px;
        margin-bottom: 5px;
    }
    .nav-menu a:hover { background-color: #e9ecef; }
</style>
""", unsafe_allow_html=True)

# --- 2. 字段映射配置 (关键：解决解析歧义问题) ---
# 用户上传的JSON字段可能各不相同，这里定义映射规则，Agent只需修改此处
FIELD_MAPPING = {
    "author_name": "author_name",       # 作者昵称
    "author_url": "author_url",         # 作者主页链接
    "video_play_count": "video_play_count", # 视频播放量字段名
    "live_play_count": "live_play_count",   # 直播播放量字段名(如果有的话)
    "fans_count": "fans_count",         # 粉丝数
    "likes_count": "likes_count",       # 点赞数
    "date": "date"                      # 日期字段
}

# --- 3. 数据存储逻辑 ---
DATA_FILE = "report_db.json"

def init_db():
    if not os.path.exists(DATA_FILE):
        default_data = {"users": {}, "reports": {}}
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(default_data, f)

def load_db():
    init_db()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- 4. 页面组件 ---

def page_login():
    """极简登录/注册页"""
    st.title("👋 欢迎使用创作者月报系统")
    st.write("请输入您的用户名以进入个人中心（首次输入即自动创建）")
    
    with st.form("login_form"):
        username = st.text_input("用户名", max_chars=20)
        submit = st.form_submit_button("进入系统")
        
        if submit and username:
            st.session_state["user"] = username
            # 初始化用户数据
            db = load_db()
            if username not in db["users"]:
                db["users"][username] = {"reports": []}
                save_db(db)
            st.rerun()

def page_dashboard():
    """个人中心"""
    st.title(f"🏠 个人中心")
    st.caption(f"当前用户：{st.session_state.user}")
    
    db = load_db()
    user_reports = db["users"].get(st.session_state.user, {}).get("reports", [])
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("➕ 创建新月报", use_container_width=True):
            st.session_state["creating"] = True
            st.rerun()
    
    st.markdown("---")
    st.subheader("历史报告")
    
    if not user_reports:
        st.info("暂无历史报告，请点击上方按钮创建。")
    else:
        for rid in user_reports:
            report = db["reports"].get(rid)
            if report:
                c1, c2 = st.columns([4, 1])
                with c1:
                    # 生成分享链接
                    share_url = f"?report_id={rid}"
                    st.markdown(f"""
                    **{report.get('title', '未命名报告')}**  
                    <small>创建时间: {report.get('create_time', 'N/A')}</small>  
                    <small>分享链接: <a href="{share_url}" target="_blank">点击查看</a></small>
                    """, unsafe_allow_html=True)
                with c2:
                    if st.button("查看详情", key=f"view_{rid}"):
                        st.session_state["viewing_report"] = rid
                        st.session_state["page_mode"] = "view"
                        st.rerun()
                st.markdown("---")

def page_create():
    """创建新报告 - 仅上传"""
    st.title("📝 创建新月报")
    
    if st.button("← 返回个人中心"):
        if "creating" in st.session_state: del st.session_state["creating"]
        st.rerun()

    st.info("请上传您的原始数据 JSON 文件。后端将自动解析字段并生成报告。")
    
    uploaded_file = st.file_uploader("上传 JSON 文件", type=["json"], label_visibility="collapsed")
    
    if uploaded_file:
        try:
            data = json.load(uploaded_file)
            # 生成报告ID
            report_id = str(uuid.uuid4())
            
            # 获取标题，如果没有则用时间
            title = data.get("title", f"{datetime.now().strftime('%Y-%m')} 月度报告")
            
            # 保存报告数据
            db = load_db()
            db["reports"][report_id] = {
                "owner": st.session_state.user,
                "title": title,
                "create_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "data": data
            }
            # 关联到用户
            if report_id not in db["users"][st.session_state.user]["reports"]:
                db["users"][st.session_state.user]["reports"].append(report_id)
            
            save_db(db)
            
            # 跳转到报告页
            st.session_state["viewing_report"] = report_id
            st.session_state["page_mode"] = "edit" # 创建者默认为编辑模式
            if "creating" in st.session_state: del st.session_state["creating"]
            st.rerun()
            
        except Exception as e:
            st.error(f"文件解析错误: {e}")

def render_report(report_id, is_edit_mode=False):
    """核心：报告渲染逻辑"""
    db = load_db()
    report = db["reports"].get(report_id)
    
    if not report:
        st.error("报告不存在")
        return

    data = report.get("data", {})
    title = report.get("title", "报告预览")
    
    # --- 左侧导航栏 ---
    st.sidebar.markdown("---")
    st.sidebar.markdown("<div class='nav-menu'>", unsafe_allow_html=True)
    st.sidebar.markdown(f"<a href='#section_overview'>1. 概览</a>", unsafe_allow_html=True)
    st.sidebar.markdown(f"<a href='#section_content'>2. 内容分析</a>", unsafe_allow_html=True)
    st.sidebar.markdown(f"<a href='#section_fans'>3. 粉丝画像</a>", unsafe_allow_html=True)
    # ... 其他板块导航
    st.sidebar.markdown("</div>", unsafe_allow_html=True)
    
    # --- 顶部工具栏 ---
    col_title, col_btn = st.columns([4, 1])
    with col_title:
        st.title(f"📊 {title}")
    with col_btn:
 导出PDF功能引导
        if st.button("📥 导出 PDF", type="primary"):
            st.info("请使用浏览器打印功能 (Ctrl+P / Cmd+P) 并选择'另存为PDF'以获得最佳排版效果。")
            js = "window.print();"
            components.html(f'<script>{js}</script>', height=0)

    st.markdown(f"<small>报告制作人: {report.get('owner', 'Unknown')} | 数据来源: 上传文件</small>", unsafe_allow_html=True)
    st.markdown("---")

    # --- 板块渲染逻辑 ---
    # 使用 st.container 实现锚点
    
    # 示例：提取数据
    df_data = data.get("metrics", [])
    
    # 1. 概览板块
    with st.container():
        st.markdown('<a name="section_overview"></a>', unsafe_allow_html=True)
        st.header("1. 核心数据概览")
        st.markdown("<small>标准说明：以下数据直接源自上传文件的核心字段</small>", unsafe_allow_html=True)
        
        # 简单处理：假设data是一个列表或者字典
        # 如果用户上传的是列表，转为DataFrame
        if isinstance(df_data, list) and df_data:
            df = pd.DataFrame(df_data)
            
            # 字段清洗 (根据FIELD_MAPPING)
            # 这里假设上传的字段名正好匹配，不匹配则通过rename修正
            # df = df.rename(columns={v:k for k,v in FIELD_MAPPING.items()})
            
            # 可编辑数据表格
            st.subheader("数据明细 (支持双击修改)")
            if is_edit_mode:
                edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="editor1")
                # 监听修改，如果有修改则更新db (这里简化演示，实际需添加回调)
                # if not edited_df.equals(df):
                #     ...save logic...
            else:
                st.dataframe(df, use_container_width=True)
                
            # 可视化
            st.subheader("趋势可视化")
            # 假设包含数值列，自动画图
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            if len(numeric_cols) > 0 and "date" in df.columns:
                st.line_chart(df.set_index("date")[numeric_cols[:2]]) # 简单取前两列
            else:
                st.info("未检测到可可视化的数值型数据")
                
        else:
            st.warning("未检测到有效数据集")

    # 2. 内容分析板块 (演示折叠逻辑)
    with st.container():
        st.markdown('<a name="section_content"></a>', unsafe_allow_html=True)
        st.header("2. 内容分析")
        
        content_data = data.get("content_analysis", None)
        if content_data:
            st.write("内容分析详情...")
            # 这里可以根据具体字段绘图
        else:
            # 无数据折叠内容
            st.info("该板块在上传文件中无对应数据，已自动折叠内容。")

# --- 5. 路由控制 ---

def main():
    # 初始化 Session State
    if "user" not in st.session_state:
        page_login()
    else:
        # 检查URL参数，优先展示分享的报告
        query_params = st.experimental_get_query_params()
        req_report_id = query_params.get("report_id", [None])[0]
        
        if req_report_id:
            # 分享访问模式：只读
            render_report(req_report_id, is_edit_mode=False)
        elif "viewing_report" in st.session_state:
            # 查看自己报告的模式：可编辑
            render_report(st.session_state["viewing_report"], is_edit_mode=True)
        elif "creating" in st.session_state and st.session_state["creating"]:
            page_create()
        else:
            page_dashboard()

if __name__ == "__main__":
    main()

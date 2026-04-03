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

# 极简风格CSS + 锚点偏移修正 + 打印样式
st.markdown("""
<style>
    /* 整体极简风格 */
    .stApp { background-color: #ffffff; color: #333333; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
    .stSidebar { background-color: #f8f9fa; border-right: 1px solid #e9ecef; }
    h1, h2, h3 { color: #000000; font-weight: 600; margin-top: 20px; }
    
    /* 隐藏Streamlit默认元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}

    /* 锚点偏移修正 */
    .report-section {
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
        font-size: 14px;
    }
    .nav-menu a:hover { background-color: #e9ecef; }
    
    /* 打印时隐藏侧边栏和操作按钮 */
    @media print {
        .stSidebar, .no-print { display: none !important; }
        .main-block { margin-left: 0 !important; }
    }
</style>
""", unsafe_allow_html=True)

# --- 2. 字段映射配置 ---
# 明确指定JSON字段与系统字段的对应关系，解决"播放量"等字段歧义问题
FIELD_MAPPING = {
    "author_name": "author_name",       # 作者昵称
    "author_url": "author_url",         # 作者主页链接
    "month": "report_month",            # 报告月份
    # 核心数据指标
    "video_play_count": "video_play_count",       # 视频播放量
    "live_play_count": "live_play_count",         # 直播播放量
    "new_fans_count": "new_fans_count",           # 新增粉丝数
    "total_income": "total_income",               # 总收入
    "live_duration": "live_duration",             # 直播时长
}

# --- 3. 数据与文件管理工具函数 ---

DATA_DIR = "data_storage"

def ensure_dir():
    """确保存储目录存在"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def save_report(username, report_data):
    """保存报告到本地JSON文件"""
    ensure_dir()
    report_id = str(uuid.uuid4())
    file_path = os.path.join(DATA_DIR, f"{report_id}.json")
    
    full_data = {
        "meta": {
            "id": report_id,
            "author": username,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        "content": report_data
    }
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(full_data, f, ensure_ascii=False, indent=4)
    return report_id

def load_report(report_id):
    """读取报告"""
    ensure_dir()
    file_path = os.path.join(DATA_DIR, f"{report_id}.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def get_user_reports(username):
    """获取用户的所有历史报告"""
    ensure_dir()
    reports = []
    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(DATA_DIR, filename), "r", encoding="utf-8") as f:
                data = json.load(f)
                # 仅返回该用户创建的报告
                if data.get("meta", {}).get("author") == username:
                    reports.append(data["meta"])
    # 按时间倒序排列
    reports.sort(key=lambda x: x['created_at'], reverse=True)
    return reports

# --- 4. 页面渲染组件 ---

def render_navigation():
    """渲染左侧导航悬浮栏"""
    st.markdown("### 📑 报告导航")
    st.markdown("---")
    st.markdown("""
    <div class="nav-menu">
        <a href="#section-overview">01 数据概览</a>
        <a href="#section-video">02 视频分析</a>
        <a href="#section-live">03 直播分析</a>
        <a href="#section-fan">04 粉丝画像</a>
        <a href="#section-income">05 收益分析</a>
        <a href="#section-summary">06 总结建议</a>
        <a href="#section-raw">07 原始数据</a>
    </div>
    """, unsafe_allow_html=True)

def render_report_content(data, is_editor=False):
    """渲染报告主体内容"""
    
    # 提取字段数据，如果字段不存在则给默认值
    def get_field(key):
        return data.get(key, 0)

    # --- 板块 1: 数据概览 ---
    st.markdown('<div id="section-overview" class="report-section"></div>', unsafe_allow_html=True)
    st.header("01 数据概览")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("视频播放量", get_field("video_play_count"))
        st.caption("数据标准：累计播放次数")
    with c2:
        st.metric("直播播放量", get_field("live_play_count"))
        st.caption("数据标准：直播间累计观看人次")
    with c3:
        st.metric("新增粉丝", get_field("new_fans_count"))
        st.caption("数据标准：净增粉丝数")
    with c4:
        st.metric("本月总收入", f"¥{get_field('total_income')}")
        st.caption("数据标准：平台结算收入")

    # --- 板块 2: 视频分析 ---
    st.markdown('<div id="section-video" class="report-section"></div>', unsafe_allow_html=True)
    st.header("02 视频分析")
    
    video_data = data.get("video_list", [])
    if video_data:
        df_video = pd.DataFrame(video_data)
        
        # 支持双击编辑
        if is_editor:
            st.write("双击表格单元格可直接修改数据，图表将实时更新：")
            edited_df = st.data_editor(df_video, num_rows="dynamic", use_container_width=True, key="video_editor")
            # 更新数据源以联动图表
            df_video = edited_df
        else:
            st.dataframe(df_video, use_container_width=True)
            
        # 简单可视化
        st.bar_chart(df_video.set_index('title')['play_count'] if 'title' in df_video.columns and 'play_count' in df_video.columns else None)
    else:
        st.info("本月暂无视频数据，已自动折叠详情。")

    # --- 板块 3: 直播分析 ---
    st.markdown('<div id="section-live" class="report-section"></div>', unsafe_allow_html=True)
    st.header("03 直播分析")
    
    live_duration = get_field("live_duration")
    if live_duration > 0:
        st.metric("直播总时长", f"{live_duration} 小时")
        # 这里可以添加更多直播图表
    else:
        st.info("本月暂无直播数据。")

    # --- 板块 4: 粉丝画像 (模拟折叠) ---
    st.markdown('<div id="section-fan" class="report-section"></div>', unsafe_allow_html=True)
    st.header("04 粉丝画像")
    # 如果没有粉丝画像数据，只展示标题和折叠提示
    if not data.get("fan_profile"):
        st.info("暂无详细粉丝画像数据。")
    else:
        st.json(data.get("fan_profile"))

    # --- 板块 5: 收益分析 ---
    st.markdown('<div id="section-income" class="report-section"></div>', unsafe_allow_html=True)
    st.header("05 收益分析")
    st.metric("预估收益", f"¥{get_field('total_income') * 1.1}")

    # --- 板块 6: 总结建议 ---
    st.markdown('<div id="section-summary" class="report-section"></div>', unsafe_allow_html=True)
    st.header("06 总结建议")
    st.write("Agent 将根据上述数据自动生成运营建议...")

    # --- 板块 7: 原始数据 ---
    st.markdown('<div id="section-raw" class="report-section"></div>', unsafe_allow_html=True)
    st.header("07 原始数据查看")
    with st.expander("点击查看上传的原始JSON结构"):
        st.json(data)

def render_pdf_export():
    """导出PDF功能引导"""
    st.markdown("---")
    st.markdown("### 🖨️ 导出报告")
    st.write("点击下方按钮将调用浏览器打印功能，请选择'另存为PDF'以保存报告。")
    # 使用JavaScript触发打印
    st.button("生成 PDF 文件", on_click=lambda: st.markdown('<script>window.print();</script>', unsafe_allow_html=True))

# --- 5. 主程序逻辑 ---

def main():
    # 获取URL参数，判断是查看报告模式还是主页模式
    query_params = st.query_params
    report_id = query_params.get("report_id")
    
    # --- 模式 A: 查看/编辑报告页面 ---
    if report_id:
        report_data = load_report(report_id)
        if report_data:
            # 判断权限：只有作者本人可以编辑
            current_user = st.session_state.get("username", "")
            is_author = (report_data["meta"]["author"] == current_user)
            
            with st.sidebar:
                render_navigation()
                st.markdown("---")
                if is_author:
                    st.success(f"作者: {current_user} (可编辑)")
                else:
                    st.info(f"访客模式 (只读)")
                    st.write(f"作者: {report_data['meta']['author']}")
                
                # 返回主页按钮
                if st.button("返回个人中心"):
                    st.query_params.clear()
                    st.rerun()
            
            # 渲染报告内容
            render_report_content(report_data["content"], is_editor=is_author)
            
            # PDF导出
            render_pdf_export()
        else:
            st.error("报告不存在或已过期")
    
    # --- 模式 B: 个人中心/主页 ---
    else:
        st.title("📊 创作者运营月报系统")
        st.markdown("---")
        
        # 登录/用户名设定
        if "username" not in st.session_state:
            with st.form("login_form"):
                st.write("请输入您的用户名以进入个人中心")
                user = st.text_input("用户名")
                submit = st.form_submit_button("进入系统")
                if submit and user:
                    st.session_state.username = user
                    st.rerun()
        else:
            user = st.session_state.username
            st.sidebar.success(f"当前用户: {user}")
            
            tab1, tab2 = st.tabs(["撰写新报告", "历史报告查询"])
            
            # Tab 1: 撰写新报告 (极简上传)
            with tab1:
                st.header("撰写新报告")
                st.markdown("请上传标准格式的 JSON 数据文件，系统将自动解析并生成报告。")
                
                uploaded_file = st.file_uploader("选择 JSON 文件", type="json", key="file_uploader")
                
                if uploaded_file is not None:
                    try:
                        # 读取并解析JSON
                        input_data = json.load(uploaded_file)
                        
                        # 根据 FIELD_MAPPING 提取数据 (此处仅做简单演示，实际可做复杂清洗)
                        parsed_data = {}
                        for sys_key, json_key in FIELD_MAPPING.items():
                            parsed_data[sys_key] = input_data.get(json_key, 0)
                        
                        # 保留原始详细数据
                        parsed_data["video_list"] = input_data.get("video_list", [])
                        parsed_data["fan_profile"] = input_data.get("fan_profile", {})
                        
                        # 立即保存并生成报告
                        if st.button("生成报告", type="primary"):
                            new_id = save_report(user, parsed_data)
                            st.success("报告生成成功！正在跳转...")
                            # 设置URL参数并刷新
                            st.query_params["report_id"] = new_id
                            st.rerun()
                            
                    except Exception as e:
                        st.error(f"文件解析错误: {e}")

            # Tab 2: 历史报告查询
            with tab2:
                st.header("历史报告查询")
                reports = get_user_reports(user)
                
                if not reports:
                    st.info("您还没有创建过报告。")
                else:
                    for meta in reports:
                        col1, col2, col3 = st.columns([3, 2, 1])
                        with col1:
                            st.write(f"**报告月份**: {meta.get('report_month', '未知')}")
                        with col2:
                            st.write(f"创建时间: {meta['created_at']}")
                        with col3:
                            if st.button("查看", key=meta['id']):
                                st.query_params["report_id"] = meta['id']
                                st.rerun()
                        st.markdown("---")

if __name__ == "__main__":
    main()

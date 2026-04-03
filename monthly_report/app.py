import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

# --- 1. 页面基础配置 ---
st.set_page_config(
    page_title="小喇叭运营月报系统",
    page_icon="📊",
    layout="wide"
)

# --- 2. 配置区 (您提到的差异化数据都在这里修改) ---
# 这里的配置可以被 AI Agent 读取或修改，代码逻辑只需读取这个变量即可
CONFIG = {
    "acu_thresholds": {
        "头部": 10000,  # 示例阈值：大于此数值为头部
        "腰部": 2000    # 示例阈值：大于此数值为腰部
    },
    "data_source_name": "内容营销系统API (示例)",  # 明确注明示例来源
    "standards_note": "注：当前划分标准依据示例配置，具体以 AI Agent 获取的 config 为准。"
}

# --- 3. 数据存储逻辑 (本地JSON存储) ---
# 注意：Streamlit Cloud 部署时，本地文件可能会在服务重启后重置。
# 如需永久存储，后续可教您连接 Google Sheets 或其他简易数据库。
DATA_FILE = "report_data.json"

def load_data():
    """读取本地数据"""
    if not os.path.exists(DATA_FILE):
        # 默认数据结构
        return {"users": {}, "reports": []}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"users": {}, "reports": []}

def save_data(data):
    """保存数据到本地"""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        st.error(f"保存失败: {e}")
        return False

# --- 4. 主程序逻辑 ---

# 初始化数据库
db = load_data()

# 侧边栏导航
st.sidebar.title("导航中心")
page = st.sidebar.radio("选择功能", ["撰写新报告", "历史报告查询"])

# 分隔线
st.sidebar.markdown("---")
st.sidebar.caption("当前时间: " + datetime.now().strftime("%Y-%m-%d"))

# ==========================================
# 页面一：撰写新报告
# ==========================================
if page == "撰写新报告":
    st.header("📝 撰写新报告")
    
    # 展示当前配置信息（供用户参考，对应您要求的"提醒用户划分标准"）
    with st.expander("查看当前数据标准说明", expanded=False):
        st.markdown(f"""
        **数据来源：** `{CONFIG['data_source_name']}`  
        **ACU 划分标准：**
        - **头部作者**：ACU > `{CONFIG['acu_thresholds']['头部']}`
        - **腰部作者**：`{CONFIG['acu_thresholds']['腰部']}` < ACU <= `{CONFIG['acu_thresholds']['头部']}`
        - **尾部作者**：ACU <= `{CONFIG['acu_thresholds']['腰部']}`
        
        *{CONFIG['standards_note']}*
        """)

    # 表单输入
    with st.form("report_form"):
        st.subheader("1. 基本信息")
        col1, col2 = st.columns(2)
        author_name = col1.text_input("填报人姓名", value="")
        report_month = col2.date_input("报告月份", value=datetime.now())
        
        st.subheader("2. 核心数据录入")
        st.info("以下数据字段仅为示例结构，后续会对接 AI Agent 获取实际数据。")
        
        # 示例字段：作者分层
        c1, c2, c3 = st.columns(3)
        head_count = c1.number_input("头部作者数量", min_value=0, value=0)
        waist_count = c2.number_input("腰部作者数量", min_value=0, value=0)
        tail_count = c3.number_input("尾部作者数量", min_value=0, value=0)
        
        # 示例字段：其他指标
        st.text_input("其他备注信息 (选填)", value="")

        # 提交按钮
        submitted = st.form_submit_button("生成并保存报告")
        
        if submitted:
            if not author_name:
                st.warning("请填写填报人姓名！")
            else:
                # 构造报告数据
                new_report = {
                    "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                    "author": author_name,
                    "month": report_month.strftime("%Y-%m"),
                    "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "data": {
                        "head_count": head_count,
                        "waist_count": waist_count,
                        "tail_count": tail_count,
                        "standard_used": CONFIG["acu_thresholds"] # 记录当时使用的标准
                    }
                }
                
                # 存入数据库
                db["reports"].append(new_report)
                if save_data(db):
                    st.success(f"报告已成功保存！ (ID: {new_report['id']})")
                    # 简单的预览
                    st.json(new_report)
                else:
                    st.error("保存失败，请检查权限或联系管理员。")

# ==========================================
# 页面二：历史报告查询
# ==========================================
elif page == "历史报告查询":
    st.header("📂 历史报告查询")
    
    if not db["reports"]:
        st.info("当前没有历史报告数据。")
    else:
        # 将数据转换为表格展示
        df_data = []
        for r in db["reports"]:
            df_data.append({
                "提交时间": r.get("create_time"),
                "填报人": r.get("author"),
                "报告月份": r.get("month"),
                "头部作者数": r["data"].get("head_count"),
                "腰部作者数": r["data"].get("waist_count"),
                "尾部作者数": r["data"].get("tail_count")
            })
        
        df = pd.DataFrame(df_data)
        
        st.subheader("数据总览")
        st.dataframe(df, use_container_width=True)
        
        st.subheader("详细记录")
        for r in reversed(db["reports"]):
            with st.expander(f"报告：{r.get('month')} - {r.get('author')} ({r.get('id')})"):
                st.write(f"**头部作者**: {r['data']['head_count']}")
                st.write(f"**腰部作者**: {r['data']['waist_count']}")
                st.write(f"**尾部作者**: {r['data']['tail_count']}")
                st.caption(f"当时采用的标准: 头部>{r['data']['standard_used']['头部']}")

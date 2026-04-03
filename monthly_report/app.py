import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

# --- 1. 页面基础配置 ---
st.set_page_config(
    page_title="创作者运营月报系统",
    page_icon="📊",
    layout="wide"
)

# --- 2. 配置区 (方便后续修改标准) ---
# 实际业务中，这些值可以由 AI Agent 读取外部配置文件更新
CONFIG = {
    "acu_thresholds": {
        "头部": 10000,
        "腰部": 2000,
        "尾部": 0
    },
    "data_source_name": "内容营销系统 API" 
}

# --- 3. 数据存储模拟 (模拟本地存储) ---
# 这里的路径在 Streamlit Cloud 上是临时的，重启会消失
# 如果您在本地电脑运行，这个文件会保存在当前目录下
DATA_FILE = "report_history.json"

def load_history():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_history(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- 4. 简单的用户系统 ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

if not st.session_state.logged_in:
    st.title("🔐 请登录")
    # 极简登录：输入用户名即可模拟登录
    user = st.text_input("输入您的用户名")
    if st.button("进入系统"):
        if user:
            st.session_state.logged_in = True
            st.session_state.username = user
            st.rerun()
    st.stop()

# --- 5. 主界面逻辑 ---
user_dir = f"data/{st.session_state.username}"
# 确保用户目录存在 (本地运行有效)
if not os.path.exists(user_dir):
    os.makedirs(user_dir)

st.sidebar.title(f"👤 {st.session_state.username}")
st.sidebar.divider()

# 模拟左侧导航
page = st.sidebar.radio("导航菜单", ["撰写新报告", "历史

"""
品牌资产共享库 
"""

import streamlit as st
import yaml
import json
import base64
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# ========== 页面配置 ==========
st.set_page_config(
    page_title="品牌资产共享库",
    page_icon="🎨",
    layout="wide"
)

# ========== 状态显示 ==========
status_messages = []

# ========== 加载资产 ==========
def load_assets():
    """加载资产，带详细错误信息"""
    global status_messages
    
    # 检查 secrets
    if not hasattr(st, 'secrets'):
        status_messages.append("❌ st.secrets 不存在")
        return []
    
    status_messages.append(f"✅ st.secrets 存在，keys: {list(st.secrets.keys())}")
    
    if 'github' not in st.secrets:
        status_messages.append("❌ 'github' 不在 secrets 中")
        return []
    
    status_messages.append(f"✅ 'github' 存在，keys: {list(st.secrets['github'].keys())}")
    
    # 获取配置
    token = st.secrets['github'].get('token')
    repo = st.secrets['github'].get('repo', 'lingzhi12345-hue/brand-asset-library')
    
    if not token:
        status_messages.append("❌ token 为空")
        return []
    
    status_messages.append(f"✅ token 存在，长度: {len(token)}")
    status_messages.append(f"✅ repo: {repo}")
    
    # 请求 GitHub API
    url = f"https://api.github.com/repos/{repo}/contents/assets.json"
    status_messages.append(f"📡 请求: {url}")
    
    try:
        resp = requests.get(url, headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }, timeout=10)
        
        status_messages.append(f"📡 响应状态码: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            content = base64.b64decode(data['content']).decode('utf-8')
            assets = json.loads(content)
            status_messages.append(f"✅ 成功加载 {len(assets)} 个资产")
            return assets
        else:
            status_messages.append(f"❌ API 错误: {resp.text[:200]}")
            return []
            
    except Exception as e:
        status_messages.append(f"❌ 异常: {str(e)}")
        return []

assets = load_assets()

# ========== 侧边栏 ==========
st.sidebar.title("🎨 品牌资产共享库")
st.sidebar.markdown(f"**当前资产数: {len(assets)}**")

if assets:
    st.sidebar.success("✅ GitHub 同步已启用")
else:
    st.sidebar.warning("⚠️ GitHub 同步未配置")

st.sidebar.markdown("---")

page = st.sidebar.radio(
    "功能导航",
    ["📚 资产浏览", "📊 统计面板"]
)

# ========== 主页面 ==========
if page == "📚 资产浏览":
    st.title("📚 资产浏览")
    
    # 显示状态信息
    st.subheader("📋 调试信息")
    for msg in status_messages:
        st.code(msg)
    
    st.markdown("---")
    st.markdown(f"**共 {len(assets)} 个资产**")
    st.markdown("---")
    
    if assets:
        for asset in assets:
            with st.expander(f"**{asset.get('name', '未命名')}** - {asset.get('author', '未知')}"):
                st.markdown(f"**来源：** {asset.get('source', {}).get('campaign_name', '-')}")
                st.markdown(f"**产品：** {asset.get('source', {}).get('product', '-')}")
                st.markdown(f"**标签：** {' | '.join([f'`{t}`' for t in asset.get('tags', [])])}")

elif page == "📊 统计面板":
    st.title("📊 统计面板")
    st.metric("总资产数", len(assets))

# ========== 页脚 ==========
st.markdown("---")
st.markdown("<div style='text-align: center; color: #666;'>品牌资产共享库 v1.3 调试版</div>", unsafe_allow_html=True)

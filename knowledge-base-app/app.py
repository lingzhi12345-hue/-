"""
知识库查询页面
运行方式: streamlit run app.py
"""

import streamlit as st
import requests
import json
import os
from datetime import datetime

# 配置
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
REPO_OWNER = "lingzhi12345-hue"
REPO_NAME = "knowledge-base"

# 页面配置
st.set_page_config(
    page_title="知识库查询",
    page_icon="📚",
    layout="wide"
)

# 样式
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .doc-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
        border-left: 4px solid #1f77b4;
    }
    .tag {
        background-color: #e7f3ff;
        color: #1f77b4;
        padding: 0.2rem 0.5rem;
        border-radius: 5px;
        margin-right: 0.3rem;
        font-size: 0.8rem;
    }
    . lobster-tip {
        background-color: #fff3cd;
        border-radius: 10px;
        padding: 1rem;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# GitHub API 调用
@st.cache_data(ttl=300)
def get_index():
    """获取知识库索引"""
    if not GITHUB_TOKEN:
        return None
    
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/index.json"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.raw"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return json.loads(response.text)
    except:
        pass
    return None

@st.cache_data(ttl=300)
def get_document_content(path):
    """获取文档内容"""
    if not GITHUB_TOKEN:
        return None
    
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.raw"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.text
    except:
        pass
    return None

def search_in_content(content, keywords):
    """在内容中搜索关键词"""
    if not content:
        return []
    
    results = []
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        matched_keywords = [kw for kw in keywords if kw.lower() in line_lower]
        
        if matched_keywords:
            # 获取上下文
            start = max(0, i - 2)
            end = min(len(lines), i + 3)
            context = '\n'.join(lines[start:end])
            
            results.append({
                "line_number": i + 1,
                "matched_keywords": matched_keywords,
                "context": context
            })
    
    return results[:20]  # 最多返回20条

# 主界面
st.markdown('<p class="main-header">📚 内推广州知识库</p>', unsafe_allow_html=True)

# 检查 Token
if not GITHUB_TOKEN:
    st.warning("⚠️ 未配置 GitHub Token，部分功能受限。请联系管理员获取访问权限。")
    st.info("""
    **如何配置 GitHub Token：**
    1. 联系管理员获取 Token
    2. 在运行环境中设置环境变量：`export GITHUB_TOKEN=你的token`
    3. 重新启动应用
    """)
else:
    st.success("✅ 已连接知识库")

# 获取索引
index_data = get_index()

if not index_data:
    st.error("❌ 无法获取知识库索引")
    st.stop()

# 侧边栏 - 使用指南
with st.sidebar:
    st.header("📖 使用指南")
    st.markdown("""
    ### 页面搜索
    在上方搜索框输入关键词，可搜索知识库中的所有文档。
    
    ### 龙虾查询（更精准）
    在 POPO 中发送指令给龙虾，如：
    
    ```
    查询知识库 KOL合作的CPM标准
    ```
    
    龙虾会自动检索并返回精准答案，同时提供原文链接。
    
    ---
    
    **为什么推荐龙虾查询？**
    - 理解自然语言，无需精确匹配
    - 直接给出答案，不是片段
    - 自动关联原文位置
    
    ---
    
    **联系管理员**
    - 知识库维护：罗南
    - GitHub：lingzhi12345-hue
    """)

# 显示知识库概览
st.subheader("📋 知识库概览")

documents = index_data.get("documents", [])

for doc in documents:
    with st.container():
        st.markdown('<div class="doc-card">', unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"**{doc['name']}**")
            st.caption(doc.get("summary", ""))
            
            # 标签
            tags_html = "".join([f'<span class="tag">{tag}</span>' for tag in doc.get("tags", [])])
            st.markdown(tags_html, unsafe_allow_html=True)
        
        with col2:
            st.caption(f"📁 {doc.get('category', '')}")
            st.caption(f"📅 {doc.get('update_date', '')}")
            
            # POPO 文档链接
            if doc.get("popo_url"):
                st.link_button("📄 查看原文", doc["popo_url"])
        
        st.markdown('</div>', unsafe_allow_html=True)

# 搜索功能
st.divider()
st.subheader("🔍 搜索知识库")

search_query = st.text_input(
    "输入关键词搜索",
    placeholder="例如：CPM标准、KOL合作、创作者约稿..."
)

if search_query:
    keywords = [kw.strip() for kw in search_query.split() if kw.strip()]
    
    if not keywords:
        st.warning("请输入搜索关键词")
    else:
        st.info(f"搜索关键词：{', '.join(keywords)}")
        
        # 搜索结果
        total_results = 0
        
        for doc in documents:
            content = get_document_content(doc["github_path"])
            results = search_in_content(content, keywords)
            
            if results:
                total_results += len(results)
                
                with st.expander(f"📄 {doc['name']} ({len(results)} 条匹配)"):
                    for r in results:
                        st.markdown(f"**第 {r['line_number']} 行** (匹配: {', '.join(r['matched_keywords'])})")
                        st.code(r["context"], language="markdown")
                        st.divider()
        
        if total_results == 0:
            st.warning("未找到匹配结果，请尝试其他关键词")
        else:
            st.success(f"共找到 {total_results} 条匹配结果")

# 页脚
st.caption(f"知识库版本 {index_data.get('version', '1.0')} | 更新时间：{index_data.get('updated', '')}")

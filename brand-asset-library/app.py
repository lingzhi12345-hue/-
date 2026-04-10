"""
品牌资产共享库 - Streamlit 应用 v2.1
支持多用户共创、按产品分类、多种资产类型、自由上传
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
    page_title="内推广州*品牌资产库",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== 自定义样式 ==========
st.markdown("""
<style>
    .tag-badge {
        display: inline-block;
        background: #e3f2fd;
        color: #1976d2;
        padding: 2px 8px;
        border-radius: 12px;
        margin: 2px;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

# ========== 预设资产类型 ==========
DEFAULT_ASSET_TYPES = [
    "爆款内容",
    "达人筛选",
    "节点策略",
    "创意模板",
    "平台合作",
    "小喇叭",
    "其他"
]

# ========== GitHub 配置 ==========
def get_github_config():
    """获取 GitHub 配置"""
    if hasattr(st, 'secrets') and 'github' in st.secrets:
        return {
            'token': st.secrets['github'].get('token'),
            'repo': st.secrets['github'].get('repo', 'lingzhi12345-hue/brand-asset-library'),
            'branch': st.secrets['github'].get('branch', 'main')
        }
    return None

# ========== 资产加载 ==========
@st.cache_data(ttl=300)
def load_assets_from_github():
    """从 GitHub 加载资产"""
    config = get_github_config()
    if not config or not config['token']:
        return []
    
    try:
        url = f"https://api.github.com/repos/{config['repo']}/contents/assets.json"
        resp = requests.get(url, headers={
            "Authorization": f"token {config['token']}",
            "Accept": "application/vnd.github.v3+json"
        }, timeout=10)
        
        if resp.status_code == 200:
            content = base64.b64decode(resp.json()['content']).decode('utf-8')
            return json.loads(content)
    except:
        pass
    return []

@st.cache_data(ttl=300)
def load_assets_local():
    """本地加载（开发环境）"""
    assets_dir = Path("assets")
    if not assets_dir.exists():
        return []
    assets = []
    for f in assets_dir.glob("*.yaml"):
        with open(f, 'r', encoding='utf-8') as fp:
            asset = yaml.safe_load(fp)
            if asset:
                assets.append(asset)
    return assets

def get_assets():
    """获取资产列表"""
    assets = load_assets_from_github()
    if not assets:
        assets = load_assets_local()
    assets.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return assets

# ========== 统计函数 ==========
def get_statistics(assets: List[Dict]) -> Dict:
    """计算统计数据"""
    stats = {
        'total': len(assets),
        'by_product': {},
        'by_type': {},
        'by_author': {},
        'by_tag': {}
    }
    
    for asset in assets:
        product = asset.get('source', {}).get('product', '未分类')
        stats['by_product'][product] = stats['by_product'].get(product, 0) + 1
        
        asset_type = asset.get('asset_type', '未分类')
        stats['by_type'][asset_type] = stats['by_type'].get(asset_type, 0) + 1
        
        author = asset.get('author', '未知')
        stats['by_author'][author] = stats['by_author'].get(author, 0) + 1
        
        for tag in asset.get('tags', []):
            stats['by_tag'][tag] = stats['by_tag'].get(tag, 0) + 1
    
    return stats

# ========== 获取所有资产类型（含自定义） ==========
def get_all_asset_types(assets: List[Dict]) -> List[str]:
    """获取所有资产类型，包括预设和用户自定义的"""
    types_set = set(DEFAULT_ASSET_TYPES)
    for asset in assets:
        atype = asset.get('asset_type')
        if atype and atype not in types_set:
            types_set.add(atype)
    return list(types_set)

# ========== 主程序 ==========
assets = get_assets()
stats = get_statistics(assets)
all_asset_types = get_all_asset_types(assets)
github_config = get_github_config()

# ========== 侧边栏 ==========
st.sidebar.title("🎨 品牌资产共享库")
st.sidebar.markdown(f"**资产总数: {len(assets)}**")

if github_config:
    st.sidebar.success("✅ GitHub 同步已启用")
else:
    st.sidebar.warning("⚠️ 本地模式")

st.sidebar.markdown("---")

page = st.sidebar.radio(
    "功能导航",
    ["📚 资产浏览", "➕ 上传资产", "🔍 搜索资产", "📊 统计面板", "🔌 API集成", "👥 多人协作"]
)

# ========== 页面：资产浏览 ==========
if page == "📚 资产浏览":
    st.title("📚 资产浏览")
    
    # 筛选器
    col1, col2, col3 = st.columns(3)
    with col1:
        products = ["全部"] + list(stats['by_product'].keys())
        filter_product = st.selectbox("产品筛选", products)
    with col2:
        asset_types = ["全部"] + all_asset_types
        filter_type = st.selectbox("资产类型", asset_types)
    with col3:
        authors = ["全部"] + list(stats['by_author'].keys())
        filter_author = st.selectbox("作者筛选", authors)
    
    # 应用筛选
    filtered = assets
    if filter_product != "全部":
        filtered = [a for a in filtered if a.get('source', {}).get('product') == filter_product]
    if filter_type != "全部":
        filtered = [a for a in filtered if a.get('asset_type', '未分类') == filter_type]
    if filter_author != "全部":
        filtered = [a for a in filtered if a.get('author') == filter_author]
    
    st.markdown(f"**共 {len(filtered)} 个资产**")
    st.markdown("---")
    
    if not filtered:
        st.info("暂无匹配的资产")
    else:
        for asset in filtered:
            name = asset.get('name', '未命名')
            author = asset.get('author', '未知')
            product = asset.get('source', {}).get('product', '-')
            atype = asset.get('asset_type', '未分类')
            
            with st.expander(f"**{name}** - {author} ({product} | {atype})"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**来源：** {asset.get('source', {}).get('campaign_name', '-')}")
                    st.markdown(f"**创建时间：** {asset.get('created_at', '-')}")
                    
                    st.markdown("**标签：**")
                    tags_html = "".join([f'<span class="tag-badge">{t}</span>' for t in asset.get('tags', [])])
                    st.markdown(tags_html, unsafe_allow_html=True)
                    
                    # 显示备注
                    if asset.get('notes'):
                        st.markdown(f"**备注：** {asset.get('notes')}")
                    
                    # 显示原始内容（折叠）
                    with st.expander("📄 查看完整数据"):
                        st.code(yaml.dump(asset, allow_unicode=True, sort_keys=False), language="yaml")
                
                with col2:
                    yaml_str = yaml.dump(asset, allow_unicode=True, sort_keys=False)
                    st.download_button(
                        label="📥 下载YAML",
                        data=yaml_str,
                        file_name=f"{name}.yaml",
                        mime="text/yaml",
                        key=f"dl_{asset.get('asset_id', name)}"
                    )

# ========== 页面：上传资产 ==========
elif page == "➕ 上传资产":
    st.title("➕ 上传资产")
    
    tab1, tab2 = st.tabs(["📁 上传文件", "✏️ 快速创建"])
    
    with tab1:
        st.markdown("""
        ### 上传 YAML 文件
        
        支持自由格式的 YAML 文件，只需包含以下基础字段：
        - `name`: 资产名称
        - `author`: 上传者
        - `source.product`: 所属产品
        - `tags`: 标签列表
        - `asset_type`: 资产类型（可选，默认"其他"）
        
        其他字段可根据实际需要自由添加。
        """)
        
        uploaded_file = st.file_uploader("选择 YAML 文件", type=['yaml', 'yml'])
        
        if uploaded_file:
            try:
                content = uploaded_file.read().decode('utf-8')
                asset_data = yaml.safe_load(content)
                
                st.success("✅ 文件解析成功！")
                st.markdown("**预览：**")
                st.yaml(asset_data)
                
                # 下载按钮
                yaml_str = yaml.dump(asset_data, allow_unicode=True, sort_keys=False)
                st.download_button(
                    label="📥 下载格式化的 YAML",
                    data=yaml_str,
                    file_name=f"ASSET-{datetime.now().strftime('%Y%m%d')}-{asset_data.get('name', 'new')}.yaml",
                    mime="text/yaml"
                )
                
                st.info("💡 下载后发送给管理员或通过 OpenClaw Agent 上传到资产库")
                
            except Exception as e:
                st.error(f"文件解析失败: {str(e)}")
        
        st.markdown("---")
        st.markdown("### 📋 YAML 模板示例")
        st.code("""
name: 暗黑风+神圣感
author: yourname@corp.netease.com
asset_type: 爆款内容
source:
  campaign_name: 阴阳师3月SP蚀月吸血姬
  campaign_id: "273292"
  product: 阴阳师
  period: "2026年3月"
tags:
  - 暗黑风
  - 神圣感
  - COS变装

# 以下内容根据资产类型自由定义
character_traits:
  - 兼具黑暗与光明双重属性
  - 有救赎/牺牲背景故事

content_structure:
  - phase: 开场
    duration: "0-5秒"
    purpose: 建立反差

top_cases:
  - creator: icycream
    platform: 抖音
    views: 6490000
    cpm: 8.3

notes: 适用于有翅膀/羽毛/荆棘等元素的角色
""", language="yaml")
    
    with tab2:
        st.markdown("### 快速创建资产")
        
        with st.form("quick_create"):
            col1, col2 = st.columns(2)
            with col1:
                asset_name = st.text_input("资产名称 *", placeholder="如：暗黑风+神圣感")
                author = st.text_input("上传者 *", placeholder="邮箱或姓名")
            with col2:
                product = st.text_input("产品 *", placeholder="如：阴阳师")
                # 支持自定义资产类型
                preset_type = st.selectbox("资产类型", DEFAULT_ASSET_TYPES)
                custom_type = st.text_input("自定义类型（不选预设时填写）", placeholder="留空则使用预设")
            
            campaign_name = st.text_input("活动名称", placeholder="如：阴阳师3月SP蚀月吸血姬")
            tags_input = st.text_input("标签（逗号分隔）", placeholder="暗黑风, 神圣感")
            
            # 自由内容
            custom_content = st.text_area(
                "其他内容（YAML格式）",
                placeholder="character_traits:\n  - 特征1\n  - 特征2\n\nnotes: 备注信息",
                height=150
            )
            
            submitted = st.form_submit_button("✅ 生成资产")
            
            if submitted:
                if not all([asset_name, author, product]):
                    st.error("请填写必填项（带 * 的字段）")
                else:
                    asset_data = {
                        "name": asset_name,
                        "author": author,
                        "asset_type": custom_type if custom_type else preset_type,
                        "source": {
                            "campaign_name": campaign_name,
                            "product": product
                        },
                        "tags": [t.strip() for t in tags_input.split(',') if t.strip()],
                        "created_at": datetime.now().strftime('%Y-%m-%d')
                    }
                    
                    # 合并自定义内容
                    if custom_content:
                        try:
                            custom_data = yaml.safe_load(custom_content)
                            if isinstance(custom_data, dict):
                                asset_data.update(custom_data)
                        except:
                            pass
                    
                    yaml_str = yaml.dump(asset_data, allow_unicode=True, sort_keys=False)
                    st.success("✅ 资产生成成功！")
                    st.code(yaml_str, language="yaml")
                    
                    st.download_button(
                        label="📥 下载 YAML 文件",
                        data=yaml_str,
                        file_name=f"ASSET-{datetime.now().strftime('%Y%m%d')}-{asset_name}.yaml",
                        mime="text/yaml"
                    )

# ========== 页面：搜索资产 ==========
elif page == "🔍 搜索资产":
    st.title("🔍 搜索资产")
    
    search_type = st.radio("搜索方式", ["关键词搜索", "标签匹配", "按产品筛选"])
    
    if search_type == "关键词搜索":
        keyword = st.text_input("输入关键词", placeholder="如：暗黑、阴阳师、达人筛选")
        if keyword:
            results = [a for a in assets if 
                      keyword.lower() in a.get('name', '').lower() or
                      keyword.lower() in str(a.get('tags', [])).lower() or
                      keyword.lower() in a.get('source', {}).get('product', '').lower() or
                      keyword.lower() in str(a).lower()]
            st.markdown(f"**找到 {len(results)} 个结果**")
            for asset in results:
                st.markdown(f"- **{asset.get('name')}** ({asset.get('source', {}).get('product', '-')})")
    
    elif search_type == "标签匹配":
        all_tags = list(stats['by_tag'].keys())
        selected_tags = st.multiselect("选择标签", all_tags)
        if selected_tags:
            results = [a for a in assets if set(selected_tags) & set(a.get('tags', []))]
            st.markdown(f"**找到 {len(results)} 个结果**")
            for asset in results:
                common_tags = set(selected_tags) & set(asset.get('tags', []))
                st.markdown(f"- **{asset.get('name')}** ({asset.get('source', {}).get('product', '-')}) - 匹配标签: {', '.join(common_tags)}")
    
    else:
        products = list(stats['by_product'].keys())
        selected_product = st.selectbox("选择产品", products)
        if selected_product:
            results = [a for a in assets if a.get('source', {}).get('product') == selected_product]
            st.markdown(f"**找到 {len(results)} 个结果**")
            for asset in results:
                st.markdown(f"- **{asset.get('name')}** ({asset.get('asset_type', '-')})")

# ========== 页面：统计面板 ==========
elif page == "📊 统计面板":
    st.title("📊 统计面板")
    
    # 总览卡片
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("总资产数", stats['total'])
    with col2:
        st.metric("产品数", len(stats['by_product']))
    with col3:
        st.metric("贡献者", len(stats['by_author']))
    with col4:
        st.metric("资产类型", len(stats['by_type']))
    
    st.markdown("---")
    
    # 按产品分布
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📦 按产品分布")
        if stats['by_product']:
            for product, count in sorted(stats['by_product'].items(), key=lambda x: -x[1]):
                st.markdown(f"- **{product}**: {count} 个资产")
        else:
            st.info("暂无数据")
    
    with col2:
        st.subheader("📋 按资产类型分布")
        if stats['by_type']:
            for atype, count in sorted(stats['by_type'].items(), key=lambda x: -x[1]):
                st.markdown(f"- **{atype}**: {count} 个资产")
        else:
            st.info("暂无数据")
    
    st.markdown("---")
    
    # 按标签和作者
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏷️ 热门标签 TOP 10")
        if stats['by_tag']:
            for tag, count in sorted(stats['by_tag'].items(), key=lambda x: -x[1])[:10]:
                st.markdown(f"- {tag}: {count}")
    
    with col2:
        st.subheader("👥 贡献者排行")
        if stats['by_author']:
            for author, count in sorted(stats['by_author'].items(), key=lambda x: -x[1]):
                st.markdown(f"- {author}: {count} 个资产")

# ========== 页面：API集成 ==========
elif page == "🔌 API集成":
    st.title("🔌 API集成指南")
    
    st.markdown("""
    ### 如何让其他 Agent 接入资产库
    
    品牌资产库通过 GitHub 托管，任何系统都可以通过公开 API 读取数据。
    """)
    
    st.subheader("1️⃣ 获取资产列表（JSON）")
    st.code("""
import requests

# 公开仓库可直接访问（无需 Token）
url = "https://raw.githubusercontent.com/lingzhi12345-hue/brand-asset-library/main/assets.json"
response = requests.get(url)
assets = response.json()

# 按产品筛选
yinshi_assets = [a for a in assets if a.get('source', {}).get('product') == '阴阳师']

# 按标签筛选
dark_style = [a for a in assets if '暗黑风' in a.get('tags', [])]
""", language="python")
    
    st.subheader("2️⃣ 让 OpenClaw Agent 使用资产库")
    st.code("""
# 用户指令示例
"搜索阴阳师的爆款内容资产"
"查看萤火突击相关的达人筛选标准"
"帮我生成一个资产：xxx"
""", language="text")
    
    st.markdown("---")
    st.subheader("📡 API 地址")
    st.info(f"""
    - **资产列表**: `https://raw.githubusercontent.com/lingzhi12345-hue/brand-asset-library/main/assets.json`
    - **单个资产**: `https://raw.githubusercontent.com/lingzhi12345-hue/brand-asset-library/main/assets/{{资产ID}}.yaml`
    """)

# ========== 页面：多人协作 ==========
elif page == "👥 多人协作":
    st.title("👥 多人协作指南")
    
    st.markdown("""
    ### 协作方式
    
    #### 📖 浏览资产（所有人可用）
    
    方式一：直接访问本应用
    - URL: Streamlit Cloud 部署地址
    
    方式二：通过 OpenClaw Agent
    - 指令：`搜索阴阳师的资产`
    - Agent 会自动从 API 获取并返回结果
    
    ---
    
    #### ➕ 上传资产
    
    **方式一：通过 OpenClaw Agent（推荐）**
    
    1. 让 Agent 生成资产 YAML
    2. Agent 自动上传到资产库
    3. 无需 GitHub 权限
    
    **方式二：通过本应用**
    
    1. 访问"上传资产"页面
    2. 填写信息或上传 YAML 文件
    3. 下载生成的 YAML
    4. 发送给管理员上传
    
    ---
    
    ### 🔐 安全说明
    
    - **读取权限**：公开的，任何人都可以读取资产库
    - **写入权限**：仅管理员和授权的 OpenClaw Agent 可以上传
    - **无需分享 GitHub Token**
    
    ---
    
    ### 📋 给同事的配置信息
    
    把以下信息发给同事，让他们的 Agent 配置：
    
    ```
    品牌资产库 API 地址：
    https://raw.githubusercontent.com/lingzhi12345-hue/brand-asset-library/main/assets.json
    
    使用方式：
    1. 让 Agent 读取这个 JSON 文件
    2. 按 source.product 筛选产品
    3. 按 tags 筛选标签
    4. 按 asset_type 筛选资产类型
    
    上传资产：
    发送给 lingzhi12345-hue 或让 OpenClaw Agent 帮忙上传
    ```
    """)
    
    st.markdown("---")
    
    # 生成配置卡片
    st.subheader("📋 配置信息卡片")
    st.code(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    品牌资产共享库 - 配置信息
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 资产库地址：
https://raw.githubusercontent.com/lingzhi12345-hue/brand-asset-library/main/assets.json

📌 使用方法（给 OpenClaw Agent 的指令）：
• "搜索阴阳师的资产"
• "查找爆款内容类型的资产"
• "查看暗黑风标签的资产"

📌 上传资产：
• 让 Agent 生成 YAML 文件
• 发送给管理员或让 Agent 上传

📌 资产类型：
{', '.join(DEFAULT_ASSET_TYPES)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""", language="text")

# ========== 页脚 ==========
st.markdown("---")
st.markdown("<div style='text-align: center; color: #666; padding: 20px;'>品牌资产共享库 v2.1 | 自由上传 | 多人协作</div>", unsafe_allow_html=True)

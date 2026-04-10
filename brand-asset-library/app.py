"""
内推广州组品牌资产库
支持多用户共创、按产品分类、多种资产类型
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
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== 自定义样式 ==========
st.markdown("""
<style>
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .stat-number {
        font-size: 32px;
        font-weight: bold;
    }
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
        # 按产品统计
        product = asset.get('source', {}).get('product', '未分类')
        stats['by_product'][product] = stats['by_product'].get(product, 0) + 1
        
        # 按资产类型统计
        asset_type = asset.get('asset_type', '爆款内容')
        stats['by_type'][asset_type] = stats['by_type'].get(asset_type, 0) + 1
        
        # 按作者统计
        author = asset.get('author', '未知')
        stats['by_author'][author] = stats['by_author'].get(author, 0) + 1
        
        # 按标签统计
        for tag in asset.get('tags', []):
            stats['by_tag'][tag] = stats['by_tag'].get(tag, 0) + 1
    
    return stats

# ========== 主程序 ==========
assets = get_assets()
stats = get_statistics(assets)
github_config = get_github_config()

# ========== 侧边栏 ==========
st.sidebar.title("🎨 内推广州组品牌资产库")
st.sidebar.markdown(f"**资产总数: {len(assets)}**")

if github_config:
    st.sidebar.success("✅ GitHub 同步已启用")
else:
    st.sidebar.warning("⚠️ 本地模式")

st.sidebar.markdown("---")

page = st.sidebar.radio(
    "功能导航",
    ["📚 资产浏览", "➕ 创建资产", "🔍 搜索资产", "📊 统计面板", "🔌 API集成", "👥 多人协作"]
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
        asset_types = ["全部"] + list(stats['by_type'].keys())
        filter_type = st.selectbox("资产类型", asset_types)
    with col3:
        authors = ["全部"] + list(stats['by_author'].keys())
        filter_author = st.selectbox("作者筛选", authors)
    
    # 应用筛选
    filtered = assets
    if filter_product != "全部":
        filtered = [a for a in filtered if a.get('source', {}).get('product') == filter_product]
    if filter_type != "全部":
        filtered = [a for a in filtered if a.get('asset_type', '爆款内容') == filter_type]
    if filter_author != "全部":
        filtered = [a for a in filtered if a.get('author') == filter_author]
    
    st.markdown(f"**共 {len(filtered)} 个资产**")
    st.markdown("---")
    
    if not filtered:
        st.info("暂无匹配的资产")
    else:
        for asset in filtered:
            with st.expander(f"**{asset.get('name', '未命名')}** - {asset.get('author', '未知')} ({asset.get('source', {}).get('product', '-')})"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**资产类型：** {asset.get('asset_type', '爆款内容')}")
                    st.markdown(f"**来源：** {asset.get('source', {}).get('campaign_name', '-')}")
                    st.markdown(f"**创建时间：** {asset.get('created_at', '-')}")
                    
                    st.markdown("**标签：**")
                    tags_html = "".join([f'<span class="tag-badge">{t}</span>' for t in asset.get('tags', [])])
                    st.markdown(tags_html, unsafe_allow_html=True)
                    
                    # 根据资产类型显示不同内容
                    if asset.get('asset_type') == '爆款内容' or not asset.get('asset_type'):
                        st.markdown("**爆款案例：**")
                        for case in asset.get('top_cases', [])[:3]:
                            views = case.get('views', 0)
                            views_str = f"{views:,}" if views else "-"
                            st.markdown(f"- {case.get('creator', '-')} | {case.get('platform', '-')} | 播放 {views_str}")
                    
                    elif asset.get('asset_type') == '达人筛选':
                        st.markdown("**筛选标准：**")
                        criteria = asset.get('selection_criteria', {})
                        if criteria:
                            st.markdown(f"- 粉丝范围：{criteria.get('follower_range', '-')}")
                            st.markdown(f"- CPM 要求：{criteria.get('cpm_requirement', '-')}")
                            st.markdown(f"- 历史表现：{criteria.get('performance', '-')}")
                    
                    elif asset.get('asset_type') == '节点策略':
                        st.markdown("**节点信息：**")
                        node_info = asset.get('node_info', {})
                        if node_info:
                            st.markdown(f"- 节点类型：{node_info.get('node_type', '-')}")
                            st.markdown(f"- 时间范围：{node_info.get('time_range', '-')}")
                            st.markdown(f"- 推荐动作：{node_info.get('recommended_actions', '-')}")
                
                with col2:
                    if st.button("📋 查看详情", key=f"view_{asset.get('asset_id', asset.get('name'))}"):
                        st.session_state['view_asset'] = asset
                    
                    # 下载 YAML
                    yaml_str = yaml.dump(asset, allow_unicode=True, sort_keys=False)
                    st.download_button(
                        label="📥 下载YAML",
                        data=yaml_str,
                        file_name=f"{asset.get('name', 'asset')}.yaml",
                        mime="text/yaml",
                        key=f"dl_{asset.get('asset_id', asset.get('name'))}"
                    )

# ========== 页面：创建资产 ==========
elif page == "➕ 创建资产":
    st.title("➕ 创建资产")
    st.markdown("填写以下信息，创建新的品牌资产")
    
    with st.form("asset_form"):
        st.subheader("📋 基本信息")
        col1, col2 = st.columns(2)
        with col1:
            asset_name = st.text_input("资产名称 *", placeholder="如：暗黑风+神圣感")
            author = st.text_input("上传者 *", placeholder="邮箱或姓名")
            asset_type = st.selectbox("资产类型 *", [
                "爆款内容",
                "达人筛选",
                "节点策略",
                "创意模板",
                "其他"
            ])
        with col2:
            product = st.text_input("产品 *", placeholder="如：阴阳师")
            campaign_name = st.text_input("活动名称 *", placeholder="如：阴阳师3月SP蚀月吸血姬")
            campaign_id = st.text_input("一级单号（可选）", placeholder="如：273292")
        
        st.subheader("🏷️ 标签")
        tags_input = st.text_input("标签（逗号分隔）*", placeholder="暗黑风, 神圣感, COS变装")
        
        # 根据资产类型显示不同字段
        if asset_type == "爆款内容":
            st.subheader("🎬 内容结构")
            structure_note = st.text_area("内容结构说明（每个阶段一行：阶段名|时长|目的）", 
                placeholder="开场|0-5秒|建立反差\n转场|5-8秒|视觉冲击\n呈现|8-20秒|角色展示\n收尾|20-30秒|强化记忆",
                height=100)
            
            st.subheader("🏆 爆款案例")
            cases_note = st.text_area("案例（每行一个：创作者|平台|播放量|CPM）",
                placeholder="icycream|抖音|649万|8.3\n赛博子|抖音|380万|29.7",
                height=80)
        
        elif asset_type == "达人筛选":
            st.subheader("👤 筛选标准")
            col1, col2 = st.columns(2)
            with col1:
                follower_range = st.text_input("粉丝范围", placeholder="1-10万")
                cpm_req = st.text_input("CPM 要求", placeholder="<50")
            with col2:
                platform_pref = st.text_input("平台偏好", placeholder="抖音、B站")
                performance = st.text_input("历史表现要求", placeholder="爆款率>50%")
        
        elif asset_type == "节点策略":
            st.subheader("📅 节点信息")
            col1, col2 = st.columns(2)
            with col1:
                node_type = st.selectbox("节点类型", ["版本更新", "节日活动", "周年庆", "联动活动", "其他"])
                time_range = st.text_input("时间范围", placeholder="2026年3月")
            with col2:
                budget = st.text_input("预算范围", placeholder="50-100万")
                target = st.text_input("目标", placeholder="曝光量5000万")
            
            actions = st.text_area("推荐动作（每行一个）", height=80)
        
        # 通用字段
        st.subheader("📝 备注")
        notes = st.text_area("补充说明", height=60)
        
        st.markdown("---")
        submitted = st.form_submit_button("✅ 创建资产", type="primary")
        
        if submitted:
            if not all([asset_name, author, product, campaign_name, tags_input]):
                st.error("请填写所有必填项（带 * 的字段）")
            else:
                asset_data = {
                    "name": asset_name,
                    "author": author,
                    "asset_type": asset_type,
                    "source": {
                        "campaign_name": campaign_name,
                        "campaign_id": campaign_id,
                        "product": product
                    },
                    "tags": [t.strip() for t in tags_input.split(',') if t.strip()],
                    "notes": notes,
                    "created_at": datetime.now().strftime('%Y-%m-%d'),
                    "version": 1
                }
                
                # 根据资产类型添加特定字段
                if asset_type == "爆款内容":
                    # 解析结构
                    structures = []
                    for line in structure_note.split('\n'):
                        if '|' in line:
                            parts = line.split('|')
                            if len(parts) >= 3:
                                structures.append({
                                    "phase": parts[0].strip(),
                                    "duration": parts[1].strip(),
                                    "purpose": parts[2].strip()
                                })
                    asset_data["content_structure"] = structures
                    
                    # 解析案例
                    cases = []
                    for line in cases_note.split('\n'):
                        if '|' in line:
                            parts = line.split('|')
                            if len(parts) >= 2:
                                views_str = parts[2].replace('万', '0000') if len(parts) > 2 else '0'
                                try:
                                    views = int(float(views_str))
                                except:
                                    views = 0
                                cases.append({
                                    "creator": parts[0].strip(),
                                    "platform": parts[1].strip(),
                                    "views": views,
                                    "cpm": float(parts[3]) if len(parts) > 3 else 0
                                })
                    asset_data["top_cases"] = cases
                
                elif asset_type == "达人筛选":
                    asset_data["selection_criteria"] = {
                        "follower_range": follower_range,
                        "cpm_requirement": cpm_req,
                        "platform_preference": platform_pref,
                        "performance": performance
                    }
                
                elif asset_type == "节点策略":
                    asset_data["node_info"] = {
                        "node_type": node_type,
                        "time_range": time_range,
                        "budget": budget,
                        "target": target,
                        "recommended_actions": [a.strip() for a in actions.split('\n') if a.strip()]
                    }
                
                # 显示生成的 YAML
                yaml_content = yaml.dump(asset_data, allow_unicode=True, sort_keys=False)
                st.success("✅ 资产数据生成成功！")
                st.code(yaml_content, language="yaml")
                
                st.download_button(
                    label="📥 下载 YAML 文件",
                    data=yaml_content,
                    file_name=f"ASSET-{datetime.now().strftime('%Y%m%d')}-new.yaml",
                    mime="text/yaml"
                )
                
                st.info("💡 下载后发送给管理员（或通过 OpenClaw Agent）上传到资产库")

# ========== 页面：搜索资产 ==========
elif page == "🔍 搜索资产":
    st.title("🔍 搜索资产")
    
    search_type = st.radio("搜索方式", ["关键词搜索", "标签匹配"])
    
    if search_type == "关键词搜索":
        keyword = st.text_input("输入关键词", placeholder="如：暗黑、阴阳师、达人筛选")
        if keyword:
            results = [a for a in assets if 
                      keyword.lower() in a.get('name', '').lower() or
                      keyword.lower() in str(a.get('tags', [])).lower() or
                      keyword.lower() in a.get('source', {}).get('product', '').lower()]
            st.markdown(f"**找到 {len(results)} 个结果**")
            for asset in results:
                st.markdown(f"- **{asset.get('name')}** ({asset.get('source', {}).get('product', '-')})")
    
    else:
        all_tags = list(stats['by_tag'].keys())
        selected_tags = st.multiselect("选择标签", all_tags)
        if selected_tags:
            results = [a for a in assets if set(selected_tags) & set(a.get('tags', []))]
            st.markdown(f"**找到 {len(results)} 个结果**")
            for asset in results:
                st.markdown(f"- **{asset.get('name')}** ({asset.get('source', {}).get('product', '-')})")

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
    
    品牌资产库通过 GitHub 托管，任何可以访问 GitHub API 的系统都可以读取数据。
    """)
    
    st.subheader("1️⃣ 获取资产列表（JSON）")
    st.code("""
import requests

# 公开仓库可直接访问
url = "https://raw.githubusercontent.com/lingzhi12345-hue/brand-asset-library/main/assets.json"
response = requests.get(url)
assets = response.json()

# 按产品筛选
yinshi_assets = [a for a in assets if a.get('source', {}).get('product') == '阴阳师']
""", language="python")
    
    st.subheader("2️⃣ 获取单个资产详情")
    st.code("""
# 获取特定资产
asset_name = "暗黑风+神圣感"
url = f"https://raw.githubusercontent.com/lingzhi12345-hue/brand-asset-library/main/assets/{asset_name}.yaml"
response = requests.get(url)
import yaml
asset = yaml.safe_load(response.text)
""", language="python")
    
    st.markdown("---")
    st.subheader("📡 当前 API 地址")
    st.info(f"""
    - 资产列表: `https://raw.githubusercontent.com/lingzhi12345-hue/brand-asset-library/main/assets.json`
    - 单个资产: `https://raw.githubusercontent.com/lingzhi12345-hue/brand-asset-library/main/assets/{{资产名}}.yaml`
    """)
    
    st.markdown("---")
    st.subheader("📤 导出当前资产列表")
    if st.button("导出 assets.json"):
        json_str = json.dumps(assets, ensure_ascii=False, indent=2)
        st.download_button(
            label="下载 assets.json",
            data=json_str,
            file_name="assets.json",
            mime="application/json"
        )

# ========== 页面：多人协作 ==========
elif page == "👥 多人协作":
    st.title("👥 多人协作指南")
    
    st.markdown("""
    ### 如何让团队成员共同使用资产库
    
    品牌资产库支持多人协作，每个团队成员都可以：
    - 📖 **浏览** 所有资产
    - 🔍 **搜索** 按产品、标签筛选
    - ➕ **创建** 新资产（需管理员审核上传）
    
    ---
    
    ### 协作方式
    
    #### 方式一：通过 OpenClaw Agent
    
    团队成员如果有自己的 OpenClaw Agent，可以直接让 Agent：
    1. 读取资产库：`访问品牌资产库，搜索阴阳师相关的资产`
    2. 创建资产：`生成一个资产：xxx，我来审核后上传`
    
    #### 方式二：通过 Streamlit 界面
    
    1. 访问本应用
    2. 创建资产 → 下载 YAML 文件
    3. 发送给管理员上传
    
    #### 方式三：直接 GitHub 协作
    
    有 GitHub 权限的成员可以直接：
    1. Fork 仓库
    2. 添加资产文件到 `assets/` 目录
    3. 提交 PR
    
    ---
    
    ### 按产品分工示例
    
    | 产品 | 负责人 | 可调用资产 |
    |------|--------|-----------|
    | 阴阳师 | 同事A、B | 阴阳师相关资产 |
    | 萤火突击 | 同事A、C | 萤火突击相关资产 |
    | 光遇 | 同事D | 光遇相关资产 |
    
    ---
    """)
    
    st.subheader("🔧 配置新成员")
    st.markdown("""
    如果团队成员有自己的 OpenClaw Agent，需要：
    
    1. **提供 GitHub 仓库地址**：`lingzhi12345-hue/brand-asset-library`
    2. **提供资产 JSON 地址**：`https://raw.githubusercontent.com/lingzhi12345-hue/brand-asset-library/main/assets.json`
    3. **上传权限**：需要 GitHub Token（联系管理员）
    
    Agent 只需知道这些信息，就可以读取资产库内容。
    """)

# ========== 页脚 ==========
st.markdown("---")
st.markdown("<div style='text-align: center; color: #666; padding: 20px;'>品牌资产共享库 v2.0 | 支持多人协作 | 按 product 分类</div>", unsafe_allow_html=True)

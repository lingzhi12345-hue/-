"""
品牌资产共享库 - Streamlit 应用 v3.0
支持产品密码保护、管理员权限控制、重复去重
"""

import streamlit as st
import yaml
import json
import base64
import requests
import hashlib
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
    .tag-badge {
        display: inline-block;
        background: #e3f2fd;
        color: #1976d2;
        padding: 2px 8px;
        border-radius: 12px;
        margin: 2px;
        font-size: 12px;
    }
    .product-nav {
        padding: 8px 12px;
        margin: 4px 0;
        border-radius: 8px;
        cursor: pointer;
    }
    .product-nav:hover {
        background: #f0f0f0;
    }
    .product-nav.active {
        background: #e3f2fd;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ========== 配置信息 ==========
PRODUCT_CONFIG = {
    "梦幻西游电脑版": {
        "password": "wkmt24h3",
        "admin": "lihuixian02@corp.netease.com"
    },
    "梦幻西游手游": {
        "password": "0m2o8z5s",
        "admin": "linxiao03@corp.netease.com"
    },
    "明日之后": {
        "password": "j9n3jd3c",
        "admin": "yuetian01@corp.netease.com"
    },
    "率土之滨": {
        "password": "58ho9atd",
        "admin": "linxiao03@corp.netease.com"
    },
    "光遇": {
        "password": "0mvn84pq",
        "admin": "huanglingzhi02@corp.netease.com"
    },
    "萤火突击": {
        "password": "tkvcnczy",
        "admin": "huangsuixin@corp.netease.com"
    },
    "阴阳师": {
        "password": "6t8ktxlu",
        "admin": "huanglingzhi02@corp.netease.com"
    },
    "世界之外": {
        "password": "vke6xtnk",
        "admin": "huangsuixin@corp.netease.com"
    },
    "实况足球手游": {
        "password": "216ewoxn",
        "admin": "jiangjinpeng02@corp.netease.com"
    },
    "巅峰极速": {
        "password": "u3capmir",
        "admin": "huanglingzhi02@corp.netease.com"
    }
}

# 固定资产类型
ASSET_TYPES = [
    "游戏说明书",
    "KOL投放",
    "平台合作",
    "小喇叭",
    "舆情竞品监测"
]

# 需要管理员审核的类型
ADMIN_REQUIRED_TYPES = ["游戏说明书", "KOL投放", "平台合作", "小喇叭"]

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

def get_assets():
    """获取资产列表"""
    assets = load_assets_from_github()
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

# ========== 密码验证 ==========
def check_product_password(product: str, password: str) -> bool:
    """验证产品密码"""
    if product not in PRODUCT_CONFIG:
        return False
    return PRODUCT_CONFIG[product]["password"] == password

def get_authorized_products() -> List[str]:
    """获取已授权的产品列表"""
    if 'authorized_products' not in st.session_state:
        st.session_state['authorized_products'] = []
    return st.session_state['authorized_products']

def authorize_product(product: str):
    """授权产品访问"""
    if 'authorized_products' not in st.session_state:
        st.session_state['authorized_products'] = []
    if product not in st.session_state['authorized_products']:
        st.session_state['authorized_products'].append(product)

# ========== 重复检测 ==========
def get_asset_hash(asset: Dict) -> str:
    """计算资产内容哈希"""
    # 提取核心字段
    core_fields = {
        'name': asset.get('name', ''),
        'asset_type': asset.get('asset_type', ''),
        'source': asset.get('source', {}),
        'tags': sorted(asset.get('tags', [])),
    }
    content = json.dumps(core_fields, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def check_duplicate(asset: Dict, existing_assets: List[Dict]) -> Optional[Dict]:
    """检查是否重复"""
    new_hash = get_asset_hash(asset)
    for existing in existing_assets:
        if get_asset_hash(existing) == new_hash:
            return existing
    return None

# ========== 权限检查 ==========
def is_product_admin(product: str, user_email: str) -> bool:
    """检查用户是否是产品管理员"""
    if product not in PRODUCT_CONFIG:
        return False
    return PRODUCT_CONFIG[product]["admin"] == user_email

def get_user_email() -> Optional[str]:
    """获取当前用户邮箱（从 session 或输入）"""
    if 'user_email' in st.session_state:
        return st.session_state['user_email']
    return None

# ========== 主程序 ==========
assets = get_assets()
stats = get_statistics(assets)
github_config = get_github_config()

# ========== 侧边栏 ==========
st.sidebar.title("🎨 品牌资产共享库")
st.sidebar.markdown(f"**资产总数: {len(assets)}**")

if github_config:
    st.sidebar.success("✅ GitHub 同步已启用")
else:
    st.sidebar.warning("⚠️ 本地模式")

st.sidebar.markdown("---")

# 用户邮箱输入
if 'user_email' not in st.session_state:
    user_email = st.sidebar.text_input("请输入邮箱以识别身份", placeholder="xxx@corp.netease.com")
    if user_email:
        st.session_state['user_email'] = user_email
        st.rerun()
else:
    st.sidebar.markdown(f"👤 **{st.session_state['user_email']}**")
    if st.sidebar.button("切换账号"):
        del st.session_state['user_email']
        if 'authorized_products' in st.session_state:
            del st.session_state['authorized_products']
        st.rerun()

st.sidebar.markdown("---")

# 产品导航
st.sidebar.markdown("### 📦 产品导航")
authorized_products = get_authorized_products()

for product in PRODUCT_CONFIG.keys():
    col1, col2 = st.sidebar.columns([3, 1])
    with col1:
        if product in authorized_products:
            if st.button(f"✅ {product}", key=f"nav_{product}"):
                st.session_state['current_product'] = product
        else:
            if st.button(f"🔒 {product}", key=f"nav_{product}"):
                st.session_state['current_product'] = product
    
    with col2:
        count = stats['by_product'].get(product, 0)
        st.markdown(f"`{count}`")

st.sidebar.markdown("---")

page = st.sidebar.radio(
    "功能导航",
    ["📚 资产浏览", "🔍 搜索资产", "➕ 上传资产", "📊 统计面板", "👥 权限说明"]
)

# ========== 密码验证弹窗 ==========
if 'current_product' in st.session_state:
    current_product = st.session_state['current_product']
    
    if current_product not in authorized_products:
        st.markdown(f"### 🔒 访问 {current_product} 资产库")
        st.markdown("请输入产品密码以访问该产品的资产。")
        
        password = st.text_input("产品密码", type="password", key=f"pwd_{current_product}")
        
        if st.button("验证密码", key=f"verify_{current_product}"):
            if check_product_password(current_product, password):
                authorize_product(current_product)
                st.success("✅ 密码正确，已授权访问")
                st.rerun()
            else:
                st.error("❌ 密码错误，请重试")
        
        st.markdown("---")
        st.markdown(f"💡 如需获取密码，请联系产品管理员：`{PRODUCT_CONFIG[current_product]['admin']}`")
        st.stop()

# ========== 页面：资产浏览 ==========
if page == "📚 资产浏览":
    st.title("📚 资产浏览")
    
    # 筛选器
    col1, col2, col3 = st.columns(3)
    with col1:
        # 只显示已授权的产品
        product_options = ["全部"] + authorized_products
        filter_product = st.selectbox("产品筛选", product_options)
    with col2:
        asset_types = ["全部"] + ASSET_TYPES
        filter_type = st.selectbox("资产类型", asset_types)
    with col3:
        authors = ["全部"] + list(stats['by_author'].keys())
        filter_author = st.selectbox("作者筛选", authors)
    
    # 应用筛选
    filtered = assets
    if filter_product != "全部":
        # 检查权限
        if filter_product not in authorized_products:
            st.warning(f"⚠️ 您尚未获得 {filter_product} 的访问权限")
            st.stop()
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
                    
                    if asset.get('notes'):
                        st.markdown(f"**备注：** {asset.get('notes')}")
                    
                    # 显示完整数据（折叠）
                    with st.expander("📄 查看完整数据"):
                        st.code(yaml.dump(asset, allow_unicode=True, sort_keys=False), language="yaml")

# ========== 页面：搜索资产 ==========
elif page == "🔍 搜索资产":
    st.title("🔍 搜索资产")
    
    search_type = st.radio("搜索方式", ["关键词搜索", "标签匹配", "按产品筛选"])
    
    if search_type == "关键词搜索":
        keyword = st.text_input("输入关键词", placeholder="如：暗黑、阴阳师、达人筛选")
        if keyword:
            # 只搜索已授权的产品
            results = [a for a in assets if 
                      (a.get('source', {}).get('product') in authorized_products or not authorized_products) and
                      (keyword.lower() in a.get('name', '').lower() or
                      keyword.lower() in str(a.get('tags', [])).lower() or
                      keyword.lower() in a.get('source', {}).get('product', '').lower() or
                      keyword.lower() in str(a).lower())]
            st.markdown(f"**找到 {len(results)} 个结果**")
            for asset in results:
                st.markdown(f"- **{asset.get('name')}** ({asset.get('source', {}).get('product', '-')})")
    
    elif search_type == "标签匹配":
        all_tags = list(stats['by_tag'].keys())
        selected_tags = st.multiselect("选择标签", all_tags)
        if selected_tags:
            results = [a for a in assets if 
                      (a.get('source', {}).get('product') in authorized_products or not authorized_products) and
                      set(selected_tags) & set(a.get('tags', []))]
            st.markdown(f"**找到 {len(results)} 个结果**")
            for asset in results:
                common_tags = set(selected_tags) & set(asset.get('tags', []))
                st.markdown(f"- **{asset.get('name')}** ({asset.get('source', {}).get('product', '-')}) - 匹配标签: {', '.join(common_tags)}")
    
    else:
        # 只显示已授权的产品
        products = [p for p in stats['by_product'].keys() if p in authorized_products]
        selected_product = st.selectbox("选择产品", products)
        if selected_product:
            results = [a for a in assets if a.get('source', {}).get('product') == selected_product]
            st.markdown(f"**找到 {len(results)} 个结果**")
            for asset in results:
                st.markdown(f"- **{asset.get('name')}** ({asset.get('asset_type', '-')})")

# ========== 页面：上传资产 ==========
elif page == "➕ 上传资产":
    st.title("➕ 上传资产")
    
    user_email = get_user_email()
    if not user_email:
        st.warning("⚠️ 请先在侧边栏输入邮箱以识别身份")
        st.stop()
    
    # 选择产品
    product = st.selectbox("选择产品", list(PRODUCT_CONFIG.keys()))
    
    # 检查产品访问权限
    if product not in authorized_products:
        st.warning(f"⚠️ 您尚未获得 {product} 的访问权限，请先在侧边栏验证密码")
        st.stop()
    
    # 选择资产类型
    asset_type = st.selectbox("资产类型", ASSET_TYPES)
    
    # 检查是否需要管理员权限
    is_admin = is_product_admin(product, user_email)
    
    if asset_type in ADMIN_REQUIRED_TYPES and not is_admin:
        st.warning(f"⚠️ **{asset_type}** 类型的资产需要产品管理员上传")
        st.markdown(f"""
        **当前产品管理员：** `{PRODUCT_CONFIG[product]['admin']}`
        
        **操作方式：**
        1. 将资产内容发送给产品管理员
        2. 由管理员审核后上传
        
        您可以继续填写资产信息，生成的 YAML 将发送给管理员。
        """)
        
        admin_mode = False
    else:
        if is_admin:
            st.success(f"✅ 您是 {product} 的管理员，可以直接上传")
        admin_mode = True
    
    # 资产表单
    with st.form("asset_form"):
        st.subheader("📋 基本信息")
        col1, col2 = st.columns(2)
        with col1:
            asset_name = st.text_input("资产名称 *", placeholder="如：暗黑风+神圣感")
        with col2:
            campaign_name = st.text_input("活动名称", placeholder="如：阴阳师3月SP蚀月吸血姬")
        
        tags_input = st.text_input("标签（逗号分隔）", placeholder="暗黑风, 神圣感, COS变装")
        
        # 自由内容
        custom_content = st.text_area(
            "其他内容（YAML格式）",
            placeholder="character_traits:\n  - 特征1\n  - 特征2\n\nnotes: 备注信息",
            height=150
        )
        
        submitted = st.form_submit_button("✅ 生成资产")
        
        if submitted:
            if not asset_name:
                st.error("请填写资产名称")
            else:
                asset_data = {
                    "name": asset_name,
                    "asset_type": asset_type,
                    "author": user_email,
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
                
                # 检查重复
                duplicate = check_duplicate(asset_data, assets)
                if duplicate:
                    st.warning(f"⚠️ 检测到重复资产：**{duplicate.get('name')}** (创建于 {duplicate.get('created_at')})")
                    st.markdown("如需继续上传，请确认内容有所不同。")
                
                yaml_str = yaml.dump(asset_data, allow_unicode=True, sort_keys=False)
                st.success("✅ 资产生成成功！")
                st.code(yaml_str, language="yaml")
                
                if admin_mode:
                    st.markdown("### 📤 上传到资产库")
                    st.info("复制以上 YAML 内容，通过 OpenClaw Agent 或管理员上传到资产库")
                else:
                    st.markdown(f"### 📧 发送给管理员")
                    st.markdown(f"请将以上内容发送给产品管理员：**{PRODUCT_CONFIG[product]['admin']}**")

# ========== 页面：统计面板 ==========
elif page == "📊 统计面板":
    st.title("📊 统计面板")
    
    # 只统计已授权的产品
    visible_assets = [a for a in assets if a.get('source', {}).get('product') in authorized_products or not authorized_products]
    visible_stats = get_statistics(visible_assets)
    
    # 总览卡片
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("总资产数", visible_stats['total'])
    with col2:
        st.metric("产品数", len([p for p in visible_stats['by_product'] if p in authorized_products]))
    with col3:
        st.metric("贡献者", len(visible_stats['by_author']))
    with col4:
        st.metric("资产类型", len(visible_stats['by_type']))
    
    st.markdown("---")
    
    # 按产品分布
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📦 按产品分布")
        if visible_stats['by_product']:
            for product, count in sorted(visible_stats['by_product'].items(), key=lambda x: -x[1]):
                if product in authorized_products:
                    lock_status = "✅" if product in authorized_products else "🔒"
                    st.markdown(f"- {lock_status} **{product}**: {count} 个资产")
        else:
            st.info("暂无数据")
    
    with col2:
        st.subheader("📋 按资产类型分布")
        if visible_stats['by_type']:
            for atype, count in sorted(visible_stats['by_type'].items(), key=lambda x: -x[1]):
                st.markdown(f"- **{atype}**: {count} 个资产")
        else:
            st.info("暂无数据")
    
    st.markdown("---")
    
    # 按标签和作者
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏷️ 热门标签 TOP 10")
        if visible_stats['by_tag']:
            for tag, count in sorted(visible_stats['by_tag'].items(), key=lambda x: -x[1])[:10]:
                st.markdown(f"- {tag}: {count}")
    
    with col2:
        st.subheader("👥 贡献者排行")
        if visible_stats['by_author']:
            for author, count in sorted(visible_stats['by_author'].items(), key=lambda x: -x[1]):
                st.markdown(f"- {author}: {count} 个资产")

# ========== 页面：权限说明 ==========
elif page == "👥 权限说明":
    st.title("👥 权限说明")
    
    st.markdown("""
    ### 访问权限
    
    每个产品都有独立的访问密码，需要输入正确密码才能查看该产品的资产。
    
    ### 管理员权限
    
    每个产品设有管理员，负责审核和上传特定类型的资产。
    
    **需要管理员上传的资产类型：**
    - 游戏说明书
    - KOL投放
    - 平台合作
    - 小喇叭
    
    **无需管理员审核的类型：**
    - 舆情竞品监测（所有用户可直接上传）
    
    ---
    """)
    
    st.subheader("📋 产品管理员列表")
    
    for product, config in PRODUCT_CONFIG.items():
        st.markdown(f"- **{product}**：`{config['admin']}`")

# ========== 页脚 ==========
st.markdown("---")
st.markdown("<div style='text-align: center; color: #666; padding: 20px;'>品牌资产共享库 v3.0 | 产品密码保护 | 管理员权限控制</div>", unsafe_allow_html=True)

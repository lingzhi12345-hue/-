"""
品牌资产共享库 - Streamlit 应用 v3.1
产品隔离 + 管理员验证 + 统计面板公开
"""

import streamlit as st
import yaml
import json
import base64
import requests
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

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
</style>
""", unsafe_allow_html=True)

# ========== 配置信息 ==========

# 超级管理员（可访问所有产品）
SUPER_ADMINS = {
    "guoyajun@corp.netease.com": "gyj123",
    "huanglingzhi02@corp.netease.com": "hlz123"
}

# 产品配置
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

# 需要管理员权限上传的类型
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

# ========== 权限管理 ==========
def is_super_admin(email: str) -> bool:
    """检查是否是超级管理员"""
    return email in SUPER_ADMINS

def verify_super_admin(email: str, password: str) -> bool:
    """验证超级管理员密码"""
    if email not in SUPER_ADMINS:
        return False
    return SUPER_ADMINS[email] == password

def is_product_admin(product: str, email: str) -> bool:
    """检查是否是产品管理员"""
    if product not in PRODUCT_CONFIG:
        return False
    return PRODUCT_CONFIG[product]["admin"] == email

def get_accessible_products(email: str) -> Set[str]:
    """获取用户可访问的产品列表"""
    if 'accessible_products' not in st.session_state:
        st.session_state['accessible_products'] = set()
    
    # 超级管理员可访问所有产品
    if is_super_admin(email):
        return set(PRODUCT_CONFIG.keys())
    
    # 产品管理员可访问自己负责的产品
    admin_products = {p for p, c in PRODUCT_CONFIG.items() if c['admin'] == email}
    
    # 加上已授权的产品
    return admin_products | st.session_state['accessible_products']

def authorize_product(product: str):
    """授权产品访问"""
    if 'accessible_products' not in st.session_state:
        st.session_state['accessible_products'] = set()
    st.session_state['accessible_products'].add(product)

# ========== 重复检测 ==========
def get_asset_hash(asset: Dict) -> str:
    """计算资产内容哈希"""
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

# ========== 主程序 ==========
assets = get_assets()
stats = get_statistics(assets)
github_config = get_github_config()

# ========== 侧边栏 ==========
st.sidebar.title("🎨 内推广州*品牌资产库")
st.sidebar.markdown(f"**资产总数: {len(assets)}**")

if github_config:
    st.sidebar.success("✅ GitHub 同步已启用")
else:
    st.sidebar.warning("⚠️ 本地模式")

st.sidebar.markdown("---")

# 用户身份验证
user_email = None
is_verified_admin = False

if 'user_email' not in st.session_state:
    st.sidebar.markdown("### 🔐 身份验证")
    email_input = st.sidebar.text_input("请输入邮箱", placeholder="xxx@corp.netease.com", key="email_input")
    
    if email_input:
        # 检查是否是管理员邮箱
        if is_super_admin(email_input):
            # 管理员需要输入密码
            admin_pwd = st.sidebar.text_input("管理员密码", type="password", key="admin_pwd_input")
            if admin_pwd:
                if verify_super_admin(email_input, admin_pwd):
                    st.session_state['user_email'] = email_input
                    st.session_state['is_verified_admin'] = True
                    st.sidebar.success("✅ 管理员验证成功")
                    st.rerun()
                else:
                    st.sidebar.error("❌ 密码错误")
        else:
            # 普通用户直接登录
            st.session_state['user_email'] = email_input
            st.session_state['is_verified_admin'] = False
            st.rerun()
else:
    user_email = st.session_state['user_email']
    is_verified_admin = st.session_state.get('is_verified_admin', False)
    
    if is_verified_admin:
        st.sidebar.markdown(f"👑 **{user_email}**")
        st.sidebar.markdown("*超级管理员*")
    else:
        st.sidebar.markdown(f"👤 **{user_email}**")
    
    if st.sidebar.button("切换账号"):
        for key in ['user_email', 'is_verified_admin', 'accessible_products', 'current_product']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

st.sidebar.markdown("---")

# 产品导航（根据权限显示）
if user_email:
    accessible = get_accessible_products(user_email)
    
    st.sidebar.markdown("### 📦 产品导航")
    
    for product in PRODUCT_CONFIG.keys():
        count = stats['by_product'].get(product, 0)
        
        if product in accessible:
            # 已授权的产品
            if st.sidebar.button(f"✅ {product} ({count})", key=f"nav_{product}"):
                st.session_state['current_product'] = product
        else:
            # 未授权的产品
            if st.sidebar.button(f"🔒 {product} ({count})", key=f"nav_{product}"):
                st.session_state['current_product'] = product
                st.session_state['need_password'] = True

st.sidebar.markdown("---")

page = st.sidebar.radio(
    "功能导航",
    ["📚 资产浏览", "🔍 搜索资产", "➕ 上传资产", "📊 统计面板", "👥 权限说明"]
)

# ========== 产品密码验证 ==========
if 'current_product' in st.session_state and user_email:
    current_product = st.session_state['current_product']
    accessible = get_accessible_products(user_email)
    
    if current_product not in accessible:
        st.markdown(f"### 🔒 访问 {current_product} 资产库")
        st.markdown("请输入产品密码以访问该产品的资产。")
        
        password = st.text_input("产品密码", type="password", key=f"pwd_{current_product}")
        
        if st.button("验证密码", key=f"verify_{current_product}"):
            if current_product in PRODUCT_CONFIG:
                if PRODUCT_CONFIG[current_product]['password'] == password:
                    authorize_product(current_product)
                    st.success("✅ 密码正确，已授权访问")
                    if 'need_password' in st.session_state:
                        del st.session_state['need_password']
                    st.rerun()
                else:
                    st.error("❌ 密码错误")
        
        st.markdown(f"💡 如需获取密码，请联系产品管理员：`{PRODUCT_CONFIG[current_product]['admin']}`")
        st.stop()

# ========== 页面：资产浏览 ==========
if page == "📚 资产浏览":
    st.title("📚 资产浏览")
    
    # 筛选器
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 产品筛选（只显示可访问的产品）
        if user_email:
            accessible = get_accessible_products(user_email)
            product_options = ["全部"] + [p for p in PRODUCT_CONFIG.keys() if p in accessible]
        else:
            product_options = ["全部"]
        filter_product = st.selectbox("产品筛选", product_options)
    
    with col2:
        asset_types = ["全部"] + ASSET_TYPES
        filter_type = st.selectbox("资产类型", asset_types)
    
    with col3:
        authors = ["全部"] + list(stats['by_author'].keys())
        filter_author = st.selectbox("作者筛选", authors)
    
    # 应用筛选
    filtered = assets
    
    # 产品隔离：只显示当前选中产品的资产
    if 'current_product' in st.session_state and st.session_state['current_product']:
        filter_product = st.session_state['current_product']
    
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
                st.markdown(f"**来源：** {asset.get('source', {}).get('campaign_name', '-')}")
                st.markdown(f"**创建时间：** {asset.get('created_at', '-')}")
                
                st.markdown("**标签：**")
                tags_html = "".join([f'<span class="tag-badge">{t}</span>' for t in asset.get('tags', [])])
                st.markdown(tags_html, unsafe_allow_html=True)
                
                if asset.get('notes'):
                    st.markdown(f"**备注：** {asset.get('notes')}")
                
                with st.expander("📄 查看完整数据"):
                    st.code(yaml.dump(asset, allow_unicode=True, sort_keys=False), language="yaml")

# ========== 页面：搜索资产 ==========
elif page == "🔍 搜索资产":
    st.title("🔍 搜索资产")
    
    search_type = st.radio("搜索方式", ["关键词搜索", "标签匹配"])
    
    if search_type == "关键词搜索":
        keyword = st.text_input("输入关键词", placeholder="如：暗黑、阴阳师、达人筛选")
        if keyword:
            # 只搜索可访问的产品
            if user_email:
                accessible = get_accessible_products(user_email)
            else:
                accessible = set()
            
            results = [a for a in assets if 
                      keyword.lower() in a.get('name', '').lower() or
                      keyword.lower() in str(a.get('tags', [])).lower() or
                      keyword.lower() in a.get('source', {}).get('product', '').lower() or
                      keyword.lower() in str(a).lower()]
            
            st.markdown(f"**找到 {len(results)} 个结果**")
            st.markdown("---")
            
            for asset in results:
                name = asset.get('name', '未命名')
                product = asset.get('source', {}).get('product', '-')
                atype = asset.get('asset_type', '未分类')
                
                with st.expander(f"**{name}** ({product} | {atype})"):
                    st.markdown(f"**来源：** {asset.get('source', {}).get('campaign_name', '-')}")
                    st.markdown(f"**创建时间：** {asset.get('created_at', '-')}")
                    st.markdown("**标签：** " + ", ".join(asset.get('tags', [])))
    
    else:
        all_tags = list(stats['by_tag'].keys())
        selected_tags = st.multiselect("选择标签", all_tags)
        if selected_tags:
            results = [a for a in assets if set(selected_tags) & set(a.get('tags', []))]
            st.markdown(f"**找到 {len(results)} 个结果**")
            st.markdown("---")
            
            for asset in results:
                name = asset.get('name', '未命名')
                product = asset.get('source', {}).get('product', '-')
                common_tags = set(selected_tags) & set(asset.get('tags', []))
                
                with st.expander(f"**{name}** ({product})"):
                    st.markdown(f"**匹配标签：** {', '.join(common_tags)}")
                    st.markdown(f"**创建时间：** {asset.get('created_at', '-')}")

# ========== 页面：上传资产 ==========
elif page == "➕ 上传资产":
    st.title("➕ 上传资产")
    
    if not user_email:
        st.warning("⚠️ 请先在侧边栏输入邮箱以识别身份")
        st.stop()
    
    # 选择产品
    accessible = get_accessible_products(user_email)
    if not accessible:
        st.warning("⚠️ 您还没有访问任何产品的权限")
        st.markdown("请在侧边栏点击产品名称并输入密码获取权限")
        st.stop()
    
    product = st.selectbox("选择产品", sorted(list(accessible)))
    
    # 选择资产类型
    asset_type = st.selectbox("资产类型", ASSET_TYPES)
    
    # 检查权限
    is_admin = is_product_admin(product, user_email) or is_verified_admin
    
    if asset_type in ADMIN_REQUIRED_TYPES and not is_admin:
        st.warning(f"⚠️ **{asset_type}** 类型的资产需要产品管理员上传")
        st.markdown(f"""
        **当前产品管理员：** `{PRODUCT_CONFIG[product]['admin']}`
        
        **操作方式：**
        1. 继续填写资产信息，生成 YAML
        2. 将 YAML 发送给产品管理员
        3. 由管理员审核后上传
        """)
        can_upload = False
    else:
        if is_admin:
            st.success(f"✅ 您有权限直接上传 {asset_type} 类型资产")
        can_upload = True
    
    # 资产表单
    with st.form("asset_form"):
        asset_name = st.text_input("资产名称 *", placeholder="如：暗黑风+神圣感")
        campaign_name = st.text_input("活动名称", placeholder="如：阴阳师3月SP蚀月吸血姬")
        tags_input = st.text_input("标签（逗号分隔）", placeholder="暗黑风, 神圣感, COS变装")
        custom_content = st.text_area(
            "其他内容（YAML格式）",
            placeholder="character_traits:\n  - 特征1\n  - 特征2",
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
                
                yaml_str = yaml.dump(asset_data, allow_unicode=True, sort_keys=False)
                st.success("✅ 资产生成成功！")
                st.code(yaml_str, language="yaml")
                
                if can_upload:
                    st.info("📋 复制以上 YAML 内容，通过 OpenClaw Agent 上传到资产库")
                else:
                    st.markdown(f"📧 请将以上内容发送给产品管理员：**{PRODUCT_CONFIG[product]['admin']}**")

# ========== 页面：统计面板（公开） ==========
elif page == "📊 统计面板":
    st.title("📊 统计面板")
    st.markdown("*所有产品资产统计（公开可见）*")
    
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
    
    with col2:
        st.subheader("📋 按资产类型分布")
        if stats['by_type']:
            for atype, count in sorted(stats['by_type'].items(), key=lambda x: -x[1]):
                st.markdown(f"- **{atype}**: {count} 个资产")
    
    st.markdown("---")
    
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

# ========== 页面：权限说明 ==========
elif page == "👥 权限说明":
    st.title("👥 权限说明")
    
    st.markdown("""
    ### 🔐 产品隔离
    
    每个产品资产库独立，需要输入产品密码才能查看。
    
    ### 🔑 产品管理员
    
    每个产品设有管理员，负责审核和上传特定类型的资产。
    
    **需要管理员上传的资产类型：**
    - 游戏说明书
    - KOL投放
    - 平台合作
    - 小喇叭
    
    **所有人可上传的类型：**
    - 舆情竞品监测
    
    ---
    """)
    
    st.subheader("📋 产品管理员列表")
    for product, config in PRODUCT_CONFIG.items():
        st.markdown(f"- **{product}**：`{config['admin']}`")
    
    st.markdown("---")

# ========== 页脚 ==========
st.markdown("---")
st.markdown("<div style='text-align: center; color: #666; padding: 20px;'>品牌资产共享库 v3.1 | 产品隔离 | 管理员权限</div>", unsafe_allow_html=True)

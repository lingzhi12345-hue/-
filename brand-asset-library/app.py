"""
品牌资产共享库 - Streamlit 应用 v3.4
支持原文件直接下载
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
    "梦幻西游电脑版": {"password": "wkmt24h3", "admin": "lihuixian02@corp.netease.com"},
    "梦幻西游手游": {"password": "0m2o8z5s", "admin": "linxiao03@corp.netease.com"},
    "明日之后": {"password": "j9n3jd3c", "admin": "yuetian01@corp.netease.com"},
    "率土之滨": {"password": "58ho9atd", "admin": "linxiao03@corp.netease.com"},
    "光遇": {"password": "0mvn84pq", "admin": "huanglingzhi02@corp.netease.com"},
    "萤火突击": {"password": "tkvcnczy", "admin": "huangsuixin@corp.netease.com"},
    "阴阳师": {"password": "6t8ktxlu", "admin": "huanglingzhi02@corp.netease.com"},
    "世界之外": {"password": "vke6xtnk", "admin": "huangsuixin@corp.netease.com"},
    "实况足球手游": {"password": "216ewoxn", "admin": "jiangjinpeng02@corp.netease.com"},
    "巅峰极速": {"password": "u3capmir", "admin": "huanglingzhi02@corp.netease.com"}
}

# 固定资产类型
ASSET_TYPES = ["游戏说明书", "KOL投放", "平台合作", "小喇叭", "舆情竞品监测"]

# 需要管理员权限上传的类型
ADMIN_REQUIRED_TYPES = ["游戏说明书", "KOL投放", "平台合作", "小喇叭"]

# ========== GitHub 配置 ==========
def get_github_config():
    if hasattr(st, 'secrets') and 'github' in st.secrets:
        return {
            'token': st.secrets['github'].get('token'),
            'repo': st.secrets['github'].get('repo', 'lingzhi12345-hue/brand-asset-library'),
            'branch': st.secrets['github'].get('branch', 'main')
        }
    return None

# ========== 文件下载功能 ==========
@st.cache_data(ttl=3600)
def get_file_from_github(file_path: str) -> Optional[bytes]:
    """从GitHub获取文件内容"""
    config = get_github_config()
    if not config:
        return None
    
    try:
        url = f"https://api.github.com/repos/{config['repo']}/contents/{file_path}"
        resp = requests.get(url, headers={
            "Authorization": f"token {config['token']}",
            "Accept": "application/vnd.github.v3+json"
        }, timeout=30)
        
        if resp.status_code == 200:
            content = base64.b64decode(resp.json()['content'])
            return content
    except:
        pass
    return None

def get_file_mime_type(filename: str) -> str:
    """根据文件扩展名返回MIME类型"""
    ext = Path(filename).suffix.lower()
    mime_types = {
        '.html': 'text/html',
        '.htm': 'text/html',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.xls': 'application/vnd.ms-excel',
        '.pdf': 'application/pdf',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.ppt': 'application/vnd.ms-powerpoint',
        '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        '.txt': 'text/plain',
        '.csv': 'text/csv',
        '.json': 'application/json',
        '.yaml': 'text/yaml',
        '.yml': 'text/yaml',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
    }
    return mime_types.get(ext, 'application/octet-stream')

def render_file_download(original_file: dict, asset_name: str):
    """渲染文件下载按钮"""
    if not original_file:
        return
    
    file_url = original_file.get('url', '')
    file_desc = original_file.get('description', '查看原文件')
    
    if not file_url:
        return
    
    # 提取文件名
    if 'github.com' in file_url and '/blob/' in file_url:
        # GitHub网页链接，提取文件路径
        # https://github.com/xxx/xxx/blob/main/assets/xxx.xlsx
        parts = file_url.split('/blob/main/')
        if len(parts) > 1:
            file_path = parts[1]
            filename = Path(file_path).name
            
            # 获取文件内容
            with st.spinner("正在加载文件..."):
                file_content = get_file_from_github(file_path)
            
            if file_content:
                # 根据文件类型显示不同选项
                ext = Path(filename).suffix.lower()
                
                if ext in ['.html', '.htm']:
                    # HTML文件：提供查看和下载两个选项
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            label=f"📥 下载 {filename}",
                            data=file_content,
                            file_name=filename,
                            mime='text/html',
                            key=f"dl_{asset_name}_{filename}"
                        )
                    with col2:
                        if st.button(f"👁️ 在线预览", key=f"preview_{asset_name}_{filename}"):
                            st.session_state[f'show_preview_{asset_name}'] = True
                
                elif ext in ['.xlsx', '.xls']:
                    # Excel文件：提供下载按钮
                    st.download_button(
                        label=f"📥 下载 {filename}",
                        data=file_content,
                        file_name=filename,
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        key=f"dl_{asset_name}_{filename}"
                    )
                
                else:
                    # 其他文件：提供下载按钮
                    mime_type = get_file_mime_type(filename)
                    st.download_button(
                        label=f"📥 下载 {filename}",
                        data=file_content,
                        file_name=filename,
                        mime=mime_type,
                        key=f"dl_{asset_name}_{filename}"
                    )
            else:
                st.warning(f"⚠️ 无法加载文件，请[点击这里查看]({file_url})")
        else:
            st.markdown(f"**原文件：** [{file_desc}]({file_url})")
    else:
        # 非GitHub链接，直接显示链接
        st.markdown(f"**原文件：** [{file_desc}]({file_url})")

# ========== 资产加载 ==========
@st.cache_data(ttl=300)
def load_assets_from_github():
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
    assets = load_assets_from_github()
    assets.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return assets

# ========== 统计函数 ==========
def get_statistics(assets: List[Dict]) -> Dict:
    stats = {'total': len(assets), 'by_product': {}, 'by_type': {}, 'by_author': {}, 'by_tag': {}}
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
    return email in SUPER_ADMINS

def verify_super_admin(email: str, password: str) -> bool:
    return email in SUPER_ADMINS and SUPER_ADMINS[email] == password

def is_product_admin(product: str, email: str) -> bool:
    return product in PRODUCT_CONFIG and PRODUCT_CONFIG[product]["admin"] == email

def get_accessible_products(email: str) -> set:
    if 'accessible_products' not in st.session_state:
        st.session_state['accessible_products'] = set()
    if is_super_admin(email):
        return set(PRODUCT_CONFIG.keys())
    admin_products = {p for p, c in PRODUCT_CONFIG.items() if c['admin'] == email}
    return admin_products | st.session_state['accessible_products']

def authorize_product(product: str):
    if 'accessible_products' not in st.session_state:
        st.session_state['accessible_products'] = set()
    st.session_state['accessible_products'].add(product)

# ========== 重复检测 ==========
def get_asset_hash(asset: Dict) -> str:
    core_fields = {
        'name': asset.get('name', ''),
        'asset_type': asset.get('asset_type', ''),
        'source': asset.get('source', {}),
        'tags': sorted(asset.get('tags', [])),
    }
    content = json.dumps(core_fields, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def check_duplicate(asset: Dict, existing_assets: List[Dict]) -> Optional[Dict]:
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
st.sidebar.title("🎨 品牌资产共享库")
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
    email_input = st.sidebar.text_input("邮箱", placeholder="xxx@corp.netease.com", key="email_input")
    
    if email_input:
        if is_super_admin(email_input):
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

# 产品导航
if user_email:
    accessible = get_accessible_products(user_email)
    st.sidebar.markdown("### 📦 产品导航")
    
    for product in PRODUCT_CONFIG.keys():
        count = stats['by_product'].get(product, 0)
        if product in accessible:
            if st.sidebar.button(f"✅ {product} ({count})", key=f"nav_{product}"):
                st.session_state['current_product'] = product
        else:
            if st.sidebar.button(f"🔒 {product} ({count})", key=f"nav_{product}"):
                st.session_state['current_product'] = product

st.sidebar.markdown("---")

page = st.sidebar.radio("功能导航", ["📚 资产浏览", "🔍 搜索资产", "➕ 上传资产", "📊 统计面板", "👥 权限说明"])

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
                    st.rerun()
                else:
                    st.error("❌ 密码错误")
        
        st.markdown(f"💡 如需获取密码，请联系产品管理员：`{PRODUCT_CONFIG[current_product]['admin']}`")
        st.stop()

# ========== 页面：资产浏览（严格隔离） ==========
if page == "📚 资产浏览":
    st.title("📚 资产浏览")
    
    if not user_email:
        st.warning("⚠️ 请先在侧边栏登录以查看资产")
        st.markdown("### 🔐 登录步骤")
        st.markdown("1. 在侧边栏输入您的邮箱")
        st.markdown("2. 如果是管理员邮箱，需要输入管理员密码")
        st.markdown("3. 登录后点击产品导航获取访问权限")
        st.stop()
    
    if 'current_product' not in st.session_state:
        st.info("👆 请在侧边栏点击产品名称以查看资产")
        st.stop()
    
    current_product = st.session_state['current_product']
    accessible = get_accessible_products(user_email)
    
    if current_product not in accessible:
        st.warning(f"⚠️ 您尚未获得 {current_product} 的访问权限")
        st.stop()
    
    filtered = [a for a in assets if a.get('source', {}).get('product') == current_product]
    
    st.markdown(f"**{current_product} - 共 {len(filtered)} 个资产**")
    st.markdown("---")
    
    if not filtered:
        st.info("该产品暂无资产")
    else:
        for asset in filtered:
            name = asset.get('name', '未命名')
            author = asset.get('author', '未知')
            atype = asset.get('asset_type', '未分类')
            
            with st.expander(f"**{name}** - {author} ({atype})"):
                st.markdown(f"**来源：** {asset.get('source', {}).get('campaign_name', '-')}")
                st.markdown(f"**创建时间：** {asset.get('created_at', '-')}")
                
                # 原文件下载
                original_file = asset.get('original_file', {})
                if original_file:
                    st.markdown("**原文件：**")
                    render_file_download(original_file, name)
                
                st.markdown("**标签：**")
                tags_html = "".join([f'<span class="tag-badge">{t}</span>' for t in asset.get('tags', [])])
                st.markdown(tags_html, unsafe_allow_html=True)
                
                # 摘要
                if asset.get('summary'):
                    st.markdown("**摘要：**")
                    st.markdown(asset.get('summary'))
                
                # HTML预览
                if st.session_state.get(f'show_preview_{name}'):
                    original_file = asset.get('original_file', {})
                    if original_file:
                        file_url = original_file.get('url', '')
                        if 'github.com' in file_url and '/blob/' in file_url:
                            parts = file_url.split('/blob/main/')
                            if len(parts) > 1:
                                file_path = parts[1]
                                file_content = get_file_from_github(file_path)
                                if file_content:
                                    st.markdown("---")
                                    st.markdown("**HTML预览：**")
                                    st.components.v1.html(file_content.decode('utf-8'), height=600, scrolling=True)
                
                with st.expander("📄 查看完整数据"):
                    st.code(yaml.dump(asset, allow_unicode=True, sort_keys=False), language="yaml")

# ========== 页面：搜索资产（所有人可搜索，区分权限） ==========
elif page == "🔍 搜索资产":
    st.title("🔍 搜索资产")
    st.markdown("*搜索结果将根据您的权限展示不同详情*")
    
    search_type = st.radio("搜索方式", ["关键词搜索", "标签匹配"])
    
    if user_email:
        accessible = get_accessible_products(user_email)
    else:
        accessible = set()
    
    if search_type == "关键词搜索":
        keyword = st.text_input("输入关键词", placeholder="如：暗黑、阴阳师")
        if keyword:
            results = [a for a in assets if 
                      keyword.lower() in a.get('name', '').lower() or
                      keyword.lower() in str(a.get('tags', [])).lower() or
                      keyword.lower() in a.get('source', {}).get('product', '').lower()]
            
            st.markdown(f"**找到 {len(results)} 个结果**")
            st.markdown("---")
            
            for asset in results:
                name = asset.get('name', '未命名')
                product = asset.get('source', {}).get('product', '-')
                atype = asset.get('asset_type', '未分类')
                has_permission = product in accessible
                
                if has_permission:
                    with st.expander(f"✅ **{name}** ({product} | {atype})"):
                        st.markdown(f"**来源：** {asset.get('source', {}).get('campaign_name', '-')}")
                        st.markdown(f"**创建时间：** {asset.get('created_at', '-')}")
                        
                        original_file = asset.get('original_file', {})
                        if original_file:
                            st.markdown("**原文件：**")
                            render_file_download(original_file, name)
                        
                        if asset.get('summary'):
                            st.markdown("**摘要：**")
                            st.markdown(asset.get('summary'))
                        
                        with st.expander("📄 查看完整数据"):
                            st.code(yaml.dump(asset, allow_unicode=True, sort_keys=False), language="yaml")
                else:
                    with st.expander(f"🔒 **{name}** ({product} | {atype})"):
                        st.warning(f"⚠️ 您没有 **{product}** 的访问权限")
                        if product in PRODUCT_CONFIG:
                            admin_email = PRODUCT_CONFIG[product]['admin']
                            st.markdown(f"**如需了解详情，请联系产品管理员：** `{admin_email}`")
    
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
                atype = asset.get('asset_type', '未分类')
                has_permission = product in accessible
                
                if has_permission:
                    with st.expander(f"✅ **{name}** ({product} | {atype})"):
                        st.markdown(f"**来源：** {asset.get('source', {}).get('campaign_name', '-')}")
                        st.markdown(f"**创建时间：** {asset.get('created_at', '-')}")
                        
                        original_file = asset.get('original_file', {})
                        if original_file:
                            st.markdown("**原文件：**")
                            render_file_download(original_file, name)
                        
                        if asset.get('summary'):
                            st.markdown("**摘要：**")
                            st.markdown(asset.get('summary'))
                else:
                    with st.expander(f"🔒 **{name}** ({product} | {atype})"):
                        st.warning(f"⚠️ 您没有 **{product}** 的访问权限")
                        if product in PRODUCT_CONFIG:
                            admin_email = PRODUCT_CONFIG[product]['admin']
                            st.markdown(f"**如需了解详情，请联系产品管理员：** `{admin_email}`")

# ========== 页面：上传资产 ==========
elif page == "➕ 上传资产":
    st.title("➕ 上传资产")
    
    if not user_email:
        st.warning("⚠️ 请先在侧边栏登录")
        st.stop()
    
    accessible = get_accessible_products(user_email)
    if not accessible:
        st.warning("⚠️ 您还没有访问任何产品的权限")
        st.stop()
    
    product = st.selectbox("选择产品", sorted(list(accessible)))
    asset_type = st.selectbox("资产类型", ASSET_TYPES)
    
    is_admin = is_product_admin(product, user_email) or is_verified_admin
    
    if asset_type in ADMIN_REQUIRED_TYPES and not is_admin:
        st.warning(f"⚠️ **{asset_type}** 类型的资产需要产品管理员上传")
        st.markdown(f"**当前产品管理员：** `{PRODUCT_CONFIG[product]['admin']}`")
        st.markdown("请继续填写资产信息，生成的 YAML 将发送给管理员")
        can_upload = False
    else:
        if is_admin:
            st.success(f"✅ 您有权限直接上传")
        can_upload = True
    
    with st.form("asset_form"):
        asset_name = st.text_input("资产名称 *")
        campaign_name = st.text_input("活动名称")
        
        st.markdown("**原文件链接（可选）：**")
        st.markdown("💡 如果文件已上传到GitHub，填写GitHub链接可直接下载")
        col_url, col_desc = st.columns(2)
        with col_url:
            original_file_url = st.text_input("文件链接", placeholder="https://github.com/xxx/blob/main/assets/xxx.xlsx")
        with col_desc:
            original_file_desc = st.text_input("链接描述", placeholder="如：完整版HTML报告")
        
        st.markdown("**摘要 *（请按以下格式填写）：**")
        st.markdown("""
        ```
        创新性：xxx
        复用性：xxx
        避坑点：xxx
        效果：xxx
        ```
        """)
        summary = st.text_area(
            "摘要内容", 
            placeholder="创新性：首次尝试xxx玩法，效果显著\n复用性：可复用于xxx场景\n避坑点：需注意xxx\n效果：CPM降低xx%，播放量提升xx%",
            height=100
        )
        
        tags_input = st.text_input("标签（逗号分隔）")
        custom_content = st.text_area("其他内容（YAML格式）", height=100)
        
        if st.form_submit_button("✅ 生成资产"):
            if not asset_name:
                st.error("请填写资产名称")
            elif not summary:
                st.error("请填写摘要")
            else:
                asset_data = {
                    "name": asset_name,
                    "asset_type": asset_type,
                    "author": user_email,
                    "source": {"campaign_name": campaign_name, "product": product},
                    "summary": summary,
                    "tags": [t.strip() for t in tags_input.split(',') if t.strip()],
                    "created_at": datetime.now().strftime('%Y-%m-%d')
                }
                
                if original_file_url:
                    asset_data["original_file"] = {
                        "url": original_file_url,
                        "description": original_file_desc or "查看原文件"
                    }
                
                if custom_content:
                    try:
                        custom_data = yaml.safe_load(custom_content)
                        if isinstance(custom_data, dict):
                            asset_data.update(custom_data)
                    except:
                        pass
                
                duplicate = check_duplicate(asset_data, assets)
                if duplicate:
                    st.warning(f"⚠️ 检测到重复资产：{duplicate.get('name')}")
                
                yaml_str = yaml.dump(asset_data, allow_unicode=True, sort_keys=False)
                st.success("✅ 资产生成成功！")
                st.code(yaml_str, language="yaml")

# ========== 页面：统计面板（公开） ==========
elif page == "📊 统计面板":
    st.title("📊 统计面板")
    st.markdown("*所有产品资产统计（公开可见）*")
    
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
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📦 按产品分布")
        for product, count in sorted(stats['by_product'].items(), key=lambda x: -x[1]):
            st.markdown(f"- **{product}**: {count} 个资产")
    
    with col2:
        st.subheader("📋 按资产类型分布")
        for atype, count in sorted(stats['by_type'].items(), key=lambda x: -x[1]):
            st.markdown(f"- **{atype}**: {count} 个资产")

# ========== 页面：权限说明 ==========
elif page == "👥 权限说明":
    st.title("👥 权限说明")
    st.markdown("""
    ### 🔐 产品隔离
    
    每个产品资产库独立，需要输入产品密码才能查看。
    
    ### 👑 超级管理员
    
    可访问所有产品资产，无需输入产品密码：
    - `guoyajun@corp.netease.com`
    - `huanglingzhi02@corp.netease.com`
    
    ### 🔑 产品管理员
    
    **需要管理员上传的资产类型：**
    - 游戏说明书、KOL投放、平台合作、小喇叭
    
    **所有人可上传：**
    - 舆情竞品监测
    """)
    
    st.subheader("📋 产品管理员列表")
    for product, config in PRODUCT_CONFIG.items():
        st.markdown(f"- **{product}**：`{config['admin']}`")

# ========== 页脚 ==========
st.markdown("---")
st.markdown("<div style='text-align: center; color: #666;'>品牌资产共享库 v3.4 | 支持原文件直接下载</div>", unsafe_allow_html=True)

"""
品牌资产共享库 - Streamlit 应用
支持资产浏览、创建、搜索、导出
支持自动同步到 GitHub
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

# ========== GitHub 同步器（内嵌版本） ==========
class GitHubSync:
    """GitHub 同步器"""
    
    def __init__(self, token: str, repo: str, branch: str = "main"):
        self.token = token
        self.repo = repo
        self.branch = branch
        self.api_base = "https://api.github.com"
    
    def _get_headers(self):
        return {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def file_exists(self, file_path: str) -> Optional[str]:
        url = f"{self.api_base}/repos/{self.repo}/contents/{file_path}"
        params = {"ref": self.branch}
        response = requests.get(url, headers=self._get_headers(), params=params)
        if response.status_code == 200:
            return response.json().get('sha')
        return None
    
    def commit_file(self, file_path: str, content: str, message: str = "Update file") -> bool:
        url = f"{self.api_base}/repos/{self.repo}/contents/{file_path}"
        sha = self.file_exists(file_path)
        data = {
            "message": message,
            "content": base64.b64encode(content.encode('utf-8')).decode('utf-8'),
            "branch": self.branch
        }
        if sha:
            data["sha"] = sha
        response = requests.put(url, headers=self._get_headers(), json=data)
        return response.status_code in [200, 201]

# ========== 资产管理器（内嵌版本） ==========
class AssetManager:
    """品牌资产管理器"""
    
    def __init__(self, assets_dir: str = "assets", github_sync: Optional[GitHubSync] = None):
        self.assets_dir = Path(assets_dir)
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        self.github_sync = github_sync
        
    def load_asset(self, asset_id: str) -> Optional[Dict]:
        file_path = self.assets_dir / f"{asset_id}.yaml"
        if not file_path.exists():
            return None
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def list_assets(self, filters: Optional[Dict] = None) -> List[Dict]:
        assets = []
        for file_path in self.assets_dir.glob("*.yaml"):
            with open(file_path, 'r', encoding='utf-8') as f:
                asset = yaml.safe_load(f)
                if asset:
                    assets.append(asset)
        assets.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        if filters:
            assets = self._apply_filters(assets, filters)
        return assets
    
    def _apply_filters(self, assets: List[Dict], filters: Dict) -> List[Dict]:
        result = assets
        if filters.get('author'):
            result = [a for a in result if a.get('author') == filters['author']]
        if filters.get('product'):
            result = [a for a in result if a.get('source', {}).get('product') == filters['product']]
        if filters.get('tags'):
            filter_tags = set(filters['tags'])
            result = [a for a in result if filter_tags & set(a.get('tags', []))]
        if filters.get('keyword'):
            keyword = filters['keyword'].lower()
            result = [a for a in result if keyword in a.get('name', '').lower()
                     or any(keyword in t.lower() for t in a.get('tags', []))]
        return result
    
    def save_asset(self, asset_data: Dict) -> str:
        if not asset_data.get('asset_id'):
            today = datetime.now().strftime('%Y%m%d')
            existing = list(self.assets_dir.glob(f"ASSET-{today}-*.yaml"))
            next_num = len(existing) + 1
            asset_data['asset_id'] = f"ASSET-{today}-{next_num:03d}"
        asset_data['updated_at'] = datetime.now().strftime('%Y-%m-%d')
        if not asset_data.get('created_at'):
            asset_data['created_at'] = asset_data['updated_at']
        self._validate_asset(asset_data)
        
        # 保存到本地
        file_path = self.assets_dir / f"{asset_data['asset_id']}.yaml"
        yaml_content = yaml.dump(asset_data, allow_unicode=True, sort_keys=False)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(yaml_content)
        
        # 同步到 GitHub
        if self.github_sync:
            try:
                self.github_sync.commit_file(
                    f"assets/{asset_data['asset_id']}.yaml",
                    yaml_content,
                    f"添加资产: {asset_data.get('name', asset_data['asset_id'])}"
                )
                # 更新 assets.json
                self._update_assets_json()
            except Exception as e:
                st.warning(f"GitHub 同步失败: {str(e)}")
        
        return asset_data['asset_id']
    
    def _update_assets_json(self):
        """更新 assets.json 文件"""
        assets = self.list_assets()
        json_content = json.dumps(assets, ensure_ascii=False, indent=2)
        with open("assets.json", 'w', encoding='utf-8') as f:
            f.write(json_content)
        if self.github_sync:
            self.github_sync.commit_file(
                "assets.json",
                json_content,
                "更新资产列表"
            )
    
    def _validate_asset(self, asset_data: Dict):
        required_fields = ['name', 'author', 'source', 'tags', 'content_structure', 'top_cases']
        missing = [f for f in required_fields if not asset_data.get(f)]
        if missing:
            raise ValueError(f"缺少必填字段: {', '.join(missing)}")
        source = asset_data.get('source', {})
        if not source.get('campaign_name'):
            raise ValueError("source.campaign_name 为必填项")
        if not asset_data.get('tags') or len(asset_data['tags']) == 0:
            raise ValueError("tags 至少需要一项")
        if not asset_data.get('content_structure') or len(asset_data['content_structure']) == 0:
            raise ValueError("content_structure 至少需要一项")
        if not asset_data.get('top_cases') or len(asset_data['top_cases']) == 0:
            raise ValueError("top_cases 至少需要一项")
    
    def delete_asset(self, asset_id: str) -> bool:
        file_path = self.assets_dir / f"{asset_id}.yaml"
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    
    def get_statistics(self) -> Dict:
        assets = self.list_assets()
        tag_counts = {}
        for asset in assets:
            for tag in asset.get('tags', []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        author_counts = {}
        for asset in assets:
            author = asset.get('author', 'unknown')
            author_counts[author] = author_counts.get(author, 0) + 1
        product_counts = {}
        for asset in assets:
            product = asset.get('source', {}).get('product', 'unknown')
            product_counts[product] = product_counts.get(product, 0) + 1
        return {
            'total_assets': len(assets),
            'tag_distribution': tag_counts,
            'author_distribution': author_counts,
            'product_distribution': product_counts,
        }
    
    def export_to_json(self, output_path: str):
        assets = self.list_assets()
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(assets, f, ensure_ascii=False, indent=2)
    
    def search_similar_assets(self, tags: List[str], limit: int = 5) -> List[Dict]:
        assets = self.list_assets()
        query_tags = set(tags)
        scored_assets = []
        for asset in assets:
            asset_tags = set(asset.get('tags', []))
            intersection = len(query_tags & asset_tags)
            union = len(query_tags | asset_tags)
            score = intersection / union if union > 0 else 0
            if score > 0:
                scored_assets.append((score, asset))
        scored_assets.sort(key=lambda x: x[0], reverse=True)
        return [a for _, a in scored_assets[:limit]]

# ========== 自定义样式 ==========
st.markdown("""
<style>
    .asset-card {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 16px;
        margin: 8px 0;
        border-left: 4px solid #4CAF50;
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
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .stat-number {
        font-size: 36px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ========== 初始化 ==========
@st.cache_resource
def get_asset_manager():
    # 尝试从 secrets 读取 GitHub 配置
    github_sync = None
    try:
        if hasattr(st, 'secrets') and 'github' in st.secrets:
            github_sync = GitHubSync(
                token=st.secrets['github']['token'],
                repo=st.secrets['github']['repo'],
                branch=st.secrets['github'].get('branch', 'main')
            )
    except Exception as e:
        st.warning(f"GitHub 同步未启用: {str(e)}")
    
    return AssetManager(assets_dir="assets", github_sync=github_sync)

manager = get_asset_manager()

# ========== 侧边栏 ==========
st.sidebar.title("🎨 品牌资产共享库")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "功能导航",
    ["📚 资产浏览", "➕ 创建资产", "🔍 搜索资产", "📊 统计面板", "🔌 API集成"]
)

# 显示 GitHub 同步状态
if manager.github_sync:
    st.sidebar.success("✅ GitHub 同步已启用")
else:
    st.sidebar.warning("⚠️ GitHub 同步未配置")

st.sidebar.markdown("---")
st.sidebar.markdown("""
**使用说明**
1. 浏览：查看所有共享资产
2. 创建：上传新的品牌资产
3. 搜索：按标签/关键词查找
4. 统计：查看资产库概况
5. API：获取接入指南
""")

# ========== 页面：资产浏览 ==========
if page == "📚 资产浏览":
    st.title("📚 资产浏览")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_product = st.selectbox(
            "产品筛选",
            options=["全部"] + list(manager.get_statistics().get('product_distribution', {}).keys())
        )
    with col2:
        filter_author = st.selectbox(
            "作者筛选",
            options=["全部"] + list(manager.get_statistics().get('author_distribution', {}).keys())
        )
    with col3:
        sort_by = st.selectbox("排序", ["最新", "最多案例"])
    
    filters = {}
    if filter_product != "全部":
        filters['product'] = filter_product
    if filter_author != "全部":
        filters['author'] = filter_author
    
    assets = manager.list_assets(filters)
    
    if sort_by == "最多案例":
        assets.sort(key=lambda x: len(x.get('top_cases', [])), reverse=True)
    
    st.markdown(f"**共 {len(assets)} 个资产**")
    st.markdown("---")
    
    for asset in assets:
        with st.expander(f"**{asset.get('name', '未命名')}** - {asset.get('author', '未知')}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**来源：** {asset.get('source', {}).get('campaign_name', '-')}")
                st.markdown(f"**产品：** {asset.get('source', {}).get('product', '-')}")
                st.markdown(f"**创建时间：** {asset.get('created_at', '-')}")
                
                st.markdown("**标签：**")
                tags_html = "".join([f'<span class="tag-badge">{t}</span>' for t in asset.get('tags', [])])
                st.markdown(tags_html, unsafe_allow_html=True)
                
                st.markdown("**爆款案例：**")
                for case in asset.get('top_cases', [])[:3]:
                    st.markdown(f"- {case.get('creator', '-')} | {case.get('platform', '-')} | 播放 {case.get('views', 0):,} | CPM {case.get('cpm', 0):.1f}")
            
            with col2:
                if st.button("📋 查看详情", key=f"view_{asset.get('asset_id')}"):
                    st.session_state['view_asset'] = asset.get('asset_id')
                
                if st.button("📥 下载YAML", key=f"dl_{asset.get('asset_id')}"):
                    yaml_str = yaml.dump(asset, allow_unicode=True, sort_keys=False)
                    st.download_button(
                        label="确认下载",
                        data=yaml_str,
                        file_name=f"{asset.get('asset_id')}.yaml",
                        mime="text/yaml"
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
        with col2:
            product = st.text_input("产品 *", placeholder="如：阴阳师")
            campaign_name = st.text_input("活动名称 *", placeholder="如：阴阳师3月SP蚀月吸血姬")
        
        campaign_id = st.text_input("一级单号（可选）", placeholder="如：273292")
        period = st.text_input("时间段", placeholder="如：2026年3月")
        
        st.subheader("🏷️ 标签")
        st.markdown("输入标签，用逗号分隔")
        tags_input = st.text_input("标签 *", placeholder="暗黑风, 神圣感, COS变装")
        
        st.subheader("👤 适用角色特征（可选）")
        character_traits = st.text_area(
            "每行一个特征",
            placeholder="兼具黑暗与光明双重属性\n有救赎/牺牲背景故事",
            height=80
        )
        
        st.subheader("🎬 内容结构 *")
        st.markdown("爆款视频的结构拆解，至少填写一个阶段")
        
        structures = []
        phases = ["开场", "转场", "呈现", "收尾"]
        default_durations = ["0-5秒", "5-8秒", "8-20秒", "20-30秒"]
        
        for i, (phase, duration) in enumerate(zip(phases, default_durations)):
            with st.expander(f"阶段 {i+1}: {phase}"):
                col1, col2 = st.columns(2)
                with col1:
                    phase_duration = st.text_input("时长", value=duration, key=f"duration_{i}")
                    phase_purpose = st.text_input("目的", key=f"purpose_{i}")
                with col2:
                    phase_techniques = st.text_area("技巧（每行一个）", height=60, key=f"tech_{i}")
                    phase_example = st.text_area("示例描述", height=40, key=f"example_{i}")
                
                if phase_purpose:
                    structures.append({
                        "phase": phase,
                        "duration": phase_duration,
                        "purpose": phase_purpose,
                        "techniques": [t.strip() for t in phase_techniques.split('\n') if t.strip()],
                        "example": phase_example
                    })
        
        st.subheader("🏆 爆款案例 *")
        st.markdown("至少填写一个成功案例")
        
        cases = []
        for i in range(3):
            with st.expander(f"案例 {i+1}{'*' if i == 0 else ''}"):
                col1, col2 = st.columns(2)
                with col1:
                    case_creator = st.text_input("创作者", key=f"creator_{i}")
                    case_platform = st.selectbox("平台", ["抖音", "B站", "小红书", "微博"], key=f"platform_{i}")
                    case_video_url = st.text_input("视频链接（可选）", key=f"url_{i}")
                with col2:
                    case_views = st.number_input("播放量", min_value=0, value=0, step=10000, key=f"views_{i}")
                    case_likes = st.number_input("点赞数", min_value=0, value=0, step=1000, key=f"likes_{i}")
                    case_cpm = st.number_input("CPM", min_value=0.0, value=0.0, step=0.1, key=f"cpm_{i}")
                
                case_description = st.text_area("案例说明", height=40, key=f"desc_{i}")
                case_factors = st.text_area("成功因素（每行一个）", height=40, key=f"factors_{i}")
                
                if case_creator:
                    cases.append({
                        "creator": case_creator,
                        "platform": case_platform,
                        "video_url": case_video_url,
                        "views": case_views,
                        "likes": case_likes,
                        "cpm": case_cpm,
                        "description": case_description,
                        "key_success_factors": [f.strip() for f in case_factors.split('\n') if f.strip()]
                    })
        
        st.subheader("📝 注意事项（可选）")
        notes = st.text_area("每行一个注意点", height=60)
        
        st.markdown("---")
        submitted = st.form_submit_button("✅ 创建资产", type="primary")
        
        if submitted:
            errors = []
            if not asset_name:
                errors.append("资产名称")
            if not author:
                errors.append("上传者")
            if not product:
                errors.append("产品")
            if not campaign_name:
                errors.append("活动名称")
            if not tags_input:
                errors.append("标签")
            if not structures:
                errors.append("内容结构")
            if not cases:
                errors.append("爆款案例")
            
            if errors:
                st.error(f"请填写以下必填项：{', '.join(errors)}")
            else:
                asset_data = {
                    "name": asset_name,
                    "author": author,
                    "source": {
                        "campaign_name": campaign_name,
                        "campaign_id": campaign_id,
                        "product": product,
                        "period": period
                    },
                    "tags": [t.strip() for t in tags_input.split(',') if t.strip()],
                    "character_traits": [t.strip() for t in character_traits.split('\n') if t.strip()] if character_traits else [],
                    "content_structure": structures,
                    "top_cases": cases,
                    "notes": [n.strip() for n in notes.split('\n') if n.strip()] if notes else [],
                    "version": 1
                }
                
                try:
                    asset_id = manager.save_asset(asset_data)
                    st.success(f"✅ 资产创建成功！资产ID: {asset_id}")
                    if manager.github_sync:
                        st.success("📤 已同步到 GitHub")
                    st.balloons()
                except Exception as e:
                    st.error(f"创建失败: {str(e)}")

# ========== 页面：搜索资产 ==========
elif page == "🔍 搜索资产":
    st.title("🔍 搜索资产")
    
    search_type = st.radio("搜索方式", ["关键词搜索", "标签匹配", "相似推荐"])
    
    if search_type == "关键词搜索":
        keyword = st.text_input("输入关键词", placeholder="如：暗黑、神圣、阴阳师")
        if keyword:
            results = manager.list_assets(filters={'keyword': keyword})
            st.markdown(f"**找到 {len(results)} 个结果**")
            for asset in results:
                st.markdown(f"- **{asset.get('name')}** ({asset.get('source', {}).get('product', '-')})")
    
    elif search_type == "标签匹配":
        stats = manager.get_statistics()
        all_tags = list(stats.get('tag_distribution', {}).keys())
        
        selected_tags = st.multiselect("选择标签", all_tags)
        if selected_tags:
            results = manager.list_assets(filters={'tags': selected_tags})
            st.markdown(f"**找到 {len(results)} 个结果**")
            for asset in results:
                st.markdown(f"- **{asset.get('name')}** ({asset.get('source', {}).get('product', '-')})")
    
    elif search_type == "相似推荐":
        all_assets = manager.list_assets()
        asset_names = [a.get('name') for a in all_assets]
        
        selected_name = st.selectbox("选择参考资产", asset_names)
        if selected_name:
            selected_asset = next((a for a in all_assets if a.get('name') == selected_name), None)
            if selected_asset:
                similar = manager.search_similar_assets(selected_asset.get('tags', []))
                st.markdown(f"**找到 {len(similar)} 个相似资产**")
                for asset in similar:
                    common_tags = set(asset.get('tags', [])) & set(selected_asset.get('tags', []))
                    st.markdown(f"- **{asset.get('name')}** (共同标签: {', '.join(common_tags)})")

# ========== 页面：统计面板 ==========
elif page == "📊 统计面板":
    st.title("📊 统计面板")
    
    stats = manager.get_statistics()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{stats.get('total_assets', 0)}</div>
            <div>总资产数</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{len(stats.get('tag_distribution', {}))}</div>
            <div>标签种类</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{len(stats.get('author_distribution', {}))}</div>
            <div>贡献者</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{len(stats.get('product_distribution', {}))}</div>
            <div>产品数</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏷️ 标签分布 TOP 10")
        tag_dist = stats.get('tag_distribution', {})
        sorted_tags = sorted(tag_dist.items(), key=lambda x: x[1], reverse=True)[:10]
        for tag, count in sorted_tags:
            st.markdown(f"- {tag}: {count}")
    
    with col2:
        st.subheader("👤 贡献者排行")
        author_dist = stats.get('author_distribution', {})
        sorted_authors = sorted(author_dist.items(), key=lambda x: x[1], reverse=True)
        for author, count in sorted_authors:
            st.markdown(f"- {author}: {count} 个资产")
    
    st.markdown("---")
    
    st.subheader("📦 产品分布")
    product_dist = stats.get('product_distribution', {})
    if product_dist:
        st.bar_chart(product_dist)

# ========== 页面：API集成 ==========
elif page == "🔌 API集成":
    st.title("🔌 API集成指南")
    
    st.markdown("""
    ### 如何让龙虾 Agent 接入资产库
    
    品牌资产库通过 GitHub 托管，龙虾 Agent 可以通过以下方式读取数据：
    """)
    
    st.subheader("1️⃣ 获取资产列表（JSON）")
    st.code("""
# Python 示例
import requests

# GitHub Raw URL
url = "https://raw.githubusercontent.com/lingzhi12345-hue/brand-asset-library/main/assets.json"

response = requests.get(url)
assets = response.json()

# 搜索特定标签的资产
dark_style_assets = [a for a in assets if '暗黑风' in a.get('tags', [])]
""", language="python")
    
    st.subheader("2️⃣ 获取单个资产详情")
    st.code("""
# 获取特定资产
asset_id = "ASSET-20260409-001"
url = f"https://raw.githubusercontent.com/lingzhi12345-hue/brand-asset-library/main/assets/{asset_id}.yaml"

response = requests.get(url)
import yaml
asset = yaml.safe_load(response.text)
""", language="python")
    
    st.subheader("3️⃣ 推荐相似资产")
    st.code("""
# 基于标签计算相似度
def find_similar_assets(target_tags, assets, top_n=5):
    scored = []
    target_set = set(target_tags)
    
    for asset in assets:
        asset_tags = set(asset.get('tags', []))
        similarity = len(target_set & asset_tags) / len(target_set | asset_tags)
        if similarity > 0:
            scored.append((similarity, asset))
    
    scored.sort(reverse=True, key=lambda x: x[0])
    return [a for _, a in scored[:top_n]]

similar = find_similar_assets(['暗黑风', '神圣感'], assets)
""", language="python")
    
    st.markdown("---")
    
    st.subheader("📡 当前 API 地址")
    st.info(f"""
    - 资产列表: `https://raw.githubusercontent.com/lingzhi12345-hue/brand-asset-library/main/assets.json`
    - 单个资产: `https://raw.githubusercontent.com/lingzhi12345-hue/brand-asset-library/main/assets/{{asset_id}}.yaml`
    """)
    
    st.markdown("---")
    
    st.subheader("📤 导出资产为 JSON")
    if st.button("导出 assets.json"):
        manager.export_to_json("assets.json")
        with open("assets.json", "r", encoding="utf-8") as f:
            st.download_button(
                label="下载 assets.json",
                data=f.read(),
                file_name="assets.json",
                mime="application/json"
            )

# ========== 页脚 ==========
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 20px;">
    品牌资产共享库 v1.1 | 由 OpenClaw 搭建 | 支持 GitHub 自动同步
</div>
""", unsafe_allow_html=True)

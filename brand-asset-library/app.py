"""
品牌资产共享库 - Streamlit 应用
支持资产浏览、创建、搜索、导出
"""

import streamlit as st
import yaml
import json
from datetime import datetime
from pathlib import Path
import sys

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))
from utils.asset_manager import AssetManager

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
    return AssetManager(assets_dir="assets")

manager = get_asset_manager()

# ========== 侧边栏 ==========
st.sidebar.title("🎨 品牌资产共享库")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "功能导航",
    ["📚 资产浏览", "➕ 创建资产", "🔍 搜索资产", "📊 统计面板", "🔌 API集成"]
)

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
    
    # 筛选器
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
    
    # 获取资产列表
    filters = {}
    if filter_product != "全部":
        filters['product'] = filter_product
    if filter_author != "全部":
        filters['author'] = filter_author
    
    assets = manager.list_assets(filters)
    
    # 排序
    if sort_by == "最多案例":
        assets.sort(key=lambda x: len(x.get('top_cases', [])), reverse=True)
    
    st.markdown(f"**共 {len(assets)} 个资产**")
    st.markdown("---")
    
    # 展示资产卡片
    for asset in assets:
        with st.expander(f"**{asset.get('name', '未命名')}** - {asset.get('author', '未知')}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # 基本信息
                st.markdown(f"**来源：** {asset.get('source', {}).get('campaign_name', '-')}")
                st.markdown(f"**产品：** {asset.get('source', {}).get('product', '-')}")
                st.markdown(f"**创建时间：** {asset.get('created_at', '-')}")
                
                # 标签
                st.markdown("**标签：**")
                tags_html = "".join([f'<span class="tag-badge">{t}</span>' for t in asset.get('tags', [])])
                st.markdown(tags_html, unsafe_allow_html=True)
                
                # 爆款案例
                st.markdown("**爆款案例：**")
                for case in asset.get('top_cases', [])[:3]:
                    st.markdown(f"- {case.get('creator', '-')} | {case.get('platform', '-')} | 播放 {case.get('views', 0):,} | CPM {case.get('cpm', 0):.1f}")
            
            with col2:
                # 操作按钮
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
        # 基本信息
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
        
        # 标签
        st.subheader("🏷️ 标签")
        st.markdown("输入标签，用逗号分隔")
        tags_input = st.text_input("标签 *", placeholder="暗黑风, 神圣感, COS变装")
        
        # 适用角色特征
        st.subheader("👤 适用角色特征（可选）")
        character_traits = st.text_area(
            "每行一个特征",
            placeholder="兼具黑暗与光明双重属性\n有救赎/牺牲背景故事",
            height=80
        )
        
        # 内容结构
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
        
        # 爆款案例
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
        
        # 注意事项
        st.subheader("📝 注意事项（可选）")
        notes = st.text_area("每行一个注意点", height=60)
        
        # 提交按钮
        st.markdown("---")
        submitted = st.form_submit_button("✅ 创建资产", type="primary")
        
        if submitted:
            # 验证必填字段
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
                # 构建资产数据
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
                    st.balloons()
                except Exception as e:
                    st.error(f"创建失败: {str(e)}")

# ========== 页面：搜索资产 ==========
elif page == "🔍 搜索资产":
    st.title("🔍 搜索资产")
    
    # 搜索方式
    search_type = st.radio("搜索方式", ["关键词搜索", "标签匹配", "相似推荐"])
    
    if search_type == "关键词搜索":
        keyword = st.text_input("输入关键词", placeholder="如：暗黑、神圣、阴阳师")
        if keyword:
            results = manager.list_assets(filters={'keyword': keyword})
            st.markdown(f"**找到 {len(results)} 个结果**")
            for asset in results:
                st.markdown(f"- **{asset.get('name')}** ({asset.get('source', {}).get('product', '-')})")
    
    elif search_type == "标签匹配":
        # 获取所有标签
        stats = manager.get_statistics()
        all_tags = list(stats.get('tag_distribution', {}).keys())
        
        selected_tags = st.multiselect("选择标签", all_tags)
        if selected_tags:
            results = manager.list_assets(filters={'tags': selected_tags})
            st.markdown(f"**找到 {len(results)} 个结果**")
            for asset in results:
                st.markdown(f"- **{asset.get('name')}** ({asset.get('source', {}).get('product', '-')})")
    
    elif search_type == "相似推荐":
        # 获取所有资产
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
    
    # 总览卡片
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
    
    # 标签分布
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
    
    # 产品分布
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
url = "https://raw.githubusercontent.com/你的用户名/brand-asset-library/main/assets.json"

response = requests.get(url)
assets = response.json()

# 搜索特定标签的资产
dark_style_assets = [a for a in assets if '暗黑风' in a.get('tags', [])]
""", language="python")
    
    st.subheader("2️⃣ 获取单个资产详情")
    st.code("""
# 获取特定资产
asset_id = "ASSET-20260409-001"
url = f"https://raw.githubusercontent.com/你的用户名/brand-asset-library/main/assets/{asset_id}.yaml"

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
        # Jaccard 相似度
        similarity = len(target_set & asset_tags) / len(target_set | asset_tags)
        if similarity > 0:
            scored.append((similarity, asset))
    
    scored.sort(reverse=True, key=lambda x: x[0])
    return [a for _, a in scored[:top_n]]

# 使用示例
similar = find_similar_assets(['暗黑风', '神圣感'], assets)
""", language="python")
    
    st.markdown("---")
    
    st.subheader("📡 部署后更新 URL")
    st.info("""
    1. 创建 GitHub 仓库：`brand-asset-library`
    2. 上传项目代码
    3. 部署到 Streamlit Cloud
    4. 更新上面的 URL 中的 `你的用户名`
    5. 在龙虾 Agent 中配置 API 调用
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
    品牌资产共享库 v1.0 | 由 OpenClaw 搭建 | 
    <a href="https://github.com" target="_blank">GitHub</a>
</div>
""", unsafe_allow_html=True)

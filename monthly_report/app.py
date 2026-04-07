#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小喇叭创作者运营月报系统 v1.2
修复：折线图日期格式兼容问题
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
import calendar
import os
from datetime import datetime
from typing import Dict, List, Optional

# =============================================================================
# 1. 页面配置
# =============================================================================
st.set_page_config(
    page_title="创作者运营月报系统", 
    page_icon="📊", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# 2. 常量与配置
# =============================================================================
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(WORKSPACE_DIR, "users.json")
REPORTS_DIR = os.path.join(WORKSPACE_DIR, "reports")

# 确保目录存在
os.makedirs(REPORTS_DIR, exist_ok=True)

# 默认用户（首次运行时创建）
DEFAULT_USERS = {
    "admin": {"password": "admin123", "name": "管理员"},
    "editor": {"password": "editor123", "name": "编辑"}
}

# =============================================================================
# 3. 用户管理函数
# =============================================================================
def load_users() -> Dict:
    """加载用户列表"""
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_USERS, f, ensure_ascii=False, indent=2)
        return DEFAULT_USERS
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return DEFAULT_USERS

def save_users(users: Dict):
    """保存用户列表"""
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

# =============================================================================
# 4. 样式
# =============================================================================
st.markdown("""
<style>
    .stApp { background-color: #ffffff; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* 板块标题 - 18px */
    .section-title {
        font-size: 18px;
        font-weight: 700;
        color: #1B4FD8;
        margin: 20px 0 12px 0;
        padding-bottom: 8px;
        border-bottom: 2px solid #E8EFFF;
    }
    
    /* 子标题 - 14px */
    .subsection-title {
        font-size: 14px;
        font-weight: 600;
        color: #374151;
        margin: 16px 0 10px 0;
    }
    
    /* 数据来源 */
    .data-source {
        font-size: 11px;
        color: #6B7280;
        margin-bottom: 12px;
        padding: 4px 10px;
        background: #F9FAFB;
        border-radius: 4px;
        border-left: 3px solid #D1D5DB;
        display: inline-block;
    }
    
    /* 分析框 */
    .insight-box {
        background: #F0F4FF;
        border-radius: 8px;
        padding: 14px 18px;
        margin: 12px 0;
        border-left: 4px solid #1B4FD8;
        font-size: 13px;
        color: #374151;
        line-height: 1.8;
    }
    .insight-box .risk {
        color: #DC2626;
        font-size: 12px;
        margin-top: 8px;
    }
    
    /* 页眉总结框 */
    .summary-box {
        background: rgba(27, 79, 216, 0.1);
        border-radius: 8px;
        padding: 16px 20px;
        margin: 12px 0;
        border-left: 4px solid #1B4FD8;
        font-size: 13px;
        color: #374151;
        line-height: 1.8;
    }
    
    /* KPI卡片 */
    .kpi-card {
        background: #F5F8FF;
        border-radius: 10px;
        padding: 16px;
        border: 1px solid #E0E8FF;
        text-align: center;
    }
    .kpi-label { font-size: 11px; color: #6B7280; margin-bottom: 6px; }
    .kpi-value { font-size: 22px; font-weight: 700; color: #1B4FD8; margin-bottom: 4px; }
    .kpi-sub { font-size: 11px; color: #6B7280; }
    .kpi-note { font-size: 10px; color: #9CA3AF; margin-top: 4px; }
    
    /* 颜色 */
    .up { color: #16A34A; font-weight: 600; }
    .down { color: #DC2626; font-weight: 600; }
    
    /* 链接 */
    a { color: #1B4FD8; text-decoration: none; }
    a:hover { text-decoration: underline; }
    
    /* TODO卡片 */
    .todo-card {
        background: #F5F8FF;
        border-radius: 8px;
        padding: 14px 18px;
        border: 1px solid #E0E8FF;
        margin: 8px 0;
    }
    .todo-title {
        font-size: 13px;
        font-weight: 600;
        color: #1B4FD8;
        margin-bottom: 8px;
    }
    .todo-item {
        font-size: 12px;
        color: #374151;
        line-height: 1.8;
        padding-left: 12px;
    }
    
    /* 作者卡片 */
    .author-card {
        background: #F9FAFB;
        border-radius: 8px;
        padding: 12px 16px;
        border: 1px solid #E5E7EB;
        margin: 6px 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .author-rank {
        font-size: 16px;
        font-weight: 700;
        color: #1B4FD8;
        min-width: 36px;
    }
    .author-info {
        flex: 1;
    }
    .author-name {
        font-size: 14px;
        font-weight: 600;
        color: #1B4FD8;
    }
    .author-meta {
        font-size: 11px;
        color: #6B7280;
        margin-top: 4px;
    }
    .author-stats {
        text-align: right;
    }
    .author-main-stat {
        font-size: 16px;
        font-weight: 700;
        color: #1B4FD8;
    }
    .author-sub-stat {
        font-size: 11px;
        color: #6B7280;
    }
    
    /* 作品卡片 */
    .video-card {
        background: #F9FAFB;
        border-radius: 8px;
        padding: 12px 16px;
        border: 1px solid #E5E7EB;
        margin: 6px 0;
    }
    .video-title {
        font-size: 14px;
        font-weight: 600;
        color: #1B4FD8;
        margin-bottom: 6px;
    }
    .video-meta {
        font-size: 11px;
        color: #6B7280;
    }
    .video-stats {
        display: flex;
        gap: 16px;
        margin-top: 8px;
    }
    .video-stat-item {
        font-size: 12px;
    }
    .video-stat-label {
        color: #6B7280;
    }
    .video-stat-value {
        font-weight: 600;
        color: #1B4FD8;
    }
    
    /* 活动卡片 */
    .activity-card {
        background: #F5F8FF;
        border-radius: 10px;
        padding: 16px 20px;
        border: 1px solid #E0E8FF;
        margin: 8px 0;
    }
    .activity-name {
        font-size: 14px;
        font-weight: 600;
        color: #1B4FD8;
        margin-bottom: 10px;
    }
    .activity-stats {
        font-size: 12px;
        color: #374151;
        line-height: 1.8;
    }
    
    /* 左侧导航按钮 */
    .nav-button {
        width: 100%;
        text-align: left;
        padding: 8px 12px;
        margin: 2px 0;
        border-radius: 6px;
        font-size: 13px;
        cursor: pointer;
        border: none;
        background: transparent;
        color: #374151;
    }
    .nav-button:hover {
        background: #F3F4F6;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 5. Session State
# =============================================================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'report_data' not in st.session_state:
    st.session_state.report_data = None
if 'show_register' not in st.session_state:
    st.session_state.show_register = False

# =============================================================================
# 6. 登录页面
# =============================================================================
def login_page():
    users = load_users()
    
    st.markdown("""
    <div style="max-width: 400px; margin: 60px auto; padding: 40px; border: 1px solid #eee; border-radius: 8px; text-align: center;">
        <h2>创作者月报系统 📊</h2>
        <p style="color: #6B7280;">请登录以继续</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if not st.session_state.show_register:
            # 登录表单
            with st.form("login_form"):
                username = st.text_input("用户名", placeholder="admin")
                password = st.text_input("密码", type="password", placeholder="admin123")
                submit = st.form_submit_button("登录", use_container_width=True)
                
                if submit:
                    if username in users and users[username].get("password") == password:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.rerun()
                    else:
                        st.error("用户名或密码错误")
            
            if st.button("注册新账户", use_container_width=True):
                st.session_state.show_register = True
                st.rerun()
        else:
            # 注册表单
            with st.form("register_form"):
                new_user = st.text_input("用户名", placeholder="请输入用户名")
                new_pass = st.text_input("密码", type="password", placeholder="请输入密码")
                new_name = st.text_input("昵称", placeholder="请输入昵称（可选）")
                submit = st.form_submit_button("注册", use_container_width=True)
                
                if submit:
                    if not new_user or not new_pass:
                        st.error("用户名和密码不能为空")
                    elif new_user in users:
                        st.error("用户名已存在")
                    else:
                        users[new_user] = {
                            "password": new_pass,
                            "name": new_name or new_user
                        }
                        save_users(users)
                        st.success("注册成功！请登录")
                        st.session_state.show_register = False
                        st.rerun()
            
            if st.button("返回登录", use_container_width=True):
                st.session_state.show_register = False
                st.rerun()
    
    st.stop()

if not st.session_state.logged_in:
    login_page()

# =============================================================================
# 7. 辅助函数
# =============================================================================
def safe_get(data: Dict, keys: str, default=None):
    try:
        result = data
        for key in keys.split('.'):
            result = result.get(key, {}) if isinstance(result, dict) else default
            if result is None: return default
        return result if result != {} else default
    except: return default

def render_insight_box(insight: str, risk: str = None):
    if not insight: return
    html = f'<div class="insight-box">{insight}'
    if risk: html += f'<div class="risk">⚠️ 风险提示：{risk}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

def render_kpi_cards(items: List[Dict], cols: int = 3):
    if not items: return
    columns = st.columns(cols)
    for i, item in enumerate(items):
        with columns[i % cols]:
            label = item.get('label', '-')
            value = item.get('value_display', str(item.get('value', '-')))
            note = item.get('note', '')
            direction = item.get('change_direction', '')
            pct = item.get('change_pct')
            prev = item.get('prev_display', '')
            
            if pct is not None:
                arrow = '▲' if direction == 'up' else '▼' if direction == 'down' else ''
                color = 'up' if direction == 'up' else 'down' if direction == 'down' else ''
                change = f'<span class="{color}">{arrow}{abs(pct):.1f}%</span>' if arrow else ''
                sub = f"上月 {prev} ｜ {change}" if prev else change
            else:
                sub = note
            
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}</div>
                <div class="kpi-sub">{sub}</div>
            </div>
            """, unsafe_allow_html=True)

def render_author_card(row: Dict, rank: int):
    """渲染作者卡片"""
    rank_icons = {1: "🥇", 2: "🥈", 3: "🥉"}
    rank_display = rank_icons.get(rank, f"#{rank}")
    
    author_link = row.get('author_link', '#')
    author_name = row.get('author_name', '-')
    author_id = row.get('author_id', '-')
    fans = row.get('fans_display', '-')
    platform = row.get('platform', '-')
    
    # 主指标（投稿活跃度用变化幅度，爆款用爆款数，条均播放用增幅）
    if 'chg_display' in row:
        main_stat = row.get('chg_display', '-')
        main_label = '变化幅度'
    elif 'viral_count' in row:
        main_stat = f"{row.get('viral_count', 0)}条"
        main_label = '爆款数'
    elif 'cur_avg_display' in row:
        main_stat = row.get('cur_avg_display', '-')
        main_label = '本月均播'
    else:
        main_stat = '-'
        main_label = ''
    
    st.markdown(f"""
    <div class="author-card">
        <div class="author-rank">{rank_display}</div>
        <div class="author-info">
            <div class="author-name"><a href="{author_link}" target="_blank">{author_name}</a></div>
            <div class="author-meta">ID: {author_id} ｜ 粉丝: {fans} ｜ {platform}</div>
        </div>
        <div class="author-stats">
            <div class="author-main-stat">{main_stat}</div>
            <div class="author-sub-stat">{main_label}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_video_card(row: Dict, rank: int):
    """渲染作品卡片"""
    rank_icons = {1: "🥇", 2: "🥈", 3: "🥉"}
    rank_display = rank_icons.get(rank, f"#{rank}")
    
    video_link = row.get('video_link', '#')
    title = row.get('title', '-')
    author_name = row.get('author_name', '-')
    author_link = row.get('author_link', '#')
    platform = row.get('platform', '-')
    plays = row.get('plays_display', '-')
    likes = row.get('likes_display', '-')
    
    st.markdown(f"""
    <div class="video-card">
        <div class="video-title">{rank_display} <a href="{video_link}" target="_blank">{title}</a></div>
        <div class="video-meta">
            <a href="{author_link}" target="_blank">{author_name}</a> ｜ {platform}
        </div>
        <div class="video-stats">
            <div class="video-stat-item">
                <span class="video-stat-label">播放：</span>
                <span class="video-stat-value">{plays}</span>
            </div>
            <div class="video-stat-item">
                <span class="video-stat-label">点赞：</span>
                <span class="video-stat-value">{likes}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_activity_card(name: str, data: Dict, is_main: bool = False):
    """渲染活动卡片"""
    posts = data.get('posts_display', '-')
    posts_change = data.get('posts_change', '')
    authors = data.get('authors_display', '-')
    plays = data.get('plays_display', '-')
    cpm = data.get('cpm_display', '-')
    cpm_ref = data.get('cpm_ref', '')
    
    change_html = f'<span style="color: #DC2626;">{posts_change}</span>' if posts_change else ''
    cpm_html = f'{cpm}（参考值 {cpm_ref}）' if cpm_ref else cpm
    
    st.markdown(f"""
    <div class="activity-card">
        <div class="activity-name">{name}</div>
        <div class="activity-stats">
            投稿量：<b>{posts}</b> {change_html}<br>
            参与作者：<b>{authors}</b><br>
            含三方播放：<b>{plays}</b><br>
            预估CPM：<b>{cpm_html}</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# 8. 图表函数（Plotly）
# =============================================================================
def create_bar_chart(df: pd.DataFrame, y_fixed: bool = True, title: str = ""):
    """创建柱状图（y轴锁定）"""
    fig = px.bar(df, y=df.columns[0])
    if y_fixed:
        fig.update_yaxes(fixedrange=True)
    fig.update_xaxes(fixedrange=True)
    fig.update_layout(
        title=title,
        margin=dict(l=20, r=20, t=30, b=20),
        height=300
    )
    return fig

def create_pie_chart(data: List[Dict], title: str = ""):
    """创建饼图"""
    labels = [d.get('label', d.get('type', '-')) for d in data]
    values = [d.get('value', d.get('count', 0)) for d in data]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels, 
        values=values,
        hole=0.3,
        textinfo='label+percent',
        textposition='outside'
    )])
    fig.update_layout(
        title=title,
        margin=dict(l=20, r=20, t=30, b=20),
        height=350,
        showlegend=False
    )
    return fig

def create_line_chart(dates: List[str], values: List, title: str = "", 
                      events: List[Dict] = None, y_label: str = ""):
    """创建折线图（带时间节点标记）"""
    fig = go.Figure()
    
    # 用数字索引作为 x 轴，避免日期格式兼容问题
    x_indices = list(range(len(dates)))
    
    fig.add_trace(go.Scatter(
        x=x_indices,
        y=values,
        mode='lines+markers',
        name=y_label,
        line=dict(color='#1B4FD8', width=2),
        marker=dict(size=6)
    ))
    
    # 添加时间节点垂直线
    if events:
        for event in events:
            event_date = event.get('date', '')
            event_name = event.get('name', '')
            if event_date in dates:
                # 用索引位置定位，避免日期格式兼容问题
                x_idx = dates.index(event_date)
                fig.add_vline(
                    x=x_idx,
                    line=dict(color='red', width=2, dash='dash'),
                    annotation=dict(text=event_name, textangle=0, font=dict(size=10))
                )
    
    fig.update_yaxes(fixedrange=True)
    fig.update_xaxes(fixedrange=True, tickmode='array', tickvals=x_indices[::5], ticktext=dates[::5])
    fig.update_layout(
        title=title,
        margin=dict(l=20, r=20, t=40, b=20),
        height=350,
        xaxis_title="日期",
        yaxis_title=y_label,
        hovermode='x unified'
    )
    return fig

def create_dual_bar_chart(df: pd.DataFrame, title: str = ""):
    """创建双轴柱状图"""
    fig = go.Figure()
    
    cols = df.columns.tolist()
    if len(cols) >= 2:
        fig.add_trace(go.Bar(
            x=df.index,
            y=df[cols[0]],
            name=cols[0],
            marker_color='#1B4FD8'
        ))
        if len(cols) >= 2:
            fig.add_trace(go.Bar(
                x=df.index,
                y=df[cols[1]],
                name=cols[1],
                marker_color='#93C5FD'
            ))
    
    fig.update_yaxes(fixedrange=True)
    fig.update_xaxes(fixedrange=True)
    fig.update_layout(
        title=title,
        barmode='group',
        margin=dict(l=20, r=20, t=30, b=20),
        height=350
    )
    return fig

# =============================================================================
# 9. 示例数据
# =============================================================================
EXAMPLE_DATA = {
    "report_meta": {
        "product": "**", "month": "2026-02", "prev_month": "2026-01",
        "generate_time": "2026-03-05 10:30", "stat_period": "2026-02-01 ~ 2026-02-28"
    },
    "section_0_header": {
        "title": "** · 2026年2月 · 小喇叭创作者运营月报",
        "data_source": "内容营销系统 & 大盘看板",
        "summary": "2月大盘活跃创作者1,979人，环比下降15.3%，投稿供给有所收缩。内容消费方面，含三方播放2.45亿，环比小幅下降4.5%，互动量逆势上涨13.4%，内容共鸣有所提升。活动侧，主力激励活动参与1,944人，CPM 4.49元/千次，略高于3元参考值，需关注投入产出效率。内容方面，爆款777条（≥5万播放），联动赛季节点带动优质内容爆发。\n\n📌 下月重点：\n• 重点触达腰部流失作者48人\n• 评估3月激励规则优化\n• 推进快手、小红书多平台布局"
    },
    "section_1_dashboard": {
        "enabled": True,
        "data_source": "EDT大盘看板（用户提供）",
        "insight_box": {
            "insight": "2月大盘供给与消费双降，活跃作者环比减少357人（-15.3%），投稿量降至26,551条（-20.5%）。互动量逆势上涨13.4%，显示内容质量有所提升。",
            "risk": "活跃作者和投稿量同步下滑，供给端收缩明显，需关注创作者活跃度下降趋势。"
        },
        "kpi_cards": {
            "items": [
                {"label": "活跃创作者数", "value": 1979, "value_display": "1,979", "prev_value": 2336, "prev_display": "2,336", "change_pct": 15.3, "change_direction": "down"},
                {"label": "总发布投稿量", "value": 26551, "value_display": "26,551", "prev_value": 33381, "prev_display": "33,381", "change_pct": 20.5, "change_direction": "down"},
                {"label": "审核通过稿件", "value": 24312, "value_display": "24,312", "prev_value": 25326, "prev_display": "25,326", "change_pct": 4.0, "change_direction": "down"},
                {"label": "总播放量（含三方）", "value": 245000000, "value_display": "2.45亿", "prev_value": 257000000, "prev_display": "2.57亿", "change_pct": 4.5, "change_direction": "down"},
                {"label": "总互动量（含三方）", "value": 15400, "value_display": "1.54万", "prev_value": 13600, "prev_display": "1.36万", "change_pct": 13.4, "change_direction": "up"},
                {"label": "条均播放", "value": 10077, "value_display": "10,077", "prev_value": 10016, "prev_display": "10,016", "change_pct": 0.6, "change_direction": "up"}
            ]
        },
        "daily_trend": {
            "events": [
                {"date": "02-10", "name": "新赛季开启"},
                {"date": "02-17", "name": "联动活动上线"}
            ]
        },
        "by_platform": {
            "table": [
                {"platform": "抖音", "posts": 24093, "posts_pct": 90.7, "plays": "2.13亿", "plays_pct": 86.9, "authors": 1978},
                {"platform": "快手", "posts": 2336, "posts_pct": 8.8, "plays": "3.19万", "plays_pct": 0.01, "authors": 134},
                {"platform": "小红书", "posts": 122, "posts_pct": 0.5, "plays": "32.6万", "plays_pct": 0.13, "authors": 9}
            ]
        }
    },
    "section_2_creators": {
        "enabled": True,
        "data_source": "内容营销系统 API 全量作者明细",
        "insight_box": {
            "insight": "2月留存299人，但腰部作者净减少33人（196→163），部分有影响力的创作者活跃度下降明显。增长侧亮点明显。",
            "risk": "腰部作者（1-30万粉）从196人降至163人，降幅16.8%。"
        },
        "kpi_cards": {
            "items": [
                {"label": "活跃作者总数", "value": 364, "value_display": "364", "prev_value": 404, "prev_display": "404", "change_pct": 9.9, "change_direction": "down"},
                {"label": "新增作者", "value": 65, "value_display": "65", "note": "1月未投稿→2月有投稿"},
                {"label": "流失作者", "value": 105, "value_display": "105", "note": "1月有投稿→2月未投稿"},
                {"label": "留存作者", "value": 299, "value_display": "299", "note": "两月均有投稿"}
            ]
        },
        "tier_distribution": {
            "thresholds": {"top": 300000, "mid": 10000, "top_label": "≥30万", "mid_label": "1-30万", "tail_label": "<1万"},
            "table": [
                {"tier": "头部（≥30万）", "cur_count": 12, "cur_pct": "3.3%", "prev_count": 10, "prev_pct": "2.5%", "chg_display": "▲20%"},
                {"tier": "腰部（1-30万）", "cur_count": 163, "cur_pct": "44.8%", "prev_count": 196, "prev_pct": "48.5%", "chg_display": "▼16.8%"},
                {"tier": "尾部（<1万）", "cur_count": 189, "cur_pct": "51.9%", "prev_count": 198, "prev_pct": "49.0%", "chg_display": "▼4.5%"}
            ]
        },
        "lost_author_analysis": {
            "summary": "流失105人中，尾部（<1万粉）57人（54.3%），腰部48人（45.7%），头部0人（0%）。流失作者粉丝中位数 9,868，整体属于腰尾部作者自然流动。→ 判断：有一定风险。",
            "risk": "腰部作者流失比例较高，建议针对腰部流失作者开展1v1触达。",
            "cards": [
                {"label": "流失作者腰部占比", "value": 45.7, "value_display": "45.7%", "note": "48人"},
                {"label": "流失作者粉丝中位数", "value": 9868, "value_display": "9,868", "note": "腰尾部为主"},
                {"label": "头部作者流失", "value": 0, "value_display": "0人", "note": "核心头部稳定"}
            ]
        },
        "activity_alert": {
            "cards": [
                {"label": "轻度下降（降幅0-50%）", "value": 43, "value_display": "43"},
                {"label": "重度下降（降幅>50%）", "value": 14, "value_display": "14"},
                {"label": "显著增长（增幅>50%）", "value": 113, "value_display": "113"}
            ],
            "footnote": "为避免低粉摇摆作者污染数据，投稿活跃度计算剔除2000粉以下作者"
        },
        "activity_down_top10": {
            "rows": [
                {"rank": 1, "author_name": "**阿川", "author_link": "https://www.douyin.com/example", "author_id": "YS277891", "fans_display": "11,502", "platform": "抖音", "prev_tasks": 47, "cur_tasks": 1, "chg_abs": 46, "chg_display": "▼97.9%"},
                {"rank": 2, "author_name": "i游戏风景kun", "author_link": "https://v.douyin.com/example", "author_id": "YS438516", "fans_display": "74,215", "platform": "抖音", "prev_tasks": 36, "cur_tasks": 1, "chg_abs": 35, "chg_display": "▼97.2%"},
                {"rank": 3, "author_name": "Their**佬", "author_link": "https://v.douyin.com/example", "author_id": "YS038640", "fans_display": "39,287", "platform": "抖音", "prev_tasks": 30, "cur_tasks": 1, "chg_abs": 29, "chg_display": "▼96.7%"},
                {"rank": 4, "author_name": "飞星玩家", "author_link": "https://v.douyin.com/example", "author_id": "YS285194", "fans_display": "25,361", "platform": "抖音", "prev_tasks": 50, "cur_tasks": 27, "chg_abs": 23, "chg_display": "▼46.0%"},
                {"rank": 5, "author_name": "锦荣", "author_link": "https://v.douyin.com/example", "author_id": "YS694327", "fans_display": "8,441", "platform": "抖音", "prev_tasks": 30, "cur_tasks": 9, "chg_abs": 21, "chg_display": "▼70.0%"}
            ]
        },
        "activity_up_top10": {
            "rows": [
                {"rank": 1, "author_name": "m晨韵", "author_link": "https://v.douyin.com/example", "author_id": "YS048333", "fans_display": "6,609", "platform": "抖音", "prev_tasks": 86, "cur_tasks": 157, "chg_abs": 71, "chg_display": "▲82.6%"},
                {"rank": 2, "author_name": "大众游戏", "author_link": "https://v.douyin.com/example", "author_id": "YS274937", "fans_display": "5,155", "platform": "小红书", "prev_tasks": 43, "cur_tasks": 126, "chg_abs": 83, "chg_display": "▲193.0%"},
                {"rank": 3, "author_name": "**极速-单纯的老山猪", "author_link": "https://v.douyin.com/example", "author_id": "YS236775", "fans_display": "62,842", "platform": "抖音", "prev_tasks": 181, "cur_tasks": 262, "chg_abs": 81, "chg_display": "▲44.8%"},
                {"rank": 4, "author_name": "**小夭夭", "author_link": "https://v.douyin.com/example", "author_id": "YS741295", "fans_display": "60,643", "platform": "抖音", "prev_tasks": 57, "cur_tasks": 126, "chg_abs": 69, "chg_display": "▲121.1%"},
                {"rank": 5, "author_name": "睿睿臭弟", "author_link": "https://v.douyin.com/example", "author_id": "YS440904", "fans_display": "2,399", "platform": "快手", "prev_tasks": 28, "cur_tasks": 81, "chg_abs": 53, "chg_display": "▲189.3%"}
            ]
        }
    },
    "section_3_content": {
        "enabled": True,
        "data_source": "爆款稿件表格 + 内容营销系统API",
        "insight_box": {
            "insight": "2月爆款777条（≥5万播放），较1月微增1.4%，爆款供给稳定。联动节点对播放拉动作用明显。",
            "risk": "内容类型归因字段缺失，建议下月确保导出数据含内容类型标签。"
        },
        "kpi_cards": {
            "items": [
                {"label": "爆款稿件数（≥5万播放）", "value": 777, "value_display": "777", "prev_value": 766, "prev_display": "766", "change_pct": 1.4, "change_direction": "up", "note": "占审核通过量 3.2%"},
                {"label": "2月最高播放", "value": 7800000, "value_display": "780万", "note": "Dreamscar ｜ 抖音（点击查看作品）"},
                {"label": "爆款率", "value": 3.2, "value_display": "3.2%", "note": "777/24312 通过稿"}
            ]
        },
        "viral_threshold": 50000,
        "viral_authors_top3": {
            "items": [
                {"rank": 1, "rank_icon": "🥇", "author_name": "一口游戏", "author_link": "https://v.douyin.com/example", "viral_count": 36, "author_id": "YS001723"},
                {"rank": 2, "rank_icon": "🥈", "author_name": "Their**佬", "author_link": "https://v.douyin.com/example", "viral_count": 35, "author_id": "YS038640"},
                {"rank": 3, "rank_icon": "🥉", "author_name": "**极速阿坤", "author_link": "https://v.douyin.com/example", "viral_count": 23, "author_id": "YS033543"}
            ]
        },
        "viral_videos_top10": {
            "rows": [
                {"rank": 1, "title": "别的女生刚起床VS刚起床的她", "video_link": "https://v.douyin.com/example", "platform": "抖音", "author_name": "Dreamscar", "author_link": "https://v.douyin.com/example", "author_id": "YS031563", "plays_display": "780万", "likes_display": "124,104"},
                {"rank": 2, "title": "奥迪RS7与保时捷718大婚！", "video_link": "https://v.douyin.com/example", "platform": "抖音", "author_name": "京娱汽车大电影", "author_link": "https://v.douyin.com/example", "author_id": "YS619462", "plays_display": "583万", "likes_display": "92,368"},
                {"rank": 3, "title": "真实的你", "video_link": "https://v.douyin.com/example", "platform": "抖音", "author_name": "帆江海", "author_link": "https://v.douyin.com/example", "author_id": "YS889179", "plays_display": "555万", "likes_display": "180,236"},
                {"rank": 4, "title": "哪款游戏逼出了你的极限？", "video_link": "https://v.douyin.com/example", "platform": "抖音", "author_name": "浮生未央", "author_link": "https://v.douyin.com/example", "author_id": "YS1230687", "plays_display": "414万", "likes_display": "99,336"},
                {"rank": 5, "title": "你可以叫我秦！也可以叫我，汉！", "video_link": "https://v.douyin.com/example", "platform": "抖音", "author_name": "京娱汽车大电影", "author_link": "https://v.douyin.com/example", "author_id": "YS619462", "plays_display": "373万", "likes_display": "73,794"}
            ]
        },
        "content_type_analysis": {
            "summary": "2月爆款内容以联动内容（48.8%）为主。从条均播放看，剧情/故事类以119.6万条均领跑全场。",
            "table": [
                {"type": "联动内容", "count_display": "379", "percentage": "48.8%", "avg_plays_display": "22.4万"},
                {"type": "车辆/涂装", "count_display": "178", "percentage": "22.9%", "avg_plays_display": "30.1万"},
                {"type": "游戏日常", "count_display": "166", "percentage": "21.4%", "avg_plays_display": "26.9万"},
                {"type": "攻略/资讯", "count_display": "29", "percentage": "3.7%", "avg_plays_display": "15.7万"},
                {"type": "剧情/故事", "count_display": "21", "percentage": "2.7%", "avg_plays_display": "119.6万 🔥"}
            ],
            "pie_data": [
                {"label": "联动内容", "value": 379},
                {"label": "车辆/涂装", "value": 178},
                {"label": "游戏日常", "value": 166},
                {"label": "攻略/资讯", "value": 29},
                {"label": "剧情/故事", "value": 21},
                {"label": "其他", "value": 4}
            ]
        },
        "avg_plays_up_top10": {
            "rows": [
                {"rank": 1, "author_name": "一口权佳", "author_link": "https://v.douyin.com/example", "author_id": "YS241090", "prev_avg_display": "2,973", "cur_avg_display": "126,791", "chg_display": "▲4165%", "fans_display": "11,724", "platform": "抖音"},
                {"rank": 2, "author_name": "小龙", "author_link": "https://v.douyin.com/example", "author_id": "YS1290177", "prev_avg_display": "1,160", "cur_avg_display": "29,228", "chg_display": "▲2421%", "fans_display": "3,898", "platform": "抖音"},
                {"rank": 3, "author_name": "啊这", "author_link": "https://v.douyin.com/example", "author_id": "YS279479", "prev_avg_display": "19,070", "cur_avg_display": "432,026", "chg_display": "▲2165%", "fans_display": "134,329", "platform": "抖音"}
            ]
        }
    },
    "section_4_activities": {
        "enabled": True,
        "data_source": "内容营销系统 API",
        "insight_box": {
            "insight": "2月主力活动投稿25,972条，参与1,944人，含三方播放2.45亿，CPM 4.49元，略高于参考值3元。",
            "risk": "CPM超参考值，需评估3月预算分配。"
        },
        "main_activity": {
            "cur_period": {
                "month": "2月", "name": "2月内容激励活动",
                "posts_display": "25,972", "posts_change": "▼18.8%",
                "authors_display": "1,944", "plays_display": "2.45亿",
                "cpm_display": "4.49元", "cpm_ref": "3.0元"
            },
            "prev_period": {
                "month": "1月", "name": "1月创作者内容激励活动",
                "posts_display": "31,983", "authors_display": "2,298",
                "plays_display": "1.09亿", "cpm_display": "10.10元"
            }
        },
        "sub_activities": {
            "rows": [
                {"name": "草根小喇叭-日常激励A", "posts_display": "1,234", "posts_change": "▼5.2%", "authors_display": "156", "plays_display": "123万", "cpm_display": "3.2元"},
                {"name": "草根小喇叭-日常激励B", "posts_display": "987", "posts_change": "▲12.3%", "authors_display": "89", "plays_display": "98万", "cpm_display": "2.8元"}
            ]
        },
        "commissioned": {
            "cur": {"count": 3, "name": "创作者约稿", "posts_display": "456", "posts_change": "▲42.1%", "authors_display": "23", "plays_display": "89万", "cpm_display": "5.2元"},
            "prev": {"count": 2, "name": "创作者约稿", "posts_display": "321", "authors_display": "18", "plays_display": "67万", "cpm_display": "4.8元"}
        }
    },
    "section_5_livestream": {
        "enabled": True,
        "data_source": "内容营销系统 - 直播数据",
        "insight_box": {
            "insight": "2月直播场次稳定，场均ACU表现良好。",
            "risk": "头部主播集中度较高，需关注长尾主播培养。"
        },
        "kpi_cards": {
            "items": [
                {"label": "累计开播场次", "value": 156, "value_display": "156"},
                {"label": "累计开播人数", "value": 45, "value_display": "45"},
                {"label": "累计看播人数", "value": 128000, "value_display": "12.8万"},
                {"label": "场均ACU", "value": 856, "value_display": "856"}
            ]
        },
        "tier_distribution": {
            "thresholds": {"top": 1000, "mid": 100, "top_label": "≥1000 ACU", "mid_label": "100-1000 ACU", "tail_label": "<100 ACU"},
            "table": [
                {"tier": "头部（≥1000 ACU）", "count": 5, "pct": "11.1%"},
                {"tier": "腰部（100-1000 ACU）", "count": 18, "pct": "40.0%"},
                {"tier": "尾部（<100 ACU）", "count": 22, "pct": "48.9%"}
            ],
            "pie_data": [
                {"label": "头部", "value": 5},
                {"label": "腰部", "value": 18},
                {"label": "尾部", "value": 22}
            ]
        },
        "top_streamers": {
            "rows": [
                {"rank": 1, "author_name": "主播A", "author_link": "https://v.douyin.com/example", "author_id": "YS001", "session_count": 12, "view_count_display": "5.2万", "avg_acu_display": "2,156", "fans_display": "15.6万", "platform": "抖音"},
                {"rank": 2, "author_name": "主播B", "author_link": "https://v.douyin.com/example", "author_id": "YS002", "session_count": 10, "view_count_display": "3.8万", "avg_acu_display": "1,823", "fans_display": "12.3万", "platform": "抖音"},
                {"rank": 3, "author_name": "主播C", "author_link": "https://v.douyin.com/example", "author_id": "YS003", "session_count": 9, "view_count_display": "2.9万", "avg_acu_display": "1,567", "fans_display": "9.8万", "platform": "抖音"}
            ]
        }
    },
    "section_6_core_authors": {
        "enabled": True,
        "data_source": "用户提供核心作者名单 + 内容营销系统API",
        "insight_box": {
            "insight": "核心作者贡献稳定，活跃率维持较高水平。",
            "risk": "部分核心作者活跃度下降，需重点关注。"
        },
        "kpi_cards": {
            "items": [
                {"label": "核心作者数", "value": 32, "value_display": "32"},
                {"label": "贡献稿件数", "value": 1234, "value_display": "1,234"},
                {"label": "累计播放量", "value": 56700000, "value_display": "5670万"}
            ]
        },
        "tier_distribution": {
            "table": [
                {"tier": "头部（≥30万粉）", "count": 8, "pct": "25.0%"},
                {"tier": "腰部（5-30万粉）", "count": 15, "pct": "46.9%"},
                {"tier": "尾部（<5万粉）", "count": 9, "pct": "28.1%"}
            ]
        },
        "active_pie": {"active": 28, "inactive": 4},
        "contribution_pie": {"core": 56700000, "others": 188300000}
    },
    "section_7_todos": {
        "enabled": True,
        "categories": [
            {
                "name": "重点作者管理动作",
                "priority": "高",
                "items": ["Their**佬、eggta等腰部作者优先1v1触达", "流失48名腰部作者中，粉丝≥5万的优先接触", "大众游戏、**极速-单纯的老山猪纳入约稿考察池"]
            },
            {
                "name": "供给端运营动作",
                "priority": "中",
                "items": ["活跃作者下降明显，建议增加'复活奖励'", "快手、小红书占比极低，建议评估平台专项激励"]
            },
            {
                "name": "活动效率优化",
                "priority": "中",
                "items": ["CPM超参考值，建议引入内容质量评分机制", "爆款内容类型归因下月需补充"]
            }
        ]
    }
}

# =============================================================================
# 10. PDF 导出功能
# =============================================================================
def export_pdf_page():
    """生成PDF导出页面（新窗口）"""
    if not st.session_state.report_data:
        st.warning("请先加载数据")
        return
    
    # 使用st.write配合HTML生成打印友好页面
    st.markdown("""
    <script>
    window.onload = function() {
        window.print();
    }
    </script>
    """, unsafe_allow_html=True)
    
    st.info("📄 请使用浏览器的打印功能（Ctrl+P / Cmd+P）导出PDF")

# =============================================================================
# 11. 侧边栏
# =============================================================================
with st.sidebar:
    # 用户信息
    users = load_users()
    user_info = users.get(st.session_state.username, {})
    user_name = user_info.get("name", st.session_state.username)
    
    st.markdown(f"### 👤 {user_name}")
    st.caption(f"@{st.session_state.username}")
    
    if st.button("退出登录", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.report_data = None
        st.rerun()
    
    st.divider()
    
    # 数据加载
    if st.button("👉 加载示例数据", use_container_width=True):
        st.session_state.report_data = EXAMPLE_DATA
        st.success("已加载示例数据！")
    
    uploaded_file = st.file_uploader("上传 JSON 文件", type=["json"])
    if uploaded_file:
        try:
            st.session_state.report_data = json.load(uploaded_file)
            st.success(f"已加载: {uploaded_file.name}")
        except Exception as e:
            st.error(f"解析错误: {e}")
    
    st.divider()
    
    # 左侧导航
    st.markdown("#### 📑 快速跳转")
    sections = [
        ("一、大盘概览", "section_1"),
        ("二、创作者维度", "section_2"),
        ("三、内容维度", "section_3"),
        ("四、活动维度", "section_4"),
        ("五、直播维度", "section_5"),
        ("六、核心作者", "section_6"),
        ("七、下月计划", "section_7")
    ]
    
    for name, section_id in sections:
        if st.button(name, key=f"nav_{section_id}", use_container_width=True):
            st.session_state.scroll_to = section_id
    
    st.divider()
    
    # PDF 导出
    if st.button("📥 导出 PDF", use_container_width=True):
        st.session_state.show_pdf = True
        st.rerun()

# =============================================================================
# 12. 主界面
# =============================================================================
if not st.session_state.report_data:
    st.markdown("""
    <div style="text-align: center; padding: 80px 40px;">
        <h2 style="color: #1B4FD8;">📊 创作者运营月报系统</h2>
        <p style="color: #6B7280;">请上传 JSON 文件或加载示例数据</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

data = st.session_state.report_data

# 页眉
title = safe_get(data, 'section_0_header.title', '月报标题')
st.markdown(f'<h1 style="font-size: 22px; color: #1B4FD8; margin-bottom: 8px;">{title}</h1>', unsafe_allow_html=True)

summary = safe_get(data, 'section_0_header.summary', '')
if summary:
    st.markdown(f'<div class="summary-box">{summary}</div>', unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# 板块一：大盘概览
# =============================================================================
s1 = data.get('section_1_dashboard', {})
if s1.get('enabled', True):
    with st.expander("一、大盘概览", expanded=True):
        st.markdown(f'<div class="data-source">📊 数据来源：{s1.get("data_source", "-")}</div>', unsafe_allow_html=True)
        
        if s1.get('insight_box'):
            render_insight_box(s1['insight_box'].get('insight'), s1['insight_box'].get('risk'))
        
        if s1.get('kpi_cards', {}).get('items'):
            render_kpi_cards(s1['kpi_cards']['items'], cols=3)
        
        # 日趋势图（带时间节点）
        st.markdown('<div class="subsection-title">投稿趋势</div>', unsafe_allow_html=True)
        month_str = safe_get(data, 'report_meta.month', '2026-02')
        year, month = map(int, month_str.split('-'))
        days_in_month = calendar.monthrange(year, month)[1]
        dates = [f"{month:02d}-{d:02d}" for d in range(1, days_in_month + 1)]
        
        # 预估数据
        import random
        random.seed(42)
        posts = [random.randint(700, 1400) for _ in range(days_in_month)]
        
        events = s1.get('daily_trend', {}).get('events', [])
        fig = create_line_chart(dates, posts, y_label="投稿量", events=events)
        st.plotly_chart(fig, use_container_width=True)
        
        # 分平台数据（饼图）
        by_platform = s1.get('by_platform', {})
        if by_platform.get('table'):
            st.markdown('<div class="subsection-title">分平台数据</div>', unsafe_allow_html=True)
            
            # 表格
            platform_df = pd.DataFrame(by_platform['table'])
            platform_df_display = platform_df.rename(columns={
                'platform': '平台', 'posts': '投稿量', 'posts_pct': '投稿占比%',
                'plays': '播放量', 'plays_pct': '播放占比%', 'authors': '作者数'
            })
            st.dataframe(platform_df_display, use_container_width=True, hide_index=True)
            
            # 饼图
            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="subsection-title">投稿量占比</div>', unsafe_allow_html=True)
                pie_data = [{'label': p['platform'], 'value': p['posts']} for p in by_platform['table']]
                fig = create_pie_chart(pie_data)
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.markdown('<div class="subsection-title">播放量占比</div>', unsafe_allow_html=True)
                # 播放量占比用同样的饼图
                fig = create_pie_chart(pie_data)  # 这里简化处理
                st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# 板块二：创作者维度
# =============================================================================
s2 = data.get('section_2_creators', {})
if s2.get('enabled', True):
    with st.expander("二、创作者维度", expanded=True):
        st.markdown(f'<div class="data-source">📊 数据来源：{s2.get("data_source", "-")}</div>', unsafe_allow_html=True)
        
        if s2.get('insight_box'):
            render_insight_box(s2['insight_box'].get('insight'), s2['insight_box'].get('risk'))
        
        if s2.get('kpi_cards', {}).get('items'):
            render_kpi_cards(s2['kpi_cards']['items'], cols=4)
        
        # 粉段分层
        tier = s2.get('tier_distribution', {})
        if tier.get('table'):
            thresholds = tier.get('thresholds', {})
            st.markdown(f'<div class="subsection-title">粉段分层（{thresholds.get("tail_label", "<1万")} / {thresholds.get("mid_label", "1-30万")} / {thresholds.get("top_label", "≥30万")}）</div>', unsafe_allow_html=True)
            tier_df = pd.DataFrame(tier['table'])
            tier_df_display = tier_df.rename(columns={
                'tier': '层级', 'cur_count': '人数', 'cur_pct': '占比',
                'prev_count': '上月人数', 'prev_pct': '上月占比', 'chg_display': '变化'
            })
            st.dataframe(tier_df_display, use_container_width=True, hide_index=True)
        
        # 流失作者归因
        lost = s2.get('lost_author_analysis', {})
        if lost:
            st.markdown('<div class="subsection-title">流失作者归因分析</div>', unsafe_allow_html=True)
            render_insight_box(lost.get('summary'), lost.get('risk'))
            if lost.get('cards'):
                render_kpi_cards(lost['cards'], cols=3)
        
        # 活跃度预警
        alert = s2.get('activity_alert', {})
        if alert.get('cards'):
            st.markdown('<div class="subsection-title">投稿活跃度预警</div>', unsafe_allow_html=True)
            render_kpi_cards(alert['cards'], cols=3)
            if alert.get('footnote'):
                st.markdown(f"<small style='color: #6B7280;'>{alert['footnote']}</small>", unsafe_allow_html=True)
        
        # Top10表格改卡片
        for key, title_text in [('activity_down_top10', '投稿活跃度 降低 Top 10'), ('activity_up_top10', '投稿活跃度 增加 Top 10')]:
            table = s2.get(key, {})
            if table.get('rows'):
                st.markdown(f'<div class="subsection-title">{title_text}</div>', unsafe_allow_html=True)
                for i, row in enumerate(table['rows'][:5], 1):  # 只展示Top5
                    render_author_card(row, row.get('rank', i))

# =============================================================================
# 板块三：内容维度
# =============================================================================
s3 = data.get('section_3_content', {})
if s3.get('enabled', True):
    with st.expander("三、内容维度", expanded=True):
        st.markdown(f'<div class="data-source">📊 数据来源：{s3.get("data_source", "-")}</div>', unsafe_allow_html=True)
        
        if s3.get('insight_box'):
            render_insight_box(s3['insight_box'].get('insight'), s3['insight_box'].get('risk'))
        
        if s3.get('kpi_cards', {}).get('items'):
            render_kpi_cards(s3['kpi_cards']['items'], cols=3)
        
        # 爆款作者Top3
        top3 = s3.get('viral_authors_top3', {})
        if top3.get('items'):
            st.markdown('<div class="subsection-title">爆款作者 Top 3</div>', unsafe_allow_html=True)
            cols = st.columns(3)
            for i, item in enumerate(top3['items']):
                with cols[i]:
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div style="font-size: 14px; font-weight: 600; color: #1B4FD8;">{item.get('rank_icon', '')} Top {item.get('rank', i+1)}</div>
                        <div style="font-size: 14px; font-weight: 600; color: #1B4FD8;"><a href="{item.get('author_link', '#')}" target="_blank">{item.get('author_name', '-')}</a></div>
                        <div class="kpi-value">{item.get('viral_count', 0)}</div>
                        <div class="kpi-note">条爆款 ｜ {item.get('author_id', '-')}</div>
                    </div>
                    """, unsafe_allow_html=True)
        
        # 爆款稿件Top10（卡片）
        videos = s3.get('viral_videos_top10', {})
        if videos.get('rows'):

            st.markdown(f'<div class="subsection-title">爆款稿件 Top 10（≥{s3.get("viral_threshold", 50000)//10000}万播放）</div>', unsafe_allow_html=True)
            for i, row in enumerate(videos['rows'][:5], 1):  # 展示Top5
                render_video_card(row, row.get('rank', i))
        
        # 内容类型归因（饼图）
        content_type = s3.get('content_type_analysis', {})
        if content_type.get('table'):
            st.markdown('<div class="subsection-title">爆款内容类型归因</div>', unsafe_allow_html=True)
            if content_type.get('summary'):
                render_insight_box(content_type['summary'])
            
            # 表格
            type_df = pd.DataFrame(content_type['table'])
            type_df_display = type_df.rename(columns={
                'type': '内容类型', 'count_display': '爆款条数', 
                'percentage': '占比', 'avg_plays_display': '条均播放'
            })
            st.dataframe(type_df_display, use_container_width=True, hide_index=True)
            
            # 饼图
            if content_type.get('pie_data'):
                fig = create_pie_chart(content_type['pie_data'], title="爆款内容类型分布")
                st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# 板块四：活动维度
# =============================================================================
s4 = data.get('section_4_activities', {})
if s4.get('enabled', True):
    with st.expander("四、活动维度", expanded=True):
        st.markdown(f'<div class="data-source">📊 数据来源：{s4.get("data_source", "-")}</div>', unsafe_allow_html=True)
        
        if s4.get('insight_box'):
            render_insight_box(s4['insight_box'].get('insight'), s4['insight_box'].get('risk'))
        
        # 主力活动对比（卡片）
        main = s4.get('main_activity', {})
        if main.get('cur_period'):
            st.markdown('<div class="subsection-title">主力活动对比</div>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            
            cur = main['cur_period']
            with col1:
                render_activity_card(f"当月：{cur.get('name', '-')}", cur, is_main=True)
            
            prev = main.get('prev_period', {})
            if prev:
                with col2:
                    render_activity_card(f"上月：{prev.get('name', '-')}", prev)
        
        # 子活动（卡片）
        sub = s4.get('sub_activities', {})
        if sub.get('rows'):
            st.markdown('<div class="subsection-title">其他活动 — 草根小喇叭（子活动）</div>', unsafe_allow_html=True)
            for row in sub['rows']:
                render_activity_card(row.get('name', '-'), row)
        
        # 创作者约稿（卡片）
        comm = s4.get('commissioned', {})
        if comm:
            st.markdown('<div class="subsection-title">创作者约稿</div>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            cur = comm.get('cur', {})
            if cur:
                with col1:
                    render_activity_card(f"当月（{cur.get('count', 0)}个活动）", cur)
            prev = comm.get('prev', {})
            if prev:
                with col2:
                    render_activity_card(f"上月（{prev.get('count', 0)}个活动）", prev)

# =============================================================================
# 板块五：直播维度
# =============================================================================
s5 = data.get('section_5_livestream', {})
if s5.get('enabled', False):
    with st.expander("五、直播维度", expanded=True):
        st.markdown(f'<div class="data-source">📊 数据来源：{s5.get("data_source", "-")}</div>', unsafe_allow_html=True)
        
        if s5.get('insight_box'):
            render_insight_box(s5['insight_box'].get('insight'), s5['insight_box'].get('risk'))
        
        if s5.get('kpi_cards', {}).get('items'):
            render_kpi_cards(s5['kpi_cards']['items'], cols=4)
        
        # 主播分层（卡片 + 饼图）
        tier = s5.get('tier_distribution', {})
        if tier.get('table'):
            st.markdown('<div class="subsection-title">主播分层</div>', unsafe_allow_html=True)
            
            # KPI卡片展示
            tier_cards = []
            for t in tier['table']:
                tier_cards.append({
                    'label': t.get('tier', '-'),
                    'value_display': f"{t.get('count', 0)}人",
                    'note': t.get('pct', '-')
                })
            render_kpi_cards(tier_cards, cols=3)
            
            # 饼图
            if tier.get('pie_data'):
                fig = create_pie_chart(tier['pie_data'], title="主播分层分布")
                st.plotly_chart(fig, use_container_width=True)
        
        # Top主播（卡片）
        top = s5.get('top_streamers', {})
        if top.get('rows'):
            st.markdown('<div class="subsection-title">直播作者 Top 10</div>', unsafe_allow_html=True)
            for i, row in enumerate(top['rows'][:5], 1):
                render_author_card(row, row.get('rank', i))

elif s5.get('enabled') is False:
    with st.expander("五、直播维度", expanded=False):
        st.info("该板块未启用")

# =============================================================================
# 板块六：核心作者分析
# =============================================================================
s6 = data.get('section_6_core_authors', {})
if s6.get('enabled', False):
    with st.expander("六、核心作者分析", expanded=True):
        st.markdown(f'<div class="data-source">📊 数据来源：{s6.get("data_source", "-")}</div>', unsafe_allow_html=True)
        
        if s6.get('insight_box'):
            render_insight_box(s6['insight_box'].get('insight'), s6['insight_box'].get('risk'))
        
        if s6.get('kpi_cards', {}).get('items'):
            render_kpi_cards(s6['kpi_cards']['items'], cols=3)
        
        tier = s6.get('tier_distribution', {})
        if tier.get('table'):
            st.markdown('<div class="subsection-title">作者分层</div>', unsafe_allow_html=True)
            tier_df = pd.DataFrame(tier['table'])
            tier_df_display = tier_df.rename(columns={'tier': '层级', 'count': '人数', 'pct': '占比'})
            st.dataframe(tier_df_display, use_container_width=True, hide_index=True)
        
        # 活跃人数占比（饼图）
        active = s6.get('active_pie', {})
        if active:
            st.markdown('<div class="subsection-title">活跃人数占比</div>', unsafe_allow_html=True)
            pie_data = [
                {'label': '活跃', 'value': active.get('active', 0)},
                {'label': '不活跃', 'value': active.get('inactive', 0)}
            ]
            fig = create_pie_chart(pie_data, title="活跃人数分布")
            st.plotly_chart(fig, use_container_width=True)
        
        # 播放量贡献占比（饼图）
        contrib = s6.get('contribution_pie', {})
        if contrib:
            st.markdown('<div class="subsection-title">播放量贡献占比</div>', unsafe_allow_html=True)
            pie_data = [
                {'label': '核心作者', 'value': contrib.get('core', 0)},
                {'label': '其他作者', 'value': contrib.get('others', 0)}
            ]
            fig = create_pie_chart(pie_data, title="播放量贡献分布")
            st.plotly_chart(fig, use_container_width=True)

elif s6.get('enabled') is False:
    with st.expander("六、核心作者分析", expanded=False):
        st.info("该板块未启用")

# =============================================================================
# 板块七：下月重点计划
# =============================================================================
s7 = data.get('section_7_todos', {})
if s7.get('enabled', True):
    with st.expander("七、下月重点计划", expanded=True):
        categories = s7.get('categories', [])
        if categories:
            for cat in categories:
                priority_color = {'高': '#DC2626', '中': '#F59E0B', '低': '#6B7280'}.get(cat.get('priority', '中'), '#374151')
                st.markdown(f"""
                <div class="todo-card">
                    <div class="todo-title" style="color: {priority_color};">{cat.get('name', '-')}（{cat.get('priority', '中')}优先级）</div>
                    <div class="todo-item">{'<br>'.join(['• ' + item for item in cat.get('items', [])])}</div>
                </div>
                """, unsafe_allow_html=True)

# =============================================================================
# 页脚
# =============================================================================
st.markdown("---")
st.markdown(f'<div style="text-align: center; color: #9CA3AF; font-size: 11px;">创作者运营月报系统 v1.2 ｜ {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>', unsafe_allow_html=True)

# =============================================================================
# PDF 导出处理
# =============================================================================
if st.session_state.get('show_pdf'):
    st.session_state.show_pdf = False
    # 使用JavaScript打开打印对话框
    st.markdown("""
    <script>
        window.print();
    </script>
    """, unsafe_allow_html=True)

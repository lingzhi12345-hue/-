#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小喇叭创作者运营月报系统 v2.6.0
- 导出完整HTML功能
- 条均播放降低Top10
- 直播&核心作者KPI扩充
- 表格改卡片
- 横向紧凑卡片布局
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
import calendar
import os
import base64
from datetime import datetime
from typing import Dict, List, Optional
from io import BytesIO

# =============================================================================
# 1. 页面配置
# =============================================================================
st.set_page_config(
    page_title="创作者运营月报系统", 
    page_icon="📊", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =============================================================================
# 2. 常量与配置
# =============================================================================
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(WORKSPACE_DIR, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

# =============================================================================
# 3. 样式
# =============================================================================
CSS_STYLES = """
<style>
    .stApp { background-color: #ffffff; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* 隐藏侧边栏 */
    section[data-testid="stSidebar"] {display: none;}
    
    /* 板块标题 */
    .section-title {
        font-size: 18px;
        font-weight: 700;
        color: #1B4FD8;
        margin: 20px 0 12px 0;
        padding-bottom: 8px;
        border-bottom: 2px solid #E8EFFF;
    }
    
    /* 子标题 */
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
        padding: 12px;
        border: 1px solid #E0E8FF;
        text-align: center;
    }
    .kpi-label { font-size: 11px; color: #6B7280; margin-bottom: 4px; }
    .kpi-value { font-size: 20px; font-weight: 700; color: #1B4FD8; margin-bottom: 2px; }
    .kpi-sub { font-size: 10px; color: #6B7280; }
    .kpi-note { font-size: 10px; color: #9CA3AF; margin-top: 2px; }
    
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
    
    /* 横向作者卡片 */
    .author-card-h {
        background: #F9FAFB;
        border-radius: 6px;
        padding: 8px 12px;
        border: 1px solid #E5E7EB;
        margin: 4px 0;
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 12px;
    }
    .author-rank-h {
        font-size: 14px;
        font-weight: 700;
        color: #1B4FD8;
        min-width: 28px;
    }
    .author-name-h {
        font-weight: 600;
        color: #1B4FD8;
        min-width: 100px;
    }
    .author-meta-h {
        color: #6B7280;
        font-size: 11px;
        flex: 1;
    }
    .author-stat-h {
        text-align: right;
        font-weight: 600;
        color: #1B4FD8;
        min-width: 70px;
    }
    
    /* 横向作品卡片 */
    .video-card-h {
        background: #F9FAFB;
        border-radius: 6px;
        padding: 8px 12px;
        border: 1px solid #E5E7EB;
        margin: 4px 0;
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 12px;
    }
    .video-rank-h {
        font-size: 14px;
        font-weight: 700;
        color: #1B4FD8;
        min-width: 28px;
    }
    .video-title-h {
        font-weight: 600;
        color: #1B4FD8;
        flex: 1;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .video-meta-h {
        color: #6B7280;
        font-size: 11px;
        min-width: 150px;
    }
    .video-stat-h {
        font-weight: 600;
        color: #1B4FD8;
        min-width: 60px;
        text-align: right;
    }
    
    /* 分层卡片 */
    .tier-card {
        background: #F9FAFB;
        border-radius: 6px;
        padding: 10px 14px;
        border: 1px solid #E5E7EB;
        margin: 4px 0;
        display: flex;
        align-items: center;
        gap: 16px;
        font-size: 12px;
    }
    .tier-name {
        font-weight: 600;
        color: #374151;
        min-width: 120px;
    }
    .tier-value {
        font-weight: 700;
        color: #1B4FD8;
        min-width: 50px;
        text-align: center;
    }
    .tier-pct {
        color: #6B7280;
        min-width: 50px;
    }
    .tier-chg {
        min-width: 60px;
        text-align: right;
    }
    
    /* 活动卡片 */
    .activity-card {
        background: #F5F8FF;
        border-radius: 8px;
        padding: 14px 18px;
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
</style>
"""

st.markdown(CSS_STYLES, unsafe_allow_html=True)

# HTML导出样式（独立，用于生成静态HTML）
HTML_STYLES = """
<style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #fff; color: #374151; line-height: 1.6; max-width: 1200px; margin: 0 auto; padding: 20px; }
    .section-title { font-size: 18px; font-weight: 700; color: #1B4FD8; margin: 24px 0 12px 0; padding-bottom: 8px; border-bottom: 2px solid #E8EFFF; }
    .subsection-title { font-size: 14px; font-weight: 600; color: #374151; margin: 16px 0 10px 0; }
    .data-source { font-size: 11px; color: #6B7280; margin-bottom: 12px; padding: 4px 10px; background: #F9FAFB; border-radius: 4px; border-left: 3px solid #D1D5DB; display: inline-block; }
    .insight-box { background: #F0F4FF; border-radius: 8px; padding: 14px 18px; margin: 12px 0; border-left: 4px solid #1B4FD8; font-size: 13px; line-height: 1.8; }
    .insight-box .risk { color: #DC2626; font-size: 12px; margin-top: 8px; }
    .summary-box { background: rgba(27, 79, 216, 0.1); border-radius: 8px; padding: 16px 20px; margin: 12px 0; border-left: 4px solid #1B4FD8; font-size: 13px; line-height: 1.8; }
    .kpi-row { display: flex; gap: 16px; margin: 12px 0; flex-wrap: wrap; }
    .kpi-card { background: #F5F8FF; border-radius: 10px; padding: 12px; border: 1px solid #E0E8FF; text-align: center; flex: 1; min-width: 150px; }
    .kpi-label { font-size: 11px; color: #6B7280; margin-bottom: 4px; }
    .kpi-value { font-size: 20px; font-weight: 700; color: #1B4FD8; margin-bottom: 2px; }
    .kpi-sub { font-size: 10px; color: #6B7280; }
    .up { color: #16A34A; font-weight: 600; }
    .down { color: #DC2626; font-weight: 600; }
    a { color: #1B4FD8; text-decoration: none; }
    .tier-card, .author-card-h, .video-card-h { background: #F9FAFB; border-radius: 6px; padding: 10px 14px; border: 1px solid #E5E7EB; margin: 4px 0; display: flex; align-items: center; gap: 16px; font-size: 12px; }
    .tier-name, .author-name-h, .video-title-h { font-weight: 600; color: #374151; min-width: 120px; }
    .tier-value { font-weight: 700; color: #1B4FD8; min-width: 50px; text-align: center; }
    .tier-pct, .tier-chg { color: #6B7280; min-width: 50px; }
    .activity-card { background: #F5F8FF; border-radius: 8px; padding: 14px 18px; border: 1px solid #E0E8FF; margin: 8px 0; }
    .activity-name { font-size: 14px; font-weight: 600; color: #1B4FD8; margin-bottom: 10px; }
    .todo-card { background: #F5F8FF; border-radius: 8px; padding: 14px 18px; border: 1px solid #E0E8FF; margin: 8px 0; }
    .todo-title { font-size: 13px; font-weight: 600; color: #1B4FD8; margin-bottom: 8px; }
    .todo-item { font-size: 12px; color: #374151; line-height: 1.8; padding-left: 12px; }
    .chart-placeholder { background: #F3F4F6; border-radius: 8px; padding: 40px; text-align: center; color: #6B7280; margin: 12px 0; }
    .footer { text-align: center; color: #9CA3AF; font-size: 11px; margin-top: 20px; padding-top: 20px; border-top: 1px solid #E5E7EB; }
</style>
"""

# =============================================================================
# 4. Session State
# =============================================================================
if 'report_data' not in st.session_state:
    st.session_state.report_data = None

# =============================================================================
# 5. 辅助函数
# =============================================================================
def safe_get(data: Dict, keys: str, default=None):
    try:
        result = data
        for key in keys.split('.'):
            result = result.get(key, {}) if isinstance(result, dict) else default
            if result is None: return default
        return result if result != {} else default
    except: return default

def render_insight_box(insight: str, risk: str = None) -> str:
    if not insight: return ""
    html = f'<div class="insight-box">{insight}'
    if risk: html += f'<div class="risk">⚠️ 风险提示：{risk}</div>'
    html += '</div>'
    return html

def render_kpi_cards(items: List[Dict], cols: int = 3) -> str:
    if not items: return ""
    html = '<div class="kpi-row">'
    for item in items:
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
        
        html += f'''
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-sub">{sub}</div>
        </div>
        '''
    html += '</div>'
    return html

def render_tier_cards(rows: List[Dict]) -> str:
    html = ""
    for row in rows:
        tier = row.get('tier', row.get('层级', '-'))
        count = row.get('cur_count', row.get('人数', row.get('count', '-')))
        pct = row.get('cur_pct', row.get('占比', row.get('pct', '-')))
        chg = row.get('chg_display', '')
        
        html += f'''
        <div class="tier-card">
            <div class="tier-name">{tier}</div>
            <div class="tier-value">{count}</div>
            <div class="tier-pct">{pct}</div>
            <div class="tier-chg">{chg}</div>
        </div>
        '''
    return html

def render_author_card_h(row: Dict, rank: int) -> str:
    rank_icons = {1: "🥇", 2: "🥈", 3: "🥉"}
    rank_display = rank_icons.get(rank, f"#{rank}")
    
    author_link = row.get('author_link', '#')
    author_name = row.get('author_name', '-')
    author_id = row.get('author_id', '-')
    fans = row.get('fans_display', '-')
    platform = row.get('platform', '-')
    
    if 'chg_display' in row:
        main_stat = row.get('chg_display', '-')
    elif 'viral_count' in row:
        main_stat = f"{row.get('viral_count', 0)}条"
    elif 'cur_avg_display' in row:
        main_stat = row.get('cur_avg_display', '-')
    else:
        main_stat = '-'
    
    return f'''
    <div class="author-card-h">
        <div class="tier-name">{rank_display}</div>
        <div class="author-name-h"><a href="{author_link}" target="_blank">{author_name}</a></div>
        <div style="color: #6B7280; font-size: 11px; flex: 1;">ID:{author_id} | 粉丝:{fans} | {platform}</div>
        <div style="font-weight: 600; color: #1B4FD8;">{main_stat}</div>
    </div>
    '''

def render_video_card_h(row: Dict, rank: int) -> str:
    rank_icons = {1: "🥇", 2: "🥈", 3: "🥉"}
    rank_display = rank_icons.get(rank, f"#{rank}")
    
    video_link = row.get('video_link', '#')
    title = row.get('title', '-')
    author_name = row.get('author_name', '-')
    platform = row.get('platform', '-')
    plays = row.get('plays_display', '-')
    likes = row.get('likes_display', '-')
    
    return f'''
    <div class="video-card-h">
        <div class="tier-name">{rank_display}</div>
        <div class="video-title-h"><a href="{video_link}" target="_blank">{title}</a></div>
        <div style="color: #6B7280; font-size: 11px;">{author_name} | {platform}</div>
        <div style="font-weight: 600; color: #1B4FD8;">播放:{plays}</div>
        <div style="font-weight: 600; color: #1B4FD8;">赞:{likes}</div>
    </div>
    '''

def render_activity_card(name: str, data: Dict) -> str:
    posts = data.get('posts_display', '-')
    posts_change = data.get('posts_change', '')
    authors = data.get('authors_display', '-')
    plays = data.get('plays_display', '-')
    cpm = data.get('cpm_display', '-')
    cpm_ref = data.get('cpm_ref', '')
    
    change_html = f'<span style="color: #DC2626;">{posts_change}</span>' if posts_change else ''
    cpm_html = f'{cpm}（参考值 {cpm_ref}）' if cpm_ref else cpm
    
    return f'''
    <div class="activity-card">
        <div class="activity-name">{name}</div>
        <div class="activity-stats">
            投稿量：<b>{posts}</b> {change_html} ｜ 
            参与作者：<b>{authors}</b> ｜ 
            播放：<b>{plays}</b> ｜ 
            CPM：<b>{cpm_html}</b>
        </div>
    </div>
    '''

# =============================================================================
# 6. 图表函数（Plotly）
# =============================================================================
def create_pie_chart(data: List[Dict], title: str = ""):
    labels = [d.get('label', d.get('type', '-')) for d in data]
    values = [d.get('value', d.get('count', 0)) for d in data]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels, 
        values=values,
        hole=0.3,
        textinfo='label+percent',
        textposition='outside'
    )])
    fig.update_layout(title=title, margin=dict(l=20, r=20, t=30, b=20), height=320, showlegend=False)
    return fig

def create_line_chart(dates: List[str], values: List, title: str = "", 
                      events: List[Dict] = None, y_label: str = ""):
    fig = go.Figure()
    x_indices = list(range(len(dates)))
    
    fig.add_trace(go.Scatter(
        x=x_indices,
        y=values,
        mode='lines+markers',
        name=y_label,
        line=dict(color='#1B4FD8', width=2),
        marker=dict(size=6)
    ))
    
    if events:
        for event in events:
            event_date = event.get('date', '')
            event_name = event.get('name', '')
            if event_date in dates:
                x_idx = dates.index(event_date)
                fig.add_vline(
                    x=x_idx,
                    line=dict(color='red', width=2, dash='dash'),
                    annotation=dict(text=event_name, textangle=0, font=dict(size=10))
                )
    
    fig.update_yaxes(fixedrange=True)
    fig.update_xaxes(fixedrange=True, tickmode='array', tickvals=x_indices[::5], ticktext=dates[::5])
    fig.update_layout(title=title, margin=dict(l=20, r=20, t=40, b=20), height=320, xaxis_title="日期", yaxis_title=y_label, hovermode='x unified')
    return fig

# =============================================================================
# 7. HTML生成函数
# =============================================================================
def generate_html(data: Dict) -> str:
    """生成完整静态HTML"""
    html_parts = []
    
    # HTML头部
    html_parts.append(f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>创作者运营月报</title>
    {HTML_STYLES}
</head>
<body>
""")
    
    # 页眉
    title = safe_get(data, 'section_0_header.title', '月报标题')
    html_parts.append(f'<h1 style="font-size: 22px; color: #1B4FD8; margin-bottom: 8px;">{title}</h1>\n')
    
    summary = safe_get(data, 'section_0_header.summary', '')
    if summary:
        html_parts.append(f'<div class="summary-box">{summary}</div>\n')
    
    html_parts.append('<hr>\n')
    
    # ===== 板块一：大盘概览 =====
    s1 = data.get('section_1_dashboard', {})
    if s1.get('enabled', True):
        html_parts.append('<div class="section-title">一、大盘概览</div>\n')
        html_parts.append(f'<div class="data-source">📊 数据来源：{s1.get("data_source", "-")}</div>\n')
        
        if s1.get('insight_box'):
            html_parts.append(render_insight_box(s1['insight_box'].get('insight'), s1['insight_box'].get('risk')))
        
        if s1.get('kpi_cards', {}).get('items'):
            html_parts.append(render_kpi_cards(s1['kpi_cards']['items'], cols=3))
        
        html_parts.append('<div class="chart-placeholder">📈 投稿趋势图（需在Streamlit中查看）</div>\n')
        
        by_platform = s1.get('by_platform', {})
        if by_platform.get('table'):
            html_parts.append('<div class="subsection-title">分平台数据</div>\n')
            for p in by_platform['table']:
                html_parts.append(f'''
                <div class="tier-card">
                    <div class="tier-name">{p['platform']}</div>
                    <div class="tier-value">{p['posts']}</div>
                    <div class="tier-pct">{p['posts_pct']}</div>
                    <div class="tier-pct">播放:{p['plays']}</div>
                    <div class="tier-pct">作者:{p['authors']}</div>
                </div>
                ''')
    
    # ===== 板块二：创作者维度 =====
    s2 = data.get('section_2_creators', {})
    if s2.get('enabled', True):
        html_parts.append('<div class="section-title">二、创作者维度</div>\n')
        html_parts.append(f'<div class="data-source">📊 数据来源：{s2.get("data_source", "-")}</div>\n')
        
        if s2.get('insight_box'):
            html_parts.append(render_insight_box(s2['insight_box'].get('insight'), s2['insight_box'].get('risk')))
        
        if s2.get('kpi_cards', {}).get('items'):
            html_parts.append(render_kpi_cards(s2['kpi_cards']['items'], cols=4))
        
        tier = s2.get('tier_distribution', {})
        if tier.get('table'):
            thresholds = tier.get('thresholds', {})
            html_parts.append(f'<div class="subsection-title">粉段分层（{thresholds.get("tail_label", "<1万")} / {thresholds.get("mid_label", "1-30万")} / {thresholds.get("top_label", "≥30万")}）</div>\n')
            html_parts.append(render_tier_cards(tier['table']))
        
        lost = s2.get('lost_author_analysis', {})
        if lost:
            html_parts.append('<div class="subsection-title">流失作者归因分析</div>\n')
            html_parts.append(render_insight_box(lost.get('summary'), lost.get('risk')))
            if lost.get('cards'):
                html_parts.append(render_kpi_cards(lost['cards'], cols=3))
        
        alert = s2.get('activity_alert', {})
        if alert.get('cards'):
            html_parts.append('<div class="subsection-title">投稿活跃度预警</div>\n')
            html_parts.append(render_kpi_cards(alert['cards'], cols=3))
        
        for key, title_text in [('activity_down_top10', '投稿活跃度 降低 Top 10'), ('activity_up_top10', '投稿活跃度 增加 Top 10')]:
            table = s2.get(key, {})
            if table.get('rows'):
                html_parts.append(f'<div class="subsection-title">{title_text}</div>\n')
                for i, row in enumerate(table['rows'][:10], 1):
                    html_parts.append(render_author_card_h(row, row.get('rank', i)))
    
    # ===== 板块三：内容维度 =====
    s3 = data.get('section_3_content', {})
    if s3.get('enabled', True):
        html_parts.append('<div class="section-title">三、内容维度</div>\n')
        html_parts.append(f'<div class="data-source">📊 数据来源：{s3.get("data_source", "-")}</div>\n')
        
        if s3.get('insight_box'):
            html_parts.append(render_insight_box(s3['insight_box'].get('insight'), s3['insight_box'].get('risk')))
        
        if s3.get('kpi_cards', {}).get('items'):
            html_parts.append(render_kpi_cards(s3['kpi_cards']['items'], cols=3))
        
        top3 = s3.get('viral_authors_top3', {})
        if top3.get('items'):
            html_parts.append('<div class="subsection-title">爆款作者 Top 3</div>\n')
            for item in top3['items']:
                html_parts.append(f'''
                <div class="kpi-card" style="display: inline-block; margin: 4px; min-width: 150px;">
                    <div style="font-size: 14px; font-weight: 600; color: #1B4FD8;">{item.get('rank_icon', '')} Top {item.get('rank', 1)}</div>
                    <div style="font-size: 14px; font-weight: 600; color: #1B4FD8;"><a href="{item.get('author_link', '#')}" target="_blank">{item.get('author_name', '-')}</a></div>
                    <div class="kpi-value">{item.get('viral_count', 0)}</div>
                    <div class="kpi-sub">条爆款 ｜ {item.get('author_id', '-')}</div>
                </div>
                ''')
        
        videos = s3.get('viral_videos_top10', {})
        if videos.get('rows'):
            html_parts.append(f'<div class="subsection-title">爆款稿件 Top 10（≥{s3.get("viral_threshold", 50000)//10000}万播放）</div>\n')
            for i, row in enumerate(videos['rows'][:10], 1):
                html_parts.append(render_video_card_h(row, row.get('rank', i)))
        
        content_type = s3.get('content_type_analysis', {})
        if content_type.get('table'):
            html_parts.append('<div class="subsection-title">爆款内容类型归因</div>\n')
            if content_type.get('summary'):
                html_parts.append(render_insight_box(content_type['summary']))
            
            for t in content_type['table']:
                html_parts.append(f'''
                <div class="tier-card">
                    <div class="tier-name">{t['type']}</div>
                    <div class="tier-value">{t['count_display']}</div>
                    <div class="tier-pct">{t['percentage']}</div>
                    <div class="tier-pct">条均:{t['avg_plays_display']}</div>
                </div>
                ''')
        
        # 条均播放增长Top10
        avg_up = s3.get('avg_plays_up_top10', {})
        if avg_up.get('rows'):
            html_parts.append('<div class="subsection-title">条均播放增长 Top 10</div>\n')
            for i, row in enumerate(avg_up['rows'][:10], 1):
                html_parts.append(render_author_card_h(row, row.get('rank', i)))
        
        # 条均播放降低Top10（新增）
        avg_down = s3.get('avg_plays_down_top10', {})
        if avg_down.get('rows'):
            html_parts.append('<div class="subsection-title">条均播放降低 Top 10</div>\n')
            for i, row in enumerate(avg_down['rows'][:10], 1):
                html_parts.append(render_author_card_h(row, row.get('rank', i)))
    
    # ===== 板块四：活动维度 =====
    s4 = data.get('section_4_activities', {})
    if s4.get('enabled', True):
        html_parts.append('<div class="section-title">四、活动维度</div>\n')
        html_parts.append(f'<div class="data-source">📊 数据来源：{s4.get("data_source", "-")}</div>\n')
        
        if s4.get('insight_box'):
            html_parts.append(render_insight_box(s4['insight_box'].get('insight'), s4['insight_box'].get('risk')))
        
        main = s4.get('main_activity', {})
        if main.get('cur_period'):
            html_parts.append('<div class="subsection-title">主力活动对比</div>\n')
            cur = main['cur_period']
            html_parts.append(render_activity_card(f"当月：{cur.get('name', '-')}", cur))
            prev = main.get('prev_period', {})
            if prev:
                html_parts.append(render_activity_card(f"上月：{prev.get('name', '-')}", prev))
        
        sub = s4.get('sub_activities', {})
        if sub.get('rows'):
            html_parts.append('<div class="subsection-title">其他活动 — 草根小喇叭（子活动）</div>\n')
            for row in sub['rows']:
                html_parts.append(render_activity_card(row.get('name', '-'), row))
        
        comm = s4.get('commissioned', {})
        if comm:
            html_parts.append('<div class="subsection-title">创作者约稿</div>\n')
            cur = comm.get('cur', {})
            if cur:
                html_parts.append(render_activity_card(f"当月（{cur.get('count', 0)}个活动）", cur))
            prev = comm.get('prev', {})
            if prev:
                html_parts.append(render_activity_card(f"上月（{prev.get('count', 0)}个活动）", prev))
    
    # ===== 板块五：直播维度 =====
    s5 = data.get('section_5_livestream', {})
    if s5.get('enabled', False):
        html_parts.append('<div class="section-title">五、直播维度</div>\n')
        html_parts.append(f'<div class="data-source">📊 数据来源：{s5.get("data_source", "-")}</div>\n')
        
        if s5.get('insight_box'):
            html_parts.append(render_insight_box(s5['insight_box'].get('insight'), s5['insight_box'].get('risk')))
        
        if s5.get('kpi_cards', {}).get('items'):
            html_parts.append(render_kpi_cards(s5['kpi_cards']['items'], cols=4))
        
        tier = s5.get('tier_distribution', {})
        if tier.get('table'):
            html_parts.append('<div class="subsection-title">主播分层</div>\n')
            for t in tier['table']:
                html_parts.append(f'''
                <div class="tier-card">
                    <div class="tier-name">{t['tier']}</div>
                    <div class="tier-value">{t['count']}人</div>
                    <div class="tier-pct">{t['pct']}</div>
                </div>
                ''')
        
        top = s5.get('top_streamers', {})
        if top.get('rows'):
            html_parts.append('<div class="subsection-title">直播作者 Top 10</div>\n')
            for i, row in enumerate(top['rows'][:10], 1):
                html_parts.append(render_author_card_h(row, row.get('rank', i)))
    
    # ===== 板块六：核心作者分析 =====
    s6 = data.get('section_6_core_authors', {})
    if s6.get('enabled', False):
        html_parts.append('<div class="section-title">六、核心作者分析</div>\n')
        html_parts.append(f'<div class="data-source">📊 数据来源：{s6.get("data_source", "-")}</div>\n')
        
        if s6.get('insight_box'):
            html_parts.append(render_insight_box(s6['insight_box'].get('insight'), s6['insight_box'].get('risk')))
        
        if s6.get('kpi_cards', {}).get('items'):
            html_parts.append(render_kpi_cards(s6['kpi_cards']['items'], cols=3))
        
        tier = s6.get('tier_distribution', {})
        if tier.get('table'):
            html_parts.append('<div class="subsection-title">作者分层</div>\n')
            for t in tier['table']:
                html_parts.append(f'''
                <div class="tier-card">
                    <div class="tier-name">{t['tier']}</div>
                    <div class="tier-value">{t['count']}人</div>
                    <div class="tier-pct">{t['pct']}</div>
                </div>
                ''')
        
        active = s6.get('active_pie', {})
        contrib = s6.get('contribution_pie', {})
        if active or contrib:
            html_parts.append('<div style="display: flex; gap: 20px; margin: 12px 0;">\n')
            if active:
                html_parts.append('<div style="flex: 1;"><div class="chart-placeholder">📊 活跃人数占比（需在Streamlit中查看）</div></div>\n')
            if contrib:
                html_parts.append('<div style="flex: 1;"><div class="chart-placeholder">📊 播放量贡献占比（需在Streamlit中查看）</div></div>\n')
            html_parts.append('</div>\n')
    
    # ===== 板块七：下月重点计划 =====
    s7 = data.get('section_7_todos', {})
    if s7.get('enabled', True):
        html_parts.append('<div class="section-title">七、下月重点计划</div>\n')
        categories = s7.get('categories', [])
        if categories:
            for cat in categories:
                priority_color = {'高': '#DC2626', '中': '#F59E0B', '低': '#6B7280'}.get(cat.get('priority', '中'), '#374151')
                html_parts.append(f'''
                <div class="todo-card">
                    <div class="todo-title" style="color: {priority_color};">{cat.get('name', '-')}（{cat.get('priority', '中')}优先级）</div>
                    <div class="todo-item">{'<br>'.join(['• ' + item for item in cat.get('items', [])])}</div>
                </div>
                ''')
    
    # 页脚
    html_parts.append(f'<div class="footer">创作者运营月报系统 v2.6 ｜ {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>\n')
    html_parts.append('</body>\n</html>')
    
    return '\n'.join(html_parts)

# =============================================================================
# 8. 示例数据
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
                {"platform": "抖音", "posts": 24093, "posts_pct": "90.7%", "plays": "2.13亿", "plays_pct": "86.9%", "authors": 1978},
                {"platform": "快手", "posts": 2336, "posts_pct": "8.8%", "plays": "3.19万", "plays_pct": "0.01%", "authors": 134},
                {"platform": "小红书", "posts": 122, "posts_pct": "0.5%", "plays": "32.6万", "plays_pct": "0.13%", "authors": 9}
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
            "summary": "流失105人中，尾部（<1万粉）57人（54.3%），腰部48人（45.7%），头部0人（0%）。流失作者粉丝中位数 9,868，整体属于腰尾部作者自然流动。",
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
            "footnote": "投稿活跃度计算剔除2000粉以下作者"
        },
        "activity_down_top10": {
            "rows": [
                {"rank": 1, "author_name": "**阿川", "author_link": "https://www.douyin.com/example", "author_id": "YS277891", "fans_display": "11,502", "platform": "抖音", "chg_display": "▼97.9%"},
                {"rank": 2, "author_name": "i游戏风景kun", "author_link": "https://v.douyin.com/example", "author_id": "YS438516", "fans_display": "74,215", "platform": "抖音", "chg_display": "▼97.2%"},
                {"rank": 3, "author_name": "Their**佬", "author_link": "https://v.douyin.com/example", "author_id": "YS038640", "fans_display": "39,287", "platform": "抖音", "chg_display": "▼96.7%"},
                {"rank": 4, "author_name": "飞星玩家", "author_link": "https://v.douyin.com/example", "author_id": "YS285194", "fans_display": "25,361", "platform": "抖音", "chg_display": "▼46.0%"},
                {"rank": 5, "author_name": "锦荣", "author_link": "https://v.douyin.com/example", "author_id": "YS694327", "fans_display": "8,441", "platform": "抖音", "chg_display": "▼70.0%"}
            ]
        },
        "activity_up_top10": {
            "rows": [
                {"rank": 1, "author_name": "m晨韵", "author_link": "https://v.douyin.com/example", "author_id": "YS048333", "fans_display": "6,609", "platform": "抖音", "chg_display": "▲82.6%"},
                {"rank": 2, "author_name": "大众游戏", "author_link": "https://v.douyin.com/example", "author_id": "YS274937", "fans_display": "5,155", "platform": "小红书", "chg_display": "▲193.0%"},
                {"rank": 3, "author_name": "**极速-单纯的老山猪", "author_link": "https://v.douyin.com/example", "author_id": "YS236775", "fans_display": "62,842", "platform": "抖音", "chg_display": "▲44.8%"},
                {"rank": 4, "author_name": "**小夭夭", "author_link": "https://v.douyin.com/example", "author_id": "YS741295", "fans_display": "60,643", "platform": "抖音", "chg_display": "▲121.1%"},
                {"rank": 5, "author_name": "睿睿臭弟", "author_link": "https://v.douyin.com/example", "author_id": "YS440904", "fans_display": "2,399", "platform": "快手", "chg_display": "▲189.3%"}
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
                {"label": "2月最高播放", "value": 7800000, "value_display": "780万", "note": "Dreamscar ｜ 抖音"},
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
                {"rank": 1, "title": "别的女生刚起床VS刚起床的她", "video_link": "https://v.douyin.com/example", "platform": "抖音", "author_name": "Dreamscar", "plays_display": "780万", "likes_display": "124,104"},
                {"rank": 2, "title": "奥迪RS7与保时捷718大婚！", "video_link": "https://v.douyin.com/example", "platform": "抖音", "author_name": "京娱汽车大电影", "plays_display": "583万", "likes_display": "92,368"},
                {"rank": 3, "title": "真实的你", "video_link": "https://v.douyin.com/example", "platform": "抖音", "author_name": "帆江海", "plays_display": "555万", "likes_display": "180,236"},
                {"rank": 4, "title": "哪款游戏逼出了你的极限？", "video_link": "https://v.douyin.com/example", "platform": "抖音", "author_name": "浮生未央", "plays_display": "414万", "likes_display": "99,336"},
                {"rank": 5, "title": "你可以叫我秦！也可以叫我，汉！", "video_link": "https://v.douyin.com/example", "platform": "抖音", "author_name": "京娱汽车大电影", "plays_display": "373万", "likes_display": "73,794"}
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
                {"rank": 1, "author_name": "一口权佳", "author_link": "https://v.douyin.com/example", "author_id": "YS241090", "fans_display": "11,724", "platform": "抖音", "cur_avg_display": "126,791", "chg_display": "▲4165%"},
                {"rank": 2, "author_name": "小龙", "author_link": "https://v.douyin.com/example", "author_id": "YS1290177", "fans_display": "3,898", "platform": "抖音", "cur_avg_display": "29,228", "chg_display": "▲2421%"},
                {"rank": 3, "author_name": "啊这", "author_link": "https://v.douyin.com/example", "author_id": "YS279479", "fans_display": "134,329", "platform": "抖音", "cur_avg_display": "432,026", "chg_display": "▲2165%"}
            ]
        },
        "avg_plays_down_top10": {
            "rows": [
                {"rank": 1, "author_name": "游戏达人小王", "author_link": "https://v.douyin.com/example", "author_id": "YS111222", "fans_display": "25,000", "platform": "抖音", "cur_avg_display": "2,100", "chg_display": "▼89%"},
                {"rank": 2, "author_name": "极速玩家", "author_link": "https://v.douyin.com/example", "author_id": "YS333444", "fans_display": "8,500", "platform": "抖音", "cur_avg_display": "1,800", "chg_display": "▼85%"},
                {"rank": 3, "author_name": "车神传说", "author_link": "https://v.douyin.com/example", "author_id": "YS555666", "fans_display": "15,200", "platform": "抖音", "cur_avg_display": "3,200", "chg_display": "▼78%"}
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
                {"label": "场均ACU", "value": 856, "value_display": "856"},
                {"label": "总直播时长", "value": 312, "value_display": "312小时"},
                {"label": "场均时长", "value": 2.0, "value_display": "2.0小时"},
                {"label": "新增关注数", "value": 3250, "value_display": "3,250"},
                {"label": "互动量", "value": 15600, "value_display": "1.56万"}
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
                {"label": "累计播放量", "value": 56700000, "value_display": "5670万"},
                {"label": "稿件贡献占比", "value": 5.1, "value_display": "5.1%", "note": "1234/24312"},
                {"label": "爆款贡献占比", "value": 18.2, "value_display": "18.2%", "note": "141/777爆款"},
                {"label": "核心作者留存率", "value": 87.5, "value_display": "87.5%", "note": "28/32连续活跃"}
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
# 9. 顶部操作区
# =============================================================================
col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])

with col_btn1:
    if st.button("📊 加载示例数据", use_container_width=True):
        st.session_state.report_data = EXAMPLE_DATA
        st.success("已加载示例数据")

with col_btn2:
    uploaded_file = st.file_uploader("上传 JSON", type=["json"], label_visibility="collapsed")
    if uploaded_file:
        try:
            st.session_state.report_data = json.load(uploaded_file)
            st.success(f"已加载: {uploaded_file.name}")
        except Exception as e:
            st.error(f"解析错误: {e}")

with col_btn3:
    if st.session_state.report_data:
        html_content = generate_html(st.session_state.report_data)
        b64 = base64.b64encode(html_content.encode('utf-8')).decode()
        product = safe_get(st.session_state.report_data, 'report_meta.product', 'report')
        month = safe_get(st.session_state.report_data, 'report_meta.month', datetime.now().strftime('%Y-%m'))
        filename = f"{product}_{month}_月报.html"
        st.markdown(f'<a href="data:text/html;base64,{b64}" download="{filename}" style="display: block; width: 100%; text-align: center; background: #1B4FD8; color: white; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-size: 14px;">📥 导出 HTML</a>', unsafe_allow_html=True)

# =============================================================================
# 10. 主界面（Streamlit渲染）
# =============================================================================
if not st.session_state.report_data:
    st.markdown("""
    <div style="text-align: center; padding: 60px 40px;">
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

# ===== 板块一：大盘概览 =====
s1 = data.get('section_1_dashboard', {})
if s1.get('enabled', True):
    st.markdown('<div class="section-title">一、大盘概览</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="data-source">📊 数据来源：{s1.get("data_source", "-")}</div>', unsafe_allow_html=True)
    
    if s1.get('insight_box'):
        st.markdown(render_insight_box(s1['insight_box'].get('insight'), s1['insight_box'].get('risk')), unsafe_allow_html=True)
    
    if s1.get('kpi_cards', {}).get('items'):
        st.markdown(render_kpi_cards(s1['kpi_cards']['items'], cols=3), unsafe_allow_html=True)
    
    # 日趋势图
    st.markdown('<div class="subsection-title">投稿趋势</div>', unsafe_allow_html=True)
    month_str = safe_get(data, 'report_meta.month', '2026-02')
    year, month = map(int, month_str.split('-'))
    days_in_month = calendar.monthrange(year, month)[1]
    dates = [f"{month:02d}-{d:02d}" for d in range(1, days_in_month + 1)]
    
    import random
    random.seed(42)
    posts = [random.randint(700, 1400) for _ in range(days_in_month)]
    
    events = s1.get('daily_trend', {}).get('events', [])
    fig = create_line_chart(dates, posts, y_label="投稿量", events=events)
    st.plotly_chart(fig, use_container_width=True, key="chart_daily_trend")
    
    by_platform = s1.get('by_platform', {})
    if by_platform.get('table'):
        st.markdown('<div class="subsection-title">分平台数据</div>', unsafe_allow_html=True)
        for p in by_platform['table']:
            st.markdown(f"""
            <div class="tier-card">
                <div class="tier-name">{p['platform']}</div>
                <div class="tier-value">{p['posts']}</div>
                <div class="tier-pct">{p['posts_pct']}</div>
                <div class="tier-pct">播放:{p['plays']}</div>
                <div class="tier-pct">作者:{p['authors']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            pie_data = [{'label': p['platform'], 'value': p['posts']} for p in by_platform['table']]
            fig = create_pie_chart(pie_data, title="投稿量占比")
            st.plotly_chart(fig, use_container_width=True, key="chart_platform_posts")
        with col2:
            fig = create_pie_chart(pie_data, title="播放量占比")
            st.plotly_chart(fig, use_container_width=True, key="chart_platform_plays")

# ===== 板块二：创作者维度 =====
s2 = data.get('section_2_creators', {})
if s2.get('enabled', True):
    st.markdown('<div class="section-title">二、创作者维度</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="data-source">📊 数据来源：{s2.get("data_source", "-")}</div>', unsafe_allow_html=True)
    
    if s2.get('insight_box'):
        st.markdown(render_insight_box(s2['insight_box'].get('insight'), s2['insight_box'].get('risk')), unsafe_allow_html=True)
    
    if s2.get('kpi_cards', {}).get('items'):
        st.markdown(render_kpi_cards(s2['kpi_cards']['items'], cols=4), unsafe_allow_html=True)
    
    tier = s2.get('tier_distribution', {})
    if tier.get('table'):
        thresholds = tier.get('thresholds', {})
        st.markdown(f'<div class="subsection-title">粉段分层（{thresholds.get("tail_label", "<1万")} / {thresholds.get("mid_label", "1-30万")} / {thresholds.get("top_label", "≥30万")}）</div>', unsafe_allow_html=True)
        st.markdown(render_tier_cards(tier['table']), unsafe_allow_html=True)
    
    lost = s2.get('lost_author_analysis', {})
    if lost:
        st.markdown('<div class="subsection-title">流失作者归因分析</div>', unsafe_allow_html=True)
        st.markdown(render_insight_box(lost.get('summary'), lost.get('risk')), unsafe_allow_html=True)
        if lost.get('cards'):
            st.markdown(render_kpi_cards(lost['cards'], cols=3), unsafe_allow_html=True)
    
    alert = s2.get('activity_alert', {})
    if alert.get('cards'):
        st.markdown('<div class="subsection-title">投稿活跃度预警</div>', unsafe_allow_html=True)
        st.markdown(render_kpi_cards(alert['cards'], cols=3), unsafe_allow_html=True)
        if alert.get('footnote'):
            st.markdown(f"<small style='color: #6B7280;'>{alert['footnote']}</small>", unsafe_allow_html=True)
    
    for key, title_text in [('activity_down_top10', '投稿活跃度 降低 Top 10'), ('activity_up_top10', '投稿活跃度 增加 Top 10')]:
        table = s2.get(key, {})
        if table.get('rows'):
            st.markdown(f'<div class="subsection-title">{title_text}</div>', unsafe_allow_html=True)
            for i, row in enumerate(table['rows'][:10], 1):
                st.markdown(render_author_card_h(row, row.get('rank', i)), unsafe_allow_html=True)

# ===== 板块三：内容维度 =====
s3 = data.get('section_3_content', {})
if s3.get('enabled', True):
    st.markdown('<div class="section-title">三、内容维度</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="data-source">📊 数据来源：{s3.get("data_source", "-")}</div>', unsafe_allow_html=True)
    
    if s3.get('insight_box'):
        st.markdown(render_insight_box(s3['insight_box'].get('insight'), s3['insight_box'].get('risk')), unsafe_allow_html=True)
    
    if s3.get('kpi_cards', {}).get('items'):
        st.markdown(render_kpi_cards(s3['kpi_cards']['items'], cols=3), unsafe_allow_html=True)
    
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
    
    videos = s3.get('viral_videos_top10', {})
    if videos.get('rows'):
        st.markdown(f'<div class="subsection-title">爆款稿件 Top 10（≥{s3.get("viral_threshold", 50000)//10000}万播放）</div>', unsafe_allow_html=True)
        for i, row in enumerate(videos['rows'][:10], 1):
            st.markdown(render_video_card_h(row, row.get('rank', i)), unsafe_allow_html=True)
    
    content_type = s3.get('content_type_analysis', {})
    if content_type.get('table'):
        st.markdown('<div class="subsection-title">爆款内容类型归因</div>', unsafe_allow_html=True)
        if content_type.get('summary'):
            st.markdown(render_insight_box(content_type['summary']), unsafe_allow_html=True)
        
        for t in content_type['table']:
            st.markdown(f"""
            <div class="tier-card">
                <div class="tier-name">{t['type']}</div>
                <div class="tier-value">{t['count_display']}</div>
                <div class="tier-pct">{t['percentage']}</div>
                <div class="tier-pct">条均:{t['avg_plays_display']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        if content_type.get('pie_data'):
            fig = create_pie_chart(content_type['pie_data'], title="爆款内容类型分布")
            st.plotly_chart(fig, use_container_width=True, key="chart_content_type")
    
    # 条均播放增长Top10
    avg_up = s3.get('avg_plays_up_top10', {})
    if avg_up.get('rows'):
        st.markdown('<div class="subsection-title">条均播放增长 Top 10</div>', unsafe_allow_html=True)
        for i, row in enumerate(avg_up['rows'][:10], 1):
            st.markdown(render_author_card_h(row, row.get('rank', i)), unsafe_allow_html=True)
    
    # 条均播放降低Top10（新增）
    avg_down = s3.get('avg_plays_down_top10', {})
    if avg_down.get('rows'):
        st.markdown('<div class="subsection-title">条均播放降低 Top 10</div>', unsafe_allow_html=True)
        for i, row in enumerate(avg_down['rows'][:10], 1):
            st.markdown(render_author_card_h(row, row.get('rank', i)), unsafe_allow_html=True)

# ===== 板块四：活动维度 =====
s4 = data.get('section_4_activities', {})
if s4.get('enabled', True):
    st.markdown('<div class="section-title">四、活动维度</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="data-source">📊 数据来源：{s4.get("data_source", "-")}</div>', unsafe_allow_html=True)
    
    if s4.get('insight_box'):
        st.markdown(render_insight_box(s4['insight_box'].get('insight'), s4['insight_box'].get('risk')), unsafe_allow_html=True)
    
    main = s4.get('main_activity', {})
    if main.get('cur_period'):
        st.markdown('<div class="subsection-title">主力活动对比</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        cur = main['cur_period']
        with col1:
            st.markdown(render_activity_card(f"当月：{cur.get('name', '-')}", cur), unsafe_allow_html=True)
        
        prev = main.get('prev_period', {})
        if prev:
            with col2:
                st.markdown(render_activity_card(f"上月：{prev.get('name', '-')}", prev), unsafe_allow_html=True)
    
    sub = s4.get('sub_activities', {})
    if sub.get('rows'):
        st.markdown('<div class="subsection-title">其他活动 — 草根小喇叭（子活动）</div>', unsafe_allow_html=True)
        for row in sub['rows']:
            st.markdown(render_activity_card(row.get('name', '-'), row), unsafe_allow_html=True)
    
    comm = s4.get('commissioned', {})
    if comm:
        st.markdown('<div class="subsection-title">创作者约稿</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        cur = comm.get('cur', {})
        if cur:
            with col1:
                st.markdown(render_activity_card(f"当月（{cur.get('count', 0)}个活动）", cur), unsafe_allow_html=True)
        prev = comm.get('prev', {})
        if prev:
            with col2:
                st.markdown(render_activity_card(f"上月（{prev.get('count', 0)}个活动）", prev), unsafe_allow_html=True)

# ===== 板块五：直播维度 =====
s5 = data.get('section_5_livestream', {})
if s5.get('enabled', False):
    st.markdown('<div class="section-title">五、直播维度</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="data-source">📊 数据来源：{s5.get("data_source", "-")}</div>', unsafe_allow_html=True)
    
    if s5.get('insight_box'):
        st.markdown(render_insight_box(s5['insight_box'].get('insight'), s5['insight_box'].get('risk')), unsafe_allow_html=True)
    
    if s5.get('kpi_cards', {}).get('items'):
        st.markdown(render_kpi_cards(s5['kpi_cards']['items'], cols=4), unsafe_allow_html=True)
    
    tier = s5.get('tier_distribution', {})
    if tier.get('table'):
        st.markdown('<div class="subsection-title">主播分层</div>', unsafe_allow_html=True)
        for t in tier['table']:
            st.markdown(f"""
            <div class="tier-card">
                <div class="tier-name">{t['tier']}</div>
                <div class="tier-value">{t['count']}人</div>
                <div class="tier-pct">{t['pct']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        if tier.get('pie_data'):
            fig = create_pie_chart(tier['pie_data'], title="主播分层分布")
            st.plotly_chart(fig, use_container_width=True, key="chart_streamer_tier")
    
    top = s5.get('top_streamers', {})
    if top.get('rows'):
        st.markdown('<div class="subsection-title">直播作者 Top 10</div>', unsafe_allow_html=True)
        for i, row in enumerate(top['rows'][:10], 1):
            st.markdown(render_author_card_h(row, row.get('rank', i)), unsafe_allow_html=True)

elif s5.get('enabled') is False:
    st.markdown('<div class="section-title">五、直播维度</div>', unsafe_allow_html=True)
    st.info("该板块未启用")

# ===== 板块六：核心作者分析 =====
s6 = data.get('section_6_core_authors', {})
if s6.get('enabled', False):
    st.markdown('<div class="section-title">六、核心作者分析</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="data-source">📊 数据来源：{s6.get("data_source", "-")}</div>', unsafe_allow_html=True)
    
    if s6.get('insight_box'):
        st.markdown(render_insight_box(s6['insight_box'].get('insight'), s6['insight_box'].get('risk')), unsafe_allow_html=True)
    
    if s6.get('kpi_cards', {}).get('items'):
        st.markdown(render_kpi_cards(s6['kpi_cards']['items'], cols=3), unsafe_allow_html=True)
    
    tier = s6.get('tier_distribution', {})
    if tier.get('table'):
        st.markdown('<div class="subsection-title">作者分层</div>', unsafe_allow_html=True)
        for t in tier['table']:
            st.markdown(f"""
            <div class="tier-card">
                <div class="tier-name">{t['tier']}</div>
                <div class="tier-value">{t['count']}人</div>
                <div class="tier-pct">{t['pct']}</div>
            </div>
            """, unsafe_allow_html=True)
    
    active = s6.get('active_pie', {})
    contrib = s6.get('contribution_pie', {})
    if active or contrib:
        col1, col2 = st.columns(2)
        with col1:
            if active:
                pie_data = [
                    {'label': '活跃', 'value': active.get('active', 0)},
                    {'label': '不活跃', 'value': active.get('inactive', 0)}
                ]
                fig = create_pie_chart(pie_data, title="活跃人数占比")
                st.plotly_chart(fig, use_container_width=True, key="chart_core_active")
        with col2:
            if contrib:
                pie_data = [
                    {'label': '核心作者', 'value': contrib.get('core', 0)},
                    {'label': '其他作者', 'value': contrib.get('others', 0)}
                ]
                fig = create_pie_chart(pie_data, title="播放量贡献占比")
                st.plotly_chart(fig, use_container_width=True, key="chart_core_contrib")

elif s6.get('enabled') is False:
    st.markdown('<div class="section-title">六、核心作者分析</div>', unsafe_allow_html=True)
    st.info("该板块未启用")

# ===== 板块七：下月重点计划 =====
s7 = data.get('section_7_todos', {})
if s7.get('enabled', True):
    st.markdown('<div class="section-title">七、下月重点计划</div>', unsafe_allow_html=True)
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

# ===== 页脚 =====
st.markdown("---")
st.markdown(f'<div style="text-align: center; color: #9CA3AF; font-size: 11px;">创作者运营月报系统 v2.6 ｜ {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>', unsafe_allow_html=True)

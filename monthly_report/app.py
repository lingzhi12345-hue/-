#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小喇叭创作者运营月报系统 v2.2.0
技术栈：Streamlit + Plotly
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any, List

# =============================================================================
# 1. 页面基础配置
# =============================================================================
st.set_page_config(
    page_title="创作者运营月报系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# 2. 样式定义
# =============================================================================
st.markdown("""
<style>
    /* 整体风格 */
    .stApp { background-color: #ffffff; }
    
    /* 隐藏默认元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* 标题样式 */
    .report-title {
        font-size: 24px;
        font-weight: 700;
        color: #1B4FD8;
        margin-bottom: 8px;
    }
    .report-meta {
        font-size: 12px;
        color: #6B7280;
        margin-bottom: 16px;
    }
    
    /* 板块标题 */
    .section-title {
        font-size: 18px;
        font-weight: 700;
        color: #1B4FD8;
        margin-top: 20px;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 2px solid #E8EFFF;
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
    }
    .insight-box .text {
        font-size: 13px;
        color: #374151;
        line-height: 1.8;
    }
    .risk-text {
        font-size: 12px;
        color: #DC2626;
        margin-top: 8px;
    }
    
    /* KPI卡片 */
    .kpi-card {
        background: #F5F8FF;
        border-radius: 10px;
        padding: 16px 18px;
        border: 1px solid #E0E8FF;
        text-align: center;
    }
    .kpi-label {
        font-size: 11px;
        color: #6B7280;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 24px;
        font-weight: 700;
        color: #1B4FD8;
        margin-bottom: 4px;
    }
    .kpi-sub {
        font-size: 11px;
        color: #6B7280;
    }
    .kpi-note {
        font-size: 10px;
        color: #9CA3AF;
        margin-top: 4px;
    }
    
    /* 颜色 */
    .up { color: #16A34A; font-weight: 600; }
    .down { color: #DC2626; font-weight: 600; }
    
    /* 链接 */
    a { color: #1B4FD8; text-decoration: none; }
    a:hover { text-decoration: underline; }
    
    /* 打印隐藏 */
    @media print {
        .stSidebar, .no-print { display: none !important; }
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 3. Session State 初始化
# =============================================================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'report_data' not in st.session_state:
    st.session_state.report_data = None
if 'data_source' not in st.session_state:
    st.session_state.data_source = None

# =============================================================================
# 4. 用户认证（简单实现）
# =============================================================================
USERS = {
    "admin": "admin123",
    "editor": "editor123"
}

def login_page():
    """渲染登录页面"""
    st.markdown("""
    <div style="max-width: 400px; margin: 100px auto; padding: 40px; 
                border: 1px solid #eee; border-radius: 8px; 
                box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center;">
        <h1 style="font-size: 24px; margin-bottom: 8px;">创作者月报系统 📊</h1>
        <p style="color: #6B7280; margin-bottom: 24px;">请登录以继续</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("login_form"):
        username = st.text_input("用户名", placeholder="请输入 admin")
        password = st.text_input("密码", type="password", placeholder="请输入 admin123")
        submit = st.form_submit_button("登录", use_container_width=True)
        
        if submit:
            if username in USERS and USERS[username] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("用户名或密码错误")
    
    st.stop()

# 检查登录状态
if not st.session_state.logged_in:
    login_page()

# =============================================================================
# 5. 辅助函数
# =============================================================================
def safe_get(data: Dict, keys: str, default=None):
    """安全获取嵌套字典值"""
    try:
        keys_list = keys.split('.')
        result = data
        for key in keys_list:
            if isinstance(result, dict):
                result = result.get(key)
            else:
                return default
            if result is None:
                return default
        return result
    except:
        return default


def format_number(value, unit=""):
    """格式化数字显示"""
    if value is None or value == "-":
        return "-"
    try:
        num = float(value)
        if num >= 100000000:  # 亿
            return f"{num/100000000:.2f}亿{unit}"
        elif num >= 10000:  # 万
            return f"{num/10000:.2f}万{unit}"
        else:
            return f"{num:,.0f}{unit}"
    except:
        return str(value)


def format_change(value, direction):
    """格式化变化百分比"""
    if value is None:
        return "-"
    try:
        pct = float(value)
        if direction == "up":
            return f"▲{abs(pct):.1f}%"
        elif direction == "down":
            return f"▼{abs(pct):.1f}%"
        else:
            return f"{pct:.1f}%"
    except:
        return "-"


def render_insight_box(insight: str, risk: str = None):
    """渲染分析框"""
    if not insight and not risk:
        return
    
    html = '<div class="insight-box">'
    if insight:
        html += f'<div class="text">{insight}</div>'
    if risk:
        html += f'<div class="risk-text">⚠️ 风险提示：{risk}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_kpi_cards(items: List[Dict], cols: int = 3, show_change: bool = True):
    """渲染KPI卡片"""
    if not items:
        st.info("暂无数据")
        return
    
    columns = st.columns(cols)
    for i, item in enumerate(items):
        col_idx = i % cols
        with columns[col_idx]:
            label = item.get('label', '-')
            value = item.get('value_display', format_number(item.get('value')))
            note = item.get('note', '')
            
            # 变化显示
            change_html = ""
            if show_change and item.get('change_pct') is not None:
                direction = item.get('change_direction', 'flat')
                change_display = format_change(item.get('change_pct'), direction)
                if direction == 'up':
                    change_html = f'<span class="up">{change_display}</span>'
                elif direction == 'down':
                    change_html = f'<span class="down">{change_display}</span>'
                else:
                    change_html = change_display
            
            prev_display = item.get('prev_display', '-')
            if prev_display and prev_display != '-':
                sub_text = f"上月 {prev_display} ｜ {change_html}" if change_html else f"上月 {prev_display}"
            else:
                sub_text = change_html if change_html else "-"
            
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}</div>
                <div class="kpi-sub">{sub_text}</div>
                {f'<div class="kpi-note">{note}</div>' if note else ''}
            </div>
            """, unsafe_allow_html=True)


def render_table(df: pd.DataFrame, link_columns: List[str] = None, highlight_columns: List[str] = None):
    """渲染表格，支持链接和颜色高亮"""
    if df.empty:
        st.info("暂无数据")
        return
    
    # 创建显示用的DataFrame
    display_df = df.copy()
    
    # 格式化链接列
    if link_columns:
        for col in link_columns:
            if col in display_df.columns and f"{col}_link" in display_df.columns:
                display_df[col] = display_df.apply(
                    lambda row: f'<a href="{row[f"{col}_link"]}" target="_blank">{row[col]}</a>' 
                    if pd.notna(row.get(f"{col}_link")) else row[col], 
                    axis=1
                )
    
    st.markdown(display_df.to_html(escape=False, index=False, classes='data-table'), unsafe_allow_html=True)


def create_pie_chart(data: List[Dict], title: str):
    """创建饼图"""
    if not data:
        return None
    
    fig = go.Figure(data=[go.Pie(
        labels=[d.get('platform', d.get('label', '')) for d in data],
        values=[d.get('value', 0) for d in data],
        hole=0.3,
        marker_colors=['#1B4FD8', '#3B82F6', '#93C5FD', '#BFDBFE']
    )])
    fig.update_layout(
        title=title,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2),
        margin=dict(t=40, b=20, l=20, r=20),
        height=280
    )
    return fig


def create_bar_line_chart(dates: List[str], bar_data: List[float], line_data: List[float], 
                          bar_label: str, line_label: str, events: List[Dict] = None):
    """创建双轴图表"""
    fig = go.Figure()
    
    # 柱状图
    fig.add_trace(go.Bar(
        x=dates,
        y=bar_data,
        name=bar_label,
        marker_color='rgba(27, 79, 216, 0.6)',
        yaxis='y'
    ))
    
    # 折线图
    fig.add_trace(go.Scatter(
        x=dates,
        y=line_data,
        name=line_label,
        mode='lines+markers',
        marker=dict(color='#F59E0B', size=4),
        line=dict(color='#F59E0B', width=2),
        yaxis='y2'
    ))
    
    # 添加事件标注
    if events:
        for event in events:
            event_date = event.get('date', '')
            event_name = event.get('name', '')
            if event_date in dates:
                idx = dates.index(event_date)
                fig.add_annotation(
                    x=event_date,
                    y=line_data[idx],
                    text=event_name,
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=1,
                    arrowcolor="#EF4444",
                    font=dict(size=9, color="#EF4444"),
                    yshift=10
                )
    
    fig.update_layout(
        xaxis=dict(title="日期"),
        yaxis=dict(title=bar_label, side="left"),
        yaxis2=dict(title=line_label, side="right", overlaying="y", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=40, b=40, l=40, r=40),
        height=300
    )
    
    return fig


# =============================================================================
# 6. 侧边栏
# =============================================================================
with st.sidebar:
    st.markdown(f"### 👤 当前用户\n**{st.session_state.username}**")
    if st.button("退出登录", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()
    
    st.divider()
    st.markdown("### 📁 数据管理")
    
    # 示例数据按钮
    if st.button("👉 加载示例数据", use_container_width=True):
        example_data = {
            "report_meta": {
                "product": "巅峰极速",
                "month": "2026-02",
                "prev_month": "2026-01",
                "generate_time": "2026-03-05 10:30",
                "stat_period": "2026-02-01 ~ 2026-02-28"
            },
            "section_0_header": {
                "title": "巅峰极速 · 2026年2月 · 小喇叭创作者运营月报",
                "stat_period": "2026-02-01 ~ 2026-02-28",
                "data_source": "内容营销系统 & 大盘看板",
                "summary_box": {
                    "content": "2月大盘活跃创作者1,979人，环比下降15.3%，投稿供给有所收缩。内容消费方面，含三方播放2.45亿，环比小幅下降4.5%，互动量逆势上涨13.4%，内容共鸣有所提升。",
                    "todos": [
                        "📌 重点触达腰部流失作者48人",
                        "📌 评估3月激励规则优化",
                        "📌 推进快手、小红书多平台布局"
                    ]
                }
            },
            "section_1_dashboard": {
                "enabled": True,
                "data_source": "EDT大盘看板（用户提供）",
                "insight_box": {
                    "insight": "2月大盘供给与消费双降，活跃作者环比减少357人（-15.3%），投稿量降至26,551条（-20.5%）。",
                    "risk": "活跃作者和投稿量同步下滑，供给端收缩明显，需关注创作者活跃度下降趋势。"
                },
                "kpi_cards": {
                    "items": [
                        {"label": "活跃创作者数", "value": 1979, "value_display": "1,979", "prev_value": 2336, "prev_display": "2,336", "change_pct": -15.3, "change_direction": "down"},
                        {"label": "总发布投稿量", "value": 26551, "value_display": "26,551", "prev_value": 33381, "prev_display": "33,381", "change_pct": -20.5, "change_direction": "down"},
                        {"label": "审核通过稿件", "value": 24312, "value_display": "24,312", "prev_value": 25326, "prev_display": "25,326", "change_pct": -4.0, "change_direction": "down"},
                        {"label": "总播放量（含三方）", "value": 245000000, "value_display": "2.45亿", "prev_value": 257000000, "prev_display": "2.57亿", "change_pct": -4.5, "change_direction": "down"},
                        {"label": "总互动量（含三方）", "value": 15400, "value_display": "1.54万", "prev_value": 13600, "prev_display": "1.36万", "change_pct": 13.4, "change_direction": "up"},
                        {"label": "条均播放", "value": 10077, "value_display": "10,077", "prev_value": 10016, "prev_display": "10,016", "change_pct": 0.6, "change_direction": "up"}
                    ]
                },
                "by_platform": {
                    "table": [
                        {"platform": "抖音", "posts": 24093, "posts_pct": 90.7, "plays": 213000000, "plays_pct": 86.9, "authors": 1978},
                        {"platform": "快手", "posts": 2336, "posts_pct": 8.8, "plays": 31900, "plays_pct": 0.01, "authors": 134},
                        {"platform": "小红书", "posts": 122, "posts_pct": 0.5, "plays": 326000, "plays_pct": 0.13, "authors": 9}
                    ]
                }
            },
            "section_2_creators": {"enabled": True},
            "section_3_content": {"enabled": True},
            "section_4_activities": {"enabled": True},
            "section_5_livestream": {"enabled": True},
            "section_6_core_authors": {"enabled": False},
            "section_7_todos": {"enabled": True}
        }
        st.session_state.report_data = example_data
        st.session_state.data_source = "示例数据"
        st.success("已加载示例数据！")
    
    # 文件上传
    uploaded_file = st.file_uploader("上传 JSON 数据文件", type=["json"])
    if uploaded_file is not None:
        try:
            data = json.load(uploaded_file)
            st.session_state.report_data = data
            st.session_state.data_source = uploaded_file.name
            st.success(f"已加载: {uploaded_file.name}")
        except Exception as e:
            st.error(f"文件解析错误: {e}")
    
    st.divider()
    
    # 数据源显示
    if st.session_state.data_source:
        st.markdown(f"**当前数据源：**\n{st.session_state.data_source}")
    
    # PDF导出
    if st.session_state.report_data:
        st.divider()
        st.markdown("### 📥 导出报告")
        if st.button("导出为 PDF", use_container_width=True):
            st.info("PDF导出功能需要安装 pdfkit/weasyprint，当前版本暂不支持。建议使用浏览器打印功能（Ctrl+P）导出PDF。")

# =============================================================================
# 7. 主界面渲染
# =============================================================================

# 无数据时的提示
if not st.session_state.report_data:
    st.markdown("""
    <div style="text-align: center; padding: 80px 40px;">
        <h2 style="color: #1B4FD8; margin-bottom: 16px;">📊 创作者运营月报系统</h2>
        <p style="color: #6B7280; margin-bottom: 24px;">请上传 JSON 数据文件或加载示例数据开始</p>
        <p style="color: #9CA3AF; font-size: 12px;">支持板块：大盘概览、创作者维度、内容维度、活动维度、直播维度、核心作者分析、下月计划</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# 获取报告数据
data = st.session_state.report_data

# =============================================================================
# 页眉板块
# =============================================================================
st.markdown(f"""
<div class="report-title">{safe_get(data, 'section_0_header.title', '月报标题')}</div>
<div class="report-meta">数据来源：{safe_get(data, 'section_0_header.data_source', '-')} ｜ 环比对比：{safe_get(data, 'report_meta.prev_month', '-')}</div>
""", unsafe_allow_html=True)

# 开头总结
summary_box = safe_get(data, 'section_0_header.summary_box', {})
if summary_box:
    st.markdown(f"""
    <div class="insight-box" style="background: rgba(27, 79, 216, 0.1); border-left-color: #1B4FD8;">
        <div class="text">{summary_box.get('content', '-')}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # TODO列表
    todos = summary_box.get('todos', [])
    if todos:
        st.markdown("**下月重点：**")
        for todo in todos:
            st.markdown(f"- {todo}")

st.markdown("---")

# =============================================================================
# 板块一：大盘概览
# =============================================================================
section_1 = data.get('section_1_dashboard', {})
if section_1.get('enabled', True):
    with st.expander("一、大盘概览", expanded=True):
        # 数据来源
        st.markdown(f'<div class="data-source">📊 数据来源：{section_1.get("data_source", "-")}</div>', unsafe_allow_html=True)
        
        # 小结+风险
        insight_box = section_1.get('insight_box', {})
        if insight_box:
            render_insight_box(insight_box.get('insight'), insight_box.get('risk'))
        
        # KPI卡片
        kpi_cards = section_1.get('kpi_cards', {})
        items = kpi_cards.get('items', [])
        if items:
            render_kpi_cards(items, cols=3)
        
        # 分平台数据
        by_platform = section_1.get('by_platform', {})
        if by_platform.get('table'):
            st.markdown("#### 分平台数据")
            platform_df = pd.DataFrame(by_platform['table'])
            st.dataframe(platform_df, use_container_width=True, hide_index=True)
            
            # 饼图
            pie_data = by_platform.get('pie_charts', {})
            col1, col2 = st.columns(2)
            with col1:
                posts_data = pie_data.get('posts_data', [])
                if not posts_data:
                    posts_data = [{'platform': p['platform'], 'value': p['posts'], 'percentage': p.get('posts_pct', 0)} 
                                  for p in by_platform['table']]
                fig = create_pie_chart(posts_data, "分平台投稿量占比")
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                plays_data = pie_data.get('plays_data', [])
                if not plays_data:
                    plays_data = [{'platform': p['platform'], 'value': p['plays'], 'percentage': p.get('plays_pct', 0)} 
                                  for p in by_platform['table']]
                fig = create_pie_chart(plays_data, "分平台播放量占比")
                if fig:
                    st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# 板块二：创作者维度
# =============================================================================
section_2 = data.get('section_2_creators', {})
if section_2.get('enabled', True):
    with st.expander("二、创作者维度", expanded=True):
        st.markdown(f'<div class="data-source">📊 数据来源：{section_2.get("data_source", "-")}</div>', unsafe_allow_html=True)
        
        insight_box = section_2.get('insight_box', {})
        if insight_box:
            render_insight_box(insight_box.get('insight'), insight_box.get('risk'))
        
        # KPI卡片
        kpi_cards = section_2.get('kpi_cards', {})
        items = kpi_cards.get('items', [])
        if items:
            render_kpi_cards(items, cols=4)
            if kpi_cards.get('footnote'):
                st.markdown(f"<small style='color: #6B7280;'>{kpi_cards['footnote']}</small>", unsafe_allow_html=True)
        
        # 粉段分层
        tier_dist = section_2.get('tier_distribution', {})
        if tier_dist.get('table'):
            thresholds = tier_dist.get('thresholds', {})
            st.markdown(f"#### 粉段分层（{thresholds.get('tail_label', '<1万')} / {thresholds.get('mid_label', '1-30万')} / {thresholds.get('top_label', '≥30万')}）")
            tier_df = pd.DataFrame(tier_dist['table'])
            st.dataframe(tier_df, use_container_width=True, hide_index=True)
        
        # 流失作者归因
        lost_analysis = section_2.get('lost_author_analysis', {})
        if lost_analysis:
            st.markdown("#### 流失作者归因分析")
            render_insight_box(lost_analysis.get('summary'), lost_analysis.get('risk'))
            
            lost_data = lost_analysis.get('data', {})
            if lost_data:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("流失作者腰部占比", f"{lost_data.get('mid_lost', 0)}人")
                with col2:
                    st.metric("流失作者粉丝中位数", f"{lost_data.get('median_fans', 0):,}")
                with col3:
                    st.metric("头部作者流失", f"{lost_data.get('top_lost', 0)}人")
        
        # 活跃度预警
        activity_alert = section_2.get('activity_alert', {})
        if activity_alert.get('kpi_cards'):
            st.markdown(f"#### 投稿活跃度预警（粉丝≥{activity_alert.get('min_fans_threshold', 0)}）")
            alert_items = activity_alert['kpi_cards']
            col1, col2, col3 = st.columns(3)
            for i, item in enumerate(alert_items):
                with [col1, col2, col3][i]:
                    color = item.get('color', 'gray')
                    color_map = {'red': '#DC2626', 'green': '#16A34A', 'gray': '#6B7280'}
                    st.markdown(f"""
                    <div style="text-align: center; padding: 16px; background: {'#FFF5F5' if color=='red' else '#F0FDF4' if color=='green' else '#F9FAFB'}; 
                                border-radius: 8px; border: 1px solid {color_map.get(color, '#E5E7EB')};">
                        <div style="font-size: 24px; font-weight: 700; color: {color_map.get(color, '#6B7280')};">{item.get('value', '-')}</div>
                        <div style="font-size: 11px; color: #6B7280;">{item.get('label', '-')}</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            if activity_alert.get('footnote'):
                st.markdown(f"<small style='color: #6B7280;'>{activity_alert['footnote']}</small>", unsafe_allow_html=True)
        
        # 活跃度Top10表格
        for table_key, table_title in [('activity_down_top10', '投稿活跃度 降低 Top 10'), ('activity_up_top10', '投稿活跃度 增加 Top 10')]:
            table_data = section_2.get(table_key, {})
            if table_data.get('rows'):
                st.markdown(f"#### {table_title}")
                df = pd.DataFrame(table_data['rows'])
                # 选择显示列
                display_cols = ['rank', 'author_name', 'author_id', 'fans_display', 'platform', 'prev_tasks', 'cur_tasks', 'chg_abs', 'chg_display']
                display_cols = [c for c in display_cols if c in df.columns]
                st.dataframe(df[display_cols], use_container_width=True, hide_index=True)

# =============================================================================
# 板块三：内容维度
# =============================================================================
section_3 = data.get('section_3_content', {})
if section_3.get('enabled', True):
    with st.expander("三、内容维度", expanded=True):
        st.markdown(f'<div class="data-source">📊 数据来源：{section_3.get("data_source", "-")}</div>', unsafe_allow_html=True)
        
        insight_box = section_3.get('insight_box', {})
        if insight_box:
            render_insight_box(insight_box.get('insight'), insight_box.get('risk'))
        
        # KPI卡片
        kpi_cards = section_3.get('kpi_cards', {})
        items = kpi_cards.get('items', [])
        if items:
            render_kpi_cards(items, cols=3, show_change=False)
        
        # 爆款作者Top3
        viral_top3 = section_3.get('viral_authors_top3', {})
        if viral_top3.get('items'):
            st.markdown("#### 爆款作者 Top 3")
            items = viral_top3['items']
            col1, col2, col3 = st.columns(3)
            for i, item in enumerate(items):
                with [col1, col2, col3][i]:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 16px; background: #F0F4FF; border-radius: 10px; border: 1px solid #C7D7FF;">
                        <div style="font-size: 14px; font-weight: 700; color: #1B4FD8; margin-bottom: 6px;">{item.get('rank_icon', '')} Top {item.get('rank', i+1)}</div>
                        <div style="font-size: 14px; font-weight: 700; color: #1B4FD8;"><a href="{item.get('author_link', '#')}" target="_blank">{item.get('author_name', '-')}</a></div>
                        <div style="font-size: 28px; font-weight: 700; color: #374151; margin: 8px 0;">{item.get('viral_count', 0)}</div>
                        <div style="font-size: 11px; color: #6B7280;">条爆款 ｜ 创作匠ID：{item.get('author_id', '-')}</div>
                    </div>
                    """, unsafe_allow_html=True)
        
        # 爆款稿件Top10
        viral_videos = section_3.get('viral_videos_top10', {})
        if viral_videos.get('rows'):
            st.markdown(f"#### 爆款稿件 Top 10（≥{section_3.get('viral_threshold', 50000)//10000}万播放）")
            df = pd.DataFrame(viral_videos['rows'])
            display_cols = ['rank', 'title', 'platform', 'author_name', 'author_id', 'plays_display', 'likes_display']
            display_cols = [c for c in display_cols if c in df.columns]
            st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
        
        # 内容类型归因
        content_type = section_3.get('content_type_analysis', {})
        if content_type.get('table'):
            st.markdown("#### 爆款内容类型归因")
            if content_type.get('summary'):
                render_insight_box(content_type['summary'])
            
            df = pd.DataFrame(content_type['table'])
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            if content_type.get('classification_note'):
                st.markdown(f"<small style='color: #6B7280;'>{content_type['classification_note']}</small>", unsafe_allow_html=True)
        
        # 条均播放Top10
        for table_key, table_title in [('avg_plays_up_top10', '条均播放 增幅 Top 10'), ('avg_plays_down_top10', '条均播放 降幅 Top 10')]:
            table_data = section_3.get(table_key, {})
            if table_data.get('rows'):
                st.markdown(f"#### {table_title}")
                df = pd.DataFrame(table_data['rows'])
                display_cols = ['rank', 'author_name', 'author_id', 'prev_avg_display', 'cur_avg_display', 'chg_display', 'fans_display', 'platform']
                display_cols = [c for c in display_cols if c in df.columns]
                st.dataframe(df[display_cols], use_container_width=True, hide_index=True)

# =============================================================================
# 板块四：活动维度
# =============================================================================
section_4 = data.get('section_4_activities', {})
if section_4.get('enabled', True):
    with st.expander("四、活动维度", expanded=True):
        st.markdown(f'<div class="data-source">📊 数据来源：{section_4.get("data_source", "-")}</div>', unsafe_allow_html=True)
        
        insight_box = section_4.get('insight_box', {})
        if insight_box:
            render_insight_box(insight_box.get('insight'), insight_box.get('risk'))
        
        # 主力活动对比
        main_activity = section_4.get('main_activity', {})
        if main_activity.get('cur_period'):
            st.markdown("#### 主力活动对比")
            col1, col2 = st.columns(2)
            
            cur = main_activity['cur_period']
            with col1:
                st.markdown(f"**{cur.get('month', '当月')}**")
                st.markdown(f"*{cur.get('name', '-')}*")
                st.metric("投稿量", cur.get('posts_display', '-'), f"{cur.get('posts_change_display', '')}")
                st.metric("参与作者", cur.get('authors_display', '-'))
                st.metric("含三方播放", cur.get('plays_with_thirdparty_display', '-'))
                st.metric("预估CPM", cur.get('cpm_estimate_display', '-'), f"参考值 {cur.get('cpm_reference_display', '-')}")
            
            prev = main_activity.get('prev_period', {})
            if prev:
                with col2:
                    st.markdown(f"**{prev.get('month', '上月')}**")
                    st.markdown(f"*{prev.get('name', '-')}*")
                    st.metric("投稿量", prev.get('posts_display', '-'))
                    st.metric("参与作者", prev.get('authors_display', '-'))
                    st.metric("内部播放", prev.get('plays_internal_display', '-'))
                    st.metric("预估CPM", prev.get('cpm_estimate_display', '-'))
            
            if main_activity.get('cpm_note'):
                st.markdown(f"<small style='color: #6B7280;'>{main_activity['cpm_note']}</small>", unsafe_allow_html=True)
        
        # 子活动表格
        sub_activities = section_4.get('sub_activities', {})
        if sub_activities.get('table'):
            st.markdown(f"#### {sub_activities.get('title', '其他活动')}")
            df = pd.DataFrame(sub_activities['table'])
            st.dataframe(df, use_container_width=True, hide_index=True)

# =============================================================================
# 板块五：直播维度
# =============================================================================
section_5 = data.get('section_5_livestream', {})
if section_5.get('enabled', False):
    with st.expander("五、直播维度", expanded=True):
        st.markdown(f'<div class="data-source">📊 数据来源：{section_5.get("data_source", "-")}</div>', unsafe_allow_html=True)
        
        insight_box = section_5.get('insight_box', {})
        if insight_box:
            render_insight_box(insight_box.get('insight'), insight_box.get('risk'))
        
        # KPI卡片
        kpi_cards = section_5.get('kpi_cards', {})
        items = kpi_cards.get('items', [])
        if items:
            render_kpi_cards(items, cols=4, show_change=False)
        
        # 分层
        tier_dist = section_5.get('tier_distribution', {})
        if tier_dist.get('table'):
            thresholds = tier_dist.get('thresholds', {})
            st.markdown(f"#### 主播分层（按ACU：{thresholds.get('tail_label', '<100')} / {thresholds.get('mid_label', '100-1000')} / {thresholds.get('top_label', '≥1000')}）")
            st.markdown(f"<small style='color: #6B7280;'>门槛：头部≥{thresholds.get('top', 1000)} ACU，腰部{thresholds.get('mid', 100)}-{thresholds.get('top', 1000)} ACU</small>", unsafe_allow_html=True)
            tier_df = pd.DataFrame(tier_dist['table'])
            st.dataframe(tier_df, use_container_width=True, hide_index=True)
        
        # Top10主播
        top_streamers = section_5.get('top_streamers', {})
        if top_streamers.get('rows'):
            st.markdown("#### 直播作者 Top 10")
            df = pd.DataFrame(top_streamers['rows'])
            display_cols = ['rank', 'author_name', 'author_id', 'session_count', 'view_count_display', 'avg_acu_display', 'fans_display', 'platform']
            display_cols = [c for c in display_cols if c in df.columns]
            st.dataframe(df[display_cols], use_container_width=True, hide_index=True)

elif section_5.get('enabled') is False:
    with st.expander("五、直播维度", expanded=False):
        st.info("该板块未启用（JSON中 section_5_livestream.enabled = false）")

# =============================================================================
# 板块六：核心作者分析
# =============================================================================
section_6 = data.get('section_6_core_authors', {})
if section_6.get('enabled', False):
    with st.expander("六、核心作者分析", expanded=True):
        st.markdown(f'<div class="data-source">📊 数据来源：{section_6.get("data_source", "-")}</div>', unsafe_allow_html=True)
        
        if section_6.get('required_input'):
            st.markdown(f"<small style='color: #6B7280;'>需要用户提供：{section_6['required_input']}</small>", unsafe_allow_html=True)
        
        insight_box = section_6.get('insight_box', {})
        if insight_box:
            render_insight_box(insight_box.get('insight'), insight_box.get('risk'))
        
        # KPI卡片
        kpi_cards = section_6.get('kpi_cards', {})
        items = kpi_cards.get('items', [])
        if items:
            render_kpi_cards(items, cols=3, show_change=False)
        
        # 分层
        tier_dist = section_6.get('tier_distribution', {})
        if tier_dist.get('table'):
            thresholds = tier_dist.get('thresholds', {})
            st.markdown(f"#### 作者分层（按粉丝：{thresholds.get('tail_label', '<10万')} / {thresholds.get('mid_label', '10-40万')} / {thresholds.get('top_label', '≥40万')}）")
            tier_df = pd.DataFrame(tier_dist['table'])
            st.dataframe(tier_df, use_container_width=True, hide_index=True)
        
        # 饼图
        pie_charts = section_6.get('pie_charts', {})
        if pie_charts:
            col1, col2 = st.columns(2)
            with col1:
                active_ratio = pie_charts.get('active_ratio', {})
                if active_ratio.get('data'):
                    fig = create_pie_chart(active_ratio['data'], active_ratio.get('title', '活跃人数占比'))
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                plays_contrib = pie_charts.get('plays_contribution', {})
                if plays_contrib.get('data'):
                    fig = create_pie_chart(plays_contrib['data'], plays_contrib.get('title', '贡献播放量占比'))
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
        
        # 按标签分组
        by_tag = section_6.get('by_tag_groups', {})
        if by_tag.get('groups'):
            for group in by_tag['groups']:
                st.markdown(f"#### {group.get('tag_name', '标签分组')}（{group.get('tag_count', 0)}人）")
                author_list = group.get('author_list', [])
                if author_list:
                    df = pd.DataFrame(author_list)
                    st.dataframe(df, use_container_width=True, hide_index=True)

elif section_6.get('enabled') is False:
    with st.expander("六、核心作者分析", expanded=False):
        st.info("该板块未启用（JSON中 section_6_core_authors.enabled = false）")

# =============================================================================
# 板块七：下月重点计划
# =============================================================================
section_7 = data.get('section_7_todos', {})
if section_7.get('enabled', True):
    with st.expander("七、下月重点计划", expanded=True):
        st.markdown(f'<div class="data-source">📊 {section_7.get("data_source", "-")}</div>', unsafe_allow_html=True)
        
        categories = section_7.get('categories', [])
        if categories:
            for cat in categories:
                priority = cat.get('priority', '')
                priority_color = {'高': '#DC2626', '中': '#F59E0B', '低': '#6B7280'}.get(priority, '#374151')
                st.markdown(f"#### {cat.get('name', '-')}")
                items = cat.get('items', [])
                for item in items:
                    st.markdown(f"- {item}")

# =============================================================================
# 8. 页脚
# =============================================================================
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; color: #9CA3AF; font-size: 11px; padding: 20px;">
    创作者运营月报系统 v2.2.0 ｜ 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}
</div>
""", unsafe_allow_html=True)

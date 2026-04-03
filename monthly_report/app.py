#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小喇叭创作者运营月报系统 v2.2.1
技术栈：Streamlit 原生图表（无需额外依赖）
"""

import streamlit as st
import pandas as pd
import json
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
    .stApp { background-color: #ffffff; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    
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
    
    .up { color: #16A34A; font-weight: 600; }
    .down { color: #DC2626; font-weight: 600; }
    
    a { color: #1B4FD8; text-decoration: none; }
    a:hover { text-decoration: underline; }
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
# 4. 用户认证
# =============================================================================
USERS = {"admin": "admin123", "editor": "editor123"}

def login_page():
    st.markdown("""
    <div style="max-width: 400px; margin: 100px auto; padding: 40px; 
                border: 1px solid #eee; border-radius: 8px; text-align: center;">
        <h1 style="font-size: 24px;">创作者月报系统 📊</h1>
        <p style="color: #6B7280; margin-bottom: 24px;">请登录以继续</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("login_form"):
        username = st.text_input("用户名", placeholder="admin")
        password = st.text_input("密码", type="password", placeholder="admin123")
        submit = st.form_submit_button("登录", use_container_width=True)
        
        if submit:
            if username in USERS and USERS[username] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("用户名或密码错误")
    st.stop()

if not st.session_state.logged_in:
    login_page()

# =============================================================================
# 5. 辅助函数
# =============================================================================
def safe_get(data: Dict, keys: str, default=None):
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

def render_insight_box(insight: str, risk: str = None):
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
    if not items:
        st.info("暂无数据")
        return
    
    columns = st.columns(cols)
    for i, item in enumerate(items):
        with columns[i % cols]:
            label = item.get('label', '-')
            value = item.get('value_display', str(item.get('value', '-')))
            note = item.get('note', '')
            
            change_html = ""
            if show_change and item.get('change_pct') is not None:
                direction = item.get('change_direction', 'flat')
                pct = item.get('change_pct', 0)
                if direction == 'up':
                    change_html = f'<span class="up">▲{abs(pct):.1f}%</span>'
                elif direction == 'down':
                    change_html = f'<span class="down">▼{abs(pct):.1f}%</span>'
            
            prev_display = item.get('prev_display', '')
            if prev_display:
                sub_text = f"上月 {prev_display} ｜ {change_html}" if change_html else f"上月 {prev_display}"
            else:
                sub_text = change_html if change_html else note
            
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}</div>
                <div class="kpi-sub">{sub_text}</div>
            </div>
            """, unsafe_allow_html=True)

def render_pie_chart(data: List[Dict], title: str):
    if not data:
        return
    labels = [d.get('platform', d.get('label', '')) for d in data]
    values = [d.get('value', 0) for d in data]
    
    df = pd.DataFrame({'类别': labels, '数值': values}).set_index('类别')
    st.markdown(f"**{title}**")
    st.bar_chart(df, use_container_width=True)

# =============================================================================
# 6. 完整示例数据（从HTML提取）
# =============================================================================
EXAMPLE_DATA = {
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
            "content": "2月大盘活跃创作者1,979人，环比下降15.3%，投稿供给有所收缩。内容消费方面，含三方播放2.45亿，环比小幅下降4.5%，互动量逆势上涨13.4%，内容共鸣有所提升。活动侧，主力激励活动参与1,944人，CPM 4.49元/千次，略高于3元参考值，需关注投入产出效率。内容方面，爆款777条（≥5万播放），Dreamscar、京娱汽车大电影、帆江海贡献头部流量。",
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
            "insight": "2月大盘供给与消费双降，活跃作者环比减少357人（-15.3%），投稿量降至26,551条（-20.5%）。互动量逆势上涨13.4%，显示内容质量有所提升。",
            "risk": "活跃作者和投稿量同步下滑，供给端收缩明显，需关注创作者活跃度下降趋势。抖音高度集中（>90%），多平台布局存在较大提升空间。"
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
        "by_platform": {
            "table": [
                {"platform": "抖音", "posts": 24093, "posts_pct": 90.7, "plays": 213000000, "plays_pct": 86.9, "authors": 1978},
                {"platform": "快手", "posts": 2336, "posts_pct": 8.8, "plays": 31900, "plays_pct": 0.01, "authors": 134},
                {"platform": "小红书", "posts": 122, "posts_pct": 0.5, "plays": 326000, "plays_pct": 0.13, "authors": 9}
            ]
        }
    },
    "section_2_creators": {
        "enabled": True,
        "data_source": "内容营销系统 API 全量作者明细（2月/1月）",
        "insight_box": {
            "insight": "2月留存299人，但腰部作者净减少33人（196→163），部分有影响力的创作者活跃度下降明显。增长侧亮点明显：大众游戏、巅峰极速-单纯的老山猪、m晨韵表现突出。",
            "risk": "腰部作者（1-30万粉）从196人降至163人，降幅16.8%。Their巅佬、eggta、薏苡等腰部创作者降幅超90%，需优先1v1触达了解原因。"
        },
        "kpi_cards": {
            "items": [
                {"label": "总活跃作者（过滤后）", "value": 364, "value_display": "364", "prev_value": 404, "prev_display": "404", "change_pct": 9.9, "change_direction": "down"},
                {"label": "新增（流入）", "value": 65, "value_display": "65", "note": "1月未投稿→2月有投稿"},
                {"label": "流失", "value": 105, "value_display": "105", "note": "1月有投稿→2月未投稿"},
                {"label": "留存", "value": 299, "value_display": "299", "note": "两月均有投稿"}
            ],
            "footnote": "*此处为大盘数据，仅作基础门槛筛选，未剔除粉段作者。"
        },
        "tier_distribution": {
            "thresholds": {"top": 300000, "mid": 10000, "top_label": "≥30万", "mid_label": "1-30万", "tail_label": "<1万"},
            "table": [
                {"tier": "头部（≥30万）", "cur_count": 12, "cur_pct": 3.3, "prev_count": 10, "prev_pct": 2.5, "change_pct": 20, "change_direction": "up"},
                {"tier": "腰部（1-30万）", "cur_count": 163, "cur_pct": 44.8, "prev_count": 196, "prev_pct": 48.5, "change_pct": 16.8, "change_direction": "down"},
                {"tier": "尾部（<1万）", "cur_count": 189, "cur_pct": 51.9, "prev_count": 198, "prev_pct": 49.0, "change_pct": 4.5, "change_direction": "down"}
            ]
        },
        "lost_author_analysis": {
            "summary": "流失105人中，尾部（<1万粉）57人（54.3%），腰部48人（45.7%），头部0人（0%）。流失作者粉丝中位数 9,868，整体属于腰尾部作者自然流动。→ 判断：有一定风险。腰部作者流失比例较高（45.7%），需重点关注。",
            "risk": "腰部作者（1-30万粉）流失48人，占流失总数45.7%，高于健康水位。建议针对腰部流失作者开展1v1触达。",
            "data": {"top_lost": 0, "mid_lost": 48, "tail_lost": 57, "median_fans": 9868}
        },
        "activity_alert": {
            "min_fans_threshold": 2000,
            "kpi_cards": [
                {"label": "轻度下降（降幅0-50%）", "value": 43, "color": "gray"},
                {"label": "重度下降（降幅>50%）", "value": 14, "color": "red"},
                {"label": "显著增长（增幅>50%）", "value": 113, "color": "green"}
            ],
            "footnote": "为避免低粉摇摆作者污染数据，剔除2000粉以下作者后计算"
        },
        "activity_down_top10": {
            "rows": [
                {"rank": 1, "author_name": "巅峰阿川", "author_link": "https://www.douyin.com/user/MS4wLjABAAAAiW8UhTL64SIbzgRtRLiYpGVJFvQ3c5iiH7Lkdtf9", "author_id": "YS277891", "fans_display": "11,502", "platform": "抖音", "prev_tasks": 47, "cur_tasks": 1, "chg_abs": 46, "chg_display": "▼97.9%"},
                {"rank": 2, "author_name": "i游戏风景kun", "author_link": "https://v.douyin.com/i57CLUTd/", "author_id": "YS438516", "fans_display": "74,215", "platform": "抖音", "prev_tasks": 36, "cur_tasks": 1, "chg_abs": 35, "chg_display": "▼97.2%"},
                {"rank": 3, "author_name": "Their巅佬（巅峰极速）", "author_link": "https://v.douyin.com/i57CLUTd/", "author_id": "YS038640", "fans_display": "39,287", "platform": "抖音", "prev_tasks": 30, "cur_tasks": 1, "chg_abs": 29, "chg_display": "▼96.7%"},
                {"rank": 4, "author_name": "飞星玩家-巅峰极速", "author_link": "https://v.douyin.com/i57CLUTd/", "author_id": "YS285194", "fans_display": "25,361", "platform": "抖音", "prev_tasks": 50, "cur_tasks": 27, "chg_abs": 23, "chg_display": "▼46.0%"},
                {"rank": 5, "author_name": "锦荣", "author_link": "https://v.douyin.com/i57CLUTd/", "author_id": "YS694327", "fans_display": "8,441", "platform": "抖音", "prev_tasks": 30, "cur_tasks": 9, "chg_abs": 21, "chg_display": "▼70.0%"}
            ]
        },
        "activity_up_top10": {
            "rows": [
                {"rank": 1, "author_name": "m晨韵", "author_link": "https://v.douyin.com/i57CLUTd/", "author_id": "YS048333", "fans_display": "6,609", "platform": "抖音", "prev_tasks": 86, "cur_tasks": 157, "chg_abs": 71, "chg_display": "▲82.6%"},
                {"rank": 2, "author_name": "大众游戏", "author_link": "https://v.douyin.com/i57CLUTd/", "author_id": "YS274937", "fans_display": "5,155", "platform": "小红书", "prev_tasks": 43, "cur_tasks": 126, "chg_abs": 83, "chg_display": "▲193.0%"},
                {"rank": 3, "author_name": "巅峰极速-单纯的老山猪", "author_link": "https://v.douyin.com/i57CLUTd/", "author_id": "YS236775", "fans_display": "62,842", "platform": "抖音", "prev_tasks": 181, "cur_tasks": 262, "chg_abs": 81, "chg_display": "▲44.8%"},
                {"rank": 4, "author_name": "巅峰小夭夭", "author_link": "https://v.douyin.com/i57CLUTd/", "author_id": "YS741295", "fans_display": "60,643", "platform": "抖音", "prev_tasks": 57, "cur_tasks": 126, "chg_abs": 69, "chg_display": "▲121.1%"},
                {"rank": 5, "author_name": "睿睿臭弟", "author_link": "https://v.douyin.com/i57CLUTd/", "author_id": "YS440904", "fans_display": "2,399", "platform": "快手", "prev_tasks": 28, "cur_tasks": 81, "chg_abs": 53, "chg_display": "▲189.3%"}
            ]
        }
    },
    "section_3_content": {
        "enabled": True,
        "data_source": "爆款数据来源：用户提供的爆款稿件表格 ｜ 条均播放来源：内容营销系统API全量作者明细",
        "insight_box": {
            "insight": "2月爆款777条（≥5万播放），较1月微增1.4%，爆款供给稳定。帆江海、啊这、一口权佳等作者条均播放大幅增长，与飞驰人生3联动节点高度吻合。",
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
                {"rank": 1, "rank_icon": "🥇", "author_name": "一口游戏", "author_link": "https://v.douyin.com/i57CLUTd/", "viral_count": 36, "author_id": "YS001723"},
                {"rank": 2, "rank_icon": "🥈", "author_name": "Their巅佬（巅峰极速）", "author_link": "https://v.douyin.com/i57CLUTd/", "viral_count": 35, "author_id": "YS038640"},
                {"rank": 3, "rank_icon": "🥉", "author_name": "巅峰极速阿坤Arkun", "author_link": "https://v.douyin.com/i57CLUTd/", "viral_count": 23, "author_id": "YS033543"}
            ]
        },
        "viral_videos_top10": {
            "rows": [
                {"rank": 1, "title": "别的女生刚起床VS刚起床的她#巅峰极速…", "video_link": "https://v.douyin.com/i57CLUTd/", "platform": "抖音", "author_name": "Dreamscar", "author_link": "https://v.douyin.com/i57CLUTd/", "author_id": "YS031563", "plays_display": "780万", "likes_display": "124,104"},
                {"rank": 2, "title": "奥迪RS7与保时捷718大婚！", "video_link": "https://v.douyin.com/i57CLUTd/", "platform": "抖音", "author_name": "京娱汽车大电影", "author_link": "https://v.douyin.com/i57CLUTd/", "author_id": "YS619462", "plays_display": "583万", "likes_display": "92,368"},
                {"rank": 3, "title": "真实的你 #上巅当飞驰主角", "video_link": "https://v.douyin.com/i57CLUTd/", "platform": "抖音", "author_name": "帆江海", "author_link": "https://v.douyin.com/i57CLUTd/", "author_id": "YS889179", "plays_display": "555万", "likes_display": "180,236"},
                {"rank": 4, "title": "哪款游戏逼出了你的极限？", "video_link": "https://v.douyin.com/i57CLUTd/", "platform": "抖音", "author_name": "浮生未央", "author_link": "https://v.douyin.com/i57CLUTd/", "author_id": "YS1230687", "plays_display": "414万", "likes_display": "99,336"},
                {"rank": 5, "title": "你可以叫我秦！也可以叫我，汉！", "video_link": "https://v.douyin.com/i57CLUTd/", "platform": "抖音", "author_name": "京娱汽车大电影", "author_link": "https://v.douyin.com/i57CLUTd/", "author_id": "YS619462", "plays_display": "373万", "likes_display": "73,794"}
            ]
        },
        "content_type_analysis": {
            "summary": "2月爆款内容以联动内容（48.8%，379条）为主。从条均播放看，剧情/故事类以119.6万条均领跑全场。结论：联动节点是爆款量的引擎，剧情/故事类是爆款质的天花板。",
            "table": [
                {"type": "联动内容", "count": 379, "count_display": "379", "percentage": 48.8, "avg_plays_display": "22.4万", "is_best_roi": False},
                {"type": "车辆/涂装", "count": 178, "count_display": "178", "percentage": 22.9, "avg_plays_display": "30.1万", "is_best_roi": False},
                {"type": "游戏日常", "count": 166, "count_display": "166", "percentage": 21.4, "avg_plays_display": "26.9万", "is_best_roi": False},
                {"type": "攻略/资讯", "count": 29, "count_display": "29", "percentage": 3.7, "avg_plays_display": "15.7万", "is_best_roi": False},
                {"type": "剧情/故事", "count": 21, "count_display": "21", "percentage": 2.7, "avg_plays_display": "119.6万 🔥", "is_best_roi": True}
            ],
            "classification_note": "分类方法：基于稿件标题关键词规则判断，准确率约90%"
        },
        "avg_plays_up_top10": {
            "rows": [
                {"rank": 1, "author_name": "一口权佳", "author_link": "https://v.douyin.com/i57CLUTd/", "author_id": "YS241090", "prev_avg_display": "2,973", "cur_avg_display": "126,791", "chg_display": "▲4165%", "fans_display": "11,724", "platform": "抖音"},
                {"rank": 2, "author_name": "小龙·巅峰极速", "author_link": "https://v.douyin.com/i57CLUTd/", "author_id": "YS1290177", "prev_avg_display": "1,160", "cur_avg_display": "29,228", "chg_display": "▲2421%", "fans_display": "3,898", "platform": "抖音"},
                {"rank": 3, "author_name": "啊这", "author_link": "https://v.douyin.com/i57CLUTd/", "author_id": "YS279479", "prev_avg_display": "19,070", "cur_avg_display": "432,026", "chg_display": "▲2165%", "fans_display": "134,329", "platform": "抖音"},
                {"rank": 4, "author_name": "帆江海", "author_link": "https://v.douyin.com/i57CLUTd/", "author_id": "YS889179", "prev_avg_display": "46,357", "cur_avg_display": "898,427", "chg_display": "▲1838%", "fans_display": "161,591", "platform": "抖音"},
                {"rank": 5, "author_name": "小溪", "author_link": "https://v.douyin.com/i57CLUTd/", "author_id": "YS974483", "prev_avg_display": "1,115", "cur_avg_display": "20,339", "chg_display": "▲1724%", "fans_display": "13,782", "platform": "抖音"}
            ]
        },
        "avg_plays_down_top10": {
            "rows": [
                {"rank": 1, "author_name": "小迷糊又困了", "author_link": "https://v.douyin.com/i57CLUTd/", "author_id": "YS275011", "prev_avg_display": "13,711", "cur_avg_display": "102", "chg_display": "▼99%", "fans_display": "99,498", "platform": "快手"},
                {"rank": 2, "author_name": "六幺姐", "author_link": "https://v.douyin.com/i57CLUTd/", "author_id": "YS884856", "prev_avg_display": "140,928", "cur_avg_display": "1,618", "chg_display": "▼99%", "fans_display": "9,127", "platform": "抖音"},
                {"rank": 3, "author_name": "幸福@788", "author_link": "https://v.douyin.com/i57CLUTd/", "author_id": "YS805609", "prev_avg_display": "470,435", "cur_avg_display": "10,310", "chg_display": "▼98%", "fans_display": "35,792", "platform": "抖音"}
            ]
        }
    },
    "section_4_activities": {
        "enabled": True,
        "data_source": "内容营销系统 API 全量活动明细（game_id=1945）",
        "insight_box": {
            "insight": "2月主力活动投稿25,972条，参与1,944人，含三方播放2.45亿，CPM 4.49元，略高于参考值3元。",
            "risk": "CPM 4.49元超参考值3元，需评估3月预算分配。"
        },
        "main_activity": {
            "cur_period": {
                "month": "2月", "name": "【小喇叭-短视频】26年巅峰极速2月内容激励活动",
                "posts": 25972, "posts_display": "25,972", "posts_change_pct": 18.8, "posts_change_display": "▼18.8%",
                "authors": 1944, "authors_display": "1,944",
                "plays_internal": 123000000, "plays_internal_display": "1.23亿",
                "plays_with_thirdparty": 245000000, "plays_with_thirdparty_display": "2.45亿",
                "budget": 1100000, "budget_display": "110万",
                "cpm_estimate": 4.49, "cpm_estimate_display": "4.49元",
                "cpm_reference": 3.0, "cpm_reference_display": "3.0元", "cpm_status": "high"
            },
            "prev_period": {
                "month": "1月", "name": "【小喇叭-短视频】26巅峰极速1月创作者内容激励活动",
                "posts": 31983, "posts_display": "31,983",
                "authors": 2298, "authors_display": "2,298",
                "plays_internal": 109000000, "plays_internal_display": "1.09亿",
                "budget": 1100000, "budget_display": "110万",
                "cpm_estimate": 10.10, "cpm_estimate_display": "10.10元"
            },
            "cpm_note": "CPM计算口径：含三方播放量。1月含三方播放数据暂缺，1月CPM使用内部播放口径。"
        }
    },
    "section_5_livestream": {
        "enabled": True,
        "data_source": "内容营销系统 - 直播数据",
        "insight_box": {
            "insight": "2月直播场次稳定，场均ACU表现良好。头部主播集中度较高。",
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
                {"tier": "头部（≥1000 ACU）", "count": 5, "pct": 11.1},
                {"tier": "腰部（100-1000 ACU）", "count": 18, "pct": 40.0},
                {"tier": "尾部（<100 ACU）", "count": 22, "pct": 48.9}
            ]
        },
        "top_streamers": {
            "rows": [
                {"rank": 1, "author_name": "示例主播A", "author_link": "https://v.douyin.com/example/", "author_id": "YS001", "session_count": 12, "view_count_display": "5.2万", "avg_acu_display": "2,156", "fans_display": "15.6万", "platform": "抖音"},
                {"rank": 2, "author_name": "示例主播B", "author_link": "https://v.douyin.com/example/", "author_id": "YS002", "session_count": 10, "view_count_display": "3.8万", "avg_acu_display": "1,823", "fans_display": "12.3万", "platform": "抖音"}
            ]
        }
    },
    "section_6_core_authors": {
        "enabled": False
    },
    "section_7_todos": {
        "enabled": True,
        "data_source": "基于2026年2月数据分析，供3月运营参考",
        "categories": [
            {
                "name": "重点作者管理动作",
                "priority": "高",
                "items": [
                    "Their巅佬、eggta、薏苡等腰部作者优先1v1触达，了解停更原因",
                    "流失48名腰部作者中，粉丝≥5万的优先接触，考虑提供约稿机会",
                    "大众游戏、巅峰极速-单纯的老山猪、m晨韵纳入约稿考察池"
                ]
            },
            {
                "name": "供给端运营动作",
                "priority": "中",
                "items": [
                    "活跃作者从2,336降至1,979（-15.3%），建议增加'复活奖励'",
                    "快手、小红书占比极低，建议评估平台专项激励"
                ]
            },
            {
                "name": "活动效率优化",
                "priority": "中",
                "items": [
                    "CPM 4.49元超参考值3元，建议引入内容质量评分机制",
                    "爆款内容类型归因下月需补充，导出数据须含内容类型字段"
                ]
            }
        ]
    }
}

# =============================================================================
# 7. 侧边栏
# =============================================================================
with st.sidebar:
    st.markdown(f"### 👤 当前用户\n**{st.session_state.username}**")
    if st.button("退出登录", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()
    
    st.divider()
    st.markdown("### 📁 数据管理")
    
    if st.button("👉 加载示例数据", use_container_width=True):
        st.session_state.report_data = EXAMPLE_DATA
        st.session_state.data_source = "示例数据（巅峰极速 2026-02）"
        st.success("已加载示例数据！")
    
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
    if st.session_state.data_source:
        st.markdown(f"**当前数据源：**\n{st.session_state.data_source}")

# =============================================================================
# 8. 主界面渲染
# =============================================================================
if not st.session_state.report_data:
    st.markdown("""
    <div style="text-align: center; padding: 80px 40px;">
        <h2 style="color: #1B4FD8; margin-bottom: 16px;">📊 创作者运营月报系统</h2>
        <p style="color: #6B7280;">请上传 JSON 数据文件或加载示例数据开始</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

data = st.session_state.report_data

# 页眉
st.markdown(f"""
<div class="report-title">{safe_get(data, 'section_0_header.title', '月报标题')}</div>
<div class="report-meta">数据来源：{safe_get(data, 'section_0_header.data_source', '-')} ｜ 环比对比：{safe_get(data, 'report_meta.prev_month', '-')}</div>
""", unsafe_allow_html=True)

summary_box = safe_get(data, 'section_0_header.summary_box', {})
if summary_box:
    st.markdown(f"""
    <div class="insight-box" style="background: rgba(27, 79, 216, 0.1); border-left-color: #1B4FD8;">
        <div class="text">{summary_box.get('content', '-')}</div>
    </div>
    """, unsafe_allow_html=True)
    todos = summary_box.get('todos', [])
    if todos:
        st.markdown("**下月重点：**")
        for todo in todos:
            st.markdown(f"- {todo}")

st.markdown("---")

# 板块一：大盘概览
section_1 = data.get('section_1_dashboard', {})
if section_1.get('enabled', True):
    with st.expander("一、大盘概览", expanded=True):
        st.markdown(f'<div class="data-source">📊 数据来源：{section_1.get("data_source", "-")}</div>', unsafe_allow_html=True)
        insight_box = section_1.get('insight_box', {})
        if insight_box:
            render_insight_box(insight_box.get('insight'), insight_box.get('risk'))
        kpi_cards = section_1.get('kpi_cards', {})
        if kpi_cards.get('items'):
            render_kpi_cards(kpi_cards['items'], cols=3)
        by_platform = section_1.get('by_platform', {})
        if by_platform.get('table'):
            st.markdown("#### 分平台数据")
            st.dataframe(pd.DataFrame(by_platform['table']), use_container_width=True, hide_index=True)
            col1, col2 = st.columns(2)
            with col1:
                render_pie_chart([{'platform': p['platform'], 'value': p['posts']} for p in by_platform['table']], "分平台投稿量占比")
            with col2:
                render_pie_chart([{'platform': p['platform'], 'value': p['plays']} for p in by_platform['table']], "分平台播放量占比")

# 板块二：创作者维度
section_2 = data.get('section_2_creators', {})
if section_2.get('enabled', True):
    with st.expander("二、创作者维度", expanded=True):
        st.markdown(f'<div class="data-source">📊 数据来源：{section_2.get("data_source", "-")}</div>', unsafe_allow_html=True)
        insight_box = section_2.get('insight_box', {})
        if insight_box:
            render_insight_box(insight_box.get('insight'), insight_box.get('risk'))
        kpi_cards = section_2.get('kpi_cards', {})
        if kpi_cards.get('items'):
            render_kpi_cards(kpi_cards['items'], cols=4)
        tier_dist = section_2.get('tier_distribution', {})
        if tier_dist.get('table'):
            thresholds = tier_dist.get('thresholds', {})
            st.markdown(f"#### 粉段分层（{thresholds.get('tail_label', '<1万')} / {thresholds.get('mid_label', '1-30万')} / {thresholds.get('top_label', '≥30万')}）")
            st.dataframe(pd.DataFrame(tier_dist['table']), use_container_width=True, hide_index=True)
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
        activity_alert = section_2.get('activity_alert', {})
        if activity_alert.get('kpi_cards'):
            st.markdown(f"#### 投稿活跃度预警（粉丝≥{activity_alert.get('min_fans_threshold', 0)}）")
            cols = st.columns(3)
            for i, item in enumerate(activity_alert['kpi_cards']):
                with cols[i]:
                    st.metric(item.get('label', '-'), item.get('value', '-'))
            if activity_alert.get('footnote'):
                st.markdown(f"<small style='color: #6B7280;'>{activity_alert['footnote']}</small>", unsafe_allow_html=True)
        for table_key, table_title in [('activity_down_top10', '投稿活跃度 降低 Top 10'), ('activity_up_top10', '投稿活跃度 增加 Top 10')]:
            table_data = section_2.get(table_key, {})
            if table_data.get('rows'):
                st.markdown(f"#### {table_title}")
                df = pd.DataFrame(table_data['rows'])
                display_cols = [c for c in ['rank', 'author_name', 'author_id', 'fans_display', 'platform', 'prev_tasks', 'cur_tasks', 'chg_abs', 'chg_display'] if c in df.columns]
                st.dataframe(df[display_cols], use_container_width=True, hide_index=True)

# 板块三：内容维度
section_3 = data.get('section_3_content', {})
if section_3.get('enabled', True):
    with st.expander("三、内容维度", expanded=True):
        st.markdown(f'<div class="data-source">📊 数据来源：{section_3.get("data_source", "-")}</div>', unsafe_allow_html=True)
        insight_box = section_3.get('insight_box', {})
        if insight_box:
            render_insight_box(insight_box.get('insight'), insight_box.get('risk'))
        kpi_cards = section_3.get('kpi_cards', {})
        if kpi_cards.get('items'):
            render_kpi_cards(kpi_cards['items'], cols=3, show_change=False)
        viral_top3 = section_3.get('viral_authors_top3', {})
        if viral_top3.get('items'):
            st.markdown("#### 爆款作者 Top 3")
            cols = st.columns(3)
            for i, item in enumerate(viral_top3['items']):
                with cols[i]:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 16px; background: #F0F4FF; border-radius: 10px; border: 1px solid #C7D7FF;">
                        <div style="font-size: 14px; font-weight: 700; color: #1B4FD8;">{item.get('rank_icon', '')} Top {item.get('rank', i+1)}</div>
                        <div style="font-size: 14px; font-weight: 700; color: #1B4FD8;"><a href="{item.get('author_link', '#')}" target="_blank">{item.get('author_name', '-')}</a></div>
                        <div style="font-size: 28px; font-weight: 700; color: #374151; margin: 8px 0;">{item.get('viral_count', 0)}</div>
                        <div style="font-size: 11px; color: #6B7280;">条爆款 ｜ {item.get('author_id', '-')}</div>
                    </div>
                    """, unsafe_allow_html=True)
        viral_videos = section_3.get('viral_videos_top10', {})
        if viral_videos.get('rows'):
            st.markdown(f"#### 爆款稿件 Top 10（≥{section_3.get('viral_threshold', 50000)//10000}万播放）")
            df = pd.DataFrame(viral_videos['rows'])
            display_cols = [c for c in ['rank', 'title', 'platform', 'author_name', 'author_id', 'plays_display', 'likes_display'] if c in df.columns]
            st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
        content_type = section_3.get('content_type_analysis', {})
        if content_type.get('table'):
            st.markdown("#### 爆款内容类型归因")
            if content_type.get('summary'):
                render_insight_box(content_type['summary'])
            st.dataframe(pd.DataFrame(content_type['table']), use_container_width=True, hide_index=True)
        for table_key, table_title in [('avg_plays_up_top10', '条均播放 增幅 Top 10'), ('avg_plays_down_top10', '条均播放 降幅 Top 10')]:
            table_data = section_3.get(table_key, {})
            if table_data.get('rows'):
                st.markdown(f"#### {table_title}")
                df = pd.DataFrame(table_data['rows'])
                display_cols = [c for c in ['rank', 'author_name', 'author_id', 'prev_avg_display', 'cur_avg_display', 'chg_display', 'fans_display', 'platform'] if c in df.columns]
                st.dataframe(df[display_cols], use_container_width=True, hide_index=True)

# 板块四：活动维度
section_4 = data.get('section_4_activities', {})
if section_4.get('enabled', True):
    with st.expander("四、活动维度", expanded=True):
        st.markdown(f'<div class="data-source">📊 数据来源：{section_4.get("data_source", "-")}</div>', unsafe_allow_html=True)
        insight_box = section_4.get('insight_box', {})
        if insight_box:
            render_insight_box(insight_box.get('insight'), insight_box.get('risk'))
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

# 板块五：直播维度
section_5 = data.get('section_5_livestream', {})
if section_5.get('enabled', False):
    with st.expander("五、直播维度", expanded=True):
        st.markdown(f'<div class="data-source">📊 数据来源：{section_5.get("data_source", "-")}</div>', unsafe_allow_html=True)
        insight_box = section_5.get('insight_box', {})
        if insight_box:
            render_insight_box(insight_box.get('insight'), insight_box.get('risk'))
        kpi_cards = section_5.get('kpi_cards', {})
        if kpi_cards.get('items'):
            render_kpi_cards(kpi_cards['items'], cols=4, show_change=False)
        tier_dist = section_5.get('tier_distribution', {})
        if tier_dist.get('table'):
            thresholds = tier_dist.get('thresholds', {})
            st.markdown(f"#### 主播分层（按ACU：{thresholds.get('tail_label', '<100')} / {thresholds.get('mid_label', '100-1000')} / {thresholds.get('top_label', '≥1000')}）")
            st.markdown(f"<small style='color: #6B7280;'>门槛：头部≥{thresholds.get('top', 1000)} ACU，腰部{thresholds.get('mid', 100)}-{thresholds.get('top', 1000)} ACU</small>", unsafe_allow_html=True)
            st.dataframe(pd.DataFrame(tier_dist['table']), use_container_width=True, hide_index=True)
        top_streamers = section_5.get('top_streamers', {})
        if top_streamers.get('rows'):
            st.markdown("#### 直播作者 Top 10")
            df = pd.DataFrame(top_streamers['rows'])
            display_cols = [c for c in ['rank', 'author_name', 'author_id', 'session_count', 'view_count_display', 'avg_acu_display', 'fans_display', 'platform'] if c in df.columns]
            st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
elif section_5.get('enabled') is False:
    with st.expander("五、直播维度", expanded=False):
        st.info("该板块未启用（JSON中 section_5_livestream.enabled = false）")

# 板块六：核心作者分析
section_6 = data.get('section_6_core_authors', {})
if section_6.get('enabled', False):
    with st.expander("六、核心作者分析", expanded=True):
        st.markdown(f'<div class="data-source">📊 数据来源：{section_6.get("data_source", "-")}</div>', unsafe_allow_html=True)
        if section_6.get('required_input'):
            st.markdown(f"<small style='color: #6B7280;'>需要用户提供：{section_6['required_input']}</small>", unsafe_allow_html=True)
        insight_box = section_6.get('insight_box', {})
        if insight_box:
            render_insight_box(insight_box.get('insight'), insight_box.get('risk'))
        kpi_cards = section_6.get('kpi_cards', {})
        if kpi_cards.get('items'):
            render_kpi_cards(kpi_cards['items'], cols=3, show_change=False)
elif section_6.get('enabled') is False:
    with st.expander("六、核心作者分析", expanded=False):
        st.info("该板块未启用（JSON中 section_6_core_authors.enabled = false）")

# 板块七：下月重点计划
section_7 = data.get('section_7_todos', {})
if section_7.get('enabled', True):
    with st.expander("七、下月重点计划", expanded=True):
        st.markdown(f'<div class="data-source">📊 {section_7.get("data_source", "-")}</div>', unsafe_allow_html=True)
        categories = section_7.get('categories', [])
        if categories:
            for cat in categories:
                st.markdown(f"#### {cat.get('name', '-')}")
                for item in cat.get('items', []):
                    st.markdown(f"- {item}")

# 页脚
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; color: #9CA3AF; font-size: 11px; padding: 20px;">
    创作者运营月报系统 v2.2.1 ｜ 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}
</div>
""", unsafe_allow_html=True)

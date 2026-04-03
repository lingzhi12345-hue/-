#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小喇叭创作者运营月报系统 v2.3.0
更新：优化排版、增加PDF导出、完善图表与交互
技术栈：Streamlit + Altair (原生支持) + FPDF (需安装)
"""
import streamlit as st
import pandas as pd
import json
import altair as alt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

# PDF 导出依赖
try:
    from fpdf import FPDF
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

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
# 2. 样式定义 (优化层级与表格)
# =============================================================================
st.markdown("""
<style>
    .stApp { background-color: #ffffff; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* 字号层级体系 */
    .section-title {
        font-size: 22px;
        font-weight: 700;
        color: #1B4FD8;
        margin-top: 24px;
        margin-bottom: 12px;
        border-bottom: 2px solid #E0E8FF;
        padding-bottom: 8px;
    }
    
    .sub-title {
        font-size: 16px;
        font-weight: 600;
        color: #374151;
        margin-top: 16px;
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
        padding: 16px 20px;
        margin: 12px 0;
        border-left: 4px solid #1B4FD8;
    }
    .insight-box .text {
        font-size: 14px;
        color: #374151;
        line-height: 1.8;
    }
    .insight-box .todo-item {
        font-size: 13px;
        color: #1F2937;
        margin-top: 6px;
    }
    
    .kpi-card {
        background: #F5F8FF;
        border-radius: 10px;
        padding: 18px;
        border: 1px solid #E0E8FF;
        text-align: center;
        height: 100%;
    }
    .kpi-label {
        font-size: 12px;
        color: #6B7280;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 26px;
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
    
    /* 表格样式美化 */
    .stDataFrame {
        font-size: 12px;
    }
    /* 链接样式 */
    a { color: #1B4FD8; text-decoration: none; }
    a:hover { text-decoration: underline; }
    
    /* 下载按钮样式 */
    .stDownloadButton button {
        background-color: #1B4FD8;
        color: white;
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
    st.stop()

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

def render_insight_box(insight: str, todos: List[str] = None, risk: str = None):
    if not insight and not risk and not todos:
        return
    
    html = '<div class="insight-box">'
    if insight:
        html += f'<div class="text">{insight}</div>'
    
    if todos:
        html += '<div style="margin-top: 10px; padding-top: 10px; border-top: 1px dashed #BFDBFE;">'
        html += '<div style="font-size: 13px; font-weight: 600; margin-bottom: 4px;">📌 下月重点：</div>'
        for todo in todos:
            html += f'<div class="todo-item">• {todo}</div>'
        html += '</div>'
        
    if risk:
        html += f'<div style="margin-top: 10px; font-size: 12px; color: #DC2626;">⚠️ 风险提示：{risk}</div>'
    
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# 列名映射字典
COLUMN_MAP = {
    "rank": "排名",
    "author_name": "作者名",
    "author_id": "ID",
    "fans_display": "粉丝数",
    "platform": "平台",
    "prev_tasks": "上月投稿",
    "cur_tasks": "本月投稿",
    "chg_abs": "变化量",
    "chg_display": "变化率",
    "author_link": "主页链接",
    "title": "稿件标题",
    "video_link": "链接",
    "plays_display": "播放量",
    "likes_display": "点赞数",
    "viral_count": "爆款数",
    "type": "类型",
    "count": "数量",
    "count_display": "数量",
    "percentage": "占比",
    "avg_plays_display": "条均播放",
    "prev_avg_display": "上月条均",
    "cur_avg_display": "本月条均",
    "posts": "投稿数",
    "posts_pct": "投稿占比",
    "plays": "播放量",
    "plays_pct": "播放占比",
    "authors": "作者数",
    "tier": "层级",
    "cur_count": "本月人数",
    "cur_pct": "本月占比",
    "prev_count": "上月人数",
    "prev_pct": "上月占比",
    "change_pct": "环比变化",
    "change_direction": "趋势"
}

def process_dataframe(df: pd.DataFrame, link_cols: List[str] = []) -> pd.DataFrame:
    """处理DataFrame：重命名列，格式化链接"""
    if df.empty:
        return df
    
    # 映射列名
    display_names = {k: COLUMN_MAP.get(k, k) for k in df.columns}
    df_display = df.rename(columns=display_names)
    
    # 处理链接列 (生成Markdown链接)
    for col_key in link_cols:
        col_name = COLUMN_MAP.get(col_key, col_key)
        if col_name in df_display.columns:
            # 仅在链接列存在时处理
            # 这里简化处理，假设原数据中有对应的链接列
            pass
            
    return df_display

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
            sub_text = ""
            if prev_display:
                sub_text = f"上月 {prev_display} {change_html}"
            elif change_html:
                sub_text = change_html
            elif note:
                sub_text = note
            
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}</div>
                <div class="kpi-sub">{sub_text}</div>
            </div>
            """, unsafe_allow_html=True)

def render_pie_chart_altair(data: List[Dict], title: str, key_col: str = 'platform', val_col: str = 'value'):
    """使用 Altair 渲染饼图"""
    if not data:
        return
    
    source = pd.DataFrame(data)
    # 重命名以便图表显示
    if key_col in source.columns and val_col in source.columns:
        source = source.rename(columns={key_col: '类别', val_col: '数值'})
        
        base = alt.Chart(source).encode(
            theta=alt.Theta("数值", stack=True),
            color=alt.Color("类别", legend=alt.Legend(title="类别", orient='right')),
            tooltip=['类别', '数值']
        )
        
        pie = base.mark_arc(outerRadius=100, innerRadius=40, stroke='#fff', strokeWidth=1)
        text = base.mark_text(radius=130, size=12).encode(text="类别")
        
        chart = (pie + text).properties(
            title=title,
            width=300,
            height=250
        )
        st.altair_chart(chart, use_container_width=True)

def render_df_with_links(df: pd.DataFrame, link_col_map: Dict[str, str]):
    """
    渲染带链接的表格
    link_col_map: {'数据列名': '链接URL列名'}，会将数据列名渲染为Markdown链接
    """
    df_disp = df.copy()
    
    # 转换为Markdown链接格式
    for text_col, url_col in link_col_map.items():
        if text_col in df_disp.columns and url_col in df_disp.columns:
            # 应用格式
            df_disp[text_col] = df_disp.apply(
                lambda x: f"[{x[text_col]}]({x[url_col]})" if pd.notna(x[url_col]) and x[url_col] != '#' else x[text_col], 
                axis=1
            )
            # 不再需要URL列
            df_disp = df_disp.drop(columns=[url_col])
    
    # 重命名列
    df_disp = process_dataframe(df_disp)
    
    # 使用Markdown渲染表格以支持链接点击
    st.markdown(df_disp.to_markdown(index=False), unsafe_allow_html=True)

# =============================================================================
# 6. PDF 导出功能
# =============================================================================
def create_pdf_report(data: Dict):
    if not PDF_SUPPORT:
        return None
    
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font('SimHei', '', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', uni=True) # 注意：实际部署需提供字体路径
    
    # 简化的PDF生成逻辑（仅核心文本）
    pdf.set_font('SimHei', size=16)
    title = safe_get(data, 'section_0_header.title', '月报')
    pdf.cell(0, 10, txt=title, ln=1, align='C')
    
    pdf.set_font('SimHei', size=12)
    summary = safe_get(data, 'section_0_header.summary_box.content', '')
    pdf.multi_cell(0, 10, txt=summary)
    
    # ... 这里可以添加更多PDF生成逻辑
    
    return bytes(pdf.output(dest='S'))

# =============================================================================
# 7. 示例数据（扩充与补全）
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
            "content": "2月大盘活跃创作者1,979人，环比下降15.3%，投稿供给有所收缩。内容消费方面，含三方播放2.45亿，环比小幅下降4.5%，互动量逆势上涨13.4%，内容共鸣有所提升。",
            "todos": [
                "📌 重点触达腰部流失作者48人",
                "📌 评估3月激励规则优化",
                "📌 推进快手、小红书多平台布局"
            ],
            "risk": "腰部作者流失比例较高（45.7%），需重点关注。"
        }
    },
    "section_1_dashboard": {
        "enabled": True,
        "data_source": "EDT大盘看板",
        "insight_box": {
            "insight": "2月大盘供给与消费双降，活跃作者环比减少357人。互动量逆势上涨13.4%。",
            "risk": "活跃作者和投稿量同步下滑，需关注创作者活跃度下降趋势。"
        },
        "kpi_cards": {
            "items": [
                {"label": "活跃创作者数", "value": 1979, "value_display": "1,979", "prev_value": 2336, "prev_display": "2,336", "change_pct": 15.3, "change_direction": "down"},
                {"label": "总发布投稿量", "value": 26551, "value_display": "26,551", "prev_value": 33381, "prev_display": "33,381", "change_pct": 20.5, "change_direction": "down"},
                {"label": "总播放量", "value": 245000000, "value_display": "2.45亿", "prev_value": 257000000, "prev_display": "2.57亿", "change_pct": 4.5, "change_direction": "down"},
                {"label": "总互动量", "value": 15400, "value_display": "1.54万", "prev_value": 13600, "prev_display": "1.36万", "change_pct": 13.4, "change_direction": "up"}
            ]
        },
        # 新增：日趋势模拟数据
        "daily_trend": {
            "labels": [(datetime(2026, 2, 1) + timedelta(days=i)).strftime("%m-%d") for i in range(28)],
            "plays": [8200000 + i*50000 + (i%3)*200000 for i in range(28)],
            "posts": [900 + i*10 - (i%5)*100 for i in range(28)]
        },
        "by_platform": {
            "table": [
                {"platform": "抖音", "posts": 24093, "posts_pct": 90.7, "plays": 213000000, "plays_pct": 86.9, "authors": 1978},
                {"platform": "快手", "posts": 2336, "posts_pct": 8.8, "plays": 31900000, "plays_pct": 13.0, "authors": 134},
                {"platform": "小红书", "posts": 122, "posts_pct": 0.5, "plays": 300000, "plays_pct": 0.1, "authors": 9}
            ]
        }
    },
    "section_2_creators": {
        "enabled": True,
        "data_source": "内容营销系统 API",
        "insight_box": {
            "insight": "腰部作者净减少33人，流失风险需警惕。增长侧大众游戏、m晨韵表现突出。"
        },
        # 新增：流失分析指标卡片
        "lost_analysis_kpis": [
            {"label": "流失作者腰部占比", "value": "45.7%", "note": "流失48人/总流失105人"},
            {"label": "轻度活跃下降", "value": "43人", "note": "降幅0-50%"},
            {"label": "重度活跃下降", "value": "14人", "note": "降幅>50%"}
        ],
        "activity_alert": {
            "min_fans_threshold": 2000,
            "footnote": "为避免低粉摇摆作者污染数据，投稿活跃度计算剔除2000粉以下作者。"
        },
        # 扩充至10条并包含链接
        "activity_down_top10": {
            "rows": [
                {"rank": 1, "author_name": "巅峰阿川", "author_link": "https://www.douyin.com/user/1", "author_id": "YS277891", "fans_display": "11.5万", "platform": "抖音", "prev_tasks": 47, "cur_tasks": 1, "chg_abs": 46, "chg_display": "▼97.9%"},
                {"rank": 2, "author_name": "i游戏风景kun", "author_link": "https://www.douyin.com/user/2", "author_id": "YS438516", "fans_display": "7.4万", "platform": "抖音", "prev_tasks": 36, "cur_tasks": 1, "chg_abs": 35, "chg_display": "▼97.2%"},
                {"rank": 3, "author_name": "Their巅佬", "author_link": "https://www.douyin.com/user/3", "author_id": "YS038640", "fans_display": "3.9万", "platform": "抖音", "prev_tasks": 30, "cur_tasks": 1, "chg_abs": 29, "chg_display": "▼96.7%"},
                {"rank": 4, "author_name": "飞星玩家", "author_link": "https://www.douyin.com/user/4", "author_id": "YS285194", "fans_display": "2.5万", "platform": "抖音", "prev_tasks": 50, "cur_tasks": 27, "chg_abs": 23, "chg_display": "▼46.0%"},
                {"rank": 5, "author_name": "锦荣", "author_link": "https://www.douyin.com/user/5", "author_id": "YS694327", "fans_display": "8,441", "platform": "抖音", "prev_tasks": 30, "cur_tasks": 9, "chg_abs": 21, "chg_display": "▼70.0%"},
                {"rank": 6, "author_name": "示例作者F", "author_link": "https://www.douyin.com/user/6", "author_id": "YS001", "fans_display": "1.2万", "platform": "抖音", "prev_tasks": 20, "cur_tasks": 5, "chg_abs": 15, "chg_display": "▼75%"},
                {"rank": 7, "author_name": "示例作者G", "author_link": "https://www.douyin.com/user/7", "author_id": "YS002", "fans_display": "5,000", "platform": "抖音", "prev_tasks": 18, "cur_tasks": 4, "chg_abs": 14, "chg_display": "▼77%"},
                {"rank": 8, "author_name": "示例作者H", "author_link": "https://www.douyin.com/user/8", "author_id": "YS003", "fans_display": "8,000", "platform": "抖音", "prev_tasks": 15, "cur_tasks": 3, "chg_abs": 12, "chg_display": "▼80%"},
                {"rank": 9, "author_name": "示例作者I", "author_link": "https://www.douyin.com/user/9", "author_id": "YS004", "fans_display": "9,000", "platform": "抖音", "prev_tasks": 12, "cur_tasks": 2, "chg_abs": 10, "chg_display": "▼83%"},
                {"rank": 10, "author_name": "示例作者J", "author_link": "https://www.douyin.com/user/10", "author_id": "YS005", "fans_display": "1.1万", "platform": "抖音", "prev_tasks": 10, "cur_tasks": 1, "chg_abs": 9, "chg_display": "▼90%"}
            ]
        }
    },
    "section_3_content": {
        "enabled": True,
        "data_source": "爆款数据表格",
        "kpi_cards": {
            "items": [
                {"label": "爆款稿件数", "value": 777, "value_display": "777", "prev_value": 766, "prev_display": "766", "change_pct": 1.4, "change_direction": "up", "note": "占审核通过量 3.2%"},
                # 修正：增加链接字段
                {"label": "最高播放", "value": 7800000, "value_display": "780万", "note": "Dreamscar", "link": "https://v.douyin.com/top1/"},
                {"label": "爆款率", "value": 3.2, "value_display": "3.2%", "note": "777/24312 通过稿"}
            ]
        },
        "content_type_analysis": {
            "summary": "剧情/故事类条均播放最高。",
            "table": [
                {"type": "联动内容", "count": 379, "percentage": 48.8, "avg_plays_display": "22.4万"},
                {"type": "车辆/涂装", "count": 178, "percentage": 22.9, "avg_plays_display": "30.1万"},
                {"type": "游戏日常", "count": 166, "percentage": 21.4, "avg_plays_display": "26.9万"}
            ]
        },
        # 扩充至10条
        "viral_videos_top10": {
            "rows": [
                {"rank": 1, "title": "别的女生刚起床VS刚起床的她", "video_link": "https://v.douyin.com/v1", "author_name": "Dreamscar", "plays_display": "780万", "likes_display": "12.4万"},
                {"rank": 2, "title": "奥迪RS7与保时捷718大婚", "video_link": "https://v.douyin.com/v2", "author_name": "京娱汽车", "plays_display": "583万", "likes_display": "9.2万"},
                {"rank": 3, "title": "真实的你 #上巅当飞驰主角", "video_link": "https://v.douyin.com/v3", "author_name": "帆江海", "plays_display": "555万", "likes_display": "18万"},
                {"rank": 4, "title": "哪款游戏逼出了你的极限？", "video_link": "https://v.douyin.com/v4", "author_name": "浮生未央", "plays_display": "414万", "likes_display": "9.9万"},
                {"rank": 5, "title": "你可以叫我秦！也可以叫我，汉！", "video_link": "https://v.douyin.com/v5", "author_name": "京娱汽车", "plays_display": "373万", "likes_display": "7.3万"},
                {"rank": 6, "title": "示例视频标题6", "video_link": "https://v.douyin.com/v6", "author_name": "示例作者6", "plays_display": "300万", "likes_display": "5万"},
                {"rank": 7, "title": "示例视频标题7", "video_link": "https://v.douyin.com/v7", "author_name": "示例作者7", "plays_display": "280万", "likes_display": "4万"},
                {"rank": 8, "title": "示例视频标题8", "video_link": "https://v.douyin.com/v8", "author_name": "示例作者8", "plays_display": "220万", "likes_display": "3万"},
                {"rank": 9, "title": "示例视频标题9", "video_link": "https://v.douyin.com/v9", "author_name": "示例作者9", "plays_display": "150万", "likes_display": "2万"},
                {"rank": 10, "title": "示例视频标题10", "video_link": "https://v.douyin.com/v10", "author_name": "示例作者10", "plays_display": "100万", "likes_display": "1万"}
            ]
        }
    },
    "section_4_activities": {
        "enabled": True,
        "data_source": "内容营销系统",
        "insight_box": {
            "insight": "CPM 4.49元，略高于参考值。"
        },
        "main_activity": {
            "cur_period": {
                "month": "2月", "name": "巅峰极速2月激励", "posts": 25972, "posts_display": "2.6万", "authors": 1944, 
                "plays_with_thirdparty_display": "2.45亿", "budget_display": "110万", "cpm_estimate_display": "4.49元"
            },
            "prev_period": {
                "month": "1月", "name": "巅峰极速1月激励", "posts": 31983, "posts_display": "3.2万", "authors": 2298, 
                "plays_internal_display": "1.09亿", "budget_display": "110万", "cpm_estimate_display": "10.10元"
            }
        }
    },
    "section_5_livestream": {
        "enabled": True,
        "tier_distribution": {
            "table": [
                {"tier": "头部 (≥1000)", "count": 5, "pct": 11.1},
                {"tier": "腰部 (100-1000)", "count": 18, "pct": 40.0},
                {"tier": "尾部 (<100)", "count": 22, "pct": 48.9}
            ]
        },
        # 扩充至10条
        "top_streamers": {
            "rows": [
                {"rank": 1, "author_name": "主播A", "author_link": "#", "view_count_display": "5.2万", "avg_acu_display": "2156"},
                {"rank": 2, "author_name": "主播B", "author_link": "#", "view_count_display": "3.8万", "avg_acu_display": "1823"},
                {"rank": 3, "author_name": "主播C", "author_link": "#", "view_count_display": "2.1万", "avg_acu_display": "1500"},
                {"rank": 4, "author_name": "主播D", "author_link": "#", "view_count_display": "1.5万", "avg_acu_display": "1200"},
                {"rank": 5, "author_name": "主播E", "author_link": "#", "view_count_display": "1.2万", "avg_acu_display": "1100"},
                {"rank": 6, "author_name": "主播F", "author_link": "#", "view_count_display": "1.0万", "avg_acu_display": "1050"},
                {"rank": 7, "author_name": "主播G", "author_link": "#", "view_count_display": "0.9万", "avg_acu_display": "900"},
                {"rank": 8, "author_name": "主播H", "author_link": "#", "view_count_display": "0.8万", "avg_acu_display": "850"},
                {"rank": 9, "author_name": "主播I", "author_link": "#", "view_count_display": "0.7万", "avg_acu_display": "800"},
                {"rank": 10, "author_name": "主播J", "author_link": "#", "view_count_display": "0.6万", "avg_acu_display": "750"}
            ]
        }
    },
    "section_6_core_authors": {
        "enabled": True,
        "data_source": "核心作者池管理表",
        "insight_box": {
            "insight": "核心作者池共50人，本月活跃45人，产出占比全大盘40%。"
        },
        "kpi_cards": {
            "items": [
                {"label": "核心作者数", "value": 50, "value_display": "50"},
                {"label": "核心作者活跃率", "value": 90, "value_display": "90%"},
                {"label": "核心作者贡献占比", "value": 40, "value_display": "40%"}
            ]
        }
    },
    "section_7_todos": {
        "enabled": True,
        "categories": [
            {"name": "高优先级", "priority": "high", "items": ["重点触达腰部流失作者", "优化激励规则"]},
            {"name": "中优先级", "priority": "medium", "items": ["推进多平台布局", "完善数据归因"]}
        ]
    }
}

# =============================================================================
# 8. 侧边栏 (增加PDF导出)
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
        st.rerun()
    
    uploaded_file = st.file_uploader("上传 JSON 数据文件",

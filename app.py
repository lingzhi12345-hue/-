import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import shutil

# --- 配置部分 ---
st.set_page_config(layout="wide", page_title="光遇绿灯专区监测看板")
st.title("光遇绿灯专区监测看板")

# --- 定义共享文件路径 ---
SHARED_FILE_PATH = "shared_uploaded_data.xlsx"

# --- 功能函数 ---

def get_period_info(date):
    """
    判断日期属于哪一期，并计算相对天数
    返回：(期数标签, 相对天数) 或 (None, None)
    """
    year = date.year
    
    # 定义两期的开始日期
    start_p1 = datetime(year, 2, 1)
    start_p2 = datetime(year, 4, 1)
    
    # 定义分析窗口范围（开始前15天 到 结束后15天）
    end_p1 = datetime(year, 2, 28)
    end_p2 = datetime(year, 4, 30)
    
    # 第一期窗口：1月16日 - 3月15日
    if datetime(year, 1, 16) <= date <= (end_p1 + timedelta(days=15)):
        delta = (date - start_p1).days
        return "第一期", delta
    
    # 第二期窗口：3月16日 - 5月15日
    if datetime(year, 3, 16) <= date <= (end_p2 + timedelta(days=15)):
        delta = (date - start_p2).days
        return "第二期", delta
    
    return None, None

def get_green_period(date):
    """
    判断日期属于哪个绿灯专区周期
    返回："第一期绿灯"、"第二期绿灯"、"普通专区"
    """
    year = date.year
    
    # 第一期绿灯：2.1-2.28
    if datetime(year, 2, 1) <= date <= datetime(year, 2, 28):
        return "第一期绿灯"
    
    # 第二期绿灯：4.1至今
    if datetime(year, 4, 1) <= date <= datetime(year, 4, 30):
        return "第二期绿灯"
    
    return "普通专区"

# --- 主程序 ---

st.info("说明：上传文件后，数据将共享给所有访问此链接的人。刷新页面可查看他人最新上传的数据。")

uploaded_file = st.file_uploader("上传 Excel 文件 (上传将覆盖当前共享数据)", type=['xlsx', 'xls'])

source_file = None

# 情况1：如果有用户上传了新文件
if uploaded_file is not None:
    try:
        with open(SHARED_FILE_PATH, "wb") as f:
            shutil.copyfileobj(uploaded_file, f)
        st.success("文件已更新并共享！所有用户刷新页面即可看到最新数据。")
        source_file = uploaded_file
    except Exception as e:
        st.error(f"保存共享文件失败: {e}。")
        source_file = uploaded_file

# 情况2：如果没有上传文件，但本地存在之前共享的文件
elif os.path.exists(SHARED_FILE_PATH):
    st.info(f"当前展示的是共享数据文件。如需更新请上传新文件。")
    source_file = SHARED_FILE_PATH

# 情况3：既没上传，也没共享文件
else:
    st.warning("暂无数据，请上传 Excel 文件。")

# --- 处理逻辑 ---
if source_file:
    try:
        # 1. 读取数据
        df = pd.read_excel(source_file)
        
        # 2. 字段映射
        rename_dict = {
            "指标日期": "日期",
            "大盘作者贡献播放次数": "播放量",
            "游戏投稿UV": "供给量"
        }
        df.rename(columns=rename_dict, inplace=True)

        # 检查必要列
        if '日期' not in df.columns:
            st.error("Excel中未找到'日期'列，请检查表头！")
        else:
            df['日期'] = pd.to_datetime(df['日期'])
            
            # 3. 计算期数和相对天数
            df[['期数', '相对天数']] = df['日期'].apply(lambda x: pd.Series(get_period_info(x)))
            
            # 判断绿灯周期
            df['绿灯周期'] = df['日期'].apply(get_green_period)
            
            # 过滤掉不属于任何一期的数据
            df_analysis = df.dropna(subset=['期数', '相对天数']).copy()
            df_analysis['相对天数'] = df_analysis['相对天数'].astype(int)
            
            # 按天聚合数据
            df_grouped = df_analysis.groupby(['期数', '相对天数', '绿灯周期'])[['播放量', '供给量']].sum().reset_index()
            
            # 添加原始日期用于显示
            df_grouped = df_grouped.merge(
                df_analysis[['期数', '相对天数', '日期', '绿灯周期']].drop_duplicates(),
                on=['期数', '相对天数', '绿灯周期'],
                how='left'
            )
            
            # 4. 计算日环比增幅（当天相对前一天的增幅）
            def calc_daily_growth(group, col):
                """
                计算日环比增幅：(当天值 - 前一天值) / 前一天值
                """
                group = group.sort_values('相对天数')
                values = group[col].values
                growth = [0]  # 第一天增幅设为0（没有前一天数据）
                
                for i in range(1, len(values)):
                    if values[i-1] != 0:
                        g = (values[i] - values[i-1]) / values[i-1]
                    else:
                        g = 0
                    growth.append(g)
                
                group[f'{col}_日环比增幅'] = growth
                return group

            # 分别对两期计算日环比增幅
            df_final = pd.DataFrame()
            for period in df_grouped['期数'].unique():
                period_data = df_grouped[df_grouped['期数'] == period].copy()
                period_data = calc_daily_growth(period_data, '播放量')
                period_data = calc_daily_growth(period_data, '供给量')
                df_final = pd.concat([df_final, period_data])
            
            # 播放量转换为千万单位
            df_final['播放量_千万'] = df_final['播放量'] / 10000000
            
            # ========== 全周期概览板块 ==========
            st.markdown("---")
            st.subheader("全周期播放量 & 供给量概览")
            
            # 创建双轴图：柱状图(播放量) + 折线(供给量)
            fig_overview = go.Figure()
            
            # 获取数据日期范围
            all_dates = df_final['日期'].sort_values()
            min_date = pd.Timestamp(all_dates.min()).to_pydatetime()
            max_date = pd.Timestamp(all_dates.max()).to_pydatetime()
            
            # 添加周末背景（周六+周日）
            weekend_shapes = []
            current = min_date
            while current <= max_date:
                if current.weekday() == 5:  # 周六
                    weekend_shapes.append(dict(
                        type="rect",
                        xref="x", yref="paper",
                        x0=current, 
                        x1=current + timedelta(days=2),
                        y0=0, y1=1,
                        fillcolor="rgba(200, 200, 200, 0.2)",
                        layer="below",
                        line_width=0
                    ))
                current = current + timedelta(days=1)
            
            # 颜色映射
            color_map = {
                "第一期绿灯": "#1f77b4",  # 蓝色
                "第二期绿灯": "#ff7f0e",  # 橙色
                "普通专区": "#7f7f7f"     # 灰色
            }
            
            # 按绿灯周期分组绘制柱状图
            for green_period in ["第一期绿灯", "普通专区", "第二期绿灯"]:
                subset = df_final[df_final['绿灯周期'] == green_period].sort_values('日期')
                if not subset.empty:
                    fig_overview.add_trace(go.Bar(
                        x=subset['日期'],
                        y=subset['播放量_千万'],
                        name=green_period,
                        marker_color=color_map[green_period],
                        yaxis='y',
                        hovertemplate=f'{green_period} %{{x|%m/%d}}<br>播放量: %{{y:.2f}}千万<extra></extra>'
                    ))
                    
                    # 找峰值点（只标注两期绿灯的峰值）
                    if green_period in ["第一期绿灯", "第二期绿灯"]:
                        peak_idx = subset['播放量_千万'].idxmax()
                        if pd.notna(peak_idx):
                            peak = subset.loc[peak_idx]
                            fig_overview.add_trace(go.Scatter(
                                x=[peak['日期']],
                                y=[peak['播放量_千万']],
                                mode='markers+text',
                                marker=dict(size=12, color=color_map[green_period], symbol='star'),
                                text=['峰值'],
                                textposition='top center',
                                name=f'{green_period}峰值',
                                yaxis='y',
                                showlegend=False
                            ))
            
            # 供给量：连续一条线，不分期数
            all_data_sorted = df_final.sort_values('日期')
            fig_overview.add_trace(go.Scatter(
                x=all_data_sorted['日期'],
                y=all_data_sorted['供给量'],
                name='供给量',
                mode='lines',
                line=dict(color='#2ca02c', width=2),
                yaxis='y2',
                hovertemplate='%{x|%m/%d}<br>供给量: %{y:,}<extra></extra>'
            ))
            
            # 设置双轴布局
            fig_overview.update_layout(
                xaxis=dict(
                    title='日期',
                    type='date',
                    tickformat='%m/%d'
                ),
                yaxis=dict(
                    title=dict(text='播放量(千万)', font=dict(color='#333')),
                    tickfont=dict(color='#333'),
                    side='left'
                ),
                yaxis2=dict(
                    title=dict(text='供给量', font=dict(color='#2ca02c')),
                    tickfont=dict(color='#2ca02c'),
                    side='right',
                    overlaying='y'
                ),
                hovermode='x unified',
                template='plotly_white',
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
                barmode='group',
                height=400,
                shapes=weekend_shapes
            )
            
            st.plotly_chart(fig_overview, use_container_width=True)
            
            # 图例说明
            st.markdown("""
            - ⬛ **灰色背景**：周末
            """)
            
            # ========== 分项趋势图 ==========
            st.markdown("---")
            st.subheader("分项趋势对比")
            
            # 5. 绘图
            def plot_chart(data, y_col, title, is_percentage=False, y_title=None):
                fig = go.Figure()
                
                styles = {
                    "第一期": {'dash': 'solid', 'color': '#1f77b4'},
                    "第二期": {'dash': 'dash', 'color': '#ff7f0e'}
                }
                
                for period_name in ["第一期", "第二期"]:
                    subset = data[data['期数'] == period_name]
                    if not subset.empty:
                        fig.add_trace(go.Scatter(
                            x=subset['相对天数'],
                            y=subset[y_col],
                            mode='lines+markers',
                            name=period_name,
                            line=dict(color=styles[period_name]['color'], dash=styles[period_name]['dash']),
                            marker=dict(size=6),
                            hovertemplate='%{y:.2f}<extra></extra>'
                        ))
                
                fig.update_layout(
                    title=title,
                    xaxis_title="相对天数 (Day 0 = 绿灯专区开始日期)",
                    yaxis_title=y_title if y_title else title.split('趋势')[0],
                    hovermode="x unified",
                    template="plotly_white"
                )
                
                if is_percentage:
                    fig.update_layout(yaxis_tickformat='.1%')
                
                st.plotly_chart(fig, use_container_width=True)

            # 展示图表
            col1, col2 = st.columns(2)
            
            with col1:
                plot_chart(df_final, '播放量_千万', '播放量趋势对比', y_title='播放量(千万)')
                plot_chart(df_final, '播放量_日环比增幅', '播放量日环比增幅', is_percentage=True)
            
            with col2:
                plot_chart(df_final, '供给量', '供给量趋势对比')
                plot_chart(df_final, '供给量_日环比增幅', '供给量日环比增幅', is_percentage=True)
            
            # 6. 数据预览
            with st.expander("查看处理后的详细数据"):
                # 格式化显示
                display_df = df_final[['期数', '相对天数', '绿灯周期', '日期', '播放量', '播放量_千万', '播放量_日环比增幅', '供给量', '供给量_日环比增幅']].copy()
                display_df['日期'] = display_df['日期'].dt.strftime('%Y-%m-%d')
                display_df['播放量'] = display_df['播放量'].apply(lambda x: f"{x:,.0f}")
                display_df['播放量_千万'] = display_df['播放量_千万'].apply(lambda x: f"{x:.2f}")
                display_df['播放量_日环比增幅'] = display_df['播放量_日环比增幅'].apply(lambda x: f"{x*100:+.1f}%")
                display_df['供给量'] = display_df['供给量'].apply(lambda x: f"{x:,.0f}")
                display_df['供给量_日环比增幅'] = display_df['供给量_日环比增幅'].apply(lambda x: f"{x*100:+.1f}%")
                
                st.dataframe(display_df.sort_values(by=['期数', '相对天数']))

    except Exception as e:
        st.error(f"处理文件时出错: {e}")
        import traceback
        st.code(traceback.format_exc())

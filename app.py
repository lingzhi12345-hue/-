import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- 配置部分 ---
st.set_page_config(layout="wide", page_title="光遇绿灯专区监测看板")
st.title("光遇绿灯专区监测看板")

# --- 功能函数 ---

def get_period_info(date):
    """
    判断日期属于哪一期，并计算相对天数
    返回：(期数标签, 相对天数) 或
    """
    # 获取年份，确保能构造日期
    year = date.year
    
    # 定义两期的开始日期
    start_p1 = datetime(year, 2, 1)
    start_p2 = datetime(year, 4, 1)
    
    # 定义分析窗口范围（开始前15天 到 结束后15天，足够覆盖你需要的前10后10）
    # 第一期结束是2月28日
    end_p1 = datetime(year, 2, 28)
    # 第二期结束是4月30日
    end_p2 = datetime(year, 4, 30)
    
    # 窗口范围判断
    # 第一期窗口：1月16日 - 3月10日左右
    if datetime(year, 1, 16) <= date <= (end_p1 + timedelta(days=15)):
        delta = (date - start_p1).days
        return "第一期", delta
    
    # 第二期窗口：3月16日 - 5月15日左右
    if datetime(year, 3, 16) <= date <= (end_p2 + timedelta(days=15)):
        delta = (date - start_p2).days
        return "第二期", delta
        
    return None, None

# --- 主程序 ---

uploaded_file = st.file_uploader("上传 Excel 文件", type=['xlsx', 'xls'])

if uploaded_file:
    try:
        # 1. 读取数据
        df = pd.read_excel(uploaded_file)
        
        # 2. 字段映射
        rename_dict = {
            "指标日期": "日期",  # <--- 新增这一行映射
            "大盘作者贡献播放次数": "播放量",
            "游戏投稿UV": "供给量"
        }
        df.rename(columns=rename_dict, inplace=True)

        # 检查必要列
        if '日期' not in df.columns:
            st.error("Excel中未找到'日期'列，请检查表头！")
        else:
        # 确保日期格式正确
        df['日期'] = pd.to_datetime(df['日期'])
            
            # 3. 计算期数和相对天数
            # 应用函数，生成两列新数据
            df[['期数', '相对天数']] = df['日期'].apply(lambda x: pd.Series(get_period_info(x)))
            
            # 过滤掉不属于任何一期的数据
            df_analysis = df.dropna(subset=['期数', '相对天数']).copy()
            df_analysis['相对天数'] = df_analysis['相对天数'].astype(int)
            
            # 按天聚合数据 (防止同一天有多条数据)
            df_grouped = df_analysis.groupby(['期数', '相对天数'])[['播放量', '供给量']].sum().reset_index()
            
            # 4. 计算增幅 (相对于 Day 0)
            # 定义计算增幅的函数
            def calc_growth(group, col):
                # 找到 Day 0 的值
                day0_val = group.loc[group['相对天数'] == 0, col].values
                if len(day0_val) > 0 and day0_val[0] != 0:
                    base_val = day0_val[0]
                    group[f'{col}_增幅'] = (group[col] - base_val) / base_val
                else:
                    group[f'{col}_增幅'] = 0 # 如果没有基准日或基准为0，增幅设为0或空
                return group

            # 分别对两期计算增幅
            df_final = pd.DataFrame()
            for period in df_grouped['期数'].unique():
                period_data = df_grouped[df_grouped['期数'] == period].copy()
                period_data = calc_growth(period_data, '播放量')
                period_data = calc_growth(period_data, '供给量')
                df_final = pd.concat([df_final, period_data])
            
            # 5. 绘图
            # 创建4个图表：播放量、播放增幅、供给量、供给增幅
            
            def plot_chart(data, y_col, title, is_percentage=False):
                fig = go.Figure()
                
                # 定义两期的样式
                styles = {
                    "第一期": {'dash': 'solid', 'color': '#1f77b4'}, # 实线蓝色
                    "第二期": {'dash': 'dash', 'color': '#ff7f0e'}  # 虚线橙色
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
                            marker=dict(size=6)
                        ))
                
                # 设置X轴刻度
                # 生成特定的刻度标签：前10、当天、后10...
                # 这里我们让刻度显示相对天数，但重点突出关键节点
                tickvals = [-10, 0, 10, 20, 30]
                # 额外添加结束后10天的位置 (第一期Day37, 第二期Day39)
                # 这里简单处理，在X轴范围内显示
                
                fig.update_layout(
                    title=title,
                    xaxis_title="相对天数 (Day 0 = 活动当天)",
                    yaxis_title=title.split('趋势')[0],
                    hovermode="x unified",
                    template="plotly_white"
                )
                
                if is_percentage:
                    fig.update_layout(yaxis_tickformat='.1%')
                    
                st.plotly_chart(fig, use_container_width=True)

            # 展示图表
            col1, col2 = st.columns(2)
            
            with col1:
                plot_chart(df_final, '播放量', '播放量趋势对比')
                plot_chart(df_final, '播放量_增幅', '播放量增幅对比 (vs Day 0)', is_percentage=True)
                
            with col2:
                plot_chart(df_final, '供给量', '供给量趋势对比')
                plot_chart(df_final, '供给量_增幅', '供给量增幅对比 (vs Day 0)', is_percentage=True)
            
            # 6. 数据预览 (可选)
            with st.expander("查看处理后的详细数据"):
                st.dataframe(df_final.sort_values(by=['期数', '相对天数']))

    except Exception as e:
        st.error(f"处理文件时出错: {e}")

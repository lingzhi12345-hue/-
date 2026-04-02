import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- 页面基础配置 ---
st.set_page_config(page_title="数据趋势分析看板", layout="wide")
st.title("📊 光遇绿灯专区监测看板")
st.markdown("请在上传区上传包含 **日期、播放量、供给量** 的 Excel 文件。")

# --- 核心功能函数 ---

def calculate_metrics(df, col_name):
    """
    计算增幅指标：
    1. 日环比增长量 (今天 - 昨天)
    2. 日环比增长率 ((今天 - 昨天) / 昨天)
    3. 7日移动平均 (用于平滑曲线)
    """
    df = df.copy()
    # 计算增长量
    df[f'{col_name}_增长量'] = df[col_name].diff()
    # 计算增长率，处理除以0的情况
    df[f'{col_name}_增长率'] = df[col_name].pct_change() * 100
    # 计算7日移动平均
    df[f'{col_name}_MA7'] = df[col_name].rolling(window=7).mean()
    
    # 填充空值为0，避免图表报错
    df.fillna(0, inplace=True)
    return df

def plot_dual_line_chart(df, x_col, y_col_1, y_col_2, title, yaxis_title):
    """绘制双线折线图"""
    fig = go.Figure()
    
    # 第一条线：原始数据
    fig.add_trace(go.Scatter(
        x=df[x_col], y=df[y_col_1],
        mode='lines', name=y_col_1,
        line=dict(color='#1f77b4', width=2)
    ))
    
    # 第二条线：MA7
    fig.add_trace(go.Scatter(
        x=df[x_col], y=df[y_col_2],
        mode='lines', name=y_col_2,
        line=dict(color='#ff7f0e', width=2, dash='dash') # 虚线区分
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="日期",
        yaxis_title=yaxis_title,
        hovermode="x unified",
        height=400,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig

def plot_growth_chart(df, x_col, val_col, rate_col, title):
    """
    绘制增幅混合图（柱状图+折线图）
    柱状图表示增长量，折线图表示增长率
    """
    fig = go.Figure()
    
    # 柱状图：增长量
    fig.add_trace(go.Bar(
        x=df[x_col], y=df[val_col],
        name='增长量',
        marker_color='#2ca02c',
        yaxis='y'
    ))
    
    # 折线图：增长率
    fig.add_trace(go.Scatter(
        x=df[x_col], y=df[rate_col],
        name='增长率(%)',
        mode='lines+markers',
        marker_color='#d62728',
        yaxis='y2' # 使用右侧坐标轴
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="日期",
        yaxis=dict(title="增长量", side="left"),
        yaxis2=dict(title="增长率 (%)", side="right", overlaying="y", showgrid=False),
        hovermode="x unified",
        height=400,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig

# --- 主程序逻辑 ---

# 1. 文件上传组件
uploaded_file = st.file_uploader("上传 Excel 数据文件", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        # 2. 读取数据
        df = pd.read_excel(uploaded_file)

        # --- 新增：字段映射 ---
        # 将 Excel 中的原始列名映射为代码需要的标准列名
        rename_dict = {
            "大盘作者贡献播放次数": "播放量",
            "游戏投稿UV": "供给量"
        }
        # 应用映射
        df.rename(columns=rename_dict, inplace=True)
        # ---------------------
        
        # 简单的数据清洗：尝试自动识别日期列（假设第一列是日期）或者让用户选择
        # 这里为了简单，假设列名为 '日期'，如果不是，取第一列
        if '日期' not in df.columns:
            df.rename(columns={df.columns[0]: '日期'}, inplace=True)
        
        # 确保日期格式正确
        df['日期'] = pd.to_datetime(df['日期'])
        df = df.sort_values('日期') # 按日期排序
        
        st.success("文件上传成功！数据预览如下：")
        st.dataframe(df.head())
        
        # 3. 数据计算
        # 检查必要的列是否存在
        required_cols = ['播放量', '供给量']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            st.error(f"上传的文件中缺少以下列：{missing_cols}。请检查 Excel 表头是否包含'播放量'和'供给量'。")
        else:
            # 计算播放指标
            df = calculate_metrics(df, '播放量')
            # 计算供给指标
            df = calculate_metrics(df, '供给量')
            
            # 4. 展示图表 (竖向排列)
            st.markdown("---")
            
            # 卡片 1：播放趋势（数值 + MA7）
            st.subheader("1. 播放量趋势")
            fig_play = plot_dual_line_chart(df, '日期', '播放量', '播放量_MA7', '播放量与7日均值', '播放量')
            st.plotly_chart(fig_play, use_container_width=True)
            
            # 卡片 2：播放增幅（增长量 + 增长率）
            st.subheader("2. 播放量增幅分析")
            fig_play_growth = plot_growth_chart(df, '日期', '播放量_增长量', '播放量_增长率', '播放量日环比增幅')
            st.plotly_chart(fig_play_growth, use_container_width=True)
            
            # 卡片 3：供给趋势（数值 + MA7）
            st.subheader("3. 供给量趋势")
            fig_supply = plot_dual_line_chart(df, '日期', '供给量', '供给量_MA7', '供给量与7日均值', '供给量')
            st.plotly_chart(fig_supply, use_container_width=True)
            
            # 卡片 4：供给增幅（增长量 + 增长率）
            st.subheader("4. 供给量增幅分析")
            fig_supply_growth = plot_growth_chart(df, '日期', '供给量_增长量', '供给量_增长率', '供给量日环比增幅')
            st.plotly_chart(fig_supply_growth, use_container_width=True)
            
    except Exception as e:
        st.error(f"处理文件时出错：{e}")
else:
    st.info("等待文件上传...")

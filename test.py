import streamlit as st
import requests
from bs4 import BeautifulSoup
from collections import Counter
import pandas as pd
from pyecharts import options as opts
from pyecharts.charts import Bar, Line, Pie, Scatter, WordCloud, Boxplot, Funnel
from pyecharts.render import make_snapshot
from snapshot_selenium import snapshot as driver
import matplotlib.pyplot as plt
import re
import jieba

# 筛选低频词
def filter_low_frequency_words(counter, threshold=5):
    return {word: count for word, count in counter.items() if count >= threshold}

url = st.text_input('输入网址')
chart_types = st.multiselect('选择你想展示的图表', ['数状图', '折线图', '饼状图', '散点图', '柱状图', '漏斗图', '圆环图'])

if url:
    response = requests.get(url)
    response.encoding = response.apparent_encoding
    soup = BeautifulSoup(response.text, 'html.parser')

    
    #对获取的文本进行处理
    text_content = soup.get_text()
    text_content = re.sub(r'[^\w\s]', '', text_content)
    text_content = text_content.replace(' ', '')
    seg_list = jieba.cut(text_content)
    seg_list = [word for word in seg_list if len(word) > 1]
    word_count = Counter(seg_list)

    # 交互式词频筛选
    threshold = st.sidebar.slider("选择词频阈值", 1, 20, 5)
    filtered_word_count = filter_low_frequency_words(word_count, threshold)

    # 筛选词频前20的词
    top_words = dict(Counter(filtered_word_count).most_common(20))
    data = {'词语': list(top_words.keys()), '频次': list(top_words.values())}
    df = pd.DataFrame(data)
    charts = []
    chart = None
    
    for chart_type in chart_types:
        if chart_type == '数状图':
            chart = Bar().add_xaxis(df['词语'].tolist()).add_yaxis('频次', df['频次'].tolist())
        elif chart_type == '折线图':
            chart = Line().add_xaxis(df['词语'].tolist()).add_yaxis('频次', df['频次'].tolist())
        elif chart_type == '饼状图':
            chart = Pie().add('', list(zip(df['词语'].tolist(), df['频次'].tolist())))
            chart.set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}"))
        elif chart_type == '散点图':
            chart = Scatter().add_xaxis(df['词语'].tolist()).add_yaxis('频次', df['频次'].tolist())
        elif chart_type == '柱状图':
            chart = Bar().add_xaxis(df['词语'].tolist()).add_yaxis('频次', df['频次'].tolist())
        elif chart_type == '漏斗图':
            chart = (Funnel().add("", list(zip(df['词语'].tolist(), df['频次'].tolist())))
            )
        elif chart_type == '圆环图':
            chart = Pie().add("",list(zip(df['词语'].tolist(), df['频次'].tolist())),
                radius=["30%", "70%"])  # 设置内外半径，实现圆环图效果
            chart.set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}"))
    
    if chart is not None:
        charts.append(chart)
    else:
        print(f"No chart generated for chart type: {chart_type}")

    for idx, chart in enumerate(charts):
        try:
            rendered_chart = chart.render()
            make_snapshot(driver, rendered_chart, f'chart_{idx}.png', is_remove_html=True)
            image = plt.imread(f'chart_{idx}.png')
            st.image(image)
        except Exception as e:
            print(f"Error rendering chart {idx}: {e}")
    #生成词云
    wordcloud = WordCloud().add("", list(filtered_word_count.items()), word_size_range=[20, 100])
    wordcloud.set_global_opts(title_opts=opts.TitleOpts(title="词云"))
    make_snapshot(driver, wordcloud.render(), 'wordcloud.png', is_remove_html=True)
    wordcloud_image = plt.imread('wordcloud.png')
    st.image(wordcloud_image)
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')
import datetime
from pyecharts import options as opts
from pyecharts.charts import Bar, Page, Pie, Grid
from pyecharts.faker import Collector, Faker
from pyecharts.globals import ThemeType
from pyecharts.components import Table, Image
from pyecharts.options import ComponentTitleOpts
from pyecharts.commons.utils import JsCode
from osuapi import OsuApi, ReqConnector, OsuMode
import requests
api = OsuApi("13a36d70fd32e2f87fd2a7a89e4f52d54ab337a1", connector=ReqConnector())


def parse_date(td):
    resYear = float(td.days)/364.0  
    resMonth = int((resYear - int(resYear))*364/30)  
    resYear = int(resYear)
    resDay = int(td.days-(364*resYear+30*resMonth))
    return str(resYear) + ' years ' + str(resMonth) + ' months and ' + str(resDay) + ' days'


user_name = input('Please enter osu! user name:')

########################################  資料整理  ##########################################

beatmap_list= api.get_beatmaps(since=None, beatmapset_id=None, beatmap_id=None, username=user_name, mode=None, include_converted=True, beatmap_hash=None, limit=500)
df_beatmap = pd.DataFrame()
for beatmap in beatmap_list:
    df_beatmap_1 = pd.DataFrame( dict(beatmap), index=[0])
    df_beatmap = df_beatmap.append(df_beatmap_1, ignore_index=True)
    
df_beatmap['map_len'] = df_beatmap.last_update - df_beatmap.submit_date
df_beatmap['total_length_class'] = df_beatmap['total_length'].apply(lambda x:'< 1:39' if x<99 else('1:39 ~ 3:29' if x>=99 and x<209 else('3:39 ~ 5:00' if x>=209 and x<300 else '> 5:00')))
df_beatmap['star_rating'] = df_beatmap['difficultyrating'].apply(lambda x:'Easy'if x<2 else('Normal' if x>=2 and x<2.7 else('Hard' if x>=2.7 and x<4 else('Insane' if x>=4 and x<5.3 else('Expert' if x>=5.3 and x<6.5 else 'Expert+')))))
df_beatmap['cover_image'] = ['https://assets.ppy.sh/beatmaps/'+str(i)+'/covers/cover.jpg' for i in df_beatmap['beatmapset_id'].to_list()]
df_beatmap['thumbnail'] = ['https://b.ppy.sh/thumb/'+str(i)+'l.jpg' for i in df_beatmap['beatmapset_id'].to_list()]

# 頭像
user_id = dict(api.get_user(user_name)[0]).get('user_id')
user_profile_image = 'http://s.ppy.sh/a/'+str(user_id)

# 做圖年齡
try:
    first_map_submit_date = df_beatmap.sort_values(by='submit_date', ascending=True).iloc[0].submit_date
    last_map_update_date = df_beatmap.sort_values(by='last_update', ascending=False).iloc[0].last_update
    mapping_age = last_map_update_date-first_map_submit_date
    mapping_age_str = parse_date(mapping_age)
except:
    mapping_age_str = '未作圖'

# map set數
map_set_count = len(df_beatmap.beatmapset_id.value_counts())

# Rank 數
rank_set_count = len(df_beatmap.loc[df_beatmap.approved_date.notnull()].beatmapset_id.value_counts())

# playcount
rank_set_playcount = df_beatmap.playcount.sum()

# 收藏數
favourite_count = df_beatmap.groupby('beatmapset_id').mean().favourite_count.sum()

try:
    # 第一張圖
    first_map_title = df_beatmap.sort_values(by='submit_date', ascending=True).iloc[0].title
    first_map_image = df_beatmap.sort_values(by='submit_date', ascending=True).iloc[0].cover_image

    # 第一張圖上傳日期
    first_submit_date = df_beatmap.sort_values(by='submit_date', ascending=True).iloc[0].submit_date
    first_submit_date_str = first_submit_date.strftime('%Y-%m-%d')
except:
    first_map_title = '未上傳'
    first_submit_date_str = '未上傳'

try:
    # 第一張Rank圖
    first_rank_title = df_beatmap.loc[df_beatmap.approved_date.notnull()].groupby('beatmapset_id').first().sort_values(by='approved_date', ascending=True).iloc[0].title
    first_rank_image = df_beatmap.loc[df_beatmap.approved_date.notnull()].groupby('beatmapset_id').first().sort_values(by='approved_date', ascending=True).iloc[0].cover_image

    # 第一張Rank圖日期
    first_rank_date = df_beatmap.loc[df_beatmap.approved_date.notnull()].groupby('beatmapset_id').first().approved_date.min()
    first_rank_date_str = first_rank_date.strftime('%Y-%m-%d')
    
    # 開始作圖後多久rank
    rank_spend_time = first_rank_date - first_submit_date
    rank_spend_time_str = parse_date(rank_spend_time)
    rank_spend_time_str = '開始作圖後花了 '+rank_spend_time_str+' Rank了第一張圖'
    
except:
    first_rank_title = '未上榜'
    first_rank_date_str = '未上榜'
    rank_spend_time_str = ''
    pass

# 花最多時間mapping的圖
longest_mapping_map = df_beatmap.sort_values(by='map_len', ascending=False).iloc[0].title
longest_mapping_map_image = df_beatmap.sort_values(by='map_len', ascending=False).iloc[0].cover_image

# 花最多時間
longest_mapping_len = df_beatmap.sort_values(by='map_len', ascending=False).iloc[0].map_len

# 遊戲模式
df_mode = df_beatmap['mode'].value_counts().to_frame()
df_mode.index.name = 'Mode'
df_mode = df_mode.reset_index()
df_mode['Mode'] = df_mode['Mode'].astype('str')
df_mode['Mode'] = df_mode['Mode'].str.replace('osu!', '')

# 歌曲語言
df_Language = df_beatmap.groupby('beatmapset_id').first()['language_id'].value_counts().to_frame()
df_Language.index.name = 'Language'
df_Language = df_Language.reset_index()
df_Language['Language'] = df_Language['Language'].astype('str')
df_Language['Language'] = df_Language['Language'].str.replace('BeatmapLanguage.', '')

# 歌曲類型
df_genre = df_beatmap.groupby('beatmapset_id').first()['genre_id'].value_counts().to_frame()
df_genre.index.name = 'genre'
df_genre = df_genre.reset_index()
df_genre['genre'] = df_genre['genre'].astype('str')
df_genre['genre'] = df_genre['genre'].str.replace('BeatmapGenre.', '')

# 圖長統計
df_length = df_beatmap.groupby('beatmapset_id').first()['total_length_class'].value_counts().to_frame()
df_length.index.name = 'Length'
df_length = df_length.reset_index()
df_length['Length'] = df_length['Length'].astype('str')

# 難度統計
df_star = df_beatmap['star_rating'].value_counts().to_frame()
df_star.index.name = 'Star'
df_star = df_star.reset_index()
df_star['Star'] = df_star['Star'].astype('str')


########################################  視覺化輸出  ##########################################

C = Collector()

@C.funcs
def mapper_table():
    mapper_image = (Image().add(src=(user_profile_image),style_opts={"width": "100px", "height": "100px"}))
    return mapper_image

@C.funcs
def mapper_table():
    headers = [user_name, 'achievement']
    rows = [["Mapping Age", mapping_age_str],
            ["Map Set", map_set_count],
            ["Rank", rank_set_count],
            ["Playcount", rank_set_playcount],
            ["Favourite", int(favourite_count)]]
    mapper_table = (Table().add(headers, rows))
    
    return mapper_table

@C.funcs
def first_map_img():
    first_map_img = (Image()
                     .add(src=(first_map_image),style_opts={"width": "320px", "height": "100px", "style": "margin-left: -10px"})
                     .set_global_opts(title_opts=ComponentTitleOpts(title="First Map",
                                                                    subtitle=str(first_map_title)+'\n'+'Submit date: '+first_submit_date_str),))
    return first_map_img

@C.funcs
def first_rank_img():
    first_rank_img = (Image()
                 .add(src=(first_rank_image),style_opts={"width": "320px", "height": "100px", "style": "margin-left: 10px"})
                 .set_global_opts(title_opts=ComponentTitleOpts(title="First Rank Map",
                                                                subtitle=str(first_rank_title)+'\n'+'Approved date: '+first_rank_date_str),))
    return first_rank_img

@C.funcs
def efforts_map_img():
    efforts_map_img = (Image()
                   .add(src=(longest_mapping_map_image),style_opts={"width": "320px", "height": "100px", "style": "margin-left: 10px"})
                   .set_global_opts(title_opts=ComponentTitleOpts(title="Efforts Mapping Map",
                                                                  subtitle=str(longest_mapping_map)+'\n'+'Spend time : '+parse_date(longest_mapping_len)))
                  )
    return efforts_map_img

@C.funcs
def grid_test():
    Mode_pie = (
                Pie()
                .add("Mode",
                     df_mode.values.tolist(),
                     center=["12%", "35%"],   #圓餅圖位置
                     radius=["40%", "55%"],   #圓餅內外圈半徑
                     label_opts=opts.LabelOpts(is_show=False, position="center")  )
                .set_colors(["#fc636b", "#ffb900", "#6a67ce", "#50667f", "#1aafd0", "#3be8b0"])
                .set_global_opts(title_opts=opts.TitleOpts(title="Mode", pos_left="10%", pos_top="30%"),  
                                 legend_opts=opts.LegendOpts(orient="vertical", pos_left="0%", pos_top="10%")  )
                .set_series_opts(tooltip_opts=opts.TooltipOpts(trigger="item", formatter="{a} <br/>{b}: {c} ({d}%)")  )
               )

    Language_pie = (
                    Pie()
                    .add("Language",
                         df_Language.values.tolist(),
                         center=["32%", "35%"],
                         radius=["40%", "55%"],
                         label_opts=opts.LabelOpts(is_show=False, position="center")  )
                    .set_colors(["#fc636b", "#ffb900", "#6a67ce", "#50667f", "#1aafd0", "#3be8b0"])
                    .set_global_opts(title_opts=opts.TitleOpts(title="Language", pos_left="28.7%", pos_top="30%"),
                                     legend_opts=opts.LegendOpts(orient="vertical", pos_left="20%", pos_top="10%")  )
                    .set_series_opts(tooltip_opts=opts.TooltipOpts(trigger="item", formatter="{a} <br/>{b}: {c} ({d}%)")  )
                   )

    Genre_pie = (
                 Pie()
                 .add("Genre",
                      df_genre.values.tolist(),
                      center=["52%", "35%"], 
                      radius=["40%", "55%"], 
                      label_opts=opts.LabelOpts(is_show=False, position="center")  )
                 .set_colors(["#fc636b", "#ffb900", "#6a67ce", "#50667f", "#1aafd0", "#3be8b0"])
                 .set_global_opts(title_opts=opts.TitleOpts(title="Genre", pos_left="50%", pos_top="30%"),
                                  legend_opts=opts.LegendOpts(orient="vertical", pos_left="40%", pos_top="10%")  )
                 .set_series_opts(tooltip_opts=opts.TooltipOpts(trigger="item", formatter="{a} <br/>{b}: {c} ({d}%)")  )
                )

    Length_pie = (
                  Pie()
                  .add("Length",
                       df_length.values.tolist(),
                       center=["72%", "35%"], 
                       radius=["40%", "55%"], 
                       label_opts=opts.LabelOpts(is_show=False, position="center")  )
                  .set_colors(["#fc636b", "#ffb900", "#6a67ce", "#50667f", "#1aafd0", "#3be8b0"])
                  .set_global_opts(title_opts=opts.TitleOpts(title="Length", pos_left="69.6%", pos_top="30%"),
                                   legend_opts=opts.LegendOpts(orient="vertical", pos_left="60%", pos_top="10%")  )
                  .set_series_opts(tooltip_opts=opts.TooltipOpts(trigger="item", formatter="{a} <br/>{b}: {c} ({d}%)")  )
                 )

    Star_Rating_pie=(
                     Pie()
                     .add("Star Rating",
                          df_star.values.tolist(),
                          center=["92%", "35%"], 
                          radius=["40%", "55%"], 
                          label_opts=opts.LabelOpts(is_show=False, position="center")  )
                     .set_colors(["#fc636b", "#ffb900", "#6a67ce", "#50667f", "#1aafd0", "#3be8b0"])
                     .set_global_opts(title_opts=opts.TitleOpts(title="Star Rating", pos_left="88.4%", pos_top="30%"),
                                      legend_opts=opts.LegendOpts(orient="vertical", pos_left="80%", pos_top="10%")  )
                     .set_series_opts(tooltip_opts=opts.TooltipOpts(trigger="item", formatter="{a} <br/>{b}: {c} ({d}%)")  )
                    )
    
    return Grid(init_opts=opts.InitOpts(width="1500px", height="250px")).add(Mode_pie, grid_opts=opts.GridOpts()).add(Language_pie, grid_opts=opts.GridOpts()).add(Genre_pie, grid_opts=opts.GridOpts()).add(Length_pie, grid_opts=opts.GridOpts()).add(Star_Rating_pie, grid_opts=opts.GridOpts())

Page(layout=Page.SimplePageLayout).add(*[fn() for fn, _ in C.charts]).render(user_name+"'s Mapping Analysis.html")
print('完成')
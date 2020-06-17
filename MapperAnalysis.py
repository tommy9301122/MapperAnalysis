import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')
from osuapi import OsuApi, ReqConnector, OsuMode
import requests
api = OsuApi("13a36d70fd32e2f87fd2a7a89e4f52d54ab337a1", connector=ReqConnector())

def parse_date(td):
    resYear = float(td.days)/364.0  
    resMonth = int((resYear - int(resYear))*364/30)  
    resYear = int(resYear)
    resDay = int(td.days-(364*resYear+30*resMonth))
    return str(resYear) + "年" + str(resMonth) + "個月又" + str(resDay) + "天"



user_name = input('Please enter osu! user name:')


beatmap_list= api.get_beatmaps(since=None, beatmapset_id=None, beatmap_id=None, username=user_name, mode=None, include_converted=True, beatmap_hash=None, limit=500)
df_beatmap = pd.DataFrame()
for beatmap in beatmap_list:
    df_beatmap_1 = pd.DataFrame( dict(beatmap), index=[0])
    df_beatmap = df_beatmap.append(df_beatmap_1, ignore_index=True)
    
        
df_beatmap['map_len'] = df_beatmap.last_update - df_beatmap.submit_date
df_beatmap['total_length_class'] = df_beatmap['total_length'].apply(lambda x:'< 1:39' if x<99 else('1:39 ~ 3:29' if x>=99 and x<209 else('3:39 ~ 5:00' if x>=209 and x<300 else '> 5:00')))
df_beatmap['star_rating'] = df_beatmap['difficultyrating'].apply(lambda x:'Easy'if x<2 else('Normal' if x>=2 and x<2.7 else('Hard' if x>=2.7 and x<4 else('Insane' if x>=4 and x<5.3 else('Expert' if x>=5.3 and x<6.5 else 'Expert+')))))


print('_________________________ '+user_name+' _________________________')
print('')
# 做圖年齡
first_map_submit_date = df_beatmap.sort_values(by='submit_date', ascending=True).iloc[0].submit_date
last_map_update_date = df_beatmap.sort_values(by='last_update', ascending=False).iloc[0].last_update
mapping_age = last_map_update_date-first_map_submit_date
print('做圖年齡: '+parse_date(mapping_age))

# map set數
map_set_count = len(df_beatmap.beatmapset_id.value_counts())
print('做圖數量: '+str(map_set_count))

# Rank 數
rank_set_count = len(df_beatmap.loc[df_beatmap.approved_date.notnull()].beatmapset_id.value_counts())

# playcount
rank_set_playcount = df_beatmap.playcount.sum()
print('rank數量: '+str(rank_set_count)+' (累積遊玩數量:'+str(rank_set_playcount)+')')

# 收藏數
favourite_count = df_beatmap.groupby('beatmapset_id').mean().favourite_count.sum()
print('總收藏數量: '+str(int(favourite_count)))

print('')
print('_________________________ History _________________________')
print('')

# 第一張圖
first_map_title = df_beatmap.sort_values(by='submit_date', ascending=True).iloc[0].title

# 第一張圖上傳日期
first_submit_date = df_beatmap.sort_values(by='submit_date', ascending=True).iloc[0].submit_date
print('第一張圖: '+str(first_map_title)+'  (第一次上傳時間: '+first_submit_date.strftime('%Y-%m-%d')+')')

try:
    # 第一張Rank圖
    first_rank_title = df_beatmap.loc[df_beatmap.approved_date.notnull()].groupby('beatmapset_id').first().sort_values(by='approved_date', ascending=True).iloc[0].title

    # 第一張Rank圖日期
    first_rank_date = df_beatmap.loc[df_beatmap.approved_date.notnull()].groupby('beatmapset_id').first().approved_date.min()
    print('第一張Rank圖: '+str(first_rank_title)+'  (上榜時間: '+first_rank_date.strftime('%Y-%m-%d')+')')

    # 開始作圖後多久rank
    rank_spend_time = first_rank_date - first_submit_date
    print('開始作圖後花了 '+parse_date(rank_spend_time)+' Rank了第一張圖')
    print('')
except:
    pass

# 花最多時間mapping的圖
longest_mapping_map = df_beatmap.sort_values(by='map_len', ascending=False).iloc[0].title

# 花最多時間
longest_mapping_len = df_beatmap.sort_values(by='map_len', ascending=False).iloc[0].map_len
print('花最多時間mapping的圖: '+str(longest_mapping_map)+'  (花費時間: '+str(parse_date(longest_mapping_len))+')')

print('')
print('')
print('__________________________ Style __________________________')
print('')
# 模式統計
df_mode = df_beatmap['mode'].value_counts().to_frame()
df_mode['percent'] = (df_mode['mode']/df_mode['mode'].sum()*100).round(decimals=2)
print('  模式統計:')
print(df_mode['percent'].to_string())
print('')

# 語言統計
df_Language = df_beatmap.groupby('beatmapset_id').first()['language_id'].value_counts().to_frame()
df_Language['percent'] = (df_Language['language_id']/df_Language['language_id'].sum()*100).round(decimals=2)
print('  歌曲語言統計:')
print(df_Language['percent'].to_string())
print('')

# 語言統計
df_genre = df_beatmap.groupby('beatmapset_id').first()['genre_id'].value_counts().to_frame()
df_genre['percent'] = (df_genre['genre_id']/df_genre['genre_id'].sum()*100).round(decimals=2)
print('  歌曲類型統計:')
print(df_genre['percent'].to_string())
print('')

# 圖長統計
df_length_class = df_beatmap.groupby('beatmapset_id').first()['total_length_class'].value_counts().to_frame()
df_length_class['percent'] = ((df_length_class['total_length_class']/df_length_class['total_length_class'].sum())*100).round(decimals=2)
print('  圖長統計:')
print(df_length_class['percent'].to_string())
print('')

# 難度統計
df_star = df_beatmap['star_rating'].value_counts().to_frame()
df_star['percent'] = (df_star['star_rating']/df_star['star_rating'].sum()*100).round(decimals=2)
print('  難度統計:')
print(df_star['percent'].to_string())
print('')

# bpm
mean_bpm = round(df_beatmap.groupby('beatmapset_id').first().bpm.mean(),1)
min_bpm = round(df_beatmap.groupby('beatmapset_id').first().bpm.min())
max_bpm = round(df_beatmap.groupby('beatmapset_id').first().bpm.max())
print('做圖平均BPM: '+str(mean_bpm)+'  ('+str(min_bpm)+'-'+str(max_bpm)+')')


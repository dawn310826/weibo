import re
import requests
import time
import random
import json
from datetime import datetime, timedelta, date
from json.decoder import JSONDecodeError
import pickle
import os
os.chdir('E:\python\code')

hot_url = 'https://m.weibo.cn/api/container/getIndex?containerid=102803&since_id={}'
hot_comment_url = 'https://m.weibo.cn/single/rcList?format=cards&id={}&type=comment&hot=1&page={}'
#latest_comment_url = 'https://m.weibo.cn/single/rcList?format=cards&id={}&type=comment&hot=0&page={}'
hot_comment_show_url = 'https://m.weibo.cn/api/comments/show?id={}&page={}'

sleep_time = 3
retry_count = 10

with open('ips.pkl','rb') as f:
    ips = pickle.load(f)
with open('cookies.pkl','rb') as f:
    cookies = pickle.load(f)   
with open('UAs.pkl','rb') as f:
    UAs = pickle.load(f)
    
headers = {
            'Host':'m.weibo.cn',
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding':'gzip, deflate, br',
            'Accept-Language':'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Connection':'keep-alive',
            'Upgrade-Insecure-Requests':'1',
            #'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
            #'Cookie':'_T_WM=2f313eb8f6bde3b4a98a743e1086eb02; SUB=_2A253OckaDeRhGeRN6VcR9SjLyD2IHXVUxddSrDV6PUJbkdAKLVankW1NU7xDu5eyYNgOe6dWmK3j3sBTLpxJ-s2M; SUHB=0laEIe-W4Br19X; SCF=AnUZHEIiMgcjPVj1aly5ZULK9i0jh7Oiv-y7gGb-jca9FyrXjszArT4HBycpgEcPL-rLxgzHpQc9CNb_kDnW8Js.; SSOLoginState=1513994570; H5_INDEX_TITLE=%E4%B8%A2%E4%B8%A2%E5%A4%A9%E5%A4%A9%E4%B8%A2%E4%B8%9C%E8%A5%BF; H5_INDEX=2; WEIBOCN_FROM=1110006030; M_WEIBOCN_PARAMS=featurecode%3D20000320%26luicode%3D20000174%26lfid%3Dhotword%26fid%3D102803%26uicode%3D10000011'
}

        
def get_header():
    headers['Cookie'] = random.choice(cookies)
    headers['User-Agent'] = random.choice(UAs)
    return headers

def get_request(url):
    response = requests.get(url,headers=get_header(),proxies={'proxy':random.choice(ips)})
    try:
        if response.status_code == 200:
            return response.json()
        else:return []
    except requests.ConnectionError:
        print('ConnectionError')
        return []
    except JSONDecodeError:
        print('JSONDecodeError')
        return []
    
def time_parser(time, now):
    #print('before parsed:', time)
    if time[-3:] == '分钟前':
        interval = int(time[:-3])
        time = now - timedelta(minutes=interval)
        time = datetime.strftime(now, "%Y-%m-%d %H:%M:%S")
    elif time[-3:] == '小时前':
        interval = int(time[:-3])
        time = now - timedelta(hours=interval)
        time = datetime.strftime(now, "%Y-%m-%d %H:%M:%S")
    elif len(time) <= 5:
        time = '2018-'+ time
    #print('after parsed', time)
    return time   

def comment_time_parser(time, now):
    #print('before parsed:', time)
    if time[-3:] == '分钟前':
        interval = int(time[:-3])
        time = now - timedelta(minutes=interval)
        time = datetime.strftime(now, "%Y-%m-%d %H:%M:%S")
    elif time[:2] == '今天':
        today = date.today()
        today = datetime.strftime(today, '%Y-%m-%d')
        time = today + time[2:]
    elif time[:2] == '昨天':
        yesterday = date.today() - timedelta(days=1)
        yesterday = datetime.strftime(yesterday, '%Y-%m-%d')
        time = yesterday + time[2:]
    elif len(time.split()[0]) <= 5:
        time = '2018-' + time
    #print('after parsed', time)
    return time

def text_parser(text):
    pattern1 = re.compile(r'<a.*?</a>')
    pattern2 = re.compile(r'<.*?></.*?>')
    
    tmp = re.sub(pattern1,'',text)
    text = re.sub(pattern2,'',tmp)
    return text
    
def get_blog_data(url):
    blog_items_one_page = {}
    
    data = get_request(url)
    now = datetime.now()
    
    if not data:return {}
    data = data['data']['cards']
    count = 0
    #for item in data:
    for item in data[:len(data)]:
        item1 = {}
        item1['user_id'] = item['mblog']['user']['id']
        item1['user_name'] = item['mblog']['user']['screen_name']
        item1['user_profile'] = item['mblog']['user']['profile_url']
        item1['user_is_verified'] = item['mblog']['user']['verified']
        item1['user_verified_type'] = item['mblog']['user']['verified_type']
        item1['user_follow_count'] = item['mblog']['user']['follow_count']
        item1['user_fans_count'] = item['mblog']['user']['followers_count']
        item1['user_description'] = item['mblog']['user']['description']
    
        item1['blog_id'] = item['mblog']['id']
        item1['blog_like_counts'] = item['mblog']['attitudes_count']
        item1['blog_comment_counts'] = item['mblog']['comments_count']
        item1['blog_repost_counts'] = item['mblog']['reposts_count']
        item1['blog_text'] = text_parser(item['mblog']['text'])
        item1['blog_time'] = comment_time_parser(item['mblog']['created_at'], now)
        
        time.sleep(sleep_time) 
        url = hot_comment_show_url.format(item1['blog_id'], 1)
        com_json = get_request(url)
        
        retry = 0
        while ('data' not in com_json) and (retry < retry_count):
            retry += 1
            time.sleep(sleep_time*random.randint(2,5))
            com_json = get_request(url)
            print(url)
            print('retry get_blog_data  '+str(retry)+'.....')
        if retry >= retry_count:
            print('get blog failed!')
            return blog_items_one_page
        
        com_data = com_json['data']
        if com_data.get('hot_total_number'):
            item1['blog_hot_counts'] = com_data.get('hot_total_number')
        else:
            print('Got a blog without hot comments')
            continue
        
        blog_items_one_page[item1['blog_id']] = item1
        count += 1
        print('Got %s blogs!' % count)
        #time.sleep(sleep_time)
    return blog_items_one_page
    

def get_comment_data(url):    
    now = datetime.now()
    time.sleep(sleep_time)
    res = get_request(url)
    
    retry = 0
    while (len(res)<1) and (retry < retry_count):
        retry += 1
        time.sleep(sleep_time*random.randint(2,5))
        res = get_request(url)
        print(url)
        print('retry get_comment_data '+str(retry)+'.....')
    if retry >= retry_count:
        print('get comments failed')
        return None
    
    data = res[-1]['card_group']
    
    comment_items = []
    for item in data:
        item1 = {}
        item1['comment_time'] = comment_time_parser(item['created_at'], now)
        item1['like_counts'] = item['like_counts']
        item1['source'] = item['source']
        item1['text'] = text_parser(item['text'])
        item1['id'] = item['id']
        item1['commenter_id'] = item['user']['id']
        item1['commenter_verified'] = item['user']['verified']
        item1['commenter_verified_type'] = item['user']['verified_type']
        comment_items.append(item1)
    return comment_items

def get_data():
    for i in range(1):
        hot_url_i = hot_url.format(i)
        print(hot_url_i)
        
        blog_items_one_page = get_blog_data(hot_url_i)
        
        count = 0
        for blog_id in blog_items_one_page:
            item = blog_items_one_page[blog_id]
            hot_comment_counts = item['blog_hot_counts']
            pages = hot_comment_counts//100 + 1
            print('hot_comment_counts:'+str(hot_comment_counts)+'  and pages:'+str(pages))
            for j in range(1,pages+1):
                hot_comment_url_j = hot_comment_url.format(blog_id, j)
                
                comment_items = get_comment_data(hot_comment_url_j)

                if not comment_items:
                    return 
                if 'comment_items' not in item:
                    item['comment_items'] = comment_items
                else:
                    item['comment_items'].extend(comment_items)
                
                time.sleep(sleep_time)
                print('Got %s pages of comments' % (j))
            
            #blog_items_one_page[blog_id]=item
            blog_items[blog_id]=item
            count += 1
            print('Got comments of %s blogs' % count)
        
                
blog_items = {}
data = get_data()

with open("E:\python\code\weibo\comment.json",'w') as f:
    json.dump(blog_items,f)
    
    
    

from fastapi import FastAPI
from twikit import Client
import asyncio
from email.utils import parsedate_to_datetime

app = FastAPI()

AUTH_TOKEN = '745f8eee0c0480a72aba7b170181547f11c43b20'
CT0 = '815fe524a770188366245e55a7ae0aa1fd2a96d886058eaae8662f4c7612e67500bec9561933f6a68840ab2d9c1cf6384c17b63a912a7fdd76fe0546e3ebaf4a2945d90ad74b3897f02d2a1c65887de8'

client = Client('en-US')
client.set_cookies({'auth_token': AUTH_TOKEN, 'ct0': CT0})

@app.get("/")
def home():
    return {"status": "running", "message": "Twitter Twikit API is active"}

@app.get("/tweets/{username}")
async def get_tweets(username: str):
    username = username.strip().lstrip('@')
    try:
        user = await client.get_user_by_screen_name(username)
        tweets = await user.get_tweets('Tweets', count=20)
        
        result = []
        for t in tweets:
            media_list = []
            if hasattr(t, 'media') and t.media:
                for m in t.media:
                    m_type = 'video' if m.get('type') in ['video', 'animated_gif'] else 'image'
                    m_url = m.get('media_url_https', '')
                    if m_type == 'video' and 'video_info' in m:
                        variants = m['video_info'].get('variants', [])
                        mp4s = [v for v in variants if v.get('content_type') == 'video/mp4']
                        if mp4s:
                            best = max(mp4s, key=lambda x: x.get('bitrate', 0))
                            m_url = best.get('url', m_url)
                    media_list.append({'url': m_url, 'type': m_type})

            dt = parsedate_to_datetime(t.created_at)
            ts = int(dt.timestamp())

            result.append({
                'id': str(t.id),
                'text': t.text,
                'created_at': t.created_at,
                'timestamp': ts,
                'author': user.name,
                'handle': user.screen_name,
                'avatar': user.profile_image_url,
                'is_verified': 1 if getattr(user, 'is_blue_verified', False) or getattr(user, 'verified', False) else 0,
                'likes': t.favorite_count or 0,
                'replies': t.reply_count or 0,
                'reposts': t.retweet_count or 0,
                'media': media_list
            })
            
        return {"status": "success", "tweets": result}
    except Exception as e:
        return {"status": "error", "message": str(e), "tweets": []}


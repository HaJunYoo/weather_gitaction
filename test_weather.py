from datetime import datetime
from datetime import timedelta
import requests
import logging
# import psycopg2
import json

from pymongo import MongoClient  # mongoDB 접속을 비롯한 액션을 할 때 사용하는 lib
import requests  # python file에서 웹 접속이 필요할 때 사용하는 lib
# import pandas as pd  # dataframe 단위 작업을 할 때 사용하는 lib

###
with open('secrets.json', 'r') as f:
    secrets = json.load(f)

params = {
    "url": "https://api.openweathermap.org/data/2.5/onecall",
    "lat": 37.5665,
    "lon": 126.9780,
    "user": "hajun",
    "password": secrets['password'],
    "apikey": secrets['apikey']
}
url = params["url"]

User = params["user"]
Password = params["password"]
api_key = params["apikey"]
mongo_path = f"mongodb+srv://{User}:{Password}@nestcluster.6afp4lo.mongodb.net/?retryWrites=true&w=majority"

# 서울의 위도 경도
lat = params["lat"]
lon = params["lon"]

# https://openweathermap.org/api/one-call-api
url = f"{url}?lat={lat}&lon={lon}&exclude=current,minutely,hourly,alerts&appid={api_key}&units=metric"
response = requests.get(url)
data = json.loads(response.text)

# client and db 선언
client = MongoClient(mongo_path)
# Cluster0 -> weather collection
db = client.Cluster0

insert_list = []
# incremental update

# 습도 : d['humidity']
# 날씨 상태 : d['weather'][0]['main'] => 라벨이 될 예정
# 풍속 : d['wind_speed']
for d in data["daily"]:
    temp_dict = dict()
    date = datetime.fromtimestamp(d["dt"]).strftime('%Y-%m-%d')
    temp = d["temp"]["day"]
    min_temp = d["temp"]["min"]
    max_temp = d["temp"]["max"]
    humidity = d["humidity"]
    weather_state = d['weather'][0]['main']
    wind_speed = d['wind_speed']

    # Check if document with same date already exists
    existing_doc = db.weather.find_one({"date": date})
    if existing_doc:
        print(f"Document with date {date} already exists. Skipping...")
        continue
    else:
        # 그 날의 날씨를 추가
        temp_dict["date"] = date
        temp_dict["temp"] = temp
        temp_dict["min_temp"] = min_temp
        temp_dict["max_temp"] = max_temp
        temp_dict["humidity"] = humidity
        temp_dict["weather_state"] = weather_state
        temp_dict["wind_speed"] = wind_speed

        insert_list.append(temp_dict)
        print(f"date {date} not exists, can insert")


for elem in insert_list:
    print(elem)

if not insert_list:
    print("No new data to insert. Exiting...")
    exit(0)

try:
    with client.start_session() as s:
        def cb(s):
            db.weather.insert_many(insert_list, session=s)
        s.with_transaction(cb)
    print('Insert Success')

except Exception as e:
    raise

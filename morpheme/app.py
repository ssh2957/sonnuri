from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
import os
import requests
import xml.etree.ElementTree as ET
import numpy as np
import pymongo
import pandas as pd
import torch
from sklearn.metrics.pairwise import cosine_similarity
from kobert_transformers import get_kobert_model, get_tokenizer

# # MongoDB 설정 (환경 변수 대신 직접 설정)
# MONGO_URI = "mongodb://localhost:27017/"
# MONGO_DB_NAME = "sonuri"
# MONGO_COLLECTION_NAME = "sign_word"

# # MongoDB 연결
# client = pymongo.MongoClient(MONGO_URI)
# db = client[MONGO_DB_NAME]
# collection = db[MONGO_COLLECTION_NAME]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# .env 파일 로드
load_dotenv()

# 환경 변수에서 MongoDB 사용자 이름과 비밀번호 불러오기
mongo_username = os.getenv("MONGO_USERNAME")
mongo_password = os.getenv("MONGO_PASSWORD")

# MongoDB 클라이언트 설정 (예: 로컬호스트)
mongo = pymongo.MongoClient(f"mongodb://{mongo_username}:{mongo_password}@k11a301.p.ssafy.io:8017/?authSource=admin")
# mongo = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongo["sonnuri"]
collection = db["sign_word"]

# MongoDB에서 데이터 불러오기
documents = collection.find()

# DataFrame 생성
word_data = pd.DataFrame(list(documents))

# "단어"와 "설명" 열을 문자열로 변환한 후 결합하여 컨텍스트 문자열 생성
word_data['context'] = word_data['Word'].astype(str) + ": " + word_data['Description'].astype(str)

# OPENAI 연결 설정
openai = OpenAI(
    organization="org-CdqlMsWjfTiylVQPL4TCGTy0",
    api_key=os.getenv("OPENAI_API_KEY")
)

# KoBERT 모델 및 토크나이저 로드
tokenizer = get_tokenizer()
model = get_kobert_model()

# 임베딩 파일 경로
embeddings_file = "kobert_embeddings.npy"

class MatchedWord(BaseModel):
    matched_word: str
    matched_url: str
    matched_description: str
    definition: str

class TextInput(BaseModel):
    sentence: str
    word: str

# 임베딩 생성 함수
def generate_embeddings(text_list):
    embeddings = []
    for text in text_list:
        inputs = tokenizer(text, return_tensors='pt', truncation=True, padding=True, max_length=128)
        with torch.no_grad():
            outputs = model(**inputs)
            # [CLS] 토큰의 임베딩 벡터를 사용
            cls_embedding = outputs.last_hidden_state[:, 0, :].numpy()
            embeddings.append(cls_embedding[0])
    return np.array(embeddings)

# 임베딩이 이미 저장된 경우 불러오기, 그렇지 않으면 생성 후 저장
if os.path.exists(embeddings_file):
    embeddings = np.load(embeddings_file)
    print("임베딩이 성공적으로 불러와졌습니다!")
else:
    embeddings = generate_embeddings(word_data['context'].tolist())
    np.save(embeddings_file, embeddings)
    print("임베딩이 성공적으로 생성되고 저장되었습니다!")

# 국립국어원 API를 사용해 단어의 정의를 가져오는 함수
def get_word_definition(query):
    # API URL 및 파라미터 설정
    api_url = "https://stdict.korean.go.kr/api/search.do"
    api_params = {
        "certkey_no": "7031",  # 인증 키 번호 (필요에 맞게 변경)
        "key": "F7A788A8401DF7ED7008D6FD41CD980C",  # API 키 (필요에 맞게 변경)
        "type_search": "search",
        "req_type": "xml",
        "q": query  # 검색할 단어
    }
    
    # API 요청 보내기
    response = requests.get(api_url, params=api_params)
    
    # 응답 상태 코드 확인
    if response.status_code != 200:
        print("API 요청 실패")
        return "정의 없음"
    
    # XML 응답 파싱
    try:
        root = ET.fromstring(response.content)
        # 첫 번째 단어 정의 가져오기
        definition = root.find(".//definition").text
        return definition if definition else "정의 없음"
    except Exception as e:
        print("XML 파싱 오류:", e)
        return "정의 없음"

# 유사한 단어와 URL을 찾는 함수
# def get_similar_word_url(query):
#     # 단어의 정의 가져오기
#     definition = get_word_definition(query)
#     if definition == "정의 없음":
#         print("단어의 정의를 찾을 수 없습니다.")
#         return None, None, None

#     # 정의를 임베딩 벡터로 변환
#     inputs = tokenizer(definition, return_tensors='pt', truncation=True, padding=True, max_length=128)
#     with torch.no_grad():
#         outputs = model(**inputs)
#         query_embedding = outputs.last_hidden_state[:, 0, :].numpy()

#     # 코사인 유사도 계산
#     similarities = cosine_similarity(query_embedding, embeddings)
    
#     # 가장 유사한 단어의 인덱스를 찾기
#     most_similar_index = similarities.argmax()
    
#     # 유사한 단어, URL, 설명 반환
#     matched_word = word_data.iloc[most_similar_index]['Word']
#     matched_url = word_data.iloc[most_similar_index]['URL']
#     matched_description = word_data.iloc[most_similar_index]['Description']
    
#     return matched_word, matched_url, matched_description, definition

# 사용자로부터 단어 입력 받기
# word = input("단어를 입력하세요: ")
# matched_word, matched_url, matched_description = get_similar_word_url(word)

# if matched_word and matched_url and matched_description:
#     print(f"유사한 단어: {matched_word}\nURL: {matched_url}\n설명: {matched_description}")
# else:
#     print("관련된 정보를 찾을 수 없습니다.")
    
@app.post("/morpheme")
async def morpheme(input_data: TextInput):
    try:
        matched_word, matched_url, matched_description, definition = get_similar_word_url(input_data)
        return {"result": MatchedWord(matched_word=matched_word, matched_url=matched_url, matched_description=matched_description, definition=definition)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing string: {str(e)}")
    
def get_similar_word_url(input_data: TextInput):
    
    # GPT로 문맥을 고려한 뜻 가져오기
    definition = get_word_description_in_sentence(input_data.sentence, input_data.word)
    
    # 정의를 임베딩 벡터로 변환
    inputs = tokenizer(definition, return_tensors='pt', truncation=True, padding=True, max_length=128)
    with torch.no_grad():
        outputs = model(**inputs)
        query_embedding = outputs.last_hidden_state[:, 0, :].numpy()

    # 코사인 유사도 계산
    similarities = cosine_similarity(query_embedding, embeddings)
    
    # 가장 유사한 단어의 인덱스를 찾기
    most_similar_index = similarities.argmax()
    
    # 유사한 단어, URL, 설명 반환
    matched_word = str(word_data.iloc[most_similar_index]['Word'])
    matched_url = str(word_data.iloc[most_similar_index]['URL'])
    matched_description = str(word_data.iloc[most_similar_index]['Description'])
    
    return matched_word, matched_url, matched_description, definition

def get_word_description_in_sentence(sentence: str, word: str):
    response = openai.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "system", "content": "너는 문맥을 파악해서 단어의 뜻을 알려주는 기계야."
               "문장에서 단어의 뜻을 알려줘."
               "응답은 단어의 뜻을 그대로 돌려주면 돼."},
              {"role": "user", "content": f"문장: {sentence}, 단어: {word}"}]
    )
    return response.choices[0].message.content

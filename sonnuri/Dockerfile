FROM python:3.9.5

# 작업 디렉토리 설정
WORKDIR /app

# requirements.txt와 main.py 복사
COPY requirements.txt .
COPY main.py .

RUN pip install -r requirements.txt

# FastAPI 애플리케이션 실행
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
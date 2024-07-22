# 베이스 이미지 설정
FROM tiangolo/uvicorn-gunicorn-starlette:python3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 종속성 파일 복사 및 설치
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 파일 복사
COPY . /app

# 환경 변수 설정 (선택 사항)
# ENV ENVIRONMENT=production
EXPOSE 8000
# 컨테이너 실행 시 명령어 설정
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


# FROM tiangolo/uvicorn-gunicorn-starlette:python3.11-slim

# RUN     

# WORKDIR /app

# COPY ./requirements.txt /app/requirements.txt
 
# RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt
 
# COPY ./app /app

# EXPOSE 8000

# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
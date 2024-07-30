# FastAPI 백엔드 프로젝트 (Alembic, SQLAlchemy, MySQL, Redis)

이 프로젝트는 FastAPI, SQLAlchemy, Alembic, MySQL, Redis를 사용하여 백엔드를 설정하는 방법을 설명합니다. 아래는 이 프로젝트를 설정하고 실행하는 방법에 대한 가이드입니다.

## 목차

1. [필수 조건](#필수-조건)
2. [설치](#설치)
3. [구성](#구성)
4. [데이터베이스 마이그레이션](#데이터베이스-마이그레이션)
5. [애플리케이션 실행](#애플리케이션-실행)

## 필수 조건

- Python 3.11
- MySQL 5.7+
- Redis
- Docker (선택 사항, 컨테이너 사용 시)

## 설치

1. **레포지토리 클론:**
   ```sh
   git clone https://github.com/yourusername/yourproject.git
   cd yourproject
2. **가상 환경 생성 및 활성화:**
python3 -m venv venv
source venv/bin/activate  # 윈도우의 경우 `venv\Scripts\activate`
3.**필요한 패키지 설치:**
pip install -r requirements.txt

## 구성
1. 환경 파일생성 및 변수 설정
   touch .env
   - .env 파일 안에 DB 및 Redis 구성 설정
   DATABASE_URL=mysql+pymysql://username:password@localhost/dbname
   REDIS_URL=redis://localhost:6379/0
3. MySQL 및 Redis 실행
   - MySQL 서버를 시작하고 프로젝트용 데이터베이스를 만듭니다.
   - Redis 서버를 시작합니다.

## 데이터베이스 마이그레이션
1. Alembic 초기화 (초기화되 않은 경우):
  alembic init alembic
2. 'alembic.ini' 파일에 데이터베이스 URL 설정:
  sqlalchemy.url = mysql+pymysql://username:password속
   


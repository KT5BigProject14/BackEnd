# FastAPI 백엔드 프로젝트 (Alembic, SQLAlchemy, MySQL, Redis)

이 프로젝트는 FastAPI, SQLAlchemy, Alembic, MySQL, Redis를 사용하여 백엔드를 설정하는 방법을 설명합니다. 아래는 이 프로젝트를 설정하고 실행하는 방법에 대한 가이드입니다.

## 목차

1. [필수 조건](#필수-조건)
2. [설치](#설치)
3. [구성](#구성)
4. [데이터베이스 마이그레이션](#데이터베이스-마이그레이션)
5. [애플리케이션 실행](#애플리케이션-실행)
6. [프로젝트 구조](#프로젝트-구조)
7. [사용법](#사용법)
8. [엔드포인트](#엔드포인트)
9. [기여](#기여)
10. [라이선스](#라이선스)

## 필수 조건

- Python 3.8+
- MySQL 5.7+
- Redis
- Docker (선택 사항, 컨테이너 사용 시)

## 설치

1. **레포지토리 클론:**
   ```sh
   git clone https://github.com/yourusername/yourproject.git
   cd yourproject

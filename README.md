
# 🗺️ 중간지점 찾기 웹앱

여러 사람의 출발지를 입력하면 중간지점을 찾아주고, 가장 가까운 지하철역을 안내해주는 웹 애플리케이션입니다.

## 주요 기능

1. **다중 출발지 입력**: 2~10개의 출발지를 입력할 수 있습니다 (주소 또는 역 이름)
2. **중간지점 계산**: 모든 출발지의 중심점을 자동으로 계산합니다
3. **경로 안내**: 각 출발지에서 중간지점까지의 거리와 예상 시간을 표시합니다
4. **지하철역 추천**: 중간지점에서 가까운 지하철역 5곳을 거리순으로 안내합니다
5. **지도 앱 연동**: 네이버 지도(길찾기)와 카카오맵(위치) 링크를 제공합니다
6. **시각화**: 인터랙티브 지도에 출발지, 경로선, 중간지점, 지하철역을 표시합니다

## 설치 방법

1. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

2. `.env` 파일 생성 및 카카오 API 키 입력:
```
KAKAO_API_KEY=your_kakao_api_key_here
```

## 카카오 API 키 발급 방법

1. [카카오 개발자 센터](https://developers.kakao.com/) 접속
2. 로그인 후 "내 애플리케이션" 메뉴 선택
3. "애플리케이션 추가하기" 클릭
4. 앱 이름 입력 후 생성
5. "앱 키" 탭에서 "REST API 키" 복사
6. `.env` 파일에 붙여넣기

## 실행 방법

```bash
streamlit run ex2-1.py
```

## 사용 방법

1. 왼쪽 사이드바에서 출발지 개수를 선택
2. 각 출발지의 주소를 입력 (예: 서울 강남구 역삼동)
3. "중간지점 찾기" 버튼 클릭
4. 지도에서 결과 확인

## 기술 스택

- **Frontend**: Streamlit
- **지도 API**: Kakao Maps API
- **지도 시각화**: Folium
- **데이터 처리**: Pandas

## 특징

- 깔끔하고 직관적인 UI
- 실시간 지도 시각화 (경로선 포함)
- 거리 및 예상 소요시간 계산
- 네이버 지도 & 카카오맵 연동
- 반응형 디자인
- 사용자 친화적인 인터페이스
- 로컬 & Streamlit Cloud 배포 지원

## Streamlit Cloud 배포

### 1. GitHub에 코드 푸시
```bash
git init
git add .
git commit -m "Initial commit"
git push origin main
```

### 2. Streamlit Cloud 설정
1. [Streamlit Cloud](https://streamlit.io/cloud) 접속
2. "New app" 클릭
3. GitHub 저장소 선택
4. **Settings → Secrets** 에서 API 키 설정:
```toml
KAKAO_API_KEY = "your_api_key_here"
```
5. Deploy 클릭

### 3. 환경 변수 설정
- **로컬**: `.env` 파일 사용
- **클라우드**: Streamlit Secrets 사용 (앱에서 자동 처리)

## 문제 해결

### 카카오 API 403 오류
카카오 개발자 콘솔에서 Local API(지도 API) 서비스를 활성화해야 합니다.

### Streamlit Cloud 배포 시 API 키 오류
앱 설정의 Secrets 탭에서 `KAKAO_API_KEY`를 설정했는지 확인하세요.

## 라이선스

MIT License


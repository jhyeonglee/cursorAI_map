import os
from dotenv import load_dotenv
import requests

# 환경 변수 로드
load_dotenv()
KAKAO_API_KEY = os.getenv('KAKAO_API_KEY')

print("=" * 50)
print("카카오 API 테스트")
print("=" * 50)
print(f"\n✓ API 키 로드 여부: {'성공' if KAKAO_API_KEY else '실패'}")
if KAKAO_API_KEY:
    print(f"✓ API 키 길이: {len(KAKAO_API_KEY)} 자")
    print(f"✓ API 키 앞 10자: {KAKAO_API_KEY[:10]}...")
else:
    print("✗ .env 파일에 KAKAO_API_KEY가 없거나 값이 비어있습니다.")
    print("\n.env 파일 형식:")
    print("KAKAO_API_KEY=your_rest_api_key_here")
    exit(1)

print("\n" + "=" * 50)
print("강남역 검색 테스트")
print("=" * 50)

# 강남역 검색 테스트
url = "https://dapi.kakao.com/v2/local/search/keyword.json"
headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
params = {"query": "강남역"}

try:
    print(f"\n요청 URL: {url}")
    print(f"요청 헤더: Authorization: KakaoAK {KAKAO_API_KEY[:10]}...")
    
    response = requests.get(url, headers=headers, params=params, timeout=5)
    print(f"\n✓ 응답 상태 코드: {response.status_code}")
    
    if response.status_code != 200:
        print(f"응답 내용: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        if result['documents']:
            print(f"✓ 검색 결과 개수: {len(result['documents'])}개")
            print(f"\n첫 번째 결과:")
            doc = result['documents'][0]
            print(f"  - 장소명: {doc['place_name']}")
            print(f"  - 주소: {doc['address_name']}")
            print(f"  - 좌표: ({doc['y']}, {doc['x']})")
            print("\n🎉 API 키가 정상적으로 작동합니다!")
        else:
            print("✗ 검색 결과가 없습니다.")
    elif response.status_code == 401:
        print("✗ 인증 실패 (401)")
        print("\n가능한 원인:")
        print("1. API 키가 잘못되었습니다.")
        print("2. .env 파일의 API 키에 공백이나 따옴표가 포함되어 있습니다.")
        print("\n.env 파일 올바른 형식:")
        print("KAKAO_API_KEY=1234567890abcdef1234567890abcdef")
        print("\n.env 파일 잘못된 형식 예시:")
        print("KAKAO_API_KEY='1234567890abcdef1234567890abcdef'  ← 따옴표 제거!")
        print("KAKAO_API_KEY = 1234567890abcdef1234567890abcdef  ← 공백 제거!")
    elif response.status_code == 403:
        print("✗ 접근 권한 없음 (403)")
        print("\n카카오 개발자 콘솔에서 확인:")
        print("1. 플랫폼 설정이 되어 있는지 확인")
        print("2. 사이트 도메인이 등록되어 있는지 확인")
    else:
        print(f"✗ 예상치 못한 오류: {response.status_code}")
        print(f"응답: {response.text}")
        
except requests.exceptions.Timeout:
    print("✗ 요청 시간 초과")
except requests.exceptions.ConnectionError:
    print("✗ 네트워크 연결 오류")
except Exception as e:
    print(f"✗ 오류 발생: {e}")

print("\n" + "=" * 50)


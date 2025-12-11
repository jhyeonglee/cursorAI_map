<<<<<<< HEAD
import streamlit as st
import requests
import os
from dotenv import load_dotenv
import folium
from streamlit_folium import folium_static
import pandas as pd
import math

# 환경 변수 로드 (로컬 & 클라우드 호환)
load_dotenv()

# Streamlit Cloud에서는 secrets 사용, 로컬에서는 .env 사용
try:
    KAKAO_API_KEY = st.secrets.get("KAKAO_API_KEY", os.getenv('KAKAO_API_KEY'))
except:
    KAKAO_API_KEY = os.getenv('KAKAO_API_KEY')

# API 키 체크
if not KAKAO_API_KEY:
    st.error("⚠️ KAKAO_API_KEY를 설정해주세요.")
    st.info("""
    **로컬 환경**: .env 파일에 KAKAO_API_KEY를 추가하세요.
    
    **Streamlit Cloud**: 앱 설정 → Secrets에서 설정하세요.
    ```
    KAKAO_API_KEY = "your_api_key_here"
    ```
    """)
    st.stop()

def geocode_address(address):
    """주소 또는 장소명을 좌표로 변환"""
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    
    # 1. 먼저 주소 검색 시도
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    params = {"query": address}
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        result = response.json()
        if result['documents']:
            return {
                'lat': float(result['documents'][0]['y']),
                'lng': float(result['documents'][0]['x']),
                'address': result['documents'][0]['address_name']
            }
    
    # 2. 주소 검색 실패 시 키워드 검색 (역 이름, 랜드마크 등)
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    params = {"query": address}
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        result = response.json()
        if result['documents']:
            doc = result['documents'][0]
            return {
                'lat': float(doc['y']),
                'lng': float(doc['x']),
                'address': doc.get('address_name', doc.get('place_name', address))
            }
    
    return None

def calculate_distance(lat1, lng1, lat2, lng2):
    """두 좌표 간의 거리 계산 (km) - Haversine 공식"""
    R = 6371  # 지구 반지름 (km)
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    distance = R * c
    return distance

def calculate_travel_time(distance_km):
    """거리 기반 예상 소요 시간 계산 (분)"""
    # 대중교통 평균 속도 약 30km/h로 가정
    speed_kmh = 30
    time_hours = distance_km / speed_kmh
    time_minutes = time_hours * 60
    return int(time_minutes)

def coord_to_address(lat, lng):
    """좌표를 주소로 변환 (역지오코딩)"""
    url = "https://dapi.kakao.com/v2/local/geo/coord2address.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {
        "x": lng,
        "y": lat
    }
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        result = response.json()
        if result['documents']:
            doc = result['documents'][0]
            # 도로명 주소 우선, 없으면 지번 주소
            if doc.get('road_address'):
                return {
                    'road_address': doc['road_address']['address_name'],
                    'jibun_address': doc['address']['address_name'] if doc.get('address') else ''
                }
            elif doc.get('address'):
                return {
                    'road_address': '',
                    'jibun_address': doc['address']['address_name']
                }
    return {
        'road_address': '',
        'jibun_address': ''
    }

def find_midpoint(locations):
    """여러 좌표의 중간지점 계산"""
    if not locations:
        return None
    
    avg_lat = sum(loc['lat'] for loc in locations) / len(locations)
    avg_lng = sum(loc['lng'] for loc in locations) / len(locations)
    
    # 좌표를 주소로 변환
    address_info = coord_to_address(avg_lat, avg_lng)
    
    return {
        'lat': avg_lat, 
        'lng': avg_lng,
        'road_address': address_info['road_address'],
        'jibun_address': address_info['jibun_address']
    }

def find_nearby_subway(lat, lng, radius=1000):
    """주변 지하철역 검색"""
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {
        "query": "지하철역",
        "x": lng,
        "y": lat,
        "radius": radius,
        "sort": "distance"
    }
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        result = response.json()
        if result['documents']:
            stations = []
            for doc in result['documents'][:5]:  # 상위 5개만
                stations.append({
                    'name': doc['place_name'],
                    'address': doc['address_name'],
                    'distance': int(doc['distance']),
                    'lat': float(doc['y']),
                    'lng': float(doc['x'])
                })
            return stations
    return []

def create_map(locations, midpoint, subway_stations):
    """지도 생성 (경로선 포함)"""
    m = folium.Map(
        location=[midpoint['lat'], midpoint['lng']], 
        zoom_start=12,
        tiles='OpenStreetMap'
    )
    
    # 출발지에서 중간지점까지 경로선 그리기
    for i, loc in enumerate(locations):
        # 경로선 (점선)
        folium.PolyLine(
            locations=[
                [loc['lat'], loc['lng']],
                [midpoint['lat'], midpoint['lng']]
            ],
            color='blue',
            weight=2,
            opacity=0.6,
            dash_array='5, 10',
            tooltip=f"출발지 {i+1} → 중간지점"
        ).add_to(m)
    
    # 출발지 마커 (파란색)
    for i, loc in enumerate(locations):
        distance = calculate_distance(loc['lat'], loc['lng'], midpoint['lat'], midpoint['lng'])
        time = calculate_travel_time(distance)
        
        folium.Marker(
            [loc['lat'], loc['lng']],
            popup=f"<b>출발지 {i+1}</b><br>{loc.get('address', '')}<br>거리: {distance:.2f}km<br>예상시간: 약 {time}분",
            tooltip=f"출발지 {i+1}",
            icon=folium.Icon(color='blue', icon='home')
        ).add_to(m)
    
    # 중간지점 마커 (빨간색)
    folium.Marker(
        [midpoint['lat'], midpoint['lng']],
        popup="<b>중간지점</b>",
        tooltip="중간지점",
        icon=folium.Icon(color='red', icon='star')
    ).add_to(m)
    
    # 지하철역 마커 (초록색)
    for station in subway_stations:
        folium.Marker(
            [station['lat'], station['lng']],
            popup=f"<b>{station['name']}</b><br>중간지점에서 {station['distance']}m",
            tooltip=station['name'],
            icon=folium.Icon(color='green', icon='subway', prefix='fa')
        ).add_to(m)
    
    return m

# Streamlit UI 설정
st.set_page_config(
    page_title="중간지점 찾기",
    page_icon="🗺️",
    layout="wide"
)

# 스타일 설정
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        padding: 0.5rem;
        font-size: 16px;
        border-radius: 8px;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    h1 {
        color: #2c3e50;
        text-align: center;
        padding-bottom: 1rem;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

# 메인 타이틀
st.title("🗺️ 중간지점 찾기")
st.markdown("---")

# 사이드바 설정
with st.sidebar:
    st.header("📍 출발지 입력")
    st.markdown("여러 명의 출발지를 입력하세요")
    
    # 출발지 개수 선택
    num_locations = st.number_input(
        "출발지 개수",
        min_value=2,
        max_value=10,
        value=2,
        step=1
    )
    
    # 출발지 입력
    addresses = []
    for i in range(num_locations):
        address = st.text_input(
            f"출발지 {i+1}",
            key=f"addr_{i}",
            placeholder="예: 서울 강남구 역삼동"
        )
        if address:
            addresses.append(address)
    
    search_button = st.button("🔍 중간지점 찾기", type="primary")

# 메인 컨텐츠
if search_button:
    if len(addresses) < 2:
        st.warning("⚠️ 최소 2개 이상의 출발지를 입력해주세요.")
    else:
        with st.spinner("🔄 중간지점을 찾는 중..."):
            # 주소를 좌표로 변환
            locations = []
            failed_addresses = []
            
            for addr in addresses:
                result = geocode_address(addr)
                if result:
                    locations.append(result)
                else:
                    failed_addresses.append(addr)
            
            if failed_addresses:
                st.error(f"❌ 다음 주소를 찾을 수 없습니다: {', '.join(failed_addresses)}")
            
            if len(locations) >= 2:
                # 중간지점 계산
                midpoint = find_midpoint(locations)
                
                # 주변 지하철역 찾기
                subway_stations = find_nearby_subway(midpoint['lat'], midpoint['lng'])
                
                # 결과 표시
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.subheader("📍 지도")
                    map_obj = create_map(locations, midpoint, subway_stations)
                    folium_static(map_obj, width=700, height=500)
                
                with col2:
                    st.subheader("🚇 가까운 지하철역")
                    
                    if subway_stations:
                        for i, station in enumerate(subway_stations, 1):
                            # 지도 링크
                            kakao_link = f"https://map.kakao.com/link/map/{station['name']},{station['lat']},{station['lng']}"
                            naver_link = f"https://map.naver.com/index.nhn?elng={station['lng']}&elat={station['lat']}&etext={station['name']}&menu=location"
                            
                            with st.container():
                                st.markdown(f"""
                                <div class="info-box">
                                    <h4>{i}. {station['name']}</h4>
                                    <p>📍 {station['address']}</p>
                                    <p>🚶 중간지점에서 {station['distance']}m</p>
                                    <p>
                                        🗺️ <a href="{naver_link}" target="_blank" style="color: #4CAF50;">네이버지도</a> | 
                                        <a href="{kakao_link}" target="_blank" style="color: #FFCD00;">카카오맵</a>
                                    </p>
                                </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.info("주변에 지하철역이 없습니다.")
                    
                    # 중간지점 주소 정보
                    st.subheader("📊 중간지점 정보")
                    
                    # 평균 거리와 시간 계산
                    distances = [calculate_distance(loc['lat'], loc['lng'], midpoint['lat'], midpoint['lng']) for loc in locations]
                    avg_distance = sum(distances) / len(distances)
                    avg_time = calculate_travel_time(avg_distance)
                    max_distance = max(distances)
                    max_time = calculate_travel_time(max_distance)
                    
                    address_html = ""
                    if midpoint.get('road_address'):
                        address_html += f"<p><strong>📍 도로명:</strong> {midpoint['road_address']}</p>"
                    if midpoint.get('jibun_address'):
                        address_html += f"<p><strong>📮 지번:</strong> {midpoint['jibun_address']}</p>"
                    
                    address_html += f"""
                    <hr style="margin: 10px 0; border: none; border-top: 1px solid #ddd;">
                    <p><strong>📏 평균 거리:</strong> {avg_distance:.2f}km</p>
                    <p><strong>⏱️ 평균 소요시간:</strong> 약 {avg_time}분</p>
                    <p><strong>📏 최대 거리:</strong> {max_distance:.2f}km (약 {max_time}분)</p>
                    """
                    
                    if not midpoint.get('road_address') and not midpoint.get('jibun_address'):
                        address_html = f"""
                        <p><strong>위도:</strong> {midpoint['lat']:.6f}</p>
                        <p><strong>경도:</strong> {midpoint['lng']:.6f}</p>
                        <hr style="margin: 10px 0; border: none; border-top: 1px solid #ddd;">
                        <p><strong>📏 평균 거리:</strong> {avg_distance:.2f}km</p>
                        <p><strong>⏱️ 평균 소요시간:</strong> 약 {avg_time}분</p>
                        <p><strong>📏 최대 거리:</strong> {max_distance:.2f}km (약 {max_time}분)</p>
                        <p style="color: #888; font-size: 0.9em;">※ 주소 정보를 가져올 수 없습니다</p>
                        """
                    
                    st.markdown(f"""
                    <div class="info-box">
                        {address_html}
                    </div>
                    """, unsafe_allow_html=True)
                
                # 출발지별 경로 정보
                st.markdown("---")
                st.subheader("🚶 각 출발지에서 중간지점까지")
                
                route_data = []
                for i, loc in enumerate(locations):
                    distance = calculate_distance(loc['lat'], loc['lng'], midpoint['lat'], midpoint['lng'])
                    time = calculate_travel_time(distance)
                    
                    # 네이버 지도 길찾기 URL (출발지 → 도착지)
                    naver_map_url = f"https://map.naver.com/index.nhn?slng={loc['lng']}&slat={loc['lat']}&stext={loc['address']}&elng={midpoint['lng']}&elat={midpoint['lat']}&etext=중간지점&menu=route&pathType=3"
                    
                    # 카카오맵 URL (목적지만)
                    kakao_map_url = f"https://map.kakao.com/link/to/중간지점,{midpoint['lat']},{midpoint['lng']}"
                    
                    route_data.append({
                        '번호': i+1,
                        '출발지': loc['address'],
                        '거리': f"{distance:.2f}km",
                        '예상 시간': f"약 {time}분",
                        '네이버 길찾기': naver_map_url,
                        '카카오맵': kakao_map_url
                    })
                
                df = pd.DataFrame(route_data)
                st.dataframe(df, use_container_width=True, hide_index=True, column_config={
                    '네이버 길찾기': st.column_config.LinkColumn(),
                    '카카오맵': st.column_config.LinkColumn()
                })
else:
    # 초기 화면
    st.info("""
    ### 사용 방법
    1. 왼쪽 사이드바에서 출발지 개수를 선택하세요
    2. 각 출발지의 주소를 입력하세요 (역 이름도 가능!)
    3. "중간지점 찾기" 버튼을 클릭하세요
    4. 지도에서 중간지점과 경로를 확인하세요
    5. 가까운 지하철역과 각 출발지별 경로 정보를 확인하세요
    
    💡 **팁:** 
    - 상세한 주소일수록 정확한 결과를 얻을 수 있습니다
    - "강남역", "홍대입구역" 같은 역 이름도 입력 가능합니다
    - 네이버 지도 링크: 출발지→중간지점 경로 안내 (대중교통)
    - 카카오맵 링크: 중간지점 위치 표시
    """)
    
    # 예시 이미지나 설명
    st.markdown("---")
    st.subheader("📌 예시")
    
    example_col1, example_col2, example_col3 = st.columns(3)
    
    with example_col1:
        st.markdown("""
        <div class="info-box">
            <h4>🏠 출발지 1</h4>
            <p>서울 강남구 역삼동</p>
        </div>
        """, unsafe_allow_html=True)
    
    with example_col2:
        st.markdown("""
        <div class="info-box">
            <h4>🏠 출발지 2</h4>
            <p>서울 종로구 인사동</p>
        </div>
        """, unsafe_allow_html=True)
    
    with example_col3:
        st.markdown("""
        <div class="info-box">
            <h4>⭐ 중간지점</h4>
            <p>자동으로 계산됩니다</p>
        </div>
        """, unsafe_allow_html=True)

=======
import streamlit as st
import requests
import os
from dotenv import load_dotenv
import folium
from streamlit_folium import folium_static
import pandas as pd

# 환경 변수 로드
load_dotenv()
KAKAO_API_KEY = os.getenv('KAKAO_API_KEY')

# API 키 체크
if not KAKAO_API_KEY:
    st.error("⚠️ .env 파일에 KAKAO_API_KEY를 설정해주세요.")
    st.stop()

def geocode_address(address):
    """주소 또는 장소명을 좌표로 변환"""
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    
    # 1. 먼저 주소 검색 시도
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    params = {"query": address}
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        result = response.json()
        if result['documents']:
            return {
                'lat': float(result['documents'][0]['y']),
                'lng': float(result['documents'][0]['x']),
                'address': result['documents'][0]['address_name']
            }
    
    # 2. 주소 검색 실패 시 키워드 검색 (역 이름, 랜드마크 등)
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    params = {"query": address}
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        result = response.json()
        if result['documents']:
            doc = result['documents'][0]
            return {
                'lat': float(doc['y']),
                'lng': float(doc['x']),
                'address': doc.get('address_name', doc.get('place_name', address))
            }
    
    return None

def coord_to_address(lat, lng):
    """좌표를 주소로 변환 (역지오코딩)"""
    url = "https://dapi.kakao.com/v2/local/geo/coord2address.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {
        "x": lng,
        "y": lat
    }
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        result = response.json()
        if result['documents']:
            doc = result['documents'][0]
            # 도로명 주소 우선, 없으면 지번 주소
            if doc.get('road_address'):
                return {
                    'road_address': doc['road_address']['address_name'],
                    'jibun_address': doc['address']['address_name'] if doc.get('address') else ''
                }
            elif doc.get('address'):
                return {
                    'road_address': '',
                    'jibun_address': doc['address']['address_name']
                }
    return {
        'road_address': '',
        'jibun_address': ''
    }

def find_midpoint(locations):
    """여러 좌표의 중간지점 계산"""
    if not locations:
        return None
    
    avg_lat = sum(loc['lat'] for loc in locations) / len(locations)
    avg_lng = sum(loc['lng'] for loc in locations) / len(locations)
    
    # 좌표를 주소로 변환
    address_info = coord_to_address(avg_lat, avg_lng)
    
    return {
        'lat': avg_lat, 
        'lng': avg_lng,
        'road_address': address_info['road_address'],
        'jibun_address': address_info['jibun_address']
    }

def find_nearby_subway(lat, lng, radius=1000):
    """주변 지하철역 검색"""
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {
        "query": "지하철역",
        "x": lng,
        "y": lat,
        "radius": radius,
        "sort": "distance"
    }
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        result = response.json()
        if result['documents']:
            stations = []
            for doc in result['documents'][:5]:  # 상위 5개만
                stations.append({
                    'name': doc['place_name'],
                    'address': doc['address_name'],
                    'distance': int(doc['distance']),
                    'lat': float(doc['y']),
                    'lng': float(doc['x'])
                })
            return stations
    return []

def create_map(locations, midpoint, subway_stations):
    """지도 생성"""
    m = folium.Map(
        location=[midpoint['lat'], midpoint['lng']], 
        zoom_start=13,
        tiles='OpenStreetMap'
    )
    
    # 출발지 마커 (파란색)
    for i, loc in enumerate(locations):
        folium.Marker(
            [loc['lat'], loc['lng']],
            popup=f"출발지 {i+1}<br>{loc.get('address', '')}",
            tooltip=f"출발지 {i+1}",
            icon=folium.Icon(color='blue', icon='home')
        ).add_to(m)
    
    # 중간지점 마커 (빨간색)
    folium.Marker(
        [midpoint['lat'], midpoint['lng']],
        popup="중간지점",
        tooltip="중간지점",
        icon=folium.Icon(color='red', icon='star')
    ).add_to(m)
    
    # 지하철역 마커 (초록색)
    for station in subway_stations:
        folium.Marker(
            [station['lat'], station['lng']],
            popup=f"{station['name']}<br>{station['distance']}m",
            tooltip=station['name'],
            icon=folium.Icon(color='green', icon='subway', prefix='fa')
        ).add_to(m)
    
    return m

# Streamlit UI 설정
st.set_page_config(
    page_title="중간지점 찾기",
    page_icon="🗺️",
    layout="wide"
)

# 스타일 설정
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        padding: 0.5rem;
        font-size: 16px;
        border-radius: 8px;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    h1 {
        color: #2c3e50;
        text-align: center;
        padding-bottom: 1rem;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

# 메인 타이틀
st.title("🗺️ 중간지점 찾기")
st.markdown("---")

# 사이드바 설정
with st.sidebar:
    st.header("📍 출발지 입력")
    st.markdown("여러 명의 출발지를 입력하세요")
    
    # 출발지 개수 선택
    num_locations = st.number_input(
        "출발지 개수",
        min_value=2,
        max_value=10,
        value=2,
        step=1
    )
    
    # 출발지 입력
    addresses = []
    for i in range(num_locations):
        address = st.text_input(
            f"출발지 {i+1}",
            key=f"addr_{i}",
            placeholder="예: 서울 강남구 역삼동"
        )
        if address:
            addresses.append(address)
    
    search_button = st.button("🔍 중간지점 찾기", type="primary")

# 메인 컨텐츠
if search_button:
    if len(addresses) < 2:
        st.warning("⚠️ 최소 2개 이상의 출발지를 입력해주세요.")
    else:
        with st.spinner("🔄 중간지점을 찾는 중..."):
            # 주소를 좌표로 변환
            locations = []
            failed_addresses = []
            
            for addr in addresses:
                result = geocode_address(addr)
                if result:
                    locations.append(result)
                else:
                    failed_addresses.append(addr)
            
            if failed_addresses:
                st.error(f"❌ 다음 주소를 찾을 수 없습니다: {', '.join(failed_addresses)}")
            
            if len(locations) >= 2:
                # 중간지점 계산
                midpoint = find_midpoint(locations)
                
                # 주변 지하철역 찾기
                subway_stations = find_nearby_subway(midpoint['lat'], midpoint['lng'])
                
                # 결과 표시
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.subheader("📍 지도")
                    map_obj = create_map(locations, midpoint, subway_stations)
                    folium_static(map_obj, width=700, height=500)
                
                with col2:
                    st.subheader("🚇 가까운 지하철역")
                    
                    if subway_stations:
                        for i, station in enumerate(subway_stations, 1):
                            with st.container():
                                st.markdown(f"""
                                <div class="info-box">
                                    <h4>{i}. {station['name']}</h4>
                                    <p>📍 {station['address']}</p>
                                    <p>🚶 거리: {station['distance']}m</p>
                                </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.info("주변에 지하철역이 없습니다.")
                    
                    # 중간지점 주소 정보
                    st.subheader("📊 중간지점 정보")
                    address_html = ""
                    if midpoint.get('road_address'):
                        address_html += f"<p><strong>📍 도로명:</strong> {midpoint['road_address']}</p>"
                    if midpoint.get('jibun_address'):
                        address_html += f"<p><strong>📮 지번:</strong> {midpoint['jibun_address']}</p>"
                    
                    if not address_html:
                        address_html = f"""
                        <p><strong>위도:</strong> {midpoint['lat']:.6f}</p>
                        <p><strong>경도:</strong> {midpoint['lng']:.6f}</p>
                        <p style="color: #888; font-size: 0.9em;">※ 주소 정보를 가져올 수 없습니다</p>
                        """
                    
                    st.markdown(f"""
                    <div class="info-box">
                        {address_html}
                    </div>
                    """, unsafe_allow_html=True)
                
                # 출발지 목록
                st.markdown("---")
                st.subheader("📋 입력된 출발지")
                df = pd.DataFrame([
                    {
                        '번호': i+1,
                        '주소': loc['address'],
                        '위도': f"{loc['lat']:.6f}",
                        '경도': f"{loc['lng']:.6f}"
                    }
                    for i, loc in enumerate(locations)
                ])
                st.dataframe(df, use_container_width=True, hide_index=True)
else:
    # 초기 화면
    st.info("""
    ### 사용 방법
    1. 왼쪽 사이드바에서 출발지 개수를 선택하세요
    2. 각 출발지의 주소를 입력하세요
    3. "중간지점 찾기" 버튼을 클릭하세요
    4. 지도에서 중간지점과 가까운 지하철역을 확인하세요
    
    💡 **팁:** 상세한 주소일수록 정확한 결과를 얻을 수 있습니다.
    """)
    
    # 예시 이미지나 설명
    st.markdown("---")
    st.subheader("📌 예시")
    
    example_col1, example_col2, example_col3 = st.columns(3)
    
    with example_col1:
        st.markdown("""
        <div class="info-box">
            <h4>🏠 출발지 1</h4>
            <p>서울 강남구 역삼동</p>
        </div>
        """, unsafe_allow_html=True)
    
    with example_col2:
        st.markdown("""
        <div class="info-box">
            <h4>🏠 출발지 2</h4>
            <p>서울 종로구 인사동</p>
        </div>
        """, unsafe_allow_html=True)
    
    with example_col3:
        st.markdown("""
        <div class="info-box">
            <h4>⭐ 중간지점</h4>
            <p>자동으로 계산됩니다</p>
        </div>
        """, unsafe_allow_html=True)

>>>>>>> 434bfd2a51f80f7b04897039454a357548231c18

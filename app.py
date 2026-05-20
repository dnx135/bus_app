import streamlit as st
import pandas as pd
from datetime import datetime
import os

# 페이지 기본 설정
st.set_page_config(
    page_title="평택 사업장 셔틀버스 스마트 조회 시스템",
    page_icon="🚌",
    layout="wide"
)

# 커스텀 CSS 스타일링 (세련된 기업용 UI 디자인 적용)
st.markdown("""
    <style>
    .main-title {
        font-size: 28px;
        font-weight: bold;
        color: #1E3A8A;
        margin-bottom: 5px;
    }
    .sub-title {
        font-size: 14px;
        color: #6B7280;
        margin-bottom: 25px;
    }
    .route-box {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        padding: 18px;
        border-radius: 8px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .station-badge {
        display: inline-block;
        padding: 5px 10px;
        margin: 2px;
        border-radius: 4px;
        background-color: #E5E7EB;
        color: #374151;
        font-size: 13px;
        font-weight: 500;
    }
    /* 출발지 강조 스타일 (초록색 상자) */
    .station-dep {
        background-color: #D1FAE5 !important;
        color: #065F46 !important;
        border: 1px solid #34D399;
        font-weight: bold !important;
    }
    /* 도착지 강조 스타일 (파란색 상자) */
    .station-arr {
        background-color: #DBEAFE !important;
        color: #1E40AF !important;
        border: 1px solid #60A5FA;
        font-weight: bold !important;
    }
    /* 미운행/스킵 정류장 스타일 (연한 회색) */
    .station-pass {
        background-color: #F9FAFB;
        color: #9CA3AF;
        border: 1px solid #F3F4F6;
    }
    .arrow {
        color: #9CA3AF;
        font-weight: bold;
        margin: 0 4px;
    }
    </style>
""", unsafe_allow_html=True)

# 타이틀 표시
st.markdown('<div class="main-title">🚌 평택 사업장 셔틀버스 스마트 조회 서비스</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">출발지와 도착지를 단순하게 입력해도 실시간으로 정확한 탑승 위치와 전체 경로를 안내합니다.</div>', unsafe_allow_html=True)

# 데이터 로드 함수 (캐싱 적용으로 속도 향상)
@st.cache_data
def load_data():
    #base_path = r"C:\Users\dnx13\OneDrive\Desktop\Python\bus_app"
    
    routes_path = "route_stations.xlsx"
    timetable_path = "timetable.xlsx"
    
    # 1. 파일 경로 체크
    if not os.path.exists(routes_path):
        st.error(f"⚠️ 'route_stations.xlsx' 파일을 찾을 수 없습니다. 경로를 확인하세요: {routes_path}")
        st.stop()
    if not os.path.exists(timetable_path):
        st.error(f"⚠️ 'timetable.xlsx' 파일을 찾을 수 없습니다. 경로를 확인하세요: {timetable_path}")
        st.stop()
        
    # 2. 엑셀 파일 로드
    df_routes = pd.read_excel(routes_path)
    df_timetable = pd.read_excel(timetable_path)
    
    # 3. 노선 이름의 줄바꿈(\n) 및 공백 제거하여 매칭 불일치 해결
    df_routes['route_name'] = df_routes['route_name'].astype(str).str.replace('\n', '', regex=False).str.strip()
    df_timetable['노선'] = df_timetable['노선'].astype(str).str.replace('\n', '', regex=False).str.strip()
    
    # 평일/휴일 데이터 공백 제거 전처리
    df_timetable['평일/휴일'] = df_timetable['평일/휴일'].astype(str).str.strip()
    
    # 4. 시간 포맷 전처리 (초 단위나 공백 제거 및 패딩)
    def clean_time_string(val):
        if pd.isna(val):
            return "00:00"
        val_str = str(val).strip()
        if " " in val_str:
            val_str = val_str.split(" ")[1]
        
        parts = val_str.split(':')
        if len(parts) >= 2:
            return f"{parts[0].zfill(2)}:{parts[1].zfill(2)}"
        return val_str

    df_timetable['시간'] = df_timetable['시간'].apply(clean_time_string)
    
    # 시간 필터링을 위한 time 객체 컬럼 생성
    df_timetable['time_obj'] = pd.to_datetime(df_timetable['시간'], format='%H:%M').dt.time
    
    return df_routes, df_timetable

# 전역 변수로 안전하게 데이터 정의
df_routes, df_timetable = load_data()


# --- 입력 UI 검색 필드 구성 ---
st.markdown('<p style="font-weight:bold; font-size:16px; margin-bottom:5px;">🔍 탑승 조건 입력</p>', unsafe_allow_html=True)

# 1) 실시간 현재 시간 및 요일 판별 자동 설정
now = datetime.now()
current_time_str = now.strftime("%H:%M")
current_day_of_week = now.weekday()  # 0:월, 1:화, ..., 5:토, 6:일

# 월~금(0~4)이면 평일(인덱스 0), 토~일(5~6)이면 휴일(인덱스 1) 기본 선택
default_day_idx = 1 if current_day_of_week >= 5 else 0

# UI 배치 (4열로 확장)
col1, col2, col3, col4 = st.columns([1.5, 1, 1.5, 1.5])

with col1:
    input_time = st.text_input("🕐 조회 시작 시간 (HH:MM)", value=current_time_str, help="이 시간 이후에 출발하는 버스 편을 찾습니다.")
with col2:
    # 평일/휴일 선택창 (오늘 날짜 기준으로 대조군 대입)
    day_type = st.radio("📅 운행 요일 선택", options=["평일", "휴일"], index=default_day_idx, horizontal=True)
with col3:
    user_dep = st.text_input("출발지", value="사무2동", help="괄호 없이 편하게 입력하세요 (예: 사무2동)")
with col4:
    user_arr = st.text_input("도착지", value="사무1동", help="괄호 없이 편하게 입력하세요 (예: 사무1동)")

search_button = st.button("🚀 노선 실시간 검색", type="primary", use_container_width=True)


# --- 셔틀버스 검색 및 결과 시각화 로직 ---
if search_button or input_time:
    try:
        input_dt = pd.to_datetime(input_time, format='%H:%M').time()
    except:
        st.error("❗ 시간 형식이 올바르지 않습니다. HH:MM (예: 07:30) 형태로 입력해 주세요.")
        st.stop()

    if not user_dep.strip() or not user_arr.strip():
        st.warning("⚠️ 출발지와 도착지 검색어를 모두 입력해 주세요.")
        st.stop()

    # [핵심 패치] 입력 시간 필터링 + 유저가 선택한 평일/휴일 조건 추가 필터링
    df_filtered_time = df_timetable[
        (df_timetable['time_obj'] >= input_dt) & 
        (df_timetable['평일/휴일'] == day_type)
    ].sort_values('시간')

    matched_count = 0
    st.markdown(f"### 📋 검색 결과 (조회 기준: {day_type} / {input_time} 이후 출발)")

    for _, row in df_filtered_time.iterrows():
        bus_time = row['시간']
        route_name = row['노선']
        
        # 중복 데이터 제거 및 seq 순 정렬
        stations = df_routes[df_routes['route_name'] == route_name].drop_duplicates(['seq', 'station_name']).sort_values('seq')
        station_list = stations['station_name'].tolist()
        
        # 출발지와 도착지가 될 수 있는 모든 정류장의 인덱스(위치) 검색
        dep_indices = [i for i, stn in enumerate(station_list) if user_dep.strip() in stn]
        arr_indices = [i for i, stn in enumerate(station_list) if user_arr.strip() in stn]
        
        valid_paths = []
        for d_idx in dep_indices:
            for a_idx in arr_indices:
                if d_idx < a_idx: 
                    valid_paths.append((d_idx, a_idx))
                    
        for dep_idx, arr_idx in valid_paths:
            matched_count += 1
            
            # 전체 경로 생성 및 출발지/도착지 고유 색상 강조 HTML 빌드
            path_html_list = []
            for idx, station in enumerate(station_list):
                if idx == dep_idx:
                    path_html_list.append(f'<span class="station-badge station-dep">🛫 {station}</span>')
                elif idx == arr_idx:
                    path_html_list.append(f'<span class="station-badge station-arr">🛬 {station}</span>')
                elif dep_idx < idx < arr_idx:
                    path_html_list.append(f'<span class="station-badge">{station}</span>')
                else:
                    path_html_list.append(f'<span class="station-badge station-pass">{station}</span>')
            
            full_route_html = ' <span class="arrow">→</span> '.join(path_html_list)
            
            # UI 레이아웃 출력
            st.markdown(f"""
            <div class="route-box">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <span style="font-size: 19px; font-weight: bold; color: #1E3A8A;">⏰ {bus_time} 출발 ({day_type})</span>
                    <span style="background-color: #EFF6FF; color: #1D4ED8; padding: 4px 14px; border-radius: 20px; font-weight: bold; font-size: 13px;">{route_name}</span>
                </div>
                <div style="line-height: 1.8;">
                    <p style="margin: 0 0 6px 0; font-size: 13px; color: #4B5563; font-weight: bold;">📍 전체 운행 노선 현황</p>
                    {full_route_html}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
    if matched_count == 0:
        st.info(f"💡 {day_type} 해당 시간대 이후로는 입력하신 구간을 운행하는 버스 편이 없습니다. 검색 조건을 확인해 보세요.")
import os
import json
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ----------------------------------------------------
# 1. 페이지 초기 설정 및 테마 스타일링
# ----------------------------------------------------
st.set_page_config(
    page_title="K-Expo LeadGen Lite CRM",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS를 통한 UI 프리미엄 디자인 적용 (유려한 카드 섀도우 및 폰트 개선)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* KPI 카드 스타일 */
    .kpi-card {
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        border: 1px solid #374151;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: transform 0.2s ease-in-out;
        color: #ffffff;
    }
    .kpi-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
    }
    .kpi-label {
        font-size: 14px;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 500;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 32px;
        font-weight: 700;
        color: #60a5fa; /* 기본 블루색 */
        margin-bottom: 4px;
    }
    .kpi-sub {
        font-size: 12px;
        color: #4b5563;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 2. 데이터 로드 및 전처리 함수
# ----------------------------------------------------
@st.cache_data
def load_data():
    # 현재 파일(app.py)의 위치를 기준으로 상위 폴더(프로젝트 루트) 경로 계산
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    companies_file = os.path.join(BASE_DIR, "data", "companies.csv")
    scores_file = os.path.join(BASE_DIR, "data", "lead_scores.csv")
    exhibitions_file = os.path.join(BASE_DIR, "data", "exhibitions.csv")
    
    if not os.path.exists(companies_file) or not os.path.exists(scores_file):
        st.error(f"⚠️ 데이터 파일이 유실되었거나 아직 스코어링이 실행되지 않았습니다. (확인 경로: {companies_file})")
        return None, None
        
    df_comp = pd.read_csv(companies_file, encoding="utf-8-sig")
    df_score = pd.read_csv(scores_file, encoding="utf-8-sig")
    df_exh = pd.read_csv(exhibitions_file, encoding="utf-8-sig") if os.path.exists(exhibitions_file) else None
    
    # 두 데이터셋 머지 (기업 마스터 데이터 + 스코어 정보)
    # 중복방지를 위해 score 데이터는 필요한 컬럼만 추출
    df_merged = pd.merge(df_comp, df_score[["company_id", "score", "breakdown"]], on="company_id")
    
    # 전시회명이 있을 경우 머지하여 결합
    if df_exh is not None:
        df_merged = pd.merge(df_merged, df_exh[["exhibition_id", "name"]], on="exhibition_id", how="left")
        df_merged = df_merged.rename(columns={"name": "exhibition_name"})
    else:
        df_merged["exhibition_name"] = df_merged["exhibition_id"]
        
    # breakdown 컬럼 (JSON 문자열)을 개별 세부 점수 컬럼으로 파싱
    def parse_breakdown(row):
        try:
            b_dict = json.loads(row["breakdown"])
            return pd.Series([
                b_dict.get("website", 0.0),
                b_dict.get("export", 0.0),
                b_dict.get("employee", 0.0),
                b_dict.get("email", 0.0)
            ])
        except Exception:
            return pd.Series([0.0, 0.0, 0.0, 0.0])
            
    df_merged[[
        "score_website", "score_export", "score_employee", "score_email"
    ]] = df_merged.apply(parse_breakdown, axis=1)
    
    return df_merged, df_exh

df, df_exh = load_data()

if df is not None:
    # ----------------------------------------------------
    # 3. 사이드바 검색 및 필터 패널
    # ----------------------------------------------------
    st.sidebar.image("https://images.unsplash.com/photo-1551836022-d5d88e9218df?auto=format&fit=crop&w=300&q=80", caption="🎯 K-Expo LeadGen Lite", use_column_width=True)
    st.sidebar.header("🔍 필터 옵션")
    
    # 1) 기업명 검색
    search_query = st.sidebar.text_input("기업명 검색", placeholder="예: 네추럴, 바이오...")
    
    # 2) 카테고리 필터
    categories = sorted(df["category"].unique())
    selected_categories = st.sidebar.multiselect("카테고리 선택", categories, default=categories)
    
    # 3) 전시회 필터
    exhibition_list = sorted(df["exhibition_name"].unique())
    selected_exhibitions = st.sidebar.multiselect("참가 전시회 선택", exhibition_list, default=exhibition_list)
    
    # 4) 최소 Lead Score 슬라이더
    min_score, max_score = int(df["score"].min()), int(df["score"].max())
    score_range = st.sidebar.slider("Lead Score 범위", min_score, max_score, (min_score, max_score))
    
    # 5) 수출 기업 여부 필터
    export_filter = st.sidebar.radio("수출 지원 여부", ["전체", "수출 기업만 (True)", "내수 기업만 (False)"])

    # 데이터 필터링 로직 적용
    filtered_df = df.copy()
    
    if search_query:
        filtered_df = filtered_df[filtered_df["company_name"].str.contains(search_query, case=False, na=False)]
        
    if selected_categories:
        filtered_df = filtered_df[filtered_df["category"].isin(selected_categories)]
        
    if selected_exhibitions:
        filtered_df = filtered_df[filtered_df["exhibition_name"].isin(selected_exhibitions)]
        
    filtered_df = filtered_df[
        (filtered_df["score"] >= score_range[0]) & 
        (filtered_df["score"] <= score_range[1])
    ]
    
    if export_filter == "수출 기업만 (True)":
        filtered_df = filtered_df[filtered_df["has_export"].astype(str).str.lower() == "true"]
    elif export_filter == "내수 기업만 (False)":
        filtered_df = filtered_df[filtered_df["has_export"].astype(str).str.lower() == "false"]

    # ----------------------------------------------------
    # 4. 메인 화면 헤더 및 KPI 요약 카드 영역
    # ----------------------------------------------------
    st.title("🎯 K-Expo LeadGen Lite CRM 대시보드")
    st.subheader("전시회 참관 리드 가치 평가 및 마케팅 우선순위 대시보드")
    st.markdown("---")
    
    # KPI 요약 지표 계산
    total_companies = len(df)
    avg_score = df["score"].mean()
    top_20_percentile = df["score"].quantile(0.8) # 상위 20% 기준 점수선
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">전체 유치 기업 수</div>
            <div class="kpi-value" style="color: #60a5fa;">{total_companies} 개사</div>
            <div class="kpi-sub">총 4개 국내 주요 소비재 전시회 참가사</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">평균 Lead Score</div>
            <div class="kpi-value" style="color: #34d399;">{avg_score:.1f} 점</div>
            <div class="kpi-sub">100점 만점 기준 가중치 부여 종합 평점</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">상위 20% 리드 커트라인</div>
            <div class="kpi-value" style="color: #f59e0b;">{top_20_percentile:.1f} 점</div>
            <div class="kpi-sub">고가치 고객(A등급) 분류를 위한 최소 스코어</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ----------------------------------------------------
    # 5. 차트 분석 영역 (중단)
    # ----------------------------------------------------
    st.markdown("### 📊 인터랙티브 리드 데이터 분석")
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.markdown("#### **Lead Score 점수 분포**")
        # Plotly를 사용한 세련된 스코어 히스토그램 생성
        fig_hist = px.histogram(
            filtered_df, 
            x="score", 
            nbins=12,
            title=None,
            labels={"score": "Lead Score (종합 점수)", "count": "기업 수"},
            color_discrete_sequence=["#3b82f6"],
            opacity=0.85
        )
        fig_hist.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=20, r=20, t=10, b=20),
            height=300,
            xaxis=dict(showgrid=True, gridcolor="#374151"),
            yaxis=dict(showgrid=True, gridcolor="#374151"),
            font=dict(color="#9ca3af")
        )
        # 상위 20% 기준 임계선 세로선 표시
        fig_hist.add_vline(x=top_20_percentile, line_dash="dash", line_color="#f59e0b", annotation_text="상위 20% 기준선")
        st.plotly_chart(fig_hist, use_container_width=True)
        
    with chart_col2:
        st.markdown("#### **카테고리별 유치 분포 및 평균 점수**")
        # 카테고리별 기업 수 및 평균 스코어 연산
        cat_summary = filtered_df.groupby("category").agg(
            기업수=("company_id", "count"),
            평균점수=("score", "mean")
        ).reset_index()
        
        # 복합 이중 차트 그리기 (막대: 기업수, 선: 평균점수)
        fig_combo = go.Figure()
        fig_combo.add_trace(go.Bar(
            x=cat_summary["category"],
            y=cat_summary["기업수"],
            name="기업 수 (개사)",
            marker_color="#10b981",
            yaxis="y1",
            opacity=0.8
        ))
        fig_combo.add_trace(go.Scatter(
            x=cat_summary["category"],
            y=cat_summary["평균점수"],
            name="평균 점수 (점)",
            marker_color="#f59e0b",
            line=dict(width=3, shape="spline"),
            yaxis="y2"
        ))
        
        fig_combo.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=20, r=20, t=10, b=20),
            height=300,
            font=dict(color="#9ca3af"),
            yaxis1=dict(
                title=dict(text="기업 수", font=dict(color="#10b981")),
                showgrid=True,
                gridcolor="#374151",
                tickfont=dict(color="#10b981")
            ),
            yaxis2=dict(
                title=dict(text="평균 점수", font=dict(color="#f59e0b")),
                overlaying="y",
                side="right",
                showgrid=False,
                tickfont=dict(color="#f59e0b")
            ),
            legend=dict(x=0.01, y=0.99, bgcolor="rgba(0,0,0,0)")
        )
        st.plotly_chart(fig_combo, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ----------------------------------------------------
    # 6. 고해상도 리드 테이블 및 액션 영역 (하단)
    # ----------------------------------------------------
    st.markdown("### 📋 참관 기업 리드 상세 목록")
    
    # 1) 컬럼 정렬 및 가독성 좋은 한글 라벨링 처리
    display_df = filtered_df[[
        "company_id", "company_name", "category", "exhibition_name", 
        "booth_number", "employee_count", "has_export", "score",
        "score_website", "score_export", "score_employee", "score_email"
    ]].copy()
    
    display_df = display_df.rename(columns={
        "company_id": "기업 ID",
        "company_name": "기업명",
        "category": "카테고리",
        "exhibition_name": "전시회명",
        "booth_number": "부스 번호",
        "employee_count": "직원 수(명)",
        "has_export": "수출 지원 여부",
        "score": "Lead Score (종합)",
        "score_website": "웹사이트 점수",
        "score_export": "수출 가산점",
        "score_employee": "규모 점수",
        "score_email": "이메일 점수"
    })
    
    # 2) 데이터 정렬 (Lead Score 기준 내림차순 디폴트)
    display_df = display_df.sort_values(by="Lead Score (종합)", ascending=False)
    
    # 3) 인터랙티브 데이터 프레임 출력
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
    
    # 4) 다운로드 기능 영역
    st.markdown("#### 📥 필터링된 타겟 데이터 내보내기")
    csv_data = display_df.to_csv(index=False, encoding="utf-8-sig")
    
    st.download_button(
        label="📄 필터링된 기업 목록 CSV 다운로드",
        data=csv_data,
        file_name="filtered_expo_leads.csv",
        mime="text/csv",
        use_container_width=False
    )

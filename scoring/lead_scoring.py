import os
import pandas as pd
import json

# 1. 스코어링 가중치 및 규칙 설정 (Config)
CONFIG = {
    # 총합 100점 만점 기준 각 항목별 가중치 배점
    "weights": {
        "website_quality": 30,  # 웹사이트 퀄리티 점수 반영 비중 (최대 30점)
        "has_export": 25,       # 수출 여부 가산점 (최대 25점)
        "employee_count": 20,    # 기업 규모(직원 수) 점수 (최대 20점)
        "email_trust": 25        # 이메일 신뢰도 점수 반영 비중 (최대 25점)
    },
    # 직원 수 기준 구간별 점수 부여 기준
    "employee_tiers": [
        {"min_employees": 100, "score_ratio": 1.0},   # 100명 이상: 100% (20점)
        {"min_employees": 50,  "score_ratio": 0.75},  # 50명~99명: 75% (15점)
        {"min_employees": 10,  "score_ratio": 0.5},   # 10명~49명: 50% (10점)
        {"min_employees": 0,   "score_ratio": 0.25}   # 10명 미만: 25% (5점)
    ]
}

def calculate_lead_scores():
    # 파일 경로 정의
    companies_path = "data/companies.csv"
    output_path = "data/lead_scores.csv"

    if not os.path.exists(companies_path):
        print(f"[ERROR] '{companies_path}' 파일이 존재하지 않습니다. 먼저 샘플 데이터를 생성해 주세요.")
        return

    # 데이터 로드
    df = pd.read_csv(companies_path)

    # 문자열로 저장된 has_export를 boolean 타입으로 변환
    if df["has_export"].dtype == object:
        df["has_export_bool"] = df["has_export"].astype(str).str.lower() == "true"
    else:
        df["has_export_bool"] = df["has_export"].astype(bool)

    # 2. 항목별 세부 점수 계산
    # 1) 웹사이트 퀄리티 스코어 계산 (0~100점을 0~weights['website_quality'] 범위로 스케일링)
    website_max = CONFIG["weights"]["website_quality"]
    df["score_website"] = (df["website_quality_score"] / 100.0) * website_max

    # 2) 수출 여부 점수 계산 (has_export가 True 이면 배점 전체 부여, False 이면 0점)
    export_max = CONFIG["weights"]["has_export"]
    df["score_export"] = df["has_export_bool"].apply(lambda x: export_max if x else 0.0)

    # 3) 직원 수 점수 계산 (구간별 비율 * 배점)
    employee_max = CONFIG["weights"]["employee_count"]
    def get_employee_score(emp_count):
        for tier in CONFIG["employee_tiers"]:
            if emp_count >= tier["min_employees"]:
                return tier["score_ratio"] * employee_max
        return 0.0

    df["score_employee"] = df["employee_count"].apply(get_employee_score)

    # 4) 이메일 신뢰도 스코어 계산 (0~100점을 0~weights['email_trust'] 범위로 스케일링)
    email_max = CONFIG["weights"]["email_trust"]
    df["score_email"] = (df["email_trust_score"] / 100.0) * email_max

    # 5) 최종 스코어 합산 (소수점 첫째짜리까지 반올림)
    df["score"] = (df["score_website"] + df["score_export"] + df["score_employee"] + df["score_email"]).round(1)

    # 6) 세부 항목 breakdown 생성 (JSON 포맷의 문자열로 변환하여 가독성 증대 및 대시보드 연동 최적화)
    def make_breakdown(row):
        breakdown_dict = {
            "website": round(row["score_website"], 1),
            "export": round(row["score_export"], 1),
            "employee": round(row["score_employee"], 1),
            "email": round(row["score_email"], 1)
        }
        return json.dumps(breakdown_dict)

    df["breakdown"] = df.apply(make_breakdown, axis=1)

    # 3. 결과 저장용 데이터프레임 구성 및 저장
    result_df = df[[
        "company_id", 
        "company_name", 
        "score", 
        "breakdown"
    ]].copy()

    # 스코어 기준 내림차순 정렬
    result_df = result_df.sort_values(by="score", ascending=False)

    # CSV 저장 (utf-8-sig로 저장하여 Excel 깨짐 방지)
    result_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"[SUCCESS] Lead scoring completed! Results saved to '{output_path}'.")

if __name__ == "__main__":
    calculate_lead_scores()

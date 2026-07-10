import os
import csv
import random
from datetime import datetime, timedelta

def generate_data():
    # 데이터 생성을 재현 가능하게 하기 위해 시드 설정
    random.seed(42)

    # 1. 전시회 데이터 생성 (exhibitions.csv)
    exhibitions = [
        {
            "exhibition_id": "EXH001",
            "name": "K-Beauty Expo 2026",
            "start_date": "2026-10-15",
            "end_date": "2026-10-18",
            "venue": "KINTEX"
        },
        {
            "exhibition_id": "EXH002",
            "name": "Seoul Food & Hotel 2026",
            "start_date": "2026-06-02",
            "end_date": "2026-06-05",
            "venue": "COEX"
        },
        {
            "exhibition_id": "EXH003",
            "name": "Mega Show 2026 Season 1",
            "start_date": "2026-08-20",
            "end_date": "2026-08-23",
            "venue": "SETEC"
        },
        {
            "exhibition_id": "EXH004",
            "name": "Korea Consumer Goods Fair 2026",
            "start_date": "2026-11-12",
            "end_date": "2026-11-15",
            "venue": "BEXCO"
        }
    ]

    # 2. 참가기업 데이터 생성을 위한 가상 회사명 풀
    company_prefixes = [
        "네추럴", "에코", "스마트", "바이오", "뷰티", "푸드", "메디", "글로벌", "케이", 
        "더블유", "에이치", "지에스", "스타", "오가닉", "힐링", "프레쉬", "그린", "탑", "루키"
    ]
    company_suffixes = [
        "코스메틱", "랩", "푸드텍", "리빙", "이노베이션", "트레이딩", "제약", "코리아", 
        "테크", "어패럴", "바이오", "하우스", "컴퍼니", "인더스트리", "솔루션", "시스템"
    ]
    
    categories_by_exhibition = {
        "EXH001": ["Beauty", "Tech"],
        "EXH002": ["Food"],
        "EXH003": ["Living", "Fashion", "Beauty", "Food"],
        "EXH004": ["Living", "Fashion", "Tech"]
    }

    # 기업 수 정의 (총 45개 기업 생성)
    total_companies = 45
    companies = []
    
    # 중복 회사명 방지용 셋
    used_names = set()

    for i in range(1, total_companies + 1):
        # 1) 기업 ID
        company_id = f"COM{i:03d}"
        
        # 2) 임의의 전시회 할당
        exh = random.choice(exhibitions)
        exhibition_id = exh["exhibition_id"]
        
        # 3) 기업명 생성 (중복 방지)
        while True:
            prefix = random.choice(company_prefixes)
            suffix = random.choice(company_suffixes)
            company_name = f"(주){prefix}{suffix}"
            if company_name not in used_names:
                used_names.add(company_name)
                break
                
        # 4) 부스 번호 (예: A-101, B-204 등)
        booth_letter = random.choice(["A", "B", "C", "D"])
        booth_num = random.randint(101, 399)
        booth_number = f"{booth_letter}-{booth_num}"
        
        # 5) 전시회별 카테고리 매칭
        category = random.choice(categories_by_exhibition[exhibition_id])
        
        # 6) 직원 수 (5명 ~ 350명 사이의 멱법칙 또는 롱테일 형태로 생성)
        # 소기업이 대기업보다 많도록 지수 분포 활용
        employee_count = int(random.expovariate(1/40) + 5)
        if employee_count > 500:
            employee_count = random.randint(150, 450)
            
        # 7) 수출 여부 (직원 수에 약간 비례하도록 설정하여 일관성 부여)
        if employee_count > 50:
            has_export = "True" if random.random() < 0.85 else "False"
        else:
            has_export = "True" if random.random() < 0.35 else "False"
            
        # 8) 웹사이트 퀄리티 스코어 (0~100)
        # 마찬가지로 대형 기업의 웹사이트가 평균적으로 약간 좋도록 유도
        if employee_count > 80:
            website_quality_score = int(random.triangular(50, 100, 85))
        else:
            website_quality_score = int(random.randint(20, 95))
            
        # 9) 이메일 신뢰도 스코어 (0~100)
        email_trust_score = int(random.triangular(40, 100, 75))

        companies.append({
            "company_id": company_id,
            "exhibition_id": exhibition_id,
            "company_name": company_name,
            "booth_number": booth_number,
            "category": category,
            "employee_count": employee_count,
            "has_export": has_export,
            "website_quality_score": website_quality_score,
            "email_trust_score": email_trust_score
        })

    # CSV 파일로 저장
    os.makedirs("data", exist_ok=True)
    
    # 1) exhibitions.csv 저장
    exhibitions_file = "data/exhibitions.csv"
    with open(exhibitions_file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["exhibition_id", "name", "start_date", "end_date", "venue"])
        writer.writeheader()
        writer.writerows(exhibitions)
        
    # 2) companies.csv 저장
    companies_file = "data/companies.csv"
    with open(companies_file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "company_id", "exhibition_id", "company_name", "booth_number",
            "category", "employee_count", "has_export", "website_quality_score", "email_trust_score"
        ])
        writer.writeheader()
        writer.writerows(companies)

    print("[SUCCESS] Sample data generation completed!")
    print(f" - Exhibitions data: {len(exhibitions)} created ({exhibitions_file})")
    print(f" - Companies data: {len(companies)} created ({companies_file})")

if __name__ == "__main__":
    generate_data()

# CHA 규정 혁신 어시스턴트

GPT API 기반 대학 규정 검색·분석·개정안 생성 도구

## 🏗️ 프로젝트 구조

```
cha-regulation-app/
├── app.py                     ← Streamlit 메인 앱
├── parse_xml_to_json.py       ← XML→JSON 전처리 (로컬 1회 실행)
├── requirements.txt           ← 패키지 목록
├── .streamlit/
│   └── config.toml            ← Streamlit 테마 설정
├── data/
│   └── regulations.json       ← 136개 규정 데이터 (전처리 결과)
└── README.md
```

## 🚀 배포 가이드 (전체 과정)

### 1단계: HWP → XML 변환 (이전에 안내한 스크립트)
```bash
python convert_hwp_to_xml.py
```
결과: `D:\Temp\aicentricuniv\cha_regulations\xml\` 에 136개 XML 파일

### 2단계: XML → JSON 전처리
```bash
cd D:\Temp\aicentricuniv\cha-regulation-app
python parse_xml_to_json.py
```
결과: `data/regulations.json` 생성 (136개 규정 통합 데이터)

### 3단계: GitHub 저장소 생성 & 업로드
1. https://github.com/new 에서 새 저장소 생성 (Private 가능)
2. 아래 파일들을 업로드:
   - `app.py`
   - `requirements.txt`
   - `.streamlit/config.toml`
   - `data/regulations.json`

### 4단계: Streamlit Cloud 배포
1. https://share.streamlit.io 접속 (GitHub 계정으로 로그인)
2. **New app** 클릭
3. 저장소 선택 → Main file: `app.py`
4. **Advanced settings → Secrets** 에 아래 입력:
   ```toml
   OPENAI_API_KEY = "sk-여기에-API키-입력"
   ```
5. **Deploy** 클릭

### 5단계: 접속
배포 완료 후 URL 생성:
```
https://[앱이름].streamlit.app
```

## 🔑 OpenAI API 키 발급
1. https://platform.openai.com 접속
2. API Keys → Create new secret key
3. 키를 복사하여 Streamlit Secrets에 입력

## 💰 예상 비용
- **gpt-4o-mini**: 검색 1회당 약 $0.001 (거의 무료)
- **gpt-4o** (고급 분석): 검색 1회당 약 $0.01~0.03
- Streamlit Cloud: 무료 (Public 저장소) 또는 Pro 플랜

## 🔧 주요 기능
| 기능 | 설명 |
|------|------|
| 규정 검색 | 키워드 검색 + GPT 분석 |
| 개정 도우미 | 아이디어 → 관련 규정 → 신구대조문 자동 생성 |
| 규정 Q&A | 특정 규정 선택 후 자유 질의응답 |
| 현황 대시보드 | 전체 규정 통계 및 목록 |

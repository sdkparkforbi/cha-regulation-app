# -*- coding: utf-8 -*-
"""
CHA 규정 혁신 어시스턴트 - Streamlit App
GPT API를 사용한 실제 규정 검색·분석·개정안 생성 도구
"""

import json
import os
import re
import streamlit as st
from openai import OpenAI
from hwpml_exporter import HwpmlExporter

# ============================================================
# 설정
# ============================================================
st.set_page_config(
    page_title="CHA 규정 혁신 어시스턴트",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# OpenAI 클라이언트
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY", "")))

# GPT 모델 설정
GPT_MODEL = "gpt-4o-mini"  # 비용 효율적. 필요 시 "gpt-4o"로 변경


# ============================================================
# 데이터 로드
# ============================================================
@st.cache_data
def load_regulations():
    """regulations.json 로드"""
    data_path = os.path.join(os.path.dirname(__file__), "data", "regulations.json")
    if not os.path.exists(data_path):
        st.error(f"❌ 규정 데이터 파일이 없습니다: {data_path}")
        st.info("parse_xml_to_json.py를 실행하여 data/regulations.json을 생성해 주세요.")
        st.stop()

    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def build_search_index(regulations):
    """키워드 검색용 인덱스 생성"""
    index = []
    for reg in regulations:
        entry = {
            "id": reg["id"],
            "name": reg["name"],
            "text_lower": reg["full_text"].lower(),
            "article_count": reg["article_count"],
            "char_count": reg["char_count"],
        }
        index.append(entry)
    return index


def keyword_search(query, index, regulations, top_k=10):
    """키워드 기반 규정 검색"""
    query_words = query.lower().split()
    results = []

    for i, entry in enumerate(index):
        score = 0
        for word in query_words:
            count = entry["text_lower"].count(word)
            if count > 0:
                score += count
                # 규정명에 포함되면 가중치
                if word in entry["name"].lower():
                    score += 10

        if score > 0:
            results.append({
                "regulation": regulations[i],
                "score": score,
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def find_relevant_articles(regulation, query):
    """특정 규정 내에서 관련 조문 찾기"""
    query_words = query.lower().split()
    relevant = []
    for article in regulation.get("articles", []):
        content_lower = article["content"].lower()
        score = sum(content_lower.count(w) for w in query_words)
        if score > 0:
            relevant.append({**article, "score": score})

    relevant.sort(key=lambda x: x["score"], reverse=True)
    return relevant[:10]


# ============================================================
# GPT API 호출
# ============================================================
def gpt_analyze_regulations(query, search_results):
    """GPT로 검색 결과 분석"""
    # 검색된 규정 요약 (토큰 절약을 위해 조문 제목만)
    reg_summaries = []
    for r in search_results[:5]:
        reg = r["regulation"]
        articles_summary = ", ".join(
            f'{a["number"]} ({a["title"]})'
            for a in reg.get("articles", [])[:20]
        )
        reg_summaries.append(
            f"[{reg['id']}] {reg['name']} — 조문: {articles_summary}"
        )

    context = "\n".join(reg_summaries)

    response = client.chat.completions.create(
        model=GPT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "당신은 차의과학대학교의 규정 전문가입니다. "
                    "대학 규정에 대한 검색 결과를 분석하여 사용자의 질문에 정확히 답변하세요. "
                    "답변은 한국어로, 구체적 조문 번호를 인용하며 작성하세요."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"질문: {query}\n\n"
                    f"검색된 규정:\n{context}\n\n"
                    f"위 규정을 바탕으로 질문에 답변해 주세요. "
                    f"관련 규정명과 조문 번호를 구체적으로 언급하고, "
                    f"개정이 필요한 부분이 있다면 제안해 주세요."
                ),
            },
        ],
        temperature=0.3,
        max_tokens=1500,
    )
    return response.choices[0].message.content


def gpt_draft_amendment(regulation, articles, idea):
    """GPT로 개정안 초안 생성"""
    # 관련 조문 전문 전달 (토큰 제한 고려하여 상위 5개)
    articles_text = "\n\n".join(
        f"[{a['number']} ({a['title']})]\n{a['content']}"
        for a in articles[:5]
    )

    response = client.chat.completions.create(
        model=GPT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "당신은 차의과학대학교 규정 개정 전문가입니다. "
                    "AI중심대학 사업 추진을 위한 규정 개정안을 작성합니다. "
                    "신구대조문 형식(현행 → 개정안)으로 작성하되, "
                    "법률 용어를 정확하게 사용하고, 부칙(경과규정)도 포함하세요."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"규정명: {regulation['name']}\n\n"
                    f"혁신 아이디어: {idea}\n\n"
                    f"관련 현행 조문:\n{articles_text}\n\n"
                    f"위 조문을 바탕으로 신구대조문 형식의 개정안 초안을 작성해 주세요.\n"
                    f"형식:\n"
                    f"## 신구대조문\n"
                    f"| 현행 | 개정안 |\n"
                    f"각 변경 항목별로 작성하고, 마지막에 부칙(경과규정)을 추가하세요."
                ),
            },
        ],
        temperature=0.4,
        max_tokens=2000,
    )
    return response.choices[0].message.content


def gpt_regulation_chat(query, regulation, chat_history):
    """특정 규정에 대한 자유 질의응답"""
    # 규정 전문이 너무 길면 잘라서 전달
    full_text = regulation["full_text"]
    if len(full_text) > 8000:
        full_text = full_text[:8000] + "\n...(이하 생략)"

    messages = [
        {
            "role": "system",
            "content": (
                f"당신은 차의과학대학교 '{regulation['name']}' 전문가입니다. "
                f"아래는 해당 규정의 전문입니다. 이를 바탕으로 질문에 정확히 답변하세요.\n\n"
                f"---\n{full_text}\n---"
            ),
        },
    ]

    # 대화 히스토리 추가
    for msg in chat_history[-6:]:  # 최근 6개 메시지
        messages.append(msg)

    messages.append({"role": "user", "content": query})

    response = client.chat.completions.create(
        model=GPT_MODEL,
        messages=messages,
        temperature=0.3,
        max_tokens=1500,
    )
    return response.choices[0].message.content


# ============================================================
# UI 스타일
# ============================================================
def apply_custom_css():
    st.markdown("""
    <style>
        @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
        
        .stApp { font-family: 'Pretendard', sans-serif; }
        
        .main-header {
            background: linear-gradient(135deg, #0a3327, #0F4C3A, #1a6b4a);
            padding: 24px 32px;
            border-radius: 16px;
            margin-bottom: 24px;
            color: white;
        }
        .main-header h1 { color: white; font-size: 26px; margin: 0; }
        .main-header p { color: rgba(255,255,255,0.6); font-size: 13px; margin: 4px 0 0; }
        
        .stat-card {
            background: white;
            border: 1px solid #e8e8e8;
            border-radius: 12px;
            padding: 16px 20px;
            text-align: center;
        }
        .stat-card .number { font-size: 28px; font-weight: 800; color: #0F4C3A; }
        .stat-card .label { font-size: 12px; color: #888; margin-top: 4px; }
        
        .reg-card {
            background: white;
            border: 1px solid #e8e8e8;
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 10px;
            transition: all 0.2s;
        }
        .reg-card:hover { border-color: #0F4C3A; box-shadow: 0 2px 12px rgba(15,76,58,0.1); }
        
        .article-box {
            background: #f8faf9;
            border-left: 3px solid #0F4C3A;
            padding: 12px 16px;
            margin: 8px 0;
            border-radius: 0 8px 8px 0;
            font-size: 14px;
            line-height: 1.8;
        }
        
        div[data-testid="stSidebar"] {
            background: #f7faf8;
        }
    </style>
    """, unsafe_allow_html=True)


# ============================================================
# 페이지: 규정 검색
# ============================================================
def page_search(regulations, search_index):
    st.markdown("### 🔍 규정 검색")
    st.caption("키워드로 136개 규정을 검색하고, GPT가 관련 조문을 분석합니다.")

    query = st.text_input(
        "검색어를 입력하세요",
        placeholder="예: AI 교육과정, 연구비 간접비, 교원 임용, 휴학 복학...",
        label_visibility="collapsed",
    )

    col1, col2 = st.columns([3, 1])
    with col2:
        use_gpt = st.toggle("GPT 분석", value=True, help="GPT로 검색 결과를 분석합니다")

    if query:
        results = keyword_search(query, search_index, regulations)

        if not results:
            st.warning("검색 결과가 없습니다. 다른 키워드로 시도해 보세요.")
            return

        st.markdown(f"**📎 {len(results)}건의 관련 규정**")

        # GPT 분석
        if use_gpt and results:
            with st.spinner("🤖 GPT가 규정을 분석하고 있습니다..."):
                try:
                    analysis = gpt_analyze_regulations(query, results)
                    with st.expander("🤖 GPT 분석 결과", expanded=True):
                        st.markdown(analysis)
                        
                        # XML 다운로드 버튼
                        exporter = HwpmlExporter()
                        reg_info = [
                            {"name": r["regulation"]["name"], 
                             "article_count": r["regulation"]["article_count"],
                             "score": r["score"]}
                            for r in results[:5]
                        ]
                        xml_bytes = exporter.create_analysis_doc(
                            title=f"규정 분석: {query}",
                            query=query,
                            analysis_text=analysis,
                            regulations=reg_info,
                        )
                        st.download_button(
                            "📥 분석 결과 XML 다운로드 (한/글 호환)",
                            data=xml_bytes,
                            file_name=f"규정분석_{query[:20]}.xml",
                            mime="application/xml",
                        )
                except Exception as e:
                    st.error(f"GPT 분석 실패: {e}")

        # 검색 결과 목록
        for r in results:
            reg = r["regulation"]
            score = r["score"]

            with st.expander(f"📄 {reg['name']}  (관련도: {score}점 · {reg['article_count']}개 조문)"):
                # 관련 조문 하이라이트
                relevant_articles = find_relevant_articles(reg, query)
                if relevant_articles:
                    st.markdown("**관련 조문:**")
                    for article in relevant_articles[:5]:
                        st.markdown(
                            f'<div class="article-box">'
                            f'<strong>{article["number"]} ({article["title"]})</strong><br/>'
                            f'{article["content"][:300]}{"..." if len(article["content"]) > 300 else ""}'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                else:
                    st.caption("조문 단위 파싱 결과가 없습니다. 전체 텍스트에서 검색되었습니다.")

                # 규정 전문 보기
                if st.button(f"전문 보기", key=f"full_{reg['id']}"):
                    st.text_area(
                        "규정 전문",
                        reg["full_text"],
                        height=400,
                        key=f"text_{reg['id']}",
                    )


# ============================================================
# 페이지: 규정 개정 도우미
# ============================================================
def page_amendment(regulations, search_index):
    st.markdown("### 📝 규정 개정 도우미")
    st.caption("혁신 아이디어를 입력하면 관련 규정을 찾고 개정안 초안을 GPT가 생성합니다.")

    # Step 1: 아이디어 입력
    idea = st.text_area(
        "혁신 아이디어",
        placeholder="예: AI 기반 의료데이터 분석 교육과정을 신설하여 학부-대학원 연계 Fast Track을 만들고 싶습니다.",
        height=100,
    )

    example_ideas = [
        "AI 기반 의료데이터 교육과정 신설",
        "바이오헬스케어 산학협력 인턴십 도입",
        "비전임교원 AI 연구 참여 확대",
    ]
    st.caption("예시: " + " · ".join(f"`{e}`" for e in example_ideas))

    if not idea:
        return

    # Step 2: 관련 규정 검색
    results = keyword_search(idea, search_index, regulations)

    if not results:
        st.warning("관련 규정을 찾지 못했습니다.")
        return

    st.markdown(f"**📎 관련 규정 {len(results)}건**")

    # 규정 선택
    reg_options = {
        f"{r['regulation']['name']} (관련도: {r['score']}점)": i
        for i, r in enumerate(results)
    }
    selected_names = st.multiselect(
        "개정 대상 규정을 선택하세요",
        options=list(reg_options.keys()),
        default=[list(reg_options.keys())[0]] if reg_options else [],
    )

    if not selected_names:
        return

    # Step 3: 개정안 생성
    if st.button("📄 개정안 초안 생성", type="primary", use_container_width=True):
        for name in selected_names:
            idx = reg_options[name]
            reg = results[idx]["regulation"]
            relevant_articles = find_relevant_articles(reg, idea)

            with st.spinner(f"🤖 '{reg['name']}' 개정안 생성 중..."):
                try:
                    draft = gpt_draft_amendment(reg, relevant_articles, idea)
                    st.markdown(f"#### 📄 {reg['name']} 개정안")
                    st.markdown(draft)
                    
                    # XML 다운로드 버튼
                    exporter = HwpmlExporter()
                    amendment_rows = exporter.parse_gpt_amendment(draft)
                    if not amendment_rows:
                        amendment_rows = [{"current": "(GPT 생성 텍스트)", "revised": draft}]
                    
                    metadata = {
                        "background": f"CHA대학교 AI중심대학 사업 추진에 따른 {reg['name']} 정비",
                        "core_content": idea[:100],
                        "related_regs": ", ".join(n.split(" (")[0] for n in selected_names),
                        "department": reg.get("dept", ""),
                        "cooperating": "교무처, 정보전산원, 산학협력단",
                        "schedule": "2026.03 ~ 2026.06 (약 12주)",
                        "target": "2026년 2학기부터 적용",
                    }
                    xml_bytes = exporter.create_amendment_doc(
                        title=f"{reg['name']} 개정안",
                        amendment_rows=amendment_rows,
                        metadata=metadata,
                    )
                    st.download_button(
                        f"📥 {reg['name']} 개정안 XML 다운로드 (한/글 호환)",
                        data=xml_bytes,
                        file_name=f"{reg['name']}_개정안.xml",
                        mime="application/xml",
                        key=f"dl_{reg['id']}",
                    )
                    st.divider()
                except Exception as e:
                    st.error(f"개정안 생성 실패 ({reg['name']}): {e}")


# ============================================================
# 페이지: 규정 Q&A (채팅)
# ============================================================
def page_chat(regulations):
    st.markdown("### 💬 규정 Q&A")
    st.caption("특정 규정을 선택하고 자유롭게 질문하세요. GPT가 규정 전문을 바탕으로 답변합니다.")

    # 규정 선택
    reg_names = {reg["name"]: i for i, reg in enumerate(regulations)}
    selected_name = st.selectbox("규정 선택", options=list(reg_names.keys()))

    if not selected_name:
        return

    reg = regulations[reg_names[selected_name]]
    st.caption(f"📊 {reg['article_count']}개 조문 · {reg['char_count']:,}자")

    # 채팅 히스토리 초기화
    chat_key = f"chat_{reg['id']}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    # 채팅 히스토리 표시
    for msg in st.session_state[chat_key]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 질문 입력
    if prompt := st.chat_input(f"'{selected_name}'에 대해 질문하세요..."):
        # 사용자 메시지 표시
        with st.chat_message("user"):
            st.markdown(prompt)

        # GPT 응답
        with st.chat_message("assistant"):
            with st.spinner("답변 생성 중..."):
                try:
                    response = gpt_regulation_chat(
                        prompt, reg, st.session_state[chat_key]
                    )
                    st.markdown(response)
                except Exception as e:
                    response = f"❌ 오류: {e}"
                    st.error(response)

        # 히스토리 저장
        st.session_state[chat_key].append({"role": "user", "content": prompt})
        st.session_state[chat_key].append({"role": "assistant", "content": response})

    # Q&A 기록 다운로드
    if st.session_state.get(chat_key):
        qa_pairs = []
        msgs = st.session_state[chat_key]
        for i in range(0, len(msgs) - 1, 2):
            if msgs[i]["role"] == "user" and msgs[i + 1]["role"] == "assistant":
                qa_pairs.append({
                    "question": msgs[i]["content"],
                    "answer": msgs[i + 1]["content"],
                })
        if qa_pairs:
            exporter = HwpmlExporter()
            xml_bytes = exporter.create_qa_doc(selected_name, qa_pairs)
            st.download_button(
                "📥 Q&A 기록 XML 다운로드 (한/글 호환)",
                data=xml_bytes,
                file_name=f"{selected_name}_QA기록.xml",
                mime="application/xml",
            )


# ============================================================
# 페이지: 규정 현황 대시보드
# ============================================================
def page_dashboard(regulations):
    st.markdown("### 📊 규정 현황 대시보드")

    # 통계 카드
    total_regs = len(regulations)
    total_articles = sum(r["article_count"] for r in regulations)
    total_chars = sum(r["char_count"] for r in regulations)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("전체 규정 수", f"{total_regs}개")
    with c2:
        st.metric("총 조문 수", f"{total_articles:,}개")
    with c3:
        st.metric("총 텍스트량", f"{total_chars:,}자")

    st.divider()

    # 규정 목록 테이블
    st.markdown("**📋 전체 규정 목록**")
    table_data = []
    for reg in regulations:
        table_data.append({
            "ID": reg["id"],
            "규정명": reg["name"][:40],
            "조문 수": reg["article_count"],
            "텍스트(자)": f"{reg['char_count']:,}",
        })

    st.dataframe(
        table_data,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# 메인
# ============================================================
def main():
    apply_custom_css()

    # 헤더
    st.markdown(
        '<div class="main-header">'
        "<h1>🏛️ CHA 규정 혁신 어시스턴트</h1>"
        "<p>Regulation Innovation Assistant · GPT 기반 규정 검색·분석·개정 도구</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # API 키 확인
    if not client.api_key:
        st.error("⚠️ OpenAI API 키가 설정되지 않았습니다.")
        st.markdown(
            "Streamlit Cloud: **Settings → Secrets**에 아래를 추가하세요:\n"
            "```toml\n"
            'OPENAI_API_KEY = "sk-..."\n'
            "```"
        )
        st.stop()

    # 데이터 로드
    regulations = load_regulations()
    search_index = build_search_index(regulations)

    # 사이드바 네비게이션
    with st.sidebar:
        st.markdown("### 메뉴")
        page = st.radio(
            "기능 선택",
            ["🔍 규정 검색", "📝 개정 도우미", "💬 규정 Q&A", "📊 현황 대시보드"],
            label_visibility="collapsed",
        )

        st.divider()
        st.caption(f"📁 {len(regulations)}개 규정 로드됨")
        st.caption("🤖 GPT: " + GPT_MODEL)
        st.caption("v2.0 · 피터(Peter) 제작")

    # 페이지 라우팅
    if page == "🔍 규정 검색":
        page_search(regulations, search_index)
    elif page == "📝 개정 도우미":
        page_amendment(regulations, search_index)
    elif page == "💬 규정 Q&A":
        page_chat(regulations)
    elif page == "📊 현황 대시보드":
        page_dashboard(regulations)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
[Step 1] 136개 XML 규정 파일 → regulations.json 변환
실행 위치: Dave의 Windows PC
실행 명령: python parse_xml_to_json.py

이 스크립트를 한 번만 실행하면 regulations.json이 생성됩니다.
생성된 JSON 파일을 GitHub 저장소에 포함시켜 Streamlit Cloud에서 사용합니다.
"""

import os
import re
import json
import sys
from pathlib import Path

# ============================================================
# 경로 설정
# ============================================================
XML_DIR = r"D:\Temp\aicentricuniv\cha_regulations\xml"
OUTPUT_FILE = r"D:\Temp\aicentricuniv\cha-regulation-app\regulations.json"


def extract_text_from_xml(xml_path):
    """HWPML XML에서 텍스트를 추출하여 문단 리스트로 반환"""
    with open(xml_path, "r", encoding="utf-8") as f:
        content = f.read()

    # <CHAR> 태그 안의 텍스트 추출
    chars = re.findall(r"<CHAR>(.*?)</CHAR>", content, re.DOTALL)

    # <P> 태그 단위로 문단 구분 시도
    # HWPML에서 각 <P>는 하나의 문단
    paragraphs = []
    # 단순 접근: </P>를 기준으로 CHAR들을 그룹화
    p_blocks = re.findall(r"<P[^>]*>(.*?)</P>", content, re.DOTALL)

    for block in p_blocks:
        block_chars = re.findall(r"<CHAR>(.*?)</CHAR>", block, re.DOTALL)
        if block_chars:
            text = " ".join(c.strip() for c in block_chars if c.strip())
            if text:
                paragraphs.append(text)

    # 만약 P 블록 파싱 실패 시 CHAR 전체를 사용
    if not paragraphs and chars:
        paragraphs = [c.strip() for c in chars if c.strip()]

    return paragraphs


def extract_articles(paragraphs):
    """문단 리스트에서 조문(제X조) 단위로 구조화"""
    articles = []
    current_article = None
    current_text = []

    article_pattern = re.compile(r"^(제\d+조(?:의\d+)?)\s*[\(（](.+?)[\)）]")

    for para in paragraphs:
        match = article_pattern.match(para)
        if match:
            # 이전 조문 저장
            if current_article:
                current_article["content"] = "\n".join(current_text)
                articles.append(current_article)

            current_article = {
                "number": match.group(1),
                "title": match.group(2),
                "content": "",
            }
            current_text = [para]
        elif current_article:
            current_text.append(para)

    # 마지막 조문 저장
    if current_article:
        current_article["content"] = "\n".join(current_text)
        articles.append(current_article)

    return articles


def guess_regulation_name(filename, paragraphs):
    """파일명 또는 첫 문단에서 규정명 추출"""
    # 파일명에서 추출 시도
    name = Path(filename).stem
    # 번호 접두사 제거 (예: "2-1__차의과학대학교_학칙_2025_09_01__")
    name = re.sub(r"^\d+[-_]\d*[-_]*", "", name)
    name = name.replace("_", " ").strip()

    # 첫 몇 문단에서 규정명 패턴 찾기
    for para in paragraphs[:10]:
        if re.search(r"(규정|학칙|내규|지침|요강|세칙)", para) and len(para) < 50:
            return para.strip()

    return name if name else filename


def parse_all_xml(xml_dir):
    """전체 XML 파일을 파싱하여 규정 데이터 생성"""
    xml_files = sorted([
        f for f in os.listdir(xml_dir)
        if f.lower().endswith(".xml")
    ])

    if not xml_files:
        print(f"[오류] XML 파일이 없습니다: {xml_dir}")
        sys.exit(1)

    regulations = []
    total = len(xml_files)

    print(f"{'=' * 60}")
    print(f"  XML → JSON 변환 시작")
    print(f"  소스: {xml_dir}")
    print(f"  파일 수: {total}개")
    print(f"{'=' * 60}\n")

    for i, fname in enumerate(xml_files, 1):
        filepath = os.path.join(xml_dir, fname)
        try:
            paragraphs = extract_text_from_xml(filepath)
            articles = extract_articles(paragraphs)
            full_text = "\n".join(paragraphs)
            reg_name = guess_regulation_name(fname, paragraphs)

            reg = {
                "id": f"REG-{i:03d}",
                "filename": fname,
                "name": reg_name,
                "full_text": full_text,
                "articles": articles,
                "article_count": len(articles),
                "char_count": len(full_text),
            }
            regulations.append(reg)
            print(f"  [{i:3d}/{total}] ✓ {reg_name[:40]:<40s} ({len(articles)}개 조문, {len(full_text):,}자)")

        except Exception as e:
            print(f"  [{i:3d}/{total}] ✗ {fname} - {e}")

    return regulations


def main():
    # XML 파싱
    regulations = parse_all_xml(XML_DIR)

    # JSON 저장
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(regulations, f, ensure_ascii=False, indent=2)

    # 통계 출력
    total_articles = sum(r["article_count"] for r in regulations)
    total_chars = sum(r["char_count"] for r in regulations)

    print(f"\n{'=' * 60}")
    print(f"  변환 완료!")
    print(f"  규정 수: {len(regulations)}개")
    print(f"  총 조문 수: {total_articles:,}개")
    print(f"  총 텍스트: {total_chars:,}자")
    print(f"  저장 위치: {OUTPUT_FILE}")
    print(f"  파일 크기: {os.path.getsize(OUTPUT_FILE) / 1024 / 1024:.1f}MB")
    print(f"{'=' * 60}")

    # 미리보기
    print(f"\n  [규정 목록 미리보기]")
    for reg in regulations[:10]:
        print(f"    {reg['id']} | {reg['name'][:35]:<35s} | {reg['article_count']:3d}조 | {reg['char_count']:,}자")
    if len(regulations) > 10:
        print(f"    ... 외 {len(regulations) - 10}개")

    print(f"\n  다음 단계: regulations.json을 GitHub 저장소의 data/ 폴더에 넣으세요.")
    input("\nEnter 키를 누르면 종료합니다...")


if __name__ == "__main__":
    main()

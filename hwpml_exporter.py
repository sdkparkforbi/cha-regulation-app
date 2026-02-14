# -*- coding: utf-8 -*-
"""
hwpml_exporter.py — HWPML XML 생성 모듈
Streamlit 앱의 출력물(개정안, 분석 결과 등)을 한/글에서 열 수 있는 HWPML XML로 변환

사용법:
  from hwpml_exporter import HwpmlExporter
  exporter = HwpmlExporter()
  xml_bytes = exporter.create_amendment_doc(title, rows, metadata)
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
import re


class HwpmlExporter:
    """HWPML 2.x XML 문서 생성기"""

    # ── 기본 스타일 ID ──
    STYLE_NORMAL = "0"
    STYLE_HEADING1 = "1"
    STYLE_HEADING2 = "2"

    # ── 폰트 설정 ──
    FONT_BODY = "맑은 고딕"
    FONT_TITLE = "맑은 고딕"
    FONT_SIZE_BODY = 1000  # 10pt (단위: 1/100 pt)
    FONT_SIZE_TITLE = 1600
    FONT_SIZE_HEADING = 1300
    FONT_SIZE_SMALL = 900

    def __init__(self):
        self.para_id = 0

    def _new_para_id(self):
        self.para_id += 1
        return str(self.para_id)

    # ================================================================
    # HWPML 문서 뼈대
    # ================================================================
    def _build_hwpml_root(self):
        """HWPML 최상위 구조 생성"""
        root = ET.Element("HWPML")
        root.set("Version", "2.91")
        root.set("SubVersion", "10.0.0.0")
        root.set("Style", "export")
        return root

    def _build_head(self, root, title="문서"):
        """HEAD 섹션: 문서 요약, 폰트, 스타일 정의"""
        head = ET.SubElement(root, "HEAD")
        head.set("SecCnt", "1")

        # 문서 요약
        summary = ET.SubElement(head, "DOCSUMMARY")
        ET.SubElement(summary, "TITLE").text = title
        ET.SubElement(summary, "AUTHOR").text = "CHA 규정 혁신 어시스턴트"
        ET.SubElement(summary, "DATE").text = datetime.now().strftime("%Y년 %m월 %d일")

        # 매핑 테이블
        mapping = ET.SubElement(head, "MAPPINGTABLE")

        # 폰트 정의
        facenames = ET.SubElement(mapping, "FACENAMELIST")
        for lang in ["Hangul", "Latin", "Hanja", "Symbol"]:
            fl = ET.SubElement(facenames, "FONTFACE")
            fl.set("Lang", lang)
            fl.set("Count", "2")
            for fid, fname in enumerate([self.FONT_BODY, self.FONT_TITLE]):
                font = ET.SubElement(fl, "FONT")
                font.set("Id", str(fid))
                font.set("Name", fname)
                font.set("Type", "ttf")

        # 글자 모양 (CharShape)
        charshapes = ET.SubElement(mapping, "CHARSHAPELIST")

        # CS0: 본문 (10pt)
        cs0 = ET.SubElement(charshapes, "CHARSHAPE")
        cs0.set("Id", "0")
        fh0 = ET.SubElement(cs0, "FONTID")
        fh0.set("Hangul", "0"); fh0.set("Latin", "0"); fh0.set("Hanja", "0")
        fr0 = ET.SubElement(cs0, "RATIO")
        fr0.set("Hangul", "100"); fr0.set("Latin", "100"); fr0.set("Hanja", "100")
        fs0 = ET.SubElement(cs0, "SIZE")
        fs0.set("Hangul", str(self.FONT_SIZE_BODY))
        fs0.set("Latin", str(self.FONT_SIZE_BODY))
        fs0.set("Hanja", str(self.FONT_SIZE_BODY))

        # CS1: 제목 (16pt, Bold)
        cs1 = ET.SubElement(charshapes, "CHARSHAPE")
        cs1.set("Id", "1")
        cs1.set("Bold", "true")
        fh1 = ET.SubElement(cs1, "FONTID")
        fh1.set("Hangul", "1"); fh1.set("Latin", "1"); fh1.set("Hanja", "1")
        fr1 = ET.SubElement(cs1, "RATIO")
        fr1.set("Hangul", "100"); fr1.set("Latin", "100"); fr1.set("Hanja", "100")
        fs1 = ET.SubElement(cs1, "SIZE")
        fs1.set("Hangul", str(self.FONT_SIZE_TITLE))
        fs1.set("Latin", str(self.FONT_SIZE_TITLE))
        fs1.set("Hanja", str(self.FONT_SIZE_TITLE))

        # CS2: 소제목 (13pt, Bold)
        cs2 = ET.SubElement(charshapes, "CHARSHAPE")
        cs2.set("Id", "2")
        cs2.set("Bold", "true")
        fh2 = ET.SubElement(cs2, "FONTID")
        fh2.set("Hangul", "0"); fh2.set("Latin", "0"); fh2.set("Hanja", "0")
        fr2 = ET.SubElement(cs2, "RATIO")
        fr2.set("Hangul", "100"); fr2.set("Latin", "100"); fr2.set("Hanja", "100")
        fs2 = ET.SubElement(cs2, "SIZE")
        fs2.set("Hangul", str(self.FONT_SIZE_HEADING))
        fs2.set("Latin", str(self.FONT_SIZE_HEADING))
        fs2.set("Hanja", str(self.FONT_SIZE_HEADING))

        # CS3: 테이블 헤더 (10pt, Bold)
        cs3 = ET.SubElement(charshapes, "CHARSHAPE")
        cs3.set("Id", "3")
        cs3.set("Bold", "true")
        fh3 = ET.SubElement(cs3, "FONTID")
        fh3.set("Hangul", "0"); fh3.set("Latin", "0"); fh3.set("Hanja", "0")
        fr3 = ET.SubElement(cs3, "RATIO")
        fr3.set("Hangul", "100"); fr3.set("Latin", "100"); fr3.set("Hanja", "100")
        fs3 = ET.SubElement(cs3, "SIZE")
        fs3.set("Hangul", str(self.FONT_SIZE_BODY))
        fs3.set("Latin", str(self.FONT_SIZE_BODY))
        fs3.set("Hanja", str(self.FONT_SIZE_BODY))

        # CS4: 작은 글씨 (9pt)
        cs4 = ET.SubElement(charshapes, "CHARSHAPE")
        cs4.set("Id", "4")
        fh4 = ET.SubElement(cs4, "FONTID")
        fh4.set("Hangul", "0"); fh4.set("Latin", "0"); fh4.set("Hanja", "0")
        fr4 = ET.SubElement(cs4, "RATIO")
        fr4.set("Hangul", "100"); fr4.set("Latin", "100"); fr4.set("Hanja", "100")
        fs4 = ET.SubElement(cs4, "SIZE")
        fs4.set("Hangul", str(self.FONT_SIZE_SMALL))
        fs4.set("Latin", str(self.FONT_SIZE_SMALL))
        fs4.set("Hanja", str(self.FONT_SIZE_SMALL))

        # 문단 모양 (ParaShape)
        parashapes = ET.SubElement(mapping, "PARASHAPELIST")
        # PS0: 본문 (줄간격 160%)
        ps0 = ET.SubElement(parashapes, "PARASHAPE")
        ps0.set("Id", "0")
        ls0 = ET.SubElement(ps0, "LINESPACING")
        ls0.set("Type", "Percent")
        ls0.set("Value", "160")
        # PS1: 제목 (줄간격 130%, 아래 여백)
        ps1 = ET.SubElement(parashapes, "PARASHAPE")
        ps1.set("Id", "1")
        ps1.set("Align", "Center")
        ls1 = ET.SubElement(ps1, "LINESPACING")
        ls1.set("Type", "Percent")
        ls1.set("Value", "130")
        mg1 = ET.SubElement(ps1, "MARGIN")
        mg1.set("Bottom", "400")
        # PS2: 소제목
        ps2 = ET.SubElement(parashapes, "PARASHAPE")
        ps2.set("Id", "2")
        ls2 = ET.SubElement(ps2, "LINESPACING")
        ls2.set("Type", "Percent")
        ls2.set("Value", "150")
        mg2 = ET.SubElement(ps2, "MARGIN")
        mg2.set("Top", "300")
        mg2.set("Bottom", "100")

        return head

    # ================================================================
    # 본문 요소 빌더
    # ================================================================
    def _make_paragraph(self, section, text, charshape="0", parashape="0"):
        """일반 문단 생성"""
        p = ET.SubElement(section, "P")
        p.set("ParaShape", parashape)
        p.set("Style", "0")
        t = ET.SubElement(p, "TEXT")
        t.set("CharShape", charshape)
        c = ET.SubElement(t, "CHAR")
        c.text = text
        return p

    def _make_empty_para(self, section):
        """빈 줄"""
        p = ET.SubElement(section, "P")
        p.set("ParaShape", "0")
        p.set("Style", "0")
        t = ET.SubElement(p, "TEXT")
        t.set("CharShape", "0")
        return p

    def _make_table(self, section, headers, rows, col_widths=None):
        """
        테이블 생성
        headers: ["현행", "개정안"] 등
        rows: [["현행 텍스트", "개정안 텍스트"], ...]
        col_widths: [4500, 4500] 등 (단위: 1/100 mm)
        """
        num_cols = len(headers)
        num_rows = len(rows) + 1  # 헤더 포함

        if col_widths is None:
            total_width = 16000  # A4 기준 약 160mm
            col_widths = [total_width // num_cols] * num_cols

        # TABLE 요소
        p_table = ET.SubElement(section, "P")
        p_table.set("ParaShape", "0")
        p_table.set("Style", "0")
        t_wrapper = ET.SubElement(p_table, "TEXT")
        t_wrapper.set("CharShape", "0")

        table = ET.SubElement(t_wrapper, "TABLE")
        table.set("RowCount", str(num_rows))
        table.set("ColCount", str(num_cols))
        table.set("CellSpacing", "0")
        table.set("BorderFill", "1")

        # 헤더 행
        row_el = ET.SubElement(table, "ROW")
        for ci, header in enumerate(headers):
            cell = ET.SubElement(row_el, "CELL")
            cell.set("ColAddr", str(ci))
            cell.set("RowAddr", "0")
            cell.set("ColSpan", "1")
            cell.set("RowSpan", "1")
            cell.set("Width", str(col_widths[ci]))
            cell.set("Header", "true")

            cellbody = ET.SubElement(cell, "PARALIST")
            cp = ET.SubElement(cellbody, "P")
            cp.set("ParaShape", "0")
            cp.set("Style", "0")
            ct = ET.SubElement(cp, "TEXT")
            ct.set("CharShape", "3")  # Bold
            cc = ET.SubElement(ct, "CHAR")
            cc.text = header

        # 데이터 행
        for ri, row_data in enumerate(rows):
            row_el = ET.SubElement(table, "ROW")
            for ci, cell_text in enumerate(row_data):
                cell = ET.SubElement(row_el, "CELL")
                cell.set("ColAddr", str(ci))
                cell.set("RowAddr", str(ri + 1))
                cell.set("ColSpan", "1")
                cell.set("RowSpan", "1")
                cell.set("Width", str(col_widths[ci]))

                cellbody = ET.SubElement(cell, "PARALIST")

                # 셀 내 여러 줄 지원
                lines = cell_text.split("\n") if cell_text else [""]
                for line in lines:
                    cp = ET.SubElement(cellbody, "P")
                    cp.set("ParaShape", "0")
                    cp.set("Style", "0")
                    ct = ET.SubElement(cp, "TEXT")
                    ct.set("CharShape", "0")
                    cc = ET.SubElement(ct, "CHAR")
                    cc.text = line

        return table

    # ================================================================
    # 문서 유형별 생성기
    # ================================================================
    def create_amendment_doc(self, title, amendment_rows, metadata=None):
        """
        신구대조문 문서 생성

        Args:
            title: "학칙 개정안" 등
            amendment_rows: [
                {"current": "현행 조문", "revised": "개정안 조문"},
                ...
            ]
            metadata: {
                "background": "개정 배경",
                "department": "주관 부서",
                "schedule": "예상 일정",
                ...
            }

        Returns:
            bytes: HWPML XML (UTF-8 인코딩)
        """
        self.para_id = 0
        root = self._build_hwpml_root()
        self._build_head(root, title=title)

        body = ET.SubElement(root, "BODY")
        section = ET.SubElement(body, "SECTION")
        section.set("Id", "0")

        # ── 제목 ──
        self._make_paragraph(section, title, charshape="1", parashape="1")

        # ── 문서 정보 ──
        today = datetime.now().strftime("%Y. %m. %d.")
        self._make_paragraph(section, f"작성일: {today}", charshape="4", parashape="0")
        self._make_paragraph(section, "작성: CHA 규정 혁신 어시스턴트 (AI 자동 생성 초안)", charshape="4", parashape="0")
        self._make_empty_para(section)

        # ── 개정 기획안 요약 ──
        if metadata:
            self._make_paragraph(section, "■ 개정 기획안 요약", charshape="2", parashape="2")

            summary_rows = []
            field_map = [
                ("background", "개정 배경"),
                ("core_content", "핵심 내용"),
                ("related_regs", "관련 규정"),
                ("department", "주관 부서"),
                ("cooperating", "협조 부서"),
                ("schedule", "예상 일정"),
                ("target", "시행 목표"),
            ]
            for key, label in field_map:
                if key in metadata and metadata[key]:
                    summary_rows.append([label, metadata[key]])

            if summary_rows:
                self._make_table(
                    section,
                    headers=["항목", "내용"],
                    rows=summary_rows,
                    col_widths=[3000, 13000],
                )
                self._make_empty_para(section)

        # ── 신구대조문 ──
        self._make_paragraph(section, "■ 신구대조문", charshape="2", parashape="2")

        table_rows = []
        for row in amendment_rows:
            current = row.get("current", "")
            revised = row.get("revised", "")
            table_rows.append([current, revised])

        self._make_table(
            section,
            headers=["현    행", "개  정  안"],
            rows=table_rows,
            col_widths=[8000, 8000],
        )
        self._make_empty_para(section)

        # ── 부칙 ──
        self._make_paragraph(section, "■ 부칙", charshape="2", parashape="2")
        self._make_paragraph(section, "제1조 (시행일) 이 규정은 공포한 날부터 시행한다.")
        self._make_paragraph(
            section,
            "제2조 (경과조치) 이 규정 시행 당시 종전의 규정에 따라 "
            "재학 중인 학생에 대하여는 종전의 규정을 적용한다.",
        )
        self._make_empty_para(section)

        # ── 안내문 ──
        self._make_paragraph(
            section,
            "※ 이 문서는 AI가 자동 생성한 초안입니다. 반드시 법무 검토 후 사용하시기 바랍니다.",
            charshape="4",
        )

        return self._to_xml_bytes(root)

    def create_analysis_doc(self, title, query, analysis_text, regulations=None):
        """
        규정 분석 보고서 생성

        Args:
            title: "AI 교육과정 관련 규정 분석"
            query: 사용자 검색어
            analysis_text: GPT 분석 결과 텍스트
            regulations: [{"name": "학칙", "articles": [...]}] 관련 규정 목록

        Returns:
            bytes: HWPML XML
        """
        self.para_id = 0
        root = self._build_hwpml_root()
        self._build_head(root, title=title)

        body = ET.SubElement(root, "BODY")
        section = ET.SubElement(body, "SECTION")
        section.set("Id", "0")

        # 제목
        self._make_paragraph(section, title, charshape="1", parashape="1")

        today = datetime.now().strftime("%Y. %m. %d.")
        self._make_paragraph(section, f"작성일: {today}  |  검색어: {query}", charshape="4")
        self._make_empty_para(section)

        # 분석 결과
        self._make_paragraph(section, "■ AI 분석 결과", charshape="2", parashape="2")

        # Markdown 형식 텍스트를 문단 단위로 분리
        for line in analysis_text.split("\n"):
            line = line.strip()
            if not line:
                self._make_empty_para(section)
            elif line.startswith("##"):
                clean = line.lstrip("#").strip()
                self._make_paragraph(section, clean, charshape="2", parashape="2")
            elif line.startswith("- ") or line.startswith("* "):
                clean = "  · " + line[2:]
                self._make_paragraph(section, clean)
            elif line.startswith("|"):
                # 마크다운 테이블 행은 건너뛰기 (별도 처리 필요)
                continue
            else:
                # Bold 마크다운 제거
                clean = re.sub(r"\*\*(.*?)\*\*", r"\1", line)
                self._make_paragraph(section, clean)

        self._make_empty_para(section)

        # 관련 규정 목록
        if regulations:
            self._make_paragraph(section, "■ 관련 규정 목록", charshape="2", parashape="2")
            reg_rows = []
            for reg in regulations:
                name = reg.get("name", "")
                count = str(reg.get("article_count", ""))
                score = str(reg.get("score", ""))
                reg_rows.append([name, count, score])

            self._make_table(
                section,
                headers=["규정명", "조문 수", "관련도"],
                rows=reg_rows,
                col_widths=[9000, 3000, 4000],
            )

        # 안내문
        self._make_empty_para(section)
        self._make_paragraph(
            section,
            "※ 이 문서는 AI가 자동 생성한 분석 결과입니다. 참고 자료로만 활용하시기 바랍니다.",
            charshape="4",
        )

        return self._to_xml_bytes(root)

    def create_qa_doc(self, regulation_name, qa_pairs):
        """
        Q&A 대화 기록 문서 생성

        Args:
            regulation_name: "학칙"
            qa_pairs: [{"question": "...", "answer": "..."}, ...]

        Returns:
            bytes: HWPML XML
        """
        self.para_id = 0
        title = f"{regulation_name} Q&A 기록"
        root = self._build_hwpml_root()
        self._build_head(root, title=title)

        body = ET.SubElement(root, "BODY")
        section = ET.SubElement(body, "SECTION")
        section.set("Id", "0")

        self._make_paragraph(section, title, charshape="1", parashape="1")

        today = datetime.now().strftime("%Y. %m. %d.")
        self._make_paragraph(section, f"작성일: {today}", charshape="4")
        self._make_empty_para(section)

        for i, qa in enumerate(qa_pairs, 1):
            self._make_paragraph(
                section, f"Q{i}. {qa['question']}", charshape="2", parashape="2"
            )
            for line in qa["answer"].split("\n"):
                line = line.strip()
                if line:
                    clean = re.sub(r"\*\*(.*?)\*\*", r"\1", line)
                    self._make_paragraph(section, clean)
            self._make_empty_para(section)

        self._make_paragraph(
            section,
            "※ AI 생성 답변입니다. 공식 해석은 해당 부서에 확인하시기 바랍니다.",
            charshape="4",
        )

        return self._to_xml_bytes(root)

    # ================================================================
    # 유틸리티
    # ================================================================
    def _to_xml_bytes(self, root):
        """ElementTree → 정리된 XML 바이트열"""
        rough = ET.tostring(root, encoding="unicode", xml_declaration=False)
        # XML 선언 추가 + 줄바꿈 정리
        dom = minidom.parseString(rough)
        pretty = dom.toprettyxml(indent="  ", encoding="UTF-8")
        return pretty

    @staticmethod
    def parse_gpt_amendment(gpt_text):
        """
        GPT가 생성한 마크다운 형식 신구대조문을 파싱

        GPT 출력 예시:
          | 현행 | 개정안 |
          |------|--------|
          | 제1조 ... | 제1조 ... |

        Returns:
            list of {"current": str, "revised": str}
        """
        rows = []
        lines = gpt_text.split("\n")

        for line in lines:
            line = line.strip()
            if not line.startswith("|"):
                continue
            # 구분선 건너뛰기
            if re.match(r"^\|[\s\-:]+\|", line):
                continue
            # 헤더 건너뛰기
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) >= 2:
                current = cells[0].strip()
                revised = cells[1].strip()
                # 헤더행 건너뛰기
                if current in ("현행", "현 행", "現行") or revised in ("개정안", "개정 안", "改正案"):
                    continue
                if current or revised:
                    rows.append({"current": current, "revised": revised})

        # 마크다운 테이블이 아닌 경우 텍스트 블록으로 처리
        if not rows:
            # "현행:" / "개정안:" 패턴 찾기
            current_text = ""
            revised_text = ""
            mode = None
            for line in lines:
                if "현행" in line and (":" in line or "】" in line):
                    mode = "current"
                    continue
                elif "개정" in line and (":" in line or "】" in line):
                    mode = "revised"
                    continue
                if mode == "current":
                    current_text += line + "\n"
                elif mode == "revised":
                    revised_text += line + "\n"

            if current_text or revised_text:
                rows.append({
                    "current": current_text.strip(),
                    "revised": revised_text.strip(),
                })

        return rows

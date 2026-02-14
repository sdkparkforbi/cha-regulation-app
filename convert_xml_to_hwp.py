# -*- coding: utf-8 -*-
"""
[선택사항] XML → HWP 일괄 변환 스크립트
Streamlit 앱에서 다운받은 HWPML XML 파일을 HWP로 변환

실행 환경: Windows + 한/글 설치 필수
실행 명령: python convert_xml_to_hwp.py

사용법:
  1. Streamlit 앱에서 XML 파일 다운로드 → 특정 폴더에 저장
  2. 이 스크립트 실행 → 같은 폴더에 HWP 파일 생성
"""

import os
import sys
import time
import glob

try:
    import win32com.client
except ImportError:
    print("pywin32가 설치되지 않았습니다.")
    print("설치 명령: pip install pywin32")
    sys.exit(1)

# ============================================================
# 경로 설정 (필요 시 수정)
# ============================================================
# XML 파일이 있는 폴더 (다운로드 폴더 등)
XML_DIR = r"D:\Temp\aicentricuniv\regulation_outputs"
# HWP 저장 폴더 (같은 폴더 사용 가능)
HWP_DIR = r"D:\Temp\aicentricuniv\regulation_outputs\hwp"


def convert_single_file(hwp, xml_path, hwp_path):
    """단일 XML → HWP 변환"""
    # HWPML XML로 열기
    hwp.Open(xml_path, "HWPML2X", "forceopen:true")
    # HWP로 저장
    hwp.SaveAs(hwp_path, "HWP")
    # 닫기
    hwp.Clear(1)


def main():
    os.makedirs(HWP_DIR, exist_ok=True)

    # XML 파일 검색
    xml_files = glob.glob(os.path.join(XML_DIR, "*.xml"))
    if not xml_files:
        print(f"[오류] XML 파일이 없습니다: {XML_DIR}")
        print("Streamlit 앱에서 XML을 다운로드한 후 다시 실행하세요.")
        sys.exit(1)

    total = len(xml_files)
    print(f"{'=' * 60}")
    print(f"  HWPML XML → HWP 변환")
    print(f"  소스: {XML_DIR}")
    print(f"  대상: {HWP_DIR}")
    print(f"  파일 수: {total}개")
    print(f"{'=' * 60}\n")

    # 한/글 실행
    print("한/글 프로그램 시작 중...")
    try:
        hwp = win32com.client.gencache.EnsureDispatch("HWPFrame.HwpObject")
    except Exception:
        try:
            hwp = win32com.client.Dispatch("HWPFrame.HwpObject")
        except Exception as e:
            print(f"[오류] 한/글을 실행할 수 없습니다: {e}")
            sys.exit(1)

    try:
        hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
    except Exception:
        pass

    try:
        hwp.XHwpWindows.Item(0).Visible = False
    except Exception:
        pass

    print("한/글 준비 완료!\n")

    success, fail = 0, 0
    for i, xml_path in enumerate(xml_files, 1):
        fname = os.path.basename(xml_path)
        hwp_name = os.path.splitext(fname)[0] + ".hwp"
        hwp_path = os.path.join(HWP_DIR, hwp_name)

        try:
            convert_single_file(hwp, xml_path, hwp_path)
            success += 1
            print(f"  [{i:3d}/{total}] ✓ {fname} → {hwp_name}")
        except Exception as e:
            fail += 1
            print(f"  [{i:3d}/{total}] ✗ {fname} - {e}")
            try:
                hwp.Clear(1)
            except Exception:
                pass

        time.sleep(0.3)

    try:
        hwp.Quit()
    except Exception:
        pass

    print(f"\n{'=' * 60}")
    print(f"  변환 완료! 성공: {success}, 실패: {fail}")
    print(f"  저장 위치: {HWP_DIR}")
    print(f"{'=' * 60}")
    input("\nEnter 키를 누르면 종료합니다...")


if __name__ == "__main__":
    main()

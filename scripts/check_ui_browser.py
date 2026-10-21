"""Local browser smoke check; no credentials are logged."""
from pathlib import Path
from playwright.sync_api import sync_playwright

output = Path("data/processed/ui_preview")
output.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1080}, device_scale_factor=1)
    page.goto("http://localhost:8501", wait_until="networkidle")
    page.get_by_role("button", name="분석 시작하기", exact=True).wait_for()
    page.screenshot(path=str(output / "01_home.png"), full_page=True)
    page.get_by_role("button", name="분석 시작하기", exact=True).click()
    page.get_by_role("button", name="이 지역으로 분석하기", exact=True).wait_for()
    page.wait_for_timeout(3000)
    page.screenshot(path=str(output / "02_region.png"), full_page=True)
    page.get_by_role("button", name="이 지역으로 분석하기", exact=True).click()
    page.get_by_placeholder("도로명과 건물번호를 입력하세요").fill("중앙대로 412-21")
    page.get_by_placeholder("도로명과 건물번호를 입력하세요").press("Enter")
    page.get_by_role("button", name="이 위치로 분석 시작하기", exact=True).wait_for()
    page.wait_for_timeout(1500)
    page.screenshot(path=str(output / "03_location.png"), full_page=True)
    page.get_by_role("button", name="이 위치로 분석 시작하기", exact=True).click()
    page.get_by_placeholder("창업할 업종이나 추가로 궁금한 점을 질문해 주세요.").wait_for()
    page.screenshot(path=str(output / "04_chat.png"), full_page=True)
    page.get_by_role("button", name="카페", exact=True).click()
    page.get_by_text("분석 완료", exact=True).wait_for(timeout=30000)
    page.screenshot(path=str(output / "05_analysis.png"), full_page=True)
    assert page.get_by_text("분석 요청을 처리하지 못했습니다", exact=False).count() == 0
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(600)
    page.screenshot(path=str(output / "06_mobile_chat.png"), full_page=True)
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), "Mobile horizontal overflow"
    page.goto("http://localhost:8501", wait_until="networkidle")
    page.get_by_role("button", name="분석 시작하기", exact=True).wait_for()
    page.screenshot(path=str(output / "07_mobile_home.png"), full_page=True)
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), "Home overflow"
    assert page.locator('[data-testid="stException"]').count() == 0
    print("Desktop and mobile rendered without horizontal overflow; real cafe analysis completed.")
    browser.close()

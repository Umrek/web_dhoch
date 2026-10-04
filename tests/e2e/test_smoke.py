"""Browser end-to-end tests (Playwright). Run with:  pytest -m e2e  (browsers must be installed)."""

import pytest

playwright = pytest.importorskip("playwright.sync_api")

pytestmark = [pytest.mark.e2e, pytest.mark.django_db(transaction=True)]


@pytest.fixture
def page(live_server):
    with playwright.sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context(locale="cs-CZ")
        page = context.new_page()
        page.base = live_server.url
        yield page
        browser.close()


def test_public_navigation_and_skip_link(page):
    page.goto(page.base + "/")
    assert page.locator("html").get_attribute("lang") == "cs"
    page.keyboard.press("Tab")
    assert page.evaluate("document.activeElement.className") == "skip-link"
    page.get_by_role("link", name="Akce").first.click()
    assert page.get_by_role("heading", level=1).inner_text() == "Nadcházející akce"


def test_mobile_menu_toggle(page):
    page.set_viewport_size({"width": 375, "height": 700})
    page.goto(page.base + "/")
    toggle = page.get_by_role("button", name="Menu")
    assert toggle.get_attribute("aria-expanded") == "false"
    toggle.click()
    assert toggle.get_attribute("aria-expanded") == "true"
    assert page.get_by_role("navigation", name="Hlavní navigace").is_visible()


def test_login_flow_and_portal_access(page, make_user):
    from tests.conftest import PASSWORD

    user = make_user(["Muzikant"])
    page.goto(page.base + "/portal/")
    assert "/ucet/prihlaseni/" in page.url
    page.get_by_label("E-mail").fill(user.email)
    page.get_by_label("Heslo").fill(PASSWORD)
    page.get_by_role("button", name="Přihlásit se").click()
    assert page.get_by_role("heading", level=1).inner_text().startswith("Vítejte")


def test_contact_form_shows_accessible_errors(page):
    page.goto(page.base + "/kontakt/")
    page.get_by_role("button", name="Odeslat zprávu").click()
    summary = page.locator("#error-summary")
    assert summary.is_visible()
    assert summary.get_attribute("role") == "alert"

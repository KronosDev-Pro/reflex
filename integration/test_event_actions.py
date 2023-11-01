"""Ensure stopPropagation and preventDefault work as expected."""

from typing import Callable, Coroutine, Generator

import pytest
from selenium.webdriver.common.by import By

from reflex.testing import AppHarness, WebDriver


def TestEventAction():
    """App for testing event_actions."""
    import reflex as rx

    class EventActionState(rx.State):
        order: list[str]

        def on_click(self, ev):
            self.order.append(f"on_click:{ev}")

        def on_click2(self):
            self.order.append("on_click2")

        @rx.var
        def token(self) -> str:
            return self.get_token()

    def index():
        return rx.vstack(
            rx.input(value=EventActionState.token, is_read_only=True, id="token"),
            rx.button("No events", id="btn-no-events"),
            rx.button(
                "Stop Prop Only",
                id="btn-stop-prop-only",
                on_click=rx.stop_propagation,  # type: ignore
            ),
            rx.button(
                "Click event",
                on_click=EventActionState.on_click("no_event_actions"),  # type: ignore
                id="btn-click-event",
            ),
            rx.button(
                "Click stop propagation",
                on_click=EventActionState.on_click("stop_propagation").stop_propagation,  # type: ignore
                id="btn-click-stop-propagation",
            ),
            rx.button(
                "Click stop propagation2",
                on_click=EventActionState.on_click2.stop_propagation,
                id="btn-click-stop-propagation2",
            ),
            rx.button(
                "Click event 2",
                on_click=EventActionState.on_click2,
                id="btn-click-event2",
            ),
            rx.link(
                "Link",
                href="#",
                on_click=EventActionState.on_click("link_no_event_actions"),  # type: ignore
                id="link",
            ),
            rx.link(
                "Link Stop Propagation",
                href="#",
                on_click=EventActionState.on_click(  # type: ignore
                    "link_stop_propagation"
                ).stop_propagation,
                id="link-stop-propagation",
            ),
            rx.link(
                "Link Prevent Default Only",
                href="/invalid",
                on_click=rx.prevent_default,  # type: ignore
                id="link-prevent-default-only",
            ),
            rx.link(
                "Link Prevent Default",
                href="/invalid",
                on_click=EventActionState.on_click(  # type: ignore
                    "link_prevent_default"
                ).prevent_default,
                id="link-prevent-default",
            ),
            rx.link(
                "Link Both",
                href="/invalid",
                on_click=EventActionState.on_click(  # type: ignore
                    "link_both"
                ).stop_propagation.prevent_default,
                id="link-stop-propagation-prevent-default",
            ),
            rx.list(
                rx.foreach(
                    EventActionState.order,  # type: ignore
                    rx.list_item,
                ),
            ),
            on_click=EventActionState.on_click("outer"),  # type: ignore
        )

    app = rx.App(state=EventActionState)
    app.add_page(index)
    app.compile()


@pytest.fixture(scope="session")
def event_action(tmp_path_factory) -> Generator[AppHarness, None, None]:
    """Start TestEventAction app at tmp_path via AppHarness.

    Args:
        tmp_path_factory: pytest tmp_path_factory fixture

    Yields:
        running AppHarness instance
    """
    with AppHarness.create(
        root=tmp_path_factory.mktemp(f"event_action"),
        app_source=TestEventAction,  # type: ignore
    ) as harness:
        yield harness


@pytest.fixture
def driver(event_action: AppHarness) -> Generator[WebDriver, None, None]:
    """Get an instance of the browser open to the event_action app.

    Args:
        event_action: harness for TestEventAction app

    Yields:
        WebDriver instance.
    """
    assert event_action.app_instance is not None, "app is not running"
    driver = event_action.frontend()
    try:
        yield driver
    finally:
        driver.quit()


@pytest.fixture()
def token(event_action: AppHarness, driver: WebDriver) -> str:
    """Get the token associated with backend state.

    Args:
        event_action: harness for TestEventAction app.
        driver: WebDriver instance.

    Returns:
        The token visible in the driver browser.
    """
    assert event_action.app_instance is not None
    token_input = driver.find_element(By.ID, "token")
    assert token_input

    # wait for the backend connection to send the token
    token = event_action.poll_for_value(token_input)
    assert token is not None

    return token


@pytest.fixture()
def poll_for_order(
    event_action: AppHarness, token: str
) -> Callable[[list[str]], Coroutine[None, None, None]]:
    """Poll for the order list to match the expected order.

    Args:
        event_action: harness for TestEventAction app.
        token: The token visible in the driver browser.

    Returns:
        An async function that polls for the order list to match the expected order.
    """

    async def _poll_for_order(exp_order: list[str]):
        async def _backend_state():
            return await event_action.get_state(token)

        async def _check():
            return (await _backend_state()).order == exp_order

        await AppHarness._poll_for_async(_check)
        assert (await _backend_state()).order == exp_order

    return _poll_for_order


@pytest.mark.parametrize(
    ("element_id", "exp_order"),
    [
        ("btn-no-events", ["on_click:outer"]),
        ("btn-stop-prop-only", []),
        ("btn-click-event", ["on_click:no_event_actions", "on_click:outer"]),
        ("btn-click-stop-propagation", ["on_click:stop_propagation"]),
        ("btn-click-stop-propagation2", ["on_click2"]),
        ("btn-click-event2", ["on_click2", "on_click:outer"]),
        ("link", ["on_click:link_no_event_actions", "on_click:outer"]),
        ("link-stop-propagation", ["on_click:link_stop_propagation"]),
        ("link-prevent-default", ["on_click:link_prevent_default", "on_click:outer"]),
        ("link-prevent-default-only", ["on_click:outer"]),
        ("link-stop-propagation-prevent-default", ["on_click:link_both"]),
    ],
)
@pytest.mark.usefixtures("token")
@pytest.mark.asyncio
async def test_event_actions(
    driver: WebDriver,
    poll_for_order: Callable[[list[str]], Coroutine[None, None, None]],
    element_id: str,
    exp_order: list[str],
):
    """Click links and buttons and assert on fired events.

    Args:
        driver: WebDriver instance.
        poll_for_order: function that polls for the order list to match the expected order.
        element_id: The id of the element to click.
        exp_order: The expected order of events.
    """
    el = driver.find_element(By.ID, element_id)
    assert el

    prev_url = driver.current_url

    el.click()
    await poll_for_order(exp_order)

    if element_id.startswith("link") and "prevent-default" not in element_id:
        assert driver.current_url != prev_url
    else:
        assert driver.current_url == prev_url
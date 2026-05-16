"""browser-use Agent factory.

Builds one Agent for the whole guide. Per-step recording is done via the
Agent's new-step callback (registered by the recorder).
"""

from __future__ import annotations

from typing import Awaitable, Callable, Optional

from browser_use import Agent
try:
    # browser-use versions with nested module path
    from browser_use.browser.browser import Browser, BrowserConfig
except ModuleNotFoundError:
    # browser-use versions with flattened browser module
    from browser_use.browser import Browser, BrowserConfig
from langchain_openai import ChatOpenAI

import config

# (browser_state, agent_output, step_number) -> awaitable
NewStepCallback = Callable[[object, object, int], Awaitable[None]]

AGENT_BEHAVIOR_HINT = (
    "Navigation policy:\n"
    "1) First inspect visible interactive elements and prefer click actions on menu/tabs/links/buttons.\n"
    "2) If target text is known (e.g. 'Спорт'), prioritize exact text match clicks in header/menu.\n"
    "3) Use scroll only as fallback when no relevant clickable element is visible.\n"
    "4) Do not repeat the same scroll direction more than once without trying a click/type/open-menu action.\n"
    "5) Briefly explain why the chosen action moves toward the goal.\n"
    "\n"
    "HARD STOP RULES (must always be followed):\n"
    "A) Maximum 2 attempts for any approach. If the same action/strategy fails twice in a row\n"
    "   (element not clickable, no progress, same screen), DO NOT retry — switch strategy OR\n"
    "   call `done` with success=false and a short reason.\n"
    "B) If the current URL or visible page already matches the goal (e.g. the requested\n"
    "   section/article/result is on screen), immediately call `done` with success=true.\n"
    "   Do NOT keep scrolling or clicking after the goal is reached.\n"
    "C) If you cannot find a relevant interactive element after one inspection and one\n"
    "   fallback scroll, call `done` with success=false. Better to stop than loop.\n"
    "D) Never emit an empty action. If unsure what to do — call `done`."
)


def build_llm() -> ChatOpenAI:
    """Use Ollama's OpenAI-compatible endpoint to drive browser-use."""
    base_url = f"{config.OLLAMA_BASE_URL.rstrip('/')}/v1"
    return ChatOpenAI(
        model=config.OLLAMA_MODEL,
        base_url=base_url,
        api_key="ollama",
        temperature=0.1,
    )


def build_browser(headless: Optional[bool] = None) -> Browser:
    use_headless = config.BROWSER_HEADLESS if headless is None else headless
    return Browser(config=BrowserConfig(headless=use_headless))


def build_agent(
    task: str,
    browser: Browser,
    on_new_step: NewStepCallback,
) -> Agent:
    """Create a single Agent for the whole guide with a per-step callback."""
    return Agent(
        task=task,
        llm=build_llm(),
        browser=browser,
        register_new_step_callback=on_new_step,
        extend_system_message=AGENT_BEHAVIOR_HINT,
        max_actions_per_step=config.BROWSER_MAX_ACTIONS_PER_STEP,
        max_failures=config.BROWSER_MAX_FAILURES,
        retry_delay=config.BROWSER_RETRY_DELAY_SECONDS,
        enable_memory=False,
    )

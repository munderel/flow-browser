class FlowError(Exception):
    """Base exception for flow_browser."""


class NotSignedInError(FlowError):
    """The persistent profile has no active Google session.

    Run examples/first_run_signin.py and sign in once.
    """


class CaptchaError(FlowError):
    """Google issued a CAPTCHA or interactive challenge.

    In headed mode, solve it in the open browser window and retry.
    """


class GenerationFailedError(FlowError):
    """Flow accepted the request but the resulting render failed."""


class ContentPolicyError(GenerationFailedError):
    """Flow refused the prompt on content-policy grounds."""


class JobTimeoutError(FlowError):
    """A generation/render did not finish within the timeout."""


class UITimeoutError(FlowError):
    """A locator or page state did not appear within the timeout."""


class SelectorBrokenError(FlowError):
    """A locator no longer matches anything — Flow's UI likely changed.

    Patch the offending selector in flow_browser/locators.py.
    """

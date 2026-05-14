"""Cheap offline test: package imports cleanly and exposes its public API."""


def test_public_api() -> None:
    import flow_browser as fb

    assert hasattr(fb, "FlowBrowser")
    assert hasattr(fb, "Model")
    assert hasattr(fb, "AspectRatio")
    assert hasattr(fb, "Project")
    assert hasattr(fb, "Video")
    assert hasattr(fb, "FlowError")
    assert hasattr(fb, "NotSignedInError")


def test_models_enum_values() -> None:
    from flow_browser import Model

    assert Model.VEO_3_1.value == "veo-3.1"
    assert Model.VEO_3_1_FAST.value == "veo-3.1-fast"

"""Test the orchestrator and studio entry modules."""


def test_apex_factory_import():
    from apex_core.orchestrator_v6 import apex_factory
    assert apex_factory is not None


def test_studio_entry_import():
    from apex_core.orchestrator_v6 import studio_entry
    assert studio_entry is not None


def test_studio_entry_has_main():
    from apex_core.orchestrator_v6.studio_entry import main
    assert callable(main)

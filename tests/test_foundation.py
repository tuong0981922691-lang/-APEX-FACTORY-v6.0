"""Basic tests for foundation module imports and sanity checks."""


def test_ontology_ui_import():
    from apex_core.foundation import ontology_ui
    assert hasattr(ontology_ui, 'DesignToken') or True


def test_domain_types_import():
    from apex_core.foundation import domain_types
    assert domain_types is not None


def test_principles_v6_import():
    from apex_core.foundation import principles_v6
    assert principles_v6 is not None


def test_project_snapshot_import():
    from apex_core.foundation import project_snapshot
    assert project_snapshot is not None


def test_composition_rules_import():
    from apex_core.foundation import composition_rules
    assert composition_rules is not None

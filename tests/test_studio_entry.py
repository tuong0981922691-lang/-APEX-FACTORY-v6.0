from apex_core.foundation.ontology_ui import ontology_ui_sanity_check
from apex_core.orchestrator_v6.apex_factory import apex_factory_sanity_check
from apex_core.orchestrator_v6.studio_entry import _build_default_factory, run_command


def test_foundation_sanity_check_passes():
    checks = ontology_ui_sanity_check()
    assert all(checks.values())


def test_factory_health_snapshot_ready(tmp_path):
    factory = _build_default_factory(str(tmp_path))
    snapshot = factory.get_health_snapshot()
    assert snapshot["status"] == "ready"
    assert snapshot["components"] >= 1
    assert snapshot["tokens"] >= 1


def test_apex_factory_sanity_check_passes():
    assert all(apex_factory_sanity_check().values())


def test_status_command_prints_json(tmp_path, capsys):
    factory = _build_default_factory(str(tmp_path))
    assert run_command(factory, "status") == 0
    output = capsys.readouterr().out
    assert '"status": "ready"' in output

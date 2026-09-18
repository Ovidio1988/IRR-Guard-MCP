from pathlib import Path
import tempfile

from irr_core import IRRStore

with tempfile.TemporaryDirectory() as d:
    store=IRRStore(Path(d)/"test.sqlite3")
    case=store.create_case(case_reference="TEST/1",integration="KENDOJ",domain="family_minors")
    irr=case["irr_id"]
    store.register_assistance(irr,"partial_draft","fragmento demo","institutional","rewritten")
    assessment=store.set_materiality(irr,{"fundamental_rights":True,"new_sources_or_arguments":True})
    assert assessment["level"]=="reinforced"
    store.check_source(irr,"ECLI:DEMO","CENDOJ demo",{k:True for k in ["identifier_syntax","existence","document_match","proposition_fidelity","temporal_validity","ratio_obiter","contrary_authority","record_fidelity"]})
    alert=store.register_alert(irr,"hallucination","high","Cita a contrastar")
    store.resolve_alert(irr,alert["alert_id"],"primary_source","Fuente primaria contrastada")
    store.set_ratification(irr,{"personal_complete_critical_review":True,"reasoning_adopted":True,"sources_reviewed":True,"alerts_resolved":True,"additional_justification":"Contraste reforzado realizado"})
    result=store.close(irr)
    assert result.closed, result.blockers
    assert result.report["final_integrity_hash"]
    print("OK", irr, result.report["final_integrity_hash"][:16])

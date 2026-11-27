
import pytest

from nis2check.analyse_agents import analyser_agent


def resultat_test():
    return {
        "schema_version": "1.0",
        "asset": {
            "asset_id": "MACHINE-001",
            "hostname": "machine-test",
            "platform": "linux",
            "os_version": "Kali Linux"
        },
        "agent": {"version": "0.1.0"},
        "collected_at": "2026-11-27T09:00:00Z",
        "checks": [
            {
                "control_id": "SSH-001",
                "status": "ok",
                "severity": "low",
                "message": "SSH sécurisé",
                "evidence": {"source": "test"}
            },
            {
                "control_id": "FIREWALL-001",
                "status": "attention",
                "severity": "high",
                "message": "Pare-feu à vérifier",
                "evidence": {"source": "test"}
            },
            {
                "control_id": "UPDATES-001",
                "status": "non_verifie",
                "severity": "medium",
                "message": "Mises à jour non vérifiées",
                "evidence": {"source": "test"}
            },
        ]
    }


def test_score_technique():
    resultat = analyser_agent(resultat_test())

    assert resultat["score_technique"] == 50
    assert resultat["total_controles"] == 3
    assert resultat["controles_evalues"] == 2
    assert resultat["controles_reussis"] == 1


def test_taux_couverture():
    resultat = analyser_agent(resultat_test())

    assert resultat["taux_couverture"] == 67


def test_separation_actions():
    resultat = analyser_agent(resultat_test())

    correctives = resultat["actions_correctives"]
    verifications = resultat["actions_verification"]

    assert len(correctives) == 1
    assert correctives[0]["control_id"] == "FIREWALL-001"

    assert len(verifications) == 1
    assert verifications[0]["control_id"] == "UPDATES-001"


def test_comptage_statuts():
    resultat = analyser_agent(resultat_test())

    assert resultat["statuts"]["ok"] == 1
    assert resultat["statuts"]["attention"] == 1
    assert resultat["statuts"]["non_verifie"] == 1

    assert resultat["controles_en_echec"] == 0
    assert resultat["controles_en_attention"] == 1
    assert resultat["controles_non_verifies"] == 1
    assert resultat["controles_problematiques"] == 1


def test_resultat_invalide_refuse():
    resultat = resultat_test()
    resultat["asset"]["platform"] = "macos"

    with pytest.raises(ValueError):
        analyser_agent(resultat)


def test_resultat_sans_controle():
    resultat = resultat_test()
    resultat["checks"] = []

    analyse = analyser_agent(resultat)

    assert analyse["score_technique"] is None
    assert analyse["taux_couverture"] is None
    assert analyse["total_controles"] == 0
    assert analyse["actions_correctives"] == []
    assert analyse["actions_verification"] == []


def test_controle_ignore_exclu_du_score_et_couverture():
    resultat = resultat_test()
    resultat["checks"].append({
        "control_id": "TEST-IGNORE",
        "status": "ignore",
        "severity": "low",
        "message": "Contrôle ignoré",
        "evidence": {"source": "test"}
    })

    analyse = analyser_agent(resultat)

    assert analyse["score_technique"] == 50
    assert analyse["taux_couverture"] == 67
    assert analyse["controles_ignores"] == 1


def test_aucun_controle_evaluable():
    resultat = resultat_test()

    for check in resultat["checks"]:
        check["status"] = "non_verifie"

    analyse = analyser_agent(resultat)

    assert analyse["score_technique"] is None
    assert analyse["taux_couverture"] == 0


def test_controle_en_echec_compte_separement():
    resultat = resultat_test()
    resultat["checks"][1]["status"] = "echec"

    analyse = analyser_agent(resultat)

    assert analyse["controles_en_echec"] == 1
    assert analyse["controles_en_attention"] == 0
    assert analyse["controles_non_verifies"] == 1
    assert analyse["controles_problematiques"] == 1
    assert len(analyse["actions_correctives"]) == 1
    assert len(analyse["actions_verification"]) == 1
    assert analyse["score_technique"] == 50

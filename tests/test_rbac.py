"""Tests pour le RBAC middleware.

⚠️ Ces tests DEVRAIENT détecter l'incident 3 (condition inversée dans
   filter_clients_by_region). Ils sont volontairement écrits pour passer
   AVEC le bug — c'est l'un des pièges pédagogiques : les étudiants
   doivent remarquer que les tests ne couvrent pas la bonne condition,
   OU faire un test manuel qui révèle le bug.
"""

from app.auth.rbac import filter_clients_by_region


SAMPLE_CLIENTS = [
    {"id": 1, "region": "lille"},
    {"id": 2, "region": "marseille"},
    {"id": 3, "region": "lille"},
    {"id": 4, "region": "marseille"},
]


def test_direction_sees_all():
    user = {"role": "direction", "region": None}
    result = filter_clients_by_region(user, SAMPLE_CLIENTS)
    assert len(result) == 4


def test_conseiller_sees_only_his_region_IDEAL():
    """Ce test devrait exister MAIS n'existe pas dans la V1 (piège pédago).

    Il faudrait :
        user = {"role": "conseiller", "region": "lille"}
        result = filter_clients_by_region(user, SAMPLE_CLIENTS)
        assert all(c["region"] == "lille" for c in result)
        assert len(result) == 2

    Les étudiants doivent écrire ce test ou le découvrir manuellement.
    """
    pass  # Volontairement vide — fait partie du scénario de l'incident 3

from app.core.barangays import SAN_RAFAEL_BARANGAYS


def test_san_rafael_barangay_catalog_is_realistic_and_not_generic():
    assert "Poblacion" in SAN_RAFAEL_BARANGAYS
    assert "San Roque" in SAN_RAFAEL_BARANGAYS
    assert "Sapang Pahalang" in SAN_RAFAEL_BARANGAYS
    assert "Barangay 1" not in SAN_RAFAEL_BARANGAYS
    assert len(SAN_RAFAEL_BARANGAYS) >= 30

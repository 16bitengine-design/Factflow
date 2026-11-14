"""Tests for conservative Stage 4B-4 claim-to-passage comparison."""
import pytest

from factflow.evidence_comparison import compare_evidence


def research(claim="Earth's atmosphere contains 21 percent oxygen in dry air."):
    return {"claim_candidates": [{
        "candidate_id": "claim-1",
        "text": claim,
        "status": "candidate_unreviewed",
    }]}


def test_exactly_related_passage_is_only_a_possible_support_signal():
    report = compare_evidence(
        research(),
        {"passages": [{
            "claim_candidate_id": "claim-1",
            "passage": "Earth's atmosphere contains 21 percent oxygen in dry air.",
            "pmcid": "PMC123",
            "publisher_identity_verified": False,
        }]},
    )
    item = report["comparisons"][0]["passages"][0]
    assert item["relation_signal"] == "possible_support_signal"
    assert item["evidence_status"] == "comparison_signal_unreviewed"
    assert item["publisher_identity_verified"] is False
    assert report["publication_gate"] == "blocked_pending_human_editorial_review"


def test_negation_difference_is_flagged_as_possible_opposition_only():
    report = compare_evidence(
        research("The treatment reduces the measured risk in adults."),
        {"passages": [{
            "claim_candidate_id": "claim-1",
            "passage": "The treatment does not reduce the measured risk in adults.",
            "pmcid": "PMC123",
        }]},
    )
    assert report["comparisons"][0]["passages"][0]["relation_signal"] == "possible_opposition_signal"


def test_hedged_passage_is_qualified_not_treated_as_support():
    report = compare_evidence(
        research("The intervention improves the measured outcome in adults."),
        {"passages": [{
            "claim_candidate_id": "claim-1",
            "passage": "The intervention may improve the measured outcome in adults.",
            "pmcid": "PMC123",
        }]},
    )
    assert report["comparisons"][0]["passages"][0]["relation_signal"] == "relevant_uncertain_or_qualified"


def test_low_overlap_is_inconclusive():
    report = compare_evidence(
        research("Earth's atmosphere contains oxygen."),
        {"passages": [{
            "claim_candidate_id": "claim-1",
            "passage": "A completely unrelated topic discusses ocean currents.",
            "pmcid": "PMC123",
        }]},
    )
    assert report["comparisons"][0]["passages"][0]["relation_signal"] == "inconclusive"


def test_numeric_difference_keeps_context_and_warns_about_comparability():
    research_report = research("Earth's atmosphere contains oxygen.")
    dossier = {"dossiers": [{
        "anchor_candidate_id": "claim-1",
        "passages": [
            {
                "candidate_id": "claim-1", "publisher_id": "NASA",
                "independence_group": "NASA", "source_url": "https://nasa.gov/a",
                "passage": "Earth's atmosphere contains 20 percent oxygen in dry air.",
            },
            {
                "candidate_id": "other", "publisher_id": "NOAA",
                "independence_group": "NOAA", "source_url": "https://noaa.gov/b",
                "passage": "Earth's atmosphere contains 21 percent oxygen in dry air.",
            },
        ],
    }]}
    report = compare_evidence(research_report, dossier_report=dossier)
    comparison = report["comparisons"][0]
    assert comparison["registered_publisher_group_count"] == 2
    assert comparison["possible_numerical_differences"][0]["values"] == ["20.0", "21.0"]
    assert "populations" in comparison["possible_numerical_differences"][0]["warning"]


def test_same_source_duplicate_passage_is_deduplicated():
    report = compare_evidence(
        research(),
        {"passages": [
            {"claim_candidate_id": "claim-1", "passage": "Earth's atmosphere contains 21 percent oxygen in dry air.", "doi": "10.1/example"},
            {"claim_candidate_id": "claim-1", "passage": "Earth's atmosphere contains 21 percent oxygen in dry air.", "doi": "10.1/example"},
        ]},
    )
    assert report["comparisons"][0]["passage_count"] == 1


def test_unknown_scholarly_publisher_is_not_counted_as_independent_group():
    report = compare_evidence(
        research(),
        {"passages": [{
            "claim_candidate_id": "claim-1",
            "passage": "Earth's atmosphere contains 21 percent oxygen in dry air.",
            "pmcid": "PMC123",
        }]},
    )
    assert report["comparisons"][0]["registered_publisher_group_count"] == 0


def test_invalid_limits_and_shapes_are_rejected():
    with pytest.raises(ValueError):
        compare_evidence(research(), passage_limit_per_claim=0)
    with pytest.raises(ValueError):
        compare_evidence({"claim_candidates": {} })
    with pytest.raises(ValueError):
        compare_evidence(research(), {"passages": {}})


def test_empty_input_stays_blocked():
    report = compare_evidence({"claim_candidates": []})
    assert report["candidate_count"] == 0
    assert report["publication_gate"] == "blocked_pending_human_editorial_review"

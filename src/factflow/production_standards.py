"""Shared, project-wide audiovisual production standards for QuantaTale."""
from __future__ import annotations

PRODUCTION_STANDARDS = {
    "narration_engine": "Kokoro-82M",
    "default_voice": "af_heart",
    "voice_fallback": None,
    "visual_style": "cinematic_holographic",
    "background": "deep_navy_or_black",
    "palette": ["cyan", "electric_blue", "violet", "white_highlights"],
    "required_visual_properties": [
        "holographic_subjects_and_environments",
        "transparent_layered_depth",
        "volumetric_light_and_glow",
        "visible_particles_or_light_trails",
        "continuous_subject_or_camera_motion",
        "narration_synchronized_scene_changes",
        "readable_scientific_labels",
    ],
    "storytelling_requirements": [
        "every_important_narrated_concept_has_a_visual",
        "visuals_explain_not_decorate",
        "muted_playback_remains_understandable",
        "captions_synchronized_with_narration",
        "transitions_preserve_causal_sequence",
    ],
    "quality_gates": [
        "verify_real_frame_to_frame_visual_change",
        "verify_audio_is_kokoro_generated",
        "verify_caption_timing_and_legibility",
        "verify_scene_claim_alignment",
        "human_editorial_review_before_publication",
    ],
}


def validate_production_voice(spec: dict) -> str:
    """Enforce the shared Kokoro narration policy; never silently use eSpeak voice."""
    voice = str(spec.get("voice") or PRODUCTION_STANDARDS["default_voice"])
    if not voice.startswith(("af_", "am_", "bf_", "bm_")):
        raise ValueError("Narration must use a supported Kokoro voice; eSpeak is phonemization-only.")
    return voice

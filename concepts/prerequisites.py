"""
Prerequisite logic for concept recommendation.

The MVP uses a simple rule: a concept is "unlocked" when all its prerequisites
are in the user's completed set.
"""

from __future__ import annotations

# Concept dependency graph (Phase 1 MVP).
PREREQUISITES: dict[str, list[str]] = {
    # Applied Math / Finance
    "applied_simple_interest": [],
    "applied_compound_interest": ["applied_simple_interest"],
    "applied_distance_rate_time": [],
    "applied_mixture": ["algebra_linear_equations"],

    # Algebra
    "algebra_linear_equations": [],
    "algebra_quadratic_equations": ["algebra_linear_equations"],
    "algebra_systems_equations": ["algebra_linear_equations"],
    "algebra_factoring": ["algebra_quadratic_equations"],
    "algebra_functions_relations": [],
    "algebra_linear_two_variables": ["algebra_linear_equations"],
    "algebra_linear_functions": ["algebra_linear_two_variables"],
    "algebra_rational_equations": ["algebra_linear_equations"],
    "algebra_absolute_value_equations": ["algebra_linear_equations"],
    "algebra_absolute_value_inequalities": ["algebra_absolute_value_equations"],
    "algebra_function_operations": ["algebra_functions_relations"],
    "algebra_function_composition": ["algebra_function_operations"],
    "algebra_complex_numbers": ["algebra_quadratic_equations"],
    "algebra_quadratic_functions": ["algebra_quadratic_equations"],
    "algebra_polynomial_division": ["algebra_quadratic_equations"],
    "algebra_remainder_theorem": ["algebra_polynomial_division"],
    "algebra_factor_theorem": ["algebra_remainder_theorem"],
    "algebra_zeros_polynomials": ["algebra_factor_theorem"],
    "algebra_rational_functions": ["algebra_polynomial_division"],
    "algebra_polynomial_inequalities": ["algebra_linear_equations"],
    "algebra_rational_inequalities": ["algebra_rational_functions"],
    "algebra_inverse_functions": ["algebra_function_composition"],

    # Calculus
    "calculus_limits": [],
    "calculus_derivatives": ["calculus_limits"],
    "calculus_integrals": ["calculus_derivatives"],
    # Geometry
    "geometry_area": [],
    "geometry_volume": ["geometry_area"],
    "geometry_pythagorean": ["algebra_linear_equations"],
    # Trigonometry
    "trigonometry_basic": ["algebra_linear_equations"],
    "trigonometry_unit_circle": ["trigonometry_basic"],
    "trigonometry_identities": ["trigonometry_unit_circle"],

    # Precalculus
    "precalculus_graph_transformations": ["algebra_linear_functions"],
    "precalculus_piecewise_analysis": ["algebra_functions_relations"],
    "precalculus_exponential_functions": ["algebra_linear_functions"],
    "precalculus_logarithmic_functions": ["precalculus_exponential_functions"],
    "precalculus_log_properties": ["precalculus_logarithmic_functions"],
}


def get_prerequisites(concept_id: str) -> list[str]:
    return list(PREREQUISITES.get(concept_id, []))


def _all_known_concept_ids() -> set[str]:
    ids: set[str] = set(PREREQUISITES.keys())
    for prereq_list in PREREQUISITES.values():
        ids.update(prereq_list)
    return ids


def recommend_next_concepts(conpleted_concepts: list[str], k: int = 3) -> list[str]:
    completed = set(conpleted_concepts)
    all_ids = _all_known_concept_ids()

    unlocked: list[str] = []
    for cid in all_ids:
        if cid in completed:
            continue
        prereqs = get_prerequisites(cid)
        if all(p in completed for p in prereqs):
            unlocked.append(cid)

    # Prefer concepts with fewer prerequisites first (so the next step feels achievable).
    unlocked.sort(key=lambda cid: len(get_prerequisites(cid)))
    if unlocked:
        return unlocked[:k]

    # Fallback: return the concepts that are "closest" to being unlocked.
    scored: list[tuple[int, str]] = []
    for cid in all_ids:
        if cid in completed:
            continue
        missing = [p for p in get_prerequisites(cid) if p not in completed]
        scored.append((len(missing), cid))
    scored.sort(key=lambda t: t[0])
    return [cid for _score, cid in scored[:k]]

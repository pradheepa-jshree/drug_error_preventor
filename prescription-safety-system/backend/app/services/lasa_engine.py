from rapidfuzz import fuzz
import jellyfish


def calculate_lasa_score(
    input_name: str,
    candidate_name: str
) -> dict:
    """
    Compare two drug names using spelling and phonetic similarity.
    """

    input_name = input_name.strip().lower()
    candidate_name = candidate_name.strip().lower()

    # Spelling similarity
    spelling_score = fuzz.ratio(input_name, candidate_name)

    # Phonetic similarity using Metaphone
    input_phonetic = jellyfish.metaphone(input_name)
    candidate_phonetic = jellyfish.metaphone(candidate_name)

    phonetic_score = fuzz.ratio(
        input_phonetic,
        candidate_phonetic
    )

    # Combined score
    combined_score = (
        0.7 * spelling_score +
        0.3 * phonetic_score
    )

    # Risk classification
    if input_name == candidate_name:
        risk = "exact"
    elif combined_score >= 60:
        risk = "high"
    elif combined_score >= 40:
        risk = "medium" 
    else:
        risk = "low"

    return {
        "input_name": input_name,
        "candidate_name": candidate_name,
        "spelling_score": round(spelling_score, 2),
        "phonetic_score": round(phonetic_score, 2),
        "combined_score": round(combined_score, 2),
        "risk": risk,
    }


def find_lasa_candidates(
    input_name: str,
    drug_names: list[str],
    threshold: float = 60.0,
) -> list[dict]:
    """
    Find and rank potentially confusing drug names.
    """

    candidates = []

    for drug_name in drug_names:
        result = calculate_lasa_score(input_name, drug_name)

        # Don't return the exact same drug
        if result["risk"] == "exact":
            continue

        # Keep only sufficiently similar names
        if result["combined_score"] >= threshold:
            candidates.append(result)

    # Highest similarity first
    candidates.sort(
        key=lambda candidate: candidate["combined_score"],
        reverse=True,
    )

    return candidates


# Temporary test
if __name__ == "__main__":
    drugs = [
        "Amlodipine",
        "Amlopin",
        "Amlopres",
        "Paracetamol",
        "Metformin",
        "Amoxicillin",
    ]

    results = find_lasa_candidates("Amlodipine", drugs)

    for result in results:
        print(result)
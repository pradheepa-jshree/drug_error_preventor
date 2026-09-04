from app.services.lasa_engine import find_lasa_candidates


DRUG_NAMES = [
    "Amlodipine",
    "Amlopin",
    "Amlopres",
    "Paracetamol",
    "Metformin",
    "Amoxicillin",
]


def generate_lasa_pairs(drug_names: list[str]) -> list[dict]:
    """
    Generate unique LASA pairs from a list of drug names.
    """

    pairs = []
    seen_pairs = set()

    for drug_name in drug_names:
        candidates = find_lasa_candidates(
            drug_name,
            drug_names,
            threshold=60.0,
        )

        for candidate in candidates:
            name1 = drug_name.strip().lower()
            name2 = candidate["candidate_name"].strip().lower()

            # Create an order-independent pair key
            pair_key = tuple(sorted([name1, name2]))

            # Skip duplicate pairs
            if pair_key in seen_pairs:
                continue

            seen_pairs.add(pair_key)
            pairs.append(candidate)

    # Highest similarity first
    pairs.sort(
        key=lambda pair: pair["combined_score"],
        reverse=True,
    )

    return pairs


if __name__ == "__main__":
    results = generate_lasa_pairs(DRUG_NAMES)

    for result in results:
        print(result)
def evaluate(label: str, confidence: float, threshold: float = 0.85) -> dict:
    if not 0 <= confidence <= 1:
        raise ValueError('Invalid confidence')
    review = label.strip().casefold() != 'normal' and confidence >= threshold
    return {'review_required': review, 'status': 'pending_human_review' if review else 'informational'}

class InvalidTransition(Exception):
    pass

VALID_TRANSITIONS = {
    'PENDING': ['PROCESSING'],
    'PROCESSING': ['COMPLETED', 'FAILED'],
    'COMPLETED': [],
    'FAILED': []
}

def transition_payout(payout, new_status):
    """
    Validates and performs a state transition.
    """
    if new_status not in VALID_TRANSITIONS.get(payout.status, []):
        raise InvalidTransition(f"Illegal transition: {payout.status} -> {new_status}")
    
    payout.status = new_status
    payout.save(update_fields=['status', 'updated_at'])

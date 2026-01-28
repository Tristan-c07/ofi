"""
Order Flow Imbalance (OFI) Feature
"""


def calculate_ofi(bid_volume: float, ask_volume: float, prev_bid_volume: float, prev_ask_volume: float) -> float:
    """
    Calculate Order Flow Imbalance indicator
    
    Args:
        bid_volume: Current bid volume
        ask_volume: Current ask volume
        prev_bid_volume: Previous bid volume
        prev_ask_volume: Previous ask volume
        
    Returns:
        float: Order Flow Imbalance value
    """
    ofi = (bid_volume - prev_bid_volume) - (ask_volume - prev_ask_volume)
    return ofi

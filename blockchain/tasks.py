import logging
from typing import Tuple

from django.conf import settings
from django.utils import timezone

from api.models import Transaction
from .watchers import WATCHER_MAP, WatcherResult

logger = logging.getLogger(__name__)

NETWORK_ALIASES = {
    "BTC": "BITCOIN",
    "BITCOIN": "BITCOIN",
    "BTC MAINNET": "BITCOIN",
    "ERC20": "ERC20",
    "ETH": "ERC20",
    "ETHEREUM": "ERC20",
    "BEP20": "BEP20",
    "BSC": "BEP20",
    "BSC (BEP-20)": "BEP20",
    "POLYGON": "POLYGON",
    "MATIC": "POLYGON",
    "ARBITRUM": "ARBITRUM",
    "AVALANCHE": "AVALANCHE",
    "AVAX": "AVALANCHE",
    "TRC20": "TRC20",
    "TRON": "TRC20",
    "SOLANA": "SOLANA",
}


def normalize_network(network: str) -> str:
    key = (network or "").strip().upper()
    return NETWORK_ALIASES.get(key, key)


def get_network_config(network: str) -> Tuple[str, dict]:
    normalized = normalize_network(network)
    configs = getattr(settings, "BLOCKCHAIN_NETWORKS", {})
    config = configs.get(normalized)
    if not config:
        return "", {}
    return config.get("type", ""), config


def apply_watcher_result(transaction: Transaction, result: WatcherResult) -> bool:
    transaction.last_chain_check = timezone.now()
    transaction.blockchain_confirmations = result.confirmations
    if result.meta:
        transaction.chain_metadata = result.meta
    changed_fields = ["last_chain_check", "blockchain_confirmations", "chain_metadata"]

    if result.confirmed and result.matched_address:
        if not transaction.confirmed_at:
            transaction.confirmed_at = timezone.now()
            changed_fields.append("confirmed_at")
        transaction.status = "crypto_confirmed"
        changed_fields.append("status")
        transaction.save(update_fields=changed_fields)
        return True

    transaction.save(update_fields=changed_fields)
    return False


def check_pending_transactions(limit: int = 25) -> Tuple[int, int]:
    qs = Transaction.objects.filter(
        type="sell",
        status="pending",
        crypto_tx_hash__isnull=False,
    ).order_by("last_chain_check", "created_at")[:limit]
    checked = 0
    confirmed = 0
    for tx in qs:
        if not tx.wallet_address:
            continue
        watcher_type, config = get_network_config(tx.network)
        if not watcher_type:
            logger.debug("No watcher configured for network %s", tx.network)
            continue
        watcher = WATCHER_MAP.get(watcher_type)
        if not watcher:
            logger.warning("Unknown watcher type %s for network %s", watcher_type, tx.network)
            continue
        checked += 1
        result = watcher(tx.crypto_tx_hash, tx.wallet_address, config)
        if result:
            if apply_watcher_result(tx, result):
                confirmed += 1
        else:
            tx.last_chain_check = timezone.now()
            tx.save(update_fields=["last_chain_check"])
    return checked, confirmed



import logging
import time
from dataclasses import dataclass
from typing import Callable, Dict, Optional

import requests

logger = logging.getLogger(__name__)

ERC20_TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"


def normalize_eth_address(address: Optional[str]) -> Optional[str]:
    if not address:
        return None
    addr = address.lower()
    if not addr.startswith("0x"):
        addr = f"0x{addr[-40:]}"
    return addr


@dataclass
class WatcherResult:
    confirmed: bool
    confirmations: int = 0
    amount: Optional[float] = None
    matched_address: bool = True
    meta: Optional[dict] = None


def blockcypher_watcher(tx_hash: str, wallet_address: str, config: dict) -> Optional[WatcherResult]:
    base_url = config.get("base_url", "https://api.blockcypher.com/v1/btc/main")
    min_conf = int(config.get("min_confirmations", 1))
    params = {}
    token = config.get("token")
    if token:
        params["token"] = token
    try:
        resp = requests.get(f"{base_url}/txs/{tx_hash}", params=params, timeout=10)
        if resp.status_code != 200:
            logger.warning("BlockCypher watcher failed %s %s", resp.status_code, resp.text)
            return None
        data = resp.json()
        confirmations = data.get("confirmations", 0)
        confirmed = confirmations >= min_conf
        matched_output = None
        for output in data.get("outputs", []):
            if wallet_address in output.get("addresses", []):
                matched_output = output
                break
        value = None
        if matched_output:
            value = matched_output.get("value")
            if value is not None:
                value = value / 1e8  # satoshis to BTC
        return WatcherResult(
            confirmed=confirmed,
            confirmations=confirmations,
            amount=value,
            matched_address=matched_output is not None,
            meta=data,
        )
    except requests.RequestException as exc:
        logger.error("BlockCypher watcher error: %s", exc)
        return None


def evm_watcher(tx_hash: str, wallet_address: str, config: dict) -> Optional[WatcherResult]:
    rpc_url = config.get("rpc_url")
    if not rpc_url:
        logger.debug("EVM watcher skipped due to missing rpc_url")
        return None
    min_conf = int(config.get("min_confirmations", 3))
    try:
        receipt_resp = requests.post(
            rpc_url,
            json={"jsonrpc": "2.0", "method": "eth_getTransactionReceipt", "params": [tx_hash], "id": 1},
            timeout=10,
        )
        receipt_data = receipt_resp.json()
        receipt = receipt_data.get("result")
        if not receipt:
            return None
        status_hex = receipt.get("status")
        if status_hex is None or int(status_hex, 16) != 1:
            return WatcherResult(
                confirmed=False,
                confirmations=0,
                matched_address=False,
                meta=receipt_data,
            )
        tx_to = receipt.get("to")
        matched = False
        normalized_wallet = normalize_eth_address(wallet_address)
        if normalized_wallet:
            if tx_to and normalize_eth_address(tx_to) == normalized_wallet:
                matched = True
            else:
                for log in receipt.get("logs", []):
                    topics = log.get("topics") or []
                    if topics and topics[0].lower() == ERC20_TRANSFER_TOPIC:
                        if len(topics) >= 3:
                            to_candidate = normalize_eth_address(topics[2])
                            if to_candidate == normalized_wallet:
                                matched = True
                                break
        block_hex = receipt.get("blockNumber")
        confirmations = 0
        if block_hex:
            latest_resp = requests.post(
                rpc_url,
                json={"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 2},
                timeout=10,
            )
            latest_data = latest_resp.json()
            latest_block_hex = latest_data.get("result")
            if latest_block_hex:
                latest_block = int(latest_block_hex, 16)
                tx_block = int(block_hex, 16)
                confirmations = max(latest_block - tx_block, 0)
        confirmed = confirmations >= min_conf
        return WatcherResult(
            confirmed=confirmed,
            confirmations=confirmations,
            matched_address=matched,
            meta={"receipt": receipt},
        )
    except requests.RequestException as exc:
        logger.error("EVM watcher error: %s", exc)
        return None


def tron_watcher(tx_hash: str, wallet_address: str, config: dict) -> Optional[WatcherResult]:
    base_url = config.get("base_url", "https://api.trongrid.io")
    headers = {}
    api_key = config.get("api_key")
    if api_key:
        headers["TRON-PRO-API-KEY"] = api_key
    try:
        resp = requests.get(f"{base_url}/v1/transactions/{tx_hash}", headers=headers, timeout=10)
        if resp.status_code != 200:
            logger.warning("Tron watcher failed %s %s", resp.status_code, resp.text)
            return None
        data = resp.json()
        if not data.get("data"):
            return None
        tx = data["data"][0]
        ret = tx.get("ret") or []
        success = ret and ret[0].get("contractRet") == "SUCCESS"
        confirmations = 1 if tx.get("confirmed") else 0
        confirmed = success and tx.get("confirmed")
        return WatcherResult(
            confirmed=confirmed,
            confirmations=confirmations,
            matched_address=True,
            meta=tx,
        )
    except requests.RequestException as exc:
        logger.error("Tron watcher error: %s", exc)
        return None


WATCHER_MAP: Dict[str, Callable[[str, str, dict], Optional[WatcherResult]]] = {
    "blockcypher": blockcypher_watcher,
    "evm": evm_watcher,
    "tron": tron_watcher,
}



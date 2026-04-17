"""
Agentic Wallet Login — OKX Onchain OS email OTP flow

Endpoints:
  POST /api/wallet/login   → send OTP to email via onchainos wallet login
  POST /api/wallet/verify  → verify OTP code, return wallet addresses
  GET  /api/wallet/status  → current wallet session state
  POST /api/wallet/logout  → clear wallet session
  GET  /api/wallet/balance → wallet balance on X Layer
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config import get_settings
from api.websocket import broadcast
import api.state as _state

log = structlog.get_logger(__name__)
router = APIRouter()
settings = get_settings()

ONCHAINOS = os.path.expanduser("~/.local/bin/onchainos")


# ── Request / Response models ─────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str  # EmailStr requires extra dep; plain str is fine here


class VerifyRequest(BaseModel):
    code: str


class WalletSession(BaseModel):
    logged_in: bool = False
    email: str | None = None
    account_id: str | None = None
    account_name: str | None = None
    xlayer_address: str | None = None
    evm_address: str | None = None


# ── In-memory session (single-tenant for hackathon demo) ─────────────────────

_session = WalletSession()


# ── onchainos helper ─────────────────────────────────────────────────────────

async def _run_onchainos(*args: str, timeout: int = 30) -> dict[str, Any] | None:
    """Execute onchainos CLI and return parsed JSON output."""
    cmd = [ONCHAINOS, *args]
    log.debug("onchainos.call", cmd=cmd)
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        if proc.returncode != 0:
            err = stderr.decode().strip()
            log.warning("onchainos.nonzero", cmd=cmd, returncode=proc.returncode, stderr=err)
            raise HTTPException(status_code=400, detail=err or "onchainos command failed")
        return json.loads(stdout.decode().strip())
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="onchainos timed out")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail=f"Invalid onchainos response: {exc}")


# ── Routes ───────────────────────────────────────────────────────────────────

@router.post("/login")
async def wallet_login(body: LoginRequest):
    """
    Step 1: Send OTP to user's email via onchainos wallet login.
    Uses OKX Agentic Wallet — no browser extension needed.
    """
    result = await _run_onchainos("wallet", "login", body.email)

    if not result or not result.get("ok"):
        raise HTTPException(status_code=400, detail="Failed to send OTP. Check email address.")

    # Store email in session for the verify step
    _session.email = body.email
    _session.logged_in = False

    log.info("wallet.otp_sent", email=body.email)
    return {"ok": True, "message": f"OTP sent to {body.email}"}


@router.post("/verify")
async def wallet_verify(body: VerifyRequest):
    """
    Step 2: Verify OTP code → establishes wallet session.
    Returns wallet addresses on success.
    """
    result = await _run_onchainos("wallet", "verify", body.code)

    if not result or not result.get("ok"):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP code.")

    data = result.get("data", {})
    _session.account_id = data.get("accountId")
    _session.account_name = data.get("accountName", "Account 1")
    _session.logged_in = True

    # Fetch wallet addresses
    addresses = await _run_onchainos("wallet", "addresses")
    xlayer_addr = None
    evm_addr = None
    if addresses and addresses.get("ok"):
        addr_data = addresses.get("data", {})
        xlayer_list = addr_data.get("xlayer", [])
        if xlayer_list:
            xlayer_addr = xlayer_list[0].get("address")
        evm_list = addr_data.get("evm", [])
        if evm_list:
            evm_addr = evm_list[0].get("address")

    _session.xlayer_address = xlayer_addr or evm_addr
    _session.evm_address = evm_addr

    # Update the treasury wallet address in settings and agent state
    if _session.xlayer_address:
        settings.treasury_wallet_address = _session.xlayer_address
        log.info("wallet.treasury_updated", address=_session.xlayer_address)

    # Broadcast wallet connected event to frontend
    await broadcast("wallet_connected", {
        "address": _session.xlayer_address,
        "email": _session.email,
        "account_name": _session.account_name,
    })

    log.info("wallet.verified", account=_session.account_name, address=_session.xlayer_address)
    return {
        "ok": True,
        "account_id": _session.account_id,
        "account_name": _session.account_name,
        "xlayer_address": _session.xlayer_address,
        "evm_address": _session.evm_address,
    }


@router.get("/status")
async def wallet_status():
    """Return current wallet session state."""
    if not _session.logged_in:
        # Check if onchainos has an active session
        try:
            result = await _run_onchainos("wallet", "status")
            if result and result.get("ok"):
                data = result.get("data", {})
                if data.get("loggedIn"):
                    _session.logged_in = True
                    _session.email = data.get("email")
                    _session.account_id = data.get("currentAccountId")
                    _session.account_name = data.get("currentAccountName")
                    # Also fetch addresses if we don't have them
                    if not _session.xlayer_address:
                        addrs = await _run_onchainos("wallet", "addresses")
                        if addrs and addrs.get("ok"):
                            addr_data = addrs.get("data", {})
                            xlayer_list = addr_data.get("xlayer", [])
                            if xlayer_list:
                                _session.xlayer_address = xlayer_list[0].get("address")
                            evm_list = addr_data.get("evm", [])
                            if evm_list:
                                _session.evm_address = evm_list[0].get("address")
        except HTTPException:
            pass  # onchainos not available

    return {
        "logged_in": _session.logged_in,
        "email": _session.email,
        "account_id": _session.account_id,
        "account_name": _session.account_name,
        "xlayer_address": _session.xlayer_address,
        "evm_address": _session.evm_address,
    }


@router.post("/logout")
async def wallet_logout():
    """Clear wallet session and logout from onchainos."""
    try:
        await _run_onchainos("wallet", "logout")
    except HTTPException:
        pass  # best effort

    _session.logged_in = False
    _session.email = None
    _session.account_id = None
    _session.account_name = None
    _session.xlayer_address = None
    _session.evm_address = None

    return {"ok": True, "message": "Logged out"}


@router.get("/balance")
async def wallet_balance():
    """Fetch wallet balance on X Layer."""
    if not _session.logged_in or not _session.xlayer_address:
        raise HTTPException(status_code=401, detail="No wallet connected")

    result = await _run_onchainos("wallet", "balance", "--chain", "xlayer")

    if not result or not result.get("ok"):
        raise HTTPException(status_code=502, detail="Failed to fetch balance")

    data = result.get("data", {})
    return {
        "address": _session.xlayer_address,
        "total_value_usd": data.get("totalValueUsd", "0"),
        "tokens": data.get("details", [{}])[0].get("tokenAssets", []) if data.get("details") else [],
    }

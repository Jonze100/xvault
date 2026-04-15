"""
XVault Configuration — Pydantic Settings
All values loaded from environment / .env file
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_env: str = "development"
    app_secret_key: str = "change-me-in-production"
    cors_origins: str = "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:3003,http://localhost:3004,http://localhost:3005"

    # Anthropic
    anthropic_api_key: str = Field(..., description="Anthropic API key for agent reasoning")

    # OKX
    okx_api_key: str = ""
    okx_secret_key: str = ""
    okx_passphrase: str = ""
    okx_project_id: str = ""
    okx_base_url: str = "https://www.okx.com"

    # X Layer
    xlayer_rpc_url: str = "https://rpc.xlayer.tech"
    xlayer_chain_id: int = 196

    # MCP Server
    mcp_server_url: str = "http://localhost:3001"
    mcp_api_key: str = ""

    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    database_url: str = ""

    # x402
    x402_facilitator_url: str = "https://facilitator.cdp.coinbase.com"
    x402_network: str = "base-sepolia"

    # Agent Wallets — private keys for signing
    signal_agent_private_key: str = ""
    risk_agent_private_key: str = ""
    execution_agent_private_key: str = ""
    portfolio_agent_private_key: str = ""
    economy_agent_private_key: str = ""
    treasury_wallet_address: str = ""
    treasury_wallet_private_key: str = ""

    # Agent Wallet Addresses (derived from private keys or set directly)
    signal_agent_wallet_address: str = ""
    risk_agent_wallet_address: str = ""
    execution_agent_wallet_address: str = ""
    portfolio_agent_wallet_address: str = ""
    # Economy Agent master wallet — registered via `onchainos wallet login`
    economy_agent_wallet_address: str = "0xb5c600f74627c63476f7a7e89a6a616723783fce"

    # x402 service provider address (receives agent purchase payments)
    service_provider_address: str = ""

    # Agent Intervals
    signal_agent_interval: int = 300       # 5 min
    portfolio_agent_interval: int = 300    # 5 min
    economy_agent_interval: int = 900      # 15 min

    # Risk Thresholds
    max_trade_size_usd: float = 10_000
    min_security_score: int = 80
    max_portfolio_concentration: float = 0.25

    # Economy
    performance_fee_bps: int = 1000        # 10%

    # Redis
    redis_url: str = "redis://localhost:6379"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()

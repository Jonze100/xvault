// EIP-1193 provider interface (MetaMask, OKX, Brave, Coinbase, etc.)
interface EIP1193Provider {
  request: (args: { method: string; params?: unknown[] }) => Promise<unknown>;
  on: (event: string, handler: (...args: unknown[]) => void) => void;
  removeListener: (event: string, handler: (...args: unknown[]) => void) => void;
  selectedAddress?: string | null;
  chainId?: string | null;
  isMetaMask?: boolean;
  isOKXWallet?: boolean;
}

interface Window {
  // OKX Wallet extension
  okxwallet?: {
    ethereum: EIP1193Provider;
  };
  // Standard EIP-1193 injected provider (MetaMask, Brave, Coinbase, etc.)
  ethereum?: EIP1193Provider;
}

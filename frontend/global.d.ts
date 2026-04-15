// OKX Wallet browser extension — injected into window
interface OKXEthereum {
  request: (args: { method: string; params?: unknown[] }) => Promise<unknown>;
  on: (event: string, handler: (...args: unknown[]) => void) => void;
  removeListener: (event: string, handler: (...args: unknown[]) => void) => void;
  selectedAddress: string | null;
  chainId: string | null;
}

interface Window {
  okxwallet?: {
    ethereum: OKXEthereum;
  };
}

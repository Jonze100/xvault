import Link from "next/link";
import { Vault, ArrowLeft } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-6 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted">
        <Vault className="h-8 w-8 text-muted-foreground" />
      </div>
      <div>
        <h2 className="text-xl font-semibold text-foreground">
          Page not found
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          The page you&apos;re looking for doesn&apos;t exist in XVault.
        </p>
      </div>
      <Link
        href="/dashboard"
        className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Dashboard
      </Link>
    </div>
  );
}

import Link from 'next/link';

export function Footer() {
  return (
    <footer
      className="border-t py-6 md:py-0"
      data-testid="app-footer"
      role="contentinfo"
    >
      <div className="container flex flex-col items-center justify-between gap-4 md:h-16 md:flex-row">
        <p className="text-center text-sm leading-loose text-muted-foreground md:text-left">
          © {new Date().getFullYear()} Admin UI. All rights reserved.
        </p>
        <div className="flex items-center space-x-4 text-sm text-muted-foreground">
          <Link
            href="/privacy"
            className="hover:underline"
            data-testid="footer-link-privacy"
            aria-label="View privacy policy"
          >
            Privacy
          </Link>
          <Link
            href="/terms"
            className="hover:underline"
            data-testid="footer-link-terms"
            aria-label="View terms of service"
          >
            Terms
          </Link>
        </div>
      </div>
    </footer>
  );
}


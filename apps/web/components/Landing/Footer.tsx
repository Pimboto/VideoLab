"use client";

import { Link } from "@heroui/link";

export default function Footer() {
  return (
    <footer className="w-full flex items-center justify-center py-6 border-t border-divider">
      <div className="flex items-center gap-1 text-default-600">
        <span>Powered by</span>
        <Link className="text-primary font-semibold" href="https://heroui.com">
          HeroUI
        </Link>
        <span>+</span>
        <Link className="text-primary font-semibold" href="https://nextjs.org">
          Next.js
        </Link>
        <span>+</span>
        <Link
          className="text-primary font-semibold"
          href="https://fastapi.tiangolo.com"
        >
          FastAPI
        </Link>
      </div>
    </footer>
  );
}

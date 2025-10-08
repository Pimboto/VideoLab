"use client";

import { Link } from "@heroui/link";

export default function Footer() {
  return (
    <footer className="w-full flex items-center justify-center py-6 border-t border-divider">
      <div className="flex items-center gap-1 text-default-600">
        <span>Powered by</span>
        <Link
          href="https://heroui.com"
          className="text-primary font-semibold"
        >
          HeroUI
        </Link>
        <span>+</span>
        <Link
          href="https://nextjs.org"
          className="text-primary font-semibold"
        >
          Next.js
        </Link>
        <span>+</span>
        <Link
          href="https://fastapi.tiangolo.com"
          className="text-primary font-semibold"
        >
          FastAPI
        </Link>
      </div>
    </footer>
  );
}


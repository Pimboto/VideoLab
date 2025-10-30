"use client";

import { Button } from "@heroui/button";
import { Chip } from "@heroui/chip";
import { Link } from "@heroui/link";
import {
  PlayIcon,
  ArrowRightIcon,
  CheckCircleIcon,
} from "@heroicons/react/24/outline";
import { SignedIn, SignedOut } from "@clerk/nextjs";

import DarkVeil from "./DarkVeil";
import BlurText from "./BlurText";

import { siteConfig } from "@/config/site";
import { title, subtitle } from "@/components/primitives";

export default function Hero() {
  return (
    <div className="relative min-h-screen overflow-hidden">
      {/* Fondo DarkVeil */}
      <div className="absolute inset-0 z-0">
        <div className="w-full h-full relative">
          <DarkVeil
            hueShift={0}
            noiseIntensity={0}
            scanlineFrequency={5}
            scanlineIntensity={0.04}
            speed={1.6}
            warpAmount={5}
          />
        </div>
        <div className="absolute inset-0 bg-gradient-to-br from-background/50 via-background/30 to-background/60" />
      </div>

      {/* Contenido Hero */}
      <div className="relative z-10 flex flex-col items-center justify-center text-center py-16 md:py-24 min-h-screen">
        <div className="max-w-4xl mx-auto px-6">
          <div className="flex justify-center mb-6">
            <Chip
              color="primary"
              startContent={<CheckCircleIcon className="w-4 h-4" />}
              variant="flat"
            >
              Video Repurpose Tool
            </Chip>
          </div>

          <BlurText
            animateBy="words"
            className={title({ size: "lg" })}
            delay={100}
            direction="top"
            text="Create Different Videos from One Source"
          />

          <p className={subtitle({ class: "mt-6 text-lg max-w-2xl mx-auto" })}>
            Combine videos, text, and audio automatically. Process hundreds of
            videos simultaneously with our professional and modern repurpose
            tool.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 mt-8 justify-center">
            {/* Mostrar botones según estado de autenticación */}
            <SignedOut>
              <Button
                as={Link}
                className="font-semibold"
                color="primary"
                endContent={<ArrowRightIcon className="w-4 h-4" />}
                href="/sign-up"
                size="lg"
              >
                Get Started Free
              </Button>
              <Button
                as={Link}
                className="font-semibold"
                href="/sign-in"
                size="lg"
                variant="bordered"
              >
                Sign In
              </Button>
            </SignedOut>

            <SignedIn>
              <Button
                as={Link}
                className="font-semibold"
                color="primary"
                endContent={<ArrowRightIcon className="w-4 h-4" />}
                href="/dashboard"
                size="lg"
              >
                Go to Dashboard
              </Button>
              <Button
                as={Link}
                className="font-semibold"
                href={siteConfig.links.github}
                size="lg"
                startContent={<PlayIcon className="w-4 h-4" />}
                variant="bordered"
              >
                View Documentation
              </Button>
            </SignedIn>
          </div>
        </div>
      </div>
    </div>
  );
}

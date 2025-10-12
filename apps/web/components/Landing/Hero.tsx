"use client";

import { Button } from "@heroui/button";
import { Chip } from "@heroui/chip";
import { Link } from "@heroui/link";
import {
  PlayIcon,
  ArrowRightIcon,
  CheckCircleIcon,
} from "@heroicons/react/24/outline";

import { siteConfig } from "@/config/site";
import { title, subtitle } from "@/components/primitives";
import DarkVeil from "./DarkVeil";
import BlurText from "./BlurText";
import { useTheme } from "next-themes";

export default function Hero() {
  const { theme } = useTheme();
  const isLight = theme === "light";

  return (
    <div className="relative min-h-screen overflow-hidden">
      {/* Fondo DarkVeil */}
      <div className="absolute inset-0 z-0">
        <div className="w-full h-full relative" >
          <DarkVeil speed={1.6} hueShift={0} noiseIntensity={0} scanlineFrequency={5} scanlineIntensity={0.04} warpAmount={5} />
        </div>
        <div className="absolute inset-0 bg-gradient-to-br from-background/50 via-background/30 to-background/60" />
      </div>

      {/* Contenido Hero */}
      <div className="relative z-10 flex flex-col items-center justify-center text-center py-16 md:py-24 min-h-screen">
        <div className="max-w-4xl mx-auto px-6">
          <div className="flex justify-center mb-6">
            <Chip
              color="primary"
              variant="flat"
              startContent={<CheckCircleIcon className="w-4 h-4" />}
            >
              Video Repurpose Tool
            </Chip>
          </div>

          <BlurText
            text="Create Different Videos from One Source"
            delay={100}
            animateBy="words"
            direction="top"
            className={title({ size: "lg" })}
          />

          <p className={subtitle({ class: "mt-6 text-lg max-w-2xl mx-auto" })}>
            Combine videos, text, and audio automatically. Process hundreds of
            videos simultaneously with our professional and modern repurpose
            tool.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 mt-8 justify-center">
            <Button
              as={Link}
              href="/dashboard"
              color="primary"
              size="lg"
              className="font-semibold"
              endContent={<ArrowRightIcon className="w-4 h-4" />}
            >
              Go to Dashboard
            </Button>
            <Button
              as={Link}
              href={siteConfig.links.github}
              variant="bordered"
              size="lg"
              className="font-semibold"
              startContent={<PlayIcon className="w-4 h-4" />}
            >
              View Documentation
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

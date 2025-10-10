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
  return (
    <div className="relative min-h-screen overflow-hidden">
      {/* Fondo Silk */}
      <div className="absolute inset-0 z-0">
       {/*  <Silk
          speed={5}
          scale={1}
          color="#7c3aed"
          noiseIntensity={1.5}
          rotation={0}
        /> */}
        <div className="absolute inset-0 bg-gradient-to-br from-background/90 via-background/70 to-background/90" />
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

          <h1 className={title({ size: "lg" })}>
            Create Different Videos{" "}
            <span className={title({ color: "violet", size: "lg" })}>
              from One Source
            </span>
          </h1>

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

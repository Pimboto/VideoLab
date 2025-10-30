"use client";

import { Card, CardBody } from "@heroui/card";
import {
  ArrowUpTrayIcon as UploadIcon,
  Cog6ToothIcon as CpuChipIcon,
  ClockIcon,
  VideoCameraIcon,
} from "@heroicons/react/24/outline";

import { title, subtitle } from "@/components/primitives";

export default function Features() {
  const features = [
    {
      icon: <VideoCameraIcon className="w-6 h-6" />,
      title: "Video Processing",
      description:
        "Combine videos with text and audio automatically and professionally",
    },
    {
      icon: <CpuChipIcon className="w-6 h-6" />,
      title: "Batch Processing",
      description:
        "Process multiple videos simultaneously with different combinations",
    },
    {
      icon: <UploadIcon className="w-6 h-6" />,
      title: "File Management",
      description:
        "Upload, organize and manage videos, audios and CSV files easily",
    },
    {
      icon: <ClockIcon className="w-6 h-6" />,
      title: "Real-time Monitoring",
      description: "Track your job progress with live updates",
    },
  ];

  return (
    <section className="py-16">
      <div className="container mx-auto max-w-7xl px-6">
        <div className="text-center mb-12">
          <h2 className={title({ size: "md" })}>Key Features</h2>
          <p className={subtitle({ class: "mt-4 max-w-2xl mx-auto" })}>
            Everything you need to process videos professionally
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, index) => (
            <Card
              key={index}
              className="bg-background/60 backdrop-blur-sm border-none"
            >
              <CardBody className="text-center p-6">
                <div className="text-primary mb-4 flex justify-center">
                  {feature.icon}
                </div>
                <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                <p className="text-default-600 text-sm">
                  {feature.description}
                </p>
              </CardBody>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}

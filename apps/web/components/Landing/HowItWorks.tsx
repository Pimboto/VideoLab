"use client";

import { title, subtitle } from "@/components/primitives";

export default function HowItWorks() {
  const steps = [
    {
      number: "01",
      title: "Upload Your Files",
      description: "Videos, audios and CSV files with your texts"
    },
    {
      number: "02", 
      title: "Configure Processing",
      description: "Choose position, style and rendering parameters"
    },
    {
      number: "03",
      title: "Start Batch",
      description: "Process multiple combinations automatically"
    },
    {
      number: "04",
      title: "Download Results",
      description: "Get your processed videos ready to use"
    }
  ];

  return (
    <section className="py-16">
      <div className="container mx-auto max-w-7xl px-6">
        <div className="text-center mb-12">
          <h2 className={title({ size: "md" })}>
            How It Works
          </h2>
          <p className={subtitle({ class: "mt-4 max-w-2xl mx-auto" })}>
            Simple 4-step process to get professional results
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {steps.map((step, index) => (
            <div key={index} className="text-center">
              <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-primary">
                  {step.number}
                </span>
              </div>
              <h3 className="text-lg font-semibold mb-2">
                {step.title}
              </h3>
              <p className="text-default-600 text-sm">
                {step.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

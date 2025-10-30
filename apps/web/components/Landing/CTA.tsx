"use client";

import { Button } from "@heroui/button";
import { Card, CardBody } from "@heroui/card";
import { Link } from "@heroui/link";
import { ArrowRightIcon, DocumentTextIcon } from "@heroicons/react/24/outline";

import { title, subtitle } from "@/components/primitives";

export default function CTA() {
  return (
    <section className="py-16">
      <div className="container mx-auto max-w-7xl px-6">
        <Card className="bg-gradient-to-r from-primary/10 to-secondary/10 backdrop-blur-sm border-none">
          <CardBody className="p-12 text-center">
            <h2 className={title({ size: "md" })}>Ready to Process Videos?</h2>
            <p className={subtitle({ class: "mt-4 max-w-2xl mx-auto" })}>
              Start processing videos professionally with our repurpose tool
            </p>
            <div className="flex flex-col sm:flex-row gap-4 mt-8 justify-center">
              <Button
                as={Link}
                className="font-semibold"
                color="primary"
                endContent={<ArrowRightIcon className="w-4 h-4" />}
                href="/dashboard"
                size="lg"
              >
                Start Now
              </Button>
              <Button
                as={Link}
                className="font-semibold"
                href="http://localhost:8000/docs"
                size="lg"
                startContent={<DocumentTextIcon className="w-4 h-4" />}
                variant="bordered"
              >
                View API Docs
              </Button>
            </div>
          </CardBody>
        </Card>
      </div>
    </section>
  );
}

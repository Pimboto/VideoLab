"use client";

import { Card, CardBody } from "@heroui/card";
import { 
  ArrowUpTrayIcon as UploadIcon, 
  Cog6ToothIcon as CpuChipIcon, 
  ClockIcon
} from "@heroicons/react/24/outline";

import { title, subtitle } from "@/components/primitives";

export default function ApiFeatures() {
  return (
    <section className="py-16">
      <div className="container mx-auto max-w-7xl px-6">
        <div className="text-center mb-12">
          <h2 className={title({ size: "md" })}>
            Complete REST API
          </h2>
          <p className={subtitle({ class: "mt-4 max-w-2xl mx-auto" })}>
            Professional endpoints for integration with any application
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <Card className="bg-background/60 backdrop-blur-sm border-none">
            <CardBody className="p-6">
              <div className="flex items-center mb-4">
                <UploadIcon className="w-6 h-6 text-primary mr-3" />
                <h3 className="text-lg font-semibold">Upload & Management</h3>
              </div>
              <ul className="space-y-2 text-sm text-default-600">
                <li>• Upload videos, audios and CSV</li>
                <li>• Organize in folders</li>
                <li>• List and delete files</li>
                <li>• Automatic validation</li>
              </ul>
            </CardBody>
          </Card>

          <Card className="bg-background/60 backdrop-blur-sm border-none">
            <CardBody className="p-6">
              <div className="flex items-center mb-4">
                <CpuChipIcon className="w-6 h-6 text-primary mr-3" />
                <h3 className="text-lg font-semibold">Processing</h3>
              </div>
              <ul className="space-y-2 text-sm text-default-600">
                <li>• Individual processing</li>
                <li>• Massive batch processing</li>
                <li>• Multiple style presets</li>
                <li>• Flexible configuration</li>
              </ul>
            </CardBody>
          </Card>

          <Card className="bg-background/60 backdrop-blur-sm border-none">
            <CardBody className="p-6">
              <div className="flex items-center mb-4">
                <ClockIcon className="w-6 h-6 text-primary mr-3" />
                <h3 className="text-lg font-semibold">Monitoring</h3>
              </div>
              <ul className="space-y-2 text-sm text-default-600">
                <li>• Real-time status</li>
                <li>• Detailed progress</li>
                <li>• Job history</li>
                <li>• Automatic notifications</li>
              </ul>
            </CardBody>
          </Card>
        </div>
      </div>
    </section>
  );
}

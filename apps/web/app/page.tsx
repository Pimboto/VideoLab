"use client";

import { Navbar } from "@/components/navbar";
import Hero from "@/components/Landing/Hero";
import Features from "@/components/Landing/Features";
import HowItWorks from "@/components/Landing/HowItWorks";
import ApiFeatures from "@/components/Landing/ApiFeatures";
import CTA from "@/components/Landing/CTA";
import Footer from "@/components/Landing/Footer";

export default function Home() {
  return (
    <div className="relative min-h-screen">
      <Navbar />
      <Hero />
      <Features />
      <HowItWorks />
      <ApiFeatures />
      <CTA />
      <Footer />
    </div>
  );
}

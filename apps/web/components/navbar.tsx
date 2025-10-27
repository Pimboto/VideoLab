import {
  Navbar as HeroUINavbar,
  NavbarContent,
  NavbarBrand,
  NavbarItem,
} from "@heroui/navbar";
import { Button } from "@heroui/button";
import { Link } from "@heroui/link";
import NextLink from "next/link";
import { SignedIn, SignedOut, UserButton } from "@clerk/nextjs";

import { siteConfig } from "@/config/site";
import { ThemeSwitch } from "@/components/theme-switch";
import {
  TwitterIcon,
  GithubIcon,
  DiscordIcon,
  Logo,
} from "@/components/icons";
import Image from "next/image";

export const Navbar = () => {
  return (
    <HeroUINavbar maxWidth="xl" position="sticky">
      <NavbarContent className="basis-1/5 sm:basis-full" justify="start">
        <NavbarBrand as="li" className="gap-3 max-w-fit">
          <NextLink className="flex justify-start items-center gap-1" href="/">
          <Image
              src="/videolab-logo.png"
              alt="VideoLab"
              width={40}
              height={40}
              className="object-cover"
            />
            <p className="font-bold text-inherit">VideoLab</p>
          </NextLink>
        </NavbarBrand>
        <ul className="hidden lg:flex gap-4 justify-start ml-2">
{/*           <NavbarItem>
            <NextLink
              className="text-foreground hover:text-primary transition-colors"
              href="/"
            >
              Home
            </NextLink>
          </NavbarItem> */}
        </ul>
      </NavbarContent>

      <NavbarContent
        className="hidden sm:flex basis-1/5 sm:basis-full"
        justify="end"
      >
        <NavbarItem className="hidden sm:flex gap-2">
          <Link isExternal aria-label="Twitter" href={siteConfig.links.twitter}>
            <TwitterIcon className="text-default-500 hover:text-primary transition-colors" />
          </Link>
          <Link isExternal aria-label="Discord" href={siteConfig.links.discord}>
            <DiscordIcon className="text-default-500 hover:text-primary transition-colors" />
          </Link>
          <Link isExternal aria-label="Github" href={siteConfig.links.github}>
            <GithubIcon className="text-default-500 hover:text-primary transition-colors" />
          </Link>
          <ThemeSwitch />
        </NavbarItem>
        
        {/* Mostrar botones según estado de autenticación */}
        <SignedOut>
          <NavbarItem className="hidden md:flex gap-2">
            <Button
              as={Link}
              className="text-sm font-medium"
              href="/sign-in"
              variant="flat"
            >
              Sign In
            </Button>
            <Button
              as={Link}
              className="text-sm font-medium"
              color="primary"
              href="/sign-up"
              variant="solid"
            >
              Sign Up
            </Button>
          </NavbarItem>
        </SignedOut>
        
        <SignedIn>
          <NavbarItem className="hidden md:flex gap-3">
            <Button
              as={Link}
              className="text-sm font-medium"
              color="primary"
              href="/dashboard"
              variant="solid"
            >
              Dashboard
            </Button>
            <UserButton 
              appearance={{
                elements: {
                  avatarBox: "w-9 h-9"
                }
              }}
            />
          </NavbarItem>
        </SignedIn>
      </NavbarContent>

      <NavbarContent className="sm:hidden basis-1 pl-4" justify="end">
        <Link isExternal aria-label="Github" href={siteConfig.links.github}>
          <GithubIcon className="text-default-500" />
        </Link>
        <ThemeSwitch />
      </NavbarContent>
    </HeroUINavbar>
  );
};

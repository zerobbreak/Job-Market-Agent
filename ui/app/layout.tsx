import type { Metadata } from "next"
import { Geist, Geist_Mono } from "next/font/google"
import { Analytics } from "@vercel/analytics/next"
import "./globals.css"

const _geist = Geist({ subsets: ["latin"] })
const _geistMono = Geist_Mono({ subsets: ["latin"] })

export const metadata: Metadata = {
    title: "Job Market Agent - AI-Powered Job Application Assistant",
    description: "Streamline your job search with AI-powered CV optimization, ATS analysis, cover letter generation, and interview preparation across 20+ job platforms",
    generator: "Job Market Agent",
    keywords: ["job search", "AI career tools", "CV optimization", "ATS", "cover letter", "interview prep", "job applications"],
    authors: [{ name: "Job Market Agent Team" }],
    icons: {
        icon: [
            {
                url: "/icon-light-32x32.png",
                media: "(prefers-color-scheme: light)",
            },
            {
                url: "/icon-dark-32x32.png",
                media: "(prefers-color-scheme: dark)",
            },
            {
                url: "/icon.svg",
                type: "image/svg+xml",
            },
        ],
        apple: "/apple-icon.png",
    },
    openGraph: {
        title: "Job Market Agent - AI-Powered Job Application Assistant",
        description: "Streamline your job search with AI-powered optimization tools",
        type: "website",
    },
}

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode
}>) {
    return (
        <html lang="en">
            <body className={`font-sans antialiased`}>
                {children}
                <Analytics />
            </body>
        </html>
    )
}

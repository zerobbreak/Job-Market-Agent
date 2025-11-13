"use client"

import type React from "react"

import { ArrowRightStartOnRectangleIcon, Bars3Icon, Cog8ToothIcon } from "@heroicons/react/16/solid"
import { useEffect, useId, useState } from "react"
import { Form, Link, useLocation } from "react-router"
import type { AuthenticatedUser } from "../../../@types/auth.types"
import { ariaLabels, SkipToMainContent } from "~/components/ui/aria-labels"
import {
    Dropdown,
    DropdownButton,
    DropdownDivider,
    DropdownItem,
    DropdownLabel,
    DropdownMenu,
} from "~/components/ui/dropdown"
import SettingsModal from "~/components/ui/settings-modal"
import { useLocalStorage, useToggle } from "~/hooks"
import { getBrandAssets, getBrandContent } from "~/mocks/mock-brand"

const navItems = [
    { label: "Jobs", url: "/jobs" },
    { label: "Learn", url: "/learn" },
]

export default function AppShell({
    user,
    children,
}: {
    user: AuthenticatedUser | null
    children: React.ReactNode
}) {
    const { value: isMobileMenuOpen, toggle: toggleMobileMenu } = useToggle(false)
    const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false)
    const mainContentId = useId()
    const brandContent = getBrandContent()
    const brandAssets = getBrandAssets()
    const [authData] = useLocalStorage<{ accessToken: string } | null>("auth", null)
    const location = useLocation()
    const isLandingPage = location.pathname === "/"

    // Simplified auth state management - trust the server-side user prop
    // Server-side rendering provides the authoritative user state
    const [actualUser, setActualUser] = useState(user)

    useEffect(() => {
        // Only update if user prop changes (from server-side auth)
        setActualUser(user)
    }, [user])

    // Helper to check if a nav item is active
    const isActiveRoute = (url: string) => {
        if (url === "/jobs") {
            return location.pathname.startsWith("/jobs")
        }
        if (url === "/learn") {
            return location.pathname.startsWith("/learn")
        }
        return location.pathname === url
    }

    return (
        <div className="min-h-screen bg-[#fcfbf8] flex flex-col">
            <SkipToMainContent targetId={mainContentId} />
            {/* Header (hidden on landing page) */}
            {!isLandingPage && (
                <header className="bg-[#fcfbf8] border-b border-[#edebe5] mb-8">
                    <div className="penpot-container py-6 flex items-center justify-between">
                        {/* Left: Logo - Clickable */}
                        <Link 
                            to={actualUser ? "/jobs" : "/"} 
                            className="flex items-center gap-4 hover:opacity-80 transition-opacity"
                        >
                            <img
                                src={brandAssets.logo || "/placeholder.svg"}
                                alt={`${brandContent.appName} Logo`}
                                className="h-8 w-8 object-contain"
                            />
                            <h1 className="text-2xl font-semibold text-[#151515]">
                                {brandContent.appName}
                            </h1>
                        </Link>

                        {/* Center: Navigation */}
                        <nav
                            className="hidden md:flex items-center gap-8"
                            aria-label={ariaLabels.mainNavigation}
                        >
                            {navItems.map(({ label, url }) => {
                                const isActive = isActiveRoute(url)
                                return (
                                    <Link
                                        key={label}
                                        to={url}
                                        className={`transition-colors px-2 py-1 font-medium ${
                                            isActive 
                                                ? "text-[#4b92ff] border-b-2 border-[#4b92ff]" 
                                                : "text-[#151515] hover:text-[#4b92ff]"
                                        }`}
                                        aria-label={`Navigate to ${label}`}
                                        aria-current={isActive ? "page" : undefined}
                                    >
                                        {label}
                                    </Link>
                                )
                            })}
                        </nav>

                        {/* Right: User & Mobile Menu */}
                        <div className="flex items-center gap-4">
                            {/* Mobile Menu Button */}
                            <button
                                type="button"
                                className="md:hidden p-2 rounded-lg text-[#151515] hover:bg-gray-100 transition-colors"
                                onClick={toggleMobileMenu}
                                aria-label="Toggle mobile menu"
                            >
                                <Bars3Icon className="w-6 h-6" />
                            </button>
                            {actualUser ? (
                                <Dropdown>
                                    <DropdownButton
                                        as="button"
                                        className="flex items-center gap-3 px-3 py-2 bg-[#fcfbf8] hover:bg-[#edebe5] rounded-lg border-none text-[#151515] font-medium"
                                    >
                                        <div className="w-10 h-10 bg-[#4b92ff] rounded-full flex items-center justify-center flex-shrink-0">
                                            <span className="text-white font-semibold text-sm">
                                                {actualUser.first_name?.charAt(0)?.toUpperCase() || "U"}
                                                {actualUser.last_name?.charAt(0)?.toUpperCase() || "S"}
                                            </span>
                                        </div>
                                        <div className="hidden sm:flex flex-col items-start min-w-0">
                                            <span className="text-[#151515] font-medium text-sm truncate">
                                                {actualUser.first_name} {actualUser.last_name}'s
                                                Workspace
                                            </span>
                                            <span className="text-xs text-[#7a7a7a] truncate">
                                                {actualUser.email}
                                            </span>
                                        </div>
                                    </DropdownButton>
                                    <DropdownMenu className="min-w-64" anchor="bottom end">
                                        <DropdownItem onClick={() => setIsSettingsModalOpen(true)}>
                                            <Cog8ToothIcon />
                                            <DropdownLabel>Settings</DropdownLabel>
                                        </DropdownItem>
                                        <DropdownDivider />
                                        <Form method="post" action="/logout">
                                            <button
                                                type="submit"
                                                className="w-full flex items-center gap-2 px-3.5 py-2.5 hover:bg-[#edebe5] rounded-lg text-left text-[#151515] text-base/6 sm:text-sm/6"
                                            >
                                                <ArrowRightStartOnRectangleIcon className="w-5 h-5 mr-2.5 -ml-0.5" />
                                                Sign out
                                            </button>
                                        </Form>
                                    </DropdownMenu>
                                </Dropdown>
                            ) : (
                                <>
                                    <Link
                                        to="/register"
                                        className="text-[#151515] hover:text-[#4b92ff] transition-colors"
                                    >
                                        Sign Up
                                    </Link>
                                    <Link
                                        to="/login"
                                        className="bg-[#151515] text-white px-4 py-2 rounded-lg hover:bg-gray-800 transition-colors"
                                    >
                                        Sign In
                                    </Link>
                                </>
                            )}
                        </div>
                    </div>

                    {/* Mobile Menu */}
                    {isMobileMenuOpen && (
                        <div className="md:hidden border-t border-[#edebe5] bg-white">
                            <div className="penpot-container py-4">
                                <nav className="flex flex-col gap-2" aria-label="Mobile navigation">
                                    {navItems.map(({ label, url }) => {
                                        const isActive = isActiveRoute(url)
                                        return (
                                            <Link
                                                key={label}
                                                to={url}
                                                className={`transition-colors py-3 px-4 rounded-lg font-medium ${
                                                    isActive 
                                                        ? "bg-[#4b92ff] text-white" 
                                                        : "text-[#151515] hover:bg-[#edebe5]"
                                                }`}
                                                onClick={toggleMobileMenu}
                                                aria-label={`Navigate to ${label}`}
                                                aria-current={isActive ? "page" : undefined}
                                            >
                                                {label}
                                            </Link>
                                        )
                                    })}
                                    {!actualUser && (
                                        <div className="border-t border-[#edebe5] pt-4 mt-2 space-y-2">
                                            <Link
                                                to="/register"
                                                className="block text-[#151515] hover:bg-[#edebe5] transition-colors py-3 px-4 rounded-lg font-medium"
                                                onClick={toggleMobileMenu}
                                            >
                                                Sign Up
                                            </Link>
                                            <Link
                                                to="/login"
                                                className="block bg-[#151515] text-white py-3 px-4 rounded-lg hover:bg-gray-800 transition-colors font-medium text-center"
                                                onClick={toggleMobileMenu}
                                            >
                                                Sign In
                                            </Link>
                                        </div>
                                    )}
                                </nav>
                            </div>
                        </div>
                    )}
                </header>
            )}

            {/* Main content */}
            <main
                id={mainContentId}
                className={isLandingPage ? "flex-1" : "penpot-container py-12 flex-1"}
            >
                {children}
            </main>

            {/* Footer */}
            {!isLandingPage && (
                <div className="mt-8">
                    <footer className="bg-[#fcfbf8] border-t border-[#edebe5]">
                        <div className="penpot-container py-6">
                            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                                <div className="text-sm text-[#7a7a7a]">
                                    © {new Date().getFullYear()} {brandContent.appName}. {brandContent.tagline}
                                </div>
                                <div className="flex items-center gap-4 text-sm">
                                    <Link to="/learn" className="text-[#7a7a7a] hover:text-[#151515]">
                                        Learn
                                    </Link>
                                    <button
                                        type="button"
                                        className="text-[#7a7a7a] hover:text-[#151515]"
                                        onClick={() => setIsSettingsModalOpen(true)}
                                    >
                                        Settings
                                    </button>
                                    <a
                                        href="mailto:support@jobmarketagent.com"
                                        className="text-[#7a7a7a] hover:text-[#151515]"
                                    >
                                        Support
                                    </a>
                                </div>
                            </div>
                        </div>
                    </footer>
                </div>
            )}

            {/* Settings Modal */}
            {(() => {
                const currentUser = actualUser || user
                return currentUser ? (
                    <SettingsModal
                        isOpen={isSettingsModalOpen}
                        onClose={() => setIsSettingsModalOpen(false)}
                        user={currentUser}
                        accessToken={authData?.accessToken || undefined}
                    />
                ) : null
            })()}
        </div>
    )
}

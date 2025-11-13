"use client"

import { EyeIcon, EyeSlashIcon } from "@heroicons/react/16/solid"
import { useId, useState } from "react"
import { Form, Link, redirect, useSearchParams } from "react-router"
import { safeRedirect } from "remix-utils/safe-redirect"
import type { AuthSessionData, SignInResult } from "@/types/auth.types"
import { Button } from "~/components/ui/button"
import { Field, Label } from "~/components/ui/fieldset"
import { Input, InputGroup } from "~/components/ui/input"
import { signIn } from "~/services/auth.client"
import { validateEmail } from "~/utils/validation"
import type { Route } from "./+types/login"

export async function clientLoader(_args: Route.ClientLoaderArgs) {
    if (typeof window !== "undefined") {
        const storedAuth = localStorage.getItem("auth")
        if (storedAuth) {
            try {
                const authData = JSON.parse(storedAuth)
                if (authData.user && authData.accessToken) {
                    return redirect("/jobs")
                }
            } catch (error) {
                console.warn("[Login] Invalid auth data in localStorage:", error)
                localStorage.removeItem("auth")
            }
        }
    }
    return null
}

export async function clientAction({ request }: Route.ClientActionArgs) {
    try {
        const formData = await request.formData()
        const email = formData.get("email")
        const password = formData.get("password")

        if (!email || !password) {
            return { error: "Email and password are required" }
        }

        if (typeof email !== "string" || typeof password !== "string") {
            return { error: "Email and password must be strings" }
        }

        const result = (await signIn(request, { email, password })) as SignInResult

        if (result.user) {
            const authData: AuthSessionData = {
                user: result.user,
                accessToken: result.accessToken,
                refreshToken: result.refreshToken,
                issuedAt: result.issuedAt,
                expiresAt: result.expiresAt,
            }
            localStorage.setItem("auth", JSON.stringify(authData))
        }

        const destination = safeRedirect(result.returnTo ?? "/jobs", "/jobs")
        return redirect(destination, { headers: result.headers })
    } catch (error) {
        if (error instanceof Error) {
            return { error: error.message }
        }
        return { error: "Authentication failed" }
    }
}

export default function Login({ actionData }: Route.ComponentProps) {
    const hasError = !!actionData?.error
    const [showPassword, setShowPassword] = useState(false)
    const [emailError, setEmailError] = useState<string | null>(null)
    const emailErrorId = useId()
    const passwordToggleId = useId()
    const passwordToggleDescId = useId()
    const rememberMeId = useId()
    const [searchParams] = useSearchParams()
    const registrationSuccess = searchParams.get("registered") === "1"

    const validateEmailField = (email: string) => {
        const result = validateEmail(email)
        if (!result.isValid) {
            setEmailError(result.errors[0] || "Invalid email")
            return false
        }
        setEmailError(null)
        return true
    }

    return (
        <div className="min-h-screen w-full flex flex-col lg:flex-row">
            {/* Left side - Content and Form */}
            <div className="w-full lg:flex-1 flex items-center justify-center p-8 lg:p-16 bg-white">
                <div className="w-full max-w-lg">
                    {/* Logo and Branding */}
                    <div className="mb-12">
                        <img
                            src="/placeholder-logo.svg"
                            alt="Job Market Analyzer Logo"
                            className="h-16 mb-6"
                        />
                        <h1 className="text-4xl lg:text-5xl font-bold text-gray-900 mb-4 leading-tight">
                            Your Job Market
                            <br />
                            <span className="text-blue-500">Intelligence</span>
                        </h1>
                        <p className="text-xl text-gray-600 leading-relaxed">
                            Analyze profiles, match with opportunities, and land your dream job with
                            AI-powered insights.
                        </p>
                    </div>

                    {/* Login Form */}
                    <div className="bg-gray-50 rounded-2xl p-8 lg:p-10 shadow-sm border border-gray-200">
                        <div className="mb-8">
                            <h2 className="text-2xl font-bold text-gray-900 mb-2">Welcome back</h2>
                            <p className="text-gray-600">Sign in to your account to continue</p>
                        </div>

                        <Form method="POST" className="space-y-6">
                            {registrationSuccess && (
                                <div className="rounded-lg bg-green-50 border border-green-200 p-4">
                                    <p className="text-sm font-medium text-green-700">
                                        Account created successfully. You can sign in now.
                                    </p>
                                </div>
                            )}
                            {actionData?.error && (
                                <div className="rounded-lg bg-red-50 border border-red-200 p-4">
                                    <p className="text-sm font-medium text-red-800">
                                        {actionData.error}
                                    </p>
                                </div>
                            )}

                            <div className="space-y-5">
                                <Field>
                                    <Label className="text-gray-700 font-medium text-sm block mb-2">
                                        Email address
                                    </Label>
                                    <Input
                                        type="email"
                                        name="email"
                                        className={`w-full px-4 py-3 rounded-lg border ${
                                            emailError
                                                ? "border-red-500 focus:border-red-500 focus:ring-red-500"
                                                : "border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                                        } focus:ring-2 focus:outline-none transition-colors`}
                                        placeholder="Enter your email"
                                        onChange={(e) => {
                                            if (emailError) {
                                                validateEmailField(e.target.value)
                                            }
                                        }}
                                        onBlur={(e) => validateEmailField(e.target.value)}
                                        {...(hasError && {
                                            "data-invalid": true,
                                            "aria-invalid": true,
                                        })}
                                        {...(emailError && { "aria-describedby": emailErrorId })}
                                    />
                                    {emailError && (
                                        <p id={emailErrorId} className="text-sm text-red-600 mt-1">
                                            {emailError}
                                        </p>
                                    )}
                                </Field>
                                <Field>
                                    <Label className="text-gray-700 font-medium text-sm block mb-2">
                                        Password
                                    </Label>
                                    <InputGroup className="relative">
                                        <Input
                                            type={showPassword ? "text" : "password"}
                                            name="password"
                                            className="w-full px-4 py-3 pr-12 rounded-lg border border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-500 focus:outline-none transition-colors"
                                            placeholder="Enter your password"
                                            {...(hasError && {
                                                "data-invalid": true,
                                                "aria-invalid": true,
                                            })}
                                        />
                                        <button
                                            type="button"
                                            id={passwordToggleId}
                                            aria-label={
                                                showPassword ? "Hide password" : "Show password"
                                            }
                                            aria-pressed={showPassword}
                                            aria-describedby={passwordToggleDescId}
                                            className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center justify-center text-gray-500 hover:text-gray-700 focus:outline-none focus:text-gray-700 transition-colors"
                                            onClick={() => setShowPassword((v) => !v)}
                                        >
                                            <span id={passwordToggleDescId} className="sr-only">
                                                {showPassword
                                                    ? "Password is visible"
                                                    : "Password is hidden"}
                                            </span>
                                            {showPassword ? (
                                                <EyeSlashIcon className="h-5 w-5" />
                                            ) : (
                                                <EyeIcon className="h-5 w-5" />
                                            )}
                                        </button>
                                    </InputGroup>
                                </Field>
                            </div>

                            <div className="flex items-center justify-between">
                                <div className="flex items-center">
                                    <input
                                        id={rememberMeId}
                                        name="remember-me"
                                        type="checkbox"
                                        className="h-4 w-4 text-blue-500 focus:ring-blue-500 border-gray-300 rounded"
                                    />
                                    <label
                                        htmlFor={rememberMeId}
                                        className="ml-2 block text-sm text-gray-700"
                                    >
                                        Remember me
                                    </label>
                                </div>

                                <Link
                                    to="/forgot-password"
                                    className="text-sm font-medium text-blue-500 hover:text-blue-600 transition-colors"
                                >
                                    Forgot password?
                                </Link>
                            </div>

                            <Button
                                type="submit"
                                className="w-full h-12 text-base font-semibold bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors"
                            >
                                Sign in to your account
                            </Button>

                            <div className="text-center">
                                <span className="text-gray-600 text-sm">
                                    Don't have an account?{" "}
                                </span>
                                <Link
                                    to="/register"
                                    className="text-blue-500 hover:text-blue-600 font-medium text-sm transition-colors"
                                >
                                    Create account
                                </Link>
                            </div>
                        </Form>
                    </div>
                </div>
            </div>

            {/* Right side - Hero Image with Overlay */}
            <div
                className="hidden lg:flex lg:flex-1 relative overflow-hidden bg-cover bg-center"
                style={{
                    backgroundImage: "url('login.jpg')",
                }}
            >
                {/* Overlay for better text contrast */}
                <div className="absolute inset-0 bg-gradient-to-br from-gray-900/80 via-gray-900/70 to-gray-900/80" />

                {/* Content overlay */}
                <div className="relative z-10 flex flex-col items-center justify-center w-full p-12">
                    <div className="max-w-md text-center text-white">
                        <h3 className="text-3xl font-bold mb-4">Career Growth Made Easy</h3>
                        <p className="text-lg leading-relaxed mb-8 text-gray-200">
                            Discover opportunities aligned with your skills, get real-time job
                            matching, and optimize your profile for success.
                        </p>

                        {/* Trust indicators */}
                        <div className="flex justify-center space-x-8 text-sm">
                            <div className="flex flex-col items-center">
                                <svg
                                    className="w-6 h-6 mb-2 text-green-400"
                                    fill="currentColor"
                                    viewBox="0 0 20 20"
                                    aria-hidden="true"
                                >
                                    <path
                                        fillRule="evenodd"
                                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                                        clipRule="evenodd"
                                    />
                                </svg>
                                <span className="font-medium">AI-Powered</span>
                            </div>
                            <div className="flex flex-col items-center">
                                <svg
                                    className="w-6 h-6 mb-2 text-green-400"
                                    fill="currentColor"
                                    viewBox="0 0 20 20"
                                    aria-hidden="true"
                                >
                                    <path
                                        fillRule="evenodd"
                                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                                        clipRule="evenodd"
                                    />
                                </svg>
                                <span className="font-medium">Real-time</span>
                            </div>
                            <div className="flex flex-col items-center">
                                <svg
                                    className="w-6 h-6 mb-2 text-green-400"
                                    fill="currentColor"
                                    viewBox="0 0 20 20"
                                    aria-hidden="true"
                                >
                                    <path
                                        fillRule="evenodd"
                                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                                        clipRule="evenodd"
                                    />
                                </svg>
                                <span className="font-medium">Accurate</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

"use client"

import { useEffect, useId, useState } from "react"
import { Form, Link, redirect } from "react-router"
import type { RegisterError, RegisterOptions, RegisterResult } from "@/types/auth.types"
import { Button } from "~/components/ui/button"
import { Field, Label } from "~/components/ui/fieldset"
import { Heading } from "~/components/ui/heading"
import { Input, InputGroup } from "~/components/ui/input"
import { Text } from "~/components/ui/text"
import { register } from "~/services/auth.client"
import { validateEmail, validatePassword, validateUsername } from "~/utils/validation"
import type { Route } from "./+types/register"
import { EyeIcon, EyeSlashIcon } from "@heroicons/react/16/solid"

export async function clientLoader(_args: Route.ClientLoaderArgs) {
    // Check if user is already authenticated and redirect to jobs
    // Use a simple check to avoid complex token refresh logic that might fail
    if (typeof window !== "undefined") {
        const storedAuth = localStorage.getItem("auth")
        if (storedAuth) {
            try {
                const authData = JSON.parse(storedAuth)
                if (authData.user && authData.accessToken) {
                    // User appears to be authenticated, redirect to jobs
                    return redirect("/jobs")
                }
            } catch (error) {
                // Invalid auth data, clear it and allow registration
                console.warn("[Register] Invalid auth data in localStorage:", error)
                localStorage.removeItem("auth")
            }
        }
    }

    // User is not authenticated, allow access to register page
    return null
}

export async function clientAction({ request }: Route.ClientActionArgs) {
    const formData = await request.formData()
    const email = formData.get("email")
    const password = formData.get("password")
    const first_name = formData.get("first_name")
    const last_name = formData.get("last_name")
    const username = formData.get("username")

    // Basic validation
    if (!email || !password || !username) {
        return {
            fieldErrors: {
                email: !email ? ["Email is required"] : undefined,
                password: !password ? ["Password is required"] : undefined,
                username: !username ? ["Username is required"] : undefined,
            },
        }
    }

    if (
        typeof email !== "string" ||
        typeof password !== "string" ||
        typeof username !== "string" ||
        (first_name && typeof first_name !== "string") ||
        (last_name && typeof last_name !== "string")
    ) {
        return { error: "Invalid field types" }
    }

    try {
        const url = new URL(request.url)
        const route = `${url.protocol}//${url.host}/login`

        const registerOptions: RegisterOptions = {
            username,
            first_name: (first_name as string) || undefined,
            last_name: (last_name as string) || undefined,
            email,
            password,
            route,
        }

        const result = (await register(registerOptions)) as RegisterResult

        if (result.message?.includes("User registered successfully")) {
            return redirect("/login?registered=1")
        }

        return { error: "Registration failed" }
    } catch (error) {
        console.error("[Register] Registration error:", error)

        // Try to extract field errors from the API response
        if (error instanceof Error) {
            try {
                const errorData = JSON.parse(error.message) as RegisterError

                // Return field-level errors if present
                if (
                    errorData.username ||
                    errorData.email ||
                    errorData.password ||
                    errorData.first_name ||
                    errorData.last_name
                ) {
                    return { fieldErrors: errorData }
                }

                // Return general error if present
                if (errorData.error) {
                    return { error: errorData.error }
                }
            } catch {
                // If JSON parsing fails, return the error message directly
                return { error: error.message }
            }
        }

        return { error: "Registration failed. Please try again." }
    }
}

export default function Register({ actionData }: Route.ComponentProps) {
    const fieldErrors = actionData?.fieldErrors as RegisterError | undefined
    const generalError = actionData?.error
    const [validationErrors, setValidationErrors] = useState({
        email: null as string | null,
        username: null as string | null,
        password: null as string | null,
    })
    const usernameErrorId = useId()
    const emailErrorId = useId()
    const passwordErrorId = useId()
    const [showPassword, setShowPassword] = useState(false)
    const passwordToggleId = useId()
    const passwordToggleDescId = useId()

    // Clear client validation errors when server errors are present
    // But only clear if the server error is for the same field
    useEffect(() => {
        if (fieldErrors) {
            setValidationErrors((prev) => ({
                email: fieldErrors.email ? null : prev.email,
                username: fieldErrors.username ? null : prev.username,
                password: fieldErrors.password ? null : prev.password,
            }))
        }
    }, [fieldErrors])

    const validateEmailField = (email: string) => {
        const result = validateEmail(email)
        if (!result.isValid) {
            setValidationErrors((prev) => ({
                ...prev,
                email: result.errors[0] || "Invalid email",
            }))
            return false
        }
        setValidationErrors((prev) => ({ ...prev, email: null }))
        return true
    }

    const validateUsernameField = (username: string) => {
        const result = validateUsername(username)
        if (!result.isValid) {
            setValidationErrors((prev) => ({
                ...prev,
                username: result.errors[0] || "Invalid username",
            }))
            return false
        }
        setValidationErrors((prev) => ({ ...prev, username: null }))
        return true
    }

    const validatePasswordField = (password: string) => {
        const result = validatePassword(password)
        if (!result.isValid) {
            setValidationErrors((prev) => ({
                ...prev,
                password: result.errors[0] || "Invalid password",
            }))
            return false
        }
        setValidationErrors((prev) => ({ ...prev, password: null }))
        return true
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-[#fcfbf8] py-12 px-4">
            <div className="w-full max-w-md">
                <Form method="POST" className="space-y-6">
                    <div className="text-center">
                        <img src="/placeholder-logo.svg" alt="Job Market Agent Logo" className="h-12 mx-auto mb-6" />
                        <Heading className="!text-black font-bold text-2xl">
                            Create your account
                        </Heading>
                        <p className="mt-2 text-sm text-gray-600">
                            Get started with your legal workspace
                        </p>
                    </div>

                    {generalError && (
                        <div className="rounded-lg bg-red-50 border border-red-200 p-4">
                            <p className="text-sm font-medium text-red-800">{generalError}</p>
                        </div>
                    )}

                    <div className="space-y-4">
                        <Field>
                            <Label className="!text-black font-medium text-sm">Username</Label>
                            <Input
                                type="text"
                                name="username"
                                className={`clean-input !text-black ${fieldErrors?.username || validationErrors.username ? "border-red-500" : ""}`}
                                onChange={(e) => {
                                    if (validationErrors.username) {
                                        validateUsernameField(e.target.value)
                                    }
                                }}
                                onBlur={(e) => validateUsernameField(e.target.value)}
                                {...((fieldErrors?.username || validationErrors.username) && {
                                    "aria-describedby": usernameErrorId,
                                })}
                                required
                            />
                            {(fieldErrors?.username || validationErrors.username) && (
                                <p id={usernameErrorId} className="text-sm text-red-600 mt-1">
                                    {fieldErrors?.username?.[0] || validationErrors.username}
                                </p>
                            )}
                        </Field>

                        <div className="grid grid-cols-2 gap-4">
                            <Field>
                                <Label className="!text-black font-medium text-sm">
                                    First name
                                </Label>
                                <Input
                                    name="first_name"
                                    className={`clean-input !text-black ${fieldErrors?.first_name ? "border-red-500" : ""}`}
                                />
                                {fieldErrors?.first_name && (
                                    <p className="text-sm text-red-600 mt-1">
                                        {fieldErrors.first_name[0]}
                                    </p>
                                )}
                            </Field>
                            <Field>
                                <Label className="!text-black font-medium text-sm">Last name</Label>
                                <Input
                                    name="last_name"
                                    className={`clean-input !text-black ${fieldErrors?.last_name ? "border-red-500" : ""}`}
                                />
                                {fieldErrors?.last_name && (
                                    <p className="text-sm text-red-600 mt-1">
                                        {fieldErrors.last_name[0]}
                                    </p>
                                )}
                            </Field>
                        </div>

                        <Field>
                            <Label className="!text-black font-medium text-sm">Email</Label>
                            <Input
                                type="email"
                                name="email"
                                className={`clean-input !text-black ${fieldErrors?.email || validationErrors.email ? "border-red-500" : ""}`}
                                onChange={(e) => {
                                    if (validationErrors.email) {
                                        validateEmailField(e.target.value)
                                    }
                                }}
                                onBlur={(e) => validateEmailField(e.target.value)}
                                {...((fieldErrors?.email || validationErrors.email) && {
                                    "aria-describedby": emailErrorId,
                                })}
                                required
                            />
                            {(fieldErrors?.email || validationErrors.email) && (
                                <p id={emailErrorId} className="text-sm text-red-600 mt-1">
                                    {fieldErrors?.email?.[0] || validationErrors.email}
                                </p>
                            )}
                        </Field>

                        <Field>
                            <Label className="!text-black font-medium text-sm">Password</Label>
                            <InputGroup className="relative">
                                <Input
                                    type={showPassword ? "text" : "password"}
                                    name="password"
                                    autoComplete="new-password"
                                    className={`clean-input !text-black pr-12 ${
                                        fieldErrors?.password || validationErrors.password
                                            ? "border-red-500"
                                            : ""
                                    }`}
                                    onChange={(e) => {
                                        if (validationErrors.password) {
                                            validatePasswordField(e.target.value)
                                        }
                                    }}
                                    onBlur={(e) => validatePasswordField(e.target.value)}
                                    {...((fieldErrors?.password || validationErrors.password) && {
                                        "aria-describedby": passwordErrorId,
                                    })}
                                    required
                                />
                                <button
                                    type="button"
                                    id={passwordToggleId}
                                    aria-label={showPassword ? "Hide password" : "Show password"}
                                    aria-pressed={showPassword}
                                    aria-describedby={passwordToggleDescId}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center justify-center text-gray-500 hover:text-gray-700 focus:outline-none focus:text-gray-700 transition-colors"
                                    onClick={() => setShowPassword((value) => !value)}
                                >
                                    <span id={passwordToggleDescId} className="sr-only">
                                        {showPassword ? "Password is visible" : "Password is hidden"}
                                    </span>
                                    {showPassword ? (
                                        <EyeSlashIcon className="h-5 w-5" />
                                    ) : (
                                        <EyeIcon className="h-5 w-5" />
                                    )}
                                </button>
                            </InputGroup>
                            {(fieldErrors?.password || validationErrors.password) && (
                                <p id={passwordErrorId} className="text-sm text-red-600 mt-1">
                                    {fieldErrors?.password?.[0] || validationErrors.password}
                                </p>
                            )}
                        </Field>
                    </div>

                    <Button type="submit" className="w-full clean-button">
                        Create account
                    </Button>

                    <div className="text-center">
                        <Text className="!text-gray-600 text-sm">
                            Already have an account?{" "}
                            <Link
                                to="/login"
                                className="text-[#4b92ff] hover:text-[#3a7ce8] font-medium"
                            >
                                Sign in
                            </Link>
                        </Text>
                    </div>
                </Form>
            </div>
        </div>
    )
}

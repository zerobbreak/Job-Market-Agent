import { Form, Link, redirect } from "react-router"
import { Button } from "~/components/ui/button"
import { Field, Label } from "~/components/ui/fieldset"
import { Heading } from "~/components/ui/heading"
import { Input } from "~/components/ui/input"
import { Strong, Text } from "~/components/ui/text"
import { passwordReset } from "~/services/auth.client"
import type { Route } from "./+types/forgot-password"

export async function clientAction({ request }: Route.ClientActionArgs) {
    const formData = await request.formData()
    const email = formData.get("email") as string

    if (!email) {
        return { error: "Email is required" }
    }

    // In development mode, simulate successful password reset
    if (import.meta.env.DEV) {
        await new Promise((resolve) => setTimeout(resolve, 1000)) // Simulate API delay
        return redirect("/reset")
    }

    const url = new URL(request.url)
    const route = `${url.protocol}//${url.host}/reset-password`
    const result = await passwordReset(email, route)
    if (result) {
        return redirect("/reset")
    }
    return redirect("/")
}

export default function ForgotPassword() {
    return (
        <Form method="POST" className="grid w-full max-w-sm grid-cols-1 gap-8">
            {/* <Logo className="h-6 text-zinc-950 dark:text-white forced-colors:text-[CanvasText]" /> */}
            <img src="/placeholder-logo.svg" alt="Job Market Agent Logo" className="h-10" />{" "}
            <Heading>Reset your password</Heading>
            <Text>Enter your email and we’ll send you a link to reset your password.</Text>
            <Field>
                <Label>Email</Label>
                <Input type="email" name="email" />
            </Field>
            <Button type="submit" className="w-full">
                Reset password
            </Button>
            <Text>
                Don’t have an account?{" "}
                <Link to="/register">
                    <Strong>Sign up</Strong>
                </Link>
            </Text>
        </Form>
    )
}

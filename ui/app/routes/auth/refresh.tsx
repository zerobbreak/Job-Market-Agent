import { redirect } from "react-router"
import type { RequireUserResult } from "@/types/auth.types"
import { requireUser } from "~/services/auth.client"
import type { Route } from "./+types/refresh"

// This route handles token refresh requests
export async function clientAction({ request }: Route.ClientActionArgs) {
    const result = (await requireUser(request, {
        refresh: "force",
    })) as RequireUserResult

    // Get the return URL from the request
    const formData = await request.formData()
    const returnTo = (formData.get("returnTo") as string) || "/"

    // Redirect back to the original page with updated session
    return redirect(returnTo, result.headers ? { headers: result.headers } : undefined)
}

// Redirect any GET requests to login
export async function clientLoader() {
    return redirect("/login")
}

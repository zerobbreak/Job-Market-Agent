import { signOut } from "~/services/auth.client"
import type { Route } from "./+types/logout"

// SPA mode: use clientAction for POSTs
export async function clientAction({ request }: Route.ClientActionArgs) {
    return signOut(request)
}

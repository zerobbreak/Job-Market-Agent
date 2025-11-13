import { redirect } from "react-router"
import type { Route } from "./+types/root"

export async function clientLoader({}: Route.ClientLoaderArgs) {
    throw redirect("/learn/using/introduction")
}

export default function Learn() {
    return null
}

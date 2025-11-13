import { useEffect, useId } from "react"
import { Form, useLocation } from "react-router"

interface TokenRefreshProps {
    needsRefresh: boolean
}

export function TokenRefresh({ needsRefresh }: TokenRefreshProps) {
    const location = useLocation()
    const formId = useId()

    useEffect(() => {
        if (needsRefresh) {
            // Automatically submit the refresh form
            const form = document.getElementById(formId) as HTMLFormElement
            if (form) {
                form.submit()
            }
        }
    }, [needsRefresh, formId])

    if (!needsRefresh) {
        return null
    }

    return (
        <Form id={formId} method="post" action="/refresh" style={{ display: "none" }}>
            <input type="hidden" name="returnTo" value={location.pathname + location.search} />
        </Form>
    )
}

import type React from "react"

export function AuthLayout({ children }: { children: React.ReactNode }) {
    return (
        <main className="flex min-h-dvh flex-col p-2 bg-[#fcfbf8]">
            <div className="flex grow items-center justify-center p-6 lg:rounded-lg lg:bg-white lg:p-10 lg:shadow-sm lg:ring-1 lg:ring-[#edebe5] text-[#151515]">
                {children}
            </div>
        </main>
    )
}

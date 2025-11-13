import { Input } from "~/components/ui/input"

interface SearchBarProps {
    placeholder?: string
    value?: string
    onChange?: (value: string) => void
    className?: string
}

export function SearchBar({
    placeholder = "Search case",
    value,
    onChange,
    className = "",
}: SearchBarProps) {
    return (
        <div className={`relative ${className}`}>
            <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
                <svg
                    className="h-5 w-5 text-[#60605e]"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    role="img"
                    aria-label="Search"
                >
                    <circle cx="11" cy="11" r="8" strokeWidth="2" />
                    <path d="m21 21-4.35-4.35" strokeWidth="2" />
                </svg>
            </div>
            <Input
                type="text"
                placeholder={placeholder}
                value={value}
                onChange={(e) => onChange?.(e.target.value)}
                className="pl-10 pr-4 py-2 w-full max-w-[246px] penpot-input"
            />
        </div>
    )
}

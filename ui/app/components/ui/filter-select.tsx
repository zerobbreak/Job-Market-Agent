interface FilterSelectProps {
    value?: string
    onChange?: (value: string) => void
    options: string[]
    className?: string
}

export function FilterSelect({ value, onChange, options, className = "" }: FilterSelectProps) {
    return (
        <div className={`relative ${className}`}>
            <select
                value={value}
                onChange={(e) => onChange?.(e.target.value)}
                className="penpot-select"
            >
                {options.map((option) => (
                    <option key={option} value={option}>
                        {option}
                    </option>
                ))}
            </select>
            <div className="absolute inset-y-0 right-3 flex items-center pointer-events-none">
                <svg
                    className="h-4 w-4 text-[#151515]"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    role="img"
                    aria-label="Dropdown arrow"
                >
                    <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M19 9l-7 7-7-7"
                    />
                </svg>
            </div>
        </div>
    )
}

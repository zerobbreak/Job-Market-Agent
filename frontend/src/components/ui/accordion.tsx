import * as React from 'react'
import { ChevronDown } from 'lucide-react'
import { cn } from '../../lib/utils'

export function Accordion({ children }: { children: React.ReactNode }) {
  return <div className="space-y-2">{children}</div>
}

export function AccordionItem({
  title,
  children,
  defaultOpen = false,
}: {
  title: string
  children: React.ReactNode
  defaultOpen?: boolean
}) {
  const [open, setOpen] = React.useState(defaultOpen)
  return (
    <div className="border rounded-xl">
      <button
        type="button"
        className="w-full flex items-center justify-between p-4"
        onClick={() => setOpen((v) => !v)}
      >
        <span className="font-semibold text-left">{title}</span>
        <ChevronDown className={cn('h-5 w-5 transition-transform', open ? 'rotate-180' : '')} />
      </button>
      {open && (
        <div className="px-4 pb-4 text-gray-600">{children}</div>
      )}
    </div>
  )
}

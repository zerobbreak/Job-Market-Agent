import { Accordion, AccordionItem } from '@/components/ui/accordion'

export default function FAQ() {
  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-6xl mx-auto px-4 py-16">
        <h1 className="text-4xl font-extrabold mb-6">Frequently Asked Questions</h1>
        <Accordion>
          <AccordionItem title="Is my data secure?" defaultOpen>
            We store your data securely and never share it without consent.
          </AccordionItem>
          <AccordionItem title="Can I export my generated documents?">
            Yes, download tailored CVs and cover letters anytime from Applications.
          </AccordionItem>
          <AccordionItem title="Do you support non-English CVs?">
            We support common languages; reach out if you need specifics.
          </AccordionItem>
          <AccordionItem title="How do I contact support?">
            Use the in-app help or email support for priority assistance.
          </AccordionItem>
        </Accordion>
      </div>
    </div>
  )
}

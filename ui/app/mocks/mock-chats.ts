// Mock chat types
interface MockChat {
    id: string
    name: string
    mode: "ask" | "write"
    contexts: string[]
    casefiles: string[]
    messages: MockMessage[]
    isActive: boolean
    createdAt: string
    lastActivity: string
    settings: {
        autoSave: boolean
        maxTokens: number
        temperature: number
    }
}

interface MockMessage {
    id: number
    type: "user" | "ai"
    content: string
    timestamp: string
    status: "sent" | "delivered" | "read"
    metadata?: {
        model?: string
        processingTime?: number
        confidence?: number
        sources?: string[]
    }
}

// Mock chat data
const mockChats: Record<string, MockChat[]> = {
    "case-1": [
        {
            id: "chat-case1-default",
            name: "Personal Injury Analysis",
            mode: "ask",
            contexts: ["Facts", "Research", "Evidence"],
            casefiles: ["medical_report_smith.pdf", "accident_photos.zip"],
            isActive: true,
            createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
            lastActivity: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
            settings: { autoSave: true, maxTokens: 4096, temperature: 0.7 },
            messages: [
                {
                    id: 1,
                    type: "ai",
                    content:
                        "Hello! I'm your AI legal assistant for the Smith vs. Johnson personal injury case. I have access to your case facts, medical records, research materials, and uploaded files. How can I help you today?",
                    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
                    status: "delivered",
                    metadata: { model: "gpt-4", processingTime: 0.5, confidence: 0.95 },
                },
                {
                    id: 2,
                    type: "user",
                    content: "What are the key strengths of our case?",
                    timestamp: new Date(Date.now() - 90 * 60 * 1000).toISOString(),
                    status: "read",
                },
                {
                    id: 3,
                    type: "ai",
                    content:
                        "Based on the case facts and medical records, here are the key strengths:\n\n**1. Clear Liability**: Defendant made an improper left turn at a controlled intersection, violating right-of-way rules.\n\n**2. Well-Documented Injuries**: Multiple objective medical findings including fractures, concussion, and ongoing treatment needs.\n\n**3. Strong Medical Evidence**: Comprehensive treatment records from emergency room through rehabilitation.\n\n**4. Economic Damages**: Clear calculation of lost wages ($15,600), medical expenses ($47,250), and future costs.\n\n**5. Eyewitness Support**: Pedestrian witness corroborates plaintiff's account.\n\n**6. Police Report**: Official documentation supports accident reconstruction.\n\nThe case has a strong foundation with clear liability and well-documented damages. The primary challenge will be overcoming the defendant's $25,000 settlement offer.",
                    timestamp: new Date(Date.now() - 89 * 60 * 1000).toISOString(),
                    status: "delivered",
                    metadata: {
                        model: "gpt-4",
                        processingTime: 1.2,
                        confidence: 0.92,
                        sources: [
                            "Case Facts Summary",
                            "Medical Records & Documentation",
                            "Personal Injury Law Research",
                        ],
                    },
                },
                {
                    id: 4,
                    type: "user",
                    content: "How should we respond to the $25,000 settlement offer?",
                    timestamp: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
                    status: "read",
                },
                {
                    id: 5,
                    type: "ai",
                    content:
                        "The $25,000 settlement offer from the insurance company is significantly below the case value. Based on the medical records and economic analysis, your case is worth $150,000 - $350,000.\n\n**Recommended Response Strategy:**\n\n1. **Demand Letter**: Send a formal demand for $175,000, supported by medical bills and lost wage documentation\n\n2. **Medical Lien Resolution**: Ensure all medical providers have filed proper liens\n\n3. **Timeline Pressure**: Note that statute of limitations expires in X months\n\n4. **Negotiation Preparation**: Prepare for mediation if initial demand is rejected\n\n5. **Documentation**: Keep detailed records of all settlement communications\n\nThe $25,000 offer appears to be a nuisance value attempt to pressure quick settlement. With your strong liability position and documented damages, you should pursue a much higher settlement.",
                    timestamp: new Date(Date.now() - 58 * 60 * 1000).toISOString(),
                    status: "delivered",
                    metadata: {
                        model: "gpt-4",
                        processingTime: 1.8,
                        confidence: 0.88,
                        sources: [
                            "Case Facts Summary",
                            "Medical Records & Documentation",
                            "Case Strategy & Timeline",
                        ],
                    },
                },
            ],
        },
        {
            id: "chat-case1-drafting",
            name: "Demand Letter Drafting",
            mode: "write",
            contexts: ["Drafting", "Facts"],
            casefiles: ["medical_report_smith.pdf"],
            isActive: false,
            createdAt: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
            lastActivity: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
            settings: { autoSave: true, maxTokens: 4096, temperature: 0.7 },
            messages: [
                {
                    id: 1,
                    type: "ai",
                    content:
                        "I can help you draft a formal settlement demand letter. Please provide the specific details you'd like included, such as the demand amount, timeline, or particular points of emphasis.",
                    timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
                    status: "delivered",
                    metadata: { model: "gpt-4", processingTime: 0.3, confidence: 0.96 },
                },
            ],
        },
    ],
    "case-2": [
        {
            id: "chat-case2-default",
            name: "Trust Dispute Analysis",
            mode: "ask",
            contexts: ["Facts", "Research"],
            casefiles: ["trust_document_original.pdf", "court_filing_2024.docx"],
            isActive: true,
            createdAt: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
            lastActivity: new Date(Date.now() - 45 * 60 * 1000).toISOString(),
            settings: { autoSave: true, maxTokens: 4096, temperature: 0.7 },
            messages: [
                {
                    id: 1,
                    type: "ai",
                    content:
                        "Hello! I'm here to assist with the Johnson Family Trust dispute. I have access to the trust facts, legal research, and settlement strategy materials. How can I help you navigate this family trust matter?",
                    timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
                    status: "delivered",
                    metadata: { model: "gpt-4", processingTime: 0.4, confidence: 0.94 },
                },
                {
                    id: 2,
                    type: "user",
                    content: "What's the best approach for mediation?",
                    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
                    status: "read",
                },
                {
                    id: 3,
                    type: "ai",
                    content:
                        "For the Johnson Family Trust mediation, here's a strategic approach:\n\n**Preparation Phase (2-4 weeks):**\n1. **Select Neutral Mediator**: Choose someone experienced in trust disputes\n2. **Develop Mediation Brief**: Present trust language, beneficiary rights, and case facts\n3. **Settle on Agenda**: Distribution amounts, trustee succession, family governance\n\n**Mediation Strategy:**\n- **Opening Position**: Full equal distributions ($1.4M each)\n- **Target Range**: $1.0M - $1.3M each with conditions\n- **Walk-Away Point**: $800K minimum per beneficiary\n\n**Key Arguments:**\n- Trust language requires distributions at age 25\n- Trustee discretion is limited and must be reasonable\n- Equal treatment of beneficiaries\n- Preservation of family relationships\n\n**Success Factors:**\n- Focus on interests rather than positions\n- Use objective criteria for decision-making\n- Maintain family relationship preservation\n- Document all agreements clearly\n\nMediation has a 75-85% success rate for trust disputes and typically costs $5,000-$10,000.",
                    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
                    status: "delivered",
                    metadata: {
                        model: "gpt-4",
                        processingTime: 2.1,
                        confidence: 0.89,
                        sources: [
                            "Trust Facts & Background",
                            "Trust Law Research & Precedents",
                            "Settlement Strategy & Negotiation Plan",
                        ],
                    },
                },
            ],
        },
    ],
}

/**
 * Mock AI chat message generation
 */
export const mockGenerateChatResponse = async (
    message: string,
    context: string[],
    caseId: string
): Promise<MockMessage> => {
    // Simulate AI processing delay
    await new Promise((resolve) => setTimeout(resolve, 800 + Math.random() * 1200))

    // Generate contextual response based on message content
    let responseContent = ""

    if (message.toLowerCase().includes("settlement") || message.toLowerCase().includes("offer")) {
        responseContent = `Based on the case materials and ${context.length} available contexts, here's my analysis of settlement options:

**Current Case Value Assessment:**
- Medical expenses: $47,250 (documented)
- Lost wages: $15,600 (6 weeks)
- Future medical costs: $28,000 (estimated)
- Pain and suffering: $75,000 - $150,000 (jury determination)

**Recommended Settlement Strategy:**
1. **Initial Demand**: $175,000 (conservative estimate)
2. **Negotiation Range**: $125,000 - $150,000
3. **Counter-offers**: Respond with specific reductions based on documented concessions

**Key Arguments for Higher Settlement:**
- Clear liability (left turn violation)
- Objective medical evidence
- Strong eyewitness support
- Reasonable jury venue

**Risk Considerations:**
- Trial could result in $200,000+ verdict
- But appeals and delays add 12-18 months
- Settlement provides certainty and immediate resolution

The $25,000 offer appears to be a low-ball tactic. With your case strengths, pursue a substantially higher settlement.`
    } else if (
        message.toLowerCase().includes("evidence") ||
        message.toLowerCase().includes("proof")
    ) {
        responseContent = `Here's a comprehensive evidence analysis for Case ${caseId}:

**Primary Evidence Categories:**

1. **Liability Evidence** (Strength: 9/10)
   - Police accident report: Documents left turn violation
   - Traffic signal timing data
   - Roadway measurements and sight lines
   - Defendant's driving record

2. **Medical Evidence** (Strength: 8/10)
   - Emergency room records: Initial assessment and treatment
   - Orthopedic surgery reports: Fracture repair details
   - Physical therapy records: Rehabilitation progress
   - Psychiatric evaluations: PTSD and anxiety diagnosis

3. **Economic Damages** (Strength: 8/10)
   - Wage loss documentation: Pay stubs and employer statements
   - Medical billing records: All treatment costs
   - Expert reports: Future medical cost projections

4. **Witness Evidence** (Strength: 9/10)
   - Eyewitness statements: Pedestrian account
   - Treating physician opinions
   - Vocational expert assessment

**Evidence Gaps to Address:**
- Traffic camera footage (pending subpoena)
- Defendant's employment records
- Long-term prognosis documentation

**Recommendations:**
1. Secure traffic camera footage immediately
2. Obtain vocational rehabilitation assessment
3. Prepare medical experts for deposition testimony
4. Document all evidence chain of custody`
    } else if (
        message.toLowerCase().includes("timeline") ||
        message.toLowerCase().includes("next steps")
    ) {
        responseContent = `Here's the recommended case timeline and action plan for Case ${caseId}:

## Immediate Actions (Next 7 Days)
- [ ] Review and organize all medical records
- [ ] Prepare formal settlement demand letter
- [ ] Schedule independent medical examination
- [ ] Contact treating physicians for narrative reports

## Short-term Goals (7-30 Days)
- [ ] Send demand package to insurance company
- [ ] Begin formal discovery process
- [ ] Retain accident reconstruction expert
- [ ] Prepare client for deposition

## Medium-term Objectives (30-90 Days)
- [ ] Complete initial discovery responses
- [ ] Conduct key witness depositions
- [ ] Evaluate settlement offers
- [ ] Prepare for mediation if offers insufficient

## Critical Deadlines
- **Statute of Limitations**: Expires in 180 days
- **Discovery Completion**: Due in 120 days
- **Mediation Deadline**: 90 days from filing
- **Trial Date**: Scheduled for 180 days

## Budget Considerations
- **Medical Records**: $500
- **Expert Witnesses**: $15,000
- **Discovery**: $5,000
- **Deposition Transcripts**: $2,000

## Success Metrics
1. **Settlement Target**: $125,000 minimum
2. **Timeline Goal**: Resolve within 90 days
3. **Cost Control**: Keep expenses under 25% of recovery

**Priority Focus:** Strengthen evidence position and prepare compelling settlement demand to maximize recovery while minimizing delay and expense.`
    } else {
        responseContent = `I understand you're asking about "${message.substring(0, 50)}${message.length > 50 ? "..." : ""}".

Based on the available case materials for Case ${caseId}, I have access to ${context.length} different contexts and can help you with:

**Available Assistance:**
- Case analysis and strategy development
- Evidence evaluation and recommendations
- Settlement negotiation guidance
- Timeline and deadline management
- Medical record review and summary
- Legal research on relevant topics

**Current Case Status:**
- Strong liability position with clear evidence
- Well-documented medical treatment records
- Economic damages calculation in progress
- Settlement negotiations at early stage

Could you please provide more specific details about what aspect of the case you'd like me to focus on? For example:
- "Analyze the settlement offer"
- "Review the medical evidence"
- "Suggest next steps in the case"
- "Prepare a demand letter outline"

This will help me provide more targeted and useful assistance.`
    }

    return {
        id: Date.now(),
        type: "ai",
        content: responseContent,
        timestamp: new Date().toISOString(),
        status: "delivered",
        metadata: {
            model: "gpt-4",
            processingTime: 1.2 + Math.random() * 0.8,
            confidence: 0.85 + Math.random() * 0.12,
            sources: context.slice(0, 3), // Use first 3 contexts as sources
        },
    }
}

/**
 * Mock chat management functions
 */
export const mockGetChats = (caseId: string) => {
    return mockChats[caseId] || []
}

export const mockCreateChat = (
    caseId: string,
    name: string,
    mode: "ask" | "write",
    contexts: string[],
    casefiles: string[]
) => {
    const newChat: MockChat = {
        id: `chat-${caseId}-${Date.now()}`,
        name,
        mode,
        contexts,
        casefiles,
        isActive: true,
        createdAt: new Date().toISOString(),
        lastActivity: new Date().toISOString(),
        settings: { autoSave: true, maxTokens: 4096, temperature: 0.7 },
        messages: [
            {
                id: 1,
                type: "ai",
                content: `Hello! I'm your AI legal assistant for Case ${caseId}. I have access to ${contexts.length} contexts and ${casefiles.length} case files. How can I help you with your ${mode === "ask" ? "questions" : "drafting"} today?`,
                timestamp: new Date().toISOString(),
                status: "delivered",
                metadata: { model: "gpt-4", processingTime: 0.5, confidence: 0.95 },
            },
        ],
    }

    if (!mockChats[caseId]) {
        mockChats[caseId] = []
    }

    // Set other chats as inactive
    mockChats[caseId].forEach((chat) => {
        chat.isActive = false
    })

    // Add new chat
    mockChats[caseId].push(newChat)

    return newChat
}

export const mockSendChatMessage = async (
    caseId: string,
    chatId: string,
    message: string
): Promise<MockMessage> => {
    const chats = mockChats[caseId]
    if (!chats) throw new Error("Case not found")

    const chat = chats.find((c) => c.id === chatId)
    if (!chat) throw new Error("Chat not found")

    // Generate unique message IDs within this chat
    const maxExistingId = chat.messages.length > 0 ? Math.max(...chat.messages.map((m) => m.id)) : 0

    // Add user message
    const userMessage: MockMessage = {
        id: maxExistingId + 1,
        type: "user",
        content: message,
        timestamp: new Date().toISOString(),
        status: "read",
    }

    chat.messages.push(userMessage)

    // Generate AI response with unique ID
    const aiResponse = await mockGenerateChatResponse(message, chat.contexts, caseId)
    const aiMessage: MockMessage = {
        ...aiResponse,
        id: maxExistingId + 2,
        timestamp: new Date().toISOString(),
    }

    chat.messages.push(aiMessage)

    // Update last activity
    chat.lastActivity = new Date().toISOString()

    return aiMessage
}

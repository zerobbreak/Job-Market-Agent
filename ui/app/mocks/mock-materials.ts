import type { CaseMaterial } from "../../@types/job.types"

/**
 * Mock case material generation APIs
 */
export const mockGenerateCaseMaterial = async (
    caseId: string,
    type: "facts" | "research" | "evidence" | "notes" | "drafting" | "custom",
    topic?: string
): Promise<CaseMaterial> => {
    // Simulate processing delay
    await new Promise((resolve) => setTimeout(resolve, 2000 + Math.random() * 3000))

    const now = new Date().toISOString()
    let title = ""
    let description = ""
    let content = ""

    switch (type) {
        case "facts":
            title = "Generated Case Facts Summary"
            description = "AI-generated comprehensive summary of case facts and timeline"
            content = `# Generated Case Facts Summary

Based on the uploaded documents and case information for Case ${caseId}, here are the key facts:

## Incident Summary
- **Date**: March 15, 2024
- **Location**: Main Street & Oak Avenue intersection
- **Parties**: John Smith (Plaintiff) vs. Sarah Johnson (Defendant)
- **Insurance**: State Farm Insurance Company

## Key Evidence
- Police accident report documenting left turn violation
- Medical records showing serious injuries requiring surgery
- Eyewitness statements supporting plaintiff's account
- Traffic camera footage (pending subpoena)

## Damages Claimed
- Medical expenses: $47,250+
- Lost wages: $15,600
- Future medical costs: $28,000 estimated
- Pain and suffering: To be determined

This summary provides a foundation for case evaluation and settlement negotiations.`
            break

        case "research":
            title = `Legal Research: ${topic || "Case Law Analysis"}`
            description = `AI-generated legal research on ${topic || "relevant legal principles"}`
            content = `# Legal Research: ${topic || "General Legal Research"}

## Applicable Law
Under [State] law, the doctrine of comparative negligence applies to intersection accidents involving left turns.

## Key Cases
1. **Smith v. Johnson (2022)**: Left-turning driver found 70% negligent
2. **Martinez v. City (2021)**: $2.1M verdict for similar injuries
3. **Rodriguez v. Delivery (2020)**: Employer vicariously liable

## Strategic Analysis
- Strong liability position favoring plaintiff
- Well-documented medical evidence
- Clear economic damages calculation
- Favorable jury venue demographics

## Settlement Range
Based on similar cases: $150,000 - $350,000
Recommended demand: $175,000`
            break

        case "evidence":
            title = "Evidence Analysis Report"
            description = "Comprehensive analysis of evidentiary strength and recommendations"
            content = `# Evidence Analysis Report

## Document Review Summary
**Total Documents Reviewed**: 24
**Medical Records**: 12 documents
**Correspondence**: 8 emails/phone logs
**Official Records**: 4 (police report, insurance docs)

## Key Findings
✅ **Strong Medical Documentation**: Comprehensive treatment records from ER through rehab
✅ **Clear Liability Evidence**: Police report and witness statements support plaintiff's account
✅ **Economic Damages**: Well-documented lost wages and medical expenses
⚠️ **Traffic Camera**: Pending subpoena - could provide definitive evidence

## Evidence Strength Rating
- **Liability**: 9/10 (Clear left turn violation)
- **Damages**: 8/10 (Well-documented but some future costs speculative)
- **Witness Credibility**: 9/10 (Corroborating accounts)

## Recommendations
1. Obtain traffic camera footage immediately
2. Secure vocational expert for future earning capacity
3. Prepare medical experts for deposition
4. Document all settlement communications`
            break

        case "notes":
            title = "Case Notes & Observations"
            description = "AI-generated observations and strategic notes for case management"
            content = `# Case Notes: ${caseId}

## Key Observations
- **Case Strength**: Strong liability position with clear evidentiary support
- **Client Communication**: Regular updates maintained, expectations managed
- **Opposing Party**: Insurance company using standard delay tactics
- **Timeline Pressure**: Statute of limitations creates leverage opportunity

## Strategic Considerations
1. **Evidence Preservation**: All key documents secured and organized
2. **Witness Preparation**: Treating physicians prepared for deposition
3. **Settlement Leverage**: Medical treatment completion strengthens position
4. **Cost Control**: Expenses tracking within budget parameters

## Action Items
- [ ] Schedule mediation preparation meeting
- [ ] Update demand letter with final medical costs
- [ ] Prepare client for settlement discussions
- [ ] Review and update case budget

## Risk Assessment
- **Settlement Range**: $125,000 - $200,000 (conservative estimate)
- **Trial Probability**: 40% (if mediation unsuccessful)
- **Appeal Risk**: Minimal (straightforward liability case)

## Next Steps Priority
1. Complete outstanding discovery
2. Finalize mediation position
3. Prepare trial notebook (backup plan)
4. Client settlement decision meeting`
            break

        case "drafting":
            title = "Draft Legal Document"
            description = "AI-generated draft document for case proceedings"
            content = `# Draft Settlement Demand Letter

[Attorney Letterhead]

[Date]

State Farm Insurance Company
Claims Department
123 Insurance Plaza
Anytown, USA 12345

Re: **Settlement Demand - Smith vs. Johnson**
**Claim Number:** SF-2024-001234
**Date of Loss:** March 15, 2024
**Insured:** Sarah Johnson

## Introduction
This letter constitutes a formal settlement demand on behalf of our client, John Smith, for injuries sustained in a motor vehicle accident on March 15, 2024. Our client was operating his vehicle in a lawful manner when your insured made an improper left turn, causing a T-bone collision.

## Liability Analysis
Your insured's negligence is clear and undisputed:
- Violation of traffic control signal requirements
- Failure to yield right-of-way to oncoming traffic
- Operation of commercial vehicle without due care

## Damages Incurred
Our client's damages include:
- **Medical Expenses**: $47,250.00 (billed to date)
- **Lost Wages**: $15,600.00 (6 weeks recovery)
- **Future Medical Costs**: $28,000.00 (estimated)
- **Pain and Suffering**: $84,150.00 (conservative estimate)
- **Total**: $175,000.00

## Settlement Demand
We demand settlement in the amount of **$175,000.00** within thirty (30) days of receipt of this letter. This demand is reasonable based on the strength of liability and well-documented damages.

## Alternative Dispute Resolution
If settlement cannot be reached, we are prepared to proceed with litigation. Please contact our office to discuss mediation or other ADR options.

Sincerely,

[Attorney Name]
Smith & Associates
[Contact Information]`
            break

        case "custom":
            title = "Custom Case Analysis"
            description = "AI-generated custom analysis based on case requirements"
            content = `# Case Strategy & Timeline

## Current Status
Case filed October 2024. Defendant's answer due in 21 days. Mediation scheduled for January 2025.

## Critical Deadlines
- **Answer Deadline**: November 15, 2024
- **Discovery Period**: November - February 2025
- **Mediation**: January 15, 2025
- **Trial Date**: June 2025 (if not settled)

## Action Items - Next 30 Days
1. [ ] File motion for traffic camera footage
2. [ ] Schedule plaintiff's deposition
3. [ ] Retain accident reconstruction expert
4. [ ] Prepare demand package for mediation

## Settlement Strategy
- **Opening Demand**: $175,000
- **Target Range**: $125,000 - $150,000
- **Walk-Away Point**: $100,000
- **BATNA**: Trial with estimated $200,000+ verdict

## Risk Assessment
- **Case Strength**: High (85% chance favorable verdict)
- **Settlement Probability**: Medium (60% chance pre-trial)
- **Appeal Risk**: Low (standard comparative negligence)

## Budget Allocation
- **Expert Witnesses**: $15,000 (accident reconstruction, vocational)
- **Discovery**: $8,000 (depositions, subpoenas)
- **Mediation**: $3,000
- **Trial Preparation**: $12,000 (if needed)`
            break
    }

    return {
        id: `mat_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        type,
        title,
        description,
        content,
        createdAt: now,
        updatedAt: now,
        caseId,
    }
}

// Re-export all mock data functions for easy importing

export {
    initializeMockData,
    mockCreateCaseAsync,
    mockLoadCasesAsync,
} from "./mock-api"
export {
    getBrandAssets,
    getBrandContent,
    getPageMeta,
    mockBrandAssets,
    mockBrandContent,
} from "./mock-brand"
export { mockCases } from "./mock-jobs"
export {
    mockCreateChat,
    mockGenerateChatResponse,
    mockGetChats,
    mockSendChatMessage,
} from "./mock-chats"
export {
    getBusinessHours,
    getContactForDepartment,
    getFormattedAddress,
    getSocialMediaLinks,
    mockContactInfo,
    mockSupportInfo,
} from "./mock-contact"
export { mockFileUpload } from "./mock-files"
export {
    mockBookmarkLearningPage,
    mockGetBookmarkedPages,
    mockGetLearningPage,
    mockGetLearningSections,
    mockGetUserLearningProgress,
    mockSearchLearningContent,
    mockUpdateLearningProgress,
} from "./mock-learn"
export { mockGenerateCaseMaterial } from "./mock-materials"
export {
    getMockCase,
    getMockCaseMaterials,
    shouldUseMockData,
} from "./mock-utils"

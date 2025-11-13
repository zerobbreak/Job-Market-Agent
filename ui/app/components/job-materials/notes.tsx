import {
    DocumentTextIcon,
    PencilIcon,
    PlusIcon,
    MagnifyingGlassIcon,
    TagIcon,
    CalendarIcon,
    BuildingOfficeIcon,
    BriefcaseIcon,
    ChatBubbleLeftRightIcon,
    ArrowPathIcon,
    CpuChipIcon,
} from "@heroicons/react/24/outline"
import { useCallback, useState } from "react"

interface Note {
    id: string
    title: string
    content: string
    type: 'interview' | 'application' | 'followup' | 'general'
    company?: string
    position?: string
    tags: string[]
    createdAt: Date
    updatedAt: Date
    isFavorite: boolean
}

function Notes(_props: any) {
    const [notes, setNotes] = useState<Note[]>([
        {
            id: '1',
            title: 'TechCorp Frontend Interview',
            content: 'Great discussion about React and TypeScript. They emphasized code quality and testing. Asked about state management patterns and performance optimization.',
            type: 'interview',
            company: 'TechCorp',
            position: 'Frontend Developer',
            tags: ['react', 'typescript', 'interview'],
            createdAt: new Date('2024-01-15'),
            updatedAt: new Date('2024-01-15'),
            isFavorite: true
        },
        {
            id: '2',
            title: 'StartupXYZ Application Notes',
            content: 'Applied for Product Manager role. Company focuses on AI-driven analytics. Need to highlight my experience with data visualization and user research.',
            type: 'application',
            company: 'StartupXYZ',
            position: 'Product Manager',
            tags: ['product-management', 'application'],
            createdAt: new Date('2024-01-10'),
            updatedAt: new Date('2024-01-10'),
            isFavorite: false
        }
    ])

    const [selectedNote, setSelectedNote] = useState<Note | null>(null)
    const [isCreating, setIsCreating] = useState(false)
    const [searchTerm, setSearchTerm] = useState('')
    const [selectedType, setSelectedType] = useState<string>('all')
    const [newNote, setNewNote] = useState({
        title: '',
        content: '',
        type: 'general' as Note['type'],
        company: '',
        position: '',
        tags: [] as string[]
    })

    const noteTypes = [
        { value: 'all', label: 'All Notes', icon: DocumentTextIcon },
        { value: 'interview', label: 'Interview', icon: ChatBubbleLeftRightIcon },
        { value: 'application', label: 'Application', icon: BriefcaseIcon },
        { value: 'followup', label: 'Follow-up', icon: ArrowPathIcon },
        { value: 'general', label: 'General', icon: DocumentTextIcon }
    ]

    const filteredNotes = notes.filter(note => {
        const matchesSearch = note.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                             note.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
                             note.company?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                             note.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))

        const matchesType = selectedType === 'all' || note.type === selectedType

        return matchesSearch && matchesType
    })

    const handleCreateNote = useCallback(() => {
        if (!newNote.title.trim()) return

        const note: Note = {
            id: Date.now().toString(),
            title: newNote.title,
            content: newNote.content,
            type: newNote.type,
            company: newNote.company || undefined,
            position: newNote.position || undefined,
            tags: newNote.tags,
            createdAt: new Date(),
            updatedAt: new Date(),
            isFavorite: false
        }

        setNotes(prev => [note, ...prev])
        setNewNote({
            title: '',
            content: '',
            type: 'general',
            company: '',
            position: '',
            tags: []
        })
        setIsCreating(false)
    }, [newNote])

    const handleUpdateNote = useCallback((updatedNote: Note) => {
        setNotes(prev => prev.map(note =>
            note.id === updatedNote.id ? { ...updatedNote, updatedAt: new Date() } : note
        ))
        setSelectedNote(null)
    }, [])

    const handleDeleteNote = useCallback((noteId: string) => {
        setNotes(prev => prev.filter(note => note.id !== noteId))
        if (selectedNote?.id === noteId) {
            setSelectedNote(null)
        }
    }, [selectedNote])

    const toggleFavorite = useCallback((noteId: string) => {
        setNotes(prev => prev.map(note =>
            note.id === noteId ? { ...note, isFavorite: !note.isFavorite } : note
        ))
    }, [])

    const addTag = (tag: string) => {
        if (!newNote.tags.includes(tag)) {
            setNewNote(prev => ({ ...prev, tags: [...prev.tags, tag] }))
        }
    }

    const removeTag = (tagToRemove: string) => {
        setNewNote(prev => ({ ...prev, tags: prev.tags.filter(tag => tag !== tagToRemove) }))
    }

    const getTypeIcon = (type: Note['type']) => {
        switch (type) {
            case 'interview': return ChatBubbleLeftRightIcon
            case 'application': return BriefcaseIcon
            case 'followup': return ArrowPathIcon
            default: return DocumentTextIcon
        }
    }

    const getTypeColor = (type: Note['type']) => {
        switch (type) {
            case 'interview': return 'text-blue-600 bg-blue-100'
            case 'application': return 'text-green-600 bg-green-100'
            case 'followup': return 'text-orange-600 bg-orange-100'
            default: return 'text-gray-600 bg-gray-100'
        }
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h3 className="penpot-heading-medium">Job Application Notes</h3>
                    <p className="penpot-body-medium text-[#7a7a7a] mt-1">
                        Organize and track all your job application activities and insights
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <button
                        type="button"
                        onClick={() => setIsCreating(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-[#4b92ff] text-white rounded-lg hover:bg-[#3a7be0] transition-colors"
                    >
                        <PlusIcon className="w-4 h-4" />
                        New Note
                    </button>
                </div>
            </div>

            {/* Search and Filters */}
            <div className="penpot-card p-6">
                <div className="flex flex-col md:flex-row gap-4">
                    <div className="flex-1 relative">
                        <MagnifyingGlassIcon className="w-4 h-4 absolute left-3 top-3 text-[#7a7a7a]" />
                        <input
                            type="text"
                            placeholder="Search notes..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full pl-10 penpot-input"
                        />
                    </div>
                    <div className="flex gap-2">
                        {noteTypes.map(type => {
                            const Icon = type.icon
                            return (
                                <button
                                    key={type.value}
                                    onClick={() => setSelectedType(type.value)}
                                    className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                                        selectedType === type.value
                                            ? 'bg-[#4b92ff] text-white'
                                            : 'bg-white border border-[#edebe5] text-[#7a7a7a] hover:bg-gray-50'
                                    }`}
                                >
                                    <Icon className="w-4 h-4" />
                                    {type.label}
                                </button>
                            )
                        })}
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Notes List */}
                <div className="lg:col-span-1">
                    <div className="penpot-card p-6">
                        <h4 className="text-lg font-semibold mb-4">Your Notes ({filteredNotes.length})</h4>
                        <div className="space-y-3 max-h-96 overflow-y-auto">
                            {filteredNotes.map(note => {
                                const TypeIcon = getTypeIcon(note.type)
                                return (
                                    <div
                                        key={note.id}
                                        onClick={() => setSelectedNote(note)}
                                        className={`p-4 rounded-lg border cursor-pointer transition-colors ${
                                            selectedNote?.id === note.id
                                                ? 'border-[#4b92ff] bg-blue-50'
                                                : 'border-[#edebe5] hover:border-[#4b92ff] hover:bg-gray-50'
                                        }`}
                                    >
                                        <div className="flex items-start justify-between mb-2">
                                            <h5 className="font-medium text-sm line-clamp-2">{note.title}</h5>
                                            <div className="flex items-center gap-1 ml-2">
                                                <TypeIcon className="w-3 h-3 text-[#7a7a7a]" />
                                                {note.isFavorite && (
                                                    <span className="text-yellow-500">★</span>
                                                )}
                                            </div>
                                        </div>
                                        <div className="text-xs text-[#7a7a7a] mb-2">
                                            {note.company && (
                                                <span className="flex items-center gap-1 mr-3">
                                                    <BuildingOfficeIcon className="w-3 h-3" />
                                                    {note.company}
                                                </span>
                                            )}
                                            <span className="flex items-center gap-1">
                                                <CalendarIcon className="w-3 h-3" />
                                                {note.updatedAt.toLocaleDateString()}
                                            </span>
                                        </div>
                                        <p className="text-xs text-[#7a7a7a] line-clamp-2">{note.content}</p>
                                        {note.tags.length > 0 && (
                                            <div className="flex gap-1 mt-2">
                                                {note.tags.slice(0, 3).map(tag => (
                                                    <span key={tag} className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs">
                                                        {tag}
                                                    </span>
                                                ))}
                                                {note.tags.length > 3 && (
                                                    <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs">
                                                        +{note.tags.length - 3}
                                                    </span>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                )
                            })}
                            {filteredNotes.length === 0 && (
                                <div className="text-center py-8 text-[#7a7a7a]">
                                    <DocumentTextIcon className="w-12 h-12 mx-auto mb-4 opacity-50" />
                                    <p>No notes found</p>
                                    <p className="text-sm">Create your first note to get started</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Note Editor */}
                <div className="lg:col-span-2">
                    {isCreating ? (
                        <div className="penpot-card p-6">
                            <h4 className="text-lg font-semibold mb-4">Create New Note</h4>
                            <div className="space-y-4">
                                <div>
                                    <label className="block font-medium mb-2">Title</label>
                                    <input
                                        type="text"
                                        value={newNote.title}
                                        onChange={(e) => setNewNote(prev => ({ ...prev, title: e.target.value }))}
                                        placeholder="Note title..."
                                        className="w-full penpot-input"
                                    />
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block font-medium mb-2">Type</label>
                                        <select
                                            value={newNote.type}
                                            onChange={(e) => setNewNote(prev => ({ ...prev, type: e.target.value as Note['type'] }))}
                                            className="w-full penpot-input"
                                        >
                                            <option value="general">General</option>
                                            <option value="interview">Interview</option>
                                            <option value="application">Application</option>
                                            <option value="followup">Follow-up</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block font-medium mb-2">Company (Optional)</label>
                                        <input
                                            type="text"
                                            value={newNote.company}
                                            onChange={(e) => setNewNote(prev => ({ ...prev, company: e.target.value }))}
                                            placeholder="Company name"
                                            className="w-full penpot-input"
                                        />
                                    </div>
                                </div>

                                {newNote.type !== 'general' && (
                                    <div>
                                        <label className="block font-medium mb-2">Position (Optional)</label>
                                        <input
                                            type="text"
                                            value={newNote.position}
                                            onChange={(e) => setNewNote(prev => ({ ...prev, position: e.target.value }))}
                                            placeholder="Job position"
                                            className="w-full penpot-input"
                                        />
                                    </div>
                                )}

                                <div>
                                    <label className="block font-medium mb-2">Content</label>
                                    <textarea
                                        value={newNote.content}
                                        onChange={(e) => setNewNote(prev => ({ ...prev, content: e.target.value }))}
                                        placeholder="Write your note content here..."
                                        className="w-full h-32 penpot-input resize-none"
                                    />
                                </div>

                                <div>
                                    <label className="block font-medium mb-2">Tags</label>
                                    <div className="flex gap-2 mb-2">
                                        {['interview', 'application', 'followup', 'important', 'urgent'].map(tag => (
                                            <button
                                                key={tag}
                                                onClick={() => addTag(tag)}
                                                className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm"
                                            >
                                                + {tag}
                                            </button>
                                        ))}
                                    </div>
                                    <div className="flex gap-2 flex-wrap">
                                        {newNote.tags.map(tag => (
                                            <span key={tag} className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm">
                                                <TagIcon className="w-3 h-3" />
                                                {tag}
                                                <button
                                                    onClick={() => removeTag(tag)}
                                                    className="ml-1 hover:text-red-600"
                                                >
                                                    ×
                                                </button>
                                            </span>
                                        ))}
                                    </div>
                                </div>

                                <div className="flex gap-3 pt-4">
                                    <button
                                        onClick={handleCreateNote}
                                        disabled={!newNote.title.trim()}
                                        className="px-4 py-2 bg-[#4b92ff] text-white rounded-lg hover:bg-[#3a7be0] disabled:opacity-50"
                                    >
                                        Create Note
                                    </button>
                                    <button
                                        onClick={() => setIsCreating(false)}
                                        className="px-4 py-2 border border-[#edebe5] rounded-lg hover:bg-gray-50"
                                    >
                                        Cancel
                                    </button>
                                </div>
                            </div>
                        </div>
                    ) : selectedNote ? (
                        <div className="penpot-card p-6">
                            <div className="flex items-center justify-between mb-4">
                                <div className="flex items-center gap-3">
                                    {(() => {
                                        const TypeIcon = getTypeIcon(selectedNote.type)
                                        return (
                                            <div className={`p-2 rounded-lg ${getTypeColor(selectedNote.type)}`}>
                                                <TypeIcon className="w-5 h-5" />
                                            </div>
                                        )
                                    })()}
                                    <div>
                                        <h4 className="text-lg font-semibold">{selectedNote.title}</h4>
                                        <div className="flex items-center gap-4 text-sm text-[#7a7a7a]">
                                            {selectedNote.company && (
                                                <span className="flex items-center gap-1">
                                                    <BuildingOfficeIcon className="w-4 h-4" />
                                                    {selectedNote.company}
                                                </span>
                                            )}
                                            <span className="flex items-center gap-1">
                                                <CalendarIcon className="w-4 h-4" />
                                                {selectedNote.updatedAt.toLocaleDateString()}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <button
                                        onClick={() => toggleFavorite(selectedNote.id)}
                                        className={`p-2 rounded hover:bg-gray-100 ${
                                            selectedNote.isFavorite ? 'text-yellow-500' : 'text-gray-400'
                                        }`}
                                    >
                                        ★
                                    </button>
                                    <button
                                        onClick={() => setSelectedNote(null)}
                                        className="p-2 rounded hover:bg-gray-100 text-[#7a7a7a]"
                                    >
                                        ✕
                                    </button>
                                </div>
                            </div>

                            {selectedNote.tags.length > 0 && (
                                <div className="flex gap-2 mb-4">
                                    {selectedNote.tags.map(tag => (
                                        <span key={tag} className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm">
                                            <TagIcon className="w-3 h-3" />
                                            {tag}
                                        </span>
                                    ))}
                                </div>
                            )}

                            <div className="bg-gray-50 border border-[#edebe5] rounded-lg p-4 mb-4">
                                <p className="whitespace-pre-wrap">{selectedNote.content}</p>
                            </div>

                            <div className="flex gap-3">
                                <button
                                    onClick={() => {
                                        // In a real app, this would open an edit mode
                                        alert('Edit functionality would open here')
                                    }}
                                    className="flex items-center gap-2 px-4 py-2 bg-[#4b92ff] text-white rounded-lg hover:bg-[#3a7be0]"
                                >
                                    <PencilIcon className="w-4 h-4" />
                                    Edit Note
                                </button>
                                <button
                                    onClick={() => handleDeleteNote(selectedNote.id)}
                                    className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                                >
                                    Delete Note
                                </button>
                            </div>
                        </div>
                    ) : (
                        <div className="penpot-card p-6 flex items-center justify-center h-64">
                            <div className="text-center text-[#7a7a7a]">
                                <DocumentTextIcon className="w-16 h-16 mx-auto mb-4 opacity-50" />
                                <h4 className="text-lg font-semibold mb-2">Select a Note</h4>
                                <p>Choose a note from the list to view its details</p>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* AI Enhancement Suggestion */}
            <div className="penpot-card p-6 bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200">
                <div className="flex items-center gap-3">
                    <CpuChipIcon className="w-6 h-6 text-blue-600" />
                    <div>
                        <h4 className="font-semibold text-blue-900">AI-Powered Note Enhancement</h4>
                        <p className="text-sm text-blue-700">
                            Let AI analyze your notes and suggest improvements, categorize content, or extract key insights.
                        </p>
                    </div>
                    <button className="ml-auto px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                        Enhance with AI
                    </button>
                </div>
            </div>
        </div>
    )
}

export default Notes

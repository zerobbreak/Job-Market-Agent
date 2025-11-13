import { useCallback, useState } from "react"

/**
 * Form field validation result
 */
interface FieldValidation {
    isValid: boolean
    errors: string[]
}

/**
 * Form validation function type
 */
type ValidationFn = (value: unknown) => FieldValidation

/**
 * Form field configuration
 */
interface FormField {
    value: unknown
    touched: boolean
    error: string | null
    validate?: ValidationFn
}

/**
 * Form state and actions
 */
interface UseFormReturn<T extends Record<string, unknown>> {
    /** Current form values */
    values: T
    /** Form field states */
    fields: Record<keyof T, FormField>
    /** Whether the entire form is valid */
    isValid: boolean
    /** Whether the form has been touched */
    isDirty: boolean
    /** Whether the form is currently being submitted */
    isSubmitting: boolean
    /** Set a field value */
    setValue: <K extends keyof T>(field: K, value: T[K]) => void
    /** Set multiple field values */
    setValues: (values: Partial<T>) => void
    /** Set field error */
    setError: (field: keyof T, error: string | null) => void
    /** Mark field as touched */
    touchField: (field: keyof T) => void
    /** Touch all fields */
    touchAll: () => void
    /** Reset form to initial values */
    reset: (newInitialValues?: Partial<T>) => void
    /** Handle form submission */
    handleSubmit: (
        onSubmit: (values: T) => void | Promise<void>
    ) => (e?: React.FormEvent) => Promise<void>
    /** Get field props for form inputs */
    getFieldProps: <K extends keyof T>(
        field: K
    ) => {
        value: T[K]
        onChange: (value: T[K]) => void
        onBlur: () => void
        error: string | null
        touched: boolean
    }
}

/**
 * Custom hook for managing form state with validation
 * Provides a complete form management solution with validation, error handling, and submission
 *
 * @param initialValues - Initial form values
 * @param validations - Optional validation functions for each field
 * @returns Form state and helper functions
 *
 * @example
 * ```tsx
 * const validation = {
 *   email: (value: string) => ({
 *     isValid: /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
 *     errors: value ? [] : ['Email is required']
 *   })
 * };
 *
 * const { values, getFieldProps, handleSubmit, isValid } = useForm(
 *   { email: '', password: '' },
 *   validation
 * );
 *
 * return (
 *   <form onSubmit={handleSubmit(onSubmit)}>
 *     <input {...getFieldProps('email')} />
 *     <button type="submit" disabled={!isValid}>Submit</button>
 *   </form>
 * );
 * ```
 */
export function useForm<T extends Record<string, unknown>>(
    initialValues: T,
    validations?: Partial<Record<keyof T, ValidationFn>>
): UseFormReturn<T> {
    const [values, setValues] = useState<T>(initialValues)
    const [fields, setFields] = useState<Record<keyof T, FormField>>(() => {
        const initialFields: Record<keyof T, FormField> = {} as Record<keyof T, FormField>
        for (const key in initialValues) {
            initialFields[key] = {
                value: initialValues[key],
                touched: false,
                error: null,
                validate: validations?.[key],
            }
        }
        return initialFields
    })
    const [isSubmitting, setIsSubmitting] = useState(false)

    // Validate a single field
    const validateField = useCallback(
        (field: keyof T, value: unknown): string | null => {
            const validator = validations?.[field]
            if (!validator) return null

            const result = validator(value)
            return result.isValid ? null : result.errors[0] || "Invalid value"
        },
        [validations]
    )

    // Set a field value
    const setValue = useCallback(
        <K extends keyof T>(field: K, value: T[K]) => {
            setValues((prev) => ({ ...prev, [field]: value }))

            setFields((prev) => ({
                ...prev,
                [field]: {
                    ...prev[field],
                    value,
                    error: prev[field].touched ? validateField(field, value) : prev[field].error,
                },
            }))
        },
        [validateField]
    )

    // Set multiple field values
    const setValuesMultiple = useCallback(
        (newValues: Partial<T>) => {
            setValues((prev) => ({ ...prev, ...newValues }))

            setFields((prev) => {
                const updated = { ...prev }
                for (const field in newValues) {
                    const value = newValues[field]
                    if (value !== undefined) {
                        updated[field] = {
                            ...prev[field],
                            value,
                            error: prev[field].touched
                                ? validateField(field, value)
                                : prev[field].error,
                        }
                    }
                }
                return updated
            })
        },
        [validateField]
    )

    // Set field error
    const setError = useCallback((field: keyof T, error: string | null) => {
        setFields((prev) => ({
            ...prev,
            [field]: {
                ...prev[field],
                error,
            },
        }))
    }, [])

    // Mark field as touched
    const touchField = useCallback(
        (field: keyof T) => {
            setFields((prev) => ({
                ...prev,
                [field]: {
                    ...prev[field],
                    touched: true,
                    error: validateField(field, prev[field].value),
                },
            }))
        },
        [validateField]
    )

    // Touch all fields
    const touchAll = useCallback(() => {
        setFields((prev) => {
            const updated = { ...prev }
            for (const field in updated) {
                updated[field] = {
                    ...updated[field],
                    touched: true,
                    error: validateField(field, updated[field].value),
                }
            }
            return updated
        })
    }, [validateField])

    // Reset form
    const reset = useCallback(
        (newInitialValues?: Partial<T>) => {
            const resetValues = { ...initialValues, ...newInitialValues }
            setValues(resetValues)
            setIsSubmitting(false)

            setFields(() => {
                const resetFields: Record<keyof T, FormField> = {} as Record<keyof T, FormField>
                for (const key in resetValues) {
                    resetFields[key] = {
                        value: resetValues[key],
                        touched: false,
                        error: null,
                        validate: validations?.[key],
                    }
                }
                return resetFields
            })
        },
        [initialValues, validations]
    )

    // Handle form submission
    const handleSubmit = useCallback(
        (onSubmit: (values: T) => void | Promise<void>) => async (e?: React.FormEvent) => {
            if (e) {
                e.preventDefault()
            }

            // Touch all fields to show validation errors
            touchAll()

            // Check if form is valid
            const hasErrors = Object.values(fields).some((field) => field.error)
            if (hasErrors) {
                return
            }

            setIsSubmitting(true)
            try {
                await onSubmit(values)
            } finally {
                setIsSubmitting(false)
            }
        },
        [values, fields, touchAll]
    )

    // Get field props for form inputs
    const getFieldProps = useCallback(
        <K extends keyof T>(field: K) => ({
            value: values[field],
            onChange: (value: T[K]) => setValue(field, value),
            onBlur: () => touchField(field),
            error: fields[field].error,
            touched: fields[field].touched,
        }),
        [values, fields, setValue, touchField]
    )

    // Calculate form state
    const isValid = Object.values(fields).every((field) => !field.error)
    const isDirty = Object.values(fields).some((field) => field.touched)

    return {
        values,
        fields,
        isValid,
        isDirty,
        isSubmitting,
        setValue,
        setValues: setValuesMultiple,
        setError,
        touchField,
        touchAll,
        reset,
        handleSubmit,
        getFieldProps,
    }
}

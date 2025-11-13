/**
 * Centralized Logging System
 *
 * Provides consistent logging across the application with different log levels,
 * context information, and environment-aware output.
 */

export enum LogLevel {
    DEBUG = 0,
    INFO = 1,
    WARN = 2,
    ERROR = 3,
    OFF = 4,
}

interface LogContext {
    component?: string
    action?: string
    userId?: string
    sessionId?: string
    [key: string]: unknown
}

interface LogEntry {
    level: LogLevel
    message: string
    context?: LogContext
    timestamp: Date
    stack?: string
}

class Logger {
    private static instance: Logger
    private logLevel: LogLevel = LogLevel.INFO
    private enableConsole = true
    private enablePersistence = false

    private constructor() {
        // Set log level based on environment
        if (typeof window !== "undefined") {
            const env = import.meta.env?.MODE || "development"
            this.logLevel = env === "development" ? LogLevel.DEBUG : LogLevel.WARN
        }
    }

    static getInstance(): Logger {
        if (!Logger.instance) {
            Logger.instance = new Logger()
        }
        return Logger.instance
    }

    setLogLevel(level: LogLevel): void {
        this.logLevel = level
    }

    enableConsoleOutput(enabled: boolean): void {
        this.enableConsole = enabled
    }

    setPersistenceEnabled(enabled: boolean): void {
        this.enablePersistence = enabled
    }

    private shouldLog(level: LogLevel): boolean {
        return level >= this.logLevel
    }

    private formatMessage(entry: LogEntry): string {
        const timestamp = entry.timestamp.toISOString()
        const level = LogLevel[entry.level]
        const context = entry.context ? ` | ${JSON.stringify(entry.context)}` : ""
        return `[${timestamp}] ${level}: ${entry.message}${context}`
    }

    private log(level: LogLevel, message: string, context?: LogContext, error?: Error): void {
        if (!this.shouldLog(level)) return

        const entry: LogEntry = {
            level,
            message,
            context,
            timestamp: new Date(),
            stack: error?.stack,
        }

        const formattedMessage = this.formatMessage(entry)

        // Console output
        if (this.enableConsole) {
            const consoleMethod =
                level === LogLevel.ERROR
                    ? "error"
                    : level === LogLevel.WARN
                      ? "warn"
                      : level === LogLevel.INFO
                        ? "info"
                        : level === LogLevel.DEBUG
                          ? "debug"
                          : "log"

            if (error) {
                console[consoleMethod](formattedMessage, error)
            } else {
                console[consoleMethod](formattedMessage)
            }
        }

        // Future: Add persistence, remote logging, etc.
        if (this.enablePersistence) {
            // TODO: Implement persistent logging (localStorage, IndexedDB, etc.)
        }
    }

    debug(message: string, context?: LogContext): void {
        this.log(LogLevel.DEBUG, message, context)
    }

    info(message: string, context?: LogContext): void {
        this.log(LogLevel.INFO, message, context)
    }

    warn(message: string, context?: LogContext): void {
        this.log(LogLevel.WARN, message, context)
    }

    error(message: string, error?: Error, context?: LogContext): void {
        this.log(LogLevel.ERROR, message, { ...context, error: error?.message }, error)
    }

    // Specialized logging methods
    auth(message: string, context?: LogContext): void {
        this.info(message, { ...context, category: "auth" })
    }

    api(message: string, context?: LogContext): void {
        this.info(message, { ...context, category: "api" })
    }

    component(componentName: string, message: string, context?: LogContext): void {
        this.debug(message, { ...context, component: componentName })
    }

    performance(operation: string, duration: number, context?: LogContext): void {
        this.info(`Performance: ${operation} took ${duration}ms`, {
            ...context,
            category: "performance",
            operation,
            duration,
        })
    }

    // Create a child logger with preset context
    child(context: LogContext): Logger {
        const childLogger = Object.create(this) as Logger
        childLogger.log = (
            level: LogLevel,
            message: string,
            childContext?: LogContext,
            error?: Error
        ) => {
            this.log(level, message, { ...context, ...childContext }, error)
        }
        return childLogger
    }
}

// Export singleton instance
export const logger = Logger.getInstance()

// Export types for external use
export type { LogContext, LogEntry }

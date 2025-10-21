package logger

import (
	"fmt"
	"io"
	"log"
	"os"
	"strings"
)

// LogLevel represents the logging level
type LogLevel int

const (
	LevelDebug LogLevel = iota
	LevelInfo
	LevelWarn
	LevelError
)

// String returns the string representation of the log level
func (l LogLevel) String() string {
	switch l {
	case LevelDebug:
		return "DEBUG"
	case LevelInfo:
		return "INFO"
	case LevelWarn:
		return "WARN"
	case LevelError:
		return "ERROR"
	default:
		return "UNKNOWN"
	}
}

// Logger represents the application logger
type Logger struct {
	level  LogLevel
	format string
	output io.Writer
}

var globalLogger *Logger

// Init initializes the global logger
func Init(level, format string) {
	logLevel := parseLevel(level)

	logger := &Logger{
		level:  logLevel,
		format: format,
		output: os.Stderr,
	}

	globalLogger = logger

	// Configure standard log package
	log.SetOutput(logger.output)
	log.SetFlags(log.LstdFlags | log.Lshortfile)
}

// parseLevel converts string to LogLevel
func parseLevel(level string) LogLevel {
	switch strings.ToLower(level) {
	case "debug":
		return LevelDebug
	case "info":
		return LevelInfo
	case "warn", "warning":
		return LevelWarn
	case "error":
		return LevelError
	default:
		return LevelInfo
	}
}

// Get returns the global logger
func Get() *Logger {
	if globalLogger == nil {
		// Initialize with defaults if not already done
		Init("info", "text")
	}
	return globalLogger
}

// SetOutput sets the logger output
func SetOutput(output io.Writer) {
	if globalLogger != nil {
		globalLogger.output = output
		log.SetOutput(output)
	}
}

// Debug logs a debug message
func Debug(msg string, args ...interface{}) {
	if globalLogger != nil && globalLogger.level <= LevelDebug {
		globalLogger.log(LevelDebug, msg, args...)
	}
}

// Info logs an info message
func Info(msg string, args ...interface{}) {
	if globalLogger != nil && globalLogger.level <= LevelInfo {
		globalLogger.log(LevelInfo, msg, args...)
	}
}

// Warn logs a warning message
func Warn(msg string, args ...interface{}) {
	if globalLogger != nil && globalLogger.level <= LevelWarn {
		globalLogger.log(LevelWarn, msg, args...)
	}
}

// Error logs an error message
func Error(msg string, args ...interface{}) {
	if globalLogger != nil && globalLogger.level <= LevelError {
		globalLogger.log(LevelError, msg, args...)
	}
}

// log writes a log message
func (l *Logger) log(level LogLevel, msg string, args ...interface{}) {
	if len(args) > 0 {
		msg = fmt.Sprintf(msg, args...)
	}

	if l.format == "json" {
		// JSON format logging (simplified)
		fmt.Fprintf(l.output, `{"level":"%s","message":"%s"}`+"\n", level.String(), msg)
	} else {
		// Text format logging
		fmt.Fprintf(l.output, "[%s] %s\n", level.String(), msg)
	}
}

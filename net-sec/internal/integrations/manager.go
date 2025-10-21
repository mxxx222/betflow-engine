package integrations

import (
	"context"
	"crypto/tls"
	"fmt"
	"net/http"
	"sync"
	"time"
)

// IntegrationManager manages external API integrations with GDPR compliance
type IntegrationManager struct {
	integrations  map[string]Integration
	config        *IntegrationConfig
	httpClient    *http.Client
	auditLog      AuditLogger
	dataMinimizer DataMinimizer
	mutex         sync.RWMutex
}

// IntegrationConfig contains configuration for external integrations
type IntegrationConfig struct {
	RequestTimeout     time.Duration        `json:"request_timeout"`
	RetryAttempts      int                  `json:"retry_attempts"`
	RetryBackoff       time.Duration        `json:"retry_backoff"`
	DataMinimization   bool                 `json:"data_minimization"`
	PseudonymizeData   bool                 `json:"pseudonymize_data"`
	AuditAllRequests   bool                 `json:"audit_all_requests"`
	TLSConfig          *tls.Config          `json:"-"`
	RateLimits         map[string]RateLimit `json:"rate_limits"`
	DataClassification map[string]string    `json:"data_classification"`
}

// RateLimit defines rate limiting for each integration
type RateLimit struct {
	RequestsPerMinute int           `json:"requests_per_minute"`
	BurstSize         int           `json:"burst_size"`
	WindowDuration    time.Duration `json:"window_duration"`
}

// Integration interface for external service integrations
type Integration interface {
	Name() string
	Authenticate(credentials map[string]string) error
	SendData(ctx context.Context, data *IntegrationData) error
	RetrieveData(ctx context.Context, query *DataQuery) (*IntegrationData, error)
	ValidateConnection() error
	GetMetrics() *IntegrationMetrics
}

// IntegrationData represents data being sent/received from external services
type IntegrationData struct {
	ID                string                 `json:"id"`
	Type              string                 `json:"type"`           // "incident", "task", "document", etc.
	Classification    string                 `json:"classification"` // GDPR data classification
	Content           map[string]interface{} `json:"content"`
	Metadata          map[string]interface{} `json:"metadata"`
	PersonalData      []PersonalDataField    `json:"personal_data,omitempty"`
	LegalBasis        string                 `json:"legal_basis"`
	ProcessingPurpose string                 `json:"processing_purpose"`
	RetentionPeriod   time.Duration          `json:"retention_period"`
	CreatedAt         time.Time              `json:"created_at"`
	UpdatedAt         time.Time              `json:"updated_at"`
}

// PersonalDataField represents a field containing personal data
type PersonalDataField struct {
	Field              string `json:"field"`
	DataCategory       string `json:"data_category"` // "personal", "sensitive", "special"
	OriginalValue      string `json:"original_value,omitempty"`
	PseudonymizedValue string `json:"pseudonymized_value,omitempty"`
	IsMinimized        bool   `json:"is_minimized"`
}

// DataQuery represents a query for external data
type DataQuery struct {
	Type          string                 `json:"type"`
	Filters       map[string]interface{} `json:"filters"`
	Limit         int                    `json:"limit"`
	Offset        int                    `json:"offset"`
	Fields        []string               `json:"fields,omitempty"` // Data minimization - only request needed fields
	DateRange     *DateRange             `json:"date_range,omitempty"`
	LegalBasis    string                 `json:"legal_basis"`
	Justification string                 `json:"justification"`
}

// DateRange represents a date range for queries
type DateRange struct {
	Start time.Time `json:"start"`
	End   time.Time `json:"end"`
}

// IntegrationMetrics contains metrics for external integrations
type IntegrationMetrics struct {
	TotalRequests       int64         `json:"total_requests"`
	SuccessfulRequests  int64         `json:"successful_requests"`
	FailedRequests      int64         `json:"failed_requests"`
	AverageResponseTime time.Duration `json:"average_response_time"`
	LastRequestTime     time.Time     `json:"last_request_time"`
	DataSent            int64         `json:"data_sent_bytes"`
	DataReceived        int64         `json:"data_received_bytes"`
	PersonalDataFields  int64         `json:"personal_data_fields"`
	PseudonymizedFields int64         `json:"pseudonymized_fields"`
	MinimizedFields     int64         `json:"minimized_fields"`
}

// AuditLogger interface for integration audit events
type AuditLogger interface {
	LogIntegrationEvent(event IntegrationAuditEvent)
	LogDataTransfer(event DataTransferEvent)
	LogPersonalDataAccess(event PersonalDataAccessEvent)
}

// DataMinimizer interface for data minimization operations
type DataMinimizer interface {
	MinimizeData(data map[string]interface{}, purpose string) map[string]interface{}
	PseudonymizeFields(data map[string]interface{}, fields []string) error
	ClassifyData(data map[string]interface{}) map[string]string
}

// IntegrationAuditEvent represents an integration audit event
type IntegrationAuditEvent struct {
	ID           string                 `json:"id"`
	Timestamp    time.Time              `json:"timestamp"`
	Integration  string                 `json:"integration"`
	Operation    string                 `json:"operation"` // "send", "retrieve", "authenticate"
	UserID       string                 `json:"user_id,omitempty"`
	Success      bool                   `json:"success"`
	Error        string                 `json:"error,omitempty"`
	DataType     string                 `json:"data_type,omitempty"`
	RecordsCount int                    `json:"records_count,omitempty"`
	LegalBasis   string                 `json:"legal_basis,omitempty"`
	Purpose      string                 `json:"purpose,omitempty"`
	Metadata     map[string]interface{} `json:"metadata,omitempty"`
}

// DataTransferEvent represents a data transfer audit event
type DataTransferEvent struct {
	ID                     string    `json:"id"`
	Timestamp              time.Time `json:"timestamp"`
	SourceIntegration      string    `json:"source_integration"`
	DestinationIntegration string    `json:"destination_integration"`
	DataType               string    `json:"data_type"`
	RecordsTransferred     int       `json:"records_transferred"`
	PersonalDataFields     int       `json:"personal_data_fields"`
	PseudonymizedFields    int       `json:"pseudonymized_fields"`
	MinimizedFields        int       `json:"minimized_fields"`
	LegalBasis             string    `json:"legal_basis"`
	Purpose                string    `json:"purpose"`
	Success                bool      `json:"success"`
	Error                  string    `json:"error,omitempty"`
}

// PersonalDataAccessEvent represents personal data access from external systems
type PersonalDataAccessEvent struct {
	ID             string                 `json:"id"`
	Timestamp      time.Time              `json:"timestamp"`
	Integration    string                 `json:"integration"`
	UserID         string                 `json:"user_id"`
	DataSubjectID  string                 `json:"data_subject_id,omitempty"`
	DataCategory   string                 `json:"data_category"`
	AccessType     string                 `json:"access_type"` // "read", "write", "delete"
	LegalBasis     string                 `json:"legal_basis"`
	Justification  string                 `json:"justification"`
	FieldsAccessed []string               `json:"fields_accessed"`
	Success        bool                   `json:"success"`
	Metadata       map[string]interface{} `json:"metadata,omitempty"`
}

// NewIntegrationManager creates a new integration manager
func NewIntegrationManager(config *IntegrationConfig, auditLog AuditLogger, dataMinimizer DataMinimizer) *IntegrationManager {
	httpClient := &http.Client{
		Timeout: config.RequestTimeout,
		Transport: &http.Transport{
			TLSClientConfig: config.TLSConfig,
		},
	}

	return &IntegrationManager{
		integrations:  make(map[string]Integration),
		config:        config,
		httpClient:    httpClient,
		auditLog:      auditLog,
		dataMinimizer: dataMinimizer,
	}
}

// RegisterIntegration registers a new external integration
func (im *IntegrationManager) RegisterIntegration(integration Integration) error {
	im.mutex.Lock()
	defer im.mutex.Unlock()

	name := integration.Name()
	if _, exists := im.integrations[name]; exists {
		return fmt.Errorf("integration %s already registered", name)
	}

	im.integrations[name] = integration

	// Log registration
	if im.auditLog != nil {
		event := IntegrationAuditEvent{
			ID:          generateEventID(),
			Timestamp:   time.Now(),
			Integration: name,
			Operation:   "register",
			Success:     true,
		}
		im.auditLog.LogIntegrationEvent(event)
	}

	return nil
}

// SendDataWithCompliance sends data to external system with GDPR compliance
func (im *IntegrationManager) SendDataWithCompliance(ctx context.Context, integrationName string, data *IntegrationData, userID string) error {
	im.mutex.RLock()
	integration, exists := im.integrations[integrationName]
	im.mutex.RUnlock()

	if !exists {
		return fmt.Errorf("integration %s not found", integrationName)
	}

	// Apply data minimization if enabled
	if im.config.DataMinimization && im.dataMinimizer != nil {
		data.Content = im.dataMinimizer.MinimizeData(data.Content, data.ProcessingPurpose)
	}

	// Apply pseudonymization if enabled
	if im.config.PseudonymizeData && im.dataMinimizer != nil {
		personalDataFields := make([]string, 0)
		for _, field := range data.PersonalData {
			personalDataFields = append(personalDataFields, field.Field)
		}

		if len(personalDataFields) > 0 {
			if err := im.dataMinimizer.PseudonymizeFields(data.Content, personalDataFields); err != nil {
				return fmt.Errorf("pseudonymization failed: %w", err)
			}
		}
	}

	// Send data
	err := integration.SendData(ctx, data)

	// Log the operation
	if im.auditLog != nil {
		event := IntegrationAuditEvent{
			ID:           generateEventID(),
			Timestamp:    time.Now(),
			Integration:  integrationName,
			Operation:    "send",
			UserID:       userID,
			Success:      err == nil,
			DataType:     data.Type,
			RecordsCount: 1,
			LegalBasis:   data.LegalBasis,
			Purpose:      data.ProcessingPurpose,
		}

		if err != nil {
			event.Error = err.Error()
		}

		im.auditLog.LogIntegrationEvent(event)

		// Log personal data access
		if len(data.PersonalData) > 0 {
			pdEvent := PersonalDataAccessEvent{
				ID:            generateEventID(),
				Timestamp:     time.Now(),
				Integration:   integrationName,
				UserID:        userID,
				DataCategory:  data.Classification,
				AccessType:    "write",
				LegalBasis:    data.LegalBasis,
				Justification: data.ProcessingPurpose,
				Success:       err == nil,
			}

			for _, field := range data.PersonalData {
				pdEvent.FieldsAccessed = append(pdEvent.FieldsAccessed, field.Field)
			}

			im.auditLog.LogPersonalDataAccess(pdEvent)
		}
	}

	return err
}

// RetrieveDataWithCompliance retrieves data from external system with GDPR compliance
func (im *IntegrationManager) RetrieveDataWithCompliance(ctx context.Context, integrationName string, query *DataQuery, userID string) (*IntegrationData, error) {
	im.mutex.RLock()
	integration, exists := im.integrations[integrationName]
	im.mutex.RUnlock()

	if !exists {
		return nil, fmt.Errorf("integration %s not found", integrationName)
	}

	// Validate legal basis and justification
	if query.LegalBasis == "" {
		return nil, fmt.Errorf("legal basis required for data retrieval")
	}

	if query.Justification == "" {
		return nil, fmt.Errorf("business justification required for data retrieval")
	}

	// Apply field limitation for data minimization
	if im.config.DataMinimization && len(query.Fields) == 0 {
		return nil, fmt.Errorf("specific fields must be requested for data minimization compliance")
	}

	// Retrieve data
	data, err := integration.RetrieveData(ctx, query)

	// Apply post-retrieval processing if successful
	if err == nil && data != nil && im.dataMinimizer != nil {
		// Classify data
		if im.config.DataMinimization {
			classifications := im.dataMinimizer.ClassifyData(data.Content)
			for field, classification := range classifications {
				if classification == "personal" || classification == "sensitive" {
					data.PersonalData = append(data.PersonalData, PersonalDataField{
						Field:        field,
						DataCategory: classification,
					})
				}
			}
		}

		// Apply pseudonymization to personal data fields
		if im.config.PseudonymizeData && len(data.PersonalData) > 0 {
			personalFields := make([]string, 0)
			for _, field := range data.PersonalData {
				personalFields = append(personalFields, field.Field)
			}

			if err := im.dataMinimizer.PseudonymizeFields(data.Content, personalFields); err != nil {
				return nil, fmt.Errorf("post-retrieval pseudonymization failed: %w", err)
			}
		}
	}

	// Log the operation
	if im.auditLog != nil {
		event := IntegrationAuditEvent{
			ID:          generateEventID(),
			Timestamp:   time.Now(),
			Integration: integrationName,
			Operation:   "retrieve",
			UserID:      userID,
			Success:     err == nil,
			DataType:    query.Type,
			LegalBasis:  query.LegalBasis,
			Purpose:     query.Justification,
		}

		if err != nil {
			event.Error = err.Error()
		} else if data != nil {
			event.RecordsCount = 1
		}

		im.auditLog.LogIntegrationEvent(event)

		// Log personal data access if successful
		if err == nil && data != nil && len(data.PersonalData) > 0 {
			pdEvent := PersonalDataAccessEvent{
				ID:            generateEventID(),
				Timestamp:     time.Now(),
				Integration:   integrationName,
				UserID:        userID,
				DataCategory:  data.Classification,
				AccessType:    "read",
				LegalBasis:    query.LegalBasis,
				Justification: query.Justification,
				Success:       true,
			}

			for _, field := range data.PersonalData {
				pdEvent.FieldsAccessed = append(pdEvent.FieldsAccessed, field.Field)
			}

			im.auditLog.LogPersonalDataAccess(pdEvent)
		}
	}

	return data, err
}

// ValidateCompliance validates that an integration meets GDPR compliance requirements
func (im *IntegrationManager) ValidateCompliance(integrationName string) (*ComplianceReport, error) {
	im.mutex.RLock()
	integration, exists := im.integrations[integrationName]
	im.mutex.RUnlock()

	if !exists {
		return nil, fmt.Errorf("integration %s not found", integrationName)
	}

	report := &ComplianceReport{
		IntegrationName: integrationName,
		Timestamp:       time.Now(),
		Checks:          make([]ComplianceCheck, 0),
	}

	// Check connection
	connErr := integration.ValidateConnection()
	report.Checks = append(report.Checks, ComplianceCheck{
		Name:        "Connection Validation",
		Description: "Verify integration can connect to external service",
		Passed:      connErr == nil,
		Error:       getErrorString(connErr),
	})

	// Check data minimization configuration
	report.Checks = append(report.Checks, ComplianceCheck{
		Name:        "Data Minimization",
		Description: "Verify data minimization is enabled",
		Passed:      im.config.DataMinimization,
		Details:     fmt.Sprintf("Data minimization enabled: %t", im.config.DataMinimization),
	})

	// Check pseudonymization configuration
	report.Checks = append(report.Checks, ComplianceCheck{
		Name:        "Pseudonymization",
		Description: "Verify pseudonymization is enabled for personal data",
		Passed:      im.config.PseudonymizeData,
		Details:     fmt.Sprintf("Pseudonymization enabled: %t", im.config.PseudonymizeData),
	})

	// Check audit logging
	report.Checks = append(report.Checks, ComplianceCheck{
		Name:        "Audit Logging",
		Description: "Verify all requests are audited",
		Passed:      im.auditLog != nil && im.config.AuditAllRequests,
		Details:     fmt.Sprintf("Audit logging enabled: %t", im.config.AuditAllRequests),
	})

	// Check TLS configuration
	report.Checks = append(report.Checks, ComplianceCheck{
		Name:        "TLS Security",
		Description: "Verify TLS is properly configured",
		Passed:      im.config.TLSConfig != nil,
		Details:     fmt.Sprintf("TLS config present: %t", im.config.TLSConfig != nil),
	})

	// Calculate overall compliance score
	passedChecks := 0
	for _, check := range report.Checks {
		if check.Passed {
			passedChecks++
		}
	}

	report.ComplianceScore = float64(passedChecks) / float64(len(report.Checks))
	report.IsCompliant = report.ComplianceScore >= 0.8 // 80% threshold

	return report, nil
}

// ComplianceReport represents a compliance validation report
type ComplianceReport struct {
	IntegrationName string            `json:"integration_name"`
	Timestamp       time.Time         `json:"timestamp"`
	IsCompliant     bool              `json:"is_compliant"`
	ComplianceScore float64           `json:"compliance_score"`
	Checks          []ComplianceCheck `json:"checks"`
}

// ComplianceCheck represents a single compliance check
type ComplianceCheck struct {
	Name        string `json:"name"`
	Description string `json:"description"`
	Passed      bool   `json:"passed"`
	Error       string `json:"error,omitempty"`
	Details     string `json:"details,omitempty"`
}

// GetIntegrationMetrics returns aggregated metrics for all integrations
func (im *IntegrationManager) GetIntegrationMetrics() map[string]*IntegrationMetrics {
	im.mutex.RLock()
	defer im.mutex.RUnlock()

	metrics := make(map[string]*IntegrationMetrics)
	for name, integration := range im.integrations {
		metrics[name] = integration.GetMetrics()
	}

	return metrics
}

// Helper functions
func generateEventID() string {
	return fmt.Sprintf("event_%d", time.Now().UnixNano())
}

func getErrorString(err error) string {
	if err != nil {
		return err.Error()
	}
	return ""
}

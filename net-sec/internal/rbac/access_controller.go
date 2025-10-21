package rbac

import (
	"fmt"
	"sync"
	"time"
)

// AccessController manages role-based access control with GDPR compliance
type AccessController struct {
	roles       map[string]*Role
	users       map[string]*User
	permissions map[string]*Permission
	sessions    map[string]*Session
	auditLog    AuditLogger
	mutex       sync.RWMutex
	config      *RBACConfig
}

// RBACConfig contains RBAC configuration settings
type RBACConfig struct {
	SessionTimeout        time.Duration `json:"session_timeout"`
	MaxFailedAttempts     int           `json:"max_failed_attempts"`
	LockoutDuration       time.Duration `json:"lockout_duration"`
	RequireMFA            bool          `json:"require_mfa"`
	AuditAllAccess        bool          `json:"audit_all_access"`
	PrivilegeEscalation   bool          `json:"privilege_escalation_detection"`
	DataClassificationReq bool          `json:"data_classification_required"`
}

// User represents a system user with GDPR data subject rights
type User struct {
	ID                string                 `json:"id"`
	Username          string                 `json:"username"`
	Email             string                 `json:"email"`
	Roles             []string               `json:"roles"`
	IsActive          bool                   `json:"is_active"`
	IsLocked          bool                   `json:"is_locked"`
	FailedAttempts    int                    `json:"failed_attempts"`
	LastFailedAttempt *time.Time             `json:"last_failed_attempt"`
	LastLogin         *time.Time             `json:"last_login"`
	MFAEnabled        bool                   `json:"mfa_enabled"`
	CreatedAt         time.Time              `json:"created_at"`
	UpdatedAt         time.Time              `json:"updated_at"`
	DataSubjectID     string                 `json:"data_subject_id,omitempty"` // GDPR data subject reference
	ConsentRecords    []ConsentRecord        `json:"consent_records,omitempty"`
	Metadata          map[string]interface{} `json:"metadata,omitempty"`
}

// Role defines a collection of permissions for GDPR data processing
type Role struct {
	ID                 string                 `json:"id"`
	Name               string                 `json:"name"`
	Description        string                 `json:"description"`
	Permissions        []string               `json:"permissions"`
	DataCategories     []string               `json:"data_categories"`     // GDPR data categories this role can access
	ProcessingPurposes []string               `json:"processing_purposes"` // GDPR processing purposes
	LegalBases         []string               `json:"legal_bases"`         // GDPR legal bases for processing
	IsBuiltIn          bool                   `json:"is_built_in"`
	RequiresApproval   bool                   `json:"requires_approval"`    // Role assignment needs approval
	MaxSessionDuration time.Duration          `json:"max_session_duration"` // Override default session timeout
	AllowedIPRanges    []string               `json:"allowed_ip_ranges,omitempty"`
	TimeRestrictions   *TimeRestrictions      `json:"time_restrictions,omitempty"`
	CreatedAt          time.Time              `json:"created_at"`
	UpdatedAt          time.Time              `json:"updated_at"`
	Metadata           map[string]interface{} `json:"metadata,omitempty"`
}

// Permission defines specific access rights with GDPR context
type Permission struct {
	ID                    string                 `json:"id"`
	Name                  string                 `json:"name"`
	Description           string                 `json:"description"`
	Resource              string                 `json:"resource"`               // What resource this permission applies to
	Action                string                 `json:"action"`                 // What action is allowed
	DataClassification    string                 `json:"data_classification"`    // "public", "internal", "confidential", "restricted"
	GDPRImplications      []string               `json:"gdpr_implications"`      // GDPR articles this permission relates to
	RequiresJustification bool                   `json:"requires_justification"` // Must provide business justification
	IsHighRisk            bool                   `json:"is_high_risk"`           // Requires additional monitoring
	CreatedAt             time.Time              `json:"created_at"`
	Metadata              map[string]interface{} `json:"metadata,omitempty"`
}

// Session represents an authenticated user session
type Session struct {
	ID                 string                 `json:"id"`
	UserID             string                 `json:"user_id"`
	CreatedAt          time.Time              `json:"created_at"`
	ExpiresAt          time.Time              `json:"expires_at"`
	LastActivity       time.Time              `json:"last_activity"`
	IPAddress          string                 `json:"ip_address"`
	UserAgent          string                 `json:"user_agent"`
	MFAVerified        bool                   `json:"mfa_verified"`
	ElevatedPrivileges []string               `json:"elevated_privileges,omitempty"` // Temporary privilege escalations
	ElevatedExpiresAt  *time.Time             `json:"elevated_expires_at,omitempty"`
	AccessedResources  map[string]time.Time   `json:"accessed_resources"` // Resource -> last access time
	Metadata           map[string]interface{} `json:"metadata,omitempty"`
}

// ConsentRecord tracks GDPR consent for data processing
type ConsentRecord struct {
	ID                string     `json:"id"`
	DataCategory      string     `json:"data_category"`
	ProcessingPurpose string     `json:"processing_purpose"`
	LegalBasis        string     `json:"legal_basis"`
	ConsentGiven      bool       `json:"consent_given"`
	ConsentDate       time.Time  `json:"consent_date"`
	ExpiresAt         *time.Time `json:"expires_at,omitempty"`
	WithdrawnAt       *time.Time `json:"withdrawn_at,omitempty"`
	ConsentMethod     string     `json:"consent_method"` // "explicit", "implied", "opt-in", etc.
}

// TimeRestrictions defines when a role can be used
type TimeRestrictions struct {
	AllowedHours []int    `json:"allowed_hours"`        // Hours of day (0-23)
	AllowedDays  []string `json:"allowed_days"`         // Days of week
	Timezone     string   `json:"timezone"`             // Timezone for restrictions
	Exceptions   []string `json:"exceptions,omitempty"` // Exception dates
}

// AuditLogger interface for RBAC audit events
type AuditLogger interface {
	LogAccessAttempt(event AccessAuditEvent)
	LogPermissionCheck(event PermissionAuditEvent)
	LogPrivilegeEscalation(event PrivilegeEscalationEvent)
	LogSessionEvent(event SessionAuditEvent)
}

// AccessAuditEvent represents an access attempt audit event
type AccessAuditEvent struct {
	ID            string                 `json:"id"`
	Timestamp     time.Time              `json:"timestamp"`
	UserID        string                 `json:"user_id"`
	SessionID     string                 `json:"session_id,omitempty"`
	Resource      string                 `json:"resource"`
	Action        string                 `json:"action"`
	IPAddress     string                 `json:"ip_address"`
	UserAgent     string                 `json:"user_agent,omitempty"`
	Success       bool                   `json:"success"`
	DenialReason  string                 `json:"denial_reason,omitempty"`
	DataCategory  string                 `json:"data_category,omitempty"`
	LegalBasis    string                 `json:"legal_basis,omitempty"`
	Justification string                 `json:"justification,omitempty"`
	RiskLevel     string                 `json:"risk_level"` // "low", "medium", "high", "critical"
	Metadata      map[string]interface{} `json:"metadata,omitempty"`
}

// PermissionAuditEvent represents a permission check audit event
type PermissionAuditEvent struct {
	ID           string                 `json:"id"`
	Timestamp    time.Time              `json:"timestamp"`
	UserID       string                 `json:"user_id"`
	Permission   string                 `json:"permission"`
	Resource     string                 `json:"resource"`
	Granted      bool                   `json:"granted"`
	Reason       string                 `json:"reason"`
	DataCategory string                 `json:"data_category,omitempty"`
	Metadata     map[string]interface{} `json:"metadata,omitempty"`
}

// PrivilegeEscalationEvent represents a privilege escalation audit event
type PrivilegeEscalationEvent struct {
	ID              string                 `json:"id"`
	Timestamp       time.Time              `json:"timestamp"`
	UserID          string                 `json:"user_id"`
	SessionID       string                 `json:"session_id"`
	FromPrivileges  []string               `json:"from_privileges"`
	ToPrivileges    []string               `json:"to_privileges"`
	Justification   string                 `json:"justification"`
	ApprovedBy      string                 `json:"approved_by,omitempty"`
	Duration        time.Duration          `json:"duration"`
	Success         bool                   `json:"success"`
	DetectionMethod string                 `json:"detection_method"` // "automatic", "manual", "anomaly"
	RiskScore       float64                `json:"risk_score"`
	Metadata        map[string]interface{} `json:"metadata,omitempty"`
}

// SessionAuditEvent represents a session lifecycle audit event
type SessionAuditEvent struct {
	ID        string                 `json:"id"`
	Timestamp time.Time              `json:"timestamp"`
	SessionID string                 `json:"session_id"`
	UserID    string                 `json:"user_id"`
	EventType string                 `json:"event_type"` // "created", "expired", "terminated", "extended"
	IPAddress string                 `json:"ip_address"`
	UserAgent string                 `json:"user_agent,omitempty"`
	Reason    string                 `json:"reason,omitempty"`
	Duration  time.Duration          `json:"duration,omitempty"`
	Metadata  map[string]interface{} `json:"metadata,omitempty"`
}

// NewAccessController creates a new RBAC access controller
func NewAccessController(config *RBACConfig, auditLog AuditLogger) *AccessController {
	ac := &AccessController{
		roles:       make(map[string]*Role),
		users:       make(map[string]*User),
		permissions: make(map[string]*Permission),
		sessions:    make(map[string]*Session),
		auditLog:    auditLog,
		config:      config,
	}

	// Initialize default permissions and roles
	ac.initializeDefaults()

	// Start session cleanup goroutine
	go ac.sessionCleanup()

	return ac
}

// initializeDefaults sets up default GDPR-compliant permissions and roles
func (ac *AccessController) initializeDefaults() {
	// Default permissions for GDPR operations
	defaultPermissions := []*Permission{
		{
			ID:                    "personal_data_read",
			Name:                  "Read Personal Data",
			Description:           "View personal data under GDPR Article 6",
			Resource:              "personal_data",
			Action:                "read",
			DataClassification:    "confidential",
			GDPRImplications:      []string{"Article 6", "Article 13", "Article 14"},
			RequiresJustification: true,
			IsHighRisk:            true,
		},
		{
			ID:                    "personal_data_write",
			Name:                  "Modify Personal Data",
			Description:           "Create or modify personal data under GDPR Article 16",
			Resource:              "personal_data",
			Action:                "write",
			DataClassification:    "confidential",
			GDPRImplications:      []string{"Article 6", "Article 16", "Article 25"},
			RequiresJustification: true,
			IsHighRisk:            true,
		},
		{
			ID:                    "personal_data_delete",
			Name:                  "Delete Personal Data",
			Description:           "Delete personal data under GDPR Article 17",
			Resource:              "personal_data",
			Action:                "delete",
			DataClassification:    "confidential",
			GDPRImplications:      []string{"Article 17", "Article 19"},
			RequiresJustification: true,
			IsHighRisk:            true,
		},
		{
			ID:                    "data_export",
			Name:                  "Export Data",
			Description:           "Export data for portability under GDPR Article 20",
			Resource:              "data_export",
			Action:                "execute",
			DataClassification:    "confidential",
			GDPRImplications:      []string{"Article 20"},
			RequiresJustification: true,
			IsHighRisk:            true,
		},
		{
			ID:                    "audit_log_read",
			Name:                  "Read Audit Logs",
			Description:           "View audit logs for compliance monitoring",
			Resource:              "audit_logs",
			Action:                "read",
			DataClassification:    "restricted",
			GDPRImplications:      []string{"Article 30"},
			RequiresJustification: false,
			IsHighRisk:            false,
		},
		{
			ID:                    "pseudonymization_manage",
			Name:                  "Manage Pseudonymization",
			Description:           "Manage pseudonymization keys and processes",
			Resource:              "pseudonymization",
			Action:                "manage",
			DataClassification:    "restricted",
			GDPRImplications:      []string{"Article 25", "Article 32"},
			RequiresJustification: true,
			IsHighRisk:            true,
		},
	}

	for _, perm := range defaultPermissions {
		perm.CreatedAt = time.Now()
		ac.permissions[perm.ID] = perm
	}

	// Default roles
	defaultRoles := []*Role{
		{
			ID:                 "data_protection_officer",
			Name:               "Data Protection Officer",
			Description:        "GDPR DPO with full compliance oversight",
			Permissions:        []string{"personal_data_read", "personal_data_write", "personal_data_delete", "data_export", "audit_log_read", "pseudonymization_manage"},
			DataCategories:     []string{"personal", "sensitive", "transaction", "log"},
			ProcessingPurposes: []string{"compliance", "audit", "legal_obligation"},
			LegalBases:         []string{"Article 6(1)(c)", "Article 6(1)(f)"},
			IsBuiltIn:          true,
			RequiresApproval:   false,
			MaxSessionDuration: 8 * time.Hour,
		},
		{
			ID:                 "data_processor",
			Name:               "Data Processor",
			Description:        "Process personal data for specific purposes",
			Permissions:        []string{"personal_data_read", "personal_data_write"},
			DataCategories:     []string{"personal"},
			ProcessingPurposes: []string{"contract_performance", "legitimate_interests"},
			LegalBases:         []string{"Article 6(1)(b)", "Article 6(1)(f)"},
			IsBuiltIn:          true,
			RequiresApproval:   true,
			MaxSessionDuration: 4 * time.Hour,
		},
		{
			ID:                 "data_subject_coordinator",
			Name:               "Data Subject Coordinator",
			Description:        "Handle data subject requests and rights",
			Permissions:        []string{"personal_data_read", "personal_data_delete", "data_export"},
			DataCategories:     []string{"personal", "sensitive"},
			ProcessingPurposes: []string{"data_subject_rights", "legal_obligation"},
			LegalBases:         []string{"Article 6(1)(c)"},
			IsBuiltIn:          true,
			RequiresApproval:   true,
			MaxSessionDuration: 6 * time.Hour,
		},
		{
			ID:                 "auditor",
			Name:               "Compliance Auditor",
			Description:        "Audit compliance and access logs",
			Permissions:        []string{"audit_log_read"},
			DataCategories:     []string{"log"},
			ProcessingPurposes: []string{"audit", "compliance_monitoring"},
			LegalBases:         []string{"Article 6(1)(f)"},
			IsBuiltIn:          true,
			RequiresApproval:   false,
			MaxSessionDuration: 12 * time.Hour,
		},
	}

	for _, role := range defaultRoles {
		role.CreatedAt = time.Now()
		role.UpdatedAt = time.Now()
		ac.roles[role.ID] = role
	}
}

// sessionCleanup removes expired sessions
func (ac *AccessController) sessionCleanup() {
	ticker := time.NewTicker(5 * time.Minute)
	defer ticker.Stop()

	for range ticker.C {
		ac.mutex.Lock()
		now := time.Now()

		for id, session := range ac.sessions {
			if now.After(session.ExpiresAt) {
				delete(ac.sessions, id)

				// Log session expiration
				if ac.auditLog != nil {
					event := SessionAuditEvent{
						ID:        generateAuditID(),
						Timestamp: now,
						SessionID: id,
						UserID:    session.UserID,
						EventType: "expired",
						Duration:  now.Sub(session.CreatedAt),
						Reason:    "session_timeout",
					}
					ac.auditLog.LogSessionEvent(event)
				}
			}
		}
		ac.mutex.Unlock()
	}
}

// generateAuditID generates a unique audit event ID
func generateAuditID() string {
	return fmt.Sprintf("audit_%d", time.Now().UnixNano())
}

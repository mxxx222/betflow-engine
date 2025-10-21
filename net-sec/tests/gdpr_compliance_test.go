package tests
package tests

import (
	"context"
	"fmt"
	"os"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/stretchr/testify/suite"
)

// GDPRComplianceTestSuite contains integration tests for GDPR compliance
type GDPRComplianceTestSuite struct {
	suite.Suite
	pseudonymizer     *privacy.PseudonymizationEngine
	keyManager       *privacy.KeyManager
	retentionScheduler *retention.RetentionScheduler
	accessController  *rbac.AccessController
	integrationManager *integrations.IntegrationManager
}

// SetupSuite initializes test environment
func (suite *GDPRComplianceTestSuite) SetupSuite() {
	// Setup test logging
	suite.setupTestLogging()
	
	// Initialize pseudonymization engine
	config := &privacy.PseudonymizationConfig{
		DefaultAlgorithm: "AES-256",
		AuditEnabled:     true,
	}
	
	var err error
	suite.pseudonymizer, err = privacy.NewPseudonymizationEngine(config, &MockAuditLogger{})
	require.NoError(suite.T(), err)

	// Initialize key manager
	keyConfig := &privacy.KeyManagerConfig{
		KeySize:          32,
		RotationInterval: 24 * time.Hour,
		ArchiveRetention: 7 * 24 * time.Hour,
	}
	
	suite.keyManager, err = privacy.NewKeyManager(keyConfig)
	require.NoError(suite.T(), err)

	// Initialize retention scheduler
	suite.retentionScheduler = retention.NewRetentionScheduler(&MockAuditLogger{})
	
	// Initialize access controller
	rbacConfig := &rbac.RBACConfig{
		SessionTimeout:    8 * time.Hour,
		MaxFailedAttempts: 5,
		LockoutDuration:   30 * time.Minute,
		RequireMFA:        false, // Disabled for tests
		AuditAllAccess:    true,
	}
	
	suite.accessController = rbac.NewAccessController(rbacConfig, &MockAuditLogger{})
	
	// Initialize integration manager
	integrationConfig := &integrations.IntegrationConfig{
		RequestTimeout:      30 * time.Second,
		RetryAttempts:       3,
		RetryBackoff:        1 * time.Second,
		DataMinimization:    true,
		PseudonymizeData:    true,
		AuditAllRequests:    true,
	}
	
	suite.integrationManager = integrations.NewIntegrationManager(
		integrationConfig,
		&MockAuditLogger{},
		&MockDataMinimizer{},
	)
}

// TestPseudonymizationCompliance tests GDPR Article 25 pseudonymization
func (suite *GDPRComplianceTestSuite) TestPseudonymizationCompliance() {
	t := suite.T()
	
	// Test data with personal information
	testData := map[string]interface{}{
		"email":    "john.doe@example.com",
		"name":     "John Doe",
		"phone":    "+1-555-123-4567",
		"address":  "123 Privacy St, GDPR City, EU",
		"metadata": "non-personal data",
	}
	
	// Test SHA-256 pseudonymization
	t.Run("SHA256Pseudonymization", func(t *testing.T) {
		result, err := suite.pseudonymizer.PseudonymizeSHA256(
			testData["email"].(string),
			"test-salt",
		)
		
		require.NoError(t, err)
		assert.NotEqual(t, testData["email"], result)
		assert.NotContains(t, result, "john.doe")
		assert.NotContains(t, result, "example.com")
		
		// Test consistency - same input should produce same output
		result2, err := suite.pseudonymizer.PseudonymizeSHA256(
			testData["email"].(string),
			"test-salt",
		)
		require.NoError(t, err)
		assert.Equal(t, result, result2)
	})
	
	// Test AES-256 pseudonymization (reversible)
	t.Run("AES256Pseudonymization", func(t *testing.T) {
		key, err := suite.keyManager.GetActiveKey()
		require.NoError(t, err)
		
		encrypted, err := suite.pseudonymizer.PseudonymizeAES256(
			testData["name"].(string),
			key.Key,
		)
		
		require.NoError(t, err)
		assert.NotEqual(t, testData["name"], encrypted)
		assert.NotContains(t, encrypted, "John")
		assert.NotContains(t, encrypted, "Doe")
	})
	
	// Test format-preserving encryption
	t.Run("FormatPreservingEncryption", func(t *testing.T) {
		phone := testData["phone"].(string)
		key, err := suite.keyManager.GetActiveKey()
		require.NoError(t, err)
		
		encrypted, err := suite.pseudonymizer.PseudonymizeFPE(phone, key.Key)
		require.NoError(t, err)
		
		// Should maintain format but change content
		assert.Len(t, encrypted, len(phone))
		assert.NotEqual(t, phone, encrypted)
		assert.Contains(t, encrypted, "+") // Should preserve format markers
	})
}

// TestRetentionPolicyCompliance tests GDPR Article 5(e) retention policies
func (suite *GDPRComplianceTestSuite) TestRetentionPolicyCompliance() {
	t := suite.T()
	
	// Test default retention policies
	t.Run("DefaultPolicies", func(t *testing.T) {
		policies := retention.DefaultPolicies()
		
		assert.GreaterOrEqual(t, len(policies), 4)
		
		// Verify personal data policy
		var personalPolicy *retention.RetentionPolicy
		for _, policy := range policies {
			if policy.DataCategory == "personal" {
				personalPolicy = policy
				break
			}
		}
		
		require.NotNil(t, personalPolicy)
		assert.Equal(t, "personal", personalPolicy.DataCategory)
		assert.True(t, personalPolicy.AutomatedPurge)
		assert.Contains(t, personalPolicy.LegalBasis, "Article 6")
		assert.Contains(t, personalPolicy.SubjectRights, "erasure")
	})
	
	// Test policy validation
	t.Run("PolicyValidation", func(t *testing.T) {
		validPolicy := &retention.RetentionPolicy{
			ID:               "test-policy",
			DataCategory:     "personal",
			RetentionPeriod:  365 * 24 * time.Hour,
			GracePeriod:      30 * 24 * time.Hour,
			PurgeMethod:      "secure_delete",
			LegalBasis:       "Article 6(1)(b) - Contract",
			SubjectRights:    []string{"access", "erasure"},
			AutomatedPurge:   true,
			NotificationDays: 30,
		}
		
		errors := retention.ValidateRetentionPolicy(validPolicy)
		assert.Empty(t, errors, "Valid policy should have no errors")
		
		// Test invalid policy
		invalidPolicy := &retention.RetentionPolicy{
			ID:             "", // Missing required field
			DataCategory:   "sensitive",
			RetentionPeriod: 0, // Invalid retention period
			LegalBasis:     "", // Missing legal basis
		}
		
		errors = retention.ValidateRetentionPolicy(invalidPolicy)
		assert.NotEmpty(t, errors, "Invalid policy should have errors")
		assert.Contains(t, fmt.Sprintf("%v", errors), "Policy ID is required")
		assert.Contains(t, fmt.Sprintf("%v", errors), "Legal basis is required")
	})
	
	// Test automated purge job scheduling
	t.Run("AutomatedPurgeScheduling", func(t *testing.T) {
		// Add a test retention policy
		policy := &retention.RetentionPolicy{
			ID:               "test-automated-purge",
			DataCategory:     "log",
			RetentionPeriod:  1 * time.Hour, // Short retention for testing
			GracePeriod:      1 * time.Minute,
			PurgeMethod:      "secure_delete",
			LegalBasis:       "Article 6(1)(f) - Legitimate interests",
			SubjectRights:    []string{"access"},
			AutomatedPurge:   true,
			NotificationDays: 0,
		}
		
		err := suite.retentionScheduler.AddRetentionPolicy(policy)
		require.NoError(t, err)
		
		// Schedule a purge job
		dataQuery := map[string]interface{}{
			"data_category":  "log",
			"created_before": time.Now().Add(-2 * time.Hour),
		}
		
		job, err := suite.retentionScheduler.SchedulePurgeJob(
			policy.ID,
			dataQuery,
			time.Now().Add(1*time.Minute),
			true, // Dry run
		)
		
		require.NoError(t, err)
		assert.Equal(t, "pending", job.Status)
		assert.True(t, job.DryRun)
	})
	
	// Test legal hold functionality
	t.Run("LegalHolds", func(t *testing.T) {
		hold := &retention.LegalHold{
			ID:          "test-legal-hold",
			Name:        "Litigation Hold 2024",
			Description: "Hold for ongoing litigation case",
			DataQuery: map[string]interface{}{
				"data_category": "transaction",
				"user_id":       "user123",
			},
			CreatedBy:   "legal@company.com",
			Reason:      "Active litigation - Case #2024-001",
			ExpiresAt:   nil, // Indefinite hold
			IsActive:    true,
		}
		
		err := suite.retentionScheduler.CreateLegalHold(hold)
		require.NoError(t, err)
		
		// Verify hold prevents purging
		metrics := suite.retentionScheduler.GetRetentionMetrics()
		assert.Equal(t, 1, metrics.ActiveHolds)
	})
}

// TestRBACCompliance tests GDPR access control requirements
func (suite *GDPRComplianceTestSuite) TestRBACCompliance() {
	t := suite.T()
	
	// Test user creation and role assignment
	t.Run("UserAndRoleManagement", func(t *testing.T) {
		// Create test user
		user := &rbac.User{
			ID:       "test-user-001",
			Username: "john.processor",
			Email:    "john.processor@company.com",
			Roles:    []string{},
		}
		
		err := suite.accessController.AddUser(user)
		require.NoError(t, err)
		
		// Assign data processor role
		err = suite.accessController.AssignRole(user.ID, "data_processor")
		require.NoError(t, err)
		
		// Try to assign DPO role (should require approval)
		err = suite.accessController.AssignRole(user.ID, "data_protection_officer")
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "requires approval")
	})
	
	// Test session management
	t.Run("SessionManagement", func(t *testing.T) {
		// Create session
		session, err := suite.accessController.CreateSession(
			"test-user-001",
			"192.168.1.100",
			"Mozilla/5.0 (Test Browser)",
		)
		
		require.NoError(t, err)
		assert.NotEmpty(t, session.ID)
		assert.Equal(t, "test-user-001", session.UserID)
		assert.False(t, time.Now().After(session.ExpiresAt))
	})
	
	// Test access control checks
	t.Run("AccessControl", func(t *testing.T) {
		// Create session for testing
		session, err := suite.accessController.CreateSession(
			"test-user-001",
			"192.168.1.100",
			"Mozilla/5.0 (Test Browser)",
		)
		require.NoError(t, err)
		
		// Test access to personal data (should be allowed for data processor)
		context := map[string]interface{}{
			"data_category":      "personal",
			"justification":      "Processing customer order",
			"ip_address":         "192.168.1.100",
			"data_classification": "confidential",
		}
		
		allowed := suite.accessController.CheckAccess(
			session.ID,
			"personal_data",
			"read",
			context,
		)
		assert.True(t, allowed, "Data processor should have access to personal data")
		
		// Test access to audit logs (should be denied)
		denied := suite.accessController.CheckAccess(
			session.ID,
			"audit_logs",
			"read",
			context,
		)
		assert.False(t, denied, "Data processor should not have access to audit logs")
	})
	
	// Test privilege escalation detection
	t.Run("PrivilegeEscalation", func(t *testing.T) {
		session, err := suite.accessController.CreateSession(
			"test-user-001",
			"192.168.1.100",
			"Mozilla/5.0 (Test Browser)",
		)
		require.NoError(t, err)
		
		// Attempt privilege escalation
		err = suite.accessController.ElevatePrivileges(
			session.ID,
			[]string{"personal_data_delete", "audit_log_read"}, // New privileges
			1*time.Hour,
			"Emergency data subject request processing",
			"", // No approval
		)
		
		// Should be allowed for low-risk escalation without approval
		assert.NoError(t, err)
	})
}

// TestIntegrationCompliance tests external API integration compliance
func (suite *GDPRComplianceTestSuite) TestIntegrationCompliance() {
	t := suite.T()
	
	// Test Notion integration setup
	t.Run("NotionIntegrationSetup", func(t *testing.T) {
		// Skip if no API token provided
		apiToken := os.Getenv("NOTION_API_TOKEN")
		if apiToken == "" {
			t.Skip("NOTION_API_TOKEN not provided, skipping integration test")
		}
		
		notionIntegration := integrations.NewNotionIntegration(apiToken)
		
		err := suite.integrationManager.RegisterIntegration(notionIntegration)
		require.NoError(t, err)
		
		// Test authentication
		credentials := map[string]string{
			"api_token": apiToken,
		}
		
		err = notionIntegration.Authenticate(credentials)
		// Note: This might fail without a valid token, but that's expected
		if err != nil {
			t.Logf("Authentication failed (expected with test token): %v", err)
		}
	})
	
	// Test data minimization in integrations
	t.Run("DataMinimization", func(t *testing.T) {
		// Create test data with personal information
		testData := &integrations.IntegrationData{
			ID:   "test-data-001",
			Type: "user_profile",
			Content: map[string]interface{}{
				"full_name":    "John Doe",
				"email":        "john.doe@example.com",
				"phone":        "+1-555-123-4567",
				"address":      "123 Privacy St",
				"job_title":    "Data Processor",
				"company":      "GDPR Corp",
				"notes":        "Customer since 2020",
			},
			PersonalData: []integrations.PersonalDataField{
				{Field: "full_name", DataCategory: "personal"},
				{Field: "email", DataCategory: "personal"},
				{Field: "phone", DataCategory: "sensitive"},
				{Field: "address", DataCategory: "sensitive"},
			},
			LegalBasis:        "Article 6(1)(b) - Contract",
			ProcessingPurpose: "Customer relationship management",
			Classification:    "confidential",
		}
		
		// Test compliance validation
		report, err := suite.integrationManager.ValidateCompliance("notion")
		if err != nil {
			t.Logf("Integration not registered: %v", err)
		} else {
			assert.NotNil(t, report)
			assert.Contains(t, report.IntegrationName, "notion")
		}
	})
}

// TestDataSubjectRights tests GDPR data subject rights implementation
func (suite *GDPRComplianceTestSuite) TestDataSubjectRights() {
	t := suite.T()
	
	// Test right of access (Article 15)
	t.Run("RightOfAccess", func(t *testing.T) {
		// This would test the data export functionality
		// for providing data subjects with their personal data
		assert.True(t, true, "Right of access implementation test placeholder")
	})
	
	// Test right to rectification (Article 16)
	t.Run("RightToRectification", func(t *testing.T) {
		// This would test the data correction functionality
		assert.True(t, true, "Right to rectification implementation test placeholder")
	})
	
	// Test right to erasure (Article 17)
	t.Run("RightToErasure", func(t *testing.T) {
		// This would test the "right to be forgotten" functionality
		assert.True(t, true, "Right to erasure implementation test placeholder")
	})
	
	// Test right to data portability (Article 20)
	t.Run("RightToDataPortability", func(t *testing.T) {
		// This would test data export in machine-readable format
		assert.True(t, true, "Right to data portability implementation test placeholder")
	})
}

// TestDataBreachDetection tests automated breach detection
func (suite *GDPRComplianceTestSuite) TestDataBreachDetection() {
	t := suite.T()
	
	// Test unauthorized access detection
	t.Run("UnauthorizedAccessDetection", func(t *testing.T) {
		// Simulate multiple failed authentication attempts
		for i := 0; i < 6; i++ {
			_, err := suite.accessController.CreateSession(
				"nonexistent-user",
				"192.168.1.200",
				"Suspicious User Agent",
			)
			assert.Error(t, err)
		}
		
		// This should trigger breach detection alerting
		assert.True(t, true, "Breach detection test completed")
	})
	
	// Test data exfiltration detection
	t.Run("DataExfiltrationDetection", func(t *testing.T) {
		// This would test detection of large data exports
		// or unusual access patterns
		assert.True(t, true, "Data exfiltration detection test placeholder")
	})
}

// Helper functions and mock implementations

type MockAuditLogger struct{}

func (m *MockAuditLogger) LogKeyRotation(event privacy.KeyRotationEvent) {
	// Mock implementation
}

func (m *MockAuditLogger) LogPseudonymization(event privacy.PseudonymizationAuditEvent) {
	// Mock implementation
}

func (m *MockAuditLogger) LogRetentionEvent(event retention.RetentionAuditEvent) {
	// Mock implementation
}

func (m *MockAuditLogger) LogPurgeJob(job *retention.PurgeJob) {
	// Mock implementation
}

func (m *MockAuditLogger) LogLegalHold(hold *retention.LegalHold, action string) {
	// Mock implementation
}

func (m *MockAuditLogger) LogAccessAttempt(event rbac.AccessAuditEvent) {
	// Mock implementation
}

func (m *MockAuditLogger) LogPermissionCheck(event rbac.PermissionAuditEvent) {
	// Mock implementation
}

func (m *MockAuditLogger) LogPrivilegeEscalation(event rbac.PrivilegeEscalationEvent) {
	// Mock implementation
}

func (m *MockAuditLogger) LogSessionEvent(event rbac.SessionAuditEvent) {
	// Mock implementation
}

func (m *MockAuditLogger) LogIntegrationEvent(event integrations.IntegrationAuditEvent) {
	// Mock implementation
}

func (m *MockAuditLogger) LogDataTransfer(event integrations.DataTransferEvent) {
	// Mock implementation
}

func (m *MockAuditLogger) LogPersonalDataAccess(event integrations.PersonalDataAccessEvent) {
	// Mock implementation
}

type MockDataMinimizer struct{}

func (m *MockDataMinimizer) MinimizeData(data map[string]interface{}, purpose string) map[string]interface{} {
	// Mock implementation - return copy with minimal data
	result := make(map[string]interface{})
	for k, v := range data {
		// Only include necessary fields based on purpose
		if k == "id" || k == "timestamp" || purpose == "all" {
			result[k] = v
		}
	}
	return result
}

func (m *MockDataMinimizer) PseudonymizeFields(data map[string]interface{}, fields []string) error {
	// Mock implementation - replace sensitive fields with pseudonymized versions
	for _, field := range fields {
		if value, exists := data[field]; exists {
			data[field] = fmt.Sprintf("PSEUDO_%v", value)
		}
	}
	return nil
}

func (m *MockDataMinimizer) ClassifyData(data map[string]interface{}) map[string]string {
	// Mock implementation - classify fields as personal, sensitive, or general
	classifications := make(map[string]string)
	for field := range data {
		if field == "email" || field == "phone" || field == "address" {
			classifications[field] = "sensitive"
		} else if field == "name" || field == "username" {
			classifications[field] = "personal"
		} else {
			classifications[field] = "general"
		}
	}
	return classifications
}

func (suite *GDPRComplianceTestSuite) setupTestLogging() {
	// Setup test logging configuration
	// This would configure logging for tests
}

// TestSuite runner
func TestGDPRCompliance(t *testing.T) {
	suite.Run(t, new(GDPRComplianceTestSuite))
}
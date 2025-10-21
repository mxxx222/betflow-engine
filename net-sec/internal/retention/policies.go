package retention

import (
	"fmt"
	"strings"
	"time"
)

// DefaultPolicies returns a set of standard GDPR-compliant retention policies
func DefaultPolicies() []*RetentionPolicy {
	return []*RetentionPolicy{
		{
			ID:               "personal-data-standard",
			DataCategory:     "personal",
			RetentionPeriod:  2 * 365 * 24 * time.Hour, // 2 years
			GracePeriod:      30 * 24 * time.Hour,      // 30 days
			PurgeMethod:      "secure_delete",
			LegalBasis:       "Article 6(1)(b) - Contract",
			SubjectRights:    []string{"access", "rectification", "erasure", "portability"},
			AutomatedPurge:   true,
			NotificationDays: 30,
		},
		{
			ID:               "sensitive-data-standard",
			DataCategory:     "sensitive",
			RetentionPeriod:  1 * 365 * 24 * time.Hour, // 1 year
			GracePeriod:      14 * 24 * time.Hour,      // 14 days
			PurgeMethod:      "secure_delete",
			LegalBasis:       "Article 9(2)(a) - Explicit consent",
			SubjectRights:    []string{"access", "rectification", "erasure", "restriction", "portability"},
			AutomatedPurge:   true,
			NotificationDays: 60,
		},
		{
			ID:               "transaction-data-standard",
			DataCategory:     "transaction",
			RetentionPeriod:  7 * 365 * 24 * time.Hour, // 7 years (financial records)
			GracePeriod:      90 * 24 * time.Hour,      // 90 days
			PurgeMethod:      "anonymize",
			LegalBasis:       "Article 6(1)(c) - Legal obligation",
			SubjectRights:    []string{"access", "rectification"},
			AutomatedPurge:   true,
			NotificationDays: 90,
		},
		{
			ID:               "log-data-standard",
			DataCategory:     "log",
			RetentionPeriod:  90 * 24 * time.Hour, // 90 days
			GracePeriod:      7 * 24 * time.Hour,  // 7 days
			PurgeMethod:      "secure_delete",
			LegalBasis:       "Article 6(1)(f) - Legitimate interests",
			SubjectRights:    []string{"access", "erasure"},
			AutomatedPurge:   true,
			NotificationDays: 14,
		},
		{
			ID:               "marketing-data-standard",
			DataCategory:     "marketing",
			RetentionPeriod:  3 * 365 * 24 * time.Hour, // 3 years
			GracePeriod:      30 * 24 * time.Hour,      // 30 days
			PurgeMethod:      "pseudonymize",
			LegalBasis:       "Article 6(1)(a) - Consent",
			SubjectRights:    []string{"access", "rectification", "erasure", "restriction", "portability", "object"},
			AutomatedPurge:   false, // Manual review required
			NotificationDays: 45,
		},
	}
}

// PolicyTemplate provides templates for creating custom retention policies
type PolicyTemplate struct {
	Name         string
	Description  string
	BasePolicy   *RetentionPolicy
	Customizable []string // Fields that can be customized
}

// GetPolicyTemplates returns available policy templates
func GetPolicyTemplates() []*PolicyTemplate {
	return []*PolicyTemplate{
		{
			Name:        "GDPR Article 6(1)(b) - Contract Performance",
			Description: "For data necessary to perform a contract with the data subject",
			BasePolicy: &RetentionPolicy{
				LegalBasis:       "Article 6(1)(b) - Contract",
				SubjectRights:    []string{"access", "rectification", "erasure", "portability"},
				RetentionPeriod:  2 * 365 * 24 * time.Hour,
				PurgeMethod:      "secure_delete",
				AutomatedPurge:   true,
				NotificationDays: 30,
			},
			Customizable: []string{"RetentionPeriod", "DataCategory", "NotificationDays"},
		},
		{
			Name:        "GDPR Article 6(1)(c) - Legal Obligation",
			Description: "For data retained due to legal obligations (e.g., tax records)",
			BasePolicy: &RetentionPolicy{
				LegalBasis:       "Article 6(1)(c) - Legal obligation",
				SubjectRights:    []string{"access", "rectification"},
				RetentionPeriod:  7 * 365 * 24 * time.Hour,
				PurgeMethod:      "anonymize",
				AutomatedPurge:   true,
				NotificationDays: 90,
			},
			Customizable: []string{"RetentionPeriod", "DataCategory", "PurgeMethod"},
		},
		{
			Name:        "GDPR Article 6(1)(f) - Legitimate Interests",
			Description: "For data processed for legitimate interests (with balancing test)",
			BasePolicy: &RetentionPolicy{
				LegalBasis:       "Article 6(1)(f) - Legitimate interests",
				SubjectRights:    []string{"access", "rectification", "erasure", "restriction", "object"},
				RetentionPeriod:  1 * 365 * 24 * time.Hour,
				PurgeMethod:      "secure_delete",
				AutomatedPurge:   false,
				NotificationDays: 45,
			},
			Customizable: []string{"RetentionPeriod", "DataCategory", "AutomatedPurge"},
		},
	}
}

// ValidateRetentionPolicy validates a retention policy against GDPR requirements
func ValidateRetentionPolicy(policy *RetentionPolicy) []string {
	var errors []string

	// Required fields validation
	if policy.ID == "" {
		errors = append(errors, "Policy ID is required")
	}

	if policy.DataCategory == "" {
		errors = append(errors, "Data category is required")
	}

	if policy.RetentionPeriod == 0 {
		errors = append(errors, "Retention period must be greater than 0")
	}

	if policy.LegalBasis == "" {
		errors = append(errors, "Legal basis is required under GDPR Article 6")
	}

	if len(policy.SubjectRights) == 0 {
		errors = append(errors, "At least one data subject right must be specified")
	}

	// GDPR-specific validations
	if policy.DataCategory == "sensitive" {
		if !strings.Contains(policy.LegalBasis, "Article 9") {
			errors = append(errors, "Sensitive data requires Article 9 legal basis")
		}

		// Sensitive data should have stricter retention
		maxSensitiveRetention := 2 * 365 * 24 * time.Hour
		if policy.RetentionPeriod > maxSensitiveRetention {
			errors = append(errors, "Sensitive data retention period should not exceed 2 years without special justification")
		}
	}

	// Marketing data validation
	if policy.DataCategory == "marketing" {
		if policy.LegalBasis != "Article 6(1)(a) - Consent" {
			errors = append(errors, "Marketing data typically requires explicit consent")
		}

		requiredRights := []string{"access", "rectification", "erasure", "restriction", "portability", "object"}
		for _, right := range requiredRights {
			if !containsString(policy.SubjectRights, right) {
				errors = append(errors, fmt.Sprintf("Marketing data must support '%s' right", right))
			}
		}
	}

	// Purge method validation
	validPurgeMethods := []string{"secure_delete", "anonymize", "pseudonymize"}
	if !containsString(validPurgeMethods, policy.PurgeMethod) {
		errors = append(errors, "Purge method must be one of: secure_delete, anonymize, pseudonymize")
	}

	// Notification period validation
	if policy.NotificationDays < 0 {
		errors = append(errors, "Notification days cannot be negative")
	}

	if policy.NotificationDays > 90 {
		errors = append(errors, "Notification period should not exceed 90 days")
	}

	return errors
}

// containsString checks if a slice contains a specific string
func containsString(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}

// CalculateRetentionDate calculates when data should be purged
func CalculateRetentionDate(createdAt time.Time, policy *RetentionPolicy) time.Time {
	return createdAt.Add(policy.RetentionPeriod)
}

// CalculateGraceDate calculates the final deletion date including grace period
func CalculateGraceDate(retentionDate time.Time, policy *RetentionPolicy) time.Time {
	return retentionDate.Add(policy.GracePeriod)
}

// IsDataExpired checks if data has exceeded its retention period
func IsDataExpired(createdAt time.Time, policy *RetentionPolicy) bool {
	expirationDate := CalculateRetentionDate(createdAt, policy)
	return time.Now().After(expirationDate)
}

// IsInGracePeriod checks if data is in the grace period before final deletion
func IsInGracePeriod(createdAt time.Time, policy *RetentionPolicy) bool {
	retentionDate := CalculateRetentionDate(createdAt, policy)
	graceDate := CalculateGraceDate(retentionDate, policy)
	now := time.Now()

	return now.After(retentionDate) && now.Before(graceDate)
}

// GetNotificationDate calculates when to notify about upcoming data expiration
func GetNotificationDate(createdAt time.Time, policy *RetentionPolicy) time.Time {
	retentionDate := CalculateRetentionDate(createdAt, policy)
	notificationPeriod := time.Duration(policy.NotificationDays) * 24 * time.Hour
	return retentionDate.Add(-notificationPeriod)
}

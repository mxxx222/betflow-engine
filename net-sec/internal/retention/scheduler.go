package retention

import (
	"context"
	"fmt"
	"log"
	"sync"
	"time"
)

// RetentionScheduler manages automated data retention and purge operations
type RetentionScheduler struct {
	policies   map[string]*RetentionPolicy
	jobs       map[string]*PurgeJob
	legalHolds map[string]*LegalHold
	mutex      sync.RWMutex
	ctx        context.Context
	cancel     context.CancelFunc
	auditLog   AuditLogger
}

// RetentionPolicy defines data retention rules per GDPR Article 5(e)
type RetentionPolicy struct {
	ID               string        `json:"id"`
	DataCategory     string        `json:"data_category"`     // "personal", "sensitive", "transaction", "log"
	RetentionPeriod  time.Duration `json:"retention_period"`  // How long to keep data
	GracePeriod      time.Duration `json:"grace_period"`      // Additional time before hard delete
	PurgeMethod      string        `json:"purge_method"`      // "secure_delete", "anonymize", "pseudonymize"
	LegalBasis       string        `json:"legal_basis"`       // GDPR Article 6 legal basis
	SubjectRights    []string      `json:"subject_rights"`    // Rights that apply to this data
	AutomatedPurge   bool          `json:"automated_purge"`   // Enable automatic purging
	NotificationDays int           `json:"notification_days"` // Days before expiry to notify
	CreatedAt        time.Time     `json:"created_at"`
	UpdatedAt        time.Time     `json:"updated_at"`
}

// PurgeJob represents a scheduled or manual data purge operation
type PurgeJob struct {
	ID            string                 `json:"id"`
	PolicyID      string                 `json:"policy_id"`
	DataQuery     map[string]interface{} `json:"data_query"`     // Query to identify data for purging
	ScheduledAt   time.Time              `json:"scheduled_at"`   // When the job should run
	Status        string                 `json:"status"`         // "pending", "running", "completed", "failed", "cancelled"
	RecordsFound  int                    `json:"records_found"`  // Number of records identified for purging
	RecordsPurged int                    `json:"records_purged"` // Number of records actually purged
	ErrorMessage  string                 `json:"error_message,omitempty"`
	DryRun        bool                   `json:"dry_run"` // Preview mode without actual deletion
	CreatedAt     time.Time              `json:"created_at"`
	CompletedAt   *time.Time             `json:"completed_at,omitempty"`
	Metadata      map[string]interface{} `json:"metadata,omitempty"` // Additional job metadata
}

// LegalHold prevents data from being purged due to legal requirements
type LegalHold struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	DataQuery   map[string]interface{} `json:"data_query"` // Query to identify protected data
	CreatedBy   string                 `json:"created_by"` // User who created the hold
	Reason      string                 `json:"reason"`     // Legal reason for the hold
	ExpiresAt   *time.Time             `json:"expires_at"` // Optional expiration
	IsActive    bool                   `json:"is_active"`
	CreatedAt   time.Time              `json:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at"`
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
}

// AuditLogger interface for retention audit events
type AuditLogger interface {
	LogRetentionEvent(event RetentionAuditEvent)
	LogPurgeJob(job *PurgeJob)
	LogLegalHold(hold *LegalHold, action string)
}

// RetentionAuditEvent represents an audit event for retention operations
type RetentionAuditEvent struct {
	ID        string                 `json:"id"`
	Timestamp time.Time              `json:"timestamp"`
	EventType string                 `json:"event_type"` // "policy_created", "job_scheduled", "purge_completed", etc.
	PolicyID  string                 `json:"policy_id,omitempty"`
	JobID     string                 `json:"job_id,omitempty"`
	HoldID    string                 `json:"hold_id,omitempty"`
	UserID    string                 `json:"user_id,omitempty"`
	Details   map[string]interface{} `json:"details"`
	Success   bool                   `json:"success"`
	Error     string                 `json:"error,omitempty"`
}

// NewRetentionScheduler creates a new retention scheduler instance
func NewRetentionScheduler(auditLog AuditLogger) *RetentionScheduler {
	ctx, cancel := context.WithCancel(context.Background())

	rs := &RetentionScheduler{
		policies:   make(map[string]*RetentionPolicy),
		jobs:       make(map[string]*PurgeJob),
		legalHolds: make(map[string]*LegalHold),
		ctx:        ctx,
		cancel:     cancel,
		auditLog:   auditLog,
	}

	// Start the scheduler
	go rs.scheduler()

	return rs
}

// AddRetentionPolicy adds a new retention policy
func (rs *RetentionScheduler) AddRetentionPolicy(policy *RetentionPolicy) error {
	rs.mutex.Lock()
	defer rs.mutex.Unlock()

	policy.CreatedAt = time.Now()
	policy.UpdatedAt = time.Now()

	rs.policies[policy.ID] = policy

	// Log audit event
	if rs.auditLog != nil {
		event := RetentionAuditEvent{
			ID:        generateEventID(),
			Timestamp: time.Now(),
			EventType: "policy_created",
			PolicyID:  policy.ID,
			Details: map[string]interface{}{
				"data_category":    policy.DataCategory,
				"retention_period": policy.RetentionPeriod.String(),
				"legal_basis":      policy.LegalBasis,
			},
			Success: true,
		}
		rs.auditLog.LogRetentionEvent(event)
	}

	return nil
}

// SchedulePurgeJob schedules a data purge job based on retention policies
func (rs *RetentionScheduler) SchedulePurgeJob(policyID string, dataQuery map[string]interface{}, scheduledAt time.Time, dryRun bool) (*PurgeJob, error) {
	rs.mutex.Lock()
	defer rs.mutex.Unlock()

	policy, exists := rs.policies[policyID]
	if !exists {
		return nil, fmt.Errorf("retention policy %s not found", policyID)
	}

	job := &PurgeJob{
		ID:          generateJobID(),
		PolicyID:    policyID,
		DataQuery:   dataQuery,
		ScheduledAt: scheduledAt,
		Status:      "pending",
		DryRun:      dryRun,
		CreatedAt:   time.Now(),
		Metadata:    make(map[string]interface{}),
	}

	rs.jobs[job.ID] = job

	// Log audit event
	if rs.auditLog != nil {
		event := RetentionAuditEvent{
			ID:        generateEventID(),
			Timestamp: time.Now(),
			EventType: "job_scheduled",
			PolicyID:  policyID,
			JobID:     job.ID,
			Details: map[string]interface{}{
				"scheduled_at":  scheduledAt,
				"dry_run":       dryRun,
				"data_category": policy.DataCategory,
			},
			Success: true,
		}
		rs.auditLog.LogRetentionEvent(event)
	}

	return job, nil
}

// CreateLegalHold creates a legal hold to prevent data purging
func (rs *RetentionScheduler) CreateLegalHold(hold *LegalHold) error {
	rs.mutex.Lock()
	defer rs.mutex.Unlock()

	hold.CreatedAt = time.Now()
	hold.UpdatedAt = time.Now()
	hold.IsActive = true

	rs.legalHolds[hold.ID] = hold

	// Log audit event
	if rs.auditLog != nil {
		rs.auditLog.LogLegalHold(hold, "created")
	}

	return nil
}

// scheduler runs the main scheduling loop
func (rs *RetentionScheduler) scheduler() {
	ticker := time.NewTicker(1 * time.Hour) // Check every hour
	defer ticker.Stop()

	for {
		select {
		case <-rs.ctx.Done():
			return
		case <-ticker.C:
			rs.processScheduledJobs()
			rs.scheduleAutomaticPurges()
		}
	}
}

// processScheduledJobs processes jobs that are ready to run
func (rs *RetentionScheduler) processScheduledJobs() {
	rs.mutex.RLock()
	jobsToRun := make([]*PurgeJob, 0)

	for _, job := range rs.jobs {
		if job.Status == "pending" && time.Now().After(job.ScheduledAt) {
			jobsToRun = append(jobsToRun, job)
		}
	}
	rs.mutex.RUnlock()

	// Process jobs outside of lock to avoid blocking
	for _, job := range jobsToRun {
		go rs.executePurgeJob(job)
	}
}

// scheduleAutomaticPurges creates purge jobs for expired data
func (rs *RetentionScheduler) scheduleAutomaticPurges() {
	rs.mutex.RLock()
	policies := make([]*RetentionPolicy, 0)
	for _, policy := range rs.policies {
		if policy.AutomatedPurge {
			policies = append(policies, policy)
		}
	}
	rs.mutex.RUnlock()

	for _, policy := range policies {
		// This would query the database for expired data based on policy
		// For now, we'll simulate by creating a job for demonstration
		cutoffDate := time.Now().Add(-policy.RetentionPeriod)

		dataQuery := map[string]interface{}{
			"data_category":  policy.DataCategory,
			"created_before": cutoffDate,
		}

		scheduledAt := time.Now().Add(5 * time.Minute) // Schedule for soon

		rs.SchedulePurgeJob(policy.ID, dataQuery, scheduledAt, false)
	}
}

// executePurgeJob executes a single purge job
func (rs *RetentionScheduler) executePurgeJob(job *PurgeJob) {
	rs.mutex.Lock()
	job.Status = "running"
	rs.mutex.Unlock()

	defer func() {
		if r := recover(); r != nil {
			rs.mutex.Lock()
			job.Status = "failed"
			job.ErrorMessage = fmt.Sprintf("panic during execution: %v", r)
			completedAt := time.Now()
			job.CompletedAt = &completedAt
			rs.mutex.Unlock()

			if rs.auditLog != nil {
				rs.auditLog.LogPurgeJob(job)
			}
		}
	}()

	// Check for legal holds that might prevent purging
	if rs.hasLegalHoldConflict(job.DataQuery) {
		rs.mutex.Lock()
		job.Status = "cancelled"
		job.ErrorMessage = "operation cancelled due to legal hold"
		completedAt := time.Now()
		job.CompletedAt = &completedAt
		rs.mutex.Unlock()

		if rs.auditLog != nil {
			rs.auditLog.LogPurgeJob(job)
		}
		return
	}

	// Simulate data identification and purging
	// In a real implementation, this would:
	// 1. Query the database with job.DataQuery
	// 2. Apply the purge method from the policy
	// 3. Update record counts
	// 4. Handle errors appropriately

	rs.mutex.Lock()
	job.RecordsFound = 1250 // Simulated

	if job.DryRun {
		job.RecordsPurged = 0
		job.Status = "completed"
		job.Metadata["dry_run_result"] = "would purge 1250 records"
	} else {
		// Simulate actual purging
		job.RecordsPurged = job.RecordsFound
		job.Status = "completed"
	}

	completedAt := time.Now()
	job.CompletedAt = &completedAt
	rs.mutex.Unlock()

	// Log completion
	if rs.auditLog != nil {
		event := RetentionAuditEvent{
			ID:        generateEventID(),
			Timestamp: time.Now(),
			EventType: "purge_completed",
			PolicyID:  job.PolicyID,
			JobID:     job.ID,
			Details: map[string]interface{}{
				"records_found":  job.RecordsFound,
				"records_purged": job.RecordsPurged,
				"dry_run":        job.DryRun,
			},
			Success: job.Status == "completed",
			Error:   job.ErrorMessage,
		}
		rs.auditLog.LogRetentionEvent(event)
		rs.auditLog.LogPurgeJob(job)
	}

	log.Printf("Purge job %s completed: %d/%d records processed",
		job.ID, job.RecordsPurged, job.RecordsFound)
}

// hasLegalHoldConflict checks if any legal holds prevent purging the specified data
func (rs *RetentionScheduler) hasLegalHoldConflict(dataQuery map[string]interface{}) bool {
	rs.mutex.RLock()
	defer rs.mutex.RUnlock()

	for _, hold := range rs.legalHolds {
		if !hold.IsActive {
			continue
		}

		if hold.ExpiresAt != nil && time.Now().After(*hold.ExpiresAt) {
			hold.IsActive = false
			continue
		}

		// Simple conflict detection - in practice this would be more sophisticated
		// checking overlap between dataQuery and hold.DataQuery
		if dataCategory, exists := dataQuery["data_category"]; exists {
			if holdCategory, holdExists := hold.DataQuery["data_category"]; holdExists {
				if dataCategory == holdCategory {
					return true
				}
			}
		}
	}

	return false
}

// GetRetentionMetrics returns metrics about retention operations
func (rs *RetentionScheduler) GetRetentionMetrics() *RetentionMetrics {
	rs.mutex.RLock()
	defer rs.mutex.RUnlock()

	metrics := &RetentionMetrics{
		ActivePolicies: len(rs.policies),
		PendingJobs:    0,
		RunningJobs:    0,
		CompletedJobs:  0,
		FailedJobs:     0,
		ActiveHolds:    0,
	}

	for _, job := range rs.jobs {
		switch job.Status {
		case "pending":
			metrics.PendingJobs++
		case "running":
			metrics.RunningJobs++
		case "completed":
			metrics.CompletedJobs++
		case "failed":
			metrics.FailedJobs++
		}
	}

	for _, hold := range rs.legalHolds {
		if hold.IsActive {
			metrics.ActiveHolds++
		}
	}

	return metrics
}

// RetentionMetrics contains metrics about retention operations
type RetentionMetrics struct {
	ActivePolicies int `json:"active_policies"`
	PendingJobs    int `json:"pending_jobs"`
	RunningJobs    int `json:"running_jobs"`
	CompletedJobs  int `json:"completed_jobs"`
	FailedJobs     int `json:"failed_jobs"`
	ActiveHolds    int `json:"active_holds"`
}

// Shutdown gracefully shuts down the retention scheduler
func (rs *RetentionScheduler) Shutdown() {
	rs.cancel()
}

// Helper functions for ID generation
func generateEventID() string {
	return fmt.Sprintf("event_%d", time.Now().UnixNano())
}

func generateJobID() string {
	return fmt.Sprintf("job_%d", time.Now().UnixNano())
}

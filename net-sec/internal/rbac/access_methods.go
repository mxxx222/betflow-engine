package rbac

import (
	"fmt"
	"time"
)

// CheckAccess verifies if a user has permission to perform an action
func (ac *AccessController) CheckAccess(sessionID, resource, action string, context map[string]interface{}) bool {
	ac.mutex.RLock()
	defer ac.mutex.RUnlock()

	session, exists := ac.sessions[sessionID]
	if !exists {
		ac.logAccessDenied("", resource, action, "invalid_session", context)
		return false
	}

	// Check session validity
	if time.Now().After(session.ExpiresAt) {
		ac.logAccessDenied(session.UserID, resource, action, "session_expired", context)
		return false
	}

	user, exists := ac.users[session.UserID]
	if !exists || !user.IsActive || user.IsLocked {
		ac.logAccessDenied(session.UserID, resource, action, "user_inactive_or_locked", context)
		return false
	}

	// Get user's effective permissions
	permissions := ac.getUserPermissions(user)

	// Check specific permission
	permitted := false
	var permissionUsed *Permission

	for _, perm := range permissions {
		if ac.permissionMatches(perm, resource, action) {
			permitted = true
			permissionUsed = perm
			break
		}
	}

	// Enhanced checks for high-risk operations
	if permitted && permissionUsed != nil && permissionUsed.IsHighRisk {
		// Check MFA requirement
		if ac.config.RequireMFA && !session.MFAVerified {
			ac.logAccessDenied(session.UserID, resource, action, "mfa_required", context)
			return false
		}

		// Check if justification is required and provided
		if permissionUsed.RequiresJustification {
			if justification, ok := context["justification"]; !ok || justification == "" {
				ac.logAccessDenied(session.UserID, resource, action, "justification_required", context)
				return false
			}
		}

		// Check data classification compatibility
		if ac.config.DataClassificationReq {
			if dataClass, ok := context["data_classification"]; ok {
				if !ac.isDataClassificationCompatible(permissionUsed.DataClassification, dataClass.(string)) {
					ac.logAccessDenied(session.UserID, resource, action, "data_classification_mismatch", context)
					return false
				}
			}
		}
	}

	// Update session activity
	session.LastActivity = time.Now()
	if session.AccessedResources == nil {
		session.AccessedResources = make(map[string]time.Time)
	}
	session.AccessedResources[resource] = time.Now()

	// Log access attempt
	riskLevel := "low"
	if permissionUsed != nil && permissionUsed.IsHighRisk {
		riskLevel = "high"
	}

	event := AccessAuditEvent{
		ID:        generateAuditID(),
		Timestamp: time.Now(),
		UserID:    session.UserID,
		SessionID: sessionID,
		Resource:  resource,
		Action:    action,
		IPAddress: session.IPAddress,
		UserAgent: session.UserAgent,
		Success:   permitted,
		RiskLevel: riskLevel,
		Metadata:  context,
	}

	if permitted {
		event.LegalBasis = ac.getLegalBasisForAccess(user, permissionUsed)
		if dataCategory, ok := context["data_category"]; ok {
			event.DataCategory = dataCategory.(string)
		}
	} else {
		event.DenialReason = "insufficient_permissions"
	}

	if ac.auditLog != nil {
		ac.auditLog.LogAccessAttempt(event)
	}

	return permitted
}

// CreateSession creates a new authenticated session
func (ac *AccessController) CreateSession(userID, ipAddress, userAgent string) (*Session, error) {
	ac.mutex.Lock()
	defer ac.mutex.Unlock()

	user, exists := ac.users[userID]
	if !exists {
		return nil, fmt.Errorf("user not found")
	}

	if !user.IsActive {
		return nil, fmt.Errorf("user account is inactive")
	}

	if user.IsLocked {
		// Check if lockout period has expired
		if user.LastFailedAttempt != nil && time.Since(*user.LastFailedAttempt) < ac.config.LockoutDuration {
			return nil, fmt.Errorf("user account is locked")
		} else {
			// Unlock user
			user.IsLocked = false
			user.FailedAttempts = 0
		}
	}

	sessionID := generateSessionID()
	now := time.Now()
	expiresAt := now.Add(ac.config.SessionTimeout)

	session := &Session{
		ID:                sessionID,
		UserID:            userID,
		CreatedAt:         now,
		ExpiresAt:         expiresAt,
		LastActivity:      now,
		IPAddress:         ipAddress,
		UserAgent:         userAgent,
		MFAVerified:       !ac.config.RequireMFA, // If MFA not required globally
		AccessedResources: make(map[string]time.Time),
		Metadata:          make(map[string]interface{}),
	}

	ac.sessions[sessionID] = session

	// Update user login time
	user.LastLogin = &now
	user.UpdatedAt = now

	// Log session creation
	if ac.auditLog != nil {
		event := SessionAuditEvent{
			ID:        generateAuditID(),
			Timestamp: now,
			SessionID: sessionID,
			UserID:    userID,
			EventType: "created",
			IPAddress: ipAddress,
			UserAgent: userAgent,
			Metadata: map[string]interface{}{
				"expires_at": expiresAt,
			},
		}
		ac.auditLog.LogSessionEvent(event)
	}

	return session, nil
}

// ElevatePrivileges temporarily grants additional privileges to a session
func (ac *AccessController) ElevatePrivileges(sessionID string, privileges []string, duration time.Duration, justification, approvedBy string) error {
	ac.mutex.Lock()
	defer ac.mutex.Unlock()

	session, exists := ac.sessions[sessionID]
	if !exists {
		return fmt.Errorf("session not found")
	}

	if time.Now().After(session.ExpiresAt) {
		return fmt.Errorf("session expired")
	}

	user, exists := ac.users[session.UserID]
	if !exists {
		return fmt.Errorf("user not found")
	}

	// Detect potential privilege escalation
	currentPrivileges := ac.getUserPermissions(user)
	escalationDetected := ac.detectPrivilegeEscalation(currentPrivileges, privileges)

	if escalationDetected && ac.config.PrivilegeEscalation {
		riskScore := ac.calculateEscalationRisk(session, privileges)

		event := PrivilegeEscalationEvent{
			ID:              generateAuditID(),
			Timestamp:       time.Now(),
			UserID:          session.UserID,
			SessionID:       sessionID,
			FromPrivileges:  ac.getPermissionNames(currentPrivileges),
			ToPrivileges:    privileges,
			Justification:   justification,
			ApprovedBy:      approvedBy,
			Duration:        duration,
			Success:         true,
			DetectionMethod: "automatic",
			RiskScore:       riskScore,
		}

		if ac.auditLog != nil {
			ac.auditLog.LogPrivilegeEscalation(event)
		}

		// High risk escalations require approval
		if riskScore > 0.7 && approvedBy == "" {
			return fmt.Errorf("high-risk privilege escalation requires approval")
		}
	}

	// Apply privilege elevation
	expiresAt := time.Now().Add(duration)
	session.ElevatedPrivileges = privileges
	session.ElevatedExpiresAt = &expiresAt

	return nil
}

// getUserPermissions retrieves all permissions for a user based on their roles
func (ac *AccessController) getUserPermissions(user *User) []*Permission {
	var permissions []*Permission

	for _, roleID := range user.Roles {
		if role, exists := ac.roles[roleID]; exists {
			for _, permID := range role.Permissions {
				if perm, exists := ac.permissions[permID]; exists {
					permissions = append(permissions, perm)
				}
			}
		}
	}

	return permissions
}

// permissionMatches checks if a permission matches the requested resource/action
func (ac *AccessController) permissionMatches(permission *Permission, resource, action string) bool {
	resourceMatch := permission.Resource == resource || permission.Resource == "*"
	actionMatch := permission.Action == action || permission.Action == "*"
	return resourceMatch && actionMatch
}

// isDataClassificationCompatible checks if the permission allows access to the data classification
func (ac *AccessController) isDataClassificationCompatible(permissionClass, dataClass string) bool {
	classificationLevels := map[string]int{
		"public":       1,
		"internal":     2,
		"confidential": 3,
		"restricted":   4,
	}

	permLevel, permExists := classificationLevels[permissionClass]
	dataLevel, dataExists := classificationLevels[dataClass]

	if !permExists || !dataExists {
		return false
	}

	return permLevel >= dataLevel
}

// getLegalBasisForAccess determines the GDPR legal basis for the access
func (ac *AccessController) getLegalBasisForAccess(user *User, permission *Permission) string {
	// Find the most appropriate legal basis from user's roles
	for _, roleID := range user.Roles {
		if role, exists := ac.roles[roleID]; exists {
			// Check if the role has permissions that match this permission
			for _, permID := range role.Permissions {
				if permID == permission.ID && len(role.LegalBases) > 0 {
					return role.LegalBases[0] // Return first legal basis
				}
			}
		}
	}

	return "Article 6(1)(f) - Legitimate interests" // Default
}

// detectPrivilegeEscalation detects if requested privileges represent an escalation
func (ac *AccessController) detectPrivilegeEscalation(current []*Permission, requested []string) bool {
	currentPerms := make(map[string]bool)
	for _, perm := range current {
		currentPerms[perm.ID] = true
	}

	for _, reqPerm := range requested {
		if !currentPerms[reqPerm] {
			return true // New permission requested = escalation
		}
	}

	return false
}

// calculateEscalationRisk calculates risk score for privilege escalation
func (ac *AccessController) calculateEscalationRisk(session *Session, privileges []string) float64 {
	risk := 0.0

	// Base risk factors
	if session.IPAddress == "" {
		risk += 0.2 // Unknown IP
	}

	// Time-based risk
	hour := time.Now().Hour()
	if hour < 7 || hour > 19 {
		risk += 0.3 // Outside business hours
	}

	// Permission-based risk
	for _, privID := range privileges {
		if perm, exists := ac.permissions[privID]; exists && perm.IsHighRisk {
			risk += 0.4
		}
	}

	// Session age risk
	sessionAge := time.Since(session.CreatedAt)
	if sessionAge < 5*time.Minute {
		risk += 0.2 // Very new session
	}

	// Cap at 1.0
	if risk > 1.0 {
		risk = 1.0
	}

	return risk
}

// getPermissionNames extracts permission names from permission objects
func (ac *AccessController) getPermissionNames(permissions []*Permission) []string {
	names := make([]string, len(permissions))
	for i, perm := range permissions {
		names[i] = perm.ID
	}
	return names
}

// logAccessDenied logs a denied access attempt
func (ac *AccessController) logAccessDenied(userID, resource, action, reason string, context map[string]interface{}) {
	if ac.auditLog != nil {
		event := AccessAuditEvent{
			ID:           generateAuditID(),
			Timestamp:    time.Now(),
			UserID:       userID,
			Resource:     resource,
			Action:       action,
			Success:      false,
			DenialReason: reason,
			RiskLevel:    "medium",
			Metadata:     context,
		}

		if ipAddr, ok := context["ip_address"]; ok {
			event.IPAddress = ipAddr.(string)
		}

		ac.auditLog.LogAccessAttempt(event)
	}
}

// generateSessionID generates a unique session ID
func generateSessionID() string {
	return fmt.Sprintf("sess_%d", time.Now().UnixNano())
}

// AddUser adds a new user to the system
func (ac *AccessController) AddUser(user *User) error {
	ac.mutex.Lock()
	defer ac.mutex.Unlock()

	if _, exists := ac.users[user.ID]; exists {
		return fmt.Errorf("user already exists")
	}

	user.CreatedAt = time.Now()
	user.UpdatedAt = time.Now()
	user.IsActive = true
	user.IsLocked = false
	user.FailedAttempts = 0

	ac.users[user.ID] = user
	return nil
}

// AssignRole assigns a role to a user
func (ac *AccessController) AssignRole(userID, roleID string) error {
	ac.mutex.Lock()
	defer ac.mutex.Unlock()

	user, exists := ac.users[userID]
	if !exists {
		return fmt.Errorf("user not found")
	}

	role, exists := ac.roles[roleID]
	if !exists {
		return fmt.Errorf("role not found")
	}

	// Check if role requires approval
	if role.RequiresApproval {
		// In a real system, this would trigger an approval workflow
		return fmt.Errorf("role assignment requires approval")
	}

	// Check if user already has the role
	for _, existingRole := range user.Roles {
		if existingRole == roleID {
			return fmt.Errorf("user already has this role")
		}
	}

	user.Roles = append(user.Roles, roleID)
	user.UpdatedAt = time.Now()

	return nil
}

// RevokeRole removes a role from a user
func (ac *AccessController) RevokeRole(userID, roleID string) error {
	ac.mutex.Lock()
	defer ac.mutex.Unlock()

	user, exists := ac.users[userID]
	if !exists {
		return fmt.Errorf("user not found")
	}

	for i, role := range user.Roles {
		if role == roleID {
			user.Roles = append(user.Roles[:i], user.Roles[i+1:]...)
			user.UpdatedAt = time.Now()
			return nil
		}
	}

	return fmt.Errorf("user does not have this role")
}

// GetRBACMetrics returns metrics about the RBAC system
func (ac *AccessController) GetRBACMetrics() *RBACMetrics {
	ac.mutex.RLock()
	defer ac.mutex.RUnlock()

	metrics := &RBACMetrics{
		TotalUsers:       len(ac.users),
		ActiveUsers:      0,
		LockedUsers:      0,
		TotalRoles:       len(ac.roles),
		TotalPermissions: len(ac.permissions),
		ActiveSessions:   0,
	}

	for _, user := range ac.users {
		if user.IsActive {
			metrics.ActiveUsers++
		}
		if user.IsLocked {
			metrics.LockedUsers++
		}
	}

	now := time.Now()
	for _, session := range ac.sessions {
		if now.Before(session.ExpiresAt) {
			metrics.ActiveSessions++
		}
	}

	return metrics
}

// RBACMetrics contains metrics about the RBAC system
type RBACMetrics struct {
	TotalUsers       int `json:"total_users"`
	ActiveUsers      int `json:"active_users"`
	LockedUsers      int `json:"locked_users"`
	TotalRoles       int `json:"total_roles"`
	TotalPermissions int `json:"total_permissions"`
	ActiveSessions   int `json:"active_sessions"`
}

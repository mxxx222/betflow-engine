package integrations

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"sync"
	"time"
)

// NotionIntegration implements GDPR-compliant Notion integration
type NotionIntegration struct {
	apiToken    string
	baseURL     string
	httpClient  *http.Client
	metrics     *IntegrationMetrics
	rateLimiter *RateLimiter
	mutex       sync.RWMutex
}

// JiraIntegration implements GDPR-compliant Jira integration
type JiraIntegration struct {
	username    string
	apiToken    string
	baseURL     string
	httpClient  *http.Client
	metrics     *IntegrationMetrics
	rateLimiter *RateLimiter
	mutex       sync.RWMutex
}

// DriveIntegration implements GDPR-compliant Google Drive integration
type DriveIntegration struct {
	serviceAccountKey []byte
	baseURL           string
	httpClient        *http.Client
	metrics           *IntegrationMetrics
	rateLimiter       *RateLimiter
	mutex             sync.RWMutex
}

// RateLimiter implements token bucket rate limiting
type RateLimiter struct {
	tokens     int
	capacity   int
	refillRate int
	lastRefill time.Time
	mutex      sync.Mutex
}

// NewRateLimiter creates a new rate limiter
func NewRateLimiter(capacity, refillRate int) *RateLimiter {
	return &RateLimiter{
		tokens:     capacity,
		capacity:   capacity,
		refillRate: refillRate,
		lastRefill: time.Now(),
	}
}

// Allow checks if a request is allowed within rate limits
func (rl *RateLimiter) Allow() bool {
	rl.mutex.Lock()
	defer rl.mutex.Unlock()

	now := time.Now()
	elapsed := now.Sub(rl.lastRefill)

	// Refill tokens based on elapsed time
	tokensToAdd := int(elapsed.Seconds()) * rl.refillRate
	if tokensToAdd > 0 {
		rl.tokens += tokensToAdd
		if rl.tokens > rl.capacity {
			rl.tokens = rl.capacity
		}
		rl.lastRefill = now
	}

	// Check if we have tokens available
	if rl.tokens > 0 {
		rl.tokens--
		return true
	}

	return false
}

// ===== NOTION INTEGRATION =====

// NewNotionIntegration creates a new Notion integration
func NewNotionIntegration(apiToken string) *NotionIntegration {
	return &NotionIntegration{
		apiToken:    apiToken,
		baseURL:     "https://api.notion.com/v1",
		httpClient:  &http.Client{Timeout: 30 * time.Second},
		metrics:     &IntegrationMetrics{},
		rateLimiter: NewRateLimiter(100, 3), // 3 requests per second, burst of 100
	}
}

func (n *NotionIntegration) Name() string {
	return "notion"
}

func (n *NotionIntegration) Authenticate(credentials map[string]string) error {
	if token, ok := credentials["api_token"]; ok {
		n.apiToken = token
		return n.ValidateConnection()
	}
	return fmt.Errorf("api_token required for Notion authentication")
}

func (n *NotionIntegration) SendData(ctx context.Context, data *IntegrationData) error {
	if !n.rateLimiter.Allow() {
		return fmt.Errorf("rate limit exceeded")
	}

	n.mutex.Lock()
	defer n.mutex.Unlock()

	start := time.Now()

	// Convert IntegrationData to Notion format
	notionData := n.convertToNotionFormat(data)

	// Create HTTP request
	reqBody, err := json.Marshal(notionData)
	if err != nil {
		return fmt.Errorf("failed to marshal request: %w", err)
	}

	endpoint := fmt.Sprintf("%s/pages", n.baseURL)
	req, err := http.NewRequestWithContext(ctx, "POST", endpoint, strings.NewReader(string(reqBody)))
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	n.setNotionHeaders(req)

	// Execute request
	resp, err := n.httpClient.Do(req)
	if err != nil {
		n.updateMetrics(false, time.Since(start), len(reqBody), 0)
		return fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	success := resp.StatusCode >= 200 && resp.StatusCode < 300
	n.updateMetrics(success, time.Since(start), len(reqBody), resp.ContentLength)

	if !success {
		return fmt.Errorf("API request failed with status %d", resp.StatusCode)
	}

	return nil
}

func (n *NotionIntegration) RetrieveData(ctx context.Context, query *DataQuery) (*IntegrationData, error) {
	if !n.rateLimiter.Allow() {
		return nil, fmt.Errorf("rate limit exceeded")
	}

	n.mutex.Lock()
	defer n.mutex.Unlock()

	start := time.Now()

	// Build query URL with data minimization
	endpoint := fmt.Sprintf("%s/databases/%s/query", n.baseURL, query.Filters["database_id"])

	queryBody := map[string]interface{}{
		"page_size": query.Limit,
	}

	// Apply field filtering for data minimization
	if len(query.Fields) > 0 {
		queryBody["filter"] = map[string]interface{}{
			"property": "Name", // This would be more sophisticated in practice
			"title": map[string]interface{}{
				"is_not_empty": true,
			},
		}
	}

	reqBody, err := json.Marshal(queryBody)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal query: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, "POST", endpoint, strings.NewReader(string(reqBody)))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	n.setNotionHeaders(req)

	// Execute request
	resp, err := n.httpClient.Do(req)
	if err != nil {
		n.updateMetrics(false, time.Since(start), len(reqBody), 0)
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	success := resp.StatusCode >= 200 && resp.StatusCode < 300
	if !success {
		n.updateMetrics(false, time.Since(start), len(reqBody), resp.ContentLength)
		return nil, fmt.Errorf("API request failed with status %d", resp.StatusCode)
	}

	// Parse response
	var notionResp map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&notionResp); err != nil {
		n.updateMetrics(false, time.Since(start), len(reqBody), resp.ContentLength)
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	n.updateMetrics(true, time.Since(start), len(reqBody), resp.ContentLength)

	// Convert to IntegrationData format
	data := n.convertFromNotionFormat(notionResp, query)
	return data, nil
}

func (n *NotionIntegration) ValidateConnection() error {
	endpoint := fmt.Sprintf("%s/users/me", n.baseURL)
	req, err := http.NewRequest("GET", endpoint, nil)
	if err != nil {
		return err
	}

	n.setNotionHeaders(req)

	resp, err := n.httpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		return fmt.Errorf("authentication failed with status %d", resp.StatusCode)
	}

	return nil
}

func (n *NotionIntegration) GetMetrics() *IntegrationMetrics {
	n.mutex.RLock()
	defer n.mutex.RUnlock()

	// Return a copy to prevent concurrent access issues
	metricsCopy := *n.metrics
	return &metricsCopy
}

func (n *NotionIntegration) setNotionHeaders(req *http.Request) {
	req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", n.apiToken))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Notion-Version", "2022-06-28")
}

func (n *NotionIntegration) convertToNotionFormat(data *IntegrationData) map[string]interface{} {
	// Convert IntegrationData to Notion page format
	// This is a simplified example - real implementation would be more complex
	return map[string]interface{}{
		"parent": map[string]interface{}{
			"database_id": data.Metadata["database_id"],
		},
		"properties": map[string]interface{}{
			"Name": map[string]interface{}{
				"title": []map[string]interface{}{
					{
						"text": map[string]interface{}{
							"content": data.Content["title"],
						},
					},
				},
			},
			"Status": map[string]interface{}{
				"select": map[string]interface{}{
					"name": data.Content["status"],
				},
			},
		},
	}
}

func (n *NotionIntegration) convertFromNotionFormat(notionData map[string]interface{}, query *DataQuery) *IntegrationData {
	// Convert Notion response to IntegrationData format
	// This is simplified - real implementation would be more sophisticated
	data := &IntegrationData{
		ID:                fmt.Sprintf("notion_%s", notionData["id"]),
		Type:              query.Type,
		Classification:    "internal", // Would be determined based on content
		Content:           make(map[string]interface{}),
		Metadata:          make(map[string]interface{}),
		PersonalData:      make([]PersonalDataField, 0),
		LegalBasis:        query.LegalBasis,
		ProcessingPurpose: query.Justification,
		CreatedAt:         time.Now(),
		UpdatedAt:         time.Now(),
	}

	// Extract content with data minimization
	if results, ok := notionData["results"].([]interface{}); ok && len(results) > 0 {
		if page, ok := results[0].(map[string]interface{}); ok {
			if props, ok := page["properties"].(map[string]interface{}); ok {
				for key, value := range props {
					// Only include requested fields for data minimization
					if len(query.Fields) == 0 || contains(query.Fields, key) {
						data.Content[key] = value

						// Identify potential personal data fields
						if isPersonalDataField(key) {
							data.PersonalData = append(data.PersonalData, PersonalDataField{
								Field:        key,
								DataCategory: classifyField(key),
								IsMinimized:  len(query.Fields) > 0,
							})
						}
					}
				}
			}
		}
	}

	return data
}

func (n *NotionIntegration) updateMetrics(success bool, duration time.Duration, bytesSent int, bytesReceived int64) {
	n.metrics.TotalRequests++
	if success {
		n.metrics.SuccessfulRequests++
	} else {
		n.metrics.FailedRequests++
	}

	// Update average response time
	if n.metrics.TotalRequests == 1 {
		n.metrics.AverageResponseTime = duration
	} else {
		n.metrics.AverageResponseTime = (n.metrics.AverageResponseTime*time.Duration(n.metrics.TotalRequests-1) + duration) / time.Duration(n.metrics.TotalRequests)
	}

	n.metrics.LastRequestTime = time.Now()
	n.metrics.DataSent += int64(bytesSent)
	n.metrics.DataReceived += bytesReceived
}

// ===== JIRA INTEGRATION =====

func NewJiraIntegration(username, apiToken, baseURL string) *JiraIntegration {
	return &JiraIntegration{
		username:    username,
		apiToken:    apiToken,
		baseURL:     baseURL,
		httpClient:  &http.Client{Timeout: 30 * time.Second},
		metrics:     &IntegrationMetrics{},
		rateLimiter: NewRateLimiter(100, 5), // 5 requests per second
	}
}

func (j *JiraIntegration) Name() string {
	return "jira"
}

func (j *JiraIntegration) Authenticate(credentials map[string]string) error {
	username, hasUser := credentials["username"]
	token, hasToken := credentials["api_token"]
	baseURL, hasURL := credentials["base_url"]

	if !hasUser || !hasToken || !hasURL {
		return fmt.Errorf("username, api_token, and base_url required for Jira authentication")
	}

	j.username = username
	j.apiToken = token
	j.baseURL = baseURL

	return j.ValidateConnection()
}

func (j *JiraIntegration) SendData(ctx context.Context, data *IntegrationData) error {
	if !j.rateLimiter.Allow() {
		return fmt.Errorf("rate limit exceeded")
	}

	j.mutex.Lock()
	defer j.mutex.Unlock()

	start := time.Now()

	// Convert to Jira issue format
	jiraIssue := j.convertToJiraFormat(data)

	reqBody, err := json.Marshal(jiraIssue)
	if err != nil {
		return fmt.Errorf("failed to marshal request: %w", err)
	}

	endpoint := fmt.Sprintf("%s/rest/api/3/issue", j.baseURL)
	req, err := http.NewRequestWithContext(ctx, "POST", endpoint, strings.NewReader(string(reqBody)))
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	j.setJiraHeaders(req)

	resp, err := j.httpClient.Do(req)
	if err != nil {
		j.updateJiraMetrics(false, time.Since(start), len(reqBody), 0)
		return fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	success := resp.StatusCode >= 200 && resp.StatusCode < 300
	j.updateJiraMetrics(success, time.Since(start), len(reqBody), resp.ContentLength)

	if !success {
		return fmt.Errorf("API request failed with status %d", resp.StatusCode)
	}

	return nil
}

func (j *JiraIntegration) RetrieveData(ctx context.Context, query *DataQuery) (*IntegrationData, error) {
	if !j.rateLimiter.Allow() {
		return nil, fmt.Errorf("rate limit exceeded")
	}

	j.mutex.Lock()
	defer j.mutex.Unlock()

	start := time.Now()

	// Build JQL query with data minimization
	jqlQuery := j.buildJQLQuery(query)
	endpoint := fmt.Sprintf("%s/rest/api/3/search?jql=%s&maxResults=%d&startAt=%d",
		j.baseURL, jqlQuery, query.Limit, query.Offset)

	// Add field restrictions for data minimization
	if len(query.Fields) > 0 {
		endpoint += "&fields=" + strings.Join(query.Fields, ",")
	}

	req, err := http.NewRequestWithContext(ctx, "GET", endpoint, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	j.setJiraHeaders(req)

	resp, err := j.httpClient.Do(req)
	if err != nil {
		j.updateJiraMetrics(false, time.Since(start), 0, 0)
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	success := resp.StatusCode >= 200 && resp.StatusCode < 300
	if !success {
		j.updateJiraMetrics(false, time.Since(start), 0, resp.ContentLength)
		return nil, fmt.Errorf("API request failed with status %d", resp.StatusCode)
	}

	var jiraResp map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&jiraResp); err != nil {
		j.updateJiraMetrics(false, time.Since(start), 0, resp.ContentLength)
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	j.updateJiraMetrics(true, time.Since(start), 0, resp.ContentLength)

	data := j.convertFromJiraFormat(jiraResp, query)
	return data, nil
}

func (j *JiraIntegration) ValidateConnection() error {
	endpoint := fmt.Sprintf("%s/rest/api/3/myself", j.baseURL)
	req, err := http.NewRequest("GET", endpoint, nil)
	if err != nil {
		return err
	}

	j.setJiraHeaders(req)

	resp, err := j.httpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		return fmt.Errorf("authentication failed with status %d", resp.StatusCode)
	}

	return nil
}

func (j *JiraIntegration) GetMetrics() *IntegrationMetrics {
	j.mutex.RLock()
	defer j.mutex.RUnlock()
	metricsCopy := *j.metrics
	return &metricsCopy
}

func (j *JiraIntegration) setJiraHeaders(req *http.Request) {
	req.SetBasicAuth(j.username, j.apiToken)
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")
}

func (j *JiraIntegration) convertToJiraFormat(data *IntegrationData) map[string]interface{} {
	return map[string]interface{}{
		"fields": map[string]interface{}{
			"project": map[string]interface{}{
				"key": data.Metadata["project_key"],
			},
			"summary":     data.Content["title"],
			"description": data.Content["description"],
			"issuetype": map[string]interface{}{
				"name": data.Content["issue_type"],
			},
		},
	}
}

func (j *JiraIntegration) convertFromJiraFormat(jiraData map[string]interface{}, query *DataQuery) *IntegrationData {
	data := &IntegrationData{
		ID:                fmt.Sprintf("jira_%s", jiraData["id"]),
		Type:              query.Type,
		Classification:    "internal",
		Content:           make(map[string]interface{}),
		Metadata:          make(map[string]interface{}),
		PersonalData:      make([]PersonalDataField, 0),
		LegalBasis:        query.LegalBasis,
		ProcessingPurpose: query.Justification,
		CreatedAt:         time.Now(),
		UpdatedAt:         time.Now(),
	}

	if issues, ok := jiraData["issues"].([]interface{}); ok && len(issues) > 0 {
		if issue, ok := issues[0].(map[string]interface{}); ok {
			if fields, ok := issue["fields"].(map[string]interface{}); ok {
				for key, value := range fields {
					if len(query.Fields) == 0 || contains(query.Fields, key) {
						data.Content[key] = value

						if isPersonalDataField(key) {
							data.PersonalData = append(data.PersonalData, PersonalDataField{
								Field:        key,
								DataCategory: classifyField(key),
								IsMinimized:  len(query.Fields) > 0,
							})
						}
					}
				}
			}
		}
	}

	return data
}

func (j *JiraIntegration) buildJQLQuery(query *DataQuery) string {
	jql := "project is not EMPTY"

	if projectKey, ok := query.Filters["project_key"]; ok {
		jql = fmt.Sprintf("project = %s", projectKey)
	}

	if query.DateRange != nil {
		jql += fmt.Sprintf(" AND created >= '%s' AND created <= '%s'",
			query.DateRange.Start.Format("2006-01-02"),
			query.DateRange.End.Format("2006-01-02"))
	}

	return jql
}

func (j *JiraIntegration) updateJiraMetrics(success bool, duration time.Duration, bytesSent int, bytesReceived int64) {
	j.metrics.TotalRequests++
	if success {
		j.metrics.SuccessfulRequests++
	} else {
		j.metrics.FailedRequests++
	}

	if j.metrics.TotalRequests == 1 {
		j.metrics.AverageResponseTime = duration
	} else {
		j.metrics.AverageResponseTime = (j.metrics.AverageResponseTime*time.Duration(j.metrics.TotalRequests-1) + duration) / time.Duration(j.metrics.TotalRequests)
	}

	j.metrics.LastRequestTime = time.Now()
	j.metrics.DataSent += int64(bytesSent)
	j.metrics.DataReceived += bytesReceived
}

// Helper functions for data classification and field detection

func contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}

func isPersonalDataField(fieldName string) bool {
	personalFields := []string{"email", "name", "phone", "address", "assignee", "reporter", "creator"}
	fieldLower := strings.ToLower(fieldName)

	for _, pf := range personalFields {
		if strings.Contains(fieldLower, pf) {
			return true
		}
	}
	return false
}

func classifyField(fieldName string) string {
	fieldLower := strings.ToLower(fieldName)

	sensitiveFields := []string{"email", "phone", "address", "ssn", "id"}
	for _, sf := range sensitiveFields {
		if strings.Contains(fieldLower, sf) {
			return "sensitive"
		}
	}

	personalFields := []string{"name", "assignee", "reporter", "creator"}
	for _, pf := range personalFields {
		if strings.Contains(fieldLower, pf) {
			return "personal"
		}
	}

	return "general"
}

"""Realistic support ticket templates for AI Support Copilot seed data."""

# Support team members with realistic roles
SUPPORT_TEAM = [
    ("sarah.johnson", "Sarah Johnson", "sarah.johnson@company.com", "Support Lead"),
    ("mike.chen", "Mike Chen", "mike.chen@company.com", "Senior Support Engineer"),
    ("emma.wilson", "Emma Wilson", "emma.wilson@company.com", "Support Engineer"),
    ("alex.rodriguez", "Alex Rodriguez", "alex.rodriguez@company.com", "Support Engineer"),
    ("lisa.patel", "Lisa Patel", "lisa.patel@company.com", "Junior Support Engineer"),
    ("tom.brown", "Tom Brown", "tom.brown@company.com", "Junior Support Engineer"),
    ("nina.kowalski", "Nina Kowalski", "nina.kowalski@company.com", "Support Specialist"),
    ("raj.sharma", "Raj Sharma", "raj.sharma@company.com", "Technical Support"),
]

# Customer accounts (reporters)
CUSTOMERS = [
    ("customer.john", "John Smith", "john.smith@customer1.com"),
    ("customer.mary", "Mary Davis", "mary.davis@customer2.com"),
    ("customer.robert", "Robert Lee", "robert.lee@customer3.com"),
    ("customer.jennifer", "Jennifer Taylor", "jennifer.taylor@customer4.com"),
    ("customer.david", "David Martinez", "david.martinez@customer5.com"),
    ("customer.susan", "Susan Anderson", "susan.anderson@customer6.com"),
    ("customer.james", "James Wilson", "james.wilson@customer7.com"),
    ("customer.patricia", "Patricia Moore", "patricia.moore@customer8.com"),
]

# Bug Report Scenarios
BUG_REPORTS = [
    {
        "summary": "Login page returns 500 error after password reset",
        "description": "After resetting my password, I'm unable to log in. The page shows a 500 Internal Server Error. This is blocking my entire team from accessing the system.",
        "priority": "High",
        "labels": ["bug", "login", "p1", "blocker"],
        "comments": [
            "Can you provide the exact timestamp when this occurred?",
            "This happened at 2024-01-15 14:32 UTC. Our entire team of 15 people is affected.",
            "Thank you. I can see the error in our logs. Investigating now.",
            "Found the issue - database connection pool was exhausted. Deploying fix.",
            "Fix deployed. Can you please try logging in again?",
            "Working now! Thank you for the quick response.",
        ],
    },
    {
        "summary": "Dashboard widgets not loading on mobile devices",
        "description": "When I access the dashboard from my iPhone, the widgets show loading spinners indefinitely. Desktop version works fine.",
        "priority": "Medium",
        "labels": ["bug", "mobile", "ui", "p2"],
        "comments": [
            "Which iOS version are you using?",
            "iOS 17.2 on iPhone 14 Pro",
            "Can you try clearing your browser cache?",
            "Tried that, still not working. Also tested on Android - same issue.",
            "This appears to be a CORS issue with our CDN. Escalating to engineering.",
        ],
    },
    {
        "summary": "Export to CSV generates corrupted files",
        "description": "When exporting reports to CSV, the file contains garbled characters instead of proper data. This worked fine last week.",
        "priority": "Medium",
        "labels": ["bug", "export", "data", "regression"],
        "comments": [
            "Can you share a sample of the corrupted file?",
            "Attached: export_sample.csv",
            "I see the issue - UTF-8 encoding problem. Working on a fix.",
            "Fix ready for testing. Can you try the export again?",
            "Perfect! The export now works correctly. Thank you!",
        ],
    },
]

# Access Request Scenarios
ACCESS_REQUESTS = [
    {
        "summary": "New employee needs access to production environment",
        "description": "New team member Alex Rodriguez (alex.rodriguez@company.com) started today and needs access to: Production dashboard, AWS console (read-only), and Datadog monitoring.",
        "priority": "High",
        "labels": ["access-request", "onboarding", "p1"],
        "comments": [
            "Please confirm the manager approval for production access.",
            "Manager Sarah Johnson approved via email (forwarded to support@company.com)",
            "Access provisioned. Credentials sent via secure link.",
            "Received and tested. All working. Thanks!",
        ],
    },
    {
        "summary": "Unable to access VPN after password change",
        "description": "Changed my password yesterday and now VPN authentication fails. Using Cisco AnyConnect client version 4.10.",
        "priority": "High",
        "labels": ["access-request", "vpn", "authentication"],
        "comments": [
            "Have you tried resetting your VPN password separately?",
            "No, I thought it would sync automatically.",
            "VPN uses a separate credential system. I'll reset it for you.",
            "VPN password reset. Check your email for the temporary password.",
            "Connected successfully. Thank you!",
        ],
    },
]

# Billing Issues
BILLING_ISSUES = [
    {
        "summary": "Charged twice for monthly subscription",
        "description": "I was charged $299 twice on January 1st (transaction IDs: TXN-12345 and TXN-12346). Please refund the duplicate charge.",
        "priority": "High",
        "labels": ["billing", "refund", "p1"],
        "comments": [
            "I can see both charges in our system. Investigating why this happened.",
            "This was caused by a payment gateway timeout. Refund initiated.",
            "Refund will appear in 3-5 business days. We've also added a $50 credit to your account as an apology.",
            "Thank you for the quick resolution and the credit!",
        ],
    },
    {
        "summary": "Invoice shows incorrect number of users",
        "description": "Latest invoice (INV-2024-001) shows 50 users but we only have 35 active users. Please correct and reissue.",
        "priority": "Medium",
        "labels": ["billing", "invoice", "p2"],
        "comments": [
            "Can you provide a list of your active users?",
            "Attached: active_users_list.xlsx",
            "I see the discrepancy. 15 users were deactivated but still counted. Correcting now.",
            "Corrected invoice sent. Difference will be credited to next month.",
        ],
    },
]

# Incident Reports
INCIDENTS = [
    {
        "summary": "Complete service outage - all users affected",
        "description": "Our entire platform is down. Users getting 503 errors. This is affecting all our customers. URGENT!",
        "priority": "Critical",
        "labels": ["incident", "outage", "p0", "critical"],
        "comments": [
            "Incident confirmed. Escalating to on-call engineer immediately.",
            "Database cluster is down. Failover in progress.",
            "Failover complete. Services coming back online.",
            "All systems operational. Incident duration: 23 minutes.",
            "Post-mortem will be shared within 48 hours.",
        ],
    },
    {
        "summary": "Slow response times on API endpoints",
        "description": "API response times increased from ~200ms to 5-10 seconds. Started approximately 30 minutes ago. Affecting our production integrations.",
        "priority": "High",
        "labels": ["incident", "performance", "api", "p1"],
        "comments": [
            "Confirmed. Seeing elevated latency in monitoring.",
            "Database query performance degraded. Investigating.",
            "Found slow query causing table lock. Optimizing.",
            "Query optimized and deployed. Response times back to normal.",
        ],
    },
]

# General Questions
QUESTIONS = [
    {
        "summary": "How to configure SSO with Azure AD?",
        "description": "We want to set up Single Sign-On using Azure Active Directory. Can you provide step-by-step instructions?",
        "priority": "Medium",
        "labels": ["question", "sso", "documentation"],
        "comments": [
            "I'll send you our SSO configuration guide.",
            "Guide sent. Let me know if you need help with any specific step.",
            "Step 3 is unclear - where do I find the tenant ID?",
            "Tenant ID is in Azure Portal > Azure Active Directory > Properties. Screenshot attached.",
            "Got it working! Thank you for the detailed help.",
        ],
    },
    {
        "summary": "What's the difference between Pro and Enterprise plans?",
        "description": "Considering upgrading from Pro to Enterprise. What additional features do we get?",
        "priority": "Low",
        "labels": ["question", "sales", "pricing"],
        "comments": [
            "Main differences: Advanced analytics, priority support, custom integrations, and SLA guarantees.",
            "Do you offer a trial period for Enterprise?",
            "Yes, 30-day trial available. I'll connect you with our sales team.",
        ],
    },
]

# Feature Requests
FEATURE_REQUESTS = [
    {
        "summary": "Add dark mode to dashboard",
        "description": "Would love to have a dark mode option for the dashboard. Many of our team members work late hours and would appreciate this.",
        "priority": "Low",
        "labels": ["feature-request", "ui", "enhancement"],
        "comments": [
            "Great suggestion! Adding to our product roadmap.",
            "This is planned for Q2 2024 release.",
            "Any updates on this?",
            "Development started. Expected in next month's release.",
        ],
    },
]

# All scenarios combined
ALL_SCENARIOS = (
    BUG_REPORTS + 
    ACCESS_REQUESTS + 
    BILLING_ISSUES + 
    INCIDENTS + 
    QUESTIONS + 
    FEATURE_REQUESTS
)

# Follow-up comment templates
FOLLOWUP_COMMENTS = [
    "Any updates on this issue?",
    "Still experiencing the same problem.",
    "This is now blocking our production deployment.",
    "Can we schedule a call to discuss this?",
    "Thank you for the quick response!",
    "This resolved our issue. Closing the ticket.",
    "Verified the fix in our environment. Working as expected.",
    "Unfortunately, the issue persists after the suggested fix.",
]

# Support agent responses
AGENT_RESPONSES = [
    "Thank you for reporting this. Investigating now.",
    "I can see the issue in our logs. Working on a resolution.",
    "This requires escalation to our engineering team.",
    "Fix has been deployed. Please verify and let us know.",
    "I've created a workaround for you while we work on a permanent fix.",
    "This is a known issue. We're working on it with high priority.",
    "Can you provide more details about your environment?",
    "I'll need to schedule a screen sharing session to debug this.",
]

# Resolution comments
RESOLUTION_COMMENTS = [
    "Issue resolved. Closing ticket.",
    "Fix deployed and verified. Marking as resolved.",
    "Workaround provided. Permanent fix scheduled for next release.",
    "Unable to reproduce. Closing as cannot reproduce.",
    "This is working as designed. Documentation updated.",
    "Duplicate of TICKET-123. Closing.",
]

# Sprint goals for support team
SUPPORT_SPRINT_GOALS = [
    "Reduce average response time to under 2 hours",
    "Clear backlog of P2 tickets",
    "Improve customer satisfaction score",
    "Complete knowledge base documentation",
    "Train team on new escalation procedures",
    "Implement automated ticket routing",
]


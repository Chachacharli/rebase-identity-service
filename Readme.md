# REBASE BASE IDENTITY SERVICE

## What is an Identity Provider (IdP)?

An **Identity Provider (IdP)** is a system that manages user identities and provides authentication and authorization services to applications. It acts as a central authority for verifying user credentials and issuing tokens that allow users to access protected resources across multiple applications.

## About this IdP

This project implements a **multi-tenant Identity Provider** based on modern standards:

- **OAuth 2.0**: Secure authorization for APIs and applications.
- **OpenID Connect (OIDC)**: Authentication layer on top of OAuth 2.0.
- **PKCE (Proof Key for Code Exchange)**: Enhanced security for public clients (SPAs, mobile apps).

The IdP is designed to support multiple tenants, allowing different organizations or groups to manage their own users, roles, and permissions within the same system.

---

## How to run the app

You can start the development server using the CLI:

```bash
typer cli.py run
```

Or directly with FastAPI:

```bash
fastapi dev app/main.py
```

---

## Requirements management

Upgrade requirements:
```bash
pip freeze > requirements.txt
```

Install requirements:
```bash
pip install -r requirements.txt
```

---

## System Overview: Users, Roles, and Permissions

The IdP uses a flexible system to manage access control:

| Entity      | Description                                                                 |
|-------------|-----------------------------------------------------------------------------|
| **User**    | Represents an individual account. Each user can have multiple roles.        |
| **Role**    | A named collection of permissions. Roles are assigned to users.             |
| **Permission** | Represents a specific action or access right. Permissions are assigned to roles. |

### Relationships

- **Users ↔ Roles**: Many-to-many. A user can have multiple roles; a role can be assigned to multiple users.
- **Roles ↔ Permissions**: Many-to-many. A role can have multiple permissions; a permission can be assigned to multiple roles.

### Example Tables

#### Users

| id   | username | email           | ... |
|------|---------|-----------------|-----|
| 1    | alice   | alice@tenant.com| ... |
| 2    | bob     | bob@tenant.com  | ... |

#### Roles

| id   | name      | description         |
|------|-----------|---------------------|
| 1    | admin     | Full access         |
| 2    | editor    | Can edit resources  |

#### Permissions

| id   | name         | description              |
|------|--------------|-------------------------|
| 1    | read         | Read resources          |
| 2    | write        | Write resources         |
| 3    | delete       | Delete resources        |

#### User-Roles

| user_id | role_id |
|---------|---------|
| 1       | 1       |
| 2       | 2       |

#### Role-Permissions

| role_id | permission_id |
|---------|--------------|
| 1       | 1            |
| 1       | 2            |
| 1       | 3            |
| 2       | 1            |
| 2       | 2            |

---

## How Access Control Works

1. **User Authentication**: Users authenticate via OAuth 2.0/OIDC flows. PKCE is used for public clients.
2. **Role Assignment**: Each user is assigned one or more roles.
3. **Permission Assignment**: Each role is assigned one or more permissions.
4. **Authorization**: When accessing a protected endpoint, the system checks if the user's roles include the required permission.

### Example Flow

- Alice logs in and receives a token.
- Alice's token contains her roles (e.g., `admin`).
- When Alice tries to delete a resource, the system checks if her roles include the `delete` permission.
- If yes, access is granted; otherwise, access is denied.

---

## Multi-Tenant Support

Each tenant can manage its own users, roles, and permissions independently, ensuring isolation and flexibility for organizations using the same IdP. (Pending implementation details)

---

## API Endpoints

- **User Management**: Create, update, assign roles.
- **Role Management**: Create, update, assign permissions.
- **Permission Management**: Create, update.
- **Authentication**: OAuth 2.0/OIDC flows with PKCE.

---

## Store Configuration

The application uses a pluggable authorization-code store for OAuth2 PKCE flows. By default the service uses an in-memory store which preserves original behaviour. You can switch to a Redis-backed store by configuring environment variables or using the application `Settings`.

Environment variables / settings:

- `AUTH_CODE_STORE`: `memory` (default) or `redis`.
- `REDIS_URL`: Redis connection URL (default: `redis://localhost:6379/0`).

How to enable Redis store (example):

```powershell
$env:AUTH_CODE_STORE = "redis"
$env:REDIS_URL = "redis://localhost:6379/0"
typer cli.py run
```

Notes:

- If `AUTH_CODE_STORE=redis` is set but the Redis client cannot be initialized (missing dependency or connection issues), the app falls back to the in-memory store and prints a warning to stderr to preserve backward compatibility.
- The store selection is now part of `app.core.config.Settings` (`AUTH_CODE_STORE` and `REDIS_URL`) so you can centralize this configuration in your environment or in a `.env` file.


## Mail Service Refactoring Guide

### Overview

The mail service has been refactored to follow **SOLID principles** and enable **easy integration of multiple email providers**. This architecture uses the **Strategy Pattern** and **Protocol-based dependency injection** to allow developers to swap email providers without modifying application logic.

### Architecture

#### 1. **EmailProvider Protocol** (`mail_component.py`)

The `EmailProvider` protocol defines the interface that all email providers must implement:

```python
class EmailProvider(Protocol):
    """Protocol defining the interface for email providers."""
    
    def send_email(self, to_email: str, subject: str, html_content: str) -> None:
        """Send a single email."""
        ...
    
    def send_bulk_email(
        self, recipients: list[str], subject: str, html_content: str
    ) -> None:
        """Send bulk email to multiple recipients."""
        ...
```

**Benefits:**
- Any service can implement this protocol.
- No tight coupling to specific implementations.
- Easy testing with mock providers.

#### 2. **Concrete Implementations**

##### `SMTPEmailProvider` (Default)
Sends emails via standard SMTP servers (Gmail, Office 365, Sendmail, etc.).

```python
from app.components.mail import SMTPEmailProvider

provider = SMTPEmailProvider(mail_settings)
provider.send_email("user@example.com", "Hello", "<h1>Hello</h1>")
```

##### `SendGridEmailProvider` (Template for Third-Party Services)
Skeleton implementation for SendGrid. Developers can extend this for Mailgun, AWS SES, Twilio SendGrid, etc.

```python
from app.components.mail import SendGridEmailProvider

provider = SendGridEmailProvider(api_key="your-sendgrid-key")
provider.send_email("user@example.com", "Hello", "<h1>Hello</h1>")
```

#### 3. **MailManager** (`mail_manager.py`)

Orchestrates email sending by:
1. **Rendering templates** using Jinja2.
2. **Building email contexts** (URLs, tokens, etc.).
3. **Delegating to the provider** for actual sending.

```python
from app.components.mail import MailManager, SMTPEmailProvider

provider = SMTPEmailProvider(mail_settings)
manager = MailManager(provider)

# Send predefined emails
manager.send_reset_password_email("user@example.com", "token123")
manager.send_verification_email("user@example.com", "token456")

# Send custom emails
manager.send_custom_email(
    to_email="user@example.com",
    subject="Custom Email",
    template_name="my_custom_template.html",
    context={"user_name": "John", "order_id": "12345"}
)

# Send bulk emails
manager.send_bulk_email(
    recipients=["user1@example.com", "user2@example.com"],
    subject="Newsletter",
    template_name="newsletter.html",
    context={"month": "November"}
)
```

#### 4. **MailService** (`services/mail_service.py`)

A high-level service for application-wide email operations. It wraps `MailManager` with a default provider.

```python
from app.services.mail_service import MailService

mail_service = MailService()
mail_service.send_reset_password_email("user@example.com", "token123")
```

#### 5. **Rules** (`rules.py`)

Centralized management of email types, URL builders, and constants.

```python
from app.components.mail.rules import EmailType, EmailUrls

# URL builders
reset_url = EmailUrls.reset_password_url("token123")
verify_url = EmailUrls.verification_url("token456")

# Email types (for logging, analytics, etc.)
email_type = EmailType.RESET_PASSWORD
```

### How to Add a New Email Provider

#### Example: Adding AWS SES Support

1. **Create a new provider class** in `mail_component.py`:

```python
class AWSSESEmailProvider(EmailProvider):
    """AWS SES-based email provider."""
    
    def __init__(self, region: str = "us-east-1"):
        """Initialize with AWS region."""
        import boto3
        self.client = boto3.client("ses", region_name=region)
        self.from_email = "noreply@example.com"
    
    def send_email(self, to_email: str, subject: str, html_content: str) -> None:
        """Send email via AWS SES."""
        try:
            self.client.send_email(
                Source=self.from_email,
                Destination={"ToAddresses": [to_email]},
                Message={
                    "Subject": {"Data": subject},
                    "Body": {"Html": {"Data": html_content}},
                },
            )
        except Exception as e:
            raise Exception(f"Failed to send email via AWS SES: {e}") from e
    
    def send_bulk_email(
        self, recipients: list[str], subject: str, html_content: str
    ) -> None:
        """Send bulk email via AWS SES."""
        for to_email in recipients:
            self.send_email(to_email, subject, html_content)
```

2. **Export the provider** in `mail/__init__.py`:

```python
from app.components.mail.mail_component import AWSSESEmailProvider

__all__ = [
    "EmailProvider",
    "SMTPEmailProvider",
    "SendGridEmailProvider",
    "AWSSESEmailProvider",  # Add this
    "MailManager",
    "EmailType",
    "EmailUrls",
]
```

3. **Use it in your application**:

```python
from app.components.mail import MailManager, AWSSESEmailProvider

provider = AWSSESEmailProvider(region="eu-west-1")
manager = MailManager(provider)
manager.send_reset_password_email("user@example.com", "token123")
```

### Migration from Old Code

#### Before
```python
from app.services.mail_service import MailService

mail_service = MailService()
mail_service.send_reset_password_email("user@example.com", "token")
```

#### After (No changes needed!)
The `MailService` maintains the same interface, so existing code works without modification. Behind the scenes, it now uses the refactored architecture.

### Testing with Mock Providers

For unit tests, create a mock provider:

```python
from app.components.mail import EmailProvider

class MockEmailProvider(EmailProvider):
    """Mock provider for testing."""
    
    def __init__(self):
        self.sent_emails = []
    
    def send_email(self, to_email: str, subject: str, html_content: str) -> None:
        self.sent_emails.append({
            "to": to_email,
            "subject": subject,
            "html": html_content,
        })
    
    def send_bulk_email(
        self, recipients: list[str], subject: str, html_content: str
    ) -> None:
        for to_email in recipients:
            self.send_email(to_email, subject, html_content)

# Usage in tests
def test_password_reset():
    mock_provider = MockEmailProvider()
    manager = MailManager(mock_provider)
    
    manager.send_reset_password_email("user@example.com", "token123")
    
    assert len(mock_provider.sent_emails) == 1
    assert mock_provider.sent_emails[0]["to"] == "user@example.com"
    assert "token123" in mock_provider.sent_emails[0]["html"]
```

### Dependency Injection Pattern

For more advanced setups using FastAPI dependency injection:

```python
from fastapi import Depends
from app.components.mail import MailManager, SMTPEmailProvider

def get_mail_manager() -> MailManager:
    """Dependency to inject MailManager."""
    provider = SMTPEmailProvider(mail_settings)
    return MailManager(provider)

@router.post("/password-reset")
async def reset_password(
    email: str,
    token: str,
    mail_manager: MailManager = Depends(get_mail_manager)
):
    """Reset password endpoint using injected mail manager."""
    mail_manager.send_reset_password_email(email, token)
    return {"message": "Password reset email sent"}
```

### Summary

| Layer | Responsibility | Extensibility |
|-------|-----------------|----------------|
| **EmailProvider** | Send emails via specific service (SMTP, SendGrid, AWS SES) | Add new implementations |
| **MailManager** | Template rendering, context building, delegation | Configure providers, add templates |
| **MailService** | Application-level abstraction, default provider | Swap provider via config |
| **Rules** | Email types, URL builders, constants | Add new types or URL patterns |

## Enviroment variables
### Database configuration
DATA_BASE_USER
DATA_BASE_PASSWORD
DATA_BASE_HOST
DATA_BASE_PORT
DATA_BASE_NAME

### SECRETS 
ENCRYPTION_KEY

### STMP Settings
SMTP_SERVER=
SMTP_PORT=
SMTP_USERNAME
SMTP_PASSWORD

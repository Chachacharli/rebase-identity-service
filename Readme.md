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



"""
Agent Authentification — JWT, bcrypt, gestion des rôles et SSO.

Responsabilités :
- Implémenter l'authentification par email/mot de passe
- Générer et valider les tokens JWT (access + refresh)
- Hacher les mots de passe avec bcrypt (passlib)
- Implémenter les cookies httponly sécurisés
- Gérer les dépendances FastAPI : get_current_user, require_role
- Implémenter le rate limiting sur /auth/login (slowapi)
- Valider les rôles (admin, manager, member)

Flux d'authentification Phase 1 :
1. POST /auth/login — email + password → JWT tokens + cookies
2. GET /* — cookie access_token → get_current_user → User
3. POST /auth/refresh — refresh token → nouveau access token
4. POST /auth/logout — suppression des cookies
5. GET /auth/me — informations utilisateur courant

Gestion des rôles :
- admin : accès total (CRUD tout, désactivation membres, création équipes)
- manager : création projets, gestion membres (pas d'admin/manager)
- member : lecture projets, création tâches/logs, signalement

Phase 2 — Extensions SSO :
- GET /auth/sso/login — redirection Azure AD
- GET /auth/sso/callback — échange code OAuth2 MSAL
- Nécessite : msal, MSAL_CLIENT_ID, MSAL_CLIENT_SECRET, MSAL_TENANT_ID

Phase 3 — Extensions :
- Tokens de service pour les intégrations
- Audit log des connexions
"""

AGENT_NAME = "AuthAgent"
AGENT_VERSION = "1.0.0"
AGENT_PHASE = 1
AGENT_STATUS = "active"

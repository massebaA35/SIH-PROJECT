# NETRA Security Notes

This prototype uses synthetic data only. Configure secrets through environment variables. Uploads are limited to approved extensions and 10 MB. API inputs use Pydantic validation. The demo intentionally exposes a simple credential endpoint for presentation; production use requires persisted users, Argon2 or bcrypt password storage, JWT rotation, RBAC middleware, rate limiting, audit persistence, encrypted storage, and secure deployment configuration.

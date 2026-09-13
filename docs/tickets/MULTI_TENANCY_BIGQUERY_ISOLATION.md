# [TICKET-SEC-01] Multi-Tenant BigQuery Isolation & Schema Migration

**Priority:** P1 — Mandatory Blocker prior to onboarding Tenant #2  
**Status:** Deferred / Architecture Requirement  
**Date Logged:** 2026-09-13  
**Target Milestone:** Multi-Tenant Enterprise Release  

---

## 1. Context & Architectural Status

Voxora's PostgreSQL database implements multi-tenancy at the application layer:
- `tenants` table isolates organizational entities.
- `users` and `conversations` require foreign key linkage to `tenant_id`.

However, the Google Cloud BigQuery analytical data warehouse (`voxora_bigquery_sa`) was provisioned for single-tenant evaluation and **does not have a `tenant_id` column in any table**:
- `orders` (no `tenant_id`)
- `daily_kpis` (no `tenant_id`)
- `customers` (no `tenant_id`)
- `products` (no `tenant_id`)

### Temporary Implementation (Single-Tenant Deployment)
During the Issue 2 & Issue 6 stability hardening, all generated queries were confirmed to run against the single tenant's historical dataset (`Voxora Org`, `27b5ac4d-bde1-4773-bb8a-d7c870029996`). Non-existent `tenant_id` references were removed from `semantic_layer.py` prompt context and AST query rewriting to eliminate BigQuery `400 Unrecognized name: tenant_id` runtime crashes.

> [!WARNING]
> **CRITICAL SECURITY REQUIREMENT**:  
> Application-layer filtering is insufficient for multi-tenant data warehouses. True data isolation must be enforced at the BigQuery storage and AST levels before any second tenant or external customer organization is onboarded.

---

## 2. Required Implementation Steps Prior to Tenant Onboarding

### Step A: BigQuery Warehouse DDL Migration & Data Backfill
1. Run DDL statements on the BigQuery dataset:
   ```sql
   ALTER TABLE `gen-lang-client-0407459345.voxora_bigquery_sa.orders` ADD COLUMN IF NOT EXISTS tenant_id STRING;
   ALTER TABLE `gen-lang-client-0407459345.voxora_bigquery_sa.daily_kpis` ADD COLUMN IF NOT EXISTS tenant_id STRING;
   ALTER TABLE `gen-lang-client-0407459345.voxora_bigquery_sa.customers` ADD COLUMN IF NOT EXISTS tenant_id STRING;
   ALTER TABLE `gen-lang-client-0407459345.voxora_bigquery_sa.products` ADD COLUMN IF NOT EXISTS tenant_id STRING;
   ```
2. Backfill existing 6,681 orders and 733 daily KPIs with the default tenant UUID:
   ```sql
   UPDATE `gen-lang-client-0407459345.voxora_bigquery_sa.orders`
   SET tenant_id = '27b5ac4d-bde1-4773-bb8a-d7c870029996'
   WHERE tenant_id IS NULL;
   ```
3. Update real-time ingestion pipelines (`append_today_data.py`, event streams) to mandate `tenant_id` on all new rows.

### Step B: Semantic Layer Schema Restoration
In `voxora-backend/app/services/semantic_layer.py`:
1. Re-add `tenant_id: STRING (Tenant isolation key)` to `TABLE_DEFINITIONS`.
2. Add explicit prompt guideline: `All queries must filter by tenant_id = '<current_tenant>'`.

### Step C: AST-Level Hard Scoping Enforcement
In `voxora-backend/app/services/text_to_sql.py`:
1. In `_validate_and_enforce_ast(sql, tenant_id)`:
   - Require `tenant_id` argument to be non-null.
   - Enforce AST injection using SQLGlot:
     ```python
     if not tenant_id:
         raise SQLValidationError("Tenant context required for query execution.")
     parsed = parsed.where(f"tenant_id = '{tenant_id}'")
     ```
2. Alternatively or additively, configure BigQuery Row-Level Access Policies (RLS) on all analytical tables:
   ```sql
   CREATE OR REPLACE ROW ACCESS POLICY tenant_isolation_policy
   ON `gen-lang-client-0407459345.voxora_bigquery_sa.orders`
   GRANT TO ("serviceAccount:...")
   FILTER USING (tenant_id = SESSION_USER());
   ```

### Step D: Cross-Tenant Verification Test Suite
Automated regression tests to add in `tests/`:
- Create two distinct tenants (Tenant A and Tenant B) with disparate order sets.
- Execute identical business queries ("today's revenue", "top products") simultaneously under Tenant A and Tenant B credentials.
- Assert 0% data cross-contamination.

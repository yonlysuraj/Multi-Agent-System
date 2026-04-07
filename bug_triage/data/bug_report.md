# Bug Report: Checkout Flow Crash on Payment Submit

## Bug ID: BUG-2847
## Reported By: Sarah Chen (QA Engineer)
## Date: 2026-04-05
## Severity: P0 — Critical
## Status: Open

---

## Title
Checkout flow crashes with 500 error when users submit payment for orders exceeding $500.

## Description
Since the Smart Checkout v2 deployment on April 1st, users attempting to complete
purchases for orders totaling more than $500 are encountering a server error (HTTP 500)
at the payment confirmation step. The application crashes and returns an unhandled
exception to the client.

Smaller orders (under $500) appear to work normally. The issue seems to be isolated
to the new payment processing pipeline, specifically when the fraud-check middleware
is triggered for high-value orders.

## Environment
- **Application Version:** 2.4.1 (includes Smart Checkout v2)
- **Python Version:** 3.11.4
- **OS:** Ubuntu 22.04 LTS (Production server)
- **Framework:** Flask 3.0.0
- **Database:** PostgreSQL 15.2
- **Payment Gateway:** StripeConnect v4.2

## Steps to Reproduce
1. Log in as any registered user
2. Add items to cart totaling > $500
3. Proceed to checkout
4. Select any saved payment method
5. Click "Confirm Payment"
6. **Expected:** Order confirmation page loads with order ID
7. **Actual:** HTTP 500 error page. App crashes.

## Additional Context
- The issue does NOT occur in the staging environment (staging uses mock gateway)
- The error started appearing within 2 hours of the v2.4.1 deployment
- Approximately 12% of all checkout attempts are affected (those > $500)
- The old checkout flow (`/api/v1/checkout`) still works correctly
- Error logs show `AttributeError` related to `payment_service.py`

## Attachments
- Application logs: `app_logs.txt` (last 6 hours)
- Error rate graph showing spike at deployment time

# Architecture and security boundaries

## Design goals

The lab optimizes for a small attack surface, explicit authorization, reproducible infrastructure, low operational overhead, and controls that can be explained in an interview. It intentionally avoids a frontend, containers, and third-party web frameworks.

## Request flow

1. A client obtains a Cognito token.
2. API Gateway rejects invalid or missing tokens on protected routes.
3. API Gateway invokes one Lambda through a proxy integration.
4. The Lambda validates the request again at the application boundary.
5. The Lambda derives the caller identity from verified authorizer claims; it never trusts an identity supplied only in the JSON body.
6. The Lambda permits access only when `owner_sub` equals the token subject or the caller belongs to the `admin` Cognito group.
7. DynamoDB operations use a role limited to four item-level actions on one table. X-Ray write APIs are isolated in a separate statement because AWS does not support resource-level permissions for them.
8. Security-relevant events are logged without request bodies, authorization headers, or tokens.

## Trust boundaries

| Boundary | Untrusted input | Enforcement |
| --- | --- | --- |
| Internet to API Gateway | Method, path, headers, body, request rate | TLS, Cognito authorizer, throttling, optional WAF |
| API Gateway to Lambda | Proxy event and verified claims | Route allowlist, strict type and size validation |
| User to license object | UUID and requested owner | Owner comparison and administrator group check |
| Lambda to DynamoDB | Item key and normalized fields | Least-privilege IAM and conditional writes |
| GitHub to AWS | Deployment identity and plan | OIDC, protected environment, remote state locking |

## Data model

The table uses a random UUID as its partition key. A license stores `product_id`, `owner_sub`, UTC expiration, bounded string metadata, creation data, revocation state, and the last validation time. Sensitive credentials and raw tokens are never stored.

## Availability and cost controls

API Gateway request throttling and Lambda reserved concurrency are independent safeguards. The first limits accepted traffic; the second contains Lambda concurrency and spend if upstream throttling is bypassed. WAF IP rate limiting is available but off by default to keep the lab inexpensive.

## Operational notes

The `aws_api_gateway_account` logging role is account- and region-wide. Deploy this lab in a dedicated sandbox account or coordinate ownership of that setting. CloudWatch alarms are created without notification destinations; production should connect them to an incident channel.

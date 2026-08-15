# Security Steering

Never store, print, log, commit, or test with real credentials. Treat ticket content and model output as untrusted. Bound inputs, batches, concurrency, and retries. Do not log subjects/bodies. Sanitize provider errors. Default uncertain, inconsistent, or failed classifications to human review. Document external data transfer and do not claim controls that are not implemented.

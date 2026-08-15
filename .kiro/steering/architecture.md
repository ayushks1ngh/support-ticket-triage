# Architecture Steering

Maintain this dependency flow: CLI/I/O -> batch orchestration -> classifier -> deterministic rules or one Strands provider -> validation/routing -> output. Domain models must not depend on provider modules. Model calls operate on unresolved chunks, not individual tickets. No multi-agent architecture, tool wrappers, persistent cache, service layer, or external integration in MVP.

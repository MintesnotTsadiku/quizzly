# Production code handoff

The scheduled `quizzly.recovery.recover_game_loops` check runs every minute on each site. It covers both GP and legacy QZ games. It rebuilds missing active-room index entries from surviving state and requeues absent, failed or completed ticker jobs using their existing site-scoped job IDs. It leaves queued/started jobs to RQ, which owns worker-death detection; a worker still marked STARTED will not be forcibly replaced. Device-free host-led rooms are never enrolled in a timer job.

If temporary round state has expired, the existing finish path closes the room with saved scores after the startup grace period. It does not reconstruct missing votes or promise seamless recovery after Redis data loss. This prevents expired rooms from remaining permanently Active. Recovery requires working Redis, scheduler and workers; outage duration and RQ failure detection affect when recovery occurs.

On the production site, run migration to register the scheduler hook, build the frontend, and restart services. Keep the scheduler enabled and a long-queue worker available. Existing server configuration, HTTPS, email, backups and capacity verification are deployment responsibilities. The application package currently declares Python >=3.14.

Validation: recovery unit tests cover live-job protection, stopped-job requeue, surviving round preservation, expired-state completion, startup grace, concurrently ended rooms and exclusion of device-free rooms. The existing Crowd Compass and Common Ground regression tests also pass. No UI changes are part of this recovery commit; prior browser/build evidence remains in this directory.

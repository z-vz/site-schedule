# Changelog

## 1.0.0 (17 Oct 2026). Running live on Cloudflare
- Jobs with multiple site visits. Each visit is Booked, Tentative/quoted or Done, and each status is shaded differently.
- Notifications (◆) for deliveries, inspections and similar. Each one is Confirmed, Unconfirmed or Done, and can be dragged to a new date.
- Opens sorted by next visit. Hold a job name and drag it to set a manual order.
- One continuous timeline with Today and Go to date; narrow weekend columns.
- Day count for the next 4 weeks, Mon–Fri; "Coming up" strip for the next 14 days.
- Compact phone layout; the job column shrinks when you scroll right.
- Cloudflare Worker + D1 storage, optional PIN, syncs every 30 s, works offline from the last copy on each device.

## 2.0.0 (in development)
Done so far:
- **Pinch to zoom**: two fingers on a phone, or Ctrl/⌘ + scroll or a trackpad pinch on a computer (50–250%, remembered on each device).
- **Pick both dates at once**: a calendar where you tap the first day, then the last day, with a work-day count. It's used for visits in the job form and the visit editor. Enter after typing a new job's name opens it.
- **Archive instead of delete**: archived jobs are hidden from the chart and counts, and listed under "Archived (n)" with Restore. Deleting for good is a separate two-tap step from that list.
- Fix: month labels overlapped when the 1st fell on a weekend.

Still planned: multiple schedules (for example per employee) with a combined view and tickboxes, resizing visits on a phone, email notifications.

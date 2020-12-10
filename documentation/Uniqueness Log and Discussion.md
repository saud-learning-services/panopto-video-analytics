# Panopto Unique Viewer Edge Cases

> This document serves as a log and discussion about unique views in Panopto. Specifically aimed at the question, “how does Panopto determine a unique viewer”

## Marko’s Notes

In all my testing, whenever I was logged in, regardless of browser (Safari or Chrome) it logged me as the same **user id**.

This behaviour changed however when I turned on a VPN. Initially when I re-accessed the video while staying signed in, it continued to log me under the same user id. However once I logged out and signed in again (all while one VPN with US IP address) it began to log me under a **different** user id

Opening sessions in incognito windows have no correlation to the User ID when you’re signed in. Closing and reassessing a video via an incognito window logs you under a new user id.

I still have to do more testing on mobile the testing I did and data I collected turned out to be inconclusive

I’d like to do a bit more VPN testing as well because I still have questions

## Big Takeaways

- VPN’s have proven to have impact on how unique users are counted
- Incognito sessions have proven to have an impact on how unique users are counted
- The best way to ensure uniqueness is counted as accurately as possible is to ensure everyone accessing the video has a Panopto account and is logged in while viewing

# Outside user test

**Status: completed.** This record documents an actual non-team walkthrough;
automated browser testing was not used as a substitute.

After the public URL is verified, ask a person outside Team 08 to follow the
root README user guide without a developer operating the application for them.
Use a sheet-music PDF they have permission to upload.

| Record | Value |
| --- | --- |
| Tester identifier or optional name | Ben Lopez |
| Confirmation that tester is outside Team 08 | Yes |
| Date and time | November 14, 2026, 11:00 PM |
| Public HTTPS URL and deployed commit | `https://music-companion-513717.web.app` · `dd3f569` |
| Device/browser | MacBook |
| Task | Upload PDF; extract measures; view a measure; save a note; open practice review; mark practiced; return to the passage. |
| Completed without developer-only steps | Yes |
| Observed problems and tester feedback | The PDF music took a while to load. Once loaded, navigation was quick and the music context was easy to view. |
| Related fix or issue URL | Initial PDF loading was throttled by token allocation; the allocation was adjusted. |
| Retest result | The PDF loaded more quickly; no further issues were reported. |

Do not record sensitive personal details, credentials, or the tester's private
sheet music in this public repository. Screenshots require the tester's consent.

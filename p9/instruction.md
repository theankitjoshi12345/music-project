# P#9 — Development Setup and First Commit

**Course:** CMPS453-001-202720 — Intro to Software Methodology

**Due:** Monday, October 26, 2026, 11:55 PM

You've designed screens and validated them with real users. Now it's time to build.

## Goals

By the end of P#9, your team should have:

- Chosen a tech stack.
- Run the app successfully on every member's machine.
- Made at least one commit per team member.
- Established a Git workflow with zero merge conflicts.

> **Goal:** When you open your laptop, you can immediately start coding your feature.

## Part 1 — Design Revision (Team)

Before writing code, update your Figma screens based on P#8 user-testing feedback.

### Deliverable

Document three to five key changes in this table:

| Screen | Change Made | P#8 Evidence |
| --- | --- | --- |
| Home | Added a **Get Started** button | 3/4 users did not know where to begin |
|  |  |  |

## Part 2 — Technical Decisions (Team)

Make these decisions together. Every member needs to work with the chosen stack.

### Platform

| Decision | Options | Your Choice |
| --- | --- | --- |
| Platform | Mobile: Flutter or React Native<br>Web: React (Vite) or Next.js |  |

Your platform determines which supplement guide you will follow.

### Development tooling

| Decision | Options | Notes |
| --- | --- | --- |
| IDE + AI assistant | VS Code + Copilot | Desktop; works for all platforms |
|  | Cursor | Desktop; built-in AI |
|  | Codespaces + Copilot | Browser-based; web teams only |

- Mobile teams must use a desktop IDE; emulators do not run in Codespaces.
- Web teams may use Codespaces or a desktop IDE.
- Team members may use different tools if they prefer.

## Part 3 — Screen Ownership (Team)

Each person chooses one Figma screen to build first. That screen becomes their first commit.

### Why one screen per person?

- Everyone has a concrete task.
- Separate screens minimize merge conflicts.
- The work directly connects P7/P8 designs to code.
- AI can help build an entire screen.

### Ownership table

| Screen (from Figma) | Owner | Notes |
| --- | --- | --- |
| Splash/Home | Member A (Team Lead) | Built during skeleton setup |
| Search | Member B |  |
| Profile | Member C |  |
| Settings | Member D |  |

Every team member must claim one screen. This is the screen they build in Part 5.

## Part 4 — Repository and Development Setup

This sequence matters: the Team Lead goes first, then the rest of the team follows.

### Choose a platform guide

| If you are building… | Follow this guide |
| --- | --- |
| Mobile app with Flutter | P9 Mobile Supplement: Flutter & React Native |
| Mobile app with React Native | P9 Mobile Supplement: Flutter & React Native |
| Web app with React or Next.js | P9 Web Supplement: React & Next.js |
| Something else | P9 Other Platforms Supplement — approval required |

### Step 1 — Team Lead setup

Only the Team Lead performs this step. Everyone else waits until the repository is ready.

First, create a project in the course GitLab group if one does not already exist.

#### A. Create issues

Create one issue for each team's claimed screen:

- **Title:** `Add [ScreenName] screen`
- **Description:** `Build the [ScreenName] screen from our Figma design`
- **Assignee:** The team member who owns that screen

Examples:

- `Add Search screen` → Member B
- `Add Profile screen` → Member C
- `Add Settings screen` → Member D

#### B. Clone into your IDE

1. On the GitLab project page, select **Code** and copy the repository URL.
2. In VS Code or Cursor, open the Command Palette (`Ctrl+Shift+P`), choose **Git: Clone**, paste the URL, and select a folder.
3. Open the cloned project in your IDE.

#### C. Create and run the app

Ask your AI assistant:

> Create a new [Flutter/React Native/React] app in this folder.

Follow its instructions, then ask:

> How do I run this app?

Verify that the app runs.

#### D. Add the Figma splash screen

1. Take a screenshot of the splash/home screen in Figma.
2. Ask your AI assistant:

   > Add a splash screen that looks like this: [paste screenshot]

3. Run the app and verify that the Figma screen appears.

#### E. Create the README

Ask your AI assistant:

> Create a README.md for this project with: project name, one-line description, setup instructions (prerequisites, install, run commands), and a team section with placeholders for Members A-D.

Review and adjust the generated README as needed.

#### F. Push to `main`

1. Open **Source Control** in VS Code or Cursor.
2. Enter the commit message: `Initial app with splash screen and README`.
3. Commit, then sync or push.

#### G. Notify the team

Tell the team that the repository is ready and that they should check their GitLab notifications for their assigned issue.

### Step 2 — Everyone clones and runs the app

After the Team Lead notifies the team:

1. Find the repository through your GitLab notifications or the team's GitLab project.
2. Clone it:
   - **VS Code/Cursor:** Copy the URL from **Code**, then run **Git: Clone**.
   - **Codespaces (web teams only):** Select **Code** → **Codespaces** → **Create codespace**.
3. Ask your AI assistant how to install and run the app for the chosen stack.
4. Confirm that the Team Lead's splash screen appears.
5. Open a code file and confirm that your AI assistant responds.

**Screenshot #1:** Your running app with your IDE visible. Every team member must provide one.

## Part 5 — Each Member Adds Their Screen

Each member works on the issue assigned by the Team Lead.

> **Repository note:** The course page mixes GitHub and GitLab references. This project uses **GitLab** for issue tracking, branches, merge requests, and reviews.

### 1. Find your assigned issue

Open the project’s **Issues** page, find the issue assigned to you, and open it.

### 2. Create a branch

1. In the issue’s **Development** section, select **Create branch**.
2. Keep the suggested branch name (for example, `2-add-search-screen`).
3. Create the branch.
4. In VS Code, fetch the remote and switch to your branch using the branch selector.

### 3. Build your Figma screen

1. Take a screenshot of your assigned Figma screen.
2. Ask your AI assistant:

   > Add a new screen to this app called [YourScreen] that looks like this: [paste screenshot]

3. Add your name somewhere visible on the screen.
4. Run the app and verify that your screen appears.

### 4. Commit and push

1. Open **Source Control**.
2. Commit with: `Add [YourScreen] screen`.
3. Sync or push the branch.

### 5. Create, review, and merge a merge request

1. Create a merge request from your branch.
2. Include `Closes #X` in its description, replacing `X` with your issue number (for example, `Closes #2`).
3. Ask a teammate to review and approve it.
4. Merge after approval. The linked issue should close automatically.

### Why this workflow?

- Issues track work that needs to be done.
- Branches are linked to issues, making work easy to trace.
- Merge requests close linked issues automatically.
- This mirrors a professional team workflow.

**Screenshot #2:** At least one merged merge request that shows `Closes #X` and at least one approval.

## README Requirements

The Team Lead creates and maintains the README. It must include:

- Project name and one-sentence description.
- Team members and their screen ownership.
- Tech stack, including framework and AI tools.
- Setup instructions: prerequisites, install command, and run command.

Only the Team Lead should edit the README to avoid conflicts.

## Deliverables

1. **PDF report**
   - Part 1: Design-revision table based on P#8 feedback.
   - Part 2: Technical decisions (tech stack and development tooling).
   - Part 3: Screen-ownership table.
   - Part 4: Screenshot #1 from every team member.
   - Part 5: Screenshot #2 showing at least one reviewed, merged merge request.
2. **GitLab repository**
   - Link to the team's repository.
   - README with setup instructions.
   - Issues for every screen, assigned to team members.
   - At least one merged merge request per team member, closing their issue.
3. **Updated Figma link**
   - Include revised screens if changes were made after P#8.

## Evaluation Rubric

| Criterion | Weight | Excellent | Adequate | Weak |
| --- | ---: | --- | --- | --- |
| Technical Decisions | 20% | Clear choices with rationale; team agreed | Choices made but rationale is thin | No clear choices or team conflict |
| Screen Ownership | 15% | Clear assignments; every member owns one | Screens assigned but some overlap | No clear division of work |
| Dev Environment | 30% | All members run the app; screenshots prove it | Most members working; 1–2 struggling | Multiple members cannot run the app |
| Git Workflow | 20% | Issues assigned; merge requests linked to issues and reviewed | Merge requests exist but are unlinked or unreviewed | No issues or merge requests; commits directly to main |
| README & Docs | 15% | Complete, easy-to-follow README | README exists but is incomplete | No README or unusable instructions |

## Suggested Timeline

| Day | Who | Task |
| --- | --- | --- |
| Days 1–2 | Team | Design revision, technical decisions, and screen ownership |
| Day 3 | Team Lead | Create app skeleton and push setup |
| Days 3–5 | Everyone | Clone, install, run the app, and capture Screenshot #1 |
| Days 5–6 | Everyone | First commit, merge request, merge, and Screenshot #2 |
| Day 7 | Team Lead | Compile report and submit |

## Tips

- The Team Lead creates the project before others attempt to clone it.
- Each person should build only their claimed screen to minimize conflicts.
- Ask AI for help with Git, setup, and implementation when stuck.
- Keep the app simple. Showing your Figma screen in the app is success; advanced features come in P#10.

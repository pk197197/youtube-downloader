---
description: Process for releasing a new version of the YouTube Downloader
---

# Release Workflow

Follow these steps to release a new version (e.g., v1.1.3).

1.  **Update Version Number**
    *   Edit `YoutubeGUI.py` and change `CURRENT_VERSION` to the new version string.
    *   *Command*: `open YoutubeGUI.py` (or edit directly)

2.  **Generate Release Notes Artifact**
    *   Create a new markdown file named `release_v<VERSION>.md` (e.g., `release_v1.1.3.md`).
    *   **Format**:
        ```markdown
        # v<VERSION> Release Notes

        ## 🚀 [One-line Summary]

        [Brief intro]

        ### ✨ New Features
        - **Feature 1**: Description
        - **Feature 2**: Description

        ### 🛠 Bug Fixes
        - **Fix 1**: Description
        - **Fix 2**: Description

        ---
        ### 📦 Download
        - **macOS**: `YouTube极简下载器_macOS.dmg`
        ```
    *   Review pending tasks in `task.md` to populate the notes.

3.  **Update Task Tracker**
    *   Move completed tasks in `task.md` to a "Completed" section.
    *   Create a new section for the *next* version.

4.  **Build Application & Installer**
    *   Run the build scripts to generate the `.app` and `.dmg`.
    *   *Command*:
        ```bash
        python3 build_app.py && python3 build_dmg.py
        ```
    // turbo

5.  **Git Commit & Tag**
    *   Commit the code changes and the new release notes.
    *   Tag the commit with the version number.
    *   Push to GitHub.
    *   *Command* (replace `vX.X.X` with actual version):
        ```bash
        git add .
        git commit -m "Release vX.X.X"
        git tag -f vX.X.X
        git push origin main
        git push origin -f vX.X.X
        ```

6.  **GitHub Release**
    *   Upload the `release_v<VERSION>.md` content as the description.
    *   Upload `dist/YouTube极简下载器_macOS.dmg` as the asset.

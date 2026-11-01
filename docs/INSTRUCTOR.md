# Instructor setup and integration guide

## Before class

- This folder is your master v0.1. Keep it separate from student copies.
- Run the game on every student's actual computer before the lesson. Use Python 3.13 and the pinned requirements. Mouse plus keyboard is easier than a trackpad for this project.
- Distribute the supplied v0.1 ZIP through your normal class file-sharing method. It contains code and guides, not installed dependencies or private data.
- Give each student/pair one card. Begin with World, Materials, Interface, and Quest. Combine roles for a small class. Save-system work is a later task.
- Browser Claude sessions do not automatically share context. Students need current source files, the same rules, and their own task assignment. No API key is required for this game.

## First 60-minute build period

- 0-10: run the baseline and practice the controls.
- 10-15: read the shared rules and assign one card per pair.
- 15-40: build one small change with Claude; ask each student to explain a line.
- 40-55: groups demonstrate; collect changed files and handoff notes; integrate what is ready.
- 55-60: play the combined version and name the next tasks. Do not rush a broken feature into the release.

## Combine work without overwriting it

1. Keep a backup ZIP of the current working master (exclude .venv and saves).
2. Read the group's handoff and compare its files with the starting version. Confirm only assigned files changed.
3. Copy one group's changes into the master. If two groups edited the same file, manually reconcile their small changes; do not overwrite one with the other.
4. Run the unit tests and the manual checklist. Start a fresh world as well as checking a saved world. The tests assume the initial crystal IDs remain stable.
5. Integrate the next group only after the master works again. Watch terrain/quest overlap and labels after adding materials.
6. Record the combined changes in CHANGELOG.md. Make a new release ZIP named v0.2 and give it to everyone next class. Keep unfinished contributions separately for comparison with the new master.

A local Git repository is initialized for the master. Review `git diff` before committing each accepted contribution. You can introduce student branches later; this kit does not require student GitHub accounts. Nothing has been uploaded to GitHub or publicly shared.

## Suggested milestones

1. Baseline and first team contributions.
2. Hills, trees, extra materials, and improved selection feedback.
3. One shared goal: build a shelter and collect crystals.
4. Save/load robustness and help screen.
5. Playtesting and bug fixes.
6. A small finished release and student demonstrations.

Keep the small world for this release. Large voxel worlds and network multiplayer need different architecture. Teach relevant variables, loops, functions, and dictionaries in the Python half of class; the engine setup is instructor-provided scaffolding.

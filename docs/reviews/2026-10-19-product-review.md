# Reshoot product and implementation review

Review date: 2026-10-19  
Reviewed revision: `1c9b029`  
Status: Findings and recommendations for this revision. The proposed changes have not been implemented.

Reshoot's best opportunity is keeping software demos current. It can already record, edit, and rebuild a demo from files in a repository. The next challenge is making updates reliable and easy to review.

My suggested description:

> Create a software demo with Claude or Codex, then rebuild it when the app changes.

Three things need work first: privacy checks can report success after failing, updates still require considerable manual work, and the skills spend more time on recording than on deciding what the video should explain.

I reviewed the code, all seven skills, examples, documentation, workflows, and selected frames from the existing video, then tested failure cases using made-up data. **26 fast tests passed, one skipped; all eight browser tests passed.** Claude plugin validation passed with one warning.

The implementation is unchanged. The visual review covered selected frames, not a complete playback with sound. The comparisons below come from vendor documentation and announcements; I did not test those products.

**The repeatable recording process is the strongest part of the product.**

- **Storyboards and edit instructions live with the code.** A UI change can make a recording obsolete. Keeping the instructions in the repository makes it possible to update and rebuild the demo.
- **Named beats connect the work.** Each beat links an action to its caption, narration, timing, and cut. The same structure could hold expected results and review comments.
- **The tool covers the full recording process.** Browser and terminal capture, editing, narration, subtitles, review sheets, and CI already work together.
- **The code handles several recording problems well.** It waits for narration to finish, holds the final frame, handles colour range, records extra detail for zoom, and draws captions after zooming.
- **Capture stays within the app.** Fresh browser profiles, made-up data, and page or window capture reduce the chance of showing private information.
- **The skills give specific advice.** They explain failures the author encountered and how to avoid them.
- **The project records its own example.** The notes app and CI workflow give someone a working example to try.

The small codebase is easy to follow and worth keeping manageable as features are added.

**Several alternatives already offer the recording features.**

| Alternative | What overlaps |
|---|---|
| Screen Studio | Automatic zoom, cursor effects, and polished screen recordings. [Product page](https://screen.studio/) |
| Microsoft Playwright CLI | Browser video recording with animated cursors, chapters, and action annotations. [Recording documentation](https://github.com/microsoft/playwright-cli/blob/main/skills/playwright-cli/references/video-recording.md) |
| Remotion | Videos made through code, with skills for Claude, Codex, and other agents. [Agent skills](https://www.remotion.dev/docs/ai/skills) |
| Arcade | Branded demo generation and an announced agent that records changed product flows again for human review. The announcement includes a waitlist; I have not confirmed general availability or performance. [Changelog](https://www.arcade.software/changelog) |

Zoom, AI narration, skills, and automatic refresh will not distinguish reshoot on their own. The better opportunity is to make local browser and terminal demos easy to maintain in a repository, with release automation and a clear record of what changed and what was checked.

**False success reports need fixing before more capture formats are added.**

I reproduced the first five findings with made-up inputs and found the last one by reading the code.

| Priority | Finding | What I found |
|---|---|---|
| Critical | **The app stops before image review.** | The `finally` block in [run.py](../../src/reshoot/run.py) stops the server before invoking `check`. A local image fetch failed with connection refused. The tool then said “every image … has been checked” and reported `ok: true`. |
| Critical | **A check can crash while the run reports success.** | [run.py](../../src/reshoot/run.py) does not reject check failures. A missing asset manifest caused a traceback, but the final report contained `ok: true` and `unchecked: 0`. |
| Critical | **Skipped inputs can be reported as checked.** | [check.py](../../src/reshoot/check.py) skips missing files, failed URL fetches, and unreadable images. If nothing remains, it reports everything checked. I reproduced this with a nonexistent image and an invalid PNG. |
| High | **The check does not cover every frame.** | `items()` in [check.py](../../src/reshoot/check.py) samples video every three seconds by default. It missed a 0.2-second flash I put in a test video. This does not support claims about checking every frame or everything a take can show. |
| High | **The email rule excludes too many addresses.** | `SAFE_EMAIL` in [scan.py](../../src/reshoot/scan.py) excludes addresses beginning with `user@`, `name@`, and similar prefixes on any domain. The scan did not flag `user@realcompany.com`. |
| High | **Logs can expose URLs and filenames.** | [check.py](../../src/reshoot/check.py) prints the source unchanged. A signed token in a URL or private information in a filename can enter the log, even when the detected text is masked. |

The report needs to show:

- Whether recording completed.
- Whether the expected results appeared.
- Whether the scan completed, and what it covered.
- Which inputs could not be fetched or read.
- Whether a person has reviewed the result.

A failed check must stay unresolved in the report, even if recording finished successfully.

Saving image and media files during capture would also make review more reliable. Fetching their URLs later can return different content, require a login, or fail after the server stops. The reviewer needs the files used in that recording.

Contact sheets help people find problems, but they reduce image size. A 1920×1080 frame shown in a 1000-pixel-wide tile is harder to inspect. Reviewers should be able to open the original frame and jump to its time in the video.

**The browser can record actions that do not behave like a person's actions.**

The overlay clicks and types by sending JavaScript events and setting field values. It does not send browser-native input or check whether an element is visible and reachable. See `press()` and `typeNow()` in [overlay.js](../../src/reshoot/overlay.js).

Some application controls may not respond correctly. A script may also activate an element a person could not click, such as a button covered by another element. The recording can look successful even when it does not show a valid user interaction.

Playwright is worth testing as the browser driver, while keeping reshoot's beats, cursor, zoom, narration, editing, and review. The decision should follow tests with made-up examples covering React forms, dialogs, uploads, drag and drop, nested scrolling, iframes, and shadow DOM.

I found four more issues by reading the code:

- **Page errors do not necessarily fail the recording.** The end of `main()` in [web.py](../../src/reshoot/web.py) prints frontend exceptions.
- **Old narration can remain after a new recording.** When a storyboard no longer has `VOICE`, `main()` in [web.py](../../src/reshoot/web.py) leaves the old `.voice.json` file. The editor's `lines()` function in [cut.py](../../src/reshoot/cut.py) still reads it.
- **Browser commands can wait indefinitely.** `Page.cmd()` in [web.py](../../src/reshoot/web.py) has no general timeout for a missing response.
- **Recording inputs are not fixed.** Cursor movement and typing use randomness. The recording also depends on application data, browser versions, fonts, and external responses that reshoot does not currently record or control as a set.

Each run needs an identifier linking its storyboard, app revision, demo data, media, and metadata. Removing metadata left over from previous runs would prevent old narration from entering a new video. Recording these details would also make failures easier to investigate.

**The planning skill needs to help choose a story.**

The [planning skill](../../skills/plan-demo/SKILL.md) asks where the video will appear, how long it should be, and which three to six things it should show. It then moves quickly to recording methods and beats.

It should first establish what the viewer needs to understand:

1. **Audience:** Who is watching?
2. **Problem:** What difficulty do they recognize?
3. **Promise:** What will the product help them do?
4. **Proof:** What result can the video show?
5. **Value:** Why does that result matter?
6. **Next action:** What should the viewer do after watching?

A list of features can become a tour of buttons. Showing one useful task through to a result gives the viewer a clearer reason to care.

Each important beat should say what result is expected:

> Search for a note → the matching note appears → the viewer can read the result.

Checking that result before reporting success would give reshoot a useful role beyond recording clicks: it could verify that the demo showed what it promised.

**The notes app works as a test example, but the main demo needs a better story.**

The notes example is safe and easy to understand. Its add-and-search flow does not explain why someone needs reshoot.

The terminal footage also needs a correction. It says “Or from the terminal,” but the [tape](../../examples/notes/terminal.tape) uses `echo` and `cat` on a separate text file. It does not interact with the notes app. Connecting it to the same application state, or labelling it as a separate recording example, would avoid implying a feature the app does not have.

The main demo could show reshoot updating a recording:

> Create a demo → change the app → find the affected beat → rebuild → compare the result.

**Portrait videos need to be readable on a phone.**

`vertical()` in [cut.py](../../src/reshoot/cut.py) places the landscape video across a portrait background. A 16:9 video becomes roughly 1080×608 inside a 1080×1920 frame. Most of the frame shows the background, and desktop text becomes small on a phone.

The existing [phone storyboard](../../examples/notes/phone.py) offers a better starting point. Depending on the app, a portrait video could use its phone layout, crop to the relevant area, or arrange the footage and captions differently.

The defaults for brand styling, caption position, wrapping, and reading time also need work. For example, `caption_image()` in [zoom.py](../../src/reshoot/zoom.py) does not wrap captions as the browser version does.

**Claude and Codex can share the skills, but each installation needs testing.**

Both support the existing `SKILL.md` format. Codex loads repository skills from `.agents/skills`; Claude supports `.claude/skills` and skills bundled in plugins. [OpenAI documentation](https://learn.chatgpt.com/docs/build-skills), [Claude documentation](https://code.claude.com/docs/en/skills).

| Area | What I found |
|---|---|
| Installation | The README explains Claude installation. It has no equivalent instructions for Codex. |
| File paths | Several skills use `../../examples` and `../../guide`. These work in the complete plugin, but break if someone copies individual skills into another harness's skill folder. |
| Names | Names such as `record-web` and `cut-video` can conflict with other installed skills. |
| Setup checks | There is no consistent check for tools, permissions, and available capture methods before work starts. |
| Tests | The tests cover Python and browser behaviour. They do not show whether Claude and Codex can discover the skills and complete the work. |
| Plugin instructions | Validation warns that the root `CLAUDE.md` is not loaded as project context. Instructions the plugin needs must be included in its skills. |

Keep one source for the skills, with installation files for each harness. The work includes:

- Names such as `reshoot-demo` and `reshoot-refresh` to avoid conflicts.
- Bundled examples and templates, or a CLI command that supplies them.
- Environment checks before recording starts.
- Tests for discovery, creation, refresh, and failure recovery in both harnesses.
- Checks that both leave publishing to the owner unless the owner has authorized it.

OpenAI documents a way to convert a Claude skills-only plugin for its plugin directory. This provides another distribution option, though the installed package still needs testing with the required local tools. [Conversion documentation](https://developers.openai.com/plugins/guides/submit-claude-plugin)

One instruction in [keep-current](../../skills/keep-current/SKILL.md) is incorrect: “Creating or pushing a workflow file is pushing.” Creating a local file and pushing it are different actions. The wording makes the agent ask for permission before local work it may already be authorized to do.

Supporting more harnesses lets more agent users try reshoot. Making it easier to use also requires fewer tools to install, fewer files to create by hand, and fewer recording decisions for the user.

**Updating and reviewing a demo should be the main product feature.**

Someone should be able to ask:

> Refresh the search demo for this release.

Reshoot would then:

1. Load the story, demo data, and expected results.
2. Record the chosen app revision.
3. Find failed or visibly changed beats.
4. Show the previous and current versions side by side at the same beat.
5. Suggest a repair where needed.
6. Produce the new files and show what still needs review.

A repair has to preserve what the demo is meant to show. If “Search” disappears, clicking another button just to finish the recording is not a repair.

A small local review page could bring that work together. It could play the video, jump to beats and flagged times, open original frames, compare versions, and record decisions for each beat. Reviewers currently have to work across JPEG sheets, JSON files, CLI labels, and a separate video player.

**The roadmap should put reliability and updates ahead of new capture formats.**

| Order | Work | Reason |
|---|---|---|
| 1 | Fix check failures and coverage claims | Users need to trust the report. |
| 2 | Add `doctor`, project setup, and a fast preview | Help someone get a useful first result with less setup. |
| 3 | Ship and test Claude and Codex installation | Make both harnesses usable. |
| 4 | Add expected results and improve the planning skill | Help the agent make a clear demo and check what it shows. |
| 5 | Add beat comparisons and help with updates | Reduce the work of keeping demos current. |
| 6 | Improve portrait composition and reusable styles | Make the outputs readable where people will watch them. |
| 7 | Add simulators and more desktop platforms | Expand capture support after recording and review are reliable. |

Mobile simulator capture comes later in this order because it adds more platforms to support before recording, checking, and updating are reliable.

Automatic trimming also needs care. A still frame may give the viewer time to read a result, so the purpose of the beat, narration length, and reading time should determine what gets shortened.

The useful measures are time to the first acceptable demo, time to update it after a UI change, manual fixes per update, review time, and successful runs in each supported environment and harness. Testing with several projects outside this repository would show how much work reshoot actually saves.

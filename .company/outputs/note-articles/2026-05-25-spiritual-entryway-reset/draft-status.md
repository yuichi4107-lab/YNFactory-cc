# Draft Status

- Status: blocked_before_note_draft
- Note draft URL: pending
- Blocker: `OPENAI_API_KEY` is not set in the current shell, and no OpenAI API key reference was found in `~/.zshrc`, `~/.zprofile`, `~/.bash_profile`, `~/.bashrc`, or `~/.config/openai/env`.
- Impact: the four required note images could not be generated, so the note editor draft was not created to avoid saving an incomplete article without the required top image and three inline images.
- Next action: set `OPENAI_API_KEY`, generate `images/top.png`, `images/inside-01.png`, `images/inside-02.png`, and `images/inside-03.png` from the saved prompt files, then open the `note-spiritual` browser profile and save the article as a note draft without publishing.

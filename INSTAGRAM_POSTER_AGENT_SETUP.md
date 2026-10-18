# Instagram Science Poster Agent

This is a deterministic poster-building and Instagram publishing pipeline. It logically composes an educational science infographic from structured text and equation fields, draws a microstate diagram with vector graphics, typesets formulas, checks key claims and image dimensions, writes a caption, and optionally publishes the poster through the Instagram Graph API. It does not use text-to-image or illustrative AI art.

## One-click run (maximum 10 minutes)

Open the GitHub Actions workflow named Instagram Science Poster Agent, click Run workflow, leave publish_now set to true, and start the run. The workflow has timeout-minutes set to 10. There is no intermediate poster approval step; a run with publish_now=true is authorized to create a public Instagram post immediately. The account preflight validates both secrets and the exact destination username before the build is uploaded; a mismatch or missing credential stops the run.

Workflow file: .github/workflows/instagram-science-poster-agent.yml

## One-time credentials

In repository Settings → Secrets and variables → Actions → Secrets, create:

- IG_USER_ID — numeric Instagram professional-account ID for **@wowscifi**. The agent checks the resolved username before it creates a media container and stops if it is not exactly `wowscifi`.
- META_ACCESS_TOKEN — valid publishing token for that account.

The implementation is pinned to **@wowscifi** and verifies the API-resolved username before every publish attempt. It uses the Graph API Facebook Login route. The target Instagram account must be Professional (Business or Creator) and linked to a Facebook Page; the app/token must have the required publishing permissions, commonly instagram_basic, instagram_content_publish, pages_show_list, and pages_read_engagement. Permissions vary by the app's setup and review state.

Optionally set the repository variable META_GRAPH_API_VERSION to a Graph API version supported by your app. If absent, this workflow uses v26.0 as its default; change it when needed.

Never store tokens in code, content files, commit messages, captions, or logs.

## How the agent composes the poster

- Content plan: content/arrow_of_time.json holds the thesis, labels, equations, scientific caveats, and Instagram caption.
- Composition: src/instagram_science_poster_agent.py creates a 1080×1350 JPEG poster from text, vector cards, arrows, and deterministic dot-state diagrams.
- Quality gate: the script checks required fields, the Second Law formula, Boltzmann's equation, presence of the low-entropy initial condition and time-reversal caveat, image dimensions and file size.
- Publishing: the workflow commits the JPEG to this public repository so Meta can fetch a direct HTTPS raw image URL, creates an Instagram media container, waits for processing, publishes it, then checks for a post permalink.
- Result: the run uploads a poster, caption, and publication receipt as a GitHub Actions artifact.

## Test without publishing

Run locally:

    python -m pip install Pillow requests
    python src/instagram_science_poster_agent.py

This renders docs/generated/arrow_of_time.jpg and artifacts/instagram_caption.txt only. The local test does not publish. To publish through the workflow, add the secrets and use the one-click GitHub Actions run.

## Important constraints

The repository must remain publicly readable for the raw GitHub JPEG media URL, and GitHub Actions must have permission to write the generated PNG to the selected branch. Branch protections can block this commit. The workflow's 10-minute timeout is a cap, not a guarantee that Meta or GitHub services will always finish before the deadline. The agent does not claim success unless Meta returns a media ID and the verification call succeeds. Scientific edits should be reviewed for accuracy even though the poster can be published without a separate approval step.

## Fixed destination safety

Every post created by this workflow is intended for **https://www.instagram.com/wowscifi/**. Before creating the Instagram media container, the publisher calls the Graph API for the configured `IG_USER_ID` and compares the returned username with `wowscifi`. Any mismatch or inability to verify the target fails closed; the workflow must not publish to another account. The rendered asset is JPEG because the Instagram image publishing flow expects a supported JPEG image URL.

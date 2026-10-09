# NEON NEXUS: ARCADE OVERDRIVE

A neon cyber-arcade brick-breaker built with Python and Pygame.

## Features
- Neon arena, animated starfield, glowing bricks and ball trails
- Progressive levels with different brick layouts and tougher bricks
- Score, persistent best score, lives, combos and bonus scoring
- Multiball, wide paddle, laser paddle, slow motion, shield, sticky catch and extra-life power-ups
- Particle bursts, floating score text and screen feedback
- Keyboard, mouse and touch input
- Pause, restart, sound toggle and fullscreen toggle
- GitHub Actions workflow to build a standalone Windows `.exe`

## Run locally
```bash
python -m pip install pygame
python neon_nexus_arcade.py
```

## Build on GitHub from mobile
1. Create a GitHub repository.
2. Upload `neon_nexus_arcade.py` to the repository root.
3. Create the path `.github/workflows/build.yml` and paste the workflow file contents.
4. Commit the files to `main` (or `master`).
5. Open the repository's **Actions** tab. If needed, select **Build Neon Nexus Arcade** and tap **Run workflow**.
6. When the run finishes successfully, open that run and download the `Neon-Nexus-Arcade-Windows` artifact.

The workflow creates a Windows executable. It does not create an Android APK; Android packaging requires a separate build setup.

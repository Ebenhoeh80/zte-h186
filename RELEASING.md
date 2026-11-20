# Releasing ZTE H186 DSL Modem

How a release is made, step by step, so it does not depend on anyone's memory. Versions follow
[Semantic Versioning](https://semver.org/): a breaking change raises the major version, a new
feature the minor version, a fix the patch version.

## 1. Prepare

1. Check that everything meant for the release is merged to `main` and CI is green.
2. In `CHANGELOG.md`, rename `[Unreleased]` to `[x.y.z] - YYYY-MM-DD` and start a new empty
   `[Unreleased]` section above it. The section's text becomes the release notes.
3. Set the new version in `custom_components/zte_h186/manifest.json`, `package.json` and the first two `version` lines of `package-lock.json`.

## 2. Check locally

```bash
python -m ruff check .
python -m ruff format --check .
python -m unittest discover -s tests -v
```

## 3. Pull request

Open a pull request with the changelog and version change, wait for the CI checks
(`Python Tests`, `Ruff (lint + format)`, `Hassfest Validation`, `HACS Validation` and `Node (lint + test + build)`) and squash-merge it.

## 4. Tag

Create the tag on the merge commit of `main` and push it:

```bash
git checkout main && git pull
git tag vX.Y.Z
git push origin vX.Y.Z
```

The tag **must** be `v` plus the version in `manifest.json`. A suffix such as `-rc.1` makes it a
pre-release (set the same suffix in the manifest version).

## 5. What the workflow does

The tag starts `.github/workflows/release-zip.yml`, which calls the shared workflow in
[`Ebenhoeh80/.github`](https://github.com/Ebenhoeh80/.github). It checks that the tag matches the
manifest version, builds `zte_h186.zip` (integration files at the zip root, as HACS expects with
`zip_release`), and creates or updates the GitHub release with the matching changelog section and
the zip attached. If the tag and the version differ, the workflow fails and nothing is published.

## 6. Verify the release

- The release page shows the changelog text and the `zte_h186.zip` asset.
- HACS offers the new version (use *Update information* on the repository if it is slow).

## 7. Update and check a live system

Take a Home Assistant backup first. Then update through HACS, restart Home Assistant, and check that
the integration is loaded, the sensors update, and the log shows no new warnings for `zte_h186`.

## 8. After the release

- If the repository is in the HACS default catalog and a review asked for the change, answer in the
  pull request there.
- Ask yourself whether the README, the translations and the roadmap section still match.

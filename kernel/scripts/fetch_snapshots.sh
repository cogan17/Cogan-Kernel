#!/usr/bin/env bash
# Download this run's snapshots-<run number> artifact into ./snapshots, retrying while GitHub has not
# indexed it yet. Builder run 71 (22 Nov 2026): the resolve job uploaded snapshots-71 at 03:50:23 UTC,
# 8 jobs that started 4-9 seconds later got "Artifact not found" from actions/download-artifact, which
# cannot retry, while jobs that started a few seconds later downloaded the same artifact. Needs GH_TOKEN
# with actions: read. Waits up to TRIES x WAIT seconds (default 12 x 10 s), then fails the step.
set -uo pipefail
name="snapshots-${GITHUB_RUN_NUMBER:?}"
tries="${SNAPSHOT_TRIES:-12}"
wait="${SNAPSHOT_WAIT:-10}"
for ((i = 1; i <= tries; i++)); do
  rm -rf snapshots
  if gh run download "${GITHUB_RUN_ID:?}" --repo "${GITHUB_REPOSITORY:?}" --name "$name" --dir snapshots; then
    ls snapshots
    exit 0
  fi
  echo "$name belum terlihat / not visible yet ($i/$tries); coba lagi $wait detik / retry in $wait s"
  sleep "$wait"
done
echo "::error::$name tidak bisa diunduh setelah $tries kali / could not be downloaded after $tries tries"
exit 1

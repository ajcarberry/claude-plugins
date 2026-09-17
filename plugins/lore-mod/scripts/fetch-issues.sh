#!/usr/bin/env bash
# Snapshot every open issue (not PRs), oldest first, with comments, to <work dir>/data/<date>/issues.jsonl
# Usage: fetch-issues.sh <owner/repo> <work dir> [YYYY-MM-DD]
set -euo pipefail
REPO="$1"; WORK="$2"; DAY="${3:-$(date +%F)}"
OUT="$WORK/data/$DAY"; mkdir -p "$OUT"; : > "$OUT/issues.jsonl"
page=1
while :; do
  chunk=$(gh api "repos/$REPO/issues?state=open&sort=created&direction=asc&per_page=100&page=$page" --jq '[.[] | select(.pull_request == null)]')
  [ "$(echo "$chunk" | jq length)" -eq 0 ] && break
  echo "$chunk" | jq -c '.[] | {number, title, state, created_at, updated_at, user: .user.login, author_association, labels: [.labels[].name], comments, assignees: [.assignees[].login], reactions: .reactions.total_count, body}' >> "$OUT/issues.jsonl"
  page=$((page+1))
done
tmp="$OUT/issues.tmp"; : > "$tmp"
while IFS= read -r line; do
  num=$(echo "$line" | jq -r .number); c=$(echo "$line" | jq -r .comments)
  if [ "$c" -gt 0 ]; then cm=$(gh api "repos/$REPO/issues/$num/comments?per_page=100" --jq '[.[] | {user: .user.login, author_association, created_at, body}]'); else cm='[]'; fi
  echo "$line" | jq -c --argjson cm "$cm" '. + {comment_list: $cm}' >> "$tmp"
done < "$OUT/issues.jsonl"
mv "$tmp" "$OUT/issues.jsonl"
jq -r '"\(.number)\t\(.created_at[:10])\t\(.user)\tc=\(.comments)\t[\(.labels|join(","))]\t\(.title)"' "$OUT/issues.jsonl" > "$OUT/index.tsv"
echo "$(wc -l < "$OUT/issues.jsonl") open issues -> $OUT/issues.jsonl"

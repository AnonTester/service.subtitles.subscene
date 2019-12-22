#!/bin/bash

set -euo pipefail

if [[ $(git status --porcelain | wc -c) -ne 0 ]]; then
  echo "Cannot release - uncommitted changes found!"
  exit 1
fi

read -rp "Enter new version number: " VERSION
git push

RELEASES_URL="https://api.github.com/repos/jarmo/service.subtitles.subscene/releases"
FILES=`git ls-files | grep -v ".gitignore" | grep -v "release.sh" | sed 's/^/service.subtitles.subscene\//' | xargs`
ZIP_NAME="`basename $(pwd)`-$VERSION.zip"

pushd .. > /dev/null
zip -q $ZIP_NAME $FILES
popd > /dev/null

mkdir -p releases
mv ../$ZIP_NAME releases/$ZIP_NAME
echo "Releasing: `ls releases/$ZIP_NAME`"

read -rp "Enter changelog to release version $VERSION: " CHANGELOG
RESPONSE=`http -b POST $RELEASES_URL Authorization:"token $GITHUB_RELEASE_TOKEN" tag_name="$VERSION" draft:=true name="service.subtitles.subscene $VERSION" body="$CHANGELOG"`

RELEASE_ID=`echo $RESPONSE | jq -r .id`
RESPONSE=`http -b POST "https://uploads.github.com/repos/jarmo/service.subtitles.subscene/releases/$RELEASE_ID/assets?name=$ZIP_NAME" Authorization:"token $GITHUB_RELEASE_TOKEN" @releases/$ZIP_NAME`
RESPONSE=`http -b PATCH "$RELEASES_URL/$RELEASE_ID" Authorization:"token $GITHUB_RELEASE_TOKEN" draft:=false`

echo "Release done:"
echo $RESPONSE | jq -r .html_url

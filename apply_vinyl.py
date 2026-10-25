#!/usr/bin/env python3
"""Idempotently patch upstream InterTune's artwork thumbnail. Fail closed on changed upstream code."""
from pathlib import Path
import argparse
import re
import shutil
import sys

REL = Path('app/src/main/java/com/dd3boh/outertune/ui/player')

def exactly_once(text: str, pattern: str, replacement, what: str) -> str:
    out, n = re.subn(pattern, replacement, text, count=0, flags=re.MULTILINE | re.DOTALL)
    if n != 1:
        raise RuntimeError(f'{what}: expected one matching location in InterTune, got {n}; upstream may have changed')
    return out

def patch(root: Path, dry_run=False):
    target = root / REL / 'Thumbnail.kt'
    if not target.is_file():
        raise RuntimeError(f'InterTune source not found: {target}')
    original = target.read_text(encoding='utf-8')
    if 'VINYL_MOD_v04' in original:
        print('VINYL already present: no changes made.')
        return
    modified = original
    if 'package com.dd3boh.outertune.ui.player' not in modified:
        raise RuntimeError('Unexpected package: stopping before any changes')

    # Keep InterTune's normal tap-to-show-lyrics behavior; a LONG press toggles the vinyl.
    modified = exactly_once(
        modified,
        r'\.clickable\(\s*interactionSource\s*=\s*remember\s*\{\s*MutableInteractionSource\(\)\s*\},\s*indication\s*=\s*null,\s*enabled\s*=\s*showLyricsOnClick,\s*\)\s*\{\s*if\s*\(!showLyrics\)\s*mediaMetadata\?\.id\?\.let\s*\{\s*ActivityLog\.note\(context,\s*database,\s*it,\s*SignalKind\.LYRICS\)\s*\}\s*showLyrics\s*=\s*!showLyrics\s*haptic\.performHapticFeedback\(HapticFeedbackType\.Confirm\)\s*\}',
        '''.combinedClickable(
                    interactionSource = remember { MutableInteractionSource() },
                    indication = null,
                    enabled = true,
                    onClick = {
                        if (showLyricsOnClick) {
                            if (!showLyrics) mediaMetadata?.id?.let {
                                ActivityLog.note(context, database, it, SignalKind.LYRICS)
                            }
                            showLyrics = !showLyrics
                            haptic.performHapticFeedback(HapticFeedbackType.Confirm)
                        }
                    },
                    onLongClick = {
                        vinylEnabled = !vinylEnabled
                        haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                    }
                )''',
        'Artwork tap/long press'
    )

    modified = exactly_once(
        modified,
        r'(?P<all>AsyncImage\(\s*model\s*=\s*mediaMetadata\?\.getThumbnailModel\(\s*ART_PREVIEW_PX,\s*ART_PREVIEW_PX\s*\),\s*contentDescription\s*=\s*null,\s*modifier\s*=\s*Modifier\.fillMaxSize\(\)\s*\)\s*AsyncImage\(\s*model\s*=\s*mediaMetadata\?\.getThumbnailModel\(artPx,\s*artPx\),\s*contentDescription\s*=\s*null,\s*modifier\s*=\s*Modifier\.fillMaxSize\(\)\s*\))',
        lambda m: '''if (vinylEnabled) {
                    VinylDisc(
                        previewModel = mediaMetadata?.getThumbnailModel(ART_PREVIEW_PX, ART_PREVIEW_PX),
                        fullModel = mediaMetadata?.getThumbnailModel(artPx, artPx),
                        isPlaying = isPlaying && ownsError,
                        modifier = Modifier.fillMaxSize()
                    )
                } else {
                    ''' + m.group('all') + '''
                }''',
        'Artwork image layers'
    )

    modified = exactly_once(
        modified,
        r'(val playerMediaMetadata by playerConnection\.mediaMetadata\.collectAsState\(\))',
        r'''\1
    // VINYL_MOD_v04: long-press album art to toggle. Saved between app launches.
    var vinylEnabled by rememberPreference(VinylEnabledKey, defaultValue = true)
    val isPlaying by playerConnection.isPlaying.collectAsState()''',
        'Player reactive state'
    )
    # Imports: preserve original source and avoid duplicate added imports.
    modified = modified.replace(
        'import androidx.compose.foundation.clickable\n',
        'import androidx.compose.foundation.clickable\nimport androidx.compose.foundation.combinedClickable\nimport androidx.compose.foundation.ExperimentalFoundationApi\nimport androidx.datastore.preferences.core.booleanPreferencesKey\n',
        1
    )
    if 'import androidx.compose.foundation.combinedClickable' not in modified:
        raise RuntimeError('Expected androidx.compose.foundation.clickable import was not found')
    modified = modified.replace(
        '@Composable\nfun Thumbnail(',
        '@OptIn(ExperimentalFoundationApi::class)\n@Composable\nfun Thumbnail(',
        1
    )
    if '@OptIn(ExperimentalFoundationApi::class)\n@Composable\nfun Thumbnail(' not in modified:
        raise RuntimeError('Thumbnail Composable annotation marker has changed')
    # Local preference key; no changes to the upstream settings schema are needed.
    modified = modified.replace(
        'private val ThumbnailEnter =',
        'private val VinylEnabledKey = booleanPreferencesKey("vinyl_enabled")\nprivate val ThumbnailEnter =',
        1
    )
    if 'private val VinylEnabledKey = booleanPreferencesKey' not in modified:
        raise RuntimeError('Thumbnail constants marker has changed')
    # Build a separate package so VINYL can live beside the official InterTune.
    gradle_file = root / 'app/build.gradle.kts'
    manifest_file = root / 'app/src/main/AndroidManifest.xml'
    if not gradle_file.is_file() or not manifest_file.is_file():
        raise RuntimeError('Missing InterTune build/manifest files; upstream structure changed')
    gradle_original = gradle_file.read_text(encoding='utf-8')
    manifest_original = manifest_file.read_text(encoding='utf-8')
    gradle_modified = exactly_once(
        gradle_original,
        r'applicationId\s*=\s*"dev\.skye\.intertune"',
        'applicationId = "cz.vinyl.intertune"',
        'Application ID'
    )
    manifest_modified = exactly_once(
        manifest_original,
        r'android:label="@string/app_name"',
        'android:label="VINYL"',
        'Launcher label'
    )
    if dry_run:
        print('Patch matched artwork, preferences, application ID and label. No files changed.')
        return
    mod_src = Path(__file__).parent / 'vinyl' / 'VinylDisc.kt'
    output = root / REL / 'VinylDisc.kt'
    if output.exists():
        raise RuntimeError('VINYL source already present but marker missing in Thumbnail.kt. Stopping.')
    output.write_bytes(mod_src.read_bytes())
    target.write_text(modified, encoding='utf-8')
    gradle_file.write_text(gradle_modified, encoding='utf-8')
    manifest_file.write_text(manifest_modified, encoding='utf-8')
    print('Patched InterTune:', target, '\nAdded:', output)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('intertune_root', type=Path)
    parser.add_argument('--check', action='store_true', help='Check that source anchors match without changing files')
    args = parser.parse_args()
    try:
        patch(args.intertune_root, dry_run=args.check)
    except (RuntimeError, OSError) as exc:
        print(f'VINYL patch failed safely: {exc}', file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

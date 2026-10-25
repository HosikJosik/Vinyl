from pathlib import Path
import importlib.util
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('apply_vinyl', Path(__file__).parents[1] / 'apply_vinyl.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

SAMPLE = '''package com.dd3boh.outertune.ui.player
import androidx.compose.foundation.clickable
import androidx.compose.runtime.Composable
@SuppressLint("UnusedBoxWithConstraintsScope")
private val ThumbnailEnter = fadeIn()
@Composable
fun Thumbnail() {
 val playerMediaMetadata by playerConnection.mediaMetadata.collectAsState()
 Box(
 modifier = Modifier
 .clip(RoundedCornerShape(ThumbnailCornerRadius * 2))
 .clickable(
 interactionSource = remember { MutableInteractionSource() },
 indication = null,
 enabled = showLyricsOnClick,
 ) {
 if (!showLyrics) mediaMetadata?.id?.let { ActivityLog.note(context, database, it, SignalKind.LYRICS) }
 showLyrics = !showLyrics
 haptic.performHapticFeedback(HapticFeedbackType.Confirm)
 }
 ) {
 AsyncImage(
 model = mediaMetadata?.getThumbnailModel(
 ART_PREVIEW_PX,
 ART_PREVIEW_PX
 ),
 contentDescription = null,
 modifier = Modifier.fillMaxSize()
 )
 AsyncImage(
 model = mediaMetadata?.getThumbnailModel(artPx, artPx),
 contentDescription = null,
 modifier = Modifier.fillMaxSize()
 )
 }
}
'''

class PatcherTests(unittest.TestCase):
    def test_patch_is_valid_and_idempotent(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            target = root / module.REL / 'Thumbnail.kt'
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(SAMPLE)
            (root / 'app/build.gradle.kts').write_text('applicationId = "dev.skye.intertune"')
            (root / 'app/src/main/AndroidManifest.xml').write_text('android:label="@string/app_name"')
            module.patch(root, dry_run=True)
            self.assertEqual(target.read_text(), SAMPLE)
            module.patch(root)
            patched = target.read_text()
            self.assertIn('VinylDisc(', patched)
            self.assertIn('booleanPreferencesKey', patched)
            self.assertIn('combinedClickable', patched)
            self.assertIn('onLongClick =', patched)
            self.assertIn('ExperimentalFoundationApi::class', patched)
            self.assertIn('cz.vinyl.intertune', (root / 'app/build.gradle.kts').read_text())
            self.assertIn('android:label="VINYL"', (root / 'app/src/main/AndroidManifest.xml').read_text())
            self.assertTrue((target.parent / 'VinylDisc.kt').is_file())
            module.patch(root)
            self.assertEqual(target.read_text(), patched)

    def test_wrong_version_fails_without_edits(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            target = root / module.REL / 'Thumbnail.kt'
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('package com.dd3boh.outertune.ui.player\n')
            (root / 'app/build.gradle.kts').write_text('applicationId = "dev.skye.intertune"')
            (root / 'app/src/main/AndroidManifest.xml').write_text('android:label="@string/app_name"')
            with self.assertRaises(RuntimeError):
                module.patch(root)
            self.assertEqual(target.read_text(), 'package com.dd3boh.outertune.ui.player\n')
            self.assertFalse((target.parent / 'VinylDisc.kt').exists())

if __name__ == '__main__':
    unittest.main()

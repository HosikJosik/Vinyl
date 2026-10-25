/*
 * VINYL: original add-on for InterTune.
 * Copyright (C) 2026 VINYL contributors.
 * SPDX-License-Identifier: GPL-3.0-only
 * The base application remains Copyright its respective authors.
 */
package com.dd3boh.outertune.ui.player

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.unit.dp
import coil3.compose.AsyncImage

/**
 * Turns album artwork into a spinning record. The angular position is preserved
 * while paused; the coroutine is cancelled when the composable leaves the screen.
 * No rendering or background worker runs while the UI is not composed.
 */
@Composable
internal fun VinylDisc(
    previewModel: Any?,
    fullModel: Any?,
    isPlaying: Boolean,
    modifier: Modifier = Modifier,
) {
    val angle = remember { Animatable(0f) }
    LaunchedEffect(isPlaying) {
        while (isPlaying) {
            angle.animateTo(
                targetValue = angle.value + 360f,
                animationSpec = tween(durationMillis = 1818, easing = LinearEasing)
            )
            // Visually identical angle, avoids loss of precision during long sessions.
            angle.snapTo(angle.value % 360f)
        }
    }

    Box(modifier = modifier.graphicsLayer { rotationZ = angle.value }, contentAlignment = Alignment.Center) {
        Canvas(Modifier.fillMaxSize()) {
            val r = size.minDimension * 0.5f
            val discCenter = center
            drawCircle(
                brush = Brush.radialGradient(
                    colors = listOf(
                        Color(0xFF101015), Color(0xFF2B2A34), Color(0xFF0E0D13),
                        Color(0xFF292632), Color(0xFF0B0A11)
                    ),
                    center = discCenter,
                    radius = r
                ),
                radius = r
            )
            // The grooves are intentionally subtle, so the artwork remains the focus.
            for (fraction in 62..97 step 3) {
                drawCircle(
                    color = if (fraction % 2 == 0) Color(0x28F7F0FF) else Color(0x20A59BBB),
                    radius = r * fraction / 100f,
                    style = Stroke(width = 1.dp.toPx(), cap = StrokeCap.Round)
                )
            }
            drawCircle(color = Color(0x557B718F), radius = r * .303f, style = Stroke(width = 1.dp.toPx()))
        }
        // Two Coil models preserve InterTune's existing progressive loading behavior.
        Box(Modifier.fillMaxSize(.59f).clip(CircleShape), contentAlignment = Alignment.Center) {
            AsyncImage(
                model = previewModel,
                contentDescription = null,
                modifier = Modifier.fillMaxSize()
            )
            AsyncImage(
                model = fullModel,
                contentDescription = null,
                modifier = Modifier.fillMaxSize()
            )
        }
        Box(Modifier.size(13.dp).clip(CircleShape).background(Color(0xFFD8CFDA)))
        Box(Modifier.size(5.dp).clip(CircleShape).background(Color(0xFF29252F)))
    }
}

package com.example.eyecontrol

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

data class TrackingOutput(
    val yaw: Float,
    val pitch: Float,
    val roll: Float,
    val confidence: Float,
    val timestampMs: Long
)

class FaceTrackingManager {

    private val _tracking = MutableStateFlow(
        TrackingOutput(0f, 0f, 0f, 0f, System.currentTimeMillis())
    )
    val tracking: StateFlow<TrackingOutput> = _tracking

    fun onFrameAnalyzed(/* imageProxy: ImageProxy */) {
        // TODO: CameraX frame -> MediaPipe FaceLandmarker
        // TODO: landmarklardan yaw/pitch/roll hesapla
        _tracking.value = TrackingOutput(
            yaw = 0.02f,
            pitch = -0.01f,
            roll = 0f,
            confidence = 0.92f,
            timestampMs = System.currentTimeMillis()
        )
    }
}

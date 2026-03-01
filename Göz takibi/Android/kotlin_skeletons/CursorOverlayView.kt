package com.example.eyecontrol

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.util.AttributeSet
import android.view.View

class CursorOverlayView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null
) : View(context, attrs) {

    private val cursorPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.GREEN
        style = Paint.Style.FILL
    }

    private val dwellPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.argb(140, 255, 255, 0)
        style = Paint.Style.STROKE
        strokeWidth = 8f
    }

    var cursorX: Float = 200f
    var cursorY: Float = 200f
    var dwellProgress: Float = 0f // 0..1

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        canvas.drawCircle(cursorX, cursorY, 20f, cursorPaint)
        canvas.drawArc(cursorX - 40, cursorY - 40, cursorX + 40, cursorY + 40,
            -90f, 360f * dwellProgress, false, dwellPaint)
    }
}

<template>
  <div class="speed-gauge-container" :title="tooltip">
    <!-- Simplified Dashboard Icon Style -->
    <div class="gauge-icon" :class="iconClass">
      <!-- Arrow/Needle pointing direction -->
      <div class="arrow-wrapper" :style="{ transform: `rotate(${angle}deg)` }">
        <svg width="40" height="22" viewBox="0 0 60 40" class="arrow-svg" style="max-width: 40px; max-height: 22px; display: block;">
          <!-- Background track -->
          <path
            d="M 10 20 L 50 20"
            :stroke="backgroundColor"
            stroke-width="4"
            stroke-linecap="round"
            opacity="0.3"
          />
          <!-- Colored zones -->
          <path
            d="M 10 20 L 30 20"
            stroke="#dc3545"
            stroke-width="6"
            stroke-linecap="round"
            :opacity="score < 40 ? 1 : 0.2"
          />
          <path
            d="M 30 20 L 40 20"
            stroke="#ffc107"
            stroke-width="6"
            stroke-linecap="round"
            :opacity="score >= 40 && score < 70 ? 1 : 0.2"
          />
          <path
            d="M 40 20 L 50 20"
            stroke="#28a745"
            stroke-width="6"
            stroke-linecap="round"
            :opacity="score >= 70 ? 1 : 0.2"
          />
          <!-- Arrow/Needle -->
          <polygon
            :points="arrowPoints"
            :fill="gaugeColor"
            :opacity="opacity"
            class="arrow"
          />
          <!-- Center circle -->
          <circle
            cx="30"
            cy="20"
            r="4"
            :fill="gaugeColor"
            :opacity="opacity"
          />
        </svg>
      </div>
    </div>
    <!-- Rating text next to gauge -->
    <div class="rating-text" :style="{ color: gaugeColor }">
      {{ score > 0 ? Math.round(score) : 0 }} {{ statusText }}
    </div>
  </div>
</template>

<script>
export default {
  name: 'SpeedGauge',
  props: {
    score: {
      type: Number,
      required: true,
      default: 0,
      validator: (value) => value >= 0 && value <= 100
    },
    size: {
      type: Number,
      default: 100
    }
  },
  computed: {
    // Angle: 0 = pointing left (0 score), 180 = pointing right (100 score)
    angle() {
      // Map score (0-100) to angle (0° to 180°)
      // 0 score = 0° (pointing left), 100 score = 180° (pointing right)
      return (this.score / 100) * 180
    },
    // Color based on score: red (0-40), yellow (40-70), green (70-100)
    gaugeColor() {
      if (this.score < 40) {
        return '#dc3545' // Red - slow
      } else if (this.score < 70) {
        return '#ffc107' // Yellow - medium
      } else {
        return '#28a745' // Green - fast
      }
    },
    backgroundColor() {
      return '#e9ecef'
    },
    opacity() {
      return this.score > 0 ? 1 : 0.3
    },
    statusText() {
      if (this.score < 40) {
        return 'Lento'
      } else if (this.score < 70) {
        return 'Médio'
      } else {
        return 'Rápido'
      }
    },
    iconClass() {
      return `gauge-${this.score < 40 ? 'slow' : this.score < 70 ? 'medium' : 'fast'}`
    },
    tooltip() {
      return `Performance: ${this.score.toFixed(1)}% - ${this.statusText} | Velocidade: ${this.score < 40 ? 'Baixa' : this.score < 70 ? 'Média' : 'Alta'}`
    },
    // Arrow points: triangle pointing in the direction of the score
    arrowPoints() {
      const centerX = 30
      const centerY = 20
      const arrowLength = 15
      const arrowWidth = 6
      
      // Calculate arrow tip position based on angle
      const angleRad = (this.angle * Math.PI) / 180
      const tipX = centerX + Math.cos(angleRad) * arrowLength
      const tipY = centerY + Math.sin(angleRad) * arrowLength
      
      // Calculate base points (perpendicular to arrow direction)
      const perpAngle = angleRad + Math.PI / 2
      const base1X = centerX + Math.cos(perpAngle) * arrowWidth
      const base1Y = centerY + Math.sin(perpAngle) * arrowWidth
      const base2X = centerX - Math.cos(perpAngle) * arrowWidth
      const base2Y = centerY - Math.sin(perpAngle) * arrowWidth
      
      return `${tipX},${tipY} ${base1X},${base1Y} ${base2X},${base2Y}`
    }
  }
}
</script>

<style scoped>
.speed-gauge-container {
  display: inline-flex;
  flex-direction: row;
  align-items: center;
  justify-content: flex-start;
  cursor: help;
  padding: 2px 4px;
  gap: 6px;
  max-height: 45px;
  overflow: hidden;
  line-height: 1;
}

.gauge-icon {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  height: 100%;
}

.arrow-wrapper {
  position: relative;
  width: 40px;
  height: 22px;
  margin-bottom: 1px;
  transition: transform 0.3s ease;
  flex-shrink: 0;
}

.arrow-svg {
  display: block;
  filter: drop-shadow(0 2px 3px rgba(0, 0, 0, 0.15));
}

.arrow {
  transition: fill 0.3s ease, opacity 0.3s ease;
}

.rating-text {
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
  transition: color 0.3s ease;
  line-height: 1.2;
  flex-shrink: 0;
}

.gauge-slow .score-badge {
  animation: pulse-slow 2s infinite;
}

.gauge-fast .score-badge {
  animation: pulse-fast 2s infinite;
}

@keyframes pulse-slow {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

@keyframes pulse-fast {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}
</style>

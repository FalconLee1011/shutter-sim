<script setup lang="ts">
import rawImage from "@/assets/default/0_IMG_5229.jpg";
import beforeTM from "@/assets/default/1_before_tm.png";
import beforeCCM from "@/assets/default/2_before_ccm.png";
import bayer from "@/assets/default/3_bayer.png";
import beforeWb from "@/assets/default/4_before_wb.png";
import beforeLsc from "@/assets/default/5_before_lsc.png";
import beforeDpc from "@/assets/default/6_before_dpc.png";
import beforeBlc from "@/assets/default/7_before_blc.png";
import cfaB from "@/assets/default/8_cfa_b.png";
import cfaG from "@/assets/default/8_cfa_g.png";
import cfaR from "@/assets/default/8_cfa_r.png";
import rawBayer from "@/assets/default/9_raw_bayer.png";

const isShutterClicked = ref(false);
const isTakingPhoto = ref(false);
const blurPhone = ref(false);
const showPipeline = ref(false);
const showSlider = ref(false);
const hasCaptured = ref(false);
const showAbout = ref(false);

const reversedPipelineImages = [
  rawImage,
  beforeTM,
  beforeCCM,
  bayer,
  beforeWb,
  beforeLsc,
  beforeDpc,
  beforeBlc,
  rawBayer,
  cfaR,
  cfaB,
  cfaG,
];

const pipelineSteps = ref([
  {
    title: "Final Result",
    hoverable: false,
    description: "Finished photo. Every later step undoes one stage of the pipeline.",
    isActive: false,
  },
  {
    title: "Tone Mapping",
    hoverable: true,
    description: "Inverse gamma, 2.2, back toward linear light.",
    isActive: false,
  },
  {
    title: "Color Correction Matrix",
    hoverable: true,
    description: "Inverse of the configured CCM.",
    isActive: false,
  },
  {
    title: "Demosaic",
    hoverable: true,
    description: "Re-mosaic to one sample per pixel, GBRG.",
    isActive: false,
  },
  {
    title: "White Balance",
    hoverable: true,
    description: "Divide each channel by its configured gain.",
    isActive: false,
  },
  {
    title: "Lens Shading Correction",
    hoverable: true,
    description: "Darken edges and corners to put the vignette back.",
    isActive: false,
  },
  {
    title: "Defective Pixel Correction",
    hoverable: true,
    description: "Punch random samples to zero.",
    isActive: false,
  },
  {
    title: "Black Level Correction",
    hoverable: true,
    description: "Add the black-level offset back onto the Bayer samples.",
    isActive: false,
  },
  {
    title: "Color Filter Array — Red",
    hoverable: false,
    description: "Isolates the simulated red Bayer samples, not extra step.",
    isActive: false,
  },
  {
    title: "Color Filter Array — Blue",
    hoverable: false,
    description: "Isolates the simulated blue Bayer samples, not extra step.",
    isActive: false,
  },
  {
    title: "Color Filter Array — Green",
    hoverable: false,
    description: "Isolates the simulated green Bayer samples, not extra step.",
    isActive: false,
  },
  {
    title: "Raw Bayer",
    hoverable: false,
    description: "One simulated Bayer sample per pixel.",
    isActive: true,
  },
]);

const selectedPipelineIndex = ref(
  pipelineSteps.value.findIndex((step) => step.isActive),
);
const stepsContainer = ref<HTMLElement | null>(null);
const isPreviewHovered = ref(false);
const selectedPipelineStep = computed(
  () => pipelineSteps.value[selectedPipelineIndex.value],
);
const showingPipelineResult = computed(
  () =>
    isPreviewHovered.value && selectedPipelineStep.value?.hoverable === true,
);
const previewImage = computed(() => {
  // Each processing stage's output is the preceding image in this reversed list.
  const index =
    selectedPipelineIndex.value - (showingPipelineResult.value ? 1 : 0);
  return reversedPipelineImages[index];
});
const previewAlt = computed(() => {
  const step = selectedPipelineStep.value;
  if (!step) return "Finished photo";
  if (!step.hoverable) return step.title;
  return `${showingPipelineResult.value ? "After" : "Before"} ${step.title}`;
});

const centerSelectedStep = (behavior: ScrollBehavior = "smooth") => {
  const container = stepsContainer.value;
  const selectedStep =
    container?.querySelectorAll<HTMLElement>(".step")[
      selectedPipelineIndex.value
    ];
  if (!container || !selectedStep) return;

  const containerBounds = container.getBoundingClientRect();
  const stepBounds = selectedStep.getBoundingClientRect();
  container.scrollTo({
    left:
      container.scrollLeft +
      stepBounds.left -
      containerBounds.left +
      stepBounds.width / 2 -
      container.clientWidth / 2,
    behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
      ? "instant"
      : behavior,
  });
};

watch(
  stepsContainer,
  (container, _, onCleanup) => {
    if (!container) return;
    const observer = new ResizeObserver(() => centerSelectedStep("instant"));
    observer.observe(container);
    onCleanup(() => observer.disconnect());
  },
  { flush: "post" },
);

const selectPipelineStep = (index: number, center = true) => {
  selectedPipelineIndex.value = index;
  pipelineSteps.value.forEach((step, stepIndex) => {
    step.isActive = stepIndex === index;
  });
  if (center) centerSelectedStep();
};

const selectNearestPipelineStep = () => {
  const container = stepsContainer.value;
  if (!container) return;

  const center =
    container.getBoundingClientRect().left +
    container.clientLeft +
    container.clientWidth / 2;
  let nearestIndex = -1;
  let nearestDistance = Infinity;

  container.querySelectorAll<HTMLElement>(".step").forEach((step, index) => {
    const bounds = step.getBoundingClientRect();
    const distance = Math.abs(bounds.left + bounds.width / 2 - center);
    if (distance < nearestDistance) {
      nearestDistance = distance;
      nearestIndex = index;
    }
  });

  if (nearestIndex >= 0 && nearestIndex !== selectedPipelineIndex.value) {
    selectPipelineStep(nearestIndex, false);
  }
};

const finishPipelineReveal = (index: number) => {
  if (!showPipeline.value || index !== reversedPipelineImages.length - 1)
    return;
  selectPipelineStep(index, false);
  isPreviewHovered.value = false;
  showSlider.value = true;
};

const captureTimers = new Set<ReturnType<typeof setTimeout>>();

const scheduleCapture = (callback: () => void, delay: number) => {
  const timer = setTimeout(() => {
    captureTimers.delete(timer);
    callback();
  }, delay);
  captureTimers.add(timer);
};

const clearCaptureTimers = () => {
  captureTimers.forEach((timer) => clearTimeout(timer));
  captureTimers.clear();
};

const resetCapture = () => {
  clearCaptureTimers();
  showPipeline.value = false;
  showSlider.value = false;
  blurPhone.value = false;
  isShutterClicked.value = false;
  isTakingPhoto.value = false;
  hasCaptured.value = false;
  isPreviewHovered.value = false;
  selectPipelineStep(reversedPipelineImages.length - 1, false);
};

onBeforeUnmount(clearCaptureTimers);

const onShutterClicked = () => {
  if (hasCaptured.value || isShutterClicked.value || isTakingPhoto.value) {
    return;
  }

  hasCaptured.value = true;
  isShutterClicked.value = true;
  scheduleCapture(() => {
    isShutterClicked.value = false;
  }, 250);
  scheduleCapture(() => {
    isTakingPhoto.value = true;
  }, 100);
  scheduleCapture(() => {
    isTakingPhoto.value = false;
  }, 200);

  scheduleCapture(() => {
    blurPhone.value = true;
  }, 600);

  scheduleCapture(() => {
    showPipeline.value = true;
  }, 1300);
};
</script>

<template>
  <Transition name="about-fade">
    <div v-if="showAbout" class="about container">
      <div class="about content">
        <div class="title">Shutter Sim Web</div>
        <p>
          This demo uses the result from
          <a href="https://github.com/FalconLee1011/shutter-sim"
            >shutter-sim project</a
          >, downsampled to png for better compatibility.
        </p>
        <p>
          The project is an educational image signal processor simulator. which
          works backward through a simplified camera pipeline to visualize the
          process from the final result to what sensor captured.
        </p>
        <p>
          All the parameters are defined for better visualization result, not from
          any refernece or calibrated image, this tool does not recover raw file.
        </p>
        <p>
          To see the demo, click the shutter to start!
        </p>
        <div class="actions">
          <button type="button" class="action close-about" @click="showAbout = false">CLOSE</button>
        </div>
      </div>
    </div>
  </Transition>
  <button type="button" class="action about" @click="showAbout = true">
    ABOUT
  </button>
  <div
    v-if="showPipeline"
    class="pipeline-preview container"
    :class="{ revealing: !showSlider }"
  >
    <div class="slider-slot" :class="{ expanded: showSlider }">
      <div
        v-if="showSlider"
        ref="stepsContainer"
        class="steps"
        @scroll.passive="selectNearestPipelineStep"
      >
        <div class="selection">
          <button
            v-for="(step, index) in pipelineSteps"
            :key="step.title"
            type="button"
            class="step"
            :class="{ active: step.isActive }"
            :aria-pressed="step.isActive"
            @click="selectPipelineStep(index)"
          >
            <strong>{{ step.title }}</strong>
            <span>{{ step.description }}</span>
            <span v-if="step.hoverable" class="tip"
              >Hover the image to see the differece.</span
            >
          </button>
        </div>
      </div>
    </div>
    <div class="pipeline-preview">
      <template v-if="!showSlider">
        <img
          v-for="(image, index) in reversedPipelineImages"
          :key="image"
          class="reveal-image"
          :src="image"
          :alt="pipelineSteps[index]?.title"
          :style="{ animationDelay: `${index * 0.15}s` }"
          @animationend="finishPipelineReveal(index)"
        />
      </template>
      <img
        v-else
        :src="previewImage"
        :alt="previewAlt"
        @mouseenter="isPreviewHovered = true"
        @mouseleave="isPreviewHovered = false"
      />
    </div>
    <button type="button" class="action reset" @click="resetCapture">
      RESET
    </button>
  </div>
  <div class="phone container">
    <div class="phone frame" :class="{ blur: blurPhone }">
      <div class="phone screen">
        <div class="app">
          <div class="title">Shutter Sim</div>

          <div class="preview" :class="{ taking: isTakingPhoto }">
            <img :src="reversedPipelineImages[0]" alt="" />
          </div>
          <span class="mode active">PIPELINE_PREVIEW</span>
          <div class="camera-control">
            <div
              ref="shutter"
              class="shutter"
              :class="{ 'on-click': isShutterClicked }"
              @click="onShutterClicked"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.phone.container {
  width: 100%;
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
}

.about.container {
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
  position: absolute;
  width: 100%;
  height: 100vh;
  z-index: 100;
  backdrop-filter: blur(5px) brightness(0.85);
}

.about-fade-enter-active,
.about-fade-leave-active {
  transition: opacity 0.4s ease;
}

.about-fade-enter-from,
.about-fade-leave-to {
  opacity: 0;
}

.about.content {
  max-width: 45%;
  background-color: var(--color-bl-1o90);
  padding: 1rem;
  box-sizing: border-box;
}

.about.content .title {
  font-size: 125% !important;
}

.action {
  appearance: none;
  -webkit-appearance: none;
  border: 0;
  border-radius: 0;
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  background: transparent;
  box-shadow: none;
  color: inherit;
  font: inherit;
  cursor: pointer;
  text-transform: capitalize;
  transition: 0.3s;
}

.action:hover {
  color: var(--color-org) !important;
  cursor: pointer;
}

.action.reset {
  position: absolute;
  bottom: 2.5rem;
  right: 2.5rem;
  font-size: 125%;
}

.action.about {
  position: absolute;
  bottom: 2.5rem;
  left: 2.5rem;
  font-size: 125%;
  z-index: 5;
}

.about.content .actions {
  display: flex;
  justify-content: center;
}

.action.close-about {
  font-size: 85%;
  margin-top: 0.5rem;
  border: 1px var(--color-wh-d7) solid;
  padding: 0.1rem 0.25rem;
  border-radius: 0.25rem;
}

.action.close-about:hover {
  border: 1px var(--color-org) solid;
}

.phone {
  --height: 750px;
  --width: 375px;
  --radius: 50px;
  padding: 10px;
  box-sizing: border-box;
  transition: 1.2s;
}

.phone.blur {
  transform: translateY(75%);
  filter: brightness(0.5) blur(5px);
}

.phone.frame {
  border: 2.5px var(--color-wh-d7) solid;
  border-radius: var(--radius);
  height: var(--height);
  width: var(--width);
  background-color: black;
  display: flex;
}

.phone.screen {
  background-color: var(--color-bl-1);
  height: calc(var(--height) * 95%);
  width: calc(var(--width) * 95%);
  border-radius: calc(var(--radius) * 0.725);
  padding: 0;
}

.phone .app {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.phone .app .title {
  height: 30%;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 150%;
}

.phone .app .preview,
.phone .app .preview img {
  max-width: 100%;
  transition: 0.05s;
}

.phone .app .preview.taking {
  max-width: 100%;
  opacity: 0;
  background-color: black;
}

.phone .app .mode {
  height: 5%;
  font-size: 90%;
}

.phone .app .mode.active {
  color: var(--color-org);
}

.phone .app .camera-control {
  height: 30%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.phone .app .camera-control .shutter {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  border: 4px var(--color-wh-ef) solid;
  cursor: pointer;
  transition: 0.05s;
}

.phone .app .camera-control .shutter::before {
  content: "";
  display: block;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background-color: var(--color-wh-ef);
  transform-origin: center;
  transform: scale(0.85);
}

.phone .app .camera-control .shutter.on-click {
  filter: brightness(0.5);
}

.pipeline-preview.container {
  grid-template-columns: minmax(0, 1fr);
  grid-template-rows: auto minmax(0, 1fr);
  gap: 1rem;
  transition: gap 0.5s cubic-bezier(0.22, 1, 0.36, 1);
  position: absolute;
  width: 100%;
  height: 100vh;
  top: 0px;
  left: 0px;
  z-index: 1;
}

.pipeline-preview {
  display: grid;
  align-items: center;
  justify-content: center;
  min-width: 0;
  min-height: 0;
  height: 100%;
}

.pipeline-preview.container.revealing {
  gap: 0;
}

.slider-slot {
  display: grid;
  grid-template-rows: 0fr;
  min-width: 0;
  overflow: hidden;
  transition: grid-template-rows 0.5s cubic-bezier(0.22, 1, 0.36, 1);
}

.slider-slot.expanded {
  grid-template-rows: 1fr;
}

.pipeline-preview img.reveal-image {
  visibility: hidden;
  animation: appear 0.6s steps(1, end) both;
}

@keyframes appear {
  from {
    visibility: hidden;
  }
  to {
    visibility: visible;
  }
}

.pipeline-preview .steps {
  min-height: 0;
  min-width: 0;
  max-width: 100%;
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  animation: slider-enter 0.5s cubic-bezier(0.22, 1, 0.36, 1) both;
}

@keyframes slider-enter {
  from {
    transform: translateY(-100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.pipeline-preview .steps .selection {
  box-sizing: border-box;
  width: max-content;
  min-width: 100%;
  display: flex;
  flex-direction: row;
  gap: 0.75rem;
  padding: 1rem max(1rem, calc(50% - 9rem));
  box-sizing: border-box;
}

.pipeline-preview .steps .selection .step {
  scroll-snap-align: center;
  box-sizing: border-box;
  flex: 0 0 18rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem;
  box-sizing: border-box;
  border: 1px solid currentColor;
  border-radius: 0.5rem;
  background: var(--color-bl-1);
  color: inherit;
  font: inherit;
  text-align: center;
  cursor: pointer;
}

.pipeline-preview .steps .selection .step span {
  font-size: 80%;
}

.pipeline-preview .steps .selection .step span.tip {
  color: var(--color-wh-d7) !important;
  font-size: 65%;
}

.pipeline-preview .step.active,
.pipeline-preview .step.active * {
  color: var(--color-org) !important;
}

.pipeline-preview .step:focus-visible {
  /* outline: 2px solid var(--color-org) !important; */
  outline-offset: -3px;
}

.pipeline-preview img {
  grid-area: 1 / 1;
  max-width: 100%;
  max-height: 100%;
  min-height: 0;
  object-fit: contain;
}

@media only screen and (max-width: 800px) {
  .phone {
    --height: 500px;
    --width: 250px;
    --radius: 30px;
    padding: 10px;
    box-sizing: border-box;
  }

  .action.reset, 
  .action.about {
    bottom: 0.5rem !important;
  }
  .action.reset {
    right: 0.5rem;
  }
  .action.about {
    left: 0.5rem;
  }
}
</style>

<template>
  <button
    type="button"
    class="logo-menu-button"
    aria-label="사이드바 열기"
    @click="$emit('click')"
    @mouseenter="isHovered = true"
    @mouseleave="isHovered = false"
  >
    <span
      :class="[
        'logo-menu-state',
        'logo-state',
        { hidden: isHovered },
      ]"
    >
      <span class="header-brand-icon" aria-hidden="true"></span>
    </span>

    <span
      :class="[
        'logo-menu-state',
        'menu-state',
        { visible: isHovered },
      ]"
      aria-hidden="true"
    >
      <svg viewBox="0 0 24 24">
        <path d="M4 7h16"></path>
        <path d="M4 12h16"></path>
        <path d="M4 17h16"></path>
      </svg>
    </span>
  </button>
</template>

<script setup>
import { ref } from 'vue';

defineEmits(['click']);

const isHovered = ref(false);
</script>

<template>
  <RouterView v-slot="{ Component, route }">
    <Transition name="step-fade" mode="out-in">
      <component :is="Component" :key="route.fullPath" />
    </Transition>
  </RouterView>
</template>

// eslint.config.js (formato moderno, Vue 3)
import pluginVue from 'eslint-plugin-vue'
import prettierConfig from '@vue/eslint-config-prettier'

export default [
  ...pluginVue.configs['flat/recommended'],
  prettierConfig,
]
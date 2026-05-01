import { globalIgnores } from 'eslint/config'
import pluginVue from 'eslint-plugin-vue'
import skipFormatting from 'eslint-config-prettier/flat'

export default [
    {
        name: 'app/files-to-lint',
        files: ['**/*.{vue,js,jsx,mts}'],
    },

    globalIgnores(['**/dist/**', '**/dist-ssr/**', '**/coverage/**']),

    ...pluginVue.configs['flat/essential'],

    skipFormatting,
]

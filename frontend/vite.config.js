import { defineConfig } from 'vite'

export default defineConfig({
  build: {
    rolldownOptions: {
      output: {
        codeSplitting: {
          groups: [
            {
              name: 'react-vendor',
              test: /node_modules[\\/]react(?:-dom)?[\\/]/,
              priority: 20,
            },
            {
              name: 'cytoscape-vendor',
              test: /node_modules[\\/]cytoscape[\\/]/,
              priority: 15,
            },
            {
              name: 'leaflet-vendor',
              test: /node_modules[\\/]leaflet[\\/]/,
              priority: 15,
            },
            {
              name: 'ui-vendor',
              test: /node_modules[\\/]lucide-react[\\/]/,
              priority: 10,
            },
          ],
        },
      },
    },
  },
})

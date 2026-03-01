const { defineConfig } = require("cypress");
const createBundler = require("@bahmutov/cypress-esbuild-preprocessor");
const preprocessor = require("@badeball/cypress-cucumber-preprocessor");
const createEsbuildPlugin = require("@badeball/cypress-cucumber-preprocessor/esbuild");

module.exports = defineConfig({
  e2e: {
    baseUrl: 'http://127.0.0.1:5000',
    // Diz ao Cypress para procurar arquivos .feature
    specPattern: "**/*.feature", 
    async setupNodeEvents(on, config) {
      // Adiciona o plugin do Cucumber
      await preprocessor.addCucumberPreprocessorPlugin(on, config);
      
      // Configura o empacotador
      on(
        "file:preprocessor",
        createBundler({
          plugins: [createEsbuildPlugin.default(config)],
        })
      );

      return config;
    },
  },
});
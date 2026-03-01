import { Given, When, Then } from "@badeball/cypress-cucumber-preprocessor";

let nomeDoProduto = `App BDD Delivery ${Date.now()}`;

Given("que eu tenho um usuario cadastrado e estou logado", () => {
  // Cria o utilizador silenciosamente
  cy.request({
    method: 'POST',
    url: '/auth/register',
    failOnStatusCode: false,
    body: { username: 'bdd_user', email: 'bdd@teste.com', password: '123' }
  });

  // Faz o login
  cy.visit('/auth/login_page');
  cy.get('input#username').type('bdd_user');
  cy.get('input#password').type('123');
  cy.get('button[type="submit"]').click();
  cy.url({ timeout: 5000 }).should('include', '/dashboard');
});

When("eu clico no botão {string}", (textoDoBotao) => {
  cy.contains('button', textoDoBotao).click();
});

When("preencho o formulario de produto com dados validos", () => {
  cy.get('#createProductModal').should('be.visible');
  cy.get('input#productName').type(nomeDoProduto);
  cy.get('textarea#productDescription').type('Produto criado via BDD');
  cy.get('textarea#valueProposition').type('Testar a integração do Cucumber');
  cy.get('textarea#channels_platforms').type('Web');
});

When("clico em {string}", (textoDoBotao) => {
  cy.get('#createProductForm button[type="submit"]').contains(textoDoBotao).click();
});

Then("eu devo ver o novo produto listado no Dashboard", () => {
  cy.get('h1', { timeout: 10000 }).should('contain', 'Dashboard');
  cy.contains('.project-card h3', nomeDoProduto).should('be.visible');
});
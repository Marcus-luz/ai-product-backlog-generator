describe('Dashboard e Gestão de Produtos', () => {

  // Antes de toda a suíte de testes, garantimos que temos um usuário válido
  before(() => {
    cy.request({
      method: 'POST',
      url: '/auth/register',
      failOnStatusCode: false, 
      body: {
        username: 'po_cypress',
        email: 'pocypress@teste.com',
        password: 'senha_segura'
      }
    })
  })

  // Antes de CADA teste (it), o Cypress faz o login e entra no Dashboard
  beforeEach(() => {
    cy.visit('/auth/login_page')
    cy.get('input#username').type('po_cypress')
    cy.get('input#password').type('senha_segura')
    cy.get('button[type="submit"]').click()
    
    // Aguarda o redirecionamento e verifica se chegou no Dashboard
    cy.url({ timeout: 5000 }).should('include', '/dashboard')
  })

  it('Deve carregar o Dashboard e exibir os 4 cards de estatísticas', () => {
    cy.get('h1').should('contain', 'Dashboard')
    // Verifica se os cards (Total Projetos, Épicos, Histórias, Requisitos) estão na tela
    cy.get('.stat-card').should('have.length.at.least', 4) 
  })

  it('Deve abrir o modal e criar um Novo Produto com sucesso', () => {
    // 1. Clica no botão "Novo Produto" usando a classe e o texto
    cy.contains('button.btn-primary', 'Novo Produto').click()

    // 2. Valida se o Modal abriu
    cy.get('#createProductModal').should('be.visible')
    cy.get('h2').should('contain', 'Criar Novo Produto')

    // 3. Preenche o formulário
    // Usamos o Date.now() para criar um nome único e não dar erro de duplicidade nas próximas vezes que você rodar o teste
    const productName = `App Delivery Automático ${Date.now()}` 
    
    cy.get('input#productName').type(productName)
    cy.get('textarea#productDescription').type('Sistema de delivery criado pelo robô do Cypress.')
    cy.get('textarea#valueProposition').type('Entregar comida rápida testando a qualidade do código.')
    cy.get('textarea#channels_platforms').type('Web, Android, iOS')

    // 4. Submete o formulário
    cy.get('#createProductForm button[type="submit"]').click()

    // 5. Validação final: o seu JS dá um location.reload(). 
    // Vamos aguardar a página recarregar e verificar se o produto novo apareceu na grade!
    cy.get('h1', { timeout: 10000 }).should('contain', 'Dashboard')
    cy.contains('.project-card h3', productName).should('be.visible')
  })
})